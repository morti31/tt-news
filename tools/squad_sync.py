"""Club squads for every league on the Clubs pages, from the leagues' own sites.

Runs on GitHub (.github/workflows/club-sync.yml, daily) and writes data/clubs/squads/<competition>.json:
  {"id", "auto": true, "updated", "source": {"name", "url"},
   "teams": [{"team": name as in data/clubs/<competition>.json, "players": [{"name", "nat"?, "role"?}], "coach"?}]}

Automatic: ttbl (ttbl.de team data), dttbl-women (players listed in DTTB click-TT team pages), tleague-men and
tleague-women (tleague.jp team pages, romanised names from the player pages), mltt (mltt.com team rosters),
utt (ultimatetabletennis.in team pages).
By hand ("auto": false, never touched here): cttsl-men, cttsl-women, proa-men, proa-women, cl-men, cl-women.
The scheduled update runs keep those current from official sources (UPDATE.md, "Club squads").

Usage: python3 tools/squad_sync.py [competition ...]
"""
import json, os, re, sys, html, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import club_sync as cs

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "clubs", "squads")
COUNTRIES = {"china": "CHN", "japan": "JPN", "germany": "GER", "france": "FRA", "india": "IND", "usa": "USA", "united states": "USA",
             "romania": "ROU", "austria": "AUT", "south korea": "KOR", "korea": "KOR", "canada": "CAN", "sweden": "SWE", "brazil": "BRA",
             "egypt": "EGY", "nigeria": "NGR", "portugal": "POR", "spain": "ESP", "england": "ENG", "wales": "WAL", "wales (great britain)": "WAL",
             "great britain": "GBR", "belgium": "BEL", "denmark": "DEN", "slovenia": "SLO", "croatia": "CRO", "hungary": "HUN", "poland": "POL",
             "czech republic": "CZE", "czechia": "CZE", "chinese taipei": "TPE", "taiwan": "TPE", "hong kong": "HKG", "singapore": "SGP",
             "puerto rico": "PUR", "argentina": "ARG", "chile": "CHI", "mexico": "MEX", "slovakia": "SVK", "ukraine": "UKR", "luxembourg": "LUX",
             "netherlands": "NED", "italy": "ITA", "greece": "GRE", "serbia": "SRB", "moldova": "MDA", "kazakhstan": "KAZ", "australia": "AUS",
             "new zealand": "NZL", "iran": "IRI", "thailand": "THA", "malaysia": "MAS", "ireland": "IRL", "switzerland": "SUI", "norway": "NOR",
             "finland": "FIN", "israel": "ISR", "turkey": "TUR", "algeria": "ALG", "tunisia": "TUN", "ghana": "GHA", "peru": "PER",
             "colombia": "COL", "venezuela": "VEN", "dominican republic": "DOM", "cuba": "CUB", "guatemala": "GUA", "vietnam": "VIE",
             "philippines": "PHI", "indonesia": "INA", "sri lanka": "SRI", "pakistan": "PAK", "bangladesh": "BAN", "monaco": "MON"}


ISO = {"DEU": "GER", "NLD": "NED", "CHE": "SUI", "DNK": "DEN", "HRV": "CRO", "PRT": "POR", "SVN": "SLO", "GRC": "GRE", "IRN": "IRI",
       "NGA": "NGR", "MYS": "MAS", "IDN": "INA", "VNM": "VIE", "PHL": "PHI", "TWN": "TPE", "LVA": "LAT", "BGR": "BUL", "SRB": "SRB"}
FAMILY_FIRST = {"CHN", "TPE", "KOR", "HKG", "MAC", "PRK", "JPN"}


def nat(country):
    return COUNTRIES.get((country or "").strip().lower())


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def text_lines(page):
    page = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
    s = html.unescape(re.sub(r"<[^>]+>", "\n", page))
    return [x.strip() for x in s.split("\n") if x.strip()]


