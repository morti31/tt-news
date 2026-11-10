"""Event pages for past WTT and ITTF events (back to 2021), made from WTT's own records.

  python3 tools/backfill_events.py draws [id ...]   fetch WTT's draws (with every result) into data/draws/<id>.json.
                                                    WTT only answers GitHub's runners, so this step runs in the
                                                    "Backfill draws" workflow, which pushes the files to the
                                                    "backfill" branch for checking before they go on the site.
  python3 tools/backfill_events.py hubs             add an event page (an entry in data/events.json) for every
                                                    event that has a draw file and no page yet. Runs anywhere.
  python3 tools/backfill_events.py list             print what "draws" would fetch.

Which events: every senior WTT Series event (Grand Smash, Finals, Champions, Star Contender, Contender, Feeder), the
World Championships and the continental championships WTT holds records for. Youth, para, veterans and test
events are left out, as are continental cups and the ITTF international opens of 2021.

Pages made here have no venue, map position or written account; add those by hand in data/events.json at any time.
New events are not this script's job: tools/wtt_sync.py makes their pages as they start.
"""
import collections, datetime as dt, glob, json, os, re, sys, unicodedata
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SINCE = 2021
SKIP = re.compile(r"\b(Youth|Junior|Cadet|Hopes|Mini|U-?(1[0-9]|2[01])|Under[- ]?(1[0-9]|2[01])|Para|Veterans?|Masters|Parkinson|TEST(ING)?|SIMULATION|Internal|"
                  r"NOT TO PUBLISH|Qualification|Qual\.|School|University)\b", re.I)
LEVEL = re.compile(r"^WTT (Star Contender|Contender|Feeder|Champions|Cup Finals|Finals)(?: (Men|Women))?\s+(.*)$")
SERIES = {"Star Contender": ("star", "WTT Star Contender"), "Contender": ("contender", "WTT Contender"), "Feeder": ("contender", "WTT Feeder"),
          "Champions": ("champions", "WTT Champions"), "Cup Finals": ("champions", "WTT Finals"), "Finals": ("champions", "WTT Finals")}

