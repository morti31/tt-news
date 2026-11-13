"""Where each ranked player's ITTF world ranking points come from: the events counted towards their total.

WTT's ranking service (the one behind the breakdown on worldtabletennis.com player pages) answers only with the
website's access key, which WTT allows Eleven to use; it is read from the site's current script on every run, so a
new key is picked up on its own. Writes data/ranking-breakdown.json: {ittf_id: {"week": ..., "events": [...]}}.
Run weekly from GitHub Actions (the API is not reachable from everywhere): python3 tools/ranking_breakdown.py
"""
import json, os, re, sys, time, urllib.request, concurrent.futures as cf

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = "https://www.worldtabletennis.com"
API = "https://wttcmsapigateway-new.azure-api.net/internalttu/Rankings/GetRankingPointsBreakdown_FullList"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def fetch(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Origin": SITE, "Referer": SITE + "/", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def site_key():
    page = fetch(SITE + "/playerDescription?playerId=1")
    main = re.search(r'src="(main\.[0-9a-f]+\.js)"', page).group(1)
    return re.search(r'ttu_apikey:"([^"]+)"', fetch(f"{SITE}/{main}")).group(1)


def breakdown(key, pid, code, wk):
    q = (f"?OrganizationCode=WTT&CategoryCode=SEN&RankingCategoryCode={code}&RankingYear={wk['y']}&RankingMonth={wk['m']}"
         f"&RankingWeek={wk['w']}&PlayerID={pid}")
    last = None
    for attempt in range(3):
        try:
            return json.loads(fetch(API + q, {"ApiKey": key})).get("Result") or []
        except Exception as err:
            last = err
            time.sleep(2 + 3 * attempt)
    print(f"{pid}: {last}")
    return None


def main():
    import switches
    if not switches.on("wtt"):
        print("WTT data is switched off (data/switches.json)")
        return
    rk = json.load(open(os.path.join(ROOT, "data", "rankings.json"), encoding="utf-8"))
    y, m, _ = rk["date"].split("-")
    wk = {"y": int(y), "m": int(m), "w": int(rk["week"])}
    key = site_key()
    jobs = [(p["ittf_id"], code) for g, code in (("men", "MS"), ("women", "WS")) for p in rk.get(g, []) if p.get("ittf_id")]
    if len(sys.argv) > 1:
        jobs = [j for j in jobs if j[0] in sys.argv[1:]]
    path = os.path.join(ROOT, "data", "ranking-breakdown.json")
    out = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    ok = 0
    with cf.ThreadPoolExecutor(6) as ex:
        for (pid, code), res in zip(jobs, ex.map(lambda j: breakdown(key, j[0], j[1], wk), jobs)):
            if res is None:
                continue
            out[pid] = {"week": rk["label"], "events": [{"event_id": str(x.get("EventId")), "event": x.get("EventName"), "result": x.get("ResultPosition"),
                                                        "points": x.get("RankingPoints"), "counted": bool(x.get("isbestofx")),
                                                        "order": x.get("bestofxorder"), "year": x.get("RankingYear"), "week": x.get("RankingWeek"),
                                                        "expires": x.get("ExpiryDate")} for x in res]}
            ok += 1
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"ranking breakdown: {ok} of {len(jobs)} players")


if __name__ == "__main__":
    main()