def ttbl():
    pp = cs.next_data(cs.get(f"{cs.TTBL}/bundesliga/teams"))
    teams = []
    for t in pp.get("teams") or []:
        name = cs.TTBL_NAMES.get(t["seasonTeam"]["name"], t["seasonTeam"]["name"])
        ps, coach = [], []
        for x in t.get("players") or []:
            sp = x.get("seasonPlayer") or {}
            if not sp.get("lastName"):
                continue
            n3 = ISO.get(sp.get("nationality") or "", sp.get("nationality"))
            first, last = sp["firstName"].strip(), sp["lastName"].strip()
            p = {"name": f"{last} {first}" if n3 in FAMILY_FIRST - {"JPN"} else f"{first} {last}".strip()}
            if n3:
                p["nat"] = n3
            if sp.get("role") and sp["role"] != "Player":
                coach.append(p["name"])
                continue
            ps.append(p)
        teams.append({"team": name, "players": ps, **({"coach": ", ".join(coach)} if coach else {})})
    return {"source": {"name": "TTBL", "url": f"{cs.TTBL}/bundesliga/teams"}, "teams": teams}


def dttbl_women():
    season = sorted(cs.DTTBL_GROUP)[-1]
    url = cs.NULIGA.format(season=season.replace("/", "%2F"), group=cs.DTTBL_GROUP[season])
    page = cs.get(url)
    teams = []
    for href in dict.fromkeys(re.findall(r'href="(/cgi-bin/WebObjects/nuLigaTTDE\.woa/wa/teamPortrait\?[^"]+)"', page)):
        tp = cs.get("https://dttb.click-tt.de" + html.unescape(href))
        lines = text_lines(tp)
        head = next((l for l in lines if re.search(r"\d+\.\s*Damen", l)), "")
        name = re.sub(r"\s*\d+\.\s*Damen.*", "", head).strip()
        players = []
        if "Spielerbilanzen" in " ".join(lines):
            i = next(k for k, l in enumerate(lines) if l.startswith("Spielerbilanzen"))
            for l in lines[i:i + 200]:
                m = re.match(r"^([A-ZÄÖÜ][^,/\d]+), ([^,/\d]+)$", l)
                if m and "/" not in l and not l.startswith("Name,"):
                    nm = f"{m.group(2).strip()} {m.group(1).strip()}"
                    if nm not in [p["name"] for p in players]:
                        players.append({"name": nm})
        name = next((v for k, v in cs.DTTBL_NAMES.items() if name and (k.lower() == name.lower() or k.lower() in name.lower() or name.lower() in k.lower())), name)
        if players:
            teams.append({"team": name, "players": players})
    return {"source": {"name": "DTTB click-TT", "url": url}, "note": "Players who have played this season.", "teams": teams}


def tleague(gender):
    lp = os.path.join(ROOT, "data", "leagues", "tleague", "players.json")
    known = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else {}
    slugs = [k for k, v in cs.TL_TEAMS.items() if not k.isdigit()]
    men = {"kanazawa", "ryukyu", "km-tokyo", "okayama", "tt-saitama", "shizuoka"}
    teams = []
    for slug in slugs:
        if (slug in men) != (gender == "m"):
            continue
        page = cs.get(f"{cs.TL}/team/{slug}/player/") or ""
        if "player=" not in page:
            page = cs.get(f"{cs.TL}/team/{slug}/") or ""
        ps = []
        for pid in dict.fromkeys(re.findall(r"detail\.php\?player=(\d+)", page)):
            if pid not in known:
                pg = cs.get(f"{cs.TL}/player/detail.php?player={pid}") or ""
                roma = re.search(r'player-detail-roma">([^<]+)<', pg)
                known[pid] = {"name": html.unescape(roma.group(1)).strip() if roma else pid}
            n = known[pid]["name"]
            # "Yuya OSHIMA" -> "Yuya Oshima"
            ps.append({"name": " ".join(w.capitalize() if w.isupper() and len(w) > 1 else w for w in n.split())})
        teams.append({"team": cs.TL_TEAMS[slug], "players": ps})
    return {"source": {"name": "T.League", "url": f"{cs.TL}/team/"}, "teams": teams}


