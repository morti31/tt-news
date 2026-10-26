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
AUTHOR = NEWS.get("author", {"name": "Eleven"})
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


def long_date(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day} {d:%B %Y}"


def initials(name):
    return "".join(w[0] for w in name.split())[:2]


def avatar(size):
    if AUTHOR.get("photo"):
        return f'<img class="avatar" src="{e(AUTHOR["photo"])}" alt="" width="{size}" height="{size}">'
    return f'<span class="avatar" style="width:{size}px;height:{size}px;font-size:{size*0.4:.0f}px" aria-hidden="true">{e(initials(AUTHOR["name"]))}</span>'


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


def page(title, desc, canonical, body, extra_head="", news_cur=False, og_image=None, og_type="website"):
    og_img = f'<meta property="og:image" content="{e(og_image)}">' if og_image else ""
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
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
{body}
{FOOT}
</body>
</html>
"""


def load_articles():
    arts = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "articles", "*.json"))):
        a = json.load(open(f, encoding="utf-8"))
        a.setdefault("slug", os.path.splitext(os.path.basename(f))[0])
        arts.append(a)
    arts.sort(key=lambda a: (a["date"], a.get("time", "")), reverse=True)
    return arts


def article_page(a, others):
    url = f"{SITE}/news/{a['slug']}.html"
    words = sum(len(p.split()) for p in a["body"])
    tag = f'<span class="tag" style="color:var(--{e(a["category"])}, var(--ink))">{e(a["category"])}'
    if a.get("lang"):
        tag += f'<span class="translated">, translated from {e(a["lang"])}</span>'
    tag += "</span>"
    paras = "\n".join(f"<p>{e(p)}</p>" for p in a["body"])
    sources = "".join(f'<li><a href="{e(s["url"])}" rel="noopener">{e(s["name"])}</a></li>' for s in a["sources"])
    more = "".join(f'<li><a href="/news/{e(o["slug"])}.html">{e(o["title"])}</a><span>{long_date(o["date"])}</span></li>' for o in others[:5])
    img = a.get("image") or {}
    ld = {
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": a["title"][:110], "description": a["standfirst"],
        "datePublished": a.get("published", a["date"] + "T09:00:00Z"), "dateModified": a.get("modified", a.get("published", a["date"] + "T09:00:00Z")),
        "author": [{"@type": "Person", "name": AUTHOR["name"], "url": f"{SITE}/#about"}],
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
  <p class="standfirst">{e(a['standfirst'])}</p>
  <div class="article-byline"><a class="byline" href="/#about">{avatar(36)}<span>By {e(AUTHOR['name'])}</span></a><time datetime="{e(a['date'])}">{long_date(a['date'])}</time></div>
  {hero(a)}
  <div class="article-body">
{paras}
  </div>
  <section class="article-sources"><h2>Sources</h2><ul>{sources}</ul></section>
</article>
<aside class="article-side">
  <section class="panel author"><div class="author-head">{avatar(56)}<div><p class="small-label">Editor</p><h2 class="panel-title">{e(AUTHOR['name'])}</h2></div></div><p class="author-bio">{e(AUTHOR.get('bio', ''))}</p></section>
  {f'<section class="panel"><h2 class="panel-title">More news</h2><ul class="more-list">{more}</ul></section>' if more else ''}
</aside>
</main>"""
    og = img.get("url") if img.get("type") == "photo" else None
    return page(f"{a['title']} | Eleven", a["standfirst"], url, body, head, og_image=og, og_type="article")


def main():
    arts = load_articles()
    os.makedirs(os.path.join(ROOT, "news"), exist_ok=True)
    for a in arts:
        others = [o for o in arts if o["slug"] != a["slug"]]
        open(os.path.join(ROOT, "news", a["slug"] + ".html"), "w", encoding="utf-8").write(article_page(a, others))

    items = "".join(f"""<li class="archive-item"><a href="/news/{e(a['slug'])}.html"><span class="tag" style="color:var(--{e(a['category'])}, var(--ink))">{e(a['category'])}</span>
<h2>{e(a['title'])}</h2><p>{e(a['standfirst'])}</p><time datetime="{e(a['date'])}">{long_date(a['date'])}</time></a></li>""" for a in arts)
    archive = f"""<main class="wrap"><section class="sched-head"><div><h1>Archive</h1><p class="lede">Every full article published on Eleven, newest first.</p></div></section>
<ul class="archive">{items or '<li class="empty">No full articles yet.</li>'}</ul></main>"""
    open(os.path.join(ROOT, "news", "index.html"), "w", encoding="utf-8").write(
        page("Archive | Eleven", "Every full table tennis article published on Eleven.", f"{SITE}/news/", archive, news_cur=True))

    index = {a.get("story_id", a["slug"]): {"slug": a["slug"], "url": f"/news/{a['slug']}.html"} for a in arts}
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
    print(f"built {len(arts)} articles, archive, sitemap ({len(urls)} URLs), robots.txt, feed.xml")


if __name__ == "__main__":
    main()
