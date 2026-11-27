"""Club table tennis: a hub at /clubs/ and one page per league, built from data/clubs/<competition>.json.

Each league page pairs the men's and women's competitions at equal size (tables side by side, results and
fixtures merged and labelled), then the league's news. Leagues with a single mixed competition (MLTT, UTT)
have one table. Files with "auto": true are refreshed every hour by tools/club_sync.py; the others are kept
current by the scheduled update runs (UPDATE.md, "Club leagues").

News: a story belongs to a league if it has "league": "<slug>" in data/news.json, or if it is in the Clubs
category and its headline or summary names the league (see LEAGUES[...]["match"]).
"""
import json, os, re, html, datetime as dt
import explainers
from zoneinfo import ZoneInfo

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UK = ZoneInfo("Europe/London")

LEAGUES = [
    {"slug": "bundesliga", "name": "Bundesliga", "country": "Germany", "flag": "de", "colour": "#c8102e",
     "comps": [("ttbl", "Men", "TTBL"), ("dttbl-women", "Women", "1. Bundesliga")],
     "match": r"\bTTBL\b|Tischtennis Bundesliga|\bBundesliga\b",
     "about": "Germany's leagues are the strongest in Europe. The men's TTBL has 12 clubs playing best-of-five team matches, with the top four going into the play-offs and the Final4. The women's 1. Bundesliga has eight clubs."},
    {"slug": "super-league", "name": "China Super League", "country": "China", "flag": "cn", "colour": "#de2910",
     "comps": [("cttsl-men", "Men", "Super League"), ("cttsl-women", "Women", "Super League")],
     "match": r"Super League|乒超|\bCTTSL\b",
     "about": "The Chinese Table Tennis Super League brings China's national team players together in club colours. The 2026 season has 10 men's and eight women's teams, with the top four of each going to the finals."},
    {"slug": "t-league", "name": "T.League", "country": "Japan", "flag": "jp", "colour": "#1d3f8f",
     "comps": [("tleague-men", "Men", "T.League"), ("tleague-women", "Women", "T.League")],
     "match": r"\bT\.? ?League\b",
     "about": "Japan's professional league, founded in 2018, has six men's and six women's teams. Matches are four rubbers, with a single-game Victory Match at 2-2, and the top two of each league meet in the play-off final."},
    {"slug": "pro-a", "name": "Pro A", "country": "France", "flag": "fr", "colour": "#0055a4",
     "comps": [("proa-men", "Men", "Pro A"), ("proa-women", "Women", "Pro A")],
     "match": r"\bPro A\b",
     "about": "France's top division has 10 men's and 12 women's clubs. Each team match is best of five, and the regular season leads into play-offs for the title."},
    {"slug": "british-league", "name": "British Clubs League", "country": "Britain", "flag": "gb", "colour": "#012169",
     "comps": [("bcl-men", "Men", "Premier Division"), ("bcl-women", "Women", "Premier Division")],
     "match": r"British (?:Clubs? )?League|\bBCL\b",
     "about": "Table Tennis England's British Clubs League is the top level of club team table tennis in Britain, with clubs from England, Scotland and Northern Ireland in this season's Premier Divisions: eight senior teams and six women's teams, who meet at weekend gatherings through the season."},
    {"slug": "champions-league", "name": "Champions League", "country": "Europe", "flag": "eu", "colour": "#0b2f6b",
     "comps": [("cl-men", "Men", "HYLO ETTU Champions League"), ("cl-women", "Women", "ETTU Champions League")],
     "match": r"Champions League|Europe Cup",
     "about": "The European Table Tennis Union's club competitions. Since 2026-27 both start with a central Stage 1 for the qualifiers, who join the seeded clubs in Stage 2."},
    {"slug": "mltt", "name": "Major League Table Tennis", "country": "United States", "flag": "us", "colour": "#0a3161",
     "comps": [("mltt", "Mixed", "MLTT")],
     "match": r"\bMLTT\b|Major League Table Tennis",
     "about": "America's professional league has 10 mixed teams in East and West divisions. Teams meet at weekend events around the country, with the play-offs in the spring."},
    {"slug": "utt", "name": "Ultimate Table Tennis", "country": "India", "flag": "in", "colour": "#ff671f",
     "comps": [("utt", "Mixed", "UTT")],
     "match": r"\bUTT\b|Ultimate Table Tennis",
     "about": "India's franchise league packs its season into a few weeks each summer. Mixed teams play singles and mixed doubles over three games each, with a Golden Point to settle ties."},
]
COLS = {"p": ("P", "Played"), "w": ("W", "Won"), "d": ("D", "Drawn"), "l": ("L", "Lost"), "pts": ("Pts", "Points"),
        "games": ("Games", "Games won and lost"), "matches": ("Matches", "Individual matches won and lost"), "points": ("Points", "Points won and lost")}


