"""Stub profiles for every ranked player without one.

    python3 tools/stubs.py

For each player in data/rankings.json (the top 400 men and women) and the doubles rankings (top 200 pairs) with no file in data/players, writes
data/players/<slug>.json with what WTT's records give: name, association, gender, date of birth and playing hand
(from data/players/wtt.json, filled by tools/match_sync.py). The file is marked "stub": true; the monthly profile
check fills stubs in, highest-ranked first. Never removes a profile. Every ranked player gets a file, whatever their age
(tools/people.py gives everyone in the rankings a page).
"""
import datetime as dt, glob, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import people

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDIR = os.path.join(ROOT, "data", "players")


def main():
    R = json.load(open(os.path.join(ROOT, "data", "rankings.json"), encoding="utf-8"))
    wtt = json.load(open(os.path.join(PDIR, "wtt.json"), encoding="utf-8"))
    have, slugs = set(), set()
    for f in glob.glob(os.path.join(PDIR, "*.json")):
        if os.path.basename(f) in ("wtt.json", "wanted.json"):
            continue
        have.add(json.load(open(f, encoding="utf-8")).get("ittf_id"))
        slugs.add(os.path.basename(f)[:-5])
    made = []
    for g, gender in (("men", "M"), ("women", "W")):
        for p in R[g]:
            pid = p.get("ittf_id")
            if not pid or pid in have:
                continue
            w = wtt.get(pid) or {}
            born = people.wtt_born(w.get("dob"))
            slug = people.slugify(p["name"])
            if slug in slugs:
                slug = f"{slug}-{p['nat'].lower()}"
            hand = {"Right Hand": "Right", "Left Hand": "Left"}.get(w.get("hand") or "")
            doc = {"name": p["name"], "ittf_id": pid, "nat": p["nat"], "gender": gender, **({"born": born} if born else {}),
                   **({"hand": hand} if hand else {}), "clubs": [], "honours": [],
                   "sources": [f"https://www.worldtabletennis.com/playerDescription?playerId={pid}"],
                   "checked": dt.date.today().isoformat(), "stub": True}
            json.dump(doc, open(os.path.join(PDIR, slug + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            slugs.add(slug)
            have.add(pid)
            made.append(f'{p["rank"]:>3} {g:5} {p["name"]}{"" if born else " (no date of birth yet)"}')
    # and everyone in the doubles world rankings (tools/doubles.py)
    import doubles
    for pid, d in doubles.players(singles=R).items():
        if pid in have:
            continue
        w = wtt.get(pid) or {}
        born = people.wtt_born(w.get("dob"))
        slug = people.slugify(d["name"])
        if slug in slugs:
            slug = f"{slug}-{d['nat'].lower()}"
        hand = {"Right Hand": "Right", "Left Hand": "Left"}.get(w.get("hand") or "")
        doc = {"name": d["name"], "ittf_id": pid, "nat": d["nat"], **({"gender": d["gender"]} if d["gender"] else {}), **({"born": born} if born else {}),
               **({"hand": hand} if hand else {}), "clubs": [], "honours": [],
               "sources": [f"https://www.worldtabletennis.com/playerDescription?playerId={pid}"],
               "checked": dt.date.today().isoformat(), "stub": True}
        json.dump(doc, open(os.path.join(PDIR, slug + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        slugs.add(slug)
        have.add(pid)
        best = min(pr["rank"] for _, pr in d["pairs"])
        made.append(f'{best:>3} doubles {d["name"]}{"" if born else " (no date of birth yet)"}')
    print("\n".join(made))
    print(f"{len(made)} stub profiles written")


if __name__ == "__main__":
    main()
