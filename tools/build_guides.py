"""The Guide: evergreen explainers for people getting into table tennis, in layers from first steps to the pro game.

Input:  data/guides/plan.json (the shelves and planned titles) and data/guides/<slug>.json (written guides)
Output: guide/index.html and guide/<slug>.html. Called from build_site.py.

A guide file:
{
  "slug": "how-world-rankings-work", "shelf": "pro", "order": 3, "level": "Beginner | Fan | Club player",
  "title": "...", "seo_title": "... (under 60 characters)", "description": "... (140 to 155 characters)",
  "summary": "one or two sentences shown on the shelf and under the headline",
  "key_points": ["three to five one-line takeaways"],
  "body": ["paragraph", "## A subheading", "paragraph with an [internal link](/rankings.html)"],
  "author": "tom", "published": "YYYY-MM-DDTHH:MM:00Z", "updated": "YYYY-MM-DD",
  "sources": [{"name": "...", "url": "https://..."}]
}
"""
import glob, html, json, os, re, datetime as dt

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load():
    plan_path = os.path.join(ROOT, "data", "guides", "plan.json")
    plan = json.load(open(plan_path, encoding="utf-8")) if os.path.exists(plan_path) else {"shelves": []}
    guides = {}
    for f in glob.glob(os.path.join(ROOT, "data", "guides", "*.json")):
        if f.endswith("plan.json"):
            continue
        g = json.load(open(f, encoding="utf-8"))
        guides[g["slug"]] = g
    return plan, guides


def minutes(g):
    return max(2, round(sum(len(p.split()) for p in g["body"]) / 220))


def body_html(g, linkify):
    out = []
    for p in g["body"]:
        if p.startswith("## "):
            out.append(f"<h2>{e(p[3:])}</h2>")
        else:
            out.append(f"<p>{linkify(p)}</p>")
    return "\n".join(out)


