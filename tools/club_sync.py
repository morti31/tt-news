"""Club league tables, fixtures and results, pulled from each league's official site.

Runs on GitHub (.github/workflows/club-sync.yml) and writes data/clubs/<competition>.json for the
competitions with a feed we can read:

  ttbl            Tischtennis Bundesliga (men)           ttbl.de, the page data behind its table and schedule
  dttbl-women     1. Bundesliga Damen (women)            DTTB click-TT (nuLiga), table and full schedule
  tleague-men     T.League men                           tleague.jp, table and schedule pages
  tleague-women   T.League women                         tleague.jp
  mltt            Major League Table Tennis (mixed)      web.mltt.com, the API behind its schedule and results

Other competitions (China Super League, UTT, Pro A, ETTU Champions League) have no feed we can read;
the scheduled update runs keep their files current by hand from official sources (see UPDATE.md).
Their files carry "auto": false and this script never touches them.

Each file:
  {"id", "auto": true, "updated", "season", "source": {"name", "url"},
   "table": {"columns": [...], "groups": [{"name"|null, "rows": [{"pos", "team", "p", "w", "l", "d"?, "for", "against", "diff", "pts"}]}], "note"?},
   "matches": [{"when": ISO UTC, "home", "away", "score": [h, a] | null, "status": "finished"|"live"|"scheduled", "round"?, "venue"?}]}

Usage: python3 tools/club_sync.py [competition ...]   (no arguments: all)
"""
import json, os, re, sys, html, datetime as dt
import urllib.request
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "clubs")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
UTC = dt.timezone.utc


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-GB,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:00Z")


