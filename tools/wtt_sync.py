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
HEADERS = {"Origin": "https://www.worldtabletennis.com", "Referer": "https://www.worldtabletennis.com/", "User-Agent": "Mozilla/5.0 (Eleven)"}
FAMILY_FIRST = fetch_draw.FAMILY_FIRST


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as r:
        return json.load(r)


def person(comp):
    """'AN Jaehyun' + KOR -> 'An Jaehyun'; 'LEBRUN Felix' + FRA -> 'Félix Lebrun'."""
    if not comp:
        return None
    d = comp.get("Description") or {}
    org = comp.get("Organization", "")
    words = (d.get("TeamName") or "").split()
    fam = " ".join(fetch_draw.cap(w) for w in words if w.isupper())
    giv = " ".join(w for w in words if not w.isupper())
    name = f"{fam} {giv}" if org in FAMILY_FIRST else f"{giv} {fam}"
    return fetch_draw.FIXES.get(name.strip(), name.strip())


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
                    "source": f"https://www.worldtabletennis.com/eventInfo?eventId={wid}", **({"detail": table} if table else {})})
    return sorted(out, key=lambda f: f["start"]), offset


def main():
    today = dt.date.today()
    events = json.load(open(os.path.join(ROOT, "data", "events.json"), encoding="utf-8"))["events"]
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
                draws = {k: {"name": label, "rounds": fetch_draw.convert(fetch_draw.fetch(ev["draw"], code), offset if fx else ev.get("utc_offset", 0))}
                         for k, (label, code) in fetch_draw.SUBEVENTS.items()}
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
        raw = get(RANKS)
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
