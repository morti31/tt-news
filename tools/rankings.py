"""Converts the official ITTF world ranking (as published by WTT) into data/rankings.json.

The data file is https://wtt-web-frontdoor-withoutcache-cqakg0andqf5hchn.a01.azurefd.net/ranking/SEN_SINGLES.json
(top 100 per event). Save it to a local file and run:

    python3 tools/rankings.py <saved SEN_SINGLES.json>

It writes data/rankings.json (top 100 men and women) and refreshes the top 10 in data/news.json,
so the sidebar and the rankings page always come from the same list.
"""
import json, os, sys, datetime as dt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_draw import FIXES, cap  # same spellings as the draws


def name(raw):
    words = raw.split()
    caps = [w for w in words if w.upper() == w and any(c.isalpha() for c in w)]
    family = " ".join(cap(w) for w in caps)
    given = " ".join(w for w in words if w not in caps)
    full = f"{family} {given}" if words and words[0] in caps else f"{given} {family}"
    full = full.strip()
    return FIXES.get(full, full)


def convert(rows):
    out = {"men": [], "women": []}
    week = pub = None
    for r in rows:
        key = {"MS": "men", "WS": "women"}.get(r.get("SubEventCode"))
        if not key:
            continue
        week = r.get("RankingWeek") or week
        pub = r.get("PublishDate") or pub
        prev = int(r["PreviousRank"]) if (r.get("PreviousRank") or "").isdigit() else None
        out[key].append({"rank": int(r["CurrentRank"]), "prev": prev, "name": name(r["PlayerName"]), "nat": r["CountryCode"],
                         "points": int(r["RankingPointsYTD"] or 0), "ittf_id": r.get("IttfId")})
    for k in out:
        out[k].sort(key=lambda p: p["rank"])
    d = dt.datetime.strptime(pub.split()[0], "%m/%d/%Y").date()
    return {"week": int(week), "date": d.isoformat(), "label": f"ITTF world ranking, week {week}, {d.day} {d:%B %Y}",
            "url": "https://www.worldtabletennis.com/rankings", **out}


def main(path):
    raw = json.load(open(path, encoding="utf-8"))
    rows = raw if isinstance(raw, list) else [x for v in raw.values() if isinstance(v, list) for x in v]
    data = convert(rows)
    json.dump(data, open(os.path.join(ROOT, "data", "rankings.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    news_path = os.path.join(ROOT, "data", "news.json")
    news = json.load(open(news_path, encoding="utf-8"))
    news["rankings"] = {"week": data["label"], "url": data["url"],
                        **{k: [{"name": p["name"], "nat": p["nat"], "points": p["points"], "prev": p["prev"]} for p in data[k][:10]] for k in ("men", "women")}}
    with open(news_path, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"rankings: {data['label']}, {len(data['men'])} men, {len(data['women'])} women")


if __name__ == "__main__":
    main(sys.argv[1])