def roster_pages(base, index_path, link_rx, start_word, stop_words):
    page = cs.get(base + index_path)
    teams = []
    for path in dict.fromkeys(re.findall(link_rx, page)):
        lines = text_lines(cs.get(base + path))
        try:
            i = lines.index(start_word)
        except ValueError:
            continue
        coach, players, j = None, [], i + 1
        while j < len(lines) - 1 and lines[j] not in stop_words:
            if lines[j].startswith("Coach "):
                coach = lines[j][6:].strip()
                j += 2
                continue
            if lines[j] == "Coaches":
                break
            players.append({"name": lines[j], **({"nat": nat(lines[j + 1])} if nat(lines[j + 1]) else {})})
            j += 2
        yield path, lines, players, coach


def mltt():
    teams = []
    for path, lines, players, coach in roster_pages("https://www.mltt.com", "/", r'href="(/mltt-team/[a-z0-9-]+)"', "Roster", {"upcoming matches", "Upcoming matches"}):
        name = " ".join(w.capitalize() for w in path.rsplit("/", 1)[1].split("-"))
        teams.append({"team": name, "players": players, **({"coach": coach} if coach else {})})
    return {"source": {"name": "MLTT", "url": "https://www.mltt.com/teams"}, "teams": teams}


UTT_TEAMS = {"ahmedabad-apl-pipers": "Ahmedabad APL Pipers", "dabang-delhi-t-t-c": "Dabang Delhi TTC", "dempo-goa-challengers": "Dempo Goa Challengers",
             "hvr-kolkata-thunder-blades": "HVR Kolkata ThunderBlades", "pbg-pune-jaguars": "PBG Pune Jaguars", "u-mumba-tt": "U Mumba TT",
             "up-prometheans": "UP Prometheans"}


def utt():
    teams = []
    for path, lines, players, coach in roster_pages("https://www.ultimatetabletennis.in", "/teams", r'href="(/teams/[a-z0-9-]+)"', "Players", {"Coaches", "Leagues"}):
        slug = re.sub(r"-\d+$", "", path.rsplit("/", 1)[1])
        name = UTT_TEAMS.get(slug, " ".join(w.capitalize() for w in slug.split("-")))
        coaches = []
        if "Coaches" in lines:
            c = lines.index("Coaches")
            coaches = [lines[x] for x in range(c + 1, min(c + 7, len(lines)), 2) if nat(lines[x + 1]) or lines[x + 1] in ("India",)]
        teams.append({"team": name,
                      "players": players, **({"coach": ", ".join(coaches)} if coaches else {})})
    return {"source": {"name": "Ultimate Table Tennis", "url": "https://www.ultimatetabletennis.in/teams"}, "teams": teams}


SOURCES = {"ttbl": ttbl, "dttbl-women": dttbl_women, "tleague-men": lambda: tleague("m"), "tleague-women": lambda: tleague("w"),
           "mltt": mltt, "utt": utt}


def main(which):
    os.makedirs(OUT, exist_ok=True)
    for cid in which or SOURCES:
        path = os.path.join(OUT, f"{cid}.json")
        old = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
        if old.get("auto") is False:
            continue
        try:
            d = SOURCES[cid]()
        except Exception as err:
            print(cid, "failed:", err)
            continue
        if not d["teams"] or not any(t["players"] for t in d["teams"]):
            print(cid, "no squads found; keeping the old file")
            continue
        changed = old.get("teams") != d["teams"]
        out = {"id": cid, "auto": True, "updated": now() if changed else old.get("updated", now()), **d}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(cid, len(d["teams"]), "teams,", sum(len(t["players"]) for t in d["teams"]), "players", "(changed)" if changed else "")


if __name__ == "__main__":
    main(sys.argv[1:])
