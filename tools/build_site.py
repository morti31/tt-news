"""Builds the article pages, news archive, sitemap and robots.txt.

Cloudflare runs this as the build command on every deploy:  python3 tools/build_site.py
It uses only the Python standard library.

Input:  data/articles/*.json  (one file per full article; merged into main once approved)
Output: news/<slug>.html, news/index.html, data/article-index.json, sitemap.xml, robots.txt, feed.xml
"""
import json, os, glob, html, datetime as dt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = os.environ.get("SITE_URL", "https://tt-news.tommorti.workers.dev")
NEWS = json.load(open(os.path.join(ROOT, "data", "news.json"), encoding="utf-8"))
AUTHORS = NEWS.get("authors", {"tom": {"name": "Eleven"}})


def author_of(a):
    return AUTHORS.get(a.get("author", "tom"), AUTHORS.get("tom", {"name": "Eleven"}))
e = html.escape

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Figtree:wght@400;500;600&display=swap" rel="stylesheet">')

NAV = """<header class="masthead"><div class="wrap masthead-inner">
<a class="wordmark" href="/" aria-label="Eleven home">Eleven<span class="ball" aria-hidden="true"></span></a>
<nav aria-label="Sections"><ul class="sections">
<li><a href="/">Home</a></li><li><a href="/#International">International</a></li><li><a href="/#England">England</a></li>
<li><a href="/#Clubs">Clubs</a></li><li><a href="/#Equipment">Equipment</a></li><li><a href="/news/"{news_cur}>Archive</a></li><li><a href="/schedule.html">Schedule</a></li>
</ul></nav></div></header>"""

FOOT = """<footer class="footer"><div class="wrap"><p class="foot-mark">Eleven<span class="ball" aria-hidden="true"></span></p>
<p>Table tennis news, results and fixtures from around the world. Stories marked as translated draw on non-English sources.</p></div></footer>"""


try:
    from zoneinfo import ZoneInfo
    UK = ZoneInfo("Europe/London")
except Exception:  # no tz database: fall back to UTC
    UK = dt.timezone.utc


def long_date(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day} {d:%B %Y}"


def pub_time(a):
    """Publication time in UK time, e.g. '26 October 2026, 16:46'."""
    raw = a.get("published")
    if not raw:
        return long_date(a["date"])
    t = dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(UK)
    return f"{t.day} {t:%B %Y}, {t:%H:%M}"


def initials(name):
    return "".join(w[0] for w in name.split())[:2]


def avatar(au, size):
    if au.get("photo"):
        return f'<img class="avatar" src="{e(au["photo"])}" alt="" width="{size}" height="{size}">'
    return (f'<span class="avatar" style="width:{size}px;height:{size}px;font-size:{size*0.4:.0f}px;background:{e(au.get("colour", "var(--ink)"))};color:#fff" '
            f'aria-hidden="true">{e(au.get("initials") or initials(au["name"]))}</span>')


def hero(a):
    im = a.get("image")
    if not im:
        return ""
    if im["type"] == "photo":
        cap = (e(im["caption"]) + ". " if im.get("caption") else "")
        return (f'<figure class="article-hero photo"><img src="{e(im["url"])}" alt="{e(im.get("alt", ""))}">'
                f'<figcaption>{cap}Photo: <a href="{e(im["page"])}" rel="noopener">{e(im["credit"])}</a>, '
                f'<a href="{e(im["licence_url"])}" rel="noopener">{e(im["licence"])}</a></figcaption></figure>')
    if im["type"] == "cartoon":
        path = os.path.join(ROOT, im["src"])
        svg = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        return f'<figure class="article-hero art cartoon">{svg}</figure>'
    return ""


