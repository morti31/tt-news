"""The Chop, by Eleven: a site about defensive table tennis (choppers and other defenders).

Lives at /defensive/ on eleventabletennis.com until defensive.eleventabletennis.com is pointed at it (UPDATE.md, "The Chop").
It writes no news of its own. It links to stories about defenders elsewhere (and on Eleven, marked as such), and builds
rankings, form and fixtures for the defenders from the data Eleven already keeps.

Inputs
  data/chop/players.json   the defenders: [{"name", "ittf_id", "gender": "M"|"W", "style": "chopper"|"defender"|"pimples",
                           "note", "status": "approved"|"draft", "sources": [url]}]. Only Tom approves names (status).
  data/chop/links.json     the reading list: [{"url", "title", "source", "date", "summary", "players": [names], "kind":
                           "news"|"analysis"|"history"|"video", "eleven": true for Eleven's own pieces}]
  data/rankings.json, data/doubles-rankings.json, data/matches (form), data/draws (next matches in tournaments),
  data/clubs and data/clubs/squads (next club matches), data/news.json and data/articles (Eleven's pieces)
Output
  defensive/index.html, defensive/defenders.html, defensive/calendar.html, defensive/reading.html,
  defensive/defenders.html, defensive/defender/<slug>.html, defensive/chop.css (copied from tools/chop.css), defensive/chop-sitemap.xml
  Served at defensive.eleventabletennis.com: worker.js maps every path on that host to /defensive/<path>.
"""
import datetime as dt, glob, html, json, os, re, shutil, unicodedata

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "defensive")
BASE = ""   # the site is served at the root of defensive.eleventabletennis.com (worker.js maps it to /defensive/)
SITE = "https://defensive.eleventabletennis.com"
ELEVEN = "https://eleventabletennis.com"
STYLE = {"chopper": "Classical chopper", "modern": "Modern defender", "allround": "Defensive all-rounder"}
STYLE_ABOUT = {"chopper": "defends from well back with heavy backspin and variation, attacking now and then",
               "modern": "chops, but counter-attacks and plays topspin as a regular part of the game",
               "allround": "defends closer to the table with blocks, pushes and long pimples, and disrupts rather than chops"}


STYLE_SOURCES = [
    ("Martin Spin's ranking of defensive and special styles, which describes how each player plays", "https://www.martinspin.ch/world-ranking"),
    ("Butterfly's coaching guide, Player archetypes: defensive styles", "https://butterflyonline.com/player-archetypes-defensive-styles"),
]

GLOSSARY = [
    ("Chop", "A backspin stroke played from well behind the table, usually against topspin. The defender's main shot."),
    ("Chopper", "A player whose game is built on chopping. The Chop splits defenders into three styles; see below."),
    ("Push", "A short backspin stroke played over the table, usually against backspin."),
    ("Float", "A chop with little or no spin, disguised to look heavy so the attacker misjudges it."),
    ("Inverted rubber", "Smooth rubber with the pimples facing in. Gives the most spin; almost every attacker uses it on both sides."),
    ("Long pimples", "Rubber with long, thin pimples facing out. Returns much of the opponent's spin, so a topspin can come back as backspin. Many choppers use it on the backhand."),
    ("Short pimples", "Rubber with short pimples facing out. Less spin, more speed and a flatter ball; some defenders use it to block and hit."),
    ("Anti-spin", "Slick rubber that takes most of the spin off the ball. Rare at the top level."),
    ("Twiddling", "Turning the bat mid-rally so the forehand and backhand rubbers swap, to change the spin the opponent receives."),
    ("Counter-attack", "A defender switching from chopping to topspin, often against a weak loop."),
    ("Expedite rule", "If a game lasts 10 minutes and fewer than 18 points have been scored, the server must win the point within 13 returns or lose it. Applies for the rest of the match. Long defensive matches trigger it most."),
    ("World ranking", "The ITTF world ranking, published weekly by World Table Tennis. Points come from a player's best results over the past year, including youth events."),
]


def tag(style, link=True):
    """A style tag. Clicking it opens a short definition with its sources (chop.js, the #ch-def dialog)."""
    lab = STYLE.get(style)
    if not lab:
        return ""
    return (f'<button type="button" class="ch-style ch-style-{e(style)}" data-style="{e(style)}" aria-haspopup="dialog" '
            f'title="What is a {e(lab.lower())}?">{e(lab)}</button>')


def def_dialog():
    data = {k: {"label": STYLE[k], "about": STYLE_ABOUT[k][0].upper() + STYLE_ABOUT[k][1:] + "."} for k in STYLE}
    src = "".join(f'<li><a href="{e(u)}" rel="noopener" target="_blank">{e(t)}</a></li>' for t, u in STYLE_SOURCES)
    return (f'<dialog id="ch-def" class="ch-dialog" aria-labelledby="ch-def-h"><form method="dialog"><button class="ch-x" aria-label="Close">×</button></form>'
            f'<p class="ch-kick">Defensive style</p><h2 id="ch-def-h"></h2><p class="ch-def-about"></p>'
            f'<p class="ch-small">How we decide: The Chop puts every defender in one of three styles. A player is only included when a source we can open '
            f'describes them as a defender; long pimples alone don\'t count. The type follows how the sources describe their game, and each player\'s page '
            f'quotes the exact words. Where no source describes the game in detail, the type is our provisional call. The definitions are ours, based on:</p>'
            f'<ul class="ch-def-src">{src}</ul><a class="ch-more" href="/glossary.html">Glossary</a>'
            f'<script type="application/json" id="ch-def-data">{json.dumps(data)}</script></dialog>')
WTT_STREAMS = "https://www.youtube.com/@WTTGlobal/streams"   # WTT's own channel, as on Eleven's event pages
LEAGUE_LIVE = {"ttbl": ("Scores on ttbl.de", "https://www.ttbl.de/"), "tleague-men": ("Scores on tleague.jp", "https://tleague.jp/"),
               "tleague-women": ("Scores on tleague.jp", "https://tleague.jp/"), "mltt": ("Scores on mltt.com", "https://www.mltt.com/"),
               "utt": ("Scores on the UTT site", "https://www.ultimatetabletennis.in/")}
ROUNDS = {"FNL": "Final", "SFNL": "Semi-final", "QFNL": "Quarter-final", "R16": "Last 16", "8FNL": "Last 16", "RND1": "Qualifying round 1", "RND2": "Qualifying round 2", "RND3": "Qualifying round 3", "QER": "Qualifying", "R32": "Last 32", "R64": "Last 64", "R128": "Last 128"}


def load(path, default):
    try:
        return json.load(open(os.path.join(ROOT, path), encoding="utf-8"))
    except Exception:
        return default


def slug(n):
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", n).strip("-")


def key(n):
    n = unicodedata.normalize("NFKD", n or "").encode("ascii", "ignore").decode().lower()
    return " ".join(sorted(re.findall(r"[a-z]+", n)))


def day(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day} {d:%b %Y}"


def page(title, desc, path, body, active=""):
    nav = "".join(f'<a href="{BASE}{href}"{" aria-current=\"page\"" if k == active else ""}>{lab}</a>'
                  for k, href, lab in (("home", "/", "Home"), ("videos", "/videos.html", "Videos"), ("rankings", "/defenders.html", "Defenders"),
                                       ("calendar", "/calendar.html", "Calendar"), ("reading", "/reading.html", "Reading"),
                                       ("legends", "/legends.html", "Legends"), ("glossary", "/glossary.html", "Glossary")))
    return f"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{path}"><link rel="sitemap" type="application/xml" href="/chop-sitemap.xml">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:site_name" content="The Chop">