def load_squads(cid):
    path = os.path.join(ROOT, "data", "clubs", "squads", f"{cid}.json")
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return None


def squads_html(comps, profiles):
    """Every team's squad, men's and women's competitions side by side, players linked to their profiles."""
    import components, unicodedata
    def key(n):
        n = unicodedata.normalize("NFKD", n or "").encode("ascii", "ignore").decode().lower()
        return " ".join(sorted(re.findall(r"[a-z]+", n)))
    by_key = {key(n): (n, u) for n, u in profiles.items()}
    def link(name):
        hit = by_key.get(key(name))
        return f'<a href="{hit[1]}">{e(hit[0])}</a>' if hit else e(name)
    blocks = []
    for cid, tag, title, _ in comps:
        sq = load_squads(cid)
        if not sq or not sq.get("teams"):
            continue
        cards = []
        for t in sorted(sq["teams"], key=lambda t: t["team"]):
            lis = "".join(
                f'<li>{components.flag(p.get("nat")) if p.get("nat") else ""}'
                + link(p["name"]) + (f' <span class="cl-rec">{e(p["rec"])}</span>' if p.get("rec") else "") + "</li>"
                for p in t["players"])
            coach = f'<p class="cl-coach">Coach: {e(t["coach"])}</p>' if t.get("coach") else ""
            cards.append(f'<div class="cl-squad"><h4>{e(t["team"])}</h4><ul>{lis}</ul>{coach}</div>')
        note = f' {e(sq["note"])}' if sq.get("note") else ""
        src = sq.get("source") or {}
        upd = sq.get("updated")
        blocks.append(f'<div class="cl-comp"><h3 class="cl-comp-h"><span class="cl-tag">{e(tag)}</span>{e(title)} squads</h3><div class="cl-squads">{"".join(cards)}</div>'
                      f'<p class="cl-note">From <a href="{e(src.get("url", "#"))}" rel="noopener">{e(src.get("name", ""))}</a>'
                      f'{f", checked {uk(upd).day} {uk(upd):%B %Y}" if upd else ""}.{note}</p></div>')
    return "".join(blocks)


