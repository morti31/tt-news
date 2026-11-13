"""Syncs official WTT data into the site. Run by .github/workflows/wtt-sync.yml every 30 minutes
(GitHub's runners can reach WTT; the scheduled update runs can't).

For every event page in data/events.json with a "wtt_id" that is on now or starts within 3 days:
  - match times and pairings from WTT's order of play become fixtures in data/schedule.json
    (and so in calendar.ics), replacing hand-entered match fixtures for that event;
  - the draw in data/draws/<id>.json is refreshed if the event page has a "draw".
Once a day it also refreshes the ITTF world ranking (data/rankings.json and the sidebar top 10).
Nothing is written if WTT can't be reached.
"""
import json, os, re, sys, urllib.request, datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_draw, rankings

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CMS = "https://wtt-website-api-vm-frontdoor-hhaec5epbhdyfugz.a01.azurefd.net/liveeventsapi/api/cms"
RANKS = "https://wtt-web-frontdoor-withoutcache-cqakg0andqf5hchn.a01.azurefd.net/ranking/SEN_SINGLES.json"
RANKS200 = "https://wttcmsapigateway-new.azure-api.net/ttu/Rankings/GetRankingIndividuals?CategoryCode=SEN"
HEADERS = {"Origin": "https://www.worldtabletennis.com", "Referer": "https://www.worldtabletennis.com/", "User-Agent": "Mozilla/5.0 (Eleven)"}
FAMILY_FIRST = fetch_draw.FAMILY_FIRST


