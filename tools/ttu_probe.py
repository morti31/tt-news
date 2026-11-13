"""Probe WTT's player-match service (behind worldtabletennis.com player pages) for one player: prints the reply.
Usage (GitHub Actions only): python3 tools/ttu_probe.py <ittf id>"""
import json, re, sys, urllib.request
sys.path.insert(0, __import__("os").path.dirname(__file__))
from ranking_breakdown import fetch, SITE


def keys():
    page = fetch(SITE + "/playerDescription?playerId=1")
    main = re.search(r'src="(main\.[0-9a-f]+\.js)"', page).group(1)
    js = fetch(f"{SITE}/{main}")
    return re.search(r'ittfapikey:"([^"]+)"', js).group(1)


k = keys()
pid = sys.argv[1]
url = f"https://wttcmsapigateway-new.azure-api.net/ttu/Matches/GetRankingHistoryMatchesIndividuals?IttfId={pid}&CategoryCode=SEN&StartRowNo=0&EndRowNo=40"
try:
    print(fetch(url, {"ApiKey": k})[:20000])
except Exception as err:
    print("ERR", err)