# city as WTT writes it (accents dropped, lower case) -> (city, country, time zone)
CITIES = {
    "doha": ("Doha", "Qatar", "Asia/Qatar"), "budapest": ("Budapest", "Hungary", "Europe/Budapest"), "tunis": ("Tunis", "Tunisia", "Africa/Tunis"),
    "lasko": ("Laško", "Slovenia", "Europe/Ljubljana"), "novo mesto": ("Novo Mesto", "Slovenia", "Europe/Ljubljana"),
    "otocec": ("Otočec", "Slovenia", "Europe/Ljubljana"), "nova gorica": ("Nova Gorica", "Slovenia", "Europe/Ljubljana"),
    "ljubljana": ("Ljubljana", "Slovenia", "Europe/Ljubljana"), "singapore": ("Singapore", "Singapore", "Asia/Singapore"),
    "dusseldorf": ("Düsseldorf", "Germany", "Europe/Berlin"), "frankfurt": ("Frankfurt", "Germany", "Europe/Berlin"), "berlin": ("Berlin", "Germany", "Europe/Berlin"),
    "muscat": ("Muscat", "Oman", "Asia/Muscat"), "macao": ("Macao", "China", "Asia/Macau"), "zagreb": ("Zagreb", "Croatia", "Europe/Zagreb"),
    "varazdin": ("Varaždin", "Croatia", "Europe/Zagreb"), "olomouc": ("Olomouc", "Czechia", "Europe/Prague"), "havirov": ("Havířov", "Czechia", "Europe/Prague"),
    "panagyurishte": ("Panagyurishte", "Bulgaria", "Europe/Sofia"), "fremont": ("Fremont", "United States", "America/Los_Angeles"),
    "westchester": ("Westchester", "United States", "America/New_York"), "fort lauderdale": ("Fort Lauderdale", "United States", "America/New_York"),
    "corpus christi": ("Corpus Christi", "United States", "America/Chicago"), "spokane": ("Spokane", "United States", "America/Los_Angeles"),
    "lima": ("Lima", "Peru", "America/Lima"), "almaty": ("Almaty", "Kazakhstan", "Asia/Almaty"), "xinxiang": ("Xinxiang", "China", "Asia/Shanghai"),
    "taiyuan": ("Taiyuan", "China", "Asia/Shanghai"), "durban": ("Durban", "South Africa", "Africa/Johannesburg"), "lagos": ("Lagos", "Nigeria", "Africa/Lagos"),
    "bangkok": ("Bangkok", "Thailand", "Asia/Bangkok"), "goa": ("Goa", "India", "Asia/Kolkata"), "chennai": ("Chennai", "India", "Asia/Kolkata"),
    "vadodara": ("Vadodara", "India", "Asia/Kolkata"), "amman": ("Amman", "Jordan", "Asia/Amman"), "antalya": ("Antalya", "Türkiye", "Europe/Istanbul"),
    "cappadocia": ("Cappadocia", "Türkiye", "Europe/Istanbul"), "istanbul": ("Istanbul", "Türkiye", "Europe/Istanbul"),
    "rio de janeiro": ("Rio de Janeiro", "Brazil", "America/Sao_Paulo"), "biella": ("Biella", "Italy", "Europe/Rome"), "cagliari": ("Cagliari", "Italy", "Europe/Rome"),
    "parma": ("Parma", "Italy", "Europe/Rome"), "vila nova de gaia": ("Vila Nova de Gaia", "Portugal", "Europe/Lisbon"),
    "stockholm": ("Stockholm", "Sweden", "Europe/Stockholm"), "halmstad": ("Halmstad", "Sweden", "Europe/Stockholm"),
    "manchester": ("Manchester", "England", "Europe/London"), "beirut": ("Beirut", "Lebanon", "Asia/Beirut"), "caracas": ("Caracas", "Venezuela", "America/Caracas"),
    "mendoza": ("Mendoza", "Argentina", "America/Argentina/Mendoza"), "buenos aires": ("Buenos Aires", "Argentina", "America/Argentina/Buenos_Aires"),
    "prishtina": ("Prishtina", "Kosovo", "Europe/Belgrade"), "skopje": ("Skopje", "North Macedonia", "Europe/Skopje"),
    "vientiane": ("Vientiane", "Laos", "Asia/Vientiane"), "gdansk": ("Gdańsk", "Poland", "Europe/Warsaw"), "lille": ("Lille", "France", "Europe/Paris"),
    "hennebont": ("Hennebont", "France", "Europe/Paris"), "senec": ("Senec", "Slovakia", "Europe/Bratislava"), "asuncion": ("Asunción", "Paraguay", "America/Asuncion"),
    "ulaanbaatar": ("Ulaanbaatar", "Mongolia", "Asia/Ulaanbaatar"), "tashkent": ("Tashkent", "Uzbekistan", "Asia/Tashkent"), "linz": ("Linz", "Austria", "Europe/Vienna"),
    "puerto princesa": ("Puerto Princesa", "Philippines", "Asia/Manila"), "nagoya": ("Nagoya", "Japan", "Asia/Tokyo"),
    "european summer series": ("Budapest", "Hungary", "Europe/Budapest"),
}
# Events whose names don't follow the "WTT <level> <city> <year>" pattern:
# id -> (name, group, tier, series, city, country, time zone)
SPECIAL = {
    "2345": ("Olympic Games", "Majors", "world", "Olympic Games", "Tokyo", "Japan", "Asia/Tokyo"),
    "2787": ("African Championships", "Continental", "continental", "African Championships", "Tunis", "Tunisia", "Africa/Tunis"),
    "2789": ("Pan American Championships", "Continental", "continental", "Pan American Championships", "Havana", "Cuba", "America/Havana"),
    "2346": ("World Championships", "Majors", "world", "World Championships", "Houston", "United States", "America/Chicago"),
    "2535": ("World Team Championships", "Majors", "world", "World Team Championships", "Chengdu", "China", "Asia/Shanghai"),
    "2660": ("World Championships", "Majors", "world", "World Championships", "Durban", "South Africa", "Africa/Johannesburg"),
    "2860": ("Mixed Team World Cup", "Majors", "world", "Mixed Team World Cup", "Chengdu", "China", "Asia/Shanghai"),
    "2979": ("Mixed Team World Cup", "Majors", "world", "Mixed Team World Cup", "Chengdu", "China", "Asia/Shanghai"),
    "3263": ("Mixed Team World Cup", "Majors", "world", "Mixed Team World Cup", "Chengdu", "China", "Asia/Shanghai"),
    "2536": ("Singapore Smash", "WTT Series", "smash", "WTT Grand Smash", "Singapore", "Singapore", "Asia/Singapore"),
    "2629": ("Singapore Smash", "WTT Series", "smash", "WTT Grand Smash", "Singapore", "Singapore", "Asia/Singapore"),
    "2537": ("WTT Macao", "WTT Series", "champions", "WTT Invitational", "Macao", "China", "Asia/Macau"),
    "2234": ("Pan American Championships", "Continental", "continental", "Pan American Championships", "Lima", "Peru", "America/Lima"),
    "2611": ("Pan American Championships", "Continental", "continental", "Pan American Championships", "Santiago", "Chile", "America/Santiago"),
    "2473": ("African Championships", "Continental", "continental", "African Championships", "Yaoundé", "Cameroon", "Africa/Douala"),
    "2609": ("African Championships", "Continental", "continental", "African Championships", "Algiers", "Algeria", "Africa/Algiers"),
    "2615": ("Oceania Championships", "Continental", "continental", "Oceania Championships", "Melbourne", "Australia", "Australia/Melbourne"),
}
# Dates WTT's records get wrong (they hold only part of the event): id -> (start, end)
DATES = {"2345": ("2021-07-24", "2021-08-06"), "2473": ("2021-09-01", "2021-09-07"), "2615": ("2022-09-05", "2022-09-10")}
# What was played, where the draws WTT holds do not show all of it: id -> text
PLAYED = {"2473": "Teams, singles and doubles", "2615": "Teams, singles and doubles", "2789": "Teams, singles and doubles"}
REGION = {"Pan American Championships": "Americas", "African Championships": "Africa", "Oceania Championships": "Oceania"}
# Ids to try that the match database holds no matches for
EXTRA = ["2345", "2535", "2776", "2787", "2789", "2860", "2979", "3263"]
# The year an event is known by, where it is not the year it was played (the Tokyo 2020 Games were held in 2021)
YEAR = {"2345": "2020"}
KINDS = [("singles", ("men", "women")), ("doubles", ("mdoubles", "wdoubles")), ("mixed doubles", ("mixed",)), ("teams", ("mteam", "wteam", "xteam"))]


