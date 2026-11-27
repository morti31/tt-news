"""Gives every WTT event on the schedule an event page.

The events page lists data/events.json hubs; the schedule page lists data/schedule.json. They were two lists
kept in step by hand (the monthly task), so an event on the schedule could be missing from the events page
(WTT Champions Shanghai was). This adds a hub to data/events.json for each upcoming WTT Feeder, Contender,
Star Contender, Champions or Finals event on the schedule that has none and a known city, and keeps the
dates, city and venue of existing hubs in line with the schedule. Posters are drawn afterwards by
tools/posters.py --missing (the sync-hubs workflow does both). Prints the number of changes.
"""
import json, os, re, datetime as dt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TIER = {"WTT Feeder": "contender", "WTT Contender": "contender", "WTT Star Contender": "star", "WTT Champions": "champions", "Season finals": "champions"}
EVENTS = {"WTT Champions": "Men's and women's singles", "Season finals": "Men's and women's singles"}


def main():
    sp, ep = os.path.join(ROOT, "data", "schedule.json"), os.path.join(ROOT, "data", "events.json")
    sched = json.load(open(sp, encoding="utf-8"))["events"]
    raw = open(ep, encoding="utf-8").read()
    doc = json.loads(raw)
    hubs = doc["events"]
    have = {h["id"] for h in hubs} | {h.get("schedule_id") for h in hubs}
    coords = {h["city"]: h["coords"] for h in hubs if h.get("coords") and h.get("city")}
    today = dt.date.today().isoformat()
    added, changed = [], 0
    for s in sorted(sched, key=lambda x: x["start"]):
        if s.get("series") != "WTT" or s.get("type") not in TIER or s["end"] < today:
            continue
        city = (s.get("city") or "").strip()
        if s["id"] in have:
            h = next(h for h in hubs if h["id"] == s["id"] or h.get("schedule_id") == s["id"])
            for k_h, k_s in (("start", "start"), ("end", "end")):
                if h.get("auto") is None and h.get(k_h) != s[k_s] and not h.get("dates_text"):
                    h[k_h] = s[k_s]; changed += 1
            continue
        if not city or "announced" in city.lower() or "tbc" in city.lower():
            continue   # no host yet: added once the schedule names a city
        hub = {"id": s["id"], "schedule_id": s["id"], "name": s["name"], "group": "WTT Series", "tier": TIER[s["type"]], "series": s["type"] if s["type"] != "Season finals" else "WTT Finals",
               "city": city, "country": s.get("country", ""), **({"venue": s["venue"]} if s.get("venue") else {}), "year": s["start"][:4], "start": s["start"], "end": s["end"],
               "events": EVENTS.get(s["type"], "Singles, doubles and mixed doubles"), **({"coords": coords[city]} if city in coords else {})}
        hubs.append(hub); added.append(hub["id"])
    if added or changed:
        text = json.dumps(doc, ensure_ascii=False, indent=1)
        open(ep, "w", encoding="utf-8").write(text if not raw.startswith('{\n "') else text)
    print(len(added) + changed)
    for a in added:
        print("added", a)


if __name__ == "__main__":
    main()
