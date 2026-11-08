"""Eleven's club league database: every tie and rubber in the leagues we cover, from the leagues' own sites.

Runs on GitHub Actions (.github/workflows/league-sync.yml), nightly, and commits
  data/leagues/<league>/<season>.json   {"league", "season", "updated", "ties": [tie, ...]}
  data/leagues/<league>/players.json    league player id -> {"name": "Given FAMILY", "nat"?: "JPN"}

A tie: {"id", "d": UTC start (ISO), "g": "M" or "W", "rd": round label, "home", "away", "s": [home, away],
        "st": "done" | "live" | "due", "venue"?, "crowd"?, "url": the league's own match page,
        "r": [rubber, ...]}
A rubber: {"k": "S" or "D", "p": [[home player ids], [away player ids]], "s": [games home, games away],
           "g": "11-7,9-11,..." (home first), "w": 0 or 1}

Sources (all official, public pages; no odds or betting data, ever):
  ttbl     Tischtennis Bundesliga, ttbl.de (the page's own JSON data)
  tleague  Nojima T.League, tleague.jp (match pages; romanised names from the player pages)

Usage: python3 tools/league_sync.py                   nightly: current season of every league
       python3 tools/league_sync.py --backfill ttbl   every season the league site has
       python3 tools/league_sync.py --backfill tleague
"""
import json, os, re, sys, time, html, datetime as dt, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LDIR = os.path.join(ROOT, "data", "leagues")
UA = "Mozilla/5.0 (Eleven table tennis news; results database)"


def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-GB,en;q=0.8"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None
            if i == tries - 1:
                raise
        except Exception:
            if i == tries - 1:
                raise
        time.sleep(3 * (i + 1))


def load(path, default):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def merge(league, season, ties):
    path = os.path.join(LDIR, league, f"{season}.json")
    old = {t["id"]: t for t in load(path, {"ties": []})["ties"]}
    for t in ties:
        old[t["id"]] = t
    out = sorted(old.values(), key=lambda t: (t["d"] or "", t["id"]))
    save(path, {"league": league, "season": season, "updated": now(), "ties": out})
    return len(out)


# ---------------------------------------------------------------- TTBL (Germany)
TTBL = "https://www.ttbl.de"


def next_data(page):
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page or "", re.S)
    return json.loads(m.group(1))["props"]["pageProps"] if m else None


def ttbl_name(p):
    return f'{p.get("firstName", "").strip()} {p.get("lastName", "").strip().upper()}'.strip()


