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


if __name__ == "__main__":
    main()