def plain(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", plain(s).lower()).strip("-")


def describe(wid, name):
    """What an event is, from its WTT id and name: None for events this script does not make pages for."""
    if wid in SPECIAL:
        nm, group, tier, series, city, country, tz = SPECIAL[wid]
        return {"name": nm, "group": group, "tier": tier, "series": series, "city": city, "country": country, "tz": tz,
                **({"name_year": YEAR[wid]} if wid in YEAR else {})}
    if SKIP.search(name):
        return None
    base = re.sub(r"\s+(presented|powered)\s+by.*$", "", name.strip(), flags=re.I)
    year = re.search(r"\b(20\d\d)\b", base)
    base = re.sub(r"\s*\b20\d\d\b", "", base).strip()
    m = LEVEL.match(base)
    if not m:
        return None
    place = re.sub(r"\s+[IVX]+$", "", m.group(3)).strip()          # "Doha II" is played in Doha
    c = CITIES.get(plain(place).lower())
    if not c:
        return None
    tier, series = SERIES[m.group(1)]
    shown = base.replace(m.group(3), m.group(3).replace(place, c[0])) if plain(place).lower() != "european summer series" else base
    return {"name": shown, "group": "WTT Series", "tier": tier, "series": series, "city": c[0], "country": c[1], "tz": c[2],
            **({"name_year": year.group(1)} if year else {})}


def database():
    known = json.load(open(os.path.join(ROOT, "data", "matches", "events.json"), encoding="utf-8"))
    days = collections.defaultdict(collections.Counter)
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "matches", "20*.json"))):
        if int(os.path.basename(f)[:4]) < SINCE:
            continue
        for m in json.load(open(f, encoding="utf-8")):
            days[m["e"]][(m.get("d") or "")[:10]] += 1
    return known, days