def ttbl_tie(season, gd, m, players):
    d = next_data(fetch(f"{TTBL}/bundesliga/gameday/{season}/{gd}/{m['id']}"))
    sm = (d or {}).get("selectedMatch") or {}
    state = {"Finished": "done", "Live": "live"}.get(sm.get("matchState") or m.get("matchState"), "due")
    rubbers = []
    for g in sm.get("games") or []:
        if g.get("gameState") != "Finished":
            continue
        if g.get("homePlayer"):
            sides = [[g["homePlayer"]], [g["awayPlayer"]]]
            k = "S"
        elif g.get("homeDouble"):
            sides = [[g["homeDouble"]["leaguePlayerOne"], g["homeDouble"]["leaguePlayerTwo"]],
                     [g["awayDouble"]["leaguePlayerOne"], g["awayDouble"]["leaguePlayerTwo"]]]
            k = "D"
        else:
            continue
        for side in sides:
            for p in side:
                players[p["id"]] = {"name": ttbl_name(p)}
        games = []
        for n in range(1, 6):
            a, b = g.get(f"set{n}HomeScore"), g.get(f"set{n}AwayScore")
            if a is None or b is None:
                break
            games.append(f"{a}-{b}")
        rubbers.append({"k": k, "p": [[p["id"] for p in sides[0]], [p["id"] for p in sides[1]]],
                        "s": [g.get("homeSets") or 0, g.get("awaySets") or 0], "g": ",".join(games),
                        "w": 0 if g.get("winnerSide") == "Home" else 1})
    ht, at = sm.get("homeTeam") or m.get("homeTeam") or {}, sm.get("awayTeam") or m.get("awayTeam") or {}
    tie = {"id": m["id"], "d": dt.datetime.fromtimestamp(m["timeStamp"], dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if m.get("timeStamp") else None,
           "g": "M", "rd": f"Matchday {gd}", "home": ht.get("name") or m.get("homeTeamId"), "away": at.get("name") or m.get("awayTeamId"),
           "s": [sm.get("homeGames", m.get("homeGames")) or 0, sm.get("awayGames", m.get("awayGames")) or 0], "st": state,
           "url": f"{TTBL}/bundesliga/gameday/{season}/{gd}/{m['id']}", "r": rubbers}
    v = (sm.get("venue") or {}).get("place")
    if v:
        tie["venue"] = v.strip()
    if sm.get("spectators"):
        tie["crowd"] = sm["spectators"]
    return tie


def ttbl_season(season, players, only_recent=False):
    """season like '2026-2027'. Walks every matchday's schedule page."""
    first = next_data(fetch(f"{TTBL}/bundesliga/gameschedule/{season}/1/all"))
    if not first:
        return []
    names = {t["seasonTeam"]["id"]: t["seasonTeam"]["name"] for t in (first.get("tableTeams") or []) + (first.get("teams") or []) if t.get("seasonTeam")}
    ties = []
    old = {t["id"]: t for t in load(os.path.join(LDIR, "ttbl", f"{season}.json"), {"ties": []})["ties"]}
    for gd in first.get("gamedays") or []:
        idx = gd["index"]
        d = first if idx == 1 else next_data(fetch(f"{TTBL}/bundesliga/gameschedule/{season}/{idx}/all"))
        for m in (d or {}).get("matches") or []:
            prev = old.get(m["id"])
            if prev and prev["st"] == "done" and m.get("matchState") == "Finished":
                ties.append(prev)
                continue
            if m.get("matchState") != "Finished" and only_recent:
                # unplayed: keep the fixture without fetching the match page
                ts = m.get("timeStamp")
                ties.append({"id": m["id"], "d": dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None,
                             "g": "M", "rd": f"Matchday {idx}", "home": names.get(m.get("homeTeamId"), m.get("homeTeamId")),
                             "away": names.get(m.get("awayTeamId"), m.get("awayTeamId")), "s": [m.get("homeGames") or 0, m.get("awayGames") or 0],
                             "st": "live" if m.get("matchState") == "Live" else "due",
                             "url": f"{TTBL}/bundesliga/gameday/{season}/{idx}/{m['id']}", "r": []})
                continue
            ties.append(ttbl_tie(season, idx, m, players))
            time.sleep(0.5)
    return ties


def sync_ttbl(backfill=False):
    ppath = os.path.join(LDIR, "ttbl", "players.json")
    players = load(ppath, {})
    d = next_data(fetch(f"{TTBL}/bundesliga/gameschedule/current/current/all")) or {}
    seasons = [s for s in d.get("seasons") or [] if s["startYear"] >= 2017]
    if not backfill:
        seasons = [s for s in seasons if s.get("isCurrentSeason")]
    for s in seasons:
        name = f'{s["startYear"]}-{s["endYear"]}'
        ties = ttbl_season(name, players, only_recent=True)
        if ties:
            n = merge("ttbl", f'{s["startYear"]}-{str(s["endYear"])[2:]}', ties)
            print("ttbl", name, n, "ties")
        save(ppath, players)


# ---------------------------------------------------------------- T.League (Japan)
TL = "https://tleague.jp"
TL_TEAMS = {"tt-saitama": ("T.T Saitama", "M"), "km-tokyo": ("Kinoshita Meister Tokyo", "M"), "kanazawa": ("Kanazawa Port", "M"),
            "shizuoka": ("Shizuoka Jade", "M"), "okayama": ("Okayama Rivets", "M"), "ryukyu": ("Ryukyu Asteeda", "M"),
            "ka-kanagawa": ("Kinoshita Abyell Kanagawa", "W"), "top-nagoya": ("Top Otome Pingpongs Nagoya", "W"), "kyoto": ("Kyoto Kaguya Rise", "W"),
            "red-elf": ("Nippon Life Red Elf", "W"), "np-mallets": ("Nippon Paint Mallets", "W"), "kyushu": ("Kyushu Karina", "W")}
PLAYER_A = r'<a href="/player/detail\.php\?player=(\d*)&year=(\d+)">([^<]*)</a>'


def tl_player(pid, year, players):
    if pid in players:
        return
    page = fetch(f"{TL}/player/detail.php?player={pid}&year={year}") or ""
    roma = re.search(r'player-detail-roma">([^<]+)<', page)
    jp = re.search(r'player-detail-name">([^<]+)<', page)
    players[pid] = {"name": html.unescape(roma.group(1)).strip() if roma else (jp.group(1).strip() if jp else pid)}
    if jp:
        players[pid]["ja"] = jp.group(1).strip()
    time.sleep(0.3)


def tl_tie(mid, players):
    page = fetch(f"{TL}/schedule/detail.php?id={mid}")
    if not page or "第1マッチ" not in page and "マッチ" not in page:
        return None
    season = re.search(r"(\d{4})-\d{4}シーズン", page)
    day = re.search(r"(\d{4})年(\d{2})月(\d{2})日\([^)]\)", page)
    start = re.search(r"開始時間：.{0,200}?(\d{1,2}):(\d{2})", page, re.S)
    crowd = re.search(r"入場者数：.{0,200}?([\d,]+)人", page, re.S)
    venue = re.search(r"\d{4}年\d{2}月\d{2}日\([^)]\)\s*(?:<[^>]+>\s*)*([^<]+)<", page)
    blocks = re.split(r'<h2 class="h4 font-weight-bold mb-0">第\d+マッチ</h2>', page)
    teams, rubbers = [], []
    for blk in blocks[1:]:
        blk = blk.split("第1ゲーム")[0]
        sides = re.findall(r'<div class="text-center py-4"><a class="font-weight-bold h6" href="/team/([a-z0-9-]+)/">(.*?)</div>', blk, re.S)
        if len(sides) != 2:
            continue
        teams = [s[0] for s in sides]
        ps = []
        for _, inner in sides:
            ids = []
            for pid, year, _nm in re.findall(PLAYER_A, inner):
                if pid:
                    tl_player(pid, year, players)
                    ids.append(pid)
            ps.append(ids)
        if not ps[0] or not ps[1]:
            continue
        nums = re.findall(r'<div class="font-weight-bold[^"]*">(\d+)</div>', blk)
        games = re.findall(r'<div class="text-center">(\d+) - (\d+)</div>', blk)
        if len(nums) < 2 or not games:
            continue
        s = [int(nums[0]), int(nums[1])]
        rubbers.append({"k": "D" if len(ps[0]) > 1 else "S", "p": ps, "s": s,
                        "g": ",".join(f"{a}-{b}" for a, b in games), "w": 0 if s[0] > s[1] else 1})
    if len(teams) != 2:
        return None
    total = [sum(1 for r in rubbers if r["w"] == 0), sum(1 for r in rubbers if r["w"] == 1)]
    d = None
    if day:
        h, mi = (int(start.group(1)), int(start.group(2))) if start else (0, 0)
        local = dt.datetime(int(day.group(1)), int(day.group(2)), int(day.group(3)), h, mi)
        d = (local - dt.timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:%SZ")
    home, away = TL_TEAMS.get(teams[0], (teams[0], "M")), TL_TEAMS.get(teams[1], (teams[1], "M"))
    tie = {"id": str(mid), "d": d, "g": home[1], "rd": "League", "home": home[0], "away": away[0], "s": total,
           "st": "done" if rubbers else "due", "url": f"{TL}/schedule/detail.php?id={mid}", "r": rubbers}
    if venue and venue.group(1).strip():
        tie["venue"] = html.unescape(venue.group(1)).strip()
    if crowd:
        tie["crowd"] = int(crowd.group(1).replace(",", ""))
    return (season.group(1) if season else None), tie


def sync_tleague(backfill=False):
    ppath = os.path.join(LDIR, "tleague", "players.json")
    players = load(ppath, {})
    page = fetch(f"{TL}/schedule/") or ""
    ids = sorted(set(map(int, re.findall(r"detail\.php\?id=(\d+)", page))))
    if backfill:
        ids = list(range(1, (max(ids) if ids else 1500) + 1))
    by_season = {}
    known = {}
    for f in os.listdir(os.path.join(LDIR, "tleague")) if os.path.isdir(os.path.join(LDIR, "tleague")) else []:
        if f[0].isdigit():
            for t in load(os.path.join(LDIR, "tleague", f), {"ties": []})["ties"]:
                known[t["id"]] = t
    for mid in ids:
        k = known.get(str(mid))
        if k and k["st"] == "done":
            continue
        try:
            got = tl_tie(mid, players)
        except Exception as err:
            print("tleague", mid, "failed:", err)
            continue
        if got and got[0]:
            y = int(got[0])
            by_season.setdefault(f"{y}-{str(y + 1)[2:]}", []).append(got[1])
        time.sleep(0.4)
        if len(players) % 25 == 0:
            save(ppath, players)
    for season, ties in by_season.items():
        print("tleague", season, merge("tleague", season, ties), "ties")
    save(ppath, players)


if __name__ == "__main__":
    args = sys.argv[1:]
    back = "--backfill" in args
    which = [a for a in args if not a.startswith("--")] or ["ttbl", "tleague"]
    for lg in which:
        try:
            {"ttbl": sync_ttbl, "tleague": sync_tleague}[lg](backfill=back)
        except Exception as err:
            print(lg, "failed:", err)
