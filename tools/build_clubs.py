"""Club table tennis: a hub at /clubs/ and one page per league, built from data/clubs/<competition>.json.

Each league page pairs the men's and women's competitions at equal size (tables side by side, results and
fixtures merged and labelled), then the league's news. Leagues with a single mixed competition (MLTT, UTT)
have one table. Files with "auto": true are refreshed every hour by tools/club_sync.py; the others are kept
current by the scheduled update runs (UPDATE.md, "Club leagues").

News: a story belongs to a league if it has "league": "<slug>" in data/news.json, or if it is in the Clubs
category and its headline or summary names the league (see LEAGUES[...]["match"]).
"""
import json, os, re, html, datetime as dt
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
    return (f'<li class="cl-m{" done" if played else ""}{" is-live" if live else ""}">{when_html(m, with_day)}'
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
    jump = "".join(f'<a href="#{k}">{v}</a>' for k, v in (("results", "Results"), ("fixtures", "Fixtures"), ("tables", "Tables"), ("news", "News"), ("about", "About")) if k != "news" or mine)
    body = f'''<main class="wrap cl-page" style="--tier:{lg["colour"]}">
<p class="crumbs"><a href="/">Home</a> / <a href="/clubs/">Clubs</a> / {e(lg["name"])}</p>
<header class="hub-head cl-head"><div><span class="ev-group"><span class="fi fi-{lg["flag"]}" aria-hidden="true"></span> {e(lg["country"])}</span>
<h1>{e(lg["name"])} {e(season)}</h1><p class="cl-status">{e(status_of(lg))}</p></div></header>
<nav class="hub-jump" aria-label="On this page">{jump}</nav>
<div class="cl-hub-top"><section class="hub-sec" id="results"><h2 class="section-title">Results</h2>{grouped(res, mixed) or '<p class="cl-none">No results yet this season.</p>'}{more}</section>
<section class="hub-sec" id="fixtures"><h2 class="section-title">Fixtures</h2>{grouped(fix, mixed) or '<p class="cl-none">No fixtures published at the moment.</p>'}
<p class="small"><span data-tz-note>Times are UK time.</span> Times can change, so check with the clubs before travelling.</p></section></div>
<section class="hub-sec" id="tables"><h2 class="section-title">{"Table" if mixed else "Tables"}</h2><div class="cl-tables{" one" if mixed else ""}">{tables}</div></section>
{f'<section class="hub-sec" id="news"><h2 class="section-title">News</h2>{news_list(mine, 12)}</section>' if mine else ""}
<section class="hub-sec" id="about"><h2 class="section-title">About the league</h2><p class="cl-about">{e(lg["about"])}</p>
<p class="small">Tables, fixtures and results from {srcs}{f', updated {uk(upd).day} {uk(upd):%B} at {uk(upd):%H:%M} UK time' if upd else ""}.</p></section>
</main>'''
    return body, season


def hub(stories, now):
    cards, allres, allfix = [], [], []
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
        for m, tag in merged(lg, "results", 8, now):
            allres.append((m, tag, lg))
        for m, tag in merged(lg, "fixtures", 8, now):
            if m.get("when"):
                allfix.append((m, tag, lg))
    week = (now - dt.timedelta(days=10)).strftime("%Y-%m-%d")
    allres = sorted((x for x in allres if (x[0].get("when") or "") >= week), key=lambda x: x[0]["when"], reverse=True)[:10]
    allfix = sorted(allfix, key=lambda x: x[0]["when"])[:10]
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
    clubs_news = [s for s in stories if s.get("category") == "Clubs"]
    chips = "".join(f'<a href="/clubs/{lg["slug"]}.html"><span class="fi fi-{lg["flag"]}" aria-hidden="true"></span>{e(lg["name"])}</a>' for lg in LEAGUES)
    return f'''<main class="wrap cl-page">
<section class="sched-head"><div><h1>Clubs</h1><p class="lede">Tables, results, fixtures and news from the leagues where the world's best play: Germany, China, Japan, France, Europe, the United States and India.</p></div></section>
<nav class="cl-chips" aria-label="Leagues">{chips}</nav>
<div class="cl-hub-top">
<section class="hub-sec" id="results"><h2 class="section-title">Latest results</h2>{block(allres) or '<p class="cl-none">No club results in the last 10 days.</p>'}</section>
<section class="hub-sec" id="fixtures"><h2 class="section-title">Coming up</h2>{block(allfix) or '<p class="cl-none">No club fixtures published at the moment.</p>'}
<p class="small"><span data-tz-note>Times are UK time.</span></p></section></div>
<section class="hub-sec" id="leagues"><h2 class="section-title">Leagues</h2><ul class="cl-cards">{"".join(cards)}</ul></section>
{f'<section class="hub-sec" id="news"><h2 class="section-title">Club news</h2>{news_list(clubs_news, 12)}</section>' if clubs_news else ""}
</main>'''


def build(page, site, stories):
    """Write /clubs/index.html and a page per league; return sitemap entries."""
    now = dt.datetime.now(dt.timezone.utc)
    os.makedirs(os.path.join(ROOT, "clubs"), exist_ok=True)
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
