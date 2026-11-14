"""Why players' world ranking points change: from WTT's ranking breakdowns (data/ranking-breakdown.json, written each
Tuesday by tools/ranking_breakdown.py) and last week's copy (data/ranking-breakdown-prev.json).

  changes(pid)   points gained and lost since last week, by event, biggest first
  dropping(pid)  counted results that expire in the next four weeks
Used by the rankings page, player profiles and the weekly rankings brief for the news runs."""
import datetime as dt, json, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _load(name):
    p = os.path.join(ROOT, "data", name)
    try:
        return json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


CUR, PREV = _load("ranking-breakdown.json"), _load("ranking-breakdown-prev.json")
RANKS = _load("rankings.json")


def short(name):
    """'WTT Champions Frankfurt 2026 Presented by X' -> 'WTT Champions Frankfurt 2026'; long official names shortened."""
    n = re.sub(r"\s+(Presented|Powered) [Bb]y.*$", "", name or "").strip()
    n = n.replace("ITTF World Team Table Tennis Championships Finals", "World Team Championships")
    n = re.sub(r"^ITTF[- ]+", "", n).replace("ATTU ", "").replace("ETTU ", "")
    n = n.replace("Men’s & Women’s World Cup", "World Cup").replace("Men's & Women's World Cup", "World Cup")
    return n


def compact(name):
    """For tight spaces: 'WTT Feeder Vila Nova de Gaia 2026' -> 'Feeder Vila Nova de Gaia'."""
    n = re.sub(r"\s+20\d\d\s*$", "", short(name)).strip()
    return re.sub(r"^WTT ", "", n)


def _expiry(x):
    try:
        return dt.datetime.strptime((x.get("expires") or "")[:10], "%m/%d/%Y").date()
    except ValueError:
        return None


def _counted(entry):
    return {x["event_id"]: x for x in (entry or {}).get("events", []) if x.get("counted")}


def changes(pid):
    """[(points, event)] gained (+) and lost (-) since last week's breakdown. Without last week's copy, only results
    added in the current ranking week count as gains."""
    cur = CUR.get(pid)
    if not cur:
        return []
    now = _counted(cur)
    prev_entry = PREV.get(pid)
    out = []
    if prev_entry and prev_entry.get("week") != cur.get("week"):
        before = _counted(prev_entry)
        for k, x in now.items():
            d = (x.get("points") or 0) - (before.get(k, {}).get("points") or 0)
            if d:
                out.append((d, short(x["event"])))
        for k, x in before.items():
            if k not in now and x.get("points"):
                out.append((-x["points"], short(x["event"])))
    else:
        wk = RANKS.get("week")
        yr = int(str(RANKS.get("date", "0000"))[:4]) if RANKS.get("date") else None
        for x in now.values():
            if x.get("week") == wk and x.get("year") == yr and x.get("points"):
                out.append((x["points"], short(x["event"])))
    return sorted(out, key=lambda t: -abs(t[0]))


def dropping(pid, weeks=4):
    """[(date, points, event)] counted results that drop off within `weeks` of this ranking."""
    cur = CUR.get(pid)
    if not cur or not RANKS.get("date"):
        return []
    start = dt.date.fromisoformat(RANKS["date"])
    out = []
    for x in _counted(cur).values():
        d = _expiry(x)
        if d and start < d <= start + dt.timedelta(weeks=weeks) and x.get("points"):
            out.append((d, x["points"], short(x["event"])))
    return sorted(out)


def day(d):
    return f"{d.day} {d:%b}"


def brief(top=100):
    """The weekly rankings brief for the news runs: big movers in the top 100 with the reasons, and points that the top 20
    must defend in the next four weeks."""
    out = {"week": RANKS.get("label"), "movers": [], "defending": []}
    for g in ("women", "men"):
        for p in RANKS.get(g, [])[:top]:
            if p.get("prev") and abs(p["prev"] - p["rank"]) >= 3:
                out["movers"].append({"gender": g, "name": p["name"], "nat": p["nat"], "rank": p["rank"], "prev": p["prev"],
                                      "points": p["points"], "why": [f"{pts:+,} {ev}" for pts, ev in changes(p["ittf_id"])[:3]]})
        for p in RANKS.get(g, [])[:20]:
            drops = dropping(p["ittf_id"])
            if drops:
                out["defending"].append({"gender": g, "name": p["name"], "nat": p["nat"], "rank": p["rank"], "points": p["points"],
                                         "drops": [{"date": d.isoformat(), "points": pts, "event": ev} for d, pts, ev in drops]})
    out["movers"].sort(key=lambda m: -abs(m["prev"] - m["rank"]))
    return out