def candidates():
    """[(WTT id, description)] for every event to try, oldest first."""
    known, days = database()
    out = []
    for wid in sorted(set(days) | set(EXTRA), key=int):
        d = describe(wid, (known.get(wid) or {}).get("name") or "")
        if d:
            out.append((wid, d))
    return out


def offset_on(tz, day):
    return dt.datetime.combine(day, dt.time(12), ZoneInfo(tz)).utcoffset().total_seconds() / 3600


def span(daycount):
    """(first, last) day of the busiest run of days: WTT's records sometimes carry a stray match weeks away."""
    ds = sorted(dt.date.fromisoformat(d) for d in daycount if d and d > "2000")
    if not ds:
        return None, None
    runs, cur = [], [ds[0]]
    for d in ds[1:]:
        if (d - cur[-1]).days <= 3:
            cur.append(d)
        else:
            runs.append(cur)
            cur = [d]
    runs.append(cur)
    best = max(runs, key=lambda r: sum(daycount[x.isoformat()] for x in r))
    return best[0], best[-1]


def cmd_draws(ids):
    known, days = database()
    todo = [(w, d) for w, d in candidates() if not ids or w in ids]
    for w in ids:
        if w not in {x for x, _ in todo}:
            print(f"{w}: not an event this script handles")

    def one(job):
        wid, d = job
        path = os.path.join(ROOT, "data", "draws", f"{wid}.json")
        if os.path.exists(path):
            return f"{wid}: have it"
        first, _ = span(days.get(wid, {}))
        info = known.get(wid) or {}
        if not first and (info.get("start") or "") > "2000":
            first = dt.date.fromisoformat(info["start"])
        offset = offset_on(d["tz"], first or dt.date(2023, 6, 1))
        try:
            events = fetch_draw.fetch_all(wid, offset)
        except Exception as err:
            return f"{wid}: {d['name']}: no draw ({err})"
        data = {"event": d["name"], "wtt_event_id": wid, "source": f"https://www.worldtabletennis.com/eventInfo?eventId={wid}&selectedTab=Draws",
                "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z"), "utc_offset": offset, "events": events}
        json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return f"{wid}: {d['name']}: {', '.join(events)}"

    with ThreadPoolExecutor(3) as pool:
        for line in pool.map(one, todo):
            print(line, flush=True)


import fetch_draw


def tidy(draw):
    """Repairs to WTT's older records. Returns True if the draw changed.
    - a result with no winner marked, or (a dozen continental team ties) the wrong one: the winner is the side with more games
    - a third-place match listed as a round: left out, so the final is the last round
    - a draw that is not a knockout (a round robin filed as a "final"), or whose final has no players: left out"""
    changed = False
    for key in list(draw["events"]):
        rounds = draw["events"][key].get("rounds") or []
        kept = [r for r in rounds if r["round"] != "34--"]
        if len(kept) != len(rounds):
            draw["events"][key]["rounds"] = rounds = kept
            changed = True
        for r in rounds:
            for m in r["matches"]:
                sc = re.match(r"(\d+)-(\d+)", m.get("score") or "")
                if sc and sc.group(1) != sc.group(2) and all(m.get("players") or [None]):
                    by_score = 0 if int(sc.group(1)) > int(sc.group(2)) else 1
                    if m.get("winner") != by_score:      # the next round's entrants confirm the score, not the flag
                        m["winner"] = by_score
                        changed = True
                for p in m.get("players") or []:
                    if p and p["name"] in fetch_draw.TEAMS:   # a team WTT left as its country code
                        p["name"] = fetch_draw.TEAMS[p["name"]]
                        changed = True
        fin = rounds[-1] if rounds else None
        ok = fin and fin["round"] == "Final" and len(fin["matches"]) == 1 and all(fin["matches"][0].get("players") or [None]) \
            and not any("Unknown" in p["name"] for p in fin["matches"][0]["players"])
        if not ok:
            del draw["events"][key]
            changed = True
    return changed