class Tables(HTMLParser):
    """Every <table> on a page as rows of (cell text, cell html-ish attrs)."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.stack = [], []
        self.cell = None
        self.links = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self.stack.append([])
        elif tag == "tr" and self.stack:
            self.stack[-1].append([])
        elif tag in ("td", "th") and self.stack and self.stack[-1]:
            self.cell, self.links = [], []
        elif tag == "a" and self.cell is not None and a.get("href"):
            self.links.append(a["href"])
        elif tag == "br" and self.cell is not None:
            self.cell.append("\n")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None and self.stack and self.stack[-1]:
            text = re.sub(r"[ \t\r\xa0]+", " ", "".join(self.cell)).strip()
            self.stack[-1][-1].append({"text": text, "links": self.links})
            self.cell = None
        elif tag == "table" and self.stack:
            self.tables.append(self.stack.pop())

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def tables(page):
    p = Tables()
    p.feed(page)
    return p.tables


def num(s):
    m = re.search(r"-?\d+", str(s).replace("−", "-"))
    return int(m.group(0)) if m else None


# ---------------------------------------------------------------- TTBL (men)
TTBL = "https://www.ttbl.de"
TTBL_NAMES = {   # club names as the league writes them in English-language coverage
    "Borussia Düsseldorf": "Borussia Düsseldorf", "1. FC Saarbrücken-TT": "1. FC Saarbrücken",
    "TTF Liebherr Ochsenhausen": "TTF Ochsenhausen", "TTC Schwalbe Bergneustadt": "TTC Bergneustadt",
    "TSV Bad Königshofen": "TSV Bad Königshofen", "ASC Grünwettersbach": "ASC Grünwettersbach",
    "TTC OE Clarity-Tel.Syst.Bad Homburg": "TTC Bad Homburg", "Post SV Mühlhausen": "Post SV Mühlhausen",
    "TTC Zugbrücke Grenzau": "TTC Grenzau", "SV Werder Bremen": "Werder Bremen",
    "TTC RhönSprudel Fulda-Maberzell": "TTC Fulda-Maberzell", "BV Borussia 09 Dortmund": "Borussia Dortmund",
}


def next_data(page):
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page, re.S)
    return json.loads(m.group(1))["props"]["pageProps"]


def ttbl():
    pp = next_data(get(f"{TTBL}/bundesliga/table"))
    season = pp["selectedSeason"]
    tag = f'{season["startYear"]}-{season["endYear"]}'
    name = lambda t: TTBL_NAMES.get(t["seasonTeam"]["name"], t["seasonTeam"]["name"])
    rows = [{"pos": t["rank"], "team": name(t), "p": t["matchCount"], "w": t["matchWins"], "l": t["matchLosses"],
             "for": t["gameWins"], "against": t["gameLosses"], "diff": t["gameDifference"], "pts": t["plusPoints"]}
            for t in sorted(pp["teams"], key=lambda t: t["rank"])]
    matches = []
    for g in pp["gamedays"]:
        try:
            day = next_data(get(f'{TTBL}/bundesliga/gameschedule/{tag}/{g["index"]}/all'))
        except Exception as e:
            print("ttbl gameday", g["index"], e)
            continue
        rnd = {"SemiFinals": "Semi-final", "Finals": "Final4"}.get(g["type"], f'Matchday {g["index"]}')
        for m in day["matches"]:
            st = m.get("matchState")
            status = "finished" if st == "Finished" else "live" if st in ("Live", "Running", "Started") else "scheduled"
            if not m.get("homeTeam") or not m.get("awayTeam"):
                continue
            matches.append({"when": iso(dt.datetime.fromtimestamp(m["timeStamp"], UTC)), "home": name(m["homeTeam"]), "away": name(m["awayTeam"]),
                            "score": [m["homeGames"], m["awayGames"]] if status != "scheduled" else None, "status": status,
                            "round": rnd, "venue": ((m.get("venue") or {}).get("place") or "").strip() or None,
                            **({"tbc": True} if m.get("isTimeToBeDefined") else {})})
    return {"season": f'{season["startYear"]}-{str(season["endYear"])[2:]}', "source": {"name": "TTBL", "url": f"{TTBL}/bundesliga/table"},
            "table": {"columns": ["p", "w", "l", "games", "pts"], "groups": [{"name": None, "rows": rows}],
                      "note": "Two points for a win. Places 1 to 4 go through to the play-offs."},
            "matches": matches}


# ---------------------------------------------------------------- women's Bundesliga (DTTB click-TT)
NULIGA = "https://dttb.click-tt.de/cgi-bin/WebObjects/nuLigaTTDE.woa/wa/groupPage?championship=DTTB+{season}&group={group}"
DTTBL_GROUP = {"26/27": "518223"}   # 1. Bundesliga Damen; add the new group id each season (shown on the DTTB league page)
DTTBL_NAMES = {"SV DJK Kolbermoor": "SV DJK Kolbermoor", "TTC 1946 Weinheim": "TTC Weinheim", "ttc berlin eastside": "TTC Berlin Eastside",
               "TG 1953 Langenselbold": "TG Langenselbold", "TuS Fürstenfeldbruck": "TuS Fürstenfeldbruck", "TSV Dachau 65": "TSV Dachau",
               "TTG Bingen/Münster-Sarmsheim": "TTG Bingen/Münster-Sarmsheim", "ESV Weil": "ESV Weil"}
BERLIN = ZoneInfo("Europe/Berlin")


def dttbl_women():
    season = sorted(DTTBL_GROUP)[-1]
    url = NULIGA.format(season=season.replace("/", "%2F"), group=DTTBL_GROUP[season])
    nm = lambda s: DTTBL_NAMES.get(s.strip(), s.strip())
    rows = []
    for t in tables(get(url)):
        head = [c["text"] for c in t[0]]
        if "Mannschaft" in head and "Punkte" in head:
            for r in t[1:]:
                c = [x["text"] for x in r]
                if len(c) < 10 or not c[1].isdigit():
                    continue
                f, a = (int(x) for x in c[7].split(":"))
                rows.append({"pos": int(c[1]), "team": nm(c[2]), "p": int(c[3]), "w": int(c[4]), "d": int(c[5]), "l": int(c[6]),
                             "for": f, "against": a, "diff": f - a, "pts": int(c[9].split(":")[0])})
    matches, date = [], None
    for t in tables(get(url + "&displayTyp=gesamt&displayDetail=meetings")):
        head = [c["text"] for c in t[0]]
        if "Heimmannschaft" not in head:
            continue
        for r in t[1:]:
            c = [x["text"] for x in r]
            if len(c) < 7:
                continue
            if re.match(r"\d\d\.\d\d\.\d{4}", c[1]):
                date = c[1]
            tm = re.search(r"\d\d:\d\d", c[2])
            if not date or not tm:
                continue
            when = dt.datetime.strptime(f"{date} {tm.group(0)}", "%d.%m.%Y %H:%M").replace(tzinfo=BERLIN)
            sc = re.match(r"\s*(\d+):(\d+)", c[6])
            matches.append({"when": iso(when), "home": nm(c[4]), "away": nm(c[5]), "score": [int(sc.group(1)), int(sc.group(2))] if sc else None,
                            "status": "finished" if sc else "scheduled"})
    return {"season": "20" + season.replace("/", "-"), "source": {"name": "DTTB click-TT", "url": url},
            "table": {"columns": ["p", "w", "d", "l", "games", "pts"], "groups": [{"name": None, "rows": rows}],
                      "note": "Two points for a win, one for a draw."},
            "matches": matches}


# ---------------------------------------------------------------- T.League (Japan)
TL = "https://tleague.jp"
TL_TEAMS = {   # schedule slug or ranking id -> English name
    "kanazawa": "Kanazawa Port", "12": "Kanazawa Port", "ryukyu": "Ryukyu Asteeda", "4": "Ryukyu Asteeda",
    "km-tokyo": "Kinoshita Meister Tokyo", "2": "Kinoshita Meister Tokyo", "okayama": "Okayama Rivets", "3": "Okayama Rivets",
    "tt-saitama": "T.T Saitama", "1": "T.T Saitama", "shizuoka": "Shizuoka Jade", "11": "Shizuoka Jade",
    "top-nagoya": "Top Otome Pingpongs Nagoya", "6": "Top Otome Pingpongs Nagoya", "np-mallets": "Nippon Paint Mallets", "8": "Nippon Paint Mallets",
    "red-elf": "Nippon Life Red Elf", "7": "Nippon Life Red Elf", "ka-kanagawa": "Kinoshita Abyell Kanagawa", "5": "Kinoshita Abyell Kanagawa",
    "kyoto": "Kyoto Kaguya Rise", "10": "Kyoto Kaguya Rise", "kyushu": "Kyushu Karina", "9": "Kyushu Karina",
}
TOKYO = ZoneInfo("Asia/Tokyo")


def tl_team(links):
    for h in links:
        m = re.search(r"/team/([a-z0-9-]+)/|team\.php\?team=(\d+)", h)
        if m:
            k = m.group(1) or m.group(2)
            return TL_TEAMS.get(k, k)
    return None


def tleague(gender):
    year = dt.date.today().year if dt.date.today().month >= 7 else dt.date.today().year - 1
    rows = []
    t = tables(get(f"{TL}/ranking/index.php?gender={1 if gender == 'm' else 2}&year={year}"))[0]
    for r in t[1:]:
        c = [x["text"] for x in r]
        if len(c) < 11 or not c[0].strip().isdigit():
            continue
        team = tl_team(r[1]["links"]) or c[1]
        f, a = num(c[8]), num(c[9])
        rows.append({"pos": int(c[0]), "team": team, "pts": num(c[2]), "p": num(c[3]), "w": num(c[4]), "l": num(c[6]),
                     "for": f, "against": a, "diff": f - a})
    matches = []
    for t in tables(get(f"{TL}/schedule/?mw={gender}")):
        for r in t:
            c = [x["text"] for x in r]
            if len(c) < 5:
                continue
            d = re.search(r"(\d{4})年\s*(\d\d)月(\d\d)日.*?(\d\d):(\d\d)", c[0], re.S)
            if not d:
                continue
            home, away = tl_team(r[2]["links"]), tl_team(r[4]["links"])
            if not home or not away:
                continue
            when = dt.datetime(*(int(x) for x in d.groups()), tzinfo=TOKYO)
            sc = re.match(r"\s*(\d+)\s*-\s*(\d+)", c[3])
            matches.append({"when": iso(when), "home": home, "away": away, "score": [int(sc.group(1)), int(sc.group(2))] if sc else None,
                            "status": "finished" if sc else "scheduled"})
    return {"season": f"{year}-{str(year + 1)[2:]}", "source": {"name": "T.League", "url": f"{TL}/ranking/"},
            "table": {"columns": ["p", "w", "l", "matches", "pts"], "groups": [{"name": None, "rows": rows}],
                      "note": "Three points for a win, two for a win after the Victory Match, one for a loss after the Victory Match. The top two reach the play-off final."},
            "matches": matches}


# ---------------------------------------------------------------- Major League Table Tennis (US)
MLTT = "https://web.mltt.com/api"


def mltt():
    teams = json.loads(get(f"{MLTT}/teams"))
    teams = teams.get("data", teams) if isinstance(teams, dict) else teams
    region = {t["name"]: t.get("region") for t in teams}
    out, page = [], 1
    while page < 10:
        d = json.loads(get(f"{MLTT}/matches?limit=100&page={page}"))
        out += d["data"]
        if not d["pagination"].get("hasNextPage"):
            break
        page += 1
    # The season runs from September to April: everything from 1 August of the season's first year
    today = dt.date.today()
    y0 = today.year if today.month >= 8 else today.year - 1
    lo, hi = f"{y0}-08-01", f"{y0 + 1}-08-01"
    season = f"{y0}-{str(y0 + 1)[2:]}"
    now = dt.datetime.now(UTC)
    matches, rec = [], {}
    for m in out:
        if not (lo <= m.get("date", "") < hi):
            continue
        h, a = m["team1"]["name"], m["team2"]["name"]
        ph, pa = m["team1"].get("points"), m["team2"].get("points")
        when = dt.datetime.fromisoformat(m["startDateTime"].replace("Z", "+00:00"))
        done = ph is not None and pa is not None and (ph != pa or ph > 0)
        status = "finished" if done and when < now - dt.timedelta(hours=3) else "live" if done else "scheduled"
        matches.append({"when": iso(when), "home": h, "away": a, "score": [ph, pa] if done else None, "status": status, "venue": m.get("city")})
        if status == "finished":
            for t, us, them in ((h, ph, pa), (a, pa, ph)):
                r = rec.setdefault(t, {"team": t, "p": 0, "w": 0, "l": 0, "for": 0, "against": 0})
                r["p"] += 1; r["w"] += us > them; r["l"] += us < them; r["for"] += us; r["against"] += them
    for t in region:
        rec.setdefault(t, {"team": t, "p": 0, "w": 0, "l": 0, "for": 0, "against": 0})
    groups = []
    for g in ("East", "West"):
        rows = sorted((r for r in rec.values() if region.get(r["team"]) == g), key=lambda r: (-r["w"], r["l"], -(r["for"] / max(1, r["for"] + r["against"]))))
        for i, r in enumerate(rows, 1):
            r.update(pos=i, diff=r["for"] - r["against"])
        groups.append({"name": f"{g} Division", "rows": rows})
    return {"season": season, "source": {"name": "MLTT", "url": "https://www.mltt.com/league/standings"},
            "table": {"columns": ["p", "w", "l", "points"], "groups": groups,
                      "note": "Eleven's table from MLTT's published results: wins first, then share of points won."},
            "matches": matches}


SOURCES = {"ttbl": ttbl, "dttbl-women": dttbl_women, "tleague-men": lambda: tleague("m"), "tleague-women": lambda: tleague("w"), "mltt": mltt}


def main(which):
    os.makedirs(OUT, exist_ok=True)
    bad = 0
    for k in which or SOURCES:
        try:
            d = SOURCES[k]()
        except Exception as e:   # keep the last good file
            print(f"{k}: failed, {e}")
            bad += 1
            continue
        if not d["table"]["groups"] or not any(g["rows"] for g in d["table"]["groups"]):
            print(f"{k}: no table, keeping the last file")
            bad += 1
            continue
        d["matches"].sort(key=lambda m: m["when"])
        path = os.path.join(OUT, f"{k}.json")
        old = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        new = {"id": k, "auto": True, "updated": old.get("updated"), **d}
        if {**old, "updated": None} != {**new, "updated": None}:
            new["updated"] = dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:00Z")
            json.dump(new, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"{k}: {sum(len(g['rows']) for g in d['table']['groups'])} teams, {len(d['matches'])} matches")
        else:
            print(f"{k}: unchanged")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) == len(sys.argv[1:] or SOURCES) else 0)