def page(title, desc, canonical, body, extra_head="", news_cur=False, og_image=None, og_type="website", robots=None):
    og_img = f'<meta property="og:image" content="{e(og_image)}">' if og_image else ""
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">{f'<meta name="robots" content="{robots}">' if robots else ""}
<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="{og_type}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canonical)}"><meta property="og:site_name" content="Eleven">{og_img}
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="Eleven" href="/feed.xml">
<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" href="/img/icons/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/img/icons/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest"><meta name="theme-color" content="#17202b">
{FONTS}
<link rel="stylesheet" href="/styles.css">
{extra_head}
</head>
<body>
{NAV.format(news_cur=' aria-current="page"' if news_cur else "")}
<section class="ticker" aria-label="Latest scores"><div class="wrap ticker-inner" id="ticker"></div></section>
{body}
{FOOT}
<script src="/widgets.js"></script>
</body>
</html>
"""


def load_articles():
    arts = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "articles", "*.json"))):
        a = json.load(open(f, encoding="utf-8"))
        a.setdefault("slug", os.path.splitext(os.path.basename(f))[0])
        arts.append(a)
    arts.sort(key=lambda a: a.get("published", a["date"]), reverse=True)
    return arts


def article_page(a, others, brief=False):
    AUTHOR = author_of(a)
    url = f"{SITE}/news/{a['slug']}.html"
    words = sum(len(p.split()) for p in a["body"])
    tag = f'<span class="tag" style="color:var(--{e(a["category"])}, var(--ink))">{e(a["category"])}'
    if a.get("lang"):
        tag += f'<span class="translated">, translated from {e(a["lang"])}</span>'
    tag += "</span>"
    paras = "\n".join(f"<p>{e(p)}</p>" for p in a["body"])
    sources = "".join(f'<li><a href="{e(s["url"])}" rel="noopener">{e(s["name"])}</a></li>' for s in a["sources"])
    more = "".join(f'<li><a href="/news/{e(o["slug"])}.html">{e(o["title"])}</a><span>{pub_time(o)}</span></li>' for o in others[:5])
    img = a.get("image") or {}
    ld = {
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": a["title"][:110], "description": a["standfirst"],
        "datePublished": a.get("published", a["date"] + "T09:00:00Z"), "dateModified": a.get("modified", a.get("published", a["date"] + "T09:00:00Z")),
        "author": [{"@type": "Person", "name": AUTHOR["name"], "url": f"{SITE}/news/"}],
        "publisher": {"@type": "Organization", "name": "Eleven", "url": SITE},
        "mainEntityOfPage": url, "articleSection": a["category"], "wordCount": words, "inLanguage": "en-GB",
    }
    if img.get("type") == "photo":
        ld["image"] = [img["url"]]
    head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    body = f"""<main class="wrap article-wrap">
<article class="article">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/#{e(a['category'])}">{e(a['category'])}</a></nav>
  {tag}
  <h1>{e(a['title'])}</h1>
  {f'<p class="standfirst">{e(a["standfirst"])}</p>' if a.get("standfirst") else ""}
  <div class="article-byline"><span class="byline">{avatar(AUTHOR, 36)}<span>By {e(AUTHOR['name'])}</span></span><time datetime="{e(a.get('published', a['date']))}">{pub_time(a)}</time></div>
  {hero(a)}
  <div class="article-body">
{paras}
  </div>
  <section class="article-sources"><h2>Sources</h2><ul>{sources}</ul></section>
</article>
<aside class="article-side">
  {f'<section class="panel author"><div class="author-head">{avatar(AUTHOR, 56)}<div><p class="small-label">Writer</p><h2 class="panel-title">{e(AUTHOR["name"])}</h2></div></div><p class="author-bio">{e(AUTHOR["bio"])}</p></section>' if AUTHOR.get("bio") else ""}
  {f'<section class="panel"><h2 class="panel-title">More news</h2><ul class="more-list">{more}</ul></section>' if more else ''}
  <section class="panel"><h2 class="panel-title">World rankings</h2>
    <div class="toggle" id="rank-toggle" role="group" aria-label="Rankings"><button data-g="men" aria-pressed="true">Men</button><button data-g="women" aria-pressed="false">Women</button></div>
    <ol id="rankings" class="rankings"></ol><p class="small" id="rank-week"></p></section>
  <section class="panel"><h2 class="panel-title">Coming up</h2><ul id="events" class="events" data-count="5"></ul>
    <a class="panel-link" href="/schedule.html">Full schedule and calendar</a></section>
</aside>
</main>"""
    og = img.get("url") if img.get("type") == "photo" else None
    desc = a.get("standfirst") or (a["body"][0] if a["body"] else a["title"])
    # Short stories stay readable and shareable but are kept out of Google's index as thin pages
    return page(f"{a['title']} | Eleven", desc[:300], url, body, head, og_image=og, og_type="article",
                robots="noindex, follow" if brief else None)


def main():
    arts = load_articles()
    os.makedirs(os.path.join(ROOT, "news"), exist_ok=True)
    for a in arts:
        others = [o for o in arts if o["slug"] != a["slug"]]
        open(os.path.join(ROOT, "news", a["slug"] + ".html"), "w", encoding="utf-8").write(article_page(a, others))

    items = "".join(f"""<li class="archive-item"><a href="/news/{e(a['slug'])}.html"><span class="tag" style="color:var(--{e(a['category'])}, var(--ink))">{e(a['category'])}</span>