def build(page, site, authors, avatar, linkify):
    plan, guides = load()
    if not plan["shelves"]:
        return []
    raw_linkify = linkify

    def linkify(text):   # links to guides that aren't written yet stay as plain words
        text = re.sub(r"\[([^\]]+)\]\(/guide/([a-z0-9-]+)\.html\)", lambda m: m.group(0) if m.group(2) in guides else m.group(1), text)
        return raw_linkify(text)
    os.makedirs(os.path.join(ROOT, "guide"), exist_ok=True)
    urls = []
    shelf_of = {}
    for sh in plan["shelves"]:
        for i, item in enumerate(sh["items"]):
            shelf_of[item["slug"]] = (sh, i)

    # Each guide page
    for slug, g in guides.items():
        sh, i = shelf_of.get(slug, ({"key": g.get("shelf", ""), "title": "Guide", "items": []}, 0))
        items = sh["items"]
        toc = "".join(
            (f'<li class="{"on" if it["slug"] == slug else ""}"><a href="/guide/{it["slug"]}.html">{e(it["title"])}</a></li>' if it["slug"] in guides
             else f'<li class="soon"><span>{e(it["title"])}</span><small>Coming soon</small></li>') for it in items)
        nxt = next((it for it in items[i + 1:] if it["slug"] in guides), None)
        nxt_html = (f'<a class="guide-next" href="/guide/{nxt["slug"]}.html"><span class="small-label">Next in {e(sh["title"])}</span><b>{e(nxt["title"])}</b></a>'
                    if nxt else '<a class="guide-next" href="/guide/"><span class="small-label">Keep going</span><b>Back to the Guide</b></a>')
        au = authors.get(g.get("author", "tom"), {"name": "Eleven"})
        keys = "".join(f"<li>{linkify(k)}</li>" for k in g.get("key_points", []))
        sources = "".join(f'<li><a href="{e(s["url"])}" rel="noopener">{e(s["name"])}</a></li>' for s in g.get("sources", []))
        url = f"{site}/guide/{slug}.html"
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": g["title"][:110], "description": g.get("description") or g["summary"],
              "author": [{"@type": "Person", "name": au["name"], "url": f"{site}/authors/{g.get('author', 'tom')}.html"}],
              "publisher": {"@type": "NewsMediaOrganization", "name": "Eleven", "url": site,
                            "logo": {"@type": "ImageObject", "url": f"{site}/img/icons/eleven-logo.png", "width": 600, "height": 60}},
              "datePublished": g.get("published"), "dateModified": (g.get("updated") or g.get("published", ""))[:10], "mainEntityOfPage": url,
              "inLanguage": "en-GB", "isPartOf": {"@type": "CreativeWorkSeries", "name": f"Eleven Guide: {sh['title']}"}}
        crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Guide", "item": f"{site}/guide/"},
            {"@type": "ListItem", "position": 2, "name": sh["title"], "item": f"{site}/guide/#{sh['key']}"},
            {"@type": "ListItem", "position": 3, "name": g["title"], "item": url}]}
        head = f'<script type="application/ld+json">{json.dumps([ld, crumbs], ensure_ascii=False)}</script>'
        updated = g.get("updated") or g.get("published", "")[:10]
        upd = dt.date.fromisoformat(updated[:10]) if updated else None
        body = f"""<main class="wrap article-wrap guide-page">
<article class="article">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/guide/">Guide</a> / <a href="/guide/#{e(sh["key"])}">{e(sh["title"])}</a></nav>
  <span class="tag" style="color:var(--ball)">{e(g.get("level", "Guide"))} · {minutes(g)} min read</span>
  <h1>{e(g["title"])}</h1>
  <p class="standfirst">{e(g["summary"])}</p>
  <div class="article-byline"><span class="byline">{avatar(au, 36)}<span>By <a href="/authors/{e(g.get('author', 'tom'))}.html">{e(au["name"])}</a></span></span>{f'<time datetime="{updated}">Updated {upd.day} {upd:%B %Y}</time>' if upd else ""}</div>
  {f'<section class="key-points"><h2>In short</h2><ul>{keys}</ul></section>' if keys else ""}
  <div class="article-body guide-body">
{body_html(g, linkify)}
  </div>
  {nxt_html}
  {f'<section class="article-sources"><h2>Sources and further reading</h2><ul>{sources}</ul></section>' if sources else ""}
</article>
<aside class="article-side">
  <section class="panel guide-toc"><h2 class="rule-title">{e(sh["title"])}</h2><ol>{toc}</ol><a class="panel-link" href="/guide/">All guides</a></section>
  <div class="side-end"><div class="ad ad-side" data-ad="sidebar"></div></div>
</aside>
</main>"""
        title = g.get("seo_title") or g["title"]
        open(os.path.join(ROOT, "guide", f"{slug}.html"), "w", encoding="utf-8").write(
            page(f"{title} | Eleven Guide", (g.get("description") or g["summary"])[:300], url, body, head))
        urls.append((url, updated[:10] or dt.date.today().isoformat()))

    # The Guide's front page: shelves in order, from first steps to the pro game
    shelves = []
    for sh in plan["shelves"]:
        cards = []
        for it in sh["items"]:
            g = guides.get(it["slug"])
            if g:
                cards.append(f'<li class="gcard"><a href="/guide/{it["slug"]}.html"><h3>{e(g["title"])}</h3><p>{e(g["summary"])}</p>'
                             f'<span class="meta">{e(g.get("level", ""))} · {minutes(g)} min read</span></a></li>')
            else:
                cards.append(f'<li class="gcard soon"><h3>{e(it["title"])}</h3><span class="meta">Coming soon</span></li>')
        shelves.append(f'<section class="shelf" id="{e(sh["key"])}"><div class="shelf-head"><span class="shelf-num">{e(sh["num"])}</span>'
                       f'<div><h2>{e(sh["title"])}</h2><p>{e(sh["intro"])}</p></div></div><ol class="gcards">{"".join(cards)}</ol></section>')
    path = "".join(f'<li><a href="#{e(sh["key"])}"><b>{e(sh["num"])}</b>{e(sh["title"])}</a></li>' for sh in plan["shelves"])
    body = f"""<main class="wrap guide-home">
<section class="sched-head"><div><h1>The Guide</h1>
<p class="lede">{e(plan.get("intro", ""))}</p></div></section>
<nav class="guide-path" aria-label="Guide sections"><ol>{path}</ol></nav>
{"".join(shelves)}
</main>"""
    open(os.path.join(ROOT, "guide", "index.html"), "w", encoding="utf-8").write(
        page("Table tennis explained: rules, equipment and the pro game | Eleven Guide",
             "New to table tennis? Eleven's Guide explains the rules, how to start playing, equipment from blades to rubbers, and how the professional game works.",
             f"{site}/guide/", body))
    urls.append((f"{site}/guide/", dt.date.today().isoformat()))
    return urls
