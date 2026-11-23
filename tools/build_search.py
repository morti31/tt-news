"""Site search for Eleven and The Chop.

Two parts, both static (no server, no cookies, no tracking):
  - search-index.json: a small list of players, tournaments, leagues, guides, defenders and recent stories,
    used by search.js for the instant suggestions under the header search box.
  - Pagefind (https://pagefind.app): a full-text index of every story, guide, player, event, league and Chop page,
    built after the site by `npx pagefind` in the deploy workflow (config in pagefind.yml), served from /pagefind/.
    search.html (Eleven) and defensive/search.html (The Chop) show its results.

Pages opt in to the full-text index through build_site.page(): it marks the main content with data-pagefind-body
and adds a "section" filter (News, Analysis, Players, Tournaments, Club game, Guide, The Chop).
"""
import json, os, re, glob, datetime as dt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHOP = "https://defensive.eleventabletennis.com"


def _load(rel, default):
    try:
        return json.load(open(os.path.join(ROOT, rel), encoding="utf-8"))
    except Exception:
        return default


def _short(d):
    try:
        x = dt.date.fromisoformat(d[:10])
        return f"{x.day} {x:%b %Y}"
    except Exception:
        return ""


def index(arts, events, leagues):
    """Entries are [title, url, kind, detail, rank]: kind p player, e event, l league, g guide, c Chop, s story.
    rank orders suggestions within a kind (higher first)."""
    out = []
    R = _load("data/rankings.json", {})
    ranked = {}
    for g in ("men", "women"):
        for r in R.get(g, []):
            ranked[r["name"]] = (r["rank"], r.get("nat", ""))
    for name, url in sorted(_load("data/profiles.json", {}).items()):
        rk, nat = ranked.get(name, (None, ""))
        out.append([name, url, "p", (f"World No {rk}" if rk else "Player"), (1000 - rk if rk else 0), nat])
    day0 = dt.date.today()
    today = day0.isoformat()
    for ev in events:
        if not ev.get("start"):
            continue
        end = ev.get("end") or ev["start"]
        live = ev["start"] <= today <= end
        place = ev.get("city") or ""
        # on now first, then the next ones (soonest first), then past ones (most recent first)
        if live:
            rank = 300000
        elif ev["start"] > today:
            rank = 200000 - (dt.date.fromisoformat(ev["start"]) - day0).days
        else:
            rank = 100000 - (day0 - dt.date.fromisoformat(end)).days
        out.append([f'{ev["name"]} {ev.get("year", "")}'.strip(), f'/events/{ev["id"]}.html', "e",
                    ("On now" if live else _short(ev["start"])) + (f", {place}" if place else ""), rank, ""])
    for lg in leagues:
        out.append([lg["name"], f'/clubs/{lg["slug"]}.html', "l", f'Club game, {lg.get("country", "")}'.rstrip(", "), 0, ""])
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "guides", "*.json"))):
        g = _load(os.path.relpath(f, ROOT), {})
        if g.get("title") and g.get("slug"):
            out.append([g["title"], f'/guide/{g["slug"]}.html', "g", "Guide", 0, ""])
    try:
        import build_chop
        for p in _load("data/chop/players.json", []):
            if p.get("status") == "approved":
                out.append([p["name"], f'{CHOP}/defender/{build_chop.slug(p["name"])}.html', "c", "The Chop: defender profile", 0, ""])
    except Exception:
        pass
    for a in arts[:250]:   # the newest stories; older ones are in the full-text search
        d = a.get("published", a.get("date", ""))
        out.append([a["title"], f'/news/{a["slug"]}.html', "s", _short(d), int(re.sub(r"\D", "", d[:10]) or 0), ""])
    return out


def search_page(site):
    """The full-text results page body (filled in by search.js)."""
    return """<main class="wrap sx-page" id="search-page">
<section class="sched-head"><div><h1>Search</h1><p class="lede">Stories, players, tournaments, leagues and guides on Eleven and The Chop.</p></div></section>
<form class="sx-form" action="/search.html" method="get" role="search">
<label class="sx-visually-hidden" for="sx-q">Search Eleven</label>
<input id="sx-q" name="q" type="search" placeholder="Search players, events, stories..." autocomplete="off" enterkeyhint="search">
<button type="submit">Search</button></form>
<div id="sx-quick"></div>
<div class="sx-filters" id="sx-filters" role="group" aria-label="Filter results"></div>
<p class="sx-count" id="sx-count" aria-live="polite"></p>
<ol class="sx-results" id="sx-results"></ol>
<button class="sx-more" id="sx-more" type="button" hidden>Show more results</button>
<noscript><p>Search needs JavaScript. You can browse <a href="/news/">all news</a>, <a href="/players/">players</a> and <a href="/events/">tournaments</a>.</p></noscript>
</main>"""


def build(page, site, arts, events, leagues):
    json.dump(index(arts, events, leagues), open(os.path.join(ROOT, "search-index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    open(os.path.join(ROOT, "search.html"), "w", encoding="utf-8").write(
        page("Search | Eleven", "Search Eleven's table tennis news, players, tournaments and guides.", f"{site}/search.html",
             search_page(site), robots="noindex,follow", search=False))