def load(cid):
    p = os.path.join(ROOT, "data", "clubs", f"{cid}.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def uk(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(UK)


def when_html(m, with_day=True):
    if not m.get("when"):
        return '<span class="cl-when tbc"></span>'
    t = uk(m["when"])
    if m.get("date_only") or m.get("tbc"):
        txt = f"{t:%a} {t.day} {t:%b}" if with_day else ("" if m.get("score") is not None else "Time tbc")
        return f'<span class="cl-when">{txt}</span>'
    fmt = "dhm" if with_day else "hm"
    txt = f"{t:%a} {t.day} {t:%b}, {t:%H:%M}" if with_day else f"{t:%H:%M}"
    return f'<span class="cl-when"><time datetime="{e(m["when"])}" data-lt="{fmt}">{txt}</time></span>'


def table_html(d, label):
    """One competition's table (or its groups)."""
    tab = (d or {}).get("table") or {}
    groups = [g for g in tab.get("groups") or [] if g.get("rows")]
    if not groups:
        return f'<p class="cl-none">{e((d or {}).get("note") or "The table appears here once the season starts.")}</p>'
    cols = tab.get("columns") or []
    out = []
    for g in groups:
        head = "".join(f'<th scope="col" title="{COLS[c][1]}">{COLS[c][0]}</th>' for c in cols)
        rows = []
        for r in g["rows"]:
            cells = []
            for c in cols:
                if c in ("games", "matches", "points"):
                    v = f'{r.get("for", "")}-{r.get("against", "")}' if r.get("for") is not None else ""
                else:
                    v = r.get(c, "")
                cells.append(f'<td{" class=pts" if c == "pts" else ""}>{e(str(v))}</td>')
            rows.append(f'<tr{" class=q" if r.get("q") else ""}><td class="pos">{r["pos"]}</td><th scope="row">{e(r["team"])}</th>{"".join(cells)}</tr>')
        cap = f'<caption>{e(g["name"])}</caption>' if g.get("name") else f'<caption class="sr-only">{e(label)} table</caption>'
        out.append(f'<table class="cl-table">{cap}<thead><tr><th scope="col" class="pos">#</th><th scope="col">Team</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>')
    note = f'<p class="cl-note">{e(tab["note"])}</p>' if tab.get("note") else ""
    return "".join(out) + note


def match_row(m, tag=None, league=None, with_day=False):
    played = m.get("score") is not None
    live = m.get("status") == "live"
    if m.get("label"):   # an event rather than a match, e.g. "finals begin"
        return f'<li class="cl-m ev">{when_html(m, with_day)}<span class="cl-ev">{e(m["label"])}</span></li>'
    sc = m.get("score") or [None, None]
    win = (0 if sc[0] > sc[1] else 1) if played and not live and sc[0] != sc[1] else None
    side = lambda i, name: f'<span class="cl-t{" won" if win == i else ""}">{e(name)}</span>'
    mid = (f'<b class="cl-sc{" live" if live else ""}">{sc[0]}<i>-</i>{sc[1]}</b>' if played else '<b class="cl-sc v">v</b>')
    meta = " · ".join(x for x in (tag, league, m.get("round") if m.get("when") else None, m.get("venue")) if x)
    live_at = f' data-when="{e(m["when"])}" data-home="{e(m["home"])}"' if m.get("when") and m.get("status") != "finished" and not m.get("date_only") else ""   # clublive.js fills in live scores
    return (f'<li class="cl-m{" done" if played else ""}{" is-live" if live else ""}"{live_at}>{when_html(m, with_day)}'
            f'<span class="cl-pair">{side(0, m["home"])}{mid}{side(1, m["away"])}</span>'
            f'{f"<span class=cl-meta>{e(meta)}</span>" if meta else ""}</li>')


def merged(lg, kind, n, now):
    """Results (newest first) or fixtures (soonest first) across the league's competitions."""
    items = []
    for cid, tag, _ in lg["comps"]:
        d = load(cid) or {}
        for m in d.get("matches") or []:
            done = m.get("score") is not None
            if kind == "results" and done:
                items.append((m, tag))
            elif kind == "fixtures" and not done and (not m.get("when") or m["when"] >= (now - dt.timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M")):
                items.append((m, tag))
    rn = lambda m: int((re.findall(r"\d+", m.get("round") or "") or [0])[0])
    key = lambda x: (x[0].get("when") or ("0000" if kind == "results" else "9999"), rn(x[0]))
    items.sort(key=key, reverse=kind == "results")
    return items[:n]


def grouped(items, mixed, league_of=None):
    """Matches under date headings, BBC Sport style."""
    out, last = [], None
    for m, tag in items:
        day = uk(m["when"]).date() if m.get("when") else (m.get("round") or "Dates to be confirmed")
        if day != last:
            if out:
                out.append("</ol>")
            out.append(f'<h3 class="cl-day">{f"{day:%A} {day.day} {day:%B}" if isinstance(day, dt.date) else e(day + ", dates to be confirmed" if not m.get("score") else day)}</h3><ol class="cl-list">')
            last = day
        out.append(match_row(m, None if mixed else tag, league_of(m) if league_of else None))
    if out:
        out.append("</ol>")
    return "".join(out)


def stories_for(lg, stories):
    rx = re.compile(lg["match"], re.I)
    return [s for s in stories if s.get("league") == lg["slug"] or (s.get("category") == "Clubs" and not s.get("league") and rx.search(s["title"] + " " + s.get("summary", "")))]


def news_list(items, n=8):
    if not items:
        return ""
    lis = "".join(f'<li><a href="{e(s["url"])}">{e(s["title"])}</a><span class="meta"><time datetime="{e(s["published"])}">{uk(s["published"]).day} {uk(s["published"]):%b}</time></span></li>' for s in items[:n])
    return f'<ul class="cl-news">{lis}</ul>'


def status_of(lg):
    ds = [load(c) or {} for c, _, _ in lg["comps"]]
    st = [d.get("status") for d in ds if d.get("status")]
    if st:
        return st[0]
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M")
    if any(m.get("status") == "live" for d in ds for m in d.get("matches") or []):
        return "Matches in play"
    left = [m for d in ds for m in d.get("matches") or [] if m.get("score") is None and (m.get("when") or "") >= now]
    return "Regular season" if left else "Season complete"


def league_page(lg, stories, now):
    comps = [(cid, tag, title, load(cid)) for cid, tag, title in lg["comps"]]
    mixed = len(comps) == 1
    season = next((d.get("season") for *_, d in comps if d and d.get("season")), "")
    seen = {}
    for *_, d in comps:
        if d and d.get("source"):
            seen.setdefault(d["source"]["name"], d["source"]["url"])
    for *_, d in comps:
        for x in (d or {}).get("sources") or []:
            seen.setdefault(x["name"], x["url"])
    srcs = ", ".join(list(f'<a href="{e(u)}" rel="noopener">{e(n)}</a>' for n, u in seen.items())[:-1]) + (" and " if len(seen) > 1 else "") + "".join(f'<a href="{e(u)}" rel="noopener">{e(n)}</a>' for n, u in list(seen.items())[-1:])
    upd = max((d.get("updated") or "" for *_, d in comps if d), default="")
    res, fix = merged(lg, "results", 12, now), merged(lg, "fixtures", 12, now)
    older = merged(lg, "results", 2000, now)[12:]
    more = (f'<details class="cl-all"><summary>All {len(older) + len(res)} results this season</summary>{grouped(older, mixed)}</details>') if older else ""
    tables = "".join(f'<div class="cl-comp"><h3 class="cl-comp-h"><span class="cl-tag">{e(tag)}</span>{e(title)}</h3>{table_html(d, f"{tag} {title}")}</div>' for cid, tag, title, d in comps)
    mine = stories_for(lg, stories)
    try:
        profiles = json.load(open(os.path.join(ROOT, "data", "profiles.json"), encoding="utf-8"))
    except Exception:
        profiles = {}
    squads = squads_html(comps, profiles)
    jump = "".join(f'<a href="#{k}">{v}</a>' for k, v in (("results", "Results"), ("fixtures", "Fixtures"), ("tables", "Tables"), ("squads", "Squads"), ("news", "News"), ("about", "About")) if (k != "news" or mine) and (k != "squads" or squads))
    body = f'''<main class="wrap cl-page" style="--tier:{lg["colour"]}">
<p class="crumbs"><a href="/">Home</a> / <a href="/clubs/">Club game</a> / {e(lg["name"])}</p>
<header class="hub-head cl-head"><div><span class="ev-group"><span class="fi fi-{lg["flag"]}" aria-hidden="true"></span> {e(lg["country"])}</span>
<h1>{e(lg["name"])} {e(season)}</h1><p class="cl-status">{e(status_of(lg))}</p></div></header>
<nav class="hub-jump" aria-label="On this page">{jump}</nav>
{explainers.combined(explainers.pick(["league:champions-league"], n=1) if lg["slug"] == "champions-league" else explainers.pick(["league:" + lg["slug"], "league"], n=2), explainers.analysis(tags=[lg["slug"]], words=[lg["name"]] + lg.get("aliases", []), keys=["league:" + lg["slug"]], n=1), "top")}
<div class="cl-hub-top"><section class="hub-sec" id="results"><h2 class="section-title">Results</h2>{grouped(res, mixed) or '<p class="cl-none">No results yet this season.</p>'}{more}</section>
<section class="hub-sec" id="fixtures"><h2 class="section-title">Fixtures</h2>{grouped(fix, mixed) or '<p class="cl-none">No fixtures published at the moment.</p>'}
<p class="small"><span data-tz-note>Times are UK time.</span> Times can change, so check with the clubs before travelling.</p></section></div>
<section class="hub-sec" id="tables"><h2 class="section-title">{"Table" if mixed else "Tables"}</h2><div class="cl-tables{" one" if mixed else ""}">{tables}</div></section>
{f'<section class="hub-sec" id="squads"><h2 class="section-title">Squads</h2>{squads}</section>' if squads else ""}
{f'<section class="hub-sec" id="news"><h2 class="section-title">News</h2>{news_list(mine, 12)}</section>' if mine else ""}
<section class="hub-sec" id="about"><h2 class="section-title">About the league</h2><p class="cl-about">{e(lg["about"])}</p>
<p class="small">Tables, fixtures and results from {srcs}{f', updated {uk(upd).day} {uk(upd):%B} at {uk(upd):%H:%M} UK time' if upd else ""}.</p></section>
</main>'''
    return body, season


def latest(now):
    """The club game's latest results and next fixtures across every league, as two HTML blocks (results, fixtures).
    Used on the Club game hub and the Tournaments page's Club fixtures tab."""
    allres, allfix = [], []
    for lg in LEAGUES:
        for m, tag in merged(lg, "results", 8, now):
            allres.append((m, tag, lg))
        for m, tag in merged(lg, "fixtures", 8, now):
            if m.get("when"):
                allfix.append((m, tag, lg))
    week = (now - dt.timedelta(days=10)).strftime("%Y-%m-%d")
    def every_league(items, recent, newest_first):
        """The nearest 10 matches overall, plus each league's nearest matchday (latest results or next fixtures) so a league
        that plays only every few weeks (the British Clubs League's weekends) is never crowded out by the weekly ones."""
        items = sorted(items, key=lambda x: x[0]["when"], reverse=newest_first)
        keep = [x for x in items if recent(x)][:10]
        for lg in LEAGUES:
            mine = [x for x in items if x[2] is lg]
            near = lambda x: abs((uk(x[0]["when"]) - now).days) <= 30   # only a matchday within a month
            if mine and near(mine[0]) and not any(x[2] is lg for x in keep):
                day = uk(mine[0][0]["when"]).date()
                keep += [x for x in mine if uk(x[0]["when"]).date() == day]
        return sorted(keep, key=lambda x: x[0]["when"], reverse=newest_first)
    allres = every_league(allres, lambda x: (x[0].get("when") or "") >= week, True)
    allfix = every_league(allfix, lambda x: True, False)
    lab = lambda x: f'{x[2]["name"]}{"" if len(x[2]["comps"]) == 1 else ", " + x[1].lower()}'
    def block(items):
        out, last = [], None
        for m, tag, lg in items:
            day = uk(m["when"]).date()
            if day != last:
                out.append(("</ol>" if out else "") + f'<h3 class="cl-day">{day:%A} {day.day} {day:%B}</h3><ol class="cl-list">')
                last = day
            out.append(match_row(m, None, lab((m, tag, lg))).replace('<li class="cl-m', f'<li style="--tier:{lg["colour"]}" class="cl-m', 1))
        return "".join(out) + ("</ol>" if out else "")
    return block(allres), block(allfix)


def hub(stories, now):
    cards = []
    for lg in LEAGUES:
        comps = [(tag, title, load(cid)) for cid, tag, title in lg["comps"]]
        mini = []
        for tag, title, d in comps:
            g = [g for g in ((d or {}).get("table") or {}).get("groups") or [] if g.get("rows")]
            rows = g[0]["rows"][:3] if g else []
            def val(r):
                if r.get("pts") is not None:
                    return f'<b>{r["pts"]}</b>'
                if r.get("w") is not None and r.get("l") is not None:
                    return f'<b>{r["w"]}-{r["l"]}</b>'
                return ""
            lis = "".join(f'<li><span>{r["pos"]}</span><em>{e(r["team"])}</em>{val(r)}</li>' for r in rows)
            mini.append(f'<div><h4>{e(tag)}</h4><ol>{lis}</ol></div>' if lis else f'<div><h4>{e(tag)}</h4><p class="cl-none">{e((d or {}).get("status") or "")}</p></div>')
        cards.append(f'''<li class="cl-card" style="--tier:{lg["colour"]}"><a href="/clubs/{lg["slug"]}.html">
<span class="ev-group"><span class="fi fi-{lg["flag"]}" aria-hidden="true"></span> {e(lg["country"])}</span><h3>{e(lg["name"])}</h3>
<p class="cl-status">{e(status_of(lg))}</p><div class="cl-mini{" one" if len(comps) == 1 else ""}">{"".join(mini)}</div><span class="cl-more">Tables, results and fixtures</span></a></li>''')
    res_html, fix_html = latest(now)
    clubs_news = [s for s in stories if s.get("category") == "Clubs"]
    chips = "".join(f'<a href="/clubs/{lg["slug"]}.html"><span class="fi fi-{lg["flag"]}" aria-hidden="true"></span>{e(lg["name"])}</a>' for lg in LEAGUES)
    return f'''<main class="wrap cl-page">
<section class="sched-head"><div><h1>Club game</h1><p class="lede">Tables, results, fixtures and news from the leagues where the world's best play: Germany, China, Japan, France, Britain, Europe, the United States and India.</p></div></section>
<nav class="cl-chips" aria-label="Leagues">{chips}</nav>
{explainers.combined(explainers.pick(["clubs"]), explainers.analysis(words=explainers.HUB_WORDS["clubs"], keys=["page:clubs"], n=2), "top")}
<div class="cl-hub-top">
<section class="hub-sec" id="results"><h2 class="section-title">Latest results</h2>{res_html or '<p class="cl-none">No club results in the last 10 days.</p>'}</section>
<section class="hub-sec" id="fixtures"><h2 class="section-title">Coming up</h2>{fix_html or '<p class="cl-none">No club fixtures published at the moment.</p>'}
<p class="small"><span data-tz-note>Times are UK time.</span></p></section></div>
<section class="hub-sec" id="leagues"><h2 class="section-title">Leagues</h2><ul class="cl-cards">{"".join(cards)}</ul></section>
{f'<section class="hub-sec" id="news"><h2 class="section-title">Club news</h2>{news_list(clubs_news, 12)}</section>' if clubs_news else ""}
</main>'''


def strip_data(now):
    """data/club-strip.json: the club results of the last few days and the fixtures of the next few, for the scores strip
    at the top of every page. The browser picks what is current (widgets.js), so the file only needs a margin either side."""
    out = []
    for lg in LEAGUES:
        for cid, tag, title in lg["comps"]:
            try:
                d = json.load(open(os.path.join(ROOT, "data", "clubs", f"{cid}.json"), encoding="utf-8"))
            except Exception:
                continue
            for m in d.get("matches") or []:
                if not (m.get("when") and m.get("home") and m.get("away")):
                    continue
                t = dt.datetime.fromisoformat(m["when"].replace("Z", "+00:00"))
                if not (now - dt.timedelta(days=4) <= t <= now + dt.timedelta(days=4)):
                    continue
                if m.get("status") == "finished" and not m.get("score"):
                    continue
                out.append({"lg": lg["slug"], "league": lg["name"], "comp": tag, "title": title, "home": m["home"], "away": m["away"],
                            "score": m.get("score") if m.get("status") == "finished" else None, "when": m["when"], "day": bool(m.get("date_only")),
                            "round": m.get("round") or ""})
    out.sort(key=lambda x: x["when"])
    json.dump(out, open(os.path.join(ROOT, "data", "club-strip.json"), "w", encoding="utf-8"), ensure_ascii=False)


def home_row(now):
    """data/club-row.json: the homepage's "Club competitions" row, beside Major events. For each league Eleven covers,
    its next round (with the pick of the fixtures: the one between the best-placed teams) and its last finished
    round (with the result between the best-placed teams), plus club events on the schedule the league data does not
    hold (Europe Cup, cup Final4s, finals weekends)."""
    def words(n):
        return {w for w in re.findall(r"[a-zà-ÿ]{4,}", (n or "").lower())} - {"borussia", "club", "team"}

    up, past = [], []
    for lg in LEAGUES:
        for cid, comp, title in lg["comps"]:
            d = load(cid)
            if not d:
                continue
            pos = {}
            for g in ((d.get("table") or {}).get("groups") or []):
                for r in g.get("rows") or []:
                    pos[r["team"]] = r.get("pos") or 99

            def rank(team):
                w = words(team)
                return min((p for t, p in pos.items() if w & words(t)), default=99)

            ms = [m for m in d.get("matches") or [] if m.get("when") and m.get("home")]
            groups = {}
            for m in ms:
                groups.setdefault(m.get("round") or m["when"][:10], []).append(m)
            name = lg["name"] + ("" if comp == "Mixed" else f" {comp.lower()}")
            base = {"lg": lg["slug"], "league": name, "colour": lg["colour"], "flag": lg["flag"], "url": f"/clubs/{lg['slug']}.html"}
            nxt = [(min(x["when"] for x in g), rd, g) for rd, g in groups.items()
                   if all(x.get("status") != "finished" for x in g) and max(x["when"] for x in g) >= (now - dt.timedelta(hours=12)).isoformat()]
            if nxt:
                start, rd, g = min(nxt, key=lambda t: t[0])
                g = [x for x in g if x.get("away")]
                lab = next((x.get("label") for x in groups[rd] if x.get("label")), "")
                top = min(g, key=lambda x: rank(x["home"]) + rank(x["away"])) if g else None
                up.append({**base, "round": lab or ("" if re.match(r"\d{4}-", rd) else rd), "start": start[:10], "end": max(x["when"] for x in groups[rd])[:10],
                           "pick": f'{top["home"]} v {top["away"]}' if top else "", "n": len(g)})
            done = [(max(x["when"] for x in g), rd, g) for rd, g in groups.items() if g and all(x.get("status") == "finished" for x in g)
                    and max(x["when"] for x in g) <= now.isoformat()]
            if done:
                end, rd, g = max(done, key=lambda t: t[0])
                g = [x for x in g if x.get("score") and x.get("away")]
                top = min(g, key=lambda x: rank(x["home"]) + rank(x["away"])) if g else None
                if end >= (now - dt.timedelta(days=21)).isoformat():
                    past.append({**base, "round": "" if re.match(r"\d{4}-", rd) else rd, "start": min(x["when"] for x in groups[rd])[:10], "end": end[:10],
                                 "pick": f'{top["home"]} {top["score"][0]}-{top["score"][1]} {top["away"]}' if top else ""})
    # Club events on the schedule that no league file holds (Europe Cup, cup Final4s)
    try:
        sched = json.load(open(os.path.join(ROOT, "data", "schedule.json"), encoding="utf-8"))["events"]
    except Exception:
        sched = []
    today = now.date().isoformat()
    for ev in sched:
        if ev.get("series") != "Clubs" or ev["end"] < today:
            continue
        lg = next((l for l in LEAGUES if re.search(l["match"], ev["name"])), None)
        if lg and lg["slug"] != "champions-league" and any(u["lg"] == lg["slug"] and u["start"] <= ev["end"] and u["end"] >= ev["start"] for u in up):
            continue
        if lg and lg["slug"] == "champions-league" and "Europe Cup" not in ev["name"] and any(
                u["lg"] == "champions-league" and u["start"] <= ev["end"] and u["end"] >= ev["start"] for u in up):
            continue
        head, _, rest = ev["name"].partition(", ")
        up.append({"lg": lg["slug"] if lg else "", "league": head.replace("ETTU ", ""), "colour": lg["colour"] if lg else "#17202b",
                   "flag": lg["flag"] if lg else "eu", "url": f"/clubs/{lg['slug']}.html" if lg else "/schedule.html",
                   "round": rest or ev.get("type", ""), "start": ev["start"], "end": ev["end"], "pick": "" if ev.get("city") in (None, "Europe", "Japan") else ev["city"], "n": 0})
    up.sort(key=lambda u: (u["start"], u["league"]))
    past.sort(key=lambda u: u["end"], reverse=True)
    json.dump({"up": up[:8], "past": past[:8]}, open(os.path.join(ROOT, "data", "club-row.json"), "w", encoding="utf-8"), ensure_ascii=False)


def build(page, site, stories):
    """Write /clubs/index.html and a page per league; return sitemap entries."""
    now = dt.datetime.now(dt.timezone.utc)
    os.makedirs(os.path.join(ROOT, "clubs"), exist_ok=True)
    strip_data(now)
    home_row(now)
    today = dt.date.today().isoformat()
    urls = [(f"{site}/clubs/", today)]
    open(os.path.join(ROOT, "clubs", "index.html"), "w", encoding="utf-8").write(page(
        "Club table tennis: tables, results and fixtures | Eleven",
        "Tables, results, fixtures and news from the TTBL and Bundesliga, China Super League, T.League, Pro A, Champions League, MLTT and UTT.",
        f"{site}/clubs/", hub(stories, now)))
    for lg in LEAGUES:
        body, season = league_page(lg, stories, now)
        what = "table, results and fixtures" if len(lg["comps"]) == 1 else "men's and women's tables, results and fixtures"
        open(os.path.join(ROOT, "clubs", f'{lg["slug"]}.html'), "w", encoding="utf-8").write(page(
            f'{lg["name"]} {season}: tables, results and fixtures | Eleven',
            f'{lg["name"]} {season} ({lg["country"]}): {what}, plus the latest news.',
            f'{site}/clubs/{lg["slug"]}.html', body))
        urls.append((f'{site}/clubs/{lg["slug"]}.html', today))
    return urls