def cmd_hubs():
    known, days = database()
    path = os.path.join(ROOT, "data", "events.json")
    doc = json.load(open(path, encoding="utf-8"))
    have = {str(x) for ev in doc["events"] for x in (ev.get("wtt_id"), ev.get("draw")) if x}
    ids = {ev["id"] for ev in doc["events"]}
    made = []
    for wid, d in candidates():
        dpath = os.path.join(ROOT, "data", "draws", f"{wid}.json")
        if wid in have or not os.path.exists(dpath):
            continue
        draw = json.load(open(dpath, encoding="utf-8"))
        if tidy(draw):
            json.dump(draw, open(dpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if not draw["events"]:
            print(f"{wid}: {d['name']}: no knockout draw in WTT's records, left out")
            continue
        offset = draw.get("utc_offset")
        count = collections.Counter(days.get(wid, {}))
        for ev in draw["events"].values():
            for rd in ev.get("rounds", []):
                for m in rd["matches"]:
                    if m.get("when"):
                        local = dt.datetime.fromisoformat(m["when"].replace("Z", "+00:00")) + dt.timedelta(hours=offset or 0)
                        count[local.date().isoformat()] += 1
        first, last = span(count)
        if not first:
            print(f"{wid}: {d['name']}: no dates, left out")
            continue
        # A draw holds the knockout rounds only. Where the match database has nothing either (team events with a
        # group stage), WTT's own dates for the event are the better guide.
        info = known.get(wid) or {}
        if not days.get(wid) and (info.get("start") or "") > "2000" and (info.get("end") or "") > "2000":
            a, b = dt.date.fromisoformat(info["start"]), dt.date.fromisoformat(info["end"])
            if 0 <= (b - a).days <= 16 and a <= first and b >= last:
                first, last = a, b
        if wid in DATES:
            first, last = (dt.date.fromisoformat(x) for x in DATES[wid])
        year = d.get("name_year") or str(first.year)
        hid = f'{slug(d["name"])}-{year}'
        if hid in ids:                      # two events of the same name in a year (Muscat 2022): the later one carries its month
            hid = f"{hid}-{first:%B}".lower()
        ids.add(hid)
        kinds = [k for k, keys in KINDS if any(x in draw["events"] for x in keys)]
        if kinds == ["teams"]:
            text = "Mixed team" if set(draw["events"]) == {"xteam"} else "Men's and women's teams"
        elif kinds == ["singles"]:
            text = "Men's and women's singles"
        elif "teams" in kinds:
            text = "Teams, singles and doubles"
        else:
            text = (", ".join(kinds[:-1]) + " and " + kinds[-1]) if len(kinds) > 1 else (kinds[0] if kinds else "")
            text = text[:1].upper() + text[1:]
        text = PLAYED.get(wid, text)
        hub = {"id": hid, "name": d["name"], "group": d["group"], "tier": d["tier"], "series": d["series"],
               **({"level": d["series"]} if d["series"] in ("WTT Feeder", "WTT Contender", "WTT Invitational") else {}),
               "city": d["city"], "country": d["country"], "year": year, "start": first.isoformat(), "end": last.isoformat(), "events": text,
               **({"region": REGION[d["series"]]} if d["series"] in REGION else {}), "draw": wid, "wtt_id": wid, "utc_offset": offset if offset is not None else 0}
        if hub["utc_offset"] == int(hub["utc_offset"]):
            hub["utc_offset"] = int(hub["utc_offset"])
        doc["events"].append(hub)
        made.append(hub)
        print(f'{hid}: {first} to {last}, {text}')
    if made:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"{len(made)} event pages added")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "draws":
        cmd_draws(set(sys.argv[2:]))
    elif cmd == "hubs":
        cmd_hubs()
    else:
        have = {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(ROOT, "data", "draws", "*.json"))}
        for wid, d in candidates():
            print(wid, "have" if wid in have else "    ", d["name"], d.get("name_year", ""), "|", d["city"], d["country"], "|", d["series"])