<h2>{e(a['title'])}</h2><p>{e(a['standfirst'])}</p><time datetime="{e(a.get('published', a['date']))}">By {e(author_of(a)["name"])}, {pub_time(a)}</time></a></li>""" for a in arts)
    archive = f"""<main class="wrap"><section class="sched-head"><div><h1>Archive</h1><p class="lede">Every full article published on Eleven, newest first.</p></div></section>
<ul class="archive">{items or '<li class="empty">No full articles yet.</li>'}</ul></main>"""
    open(os.path.join(ROOT, "news", "index.html"), "w", encoding="utf-8").write(
        page("Archive | Eleven", "Every full table tennis article published on Eleven.", f"{SITE}/news/", archive, news_cur=True))

    index = {a.get("story_id", a["slug"]): {"slug": a["slug"], "url": f"/news/{a['slug']}.html", "published": a.get("published")} for a in arts}

    # Short stories without a full article get a short page of their own
    briefs = 0
    for s in NEWS.get("stories", []):
        if s["id"] in index:
            continue
        brief = {"slug": s["id"], "title": s["headline"], "standfirst": "", "category": s["category"], "date": s["date"],
                 "body": s.get("body") or [s["summary"]], "sources": s.get("sources", []), "author": s.get("author", "tom")}
        for k in ("lang", "image", "published"):
            if s.get(k):
                brief[k] = s[k]
        open(os.path.join(ROOT, "news", s["id"] + ".html"), "w", encoding="utf-8").write(article_page(brief, arts, brief=True))
        index[s["id"]] = {"slug": s["id"], "url": f"/news/{s['id']}.html", "brief": True}
        briefs += 1
    json.dump(index, open(os.path.join(ROOT, "data", "article-index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    today = dt.date.today().isoformat()
    urls = [(f"{SITE}/", today), (f"{SITE}/schedule.html", today), (f"{SITE}/news/", arts[0]["date"] if arts else today)]
    urls += [(f"{SITE}/news/{a['slug']}.html", a.get("modified", a["date"])[:10]) for a in arts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"  <url><loc>{e(u)}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n"
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(sm)
    open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

    def rfc822(a):
        d = dt.datetime.fromisoformat(a.get("published", a["date"] + "T09:00:00+00:00").replace("Z", "+00:00"))
        return d.strftime("%a, %d %b %Y %H:%M:%S +0000")
    rss = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0"><channel>', "<title>Eleven</title>", f"<link>{SITE}/</link>",
           "<description>Table tennis news from around the world</description>", "<language>en-gb</language>"]
    for a in arts[:30]:
        rss.append(f"<item><title>{e(a['title'])}</title><link>{SITE}/news/{e(a['slug'])}.html</link><guid>{SITE}/news/{e(a['slug'])}.html</guid>"
                   f"<pubDate>{rfc822(a)}</pubDate><description>{e(a['standfirst'])}</description></item>")
    rss.append("</channel></rss>")
    open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8").write("\n".join(rss) + "\n")
    print(f"built {len(arts)} articles, {briefs} short pages, archive, sitemap ({len(urls)} URLs), robots.txt, feed.xml")


def check_schedule():
    """Warn about schedule entries that would break the page or the calendar feed."""
    s = json.load(open(os.path.join(ROOT, "data", "schedule.json"), encoding="utf-8"))
    ids, problems = set(), []
    for ev in s.get("events", []):
        try:
            if dt.date.fromisoformat(ev["end"]) < dt.date.fromisoformat(ev["start"]):
                problems.append(f'{ev["id"]}: ends before it starts')
        except (KeyError, ValueError) as err:
            problems.append(f'{ev.get("id", "?")}: bad or missing date ({err})')
        if ev.get("id") in ids:
            problems.append(f'{ev["id"]}: duplicate id')
        ids.add(ev.get("id"))
    for fx in s.get("fixtures", []):
        if fx.get("event_id") not in ids:
            problems.append(f'fixture {fx.get("id")}: unknown event_id {fx.get("event_id")}')
        try:
            dt.datetime.fromisoformat(fx["start"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            problems.append(f'fixture {fx.get("id")}: bad start time')
    for p in problems:
        print("schedule warning:", p)
    return problems


if __name__ == "__main__":
    main()
    check_schedule()
    # Rebuild the subscribable calendar on every deploy so it always matches data/schedule.json
    import runpy
    runpy.run_path(os.path.join(ROOT, "tools", "build_calendar.py"), run_name="__main__")
