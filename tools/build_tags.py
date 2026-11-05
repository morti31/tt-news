"""Tag pages (/tag/<slug>) and the tag chips used on cards and articles.

Called from build_site.py after the stories are loaded. See tags.py for how a story gets its tags.
"""
import html, json, os, datetime as dt
import components
from tags import TYPES, MAX_TAGS

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PLURAL = {"tournament": "Tournaments", "player": "Players", "country": "Countries", "club": "Clubs and leagues"}


def url(tg, slug):
    return f"/tag/{slug}.html"


def chips(tg, slugs, n=MAX_TAGS, skip=None):
    """The small row of tag links under a story. n is 2 or 3."""
    out = [s for s in slugs if s != skip][:n]
    if not out:
        return ""
    lis = "".join(f'<li><a class="tg tg-{tg.tags[s]["type"]}" href="{url(tg, s)}">{e(tg.tags[s]["name"])}</a></li>' for s in out)
    return f'<ul class="tags" aria-label="Tags">{lis}</ul>'


def topics(tg, slugs):
    """All of a story's tags, at the foot of the article."""
    row = chips(tg, slugs, 8)
    return f'<section class="article-topics"><h2>Topics</h2>{row}</section>' if row else ""


def _date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d:%B}"


def _span(h):
    if not h.get("start"):
        return ""
    s, en = h["start"], h.get("end") or h["start"]
    a, b = dt.date.fromisoformat(s), dt.date.fromisoformat(en)
    if a == b:
        return f"{a.day} {a:%B %Y}"
    if a.month == b.month:
        return f"{a.day} to {b.day} {b:%B %Y}"
    return f"{a.day} {a:%B} to {b.day} {b:%B %Y}"


def header(tg, t, R, hubs, entries, taglinks):
    """The short block above the stories: who or what this tag is, with links onward."""
    kind = TYPES[t["type"]]
    meta, links = [], []
    if t["type"] == "tournament":
        if t.get("hub"):
            where = ", ".join(x for x in (t.get("city"), t.get("country")) if x)
            meta = [x for x in (where, _span(t), t.get("venue")) if x]
            links.append((f'/events/{t["hub"]}.html', "Results, draw and schedule"))
    elif t["type"] == "player":
        bits = []
        for g, label in (("men", "men's"), ("women", "women's")):
            p = (t.get("rank") or {}).get(g)
            if p:
                bits.append(f"World No. {p['rank']} in the {label} singles rankings, {p['points']:,} points")
        meta = bits or ["Outside the world top 100"]
        links.append(("/rankings.html", "World rankings"))
    elif t["type"] == "country":
        code = t.get("code")
        if R:
            for g, label in (("men", "men"), ("women", "women")):
                ps = [p for p in R.get(g, []) if p["nat"] == code]
                if ps:
                    top = ps[0]
                    meta.append(f"{len(ps)} {label} in the top 100, led by {top['name']} at No. {top['rank']}")
        links.append(("/rankings.html", "World rankings"))
    else:
        if t.get("league"):
            links.append((f'/clubs/{t["league"]}.html', "Tables, fixtures and results"))
            meta = [t["country"]] if t.get("country") else []
    flag = components.flag(t.get("nat") or t.get("code") or "")
    meta_html = "".join(f"<li>{e(m)}</li>" for m in meta)
    link_html = "".join(f'<a class="tag-link" href="{u}">{e(x)} &rarr;</a>' for u, x in links)
    # Where this tag has been in the news: the events of its stories
    evs = []
    for it in entries:
        h = hubs.get(it.get("event") or "")
        if h and h["id"] != t.get("hub") and h not in evs:
            evs.append(h)
    ev_html = ""
    if evs and t["type"] in ("player", "country", "club"):
        ev_html = '<p class="tag-events">In the news at ' + ", ".join(
            f'<a href="/events/{h["id"]}.html">{e(h["name"])} {e(h["year"])}</a>' for h in evs[:4]) + "</p>"
    return f'''<header class="hub-head tag-head" style="--tier:#17202b"><div><span class="ev-group">{e(kind)}</span>
<h1>{flag} {e(t["name"])}</h1>{f'<ul class="tag-meta">{meta_html}</ul>' if meta_html else ""}{ev_html}</div>
<div class="tag-links">{link_html}</div></header>'''


def story_li(tg, it, skip):
    kind = it.get("kind") or it["category"]
    return (f'<li class="archive-item"><a href="{e(it["url"])}"><span class="tag" style="color:var(--{e(it["category"])}, var(--ink))">{e(kind)}</span>'
            f'<h2>{e(it["title"])}</h2><p>{e(it["summary"])}</p><time datetime="{e(it["published"])}">By Eleven Team, {e(it["when"])}</time></a>'
            f'{chips(tg, it["tags"], MAX_TAGS, skip)}</li>')


def build(page, site, tg, items, R, hubs):
    """items: dicts with id, url, title, summary, published, when, category, kind, event, tags (display slugs), all (every slug)."""
    os.makedirs(os.path.join(ROOT, "tag"), exist_ok=True)
    members = {}
    for it in items:
        for s in it["all"]:
            members.setdefault(s, []).append(it)
    urls, built = [], []
    today = dt.date.today().isoformat()
    for slug, entries in sorted(members.items()):
        t = tg.tags[slug]
        entries.sort(key=lambda x: x["published"], reverse=True)
        n = len(entries)
        lis = "".join(story_li(tg, it, slug) for it in entries)
        body = f'''<main class="wrap tag-page">
<p class="crumbs"><a href="/">Home</a> / <a href="/tag/">Topics</a> / {e(t["name"])}</p>
{header(tg, t, R, hubs, entries, None)}
<section class="hub-sec"><h2 class="section-title">{n} {"story" if n == 1 else "stories"}</h2><ul class="archive">{lis}</ul></section>
</main>'''
        title = f'{t["name"]}: table tennis news, results and reports | Eleven'
        desc = f'Every Eleven story on {t["name"]}: {n} {"report" if n == 1 else "reports"} and previews, newest first.'
        robots = None if n >= 2 else "noindex,follow"
        open(os.path.join(ROOT, "tag", slug + ".html"), "w", encoding="utf-8").write(page(title, desc, f"{site}/tag/{slug}.html", body, robots=robots))
        built.append((slug, n))
        if n >= 2:
            urls.append((f"{site}/tag/{slug}.html", today))
    # Topics index, grouped by kind
    groups = ""
    for typ in ("tournament", "player", "club", "country"):
        rows = sorted([(s, n) for s, n in built if tg.tags[s]["type"] == typ], key=lambda x: (-x[1], tg.tags[x[0]]["name"]))
        if rows:
            lis = "".join(f'<li><a href="{url(tg, s)}">{e(tg.tags[s]["name"])}</a><span class="meta">{n}</span></li>' for s, n in rows)
            groups += f'<section class="hub-sec"><h2 class="section-title">{PLURAL[typ]}</h2><ul class="tag-index">{lis}</ul></section>'
    idx = f'''<main class="wrap tag-page"><section class="sched-head"><div><h1>Topics</h1>
<p class="lede">Tournaments, players, countries and clubs in the news on Eleven. Each page gathers every story on that topic.</p></div></section>{groups}</main>'''
    open(os.path.join(ROOT, "tag", "index.html"), "w", encoding="utf-8").write(
        page("Topics: tournaments, players, countries and clubs | Eleven", "Browse Eleven's table tennis news by tournament, player, country and club.", f"{site}/tag/", idx))
    urls.append((f"{site}/tag/", today))
    return urls
