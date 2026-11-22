"""Add the league table, as it stands now, to a club story or article (UPDATE.md, "League tables in league stories").

Usage: python3 tools/league_table.py <story id or article slug> <competition> ["as of" line] [--round "Matchday 9"]
  competition: a file name in data/clubs, e.g. ttbl, dttbl-women, tleague-men, tleague-women, proa-men, proa-women,
               cl-men, cl-women, cttsl-men, cttsl-women, mltt, bcl-men, bcl-women, utt
Example: python3 tools/league_table.py ttbl-2026-27-matchday-9-ionescu-beats-fan-zhendong ttbl "After Sunday's matches, 22 November"

The table and every match of the round (results so far, and the matches still to play with their times) are copied into the story ("league_table") so the page keeps showing it as it stood that day; the build
shows it after the article text with a link to the league page for the latest one. Run it after updating the
league's file, for every league result story (full article or quick update).
"""
import json, os, sys, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAGE = {"ttbl": "bundesliga", "dttbl-women": "bundesliga", "tleague-men": "t-league", "tleague-women": "t-league",
        "proa-men": "pro-a", "proa-women": "pro-a", "cl-men": "champions-league", "cl-women": "champions-league",
        "cttsl-men": "super-league", "cttsl-women": "super-league", "mltt": "mltt", "bcl-men": "british-league",
        "bcl-women": "british-league", "utt": "utt"}
LABEL = {"ttbl": "Tischtennis Bundesliga table", "dttbl-women": "Women's Bundesliga table", "tleague-men": "T.League men's table",
         "tleague-women": "T.League women's table", "proa-men": "Pro A men's table", "proa-women": "Pro A women's table",
         "cl-men": "Champions League men's table", "cl-women": "Champions League women's table",
         "cttsl-men": "China Super League men's table", "cttsl-women": "China Super League women's table",
         "mltt": "Major League Table Tennis table", "bcl-men": "British League men's table", "bcl-women": "British League women's table",
         "utt": "Ultimate Table Tennis table"}


def round_of(d, rnd=None):
    """Every match of one round: the round named, else the round of the most recent result."""
    ms = d.get("matches") or []
    if not rnd:
        done = sorted((m for m in ms if m.get("status") == "finished" and m.get("round")), key=lambda m: m.get("when") or "")
        rnd = done[-1]["round"] if done else None
    keep = ("when", "home", "away", "score", "status", "round", "date_only", "tbc")
    if not rnd:   # leagues without round names: the matches within three days of the latest result
        done = sorted((m for m in ms if m.get("status") == "finished" and m.get("when")), key=lambda m: m["when"])
        if not done:
            return None
        import datetime as dt
        last = dt.date.fromisoformat(done[-1]["when"][:10])
        near = lambda m: m.get("when") and abs((dt.date.fromisoformat(m["when"][:10]) - last).days) <= 3
        sel = [{k: m[k] for k in keep if m.get(k) is not None} for m in ms if near(m)]
        return {"name": "This weekend's matches", "matches": sorted(sel, key=lambda m: m["when"])} if sel else None
    keep = ("when", "home", "away", "score", "status", "round", "date_only", "tbc")
    sel = [{k: m[k] for k in keep if m.get(k) is not None} for m in ms if m.get("round") == rnd]
    return {"name": rnd, "matches": sorted(sel, key=lambda m: m.get("when") or "")} if sel else None


def snapshot(comp, as_of=None, rnd=None):
    d = json.load(open(os.path.join(ROOT, "data", "clubs", comp + ".json"), encoding="utf-8"))
    tab = d.get("table") or {}
    if not [g for g in tab.get("groups") or [] if g.get("rows")]:
        raise SystemExit(f"{comp} has no table yet")
    return {"comp": comp, "label": LABEL.get(comp, "League table"), "as_of": as_of or f"As it stood on {d.get('updated', '')[:10]}",
            "page": f"/clubs/{PAGE.get(comp, '')}.html" if PAGE.get(comp) else None, "table": tab, "round": round_of(d, rnd)}


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    args = sys.argv[1:]
    rnd = None
    if "--round" in args:
        i = args.index("--round")
        rnd = args[i + 1]
        del args[i:i + 2]
    ident, comp = args[0], args[1]
    lt = snapshot(comp, args[2] if len(args) > 2 else None, rnd)
    done = False
    for f in glob.glob(os.path.join(ROOT, "data", "articles", "*.json")):
        a = json.load(open(f, encoding="utf-8"))
        if a.get("slug") == ident or a.get("story_id") == ident:
            a["league_table"] = lt
            json.dump(a, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("table added to article", a["slug"])
            done = True
    if not done:
        path = os.path.join(ROOT, "data", "news.json")
        n = json.load(open(path, encoding="utf-8"))
        for s in n["stories"]:
            if s["id"] == ident:
                s["league_table"] = lt
                done = True
                print("table added to story", ident)
        if done:
            json.dump(n, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            open(path, "a").write("\n")
    if not done:
        raise SystemExit(f"no article or story called {ident}")


if __name__ == "__main__":
    main()