def get(url):
    # Ask for identity or gzip only, and undo whatever compression the CDN still applies
    # (Azure Front Door sometimes serves the ranking file compressed regardless).
    req = urllib.request.Request(url, headers={**HEADERS, "Accept-Encoding": "gzip, deflate"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
        enc = (r.headers.get("Content-Encoding") or "").lower()
    return json.loads(decompress(body, enc).decode("utf-8-sig"))


def decompress(body, enc=""):
    import gzip, zlib
    if enc == "gzip" or body[:2] == b"\x1f\x8b":
        return gzip.decompress(body)
    if enc == "deflate":
        try:
            return zlib.decompress(body)
        except zlib.error:
            return zlib.decompress(body, -zlib.MAX_WBITS)
    if enc == "br" or (body[:1] not in (b"{", b"[", b" ", b"\n", b"\r", b"\t", b"\xef")):
        try:
            import brotli
            return brotli.decompress(body)
        except ImportError:
            pass
        for wbits in (zlib.MAX_WBITS | 32, -zlib.MAX_WBITS):
            try:
                return zlib.decompress(body, wbits)
            except zlib.error:
                continue
    return body


def person(comp):
    """'AN Jaehyun' + KOR -> 'An Jaehyun'; 'LEBRUN Felix' + FRA -> 'Félix Lebrun'."""
    if not comp:
        return None
    d = comp.get("Description") or {}
    orgs = str(comp.get("Organization", "")).split("/")
    out = []
    # Doubles pairs come as one team: "FANG Bo/POLCANOVA Sofia" -> "Fang Bo / Sofia Polcanova"
    for i, part in enumerate((d.get("TeamName") or "").split("/")):
        words = part.split()
        org = orgs[i] if i < len(orgs) else orgs[0]
        fam = " ".join(fetch_draw.cap(w) for w in words if w.isupper())
        giv = " ".join(w for w in words if not w.isupper())
        name = (f"{fam} {giv}" if org in FAMILY_FIRST else f"{giv} {fam}").strip()
        out.append(fetch_draw.FIXES.get(name, name))
    return " / ".join(n for n in out if n)


def utc_offset(wtt_id, fallback):
    """Hours between the venue's local time and UTC, read from a finished match if there is one."""
    try:
        for r in get(f"{CMS}/GetOfficialResult?EventId={wtt_id}&include_match_card=false&take=1"):
            x = r.get("extended_info") or {}
            f = "%m/%d/%Y %H:%M:%S"
            local, utc = dt.datetime.strptime(x["startDateLocal"], f), dt.datetime.strptime(x["startDateUTC"], f)
            return round((local - utc).total_seconds() / 3600, 2)
    except Exception:
        pass
    return fallback


def fixtures(ev):
    wid = ev["wtt_id"]
    offset = utc_offset(wid, ev.get("utc_offset", 0))
    units = [u for block in get(f"{CMS}/GetEventSchedule/{wid}") for u in (block.get("Competition") or {}).get("Unit", [])]
    out, seen = [], set()
    for u in units:
        if not u.get("StartDate") or u["Code"] in seen:
            continue
        seen.add(u["Code"])
        start = dt.datetime.fromisoformat(u["StartDate"]) - dt.timedelta(hours=offset)
        end = dt.datetime.fromisoformat(u["EndDate"]) - dt.timedelta(hours=offset) if u.get("EndDate") else start + dt.timedelta(minutes=50)
        desc = next((x["Value"] for x in u.get("ItemDescription", []) if x.get("Language") == "ENG"), u["Code"])
        parts = desc.split(" - ")   # "Men's Singles - Round of 32 - Match 10"
        what = ", ".join(p.lower() for p in parts[:2])
        what = re.sub(r"round of (\d+)", r"last \1", what).replace("finals", "final")
        players = [person((s or {}).get("Competitor")) for s in ((u.get("StartList") or {}).get("Start") or [])]
        players = [p for p in players if p]
        title = f'{ev["name"]}: {" v ".join(players)}, {what}' if len(players) == 2 else f'{ev["name"]}: {desc.replace(" - ", ", ")}'
        table = (u.get("VenueDescription") or {}).get("LocationName")
        out.append({"id": "wtt-" + wid + "-" + u["Code"].replace("-", "").lower(), "event_id": ev.get("schedule_id", ev["id"]), "name": title,
                    "start": start.strftime("%Y-%m-%dT%H:%M:00Z"), "end": end.strftime("%Y-%m-%dT%H:%M:00Z"),
                    "source": f"https://www.worldtabletennis.com/eventInfo?eventId={wid}", "code": u["Code"], **({"detail": table} if table else {})})
    return sorted(out, key=lambda f: f["start"]), offset


WTT_NAME = re.compile(r"^WTT (Star Contender|Contender|Feeder|Champions|Grand Smash|Smash|Finals)\b", re.I)
SERIES = {"star contender": ("star", "WTT Star Contender"), "contender": ("contender", "WTT Contender"), "feeder": ("contender", "WTT Feeder"),
          "champions": ("champions", "WTT Champions"), "grand smash": ("smash", "WTT Grand Smash"), "smash": ("smash", "WTT Grand Smash"),
          "finals": ("champions", "WTT Finals")}


def slug(s):
    import unicodedata
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# Host countries for places that have no event page yet (a new city falls back to the city's own name)
COUNTRY_OF = {"istanbul": "Türkiye", "gdansk": "Poland", "doha": "Qatar", "dusseldorf": "Germany", "vila-nova-de-gaia": "Portugal", "tunis": "Tunisia",
              "buenos-aires": "Argentina", "panagyurishte": "Bulgaria", "havirov": "Czechia", "lagos": "Nigeria", "spokane": "United States",
              "fukuoka": "Japan", "nice": "France", "baku": "Azerbaijan", "szombathely": "Hungary", "olomouc": "Czechia", "metz": "France",
              "tashkent": "Uzbekistan", "lima": "Peru", "cappadocia": "Türkiye", "skopje": "North Macedonia", "zagreb": "Croatia", "pontevedra": "Spain",
              "cairo": "Egypt", "amman": "Jordan", "bangkok": "Thailand", "muscat": "Oman", "kuala-lumpur": "Malaysia", "manila": "Philippines", "chennai": "India"}


def event_span(units):
    """(first day, last day, "Singles and doubles") from an order of play."""
    days = sorted({u["StartDate"][:10] for u in units if u.get("StartDate")})
    codes = " ".join(u.get("Code", "") for u in units)
    kinds = [k for k, hit in (("singles", "SINGLES" in codes), ("doubles", "DOUBLES" in codes.replace("XDOUBLES", "")), ("mixed doubles", "XDOUBLES" in codes)) if hit]
    text = {1: kinds[0] if kinds else "", 2: " and ".join(kinds), 3: "Singles, doubles and mixed doubles"}[min(len(kinds), 3)] if kinds else ""
    return (days[0], days[-1], text[:1].upper() + text[1:]) if days else (None, None, "")


def auto_hubs(doc, sched, today):
    """Every senior WTT event that is on now or starts within 3 days gets an event page, so its live scores, order of
    play, results and draw flow in without anyone adding it by hand. The event ids come from Eleven's match database
    (data/matches/events.json, which lists WTT's events ahead of time); an event that already has a page is left alone.
    Pages made here carry "auto": true; remove that flag to take one over by hand. Dates are refreshed from WTT's order
    of play on every run. Returns True if events.json changed."""
    mpath = os.path.join(ROOT, "data", "matches", "events.json")
    if not os.path.exists(mpath):
        return False
    known = json.load(open(mpath, encoding="utf-8"))
    have = {str(x) for ev in doc["events"] for x in (ev.get("wtt_id"), ev.get("draw")) if x}
    by_city = {}
    for ev in doc["events"]:
        by_city.setdefault(slug(ev["city"]), (ev["city"], ev["country"], ev.get("utc_offset")))
    sch = {slug(e["name"]) + "-" + e["start"][:4]: e for e in sched.get("events", []) if e.get("start")}
    changed = False
    sched_changed = doc.setdefault("_sched_changed", [])
    for wid, info in sorted(known.items(), key=lambda kv: int(kv[0])):
        name = (info.get("name") or "").strip()
        m = WTT_NAME.match(name)
        year = re.search(r"\b(20\d\d)\b", name)
        if not m or not year or info.get("skip") or info.get("done") or int(year.group(1)) not in (today.year, today.year + 1):
            continue
        mine = next((ev for ev in doc["events"] if str(ev.get("wtt_id")) == wid and ev.get("auto")), None)
        if wid in have and not mine:
            continue
        try:
            units = [u for block in get(f"{CMS}/GetEventSchedule/{wid}") for u in (block.get("Competition") or {}).get("Unit", [])]
        except Exception as err:
            print(f"{name}: schedule unavailable ({err})")
            continue
        first, last, kinds = event_span(units)
        if not first:
            continue
        a, b = dt.date.fromisoformat(first), dt.date.fromisoformat(last)
        # WTT publishes the order of play a few days at a time, so the last day seen is not the last day of the event:
        # an event runs at least 4 days (Feeder) or 6 (the rest), and never shrinks below what a page already says
        b = max(b, a + dt.timedelta(days=3 if m.group(1).lower() == "feeder" else 5), dt.date.fromisoformat(mine["end"]) if mine else b)
        a = min(a, dt.date.fromisoformat(mine["start"]) if mine else a)
        first, last = a.isoformat(), b.isoformat()
        if mine is None and not (a - dt.timedelta(days=3) <= today <= b + dt.timedelta(days=1)):
            continue
        base = re.sub(r"\s+(Presented|Powered) [Bb]y.*$", "", name)
        base = re.sub(r"\s*\b20\d\d\b.*$", "", base).strip()                      # "WTT Contender Istanbul"
        city = re.sub(r"^WTT (Star Contender|Contender|Feeder|Champions|Grand Smash|Smash|Finals)\s*", "", base).strip()
        city = re.sub(r"\s+[IVX]+$", "", city)                                            # "Doha II" is Doha
        city_key = slug(city)
        known_city = by_city.get(city_key)
        sch_ev = sch.get(slug(base) + "-" + year.group(1))
        tier, series = SERIES[m.group(1).lower()]
        offset = (known_city or (None, None, None))[2]
        hub = {"id": slug(base) + "-" + year.group(1), "name": base, "group": "Majors" if tier == "smash" else "WTT Series", "tier": tier, "series": series, "level": series,
               "city": city, "country": (sch_ev or {}).get("country") or (known_city or (city, COUNTRY_OF.get(city_key) or city))[1] or city, "year": year.group(1),
               "start": first, "end": last, "events": kinds, "live": True, "wtt_id": wid, "draw": wid, "auto": True}
        if sch_ev:
            hub["schedule_id"] = sch_ev["id"]
        elif not mine:
            # Events the calendar doesn't list (most Feeders) still need a schedule entry: the homepage, the scores strip and the
            # calendar read events from data/schedule.json. Prestige: 1 for a Feeder, 1.5 for a Contender (see TIER_PRESTIGE).
            sched["events"].append({"id": hub["id"], "name": base, "start": first, "end": last, "city": city, "country": hub["country"], "series": "WTT",
                                    "type": series, "prestige": 1 if m.group(1).lower() == "feeder" else 1.5 if tier == "contender" else 2})
            sched["events"].sort(key=lambda e: e["start"])
            hub["schedule_id"] = hub["id"]
            sched_changed.append(hub["id"])
        if offset is not None:
            hub["utc_offset"] = offset
        if mine:
            new = {**mine, "start": first, "end": last, "events": kinds or mine.get("events", "")}
            if new != mine:
                mine.update(new)
                changed = True
                print(f"{mine['id']}: dates now {first} to {last}")
            continue
        doc["events"].append(hub)
        have.add(wid)
        changed = True
        print(f"{hub['id']}: new event page (WTT id {wid}, {first} to {last})")
    return changed


def main():
    today = dt.date.today()
    ev_path = os.path.join(ROOT, "data", "events.json")
    ev_doc = json.load(open(ev_path, encoding="utf-8"))
    events = ev_doc["events"]
    sched0 = json.load(open(os.path.join(ROOT, "data", "schedule.json"), encoding="utf-8"))
    try:
        if auto_hubs(ev_doc, sched0, today):
            if ev_doc.pop("_sched_changed", None):
                sched0["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z")
                with open(os.path.join(ROOT, "data", "schedule.json"), "w", encoding="utf-8") as f:
                    json.dump(sched0, f, ensure_ascii=False, indent=2)
                    f.write("\n")
            ev_doc.pop("_sched_changed", None)
            with open(ev_path, "w", encoding="utf-8") as f:
                json.dump(ev_doc, f, ensure_ascii=False, indent=1)
    except Exception as err:
        print(f"auto event pages: {err}")
    sched_path = os.path.join(ROOT, "data", "schedule.json")
    sched = json.load(open(sched_path, encoding="utf-8"))
    changed = False
    for ev in events:
        if not ev.get("wtt_id") or not ev.get("start"):
            continue
        start, end = dt.date.fromisoformat(ev["start"]), dt.date.fromisoformat(ev["end"])
        if not (start - dt.timedelta(days=3) <= today <= end + dt.timedelta(days=1)):
            continue
        try:
            fx, offset = fixtures(ev)
        except Exception as err:
            print(f"{ev['id']}: schedule unavailable ({err})")
            continue
        if fx:
            sid = ev.get("schedule_id", ev["id"])
            # keep session times and anything not about a single match; WTT's order of play replaces the rest
            keep = [f for f in sched.get("fixtures", []) if f.get("event_id") != sid or (not f["id"].startswith("wtt-") and " v " not in f["name"])]
            new = keep + fx
            if new != sched.get("fixtures"):
                sched["fixtures"] = sorted(new, key=lambda f: f["start"])
                changed = True
            print(f"{ev['id']}: {len(fx)} matches from WTT (UTC{offset:+g})")
        if ev.get("draw"):
            try:
                draws = fetch_draw.fetch_all(ev["draw"], offset if fx else ev.get("utc_offset", 0))   # singles, doubles, mixed and teams
                path = os.path.join(ROOT, "data", "draws", f'{ev["draw"]}.json')
                old = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
                if old.get("events") != draws:
                    data = {"event": ev["name"], "wtt_event_id": ev["draw"], "source": f'https://www.worldtabletennis.com/eventInfo?eventId={ev["draw"]}&selectedTab=Draws',
                            "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z"), "events": draws}
                    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                    print(f"{ev['id']}: draw updated")
            except Exception as err:
                print(f"{ev['id']}: draw unavailable ({err})")
    if changed:
        sched["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z")
        with open(sched_path, "w", encoding="utf-8") as f:
            json.dump(sched, f, ensure_ascii=False, indent=2)
            f.write("\n")
    # Rankings: WTT publishes on Mondays; checking every run is cheap and only writes on change
    try:
        raw = None
        try:   # the top 400 for each list, in pages of 100, from the service behind WTT's rankings page
            raw = [r for ev in ("MS", "WS") for a, b in ((1, 100), (101, 200), (201, 300), (301, 400)) for r in (get(f"{RANKS200}&SubEventCode={ev}&StartRank={a}&EndRank={b}").get("Result") or [])]
            if len({r.get("CurrentRank") for r in raw}) < 300:
                raw = None
        except Exception as err:
            print(f"top 400 unavailable ({err}), using the top 100")
        raw = raw or get(RANKS)
        tmp = os.path.join(ROOT, ".rankings-tmp.json")
        json.dump(raw, open(tmp, "w"))
        before = open(os.path.join(ROOT, "data", "rankings.json"), encoding="utf-8").read() if os.path.exists(os.path.join(ROOT, "data", "rankings.json")) else ""
        rankings.main(tmp)
        os.remove(tmp)
        if open(os.path.join(ROOT, "data", "rankings.json"), encoding="utf-8").read() == before:
            print("rankings unchanged")
    except Exception as err:
        print(f"rankings unavailable ({err})")


if __name__ == "__main__":
    main()
