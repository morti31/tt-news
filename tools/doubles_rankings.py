"""The ITTF doubles world rankings (men's, women's and mixed), from WTT's ranking service, into data/doubles-rankings.json.

Uses the same website key as tools/ranking_breakdown.py (WTT allows Eleven to use its data). Run from GitHub Actions:
python3 tools/doubles_rankings.py [--sample]"""
import json, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from ranking_breakdown import fetch, SITE, ROOT

API = "https://wttcmsapigateway-new.azure-api.net/internalttu/RankingsCurrentWeek/CurrentWeek/"


def key():
    page = fetch(SITE + "/playerDescription?playerId=1")
    main = re.search(r'src="(main\.[0-9a-f]+\.js)"', page).group(1)
    return re.search(r'ittfapikey:"([^"]+)"', fetch(f"{SITE}/{main}")).group(1)


def call(k, what, **params):
    try:
        d = json.loads(fetch(API + what + "?" + urllib.parse.urlencode(params), {"ApiKey": k}))
        return d.get("Result") or []
    except Exception as err:
        print(what, params, err)
        return []


def main():
    import switches
    if not switches.on("wtt"):
        print("WTT data is switched off (data/switches.json)")
        return
    k = key()
    if "--sample" in sys.argv:
        for what in ("GetRankingPairs", "GetRankingIndividuals"):
            for ev in ("MD", "XD"):
                r = call(k, what, CategoryCode="SEN", SubEventCode=ev, StartRank=1, EndRank=3)
                print(what, ev, json.dumps(r, ensure_ascii=False)[:1500])
        return
    from rankings import name as nice
    out = {}
    pub = week = None
    for ev in ("WD", "MD", "XD"):
        rows = []
        for a, b in ((1, 100), (101, 200)):
            rows += call(k, "GetRankingPairs", CategoryCode="SEN", SubEventCode=ev, StartRank=a, EndRank=b)
        lst, seen = [], set()
        for r in rows:
            if r.get("PairId") in seen or not str(r.get("CurrentRank") or "").isdigit():
                continue
            seen.add(r.get("PairId"))
            pub, week = r.get("PublishDate") or pub, r.get("RankingWeek") or week
            prev = int(r["PreviousRank"]) if str(r.get("PreviousRank") or "").isdigit() else None
            players = [{"name": nice(r.get(f"PlayerName{s_}") or ""), "nat": r.get(f"CountryCode{s_}") or "", "ittf_id": r.get(f"IttfId{s_}")}
                       for s_ in ("1", "1d") if r.get(f"PlayerName{s_}")]
            lst.append({"rank": int(r["CurrentRank"]), "prev": prev, "points": int(float(r.get("Points") or 0)), "pair_id": r.get("PairId"), "players": players})
        lst.sort(key=lambda x: x["rank"])
        out[{"WD": "women", "MD": "men", "XD": "mixed"}[ev]] = lst
    if not all(len(out[x]) >= 50 for x in ("women", "men", "mixed")):
        print("doubles rankings: too few pairs returned, keeping the old file", {k: len(v) for k, v in out.items()})
        return
    import datetime as dt
    d = dt.datetime.strptime(pub.split()[0], "%m/%d/%Y").date()
    doc = {"week": int(week), "date": d.isoformat(), "label": f"ITTF doubles world ranking, week {week}, {d.day} {d:%B %Y}",
           "url": "https://www.worldtabletennis.com/rankings", **out}
    json.dump(doc, open(os.path.join(ROOT, "data", "doubles-rankings.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("doubles rankings:", doc["label"], {k: len(v) for k, v in out.items()})


if __name__ == "__main__":
    main()