<link rel="icon" href="{BASE}/chop.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,600..800&family=Figtree:wght@400;500;600&family=Inter+Tight:wght@500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="{BASE}/chop.css?v={VER}">
<script src="{ELEVEN}/consent.js" defer></script>
</head><body>
<header class="ch-mast"><div class="ch-wrap ch-mast-in">
<a class="ch-mark" href="{BASE}/" aria-label="The Chop home"><svg viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="18" class="ch-mark-ball"/><path d="M6 27 34 13" class="ch-mark-cut"/></svg><span>The Chop</span></a>
<nav class="ch-nav" aria-label="Sections">{nav}</nav></div></header>
<main class="ch-wrap">{body}</main>
<footer class="ch-foot"><div class="ch-wrap"><p><b>The Chop</b> follows the defenders of table tennis: the choppers, the blockers and the players who win from the back of the court. It writes no news of its own; every story here links to the publication that wrote it.</p>
<p>Rankings, results and fixtures from <a href="{ELEVEN}/">Eleven</a>, which takes them from World Table Tennis and the leagues. <a href="{BASE}/glossary.html">Glossary</a> · <a href="{ELEVEN}/contact.html">Contact</a> · <a href="{ELEVEN}/privacy.html">Privacy and cookies</a> · <a href="{ELEVEN}/privacy.html" data-consent-open>Privacy settings</a></p></div></footer>
{def_dialog()}
<script src="{BASE}/chop.js?v={VER}" defer></script>
</body></html>"""


VER = "1"


def build():
    global VER
    players = [p for p in load("data/chop/players.json", []) if p.get("status") in ("approved", "draft")]
    links = load("data/chop/links.json", [])
    R = load("data/rankings.json", {})
    rk = {str(r["ittf_id"]): r for g in ("men", "women") for r in R.get(g, [])}
    D = load("data/doubles-rankings.json", {})
    prof = load("data/profiles.json", {})
    now = dt.datetime.now(dt.timezone.utc)
    today = now.date().isoformat()

    # Match database: every singles match of each defender, newest first
    P = load("data/matches/players.json", {})
    E = load("data/matches/events.json", {})
    ids = {p["ittf_id"] for p in players if p.get("ittf_id")}
    ms = {i: [] for i in ids}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "matches", "[0-9]*.json")))[-3:]:
        for m in load(os.path.relpath(f, ROOT), []):
            if m.get("k") not in ("MS", "WS") or len(m["p"][0]) != 1 or m.get("w") not in (0, 1):
                continue
            for side in (0, 1):
                pid = m["p"][side][0]
                if pid in ms:
                    ms[pid].append((m, side))
    # Club league singles (T.League, Bundesliga) count too: many defenders play more for their club than on the WTT tour
    import names as names_mod
    byname = {key(p["name"]): p["ittf_id"] for p in players if p.get("ittf_id")}
    rk_name = {key(r["name"]): r for r in rk.values()}
    for lg, label, nat in (("tleague", "T.League", "JPN"), ("ttbl", "Bundesliga", "")):
        LP = load(f"data/leagues/{lg}/players.json", {})
        for f in sorted(glob.glob(os.path.join(ROOT, "data", "leagues", lg, "20*.json")))[-2:]:
            for t in load(os.path.relpath(f, ROOT), {}).get("ties", []):
                if t.get("st") != "done":
                    continue
                for r in t.get("r", []):
                    if r.get("k") != "S" or r.get("w") not in (0, 1) or not r.get("s") or max(r["s"]) < 2:
                        continue
                    nm2 = [names_mod.from_wtt((LP.get(x[0]) or {}).get("name", ""), nat) for x in r["p"]]
                    for side in (0, 1):
                        pid = byname.get(key(nm2[side]))
                        if pid and pid in ms:
                            ms[pid].append(({"d": t["d"], "p": [["c0"], ["c1"]], "w": r["w"], "s": r["s"], "lbl": f'{label}: {t["home"]} v {t["away"]}',
                                             "on": nm2[1 - side]}, side))
    for v in ms.values():
        v.sort(key=lambda t: t[0].get("d") or "", reverse=True)

    # Titles: finals won at senior events, singles and doubles, from every season in the match database
    KIND = {"MS": "men's singles", "WS": "women's singles", "MD": "men's doubles", "WD": "women's doubles", "XD": "mixed doubles"}
    titles = {i: [] for i in ids}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "matches", "[0-9]*.json"))):
        for m in load(os.path.relpath(f, ROOT), []):
            if m.get("r") != "FNL" or m.get("w") not in (0, 1) or m.get("k") not in KIND:
                continue
            evn = (E.get(m["e"]) or {}).get("name", "")
            if re.search(r"youth|junior|cadet|U1\d|U2\d|hopes", evn, re.I):
                continue
            for pid in m["p"][m["w"]]:
                if pid in titles:
                    titles[pid].append(((m.get("d") or "")[:4], re.sub(r"\s+Presented by.*$", "", evn), KIND[m["k"]]))
    # Clubs: every squad Eleven keeps that lists the player
    clubs = {p["name"]: [] for p in players}
    for sq in glob.glob(os.path.join(ROOT, "data", "clubs", "squads", "*.json")):
        s_ = load(os.path.relpath(sq, ROOT), {})
        for t in s_.get("teams", []):
            for x in t.get("players", []):
                n = {key(q["name"]): q["name"] for q in players}.get(key(x.get("name")))
                if n:
                    cid_ = os.path.basename(sq)[:-5]
                    lgname = next((v for k, v in (("cl-", "Champions League"), ("tleague", "T.League"), ("ttbl", "Bundesliga"), ("dttbl", "Bundesliga"),
                                                  ("proa", "Pro A"), ("cttsl", "China Super League"), ("mltt", "Major League Table Tennis"), ("utt", "UTT")) if cid_.startswith(k)), "")
                    clubs[n].append((t["team"], lgname))

    import names as names_mod

    def nm(i):
        r = rk.get(i)
        if r:
            return r["name"]
        raw = P.get(i)
        return names_mod.from_wtt(*raw) if raw else "Unknown"

    def ev_name(i):
        n = (E.get(i) or {}).get("name", "")
        return re.sub(r"\s+Presented by.*$", "", n)

    # Next matches: tournament draws with a time and no score, then club fixtures through the squads
    nxt = {p["name"]: [] for p in players}
    WTT2EV = {str(x.get("wtt_id")): x["id"] for x in load("data/events.json", {}).get("events", []) if x.get("wtt_id")}
    pk = {key(p["name"]): p["name"] for p in players}
    for f in glob.glob(os.path.join(ROOT, "data", "draws", "*.json")):
        d = load(os.path.relpath(f, ROOT), {})
        title = re.sub(r"\s+Presented by.*$", "", (d.get("event") or {}).get("name", "") if isinstance(d.get("event"), dict) else str(d.get("event") or ""))
        for ev in (d.get("events") or {}).values():
            for rd in ev.get("rounds", []):
                for m in rd.get("matches", []):
                    w = m.get("when") or ""
                    if m.get("score") or not w or w < now.isoformat()[:19]:
                        continue
                    pl = m.get("players") or []
                    eid = WTT2EV.get(os.path.basename(f)[:-5])
                    for i, x in enumerate(pl):
                        if not x:
                            continue   # an empty slot (a bye or a player still to be decided)
                        n = pk.get(key(x.get("name")))
                        if n and len(pl) == 2:
                            o = pl[1 - i] or {}
                            nxt[n].append({"when": w, "what": f'{title or "Tournament"}, {ev.get("name", "")}, {rd.get("round", "")}',
                                           "v": o.get("name", "TBC"), "nat": o.get("nat", ""), "eid": eid})
    for sq in glob.glob(os.path.join(ROOT, "data", "clubs", "squads", "*.json")):
        cid = os.path.basename(sq)[:-5]
        s = load(os.path.relpath(sq, ROOT), {})
        c = load(f"data/clubs/{cid}.json", {})
        for t in s.get("teams", []):
            for x in t.get("players", []):
                n = pk.get(key(x.get("name")))
                if not n:
                    continue
                tn = key(t["team"])
                for m in c.get("matches", []):
                    if m.get("status") == "finished" or (m.get("when") or "") < now.isoformat()[:19]:
                        continue
                    for side, other in (("home", "away"), ("away", "home")):
                        mn = key(m.get(side) or "")
                        if mn and (mn == tn or set(mn.split()) <= set(tn.split()) or set(tn.split()) <= set(mn.split())) and m.get(other):
                            nxt[n].append({"when": m["when"], "what": f'{s.get("source", {}).get("name") or cid}: {m["home"]} v {m["away"]}',
                                           "v": "", "nat": "", "club": True, "day": m.get("date_only"), "cid": cid})
    for k_, v in nxt.items():
        u = {}
        for x in v:
            u.setdefault((x["when"], x["what"]), x)
        nxt[k_] = sorted(u.values(), key=lambda x: x["when"])

    # Likely next tournament: the draw they're in, else the next event of a kind they have played in the past year
    # (and can get into on ranking), else their club's next match. Labelled "likely" everywhere: entries aren't published.
    EV = load("data/events.json", {}).get("events", [])
    upcoming = sorted((x for x in EV if x.get("end", "") >= today and x.get("group") in ("WTT Series", "Majors", "Continental")), key=lambda x: x["start"])
    SERIES = [("WTT Feeder", r"\bFeeder\b"), ("WTT Star Contender", r"Star Contender"), ("WTT Contender", r"\bContender\b"),
              ("WTT Champions", r"\bChampions\b"), ("WTT Grand Smash", r"\bSmash\b"), ("WTT Finals", r"\bWTT Finals\b")]
    ENTRY = {"WTT Finals": 16, "WTT Champions": 32, "WTT Grand Smash": 120}   # rough ranking needed to get in

    def series_of(name):
        return next((sname for sname, rx in SERIES if re.search(rx, name or "")), None)

    # Published draws of current and upcoming events. Once an event's draw is out, nobody is "likely" for it any more:
    # a player is either in it (any round, times or not: a seed with a bye has no match time until the round before
    # finishes) or not playing it. Being in the draw doesn't need a scheduled match.
    EVBY = {x["id"]: x for x in EV}
    drawn, drawn_ev = {}, set()
    for f in glob.glob(os.path.join(ROOT, "data", "draws", "*.json")):
        eid = WTT2EV.get(os.path.basename(f)[:-5])
        x = EVBY.get(eid)
        if not x or x.get("end", "") < today:
            continue
        d = load(os.path.relpath(f, ROOT), {})
        drawn_ev.add(eid)
        for ev in (d.get("events") or {}).values():
            for rd in ev.get("rounds", []):
                for m in rd.get("matches", []):
                    pl = m.get("players") or []
                    for i, q in enumerate(pl):
                        n = pk.get(key((q or {}).get("name")))
                        if not n:
                            continue
                        st = drawn.setdefault(n, {}).setdefault(eid, {"out": False})
                        w = m.get("winner")
                        if w in (0, 1) and w != i and len(pl) == 2 and (pl[1 - i] or {}).get("name"):
                            st["out"] = True
    played_ev = {}   # WTT event ids each player has already played at (qualifying included)
    for i_, rows in ms.items():
        for m, s_ in rows:
            played_ev.setdefault(i_, set()).add(str(m.get("e")))

    def likely(p):
        nx = [x for x in nxt.get(p["name"], []) if not x.get("club")]
        live = [(eid, st) for eid, st in (drawn.get(p["name"]) or {}).items() if not st["out"]]
        if nx or live:
            eid = nx[0].get("eid") if nx else min(live, key=lambda t: EVBY[t[0]]["start"])[0]
            x = EVBY.get(eid) or {}
            title = f'{x["name"]} {x.get("year", "")}'.strip() if x else nx[0]["what"].split(",")[0]
            out = {"kind": "draw", "event": title, "when": nx[0]["when"] if nx else x.get("start", ""), "why": "in the draw", "eid": eid,
                   "url": f'{ELEVEN}/events/{eid}.html' if eid else None}
            if x:
                out.update(start=x["start"], end=x["end"], city=x.get("city", ""))
            return out
        r = rank_of(p)
        played = {}
        for m, s_ in ms.get(p.get("ittf_id"), []):
            if m.get("lbl") or (m.get("d") or "") < (now - dt.timedelta(days=365)).isoformat()[:10]:
                continue
            sr = series_of(ev_name(m["e"]))
            if sr:
                played.setdefault(sr, set()).add(m["e"])
        for x in upcoming:
            sr = x.get("series")
            if x["id"] in drawn_ev or str(x.get("wtt_id")) in played_ev.get(p.get("ittf_id"), set()):
                continue   # draw out and they're not in it, or already played there (out in qualifying)
            if sr in played and (not r or r["rank"] <= ENTRY.get(sr, 9999)) and x["start"] <= (now + dt.timedelta(days=150)).date().isoformat():
                n = len(played[sr])
                return {"kind": "likely", "event": f'{x["name"]} {x["year"]}', "url": f"{ELEVEN}/events/{x['id']}.html", "eid": x["id"], "start": x["start"], "end": x["end"],
                        "city": x.get("city", ""), "why": f"has played {n} {sr} event{'s' if n > 1 else ''} in the past year"}
        cl = [x for x in nxt.get(p["name"], []) if x.get("club")]
        if cl:
            return {"kind": "club", "event": cl[0]["what"].split(":")[0], "when": cl[0]["when"], "why": "next club match"}
        return None

    def span(a, b):
        da, db = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
        return f"{da.day} {da:%b}" + ("" if a == b else f" to {db.day} {db:%b}") + f" {db.year}"

    def watch(x=None, eid=None):
        """Where to follow a match live: Eleven's live scores and WTT's streams for tournaments, the league's own site for club matches."""
        eid = eid or (x or {}).get("eid")
        if eid:
            ls = [("Live scores", f"{ELEVEN}/events/{eid}.html#live"), ("Stream", WTT_STREAMS)]
        elif x and x.get("cid") in LEAGUE_LIVE:
            ls = [LEAGUE_LIVE[x["cid"]]]
        else:
            return ""
        return '<span class="ch-watch">' + "".join(f'<a href="{e(u)}" rel="noopener"{"" if u.startswith(ELEVEN) else " target=_blank"}>{e(t)}</a>' for t, u in ls) + "</span>"

    WTTREC = load("data/players/wtt.json", {})

    def age_of(p):
        b = p.get("born")
        if not b:
            bio = load(f"data/players/{slug(p['name'])}.json", {})
            b = bio.get("born") if isinstance(bio, dict) else None
        if not b:
            m_ = re.match(r"(\d\d)/(\d\d)/(\d{4})", (WTTREC.get(p.get("ittf_id") or "", {}) or {}).get("dob") or "")
            b = f"{m_[3]}-{m_[1]}-{m_[2]}" if m_ else None
        if not b:
            return None
        bd = dt.date.fromisoformat(b[:10])
        return now.date().year - bd.year - ((now.date().month, now.date().day) < (bd.month, bd.day))

    # Youth results (tools/youth_sync.py: U17 and older) and where the ranking points come from (tools/ranking_breakdown.py)
    YEV = load("data/matches/youth/events.json", {})
    youth = {i: [] for i in ids}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "matches", "youth", "[0-9]*.json"))):
        for m in load(os.path.relpath(f, ROOT), []):
            if m.get("k") not in ("MS", "WS") or m.get("w") not in (0, 1):
                continue
            for side in (0, 1):
                pid = m["p"][side][0]
                if pid in youth:
                    youth[pid].append((m, side))
    for v in youth.values():
        v.sort(key=lambda t: t[0].get("d") or "", reverse=True)
    BRK = load("data/ranking-breakdown.json", {})

    def youth_row(m, side):
        won = m["w"] == side
        o = m["p"][1 - side][0]
        sc = m.get("s") or [0, 0]
        evn = re.sub(r"\s+Presented by.*$", "", (YEV.get(m["e"]) or {}).get("name", "") or ev_name(m["e"]))
        return (f'<li class="{"w" if won else "l"}"><span class="ch-res">{"W" if won else "L"} {sc[side]}-{sc[1 - side]}</span>'
                f'<span class="ch-opp">{e(nm(o))}</span><span class="ch-ev">{e(evn)}, {e(m.get("a", ""))} · {day(m["d"])}</span></li>')

    def points_html(p):
        b = BRK.get(p.get("ittf_id") or "")
        evs = [x for x in (b or {}).get("events", []) if x.get("counted")]
        if not evs:
            return ""
        rows = "".join(f'<li><span class="ch-yr">{e(str(x.get("points")))}</span><span>{e(re.sub(r"\s+Presented by.*$", "", x.get("event") or ""))}'
                       f'{f" <small>{e(str(x.get(chr(114)+chr(101)+chr(115)+chr(117)+chr(108)+chr(116))))}</small>" if x.get("result") else ""}</span></li>' for x in evs)
        return (f'<section class="ch-sec"><h2>Where the ranking points come from</h2><ul class="ch-hon">{rows}</ul>'
                f'<p class="ch-small">The events that count towards the world ranking, from WTT\'s ranking breakdown ({e(b.get("week", ""))}).</p></section>')

    def likely_html(lk, compact=False):
        if not lk:
            return ""
        if lk["kind"] == "likely":
            body = (f'<a href="{e(lk["url"])}"><b>{e(lk["event"])}</b></a>, {e(lk["city"])}, {span(lk["start"], lk["end"])}'
                    f'<span class="ch-why">Likely: {e(lk["why"])}. Entry lists aren\'t published until the draw.</span>{watch(eid=lk.get("eid"))}')
            lab = "Likely next tournament"
        elif lk["kind"] == "draw":
            body = f'<b>{e(lk["event"])}</b><span class="ch-why">In the draw.</span>{watch(eid=lk.get("eid"))}'
            lab = "Next tournament"
        else:
            body = f'<b>{e(lk["event"])}</b>, {day(lk["when"])}<span class="ch-why">No tournament in view; next club match.</span>'
            lab = "Next up"
        return f'<div class="ch-likely"><span class="ch-kick">{lab}</span>{body}</div>'

    def form(p):
        """Last results and this year's record. Senior and club results first; youth events are merged into the form chips
        (marked "y", outlined) and counted apart in the record. Returns (last senior rows, form string, senior record, youth record)."""
        rows = ms.get(p.get("ittf_id"), [])
        yrows = youth.get(p.get("ittf_id"), [])
        both = sorted([(m, s_, False) for m, s_ in rows] + [(m, s_, True) for m, s_ in yrows], key=lambda t: t[0].get("d") or "", reverse=True)
        wl = "".join(("W" if m["w"] == s_ else "L") + ("y" if y else "") for m, s_, y in both[:10])
        rec = lambda rs: (sum(1 for m, s_ in rs if (m.get("d") or "")[:4] == today[:4] and m["w"] == s_),
                          sum(1 for m, s_ in rs if (m.get("d") or "")[:4] == today[:4] and m["w"] != s_))
        return rows[:10], wl, rec(rows), rec(yrows)

    def recs(rec, yrec):
        out = f"{rec[0]}-{rec[1]}" if sum(rec) or not sum(yrec) else ""
        if sum(yrec):
            out += f'<small class="ch-yrec" title="Youth events">{"+ " if out else ""}{yrec[0]}-{yrec[1]} youth</small>'
        return out

    def res_row(m, side):
        won = m["w"] == side
        o = m["p"][1 - side][0]
        sc = m.get("s") or [0, 0]
        oname = m.get("on") or nm(o)
        orr = rk.get(o) if not m.get("on") else rk_name.get(key(oname))
        where = m.get("lbl") or ev_name(m["e"])
        return (f'<li class="{"w" if won else "l"}"><span class="ch-res">{"W" if won else "L"} {sc[side]}-{sc[1 - side]}</span>'
                f'<span class="ch-opp">{e(oname)}{f" <small>No {orr["rank"]}</small>" if orr else ""}</span>'
                f'<span class="ch-ev">{e(where)}{", " + ROUNDS[m["r"]] if m.get("r") in ROUNDS else ""} · {day(m["d"])}</span></li>')

    def chip(wl, n=None):
        """Form chips, oldest first. wl is "W"/"L", each followed by "y" for a youth event (an outlined chip)."""
        res = re.findall(r"[WL]y?", wl)[:n]
        return "".join(f'<i class="{"w" if c[0] == "W" else "l"}{" y" if len(c) > 1 else ""}" title="{"Won" if c[0] == "W" else "Lost"}{", youth event" if len(c) > 1 else ""}">{c[0]}</i>'
                       for c in reversed(res))

    def rank_of(p):
        return rk.get(p.get("ittf_id") or "")

    def move(r):
        if not r or not r.get("prev"):
            return ""
        d_ = r["prev"] - r["rank"]
        return f'<span class="ch-mv {"up" if d_ > 0 else "dn" if d_ < 0 else ""}">{("+" if d_ > 0 else "") + str(d_) if d_ else "="}</span>'

    def flag(nat):
        import components
        return components.flag(nat)

    def plink(p):
        return f'{BASE}/defender/{slug(p["name"])}.html'

    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(os.path.join(OUT, "defender"), exist_ok=True)
    shutil.copy(os.path.join(ROOT, "tools", "chop.css"), os.path.join(OUT, "chop.css"))
    shutil.copy(os.path.join(ROOT, "tools", "chop.js"), os.path.join(OUT, "chop.js"))
    shutil.copy(os.path.join(ROOT, "tools", "chop.svg"), os.path.join(OUT, "chop.svg"))
    import hashlib
    VER = hashlib.md5((open(os.path.join(OUT, "chop.css"), "rb").read() + open(os.path.join(OUT, "chop.js"), "rb").read())).hexdigest()[:8]

    # Eleven's own pieces about defenders: articles and stories that name a defender with a defensive word, or are about defence
    def_words = re.compile(r"\b(chop|chopper|choppers|chopping|defender|defenders|defensive|defence|backspin)\b", re.I)
    eleven = []
    seen = {l["url"] for l in links}
    for f in glob.glob(os.path.join(ROOT, "data", "articles", "*.json")):
        a = load(os.path.relpath(f, ROOT), {})
        txt = " ".join([a.get("title", ""), a.get("standfirst", "")] + a.get("body", []))
        head = a.get("title", "") + " " + a.get("standfirst", "")
        if len(def_words.findall(txt)) >= 6 or (len(def_words.findall(txt)) >= 2 and any(p["name"] in head for p in players)):
            url = f'{ELEVEN}/news/{a["slug"]}.html'
            if url not in seen:
                who = [p["name"] for p in players if p["name"] in txt]
                eleven.append({"url": url, "title": a["title"], "source": "Eleven", "date": (a.get("published") or a.get("date", ""))[:10],
                               "summary": a.get("standfirst", ""), "players": who, "kind": "analysis" if a.get("category") == "Features" else "news", "eleven": True})
    # Eleven is at most a quarter of what The Chop shows: its newest pieces up to a third of the outside links
    eleven.sort(key=lambda l: l.get("date") or "", reverse=True)
    eleven = eleven[:len(links) // 3]
    allinks = sorted(links + eleven, key=lambda l: l.get("date") or "", reverse=True)

    def capped(rows, n):
        """The first n rows with Eleven's pieces spread out: at most one in every four places (2nd, 6th, 10th...)."""
        ext = [l for l in rows if not l.get("eleven")]
        el = [l for l in rows if l.get("eleven")]
        out = []
        while len(out) < n and (ext or el):
            if len(out) % 4 == 1 and el:
                out.append(el.pop(0))
            elif ext:
                out.append(ext.pop(0))
            else:
                break
        return out

    def link_li(l, show_players=True):
        who = [p for p in players if p["name"] in (l.get("players") or [])]
        tags = "".join(f'<a class="ch-tag" href="{plink(p)}">{e(p["name"])}</a>' for p in who) if show_players else ""
        src = f'<span class="ch-src{" ch-eleven" if l.get("eleven") else ""}">{e(l.get("source", ""))}</span>'
        return (f'<li class="ch-link"><a class="ch-link-a" href="{e(l["url"])}"{"" if l.get("eleven") else " rel=\"noopener\" target=\"_blank\""}>'
                f'<span class="ch-link-meta">{src}<span>{e(l.get("kind", "news").capitalize())}</span>{f"<time>{day(l["date"])}</time>" if l.get("date") else ""}</span>'
                f'<span class="ch-link-t">{e(l["title"])}</span><span class="ch-link-s">{e(l.get("summary", ""))}</span></a>'
                f'{f"<span class=\"ch-tags\">{tags}</span>" if tags else ""}</li>')

    # ---- Rankings
    def table(g):
        rows = sorted((p for p in players if p.get("gender") == g and rank_of(p)), key=lambda p: rank_of(p)["rank"])
        out = []
        for i, p in enumerate(rows, 1):
            r = rank_of(p)
            _, wl, rec, yrec = form(p)
            empty = not wl
            out.append(f'<tr><td class="ch-n">{i}</td><td class="ch-wr">{r["rank"]}{move(r)}</td>'
                       f'<td><a href="{plink(p)}">{flag(r.get("nat"))}{e(p["name"])}</a><span class="ch-sty">{tag(p.get("style"))}</span></td>'
                       f'<td class="ch-pts">{r.get("points", 0):,}</td>'
                       + (f'<td class="ch-frm" colspan="2"><span class="ch-none">No results on record {INFO}</span></td></tr>' if empty else
                          f'<td class="ch-frm">{chip(wl, 5)}</td><td class="ch-rec">{recs(rec, yrec)}</td></tr>'))
        return rows, ("<table class=\"ch-table\"><thead><tr><th>#</th><th>World</th><th>Player</th><th>Points</th>"
                      f"<th>Form {INFO}</th><th title=\"Singles won and lost in {today[:4]}\">{today[:4]}</th></tr></thead><tbody>{''.join(out)}</tbody></table>"
                      '<p class="ch-small ch-key"><i class="ch-ychip">W</i> Outlined chips are youth events, counted apart in the record.</p>')

    INFO = ('<details class="ch-info"><summary aria-label="Why some players have no results">i</summary><div>'
            '<b>Where form comes from.</b> Form (the last five results) and the year\'s record cover senior WTT and ITTF events and the '
            'T.League and Bundesliga, the results Eleven keeps, plus WTT youth events from under-15 level up. Youth results are shown as '
            '<i class="ch-ychip">W</i> outlined chips and counted separately in the record, because young players can earn senior ranking points '
            'at youth events. A player can still be ranked with nothing here if they play mostly in national leagues and championships we '
            'don\'t yet have. Their results appear as soon as they play an event we follow.</div></details>')
    wrows, wtab = table("W")
    mrows, mtab = table("M")

    def unranked(g):
        """Defenders outside the world rankings who still play in the leagues Eleven follows."""
        rows = sorted((p for p in players if p.get("gender") == g and not rank_of(p)), key=lambda p: p["name"].split()[-1])
        if not rows:
            return ""
        out = []
        for p in rows:
            _, wl, rec, yrec = form(p)
            cl = ", ".join(f"{c} ({lg})" if lg else c for c, lg in clubs.get(p["name"], []))
            out.append(f'<tr><td><a href="{plink(p)}">{e(p["name"])}</a><span class="ch-sty">{tag(p.get("style"))}</span></td><td class="ch-club">{e(cl) or "-"}</td>'
                       + (f'<td class="ch-frm">{chip(wl, 5)}</td><td class="ch-rec">{recs(rec, yrec)}</td>' if wl else f'<td class="ch-frm" colspan="2"><span class="ch-none">No results on record {INFO}</span></td>') + '</tr>')
        return (f'<section class="ch-sec ch-unr"><h3>Not in the world rankings, still playing in the top leagues</h3>'
                f'<p class="ch-small">Defenders who don\'t play enough WTT events to hold a world ranking but play in the leagues Eleven follows.</p>'
                f'<table class="ch-table"><thead><tr><th>Player</th><th>Club</th><th>Form</th><th>{today[:4]}</th></tr></thead><tbody>{"".join(out)}</tbody></table></section>')
    wtab += unranked("W")
    mtab += unranked("M")
    dd = []
    did = {p["ittf_id"] for p in players}
    for g, lab in (("women", "Women's doubles"), ("men", "Men's doubles"), ("mixed", "Mixed doubles")):
        prs = [x for x in D.get(g, []) if any(pl.get("ittf_id") in did for pl in x["players"])]
        if prs:
            li = "".join(f'<tr><td class="ch-wr">{x["rank"]}</td><td>' + " / ".join(
                (f'<a href="{plink(next(p for p in players if p["ittf_id"] == pl.get("ittf_id")))}"><b>{e(pl["name"])}</b></a>' if pl.get("ittf_id") in did else e(pl["name"]))
                for pl in x["players"]) + f'</td><td class="ch-pts">{x.get("points", 0):,}</td></tr>' for x in prs)
            dd.append(f'<section class="ch-sec"><h3>{lab}</h3><table class="ch-table"><thead><tr><th>World</th><th>Pair</th><th>Points</th></tr></thead><tbody>{li}</tbody></table></section>')
    rbody = f"""<section class="ch-head"><h1>The defenders</h1>
<p class="ch-lede">Every defensive player in the world top 1,000, ranked by their place in the ITTF world rankings ({e(R.get("label", ""))}), with their last five results and this year's record. Select a player's name for their full profile, or a style tag to see what it means.</p></section>
<div class="ch-tabs" role="tablist"><button role="tab" aria-selected="true" data-t="W">Women ({len(wrows)})</button><button role="tab" aria-selected="false" data-t="M">Men ({len(mrows)})</button><button role="tab" aria-selected="false" data-t="D">Doubles</button></div>
<div class="ch-panel" data-p="W">{wtab}</div><div class="ch-panel" data-p="M" hidden>{mtab}</div>
<div class="ch-panel" data-p="D" hidden><p class="ch-small">Pairs in the doubles world rankings with at least one defender, the defender in bold.</p>{"".join(dd) or "<p>No ranked pairs.</p>"}</div>
<section class="ch-sec" id="styles"><h2>The styles</h2><dl class="ch-styles">{"".join(f"<div><dt>{tag(k, False)}</dt><dd>{e(v[0].upper() + v[1:])}.</dd></div>" for k, v in STYLE_ABOUT.items())}</dl>
<p class="ch-small">Long pimples alone don't make a defender: players who attack with long pimples or anti-spin are not included. Rankings from the <a href="{ELEVEN}/rankings.html">ITTF world rankings on Eleven</a>.</p></section>"""
    open(os.path.join(OUT, "defenders.html"), "w", encoding="utf-8").write(page(
        "Defensive table tennis players: rankings and form | The Chop", "Every chopper and defender in the table tennis world top 1,000: rankings, form and records.", "/defenders.html", rbody, "rankings"))

    # ---- Player pages
    for p in players:
        r = rank_of(p)
        last, wl, rec, yrec = form(p)
        nx = nxt.get(p["name"], [])[:5]
        mine = capped([l for l in allinks if p["name"] in (l.get("players") or [])], 12)
        es = next((v for k, v in prof.items() if k == p["name"]), None)
        bio = load(f"data/players/{slug(p['name'])}.json", {}) if es else {}
        hon = [(str(h.get("year", "")), f'{h.get("event", "")}', h.get("result", "")) for h in bio.get("honours") or []]
        tl = sorted(set(titles.get(p.get("ittf_id"), [])), key=lambda t: (t[0], "singles" in t[2]), reverse=True)
        hon_html = "".join(f'<li><span class="ch-yr">{e(y)}</span><span><b>{e(r)}</b> {e(ev)}</span></li>' for y, ev, r in sorted(hon, reverse=True))
        hon_html += "".join(f'<li><span class="ch-yr">{e(y)}</span><span><b>Winner</b> {e(ev)}, {e(k_)}</span></li>' for y, ev, k_ in tl[:12])
        cl = clubs.get(p["name"], []) or [(c.get("club"), c.get("league", "")) for c in bio.get("clubs") or [] if c.get("current")]
        wd_html = "".join(f'<li><q>{e(w["text"])}</q> <a href="{e(w["url"])}" rel="noopener" target="_blank">{e(w["source"])}</a></li>' for w in p.get("wording") or [])
        prov = "" if p.get("subtype_confirmed") else '<p class="ch-small">The sources confirm a defensive style; which of the three types fits best is our provisional call until a source describes the game in more detail.</p>'
        cl_html = "".join(f'<li><b>{e(c)}</b>{f" <span>{e(lg)}</span>" if lg else ""}</li>' for c, lg in cl)
        nxt_html = "".join(f'<li><time datetime="{e(x["when"])}">{day(x["when"]) if x.get("day") else dt.datetime.fromisoformat(x["when"].replace("Z", "+00:00")).strftime("%a %-d %b, %H:%M")} UK</time>'
                           f'<span>{e(x["what"])}{f" v <b>{e(x["v"])}</b>" if x.get("v") else ""}{watch(x)}</span></li>' for x in nx)
        body = f"""<p class="ch-crumbs"><a href="{BASE}/defenders.html">The defenders</a> / {e(p["name"])}</p>
<section class="ch-phead"><div><p class="ch-kick">{tag(p.get("style"))}</p><h1>{flag(r.get("nat") if r else "")}{e(p["name"])}</h1>
<p class="ch-lede">{e(p.get("note", ""))}</p></div>
<dl class="ch-facts"><div><dt>World ranking</dt><dd>{f'No {r["rank"]}{move(r)}' if r else "Unranked"}</dd></div>
<div><dt>Points</dt><dd>{f'{r["points"]:,}' if r else "-"}</dd></div><div><dt>{today[:4]} record</dt><dd>{recs(rec, yrec)}</dd></div>
<div><dt>Last 10</dt><dd class="ch-frm">{chip(wl) or "-"}</dd></div>
<div><dt>Age</dt><dd>{age_of(p) or "-"}</dd></div><div><dt>Club</dt><dd class="ch-fclub">{e(", ".join(c for c, _ in cl) or "-")}</dd></div></dl></section>
<div class="ch-grid"><section class="ch-sec"><h2>Recent results</h2><ul class="ch-results">{"".join(res_row(m, s) for m, s in last) or "<li>No senior or club results on record.</li>"}</ul>
{f'<h3>Youth events</h3><ul class="ch-results">{"".join(youth_row(m, s) for m, s in youth.get(p.get("ittf_id"), [])[:8])}</ul>' if youth.get(p.get("ittf_id")) else ""}</section>
<section class="ch-sec"><h2>Next matches</h2>{likely_html(likely(p))}<ul class="ch-next">{nxt_html or "<li>No match scheduled in Eleven's tournament draws or club fixtures yet.</li>"}</ul>
{f'<p class="ch-small"><a href="{ELEVEN}{es}">Full profile on Eleven</a>: titles, head to heads and ranking history.</p>' if es else ""}</section></div>
<div class="ch-grid"><section class="ch-sec"><h2>Honours and titles</h2>{f'<ul class="ch-hon">{hon_html}</ul>' if hon_html else "<p class='ch-small'>No major medals or senior titles on record yet.</p>"}</section>
<section class="ch-sec"><h2>Club</h2>{f'<ul class="ch-clubs">{cl_html}</ul>' if cl_html else "<p class='ch-small'>No club in the leagues Eleven follows.</p>"}</section></div>
{points_html(p)}
{f'<section class="ch-sec"><h2>How the sources describe the style</h2><ul class="ch-quotes">{wd_html}</ul>{prov}</section>' if wd_html else ""}
<section class="ch-sec"><h2>Reading</h2>{f'<ul class="ch-links">{"".join(link_li(l, False) for l in mine)}</ul>' if mine else "<p>No stories linked yet.</p>"}</section>"""
        open(os.path.join(OUT, "defender", slug(p["name"]) + ".html"), "w", encoding="utf-8").write(page(
            f'{p["name"]}: {STYLE.get(p.get("style"), "defender").lower()}, rankings and form | The Chop',
            f'{p["name"]}, {STYLE.get(p.get("style"), "defender").lower()}: world ranking, recent results, next matches and stories.',
            f'/defender/{slug(p["name"])}.html', body))

    # ---- Recent results of every defender (senior WTT and ITTF events and club matches), newest first.
    # Built from data/matches (match-sync workflow) and data/clubs and data/leagues (club-sync and league-sync), so it updates itself.
    RECENT_DAYS = 14
    allrec = []
    for p in players:
        for m, s in ms.get(p.get("ittf_id"), []):
            if (m.get("d") or "") >= (now - dt.timedelta(days=RECENT_DAYS)).isoformat()[:19] and m.get("w") in (0, 1):
                allrec.append((m["d"], p, m, s))
    allrec.sort(key=lambda t: t[0], reverse=True)

    def rec_li(p, m, s, show_day=True):
        row = res_row(m, s)
        cls = re.match(r'<li class="(\w)">', row).group(1)
        inner = row[len(f'<li class="{cls}">'):-len("</li>")]
        if not show_day:
            inner = re.sub(r" · [^<]*</span>$", "</span>", inner)
        return f'<li class="{cls}"><a href="{plink(p)}"><b>{e(p["name"])}</b></a> {inner}</li>'

    # ---- Calendar: likely next tournaments (grouped by event), then fixtures by day, then recent results
    cal = []
    for p in players:
        for x in nxt.get(p["name"], []):
            cal.append((x["when"], p, x))
    cal.sort(key=lambda t: t[0])
    by_ev = {}
    for p in players:
        lk = likely(p)
        if lk and lk["kind"] in ("likely", "draw"):
            by_ev.setdefault((lk.get("start") or (lk.get("when") or "")[:10], lk["event"], lk["kind"]), []).append((p, lk))
    ev_cards = []
    for (st, evn, _k), who in sorted(by_ev.items()):
        lk0 = who[0][1]
        when_ = span(lk0["start"], lk0["end"]) if lk0.get("start") else day(lk0["when"])
        ppl = "".join(f'<li><a href="{plink(p)}">{e(p["name"])}</a> {tag(p.get("style"))}<span class="ch-why">{e(lk["why"])}</span></li>' for p, lk in who)
        head = f'<a href="{e(lk0["url"])}">{e(evn)}</a>' if lk0.get("url") else e(evn)
        ev_cards.append(f'<li class="ch-evcard"><span class="ch-kick">{"In the draw" if lk0["kind"] == "draw" else "Likely"}</span><h3>{head}</h3>'
                        f'<p class="ch-evwhen">{e(when_)}{", " + e(lk0.get("city", "")) if lk0.get("city") else ""}</p>{watch(eid=lk0.get("eid"))}<ul>{ppl}</ul></li>')
    days_, cur = [], None
    for w, p, x in cal:
        d0 = w[:10]
        if d0 != cur:
            cur = d0
            dd = dt.date.fromisoformat(d0)
            days_.append([f"{dd:%A} {dd.day} {dd:%B %Y}", []])
        t = "" if x.get("day") else dt.datetime.fromisoformat(w.replace("Z", "+00:00")).strftime("%H:%M")
        comp, _, tie = x["what"].partition(": ")
        days_[-1][1].append(f'<li class="ch-fx"><span class="ch-fx-t">{e(t) or "TBC"}</span><span class="ch-fx-who"><a href="{plink(p)}">{e(p["name"])}</a> {tag(p.get("style"))}</span>'
                            f'<span class="ch-fx-what"><b>{e(comp)}</b> {e(tie)}{f" v {e(x["v"])}" if x.get("v") else ""}{watch(x)}</span></li>')
    fx = "".join(f'<section class="ch-day"><h3>{e(h)}</h3><ul>{"".join(it)}</ul></section>' for h, it in days_)
    rdays, cur = [], None
    for d_, p, m, s in allrec:
        if d_[:10] != cur:
            cur = d_[:10]
            dd = dt.date.fromisoformat(cur)
            rdays.append([f"{dd:%A} {dd.day} {dd:%B %Y}", []])
        rdays[-1][1].append(rec_li(p, m, s, show_day=False))
    rx = "".join(f'<section class="ch-day"><h3>{e(h)}</h3><ul class="ch-results ch-recent">{"".join(it)}</ul></section>' for h, it in rdays)
    cbody = f"""<section class="ch-head"><h1>Calendar</h1><p class="ch-lede">Where the defenders are likely to play next, every fixture we know of, with links to live scores and streams where they exist, and their latest results. Times are UK time. <a href="#results">Recent results</a></p></section>
<section class="ch-sec"><h2>Likely next tournaments</h2><p class="ch-small">Entry lists are only published with the draw, so these are our best guesses: the next event of a kind each player has entered in the past year and can get into on their ranking. Players move to "In the draw" when it's published.</p>
<ul class="ch-evcards">{"".join(ev_cards) or "<li>No tournaments in view.</li>"}</ul></section>
<section class="ch-sec" id="matches"><div class="ch-tabs" role="tablist" aria-label="Fixtures and results"><button type="button" role="tab" data-t="fixtures" aria-selected="true">Fixtures</button><button type="button" role="tab" data-t="results" aria-selected="false">Recent results</button></div>
<div class="ch-panel" data-p="fixtures" id="fixtures"><h2 class="sr-only">Fixtures</h2>{fx or "<p>Nothing scheduled yet.</p>"}</div>
<div class="ch-panel" data-p="results" id="results" hidden><h2 class="sr-only">Recent results</h2><p class="ch-small">Every result for the defenders in the last {RECENT_DAYS} days, at WTT and ITTF events and in the club leagues, newest first. Updated automatically as results come in.</p>{rx or "<p>No results in the last two weeks.</p>"}</div></section>"""
    open(os.path.join(OUT, "calendar.html"), "w", encoding="utf-8").write(page(
        "When the defenders play next | The Chop", "Where table tennis's choppers and defenders are likely to play next, their upcoming fixtures and their latest results.", "/calendar.html", cbody, "calendar"))

    # ---- Reading
    kinds = [("all", "All")] + [(k, k.capitalize()) for k in ("news", "analysis", "history", "video") if any(l.get("kind") == k for l in allinks)]
    rbody = f"""<section class="ch-head"><h1>Reading</h1><p class="ch-lede">The best writing on defensive table tennis: news, analysis and history from around the game, with a line from us on each.</p></section>
<div class="ch-tabs ch-filter" role="group">{"".join(f'<button aria-pressed="{str(k == "all").lower()}" data-k="{k}">{lab}</button>' for k, lab in kinds)}</div>
<ul class="ch-links">{"".join(link_li(l).replace('<li class="ch-link">', f'<li class="ch-link" data-k="{e(l.get("kind", "news"))}">', 1) for l in allinks)}</ul>"""
    open(os.path.join(OUT, "reading.html"), "w", encoding="utf-8").write(page(
        "Reading: choppers and defensive table tennis | The Chop", "News, analysis and history of defensive table tennis and its choppers, from around the web.", "/reading.html", rbody, "reading"))

    # ---- Legends: the great defenders of the past, from data/chop/legends.json
    legends = load("data/chop/legends.json", [])
    import components
    lg_html = "".join(
        f'<li class="ch-legend"><div class="ch-legend-h"><h2>{components.flag(l.get("nat"))}{e(l["name"])}</h2>{tag(l.get("style"))}</div>'
        f'<p class="ch-era">{e(l.get("era", ""))}</p><p>{e(l["summary"])}</p>'
        + "".join(f'<a class="ch-more" href="{e(u)}" rel="noopener" target="_blank">Source</a> ' for u in l.get("sources", [])[:1])
        + (lambda mine: f'<ul class="ch-links">{"".join(link_li(x, False) for x in mine)}</ul>' if mine else "")(
            [x for x in allinks if x.get("kind") == "history" and l["name"].split()[-1] in x["title"] + x.get("summary", "")][:3])
        + "</li>" for l in legends)
    lbody = f"""<section class="ch-head"><h1>Legends</h1><p class="ch-lede">The great defenders of the past, from Richard Bergmann's world titles in the 1930s to the choppers who kept the style alive in the modern game.</p></section>
<ul class="ch-legends">{lg_html}</ul>"""
    open(os.path.join(OUT, "legends.html"), "w", encoding="utf-8").write(page(
        "Legends of defensive table tennis | The Chop", "The great choppers and defenders in table tennis history, from Richard Bergmann to Joo Se-hyuk.", "/legends.html", lbody, "legends"))

    # ---- Videos: data/chop/videos.json (tools/chop_videos.py), newest first, 20 a page; click to play (youtube-nocookie)
    VIDS = load("data/chop/videos.json", [])
    vfeat = load("data/chop/video-sources.json", {}).get("players", [])
    pbn = {p["name"]: p for p in players}
    PER = 20
    pages_ = [VIDS[i:i + PER] for i in range(0, len(VIDS), PER)] or [[]]
    vurl = lambda n: "/videos.html" if n == 1 else f"/videos-{n}.html"
    vurls = []
    for n, chunk in enumerate(pages_, 1):
        cards = "".join(
            f'<li class="ch-vid"><button type="button" class="ch-yt" data-yt="{e(v["id"])}" aria-label="Play: {e(v["title"])}">'
            f'<img src="https://i.ytimg.com/vi/{e(v["id"])}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360"><span class="ch-play" aria-hidden="true"></span></button>'
            f'<p class="ch-vid-t">{e(v["title"])}</p><p class="ch-vid-m"><time datetime="{e(v["date"][:7] if v.get("approx") else v["date"])}">{dt.date.fromisoformat(v["date"][:10]).strftime("%b %Y") if v.get("approx") else day(v["date"])}</time> · {e(v.get("channel", "YouTube"))}'
            + "".join(f' · <a href="{plink(pbn[x])}">{e(x)}</a>' for x in v.get("players", []) if x in pbn) + '</p></li>' for v in chunk)
        nav_ = "".join(f'<a href="{BASE}{vurl(k)}"{" aria-current=\"page\"" if k == n else ""}>{k}</a>' for k in range(1, len(pages_) + 1)) if len(pages_) > 1 else ""
        names_ = ", ".join(vfeat[:-1]) + (" and " + vfeat[-1] if len(vfeat) > 1 else "".join(vfeat))
        vbody = f"""<section class="ch-head"><h1>Videos</h1><p class="ch-lede">Every video of {e(names_)} on World Table Tennis's YouTube channel, newest first. Updated through the day.</p></section>
<ul class="ch-vids">{cards or "<li>No videos yet.</li>"}</ul>{f'<nav class="ch-pager" aria-label="Pages">{nav_}</nav>' if nav_ else ""}"""
        open(os.path.join(OUT, vurl(n).lstrip("/")), "w", encoding="utf-8").write(page(
            f'Videos{f" (page {n})" if n > 1 else ""} | The Chop', f"Videos of {names_}, newest first.", vurl(n), vbody, "videos"))
        vurls.append(vurl(n))

    # ---- Glossary
    abody = f"""<section class="ch-head"><h1>Glossary</h1><p class="ch-lede">The terms used for defensive table tennis, and how The Chop works.</p></section>
<section class="ch-sec" id="glossary"><h2>Terms</h2><dl class="ch-styles">{"".join(f"<div><dt>{e(t)}</dt><dd>{e(d)}</dd></div>" for t, d in GLOSSARY)}</dl></section>
<section class="ch-sec" id="styles"><h2>The three styles</h2><dl class="ch-styles">{"".join(f"<div><dt>{tag(k, False)}</dt><dd>{e(v[0].upper() + v[1:])}.</dd></div>" for k, v in STYLE_ABOUT.items())}</dl></section>
<section class="ch-sec"><h2>How it works</h2><p>Players are listed only when a source we can open describes them as a defender. Rankings, results and fixtures come from Eleven, which takes them from World Table Tennis and the leagues. Reading links go to the publication that wrote each piece; Eleven's own pieces are marked and kept to a quarter at most.</p></section>"""
    open(os.path.join(OUT, "glossary.html"), "w", encoding="utf-8").write(page(
        "Glossary | The Chop", "The terms used for defensive table tennis: chop, float, long pimples, the expedite rule and more.", "/glossary.html", abody, "glossary"))

    # ---- Home
    week = [(w, p, x) for w, p, x in cal if w <= (now + dt.timedelta(days=7)).isoformat()]
    top_w = wrows[:5]
    top_m = mrows[:5]
    mini = lambda rows: "".join(f'<li><span class="ch-wr">{rank_of(p)["rank"]}</span><a href="{plink(p)}">{e(p["name"])}</a>{tag(p.get("style"), False)}</li>' for p in rows)
    hbody = f"""<section class="ch-hero"><h1>The game from the back of the court</h1>
<p class="ch-lede">Choppers and defenders: who they are, how they are playing and the best writing about them. {len(wrows)} women and {len(mrows)} men in the world top 1,000 play this way.</p></section>
<div class="ch-home">
<section class="ch-sec ch-main"><h2>Latest reading</h2><ul class="ch-links">{"".join(link_li(l) for l in capped(allinks, 6))}</ul><a class="ch-more" href="{BASE}/reading.html">All reading</a></section>
<aside class="ch-side">
<section class="ch-sec"><h2>Top defenders</h2><h3>Women</h3><ol class="ch-mini">{mini(top_w)}</ol><h3>Men</h3><ol class="ch-mini">{mini(top_m)}</ol><a class="ch-more" href="{BASE}/defenders.html">All the defenders</a></section>
<section class="ch-sec"><h2>Recent results</h2><ul class="ch-results">{"".join(rec_li(p, m, s) for _, p, m, s in allrec[:6]) or "<li>No results for the defenders in the last two weeks.</li>"}</ul><a class="ch-more" href="{BASE}/calendar.html#results">All recent results in the calendar</a></section>
<section class="ch-sec"><h2>Coming up</h2><ul class="ch-evcards ch-evcards-side">{"".join(ev_cards[:3])}</ul>
<h3>This week</h3><ul class="ch-cal">{"".join(f'<li><time>{day(w)}</time><a href="{plink(p)}"><b>{e(p["name"])}</b></a><span>{e(x["what"])}{watch(x)}</span></li>' for w, p, x in week[:6]) or "<li>No defenders scheduled this week.</li>"}</ul><a class="ch-more" href="{BASE}/calendar.html">Full calendar</a></section>
</aside></div>"""
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page(
        "The Chop: choppers and defensive table tennis", "Choppers and defenders in table tennis: rankings, form, fixtures and the best writing about them.", "/", hbody, "home"))

    # ---- 404: served by Cloudflare for any missing address on the subdomain (wrangler.jsonc "not_found_handling")
    nbody = f"""<section class="ch-head"><h1>Sorry, we can't find that page</h1><p class="ch-lede">It may have moved, or the address may have a typo.</p></section>
<section class="ch-sec"><h2>Try</h2><ul class="ch-links-plain"><li><a href="{BASE}/defenders.html">The defenders</a>: rankings, form and profiles</li>
<li><a href="{BASE}/calendar.html">Calendar</a>: when the defenders play next</li><li><a href="{BASE}/reading.html">Reading</a>: the best writing about them</li>
<li><a href="{BASE}/videos.html">Videos</a></li><li><a href="{BASE}/legends.html">Legends</a></li><li><a href="{BASE}/">Home</a></li></ul></section>"""
    nf_html = page("Page not found | The Chop", "The page you were looking for isn't on The Chop.", "/404.html", nbody)
    for nf_name in ("404.html", "not-found.html"):   # worker.js serves not-found.html for missing pages on the subdomain
        open(os.path.join(OUT, nf_name), "w", encoding="utf-8").write(nf_html)

    urls = ["/", "/defenders.html", "/calendar.html", "/reading.html", "/legends.html", "/glossary.html"] + vurls + [f'/defender/{slug(p["name"])}.html' for p in players]
    open(os.path.join(OUT, "chop-sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls) + "</urlset>")
    return len(players), len(allinks)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    print("The Chop:", build())
