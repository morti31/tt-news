"""Builds the article pages, news archive, sitemap and robots.txt.

Cloudflare runs this as the build command on every deploy:  python3 tools/build_site.py
It uses only the Python standard library.

Input:  data/articles/*.json  (one file per full article; merged into main once approved)
Output: news/<slug>.html, news/index.html, data/article-index.json, sitemap.xml, robots.txt, feed.xml
"""
import json, os, glob, html, sys, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import components
import build_events
import build_rankings

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = os.environ.get("SITE_URL", "https://tt-news.tommorti.workers.dev")
NEWS = json.load(open(os.path.join(ROOT, "data", "news.json"), encoding="utf-8"))
AUTHORS = NEWS.get("authors", {"tom": {"name": "Eleven"}})
EVENTS = build_events.load()
HUBS = {ev["id"]: ev for ev in EVENTS["events"]}
STORY_EVENT = {s["id"]: s["event"] for s in NEWS.get("stories", []) if s.get("event")}


def event_of(a):
    """The hub event an article or story belongs to, if any."""
    return HUBS.get(a.get("event") or STORY_EVENT.get(a.get("story_id"), ""))


def author_of(a):
    return AUTHORS.get(a.get("author", "tom"), AUTHORS.get("tom", {"name": "Eleven"}))
e = html.escape

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,600..800&family=Figtree:wght@400;500;600&family=Inter+Tight:wght@500;600;700;800&display=swap" rel="stylesheet">')

NAV = """<header class="masthead"><div class="wrap masthead-inner">
<a class="wordmark" href="/" aria-label="Eleven home">Eleven<span class="ball" aria-hidden="true"></span></a>
<nav aria-label="Sections"><ul class="sections">
<li><a href="/">Home</a></li><li><a href="/events/">Events</a></li><li><a href="/rankings.html">Rankings</a></li>
<li><a href="/#Clubs">Clubs</a></li><li><a href="/#Equipment">Equipment</a></li><li><a href="/schedule.html">Schedule</a></li>
</ul></nav></div></header>"""

FOOT = """<div class="wrap ad-wrap"><div class="ad ad-leader" data-ad="bottom"></div></div>
<footer class="footer"><div class="wrap"><p class="foot-mark">Eleven<span class="ball" aria-hidden="true"></span></p>
<nav class="foot-links" aria-label="Footer"><a href="/about.html">About</a><a href="/contact.html">Contact</a><a href="/#International">International</a><a href="/#England">England</a><a href="/events/">Events</a><a href="/news/">News</a><a href="/schedule.html">Schedule</a><a href="/contact.html#advertise">Advertise</a></nav>
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
    im = a.get("image") or {}
    ev = event_of(a)
    if im.get("type") != "photo" and ev and build_events.poster(ev):
        return (f'<figure class="article-hero poster">{build_events.picture(ev, ev["name"] + " " + ev["year"] + ": Eleven event poster", "/events/" + ev["id"] + ".html")}'
                f'<figcaption>{build_events.credit(ev)}</figcaption></figure>')
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
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/styles.css">
{extra_head}
</head>
<body>
{NAV.format(news_cur=' aria-current="page"' if news_cur else "")}
<section class="ticker" aria-label="Latest scores"><div class="wrap ticker-inner" id="ticker"></div></section>
<div class="wrap ad-wrap"><div class="ad ad-leader" data-ad="top"></div></div>
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


def story_list(arts):
    """Every story on the site, lead story first then newest, with what the story lists need."""
    amap = {x.get("story_id"): x for x in arts}
    out = []
    for s in NEWS.get("stories", []):
        a = amap.get(s["id"])
        vids = (a or {}).get("videos") or s.get("videos") or []
        out.append({"id": s["id"], "slug": a["slug"] if a else s["id"], "url": f"/news/{a['slug'] if a else s['id']}.html",
                    "title": a["title"] if a else s["headline"], "category": s["category"], "top": s.get("top"),
                    "published": (a or {}).get("published") or s.get("published") or s["date"] + "T09:00:00Z",
                    "event": s.get("event") or (a or {}).get("event"), "video": vids[0]["id"] if vids else None,
                    "image": (a or {}).get("image") or s.get("image"), "author": s.get("author", "tom")})
    out.sort(key=lambda i: i["published"], reverse=True)
    out.sort(key=lambda i: not i["top"])
    return out


STORIES = []
TOP = []   # story ids in Top stories order (see top_stories)

# How much each kind of event matters, on the schedule's 1 to 5 prestige scale
TIER_PRESTIGE = {"world": 5, "smash": 4, "continental": 3.5, "champions": 3, "star": 2, "contender": 1.5, "club": 2}
CATEGORY_PRESTIGE = {"International": 2.5, "England": 2, "Clubs": 2, "Equipment": 1.5}


def top_stories(stories, now=None):
    """Top stories by weight, not just time.

    score = freshness x (0.5 + importance + extras), then a diversity pass.
      freshness  halves every 18 hours, so a big story stays up for a day or two and then gives way
      importance the event's prestige (schedule 1 to 5, divided by 5); stories without an event use their section
      extras     +0.15 a full article, +0.1 match results, +0.1 official video, +0.25 the event is on now
      diversity  each further story from the same event counts 25% less, so one tournament can't fill the list
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    sched = {ev["id"]: ev for ev in json.load(open(os.path.join(ROOT, "data", "schedule.json"), encoding="utf-8")).get("events", [])}
    today = now.date().isoformat()
    amap = {}
    for f in glob.glob(os.path.join(ROOT, "data", "articles", "*.json")):
        x = json.load(open(f, encoding="utf-8"))
        amap[x.get("story_id")] = x
    raw = {s["id"]: s for s in NEWS.get("stories", [])}
    scored = []
    for i in stories:
        hub = HUBS.get(i["event"] or "")
        if hub and hub.get("schedule_id") in sched and sched[hub["schedule_id"]].get("prestige"):
            prestige = sched[hub["schedule_id"]]["prestige"]
        elif hub:
            prestige = TIER_PRESTIGE.get(hub["tier"], 2.5)
        else:
            prestige = CATEGORY_PRESTIGE.get(i["category"], 2)
        age = max(0, (now - dt.datetime.fromisoformat(i["published"].replace("Z", "+00:00"))).total_seconds() / 3600)
        fresh = 0.5 ** (age / 18)
        art, s = amap.get(i["id"]), raw.get(i["id"], {})
        extras = (0.15 if art else 0) + (0.1 if (art or s).get("matches") else 0) + (0.1 if i["video"] else 0)
        if hub and hub.get("start") and hub["start"] <= today <= hub["end"]:
            extras += 0.25
        scored.append([fresh * (0.5 + prestige / 5 + extras), i])
    out, per_event = [], {}
    pool = sorted(scored, key=lambda x: -x[0])
    while pool:
        for x in pool:   # re-weight by how many of the same event are already in
            x.append(x[0] * 0.75 ** per_event.get(x[1]["event"] or x[1]["id"], 0))
        pool.sort(key=lambda x: -x[-1])
        best = pool.pop(0)
        out.append(best[1])
        k = best[1]["event"] or best[1]["id"]
        per_event[k] = per_event.get(k, 0) + 1
        for x in pool:
            del x[-1]
    return out


def story_thumb(i, seen):
    """Same picture order as the homepage: video, event poster (once per page), photo, illustration."""
    if i["video"]:
        return (f'<div class="pic video-art"><img src="https://i.ytimg.com/vi/{e(i["video"])}/hqdefault.jpg" alt="" loading="lazy">'
                f'<span class="yt-play" aria-hidden="true"></span></div>')
    ev = HUBS.get(i["event"] or "")
    if ev and build_events.poster(ev) and ev["id"] not in seen:
        seen.add(ev["id"])
        return f'<div class="pic poster"><img src="{build_events.poster(ev)}" alt="" loading="lazy"></div>'
    im = i["image"] or {}
    if im.get("type") == "photo":
        return f'<div class="pic photo"><img src="{e(im["url"])}" alt="" loading="lazy"></div>'
    if im.get("type") == "cartoon":
        return f'<div class="pic cartoon"><img src="/{e(im["src"])}" alt="" loading="lazy"></div>'
    return ""


def side_extras(a, ev0):
    """Sidebar panels kept in reserve for long stories, shown in this order until the columns line up."""
    out = []
    today = dt.date.today().isoformat()
    # Latest results: live from WTT for the event on now, otherwise the most recent event's finals
    live = next((h for h in HUBS.values() if h.get("wtt_id") and h.get("start") and h["start"] <= today <= h["end"]), None)
    if live:
        out.append(f'<section class="panel" data-extra data-wtt="{e(live["wtt_id"])}"><h2 class="rule-title">Latest results</h2>'
                   f'<p class="small">{e(live["name"])}</p><ul class="lr"><li>Loading…</li></ul><a class="panel-link" href="/events/{live["id"]}.html#live">Live scores</a></section>')
    elif NEWS.get("results"):
        r = NEWS["results"][0]
        rows = "".join(f'<li><span class="lr-label">{e(m["round"])}</span><span class="won">{e(m["winner"])}</span><b>{e(m["score"])}</b><span>{e(m["loser"])}</span></li>'
                       for m in r["matches"][:6] if m.get("loser"))
        out.append(f'<section class="panel" data-extra><h2 class="rule-title">Latest results</h2><p class="small">{e(r["event"])}</p><ul class="lr">{rows}</ul></section>')
    # Watch: one official highlight, from this story's event if there is one
    hl = sorted(NEWS.get("highlights", []), key=lambda v: v["date"], reverse=True)
    own = [v for v in hl if ev0 and v.get("event") == ev0["id"]]
    pick = (own or hl or [None])[0]
    if pick and pick["id"] not in {v["id"] for v in a.get("videos") or []}:
        out.append(f'<section class="panel" data-extra><h2 class="rule-title">Watch</h2>{components.videos([pick]).replace("<h2 id=\"vid-h\">Watch</h2>", "")}</section>')
    # The next major event, with its poster
    nxt = sorted((h for h in HUBS.values() if h.get("start") and h["start"] > today and h is not ev0), key=lambda h: h["start"])
    if nxt and build_events.tile(nxt[0]):
        h = nxt[0]
        out.append(f'<section class="panel" data-extra><h2 class="rule-title">Next up</h2><a class="ev-tile" href="/events/{h["id"]}.html">'
                   f'<img src="{build_events.tile(h)}" alt="" loading="lazy"><h3>{e(h["name"])} {e(h["year"])}</h3><span>{e(build_events.dates(h))}</span></a></section>')
    out.append('<div class="ad ad-side" data-extra data-ad="sidebar3"></div>')
    return "\n".join(out)


def short_when(iso):
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(UK)
    return f"{t.day} {t:%b}, {t:%H:%M}"


def article_page(a, others, brief=False):
    AUTHOR = author_of(a)
    url = f"{SITE}/news/{a['slug']}.html"
    words = sum(len(p.split()) for p in a["body"])
    tag = f'<span class="tag" style="color:var(--{e(a["category"])}, var(--ink))">{e(a["category"])}'
    if a.get("lang"):
        tag += f'<span class="translated">, translated from {e(a["lang"])}</span>'
    tag += "</span>"
    ev = event_of(a)
    crumb = (f'<a href="/events/">Events</a> / <a href="/events/{ev["id"]}.html">{e(ev["name"])} {e(ev["year"])}</a>' if ev
             else f'<a href="/#{e(a["category"])}">{e(a["category"])}</a>')
    ps = [f"<p>{e(p)}</p>" for p in a["body"]]
    # Highlights sit after the second paragraph, like a broadcaster's match report
    vids = a.get("videos") or []
    # The first official video becomes the lead image; any others go in the Watch section
    ps.insert(min(2, len(ps)), components.videos(vids[1:]))
    paras = "\n".join(x for x in ps if x)
    sources = "".join(f'<li><a href="{e(s["url"])}" rel="noopener">{e(s["name"])}</a></li>' for s in a["sources"])
    cur = a.get("story_id") or a["slug"]
    pool = [i for i in STORIES if i["id"] != cur and i["slug"] != a["slug"]]
    tops = [i for i in TOP if i["id"] != cur and i["slug"] != a["slug"]][:5]
    rest = [i for i in pool if i not in tops]
    tops_html = "".join(f'<li><a href="{i["url"]}">{e(i["title"])}</a><span class="meta">{short_when(i["published"])}</span></li>' for i in tops)
    ev0 = event_of(a)
    seen = {ev0["id"]} if ev0 else set()   # this story's own poster is already at the top
    more_html = "".join(
        f'<article class="promo">{story_thumb(i, seen)}<div><span class="kicker" style="color:var(--{e(i["category"])}, var(--ink))">'
        f'{e(HUBS[i["event"]]["name"] if i["event"] in HUBS else i["category"])}</span>'
        f'<h3><a class="stretch" href="{i["url"]}">{e(i["title"])}</a></h3><span class="meta">{short_when(i["published"])} · By {e(AUTHORS.get(i["author"], {}).get("name", "Eleven"))}</span></div></article>'
        for i in rest[:16])
    extras = side_extras(a, ev0)
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
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / {crumb}</nav>
  {tag}
  <h1>{e(a['title'])}</h1>
  {f'<p class="standfirst">{e(a["standfirst"])}</p>' if a.get("standfirst") else ""}
  <div class="article-byline"><span class="byline">{avatar(AUTHOR, 36)}<span>By {e(AUTHOR['name'])}</span></span><time datetime="{e(a.get('published', a['date']))}">{pub_time(a)}</time></div>
  {components.scoreboard(a.get("matches"))}
  {components.video_hero(vids[0]) if vids else hero(a)}
  <div class="article-body">
{paras}
  </div>
  {components.social(a.get("social"))}
  {components.draw(a.get("draw"))}
  {f'<a class="event-link" href="/events/{ev["id"]}.html" style="--tier:{build_events.TIERS.get(ev["tier"], "#17202b")}"><span class="small-label">Event guide</span><b>{e(ev["name"])} {e(ev["year"])}</b><span>Results, draw, schedule and all the news</span></a>' if ev else ""}
  <section class="article-sources"><h2>Sources</h2><ul>{sources}</ul></section>
  {f'<section class="more-news"><div class="sec-head"><h2>More news</h2><a href="/news/">All news</a></div><div class="promos" id="more-news">{more_html}</div></section>' if more_html else ""}
</article>
<aside class="article-side">
  <div class="ad ad-side" data-ad="sidebar"></div>
  {f'<section class="panel author"><div class="author-head">{avatar(AUTHOR, 56)}<div><p class="small-label">Writer</p><h2 class="panel-title">{e(AUTHOR["name"])}</h2></div></div><p class="author-bio">{e(AUTHOR["bio"])}</p></section>' if AUTHOR.get("bio") else ""}
  {f'<section class="panel tops"><h2 class="rule-title">Top stories</h2><ol>{tops_html}</ol></section>' if tops_html else ''}
  <section class="panel"><h2 class="panel-title">World rankings</h2>
    <div class="toggle" id="rank-toggle" role="group" aria-label="Rankings"><button data-g="men" aria-pressed="true">Men</button><button data-g="women" aria-pressed="false">Women</button></div>
    <div id="rank-lead" class="rank-lead"></div><ol id="rankings" class="rankings"></ol><p class="small" id="rank-week"></p></section>
  <section class="panel"><h2 class="panel-title">Coming up</h2><ul id="events" class="events" data-count="5"></ul>
    <a class="panel-link" href="/schedule.html">Full schedule and calendar</a></section>
  {extras}
  <div class="side-end"><div class="ad ad-side" data-ad="sidebar2"></div></div>
</aside>
</main>
<section class="wrap more-wide" hidden><div class="sec-head"><h2>More news</h2><a href="/news/">All news</a></div><div class="more-grid" id="more-grid"></div></section>
{components.SCRIPT}
<script>
// Balance the two columns, BBC style:
// 1. a long story: add sidebar panels (latest results, a video, the next event) until the sidebar reaches the end of the story
// 2. a short story: add "More news" under it until it reaches the end of the sidebar
// 3. anything left over runs full width below both columns
(function () {{
  var side = document.querySelector(".article-side"), end = document.querySelector(".article-sources");
  var list = document.getElementById("more-news"), grid = document.getElementById("more-grid");
  if (!side || !end) return;
  var extras = [].slice.call(side.querySelectorAll("[data-extra]"));
  var items = list ? [].slice.call(list.querySelectorAll(".promo")) : [];
  var bottom = function (el) {{ return el.getBoundingClientRect().bottom; }};
  var sideEnd = function () {{ var k = side.querySelector(".side-end"); return k.getBoundingClientRect().top; }};
  function fit() {{
    var stacked = side.getBoundingClientRect().top > end.getBoundingClientRect().top;
    extras.forEach(function (x) {{ x.hidden = true; }});
    items.forEach(function (x) {{ list.appendChild(x); x.hidden = false; }});
    if (list) list.closest(".more-news").hidden = false;
    if (stacked) {{
      items.forEach(function (x, k) {{ x.hidden = k >= 6; }});
    }} else {{
      for (var i = 0; i < extras.length && sideEnd() < bottom(end) - 60; i++) extras[i].hidden = false;
      var shown = 0;
      items.forEach(function (x) {{ x.hidden = true; }});
      for (var j = 0; j < items.length; j++) {{
        if (bottom(list.closest(".more-news")) > sideEnd() + 40 && shown > 0) break;
        if (shown === 0 && bottom(end) > sideEnd() - 120) break;
        items[j].hidden = false; shown++;
      }}
      if (list) list.closest(".more-news").hidden = shown === 0;
    }}
    var left = stacked ? [] : items.filter(function (x) {{ return x.hidden; }}).slice(0, 8);
    grid.innerHTML = "";
    left.forEach(function (x) {{ var c = x.cloneNode(true); c.hidden = false; grid.appendChild(c); }});
    grid.closest(".more-wide").hidden = !left.length;
    // one "More news" heading: if the list under the story is showing, the full-width row just continues it
    grid.closest(".more-wide").classList.toggle("continues", !!list && !list.closest(".more-news").hidden);
  }}
  fit();
  window.addEventListener("load", fit);
  window.addEventListener("resize", function () {{ clearTimeout(fit.r); fit.r = setTimeout(fit, 150); }});
  new MutationObserver(function () {{ clearTimeout(fit.t); fit.t = setTimeout(fit, 250); }}).observe(side, {{ childList: true, subtree: true }});
  // Latest results panel: live from WTT while an event is on
  var lr = side.querySelector("[data-wtt]");
  if (lr) fetch("/api/live?event=" + lr.dataset.wtt).then(function (r) {{ return r.json(); }}).then(function (d) {{
    var ms = (d.live || []).concat(d.results || []).slice(0, 6);
    if (!ms.length) return;
    lr.querySelector("ul").innerHTML = ms.map(function (m) {{
      var w = m.status === "live" ? -1 : (m.score[0] > m.score[1] ? 0 : 1);
      var nm = function (i) {{ return '<span class="' + (w === i ? "won" : "") + '">' + m.sides[i].name.replace(/[<>&]/g, "") + "</span>"; }};
      return '<li><span class="lr-label">' + (m.status === "live" ? '<span class="live-dot"></span>Live · ' : "") + m.label + "</span>" + nm(0) + "<b>" + m.score[0] + "–" + m.score[1] + "</b>" + nm(1) + "</li>";
    }}).join("");
  }}).catch(function () {{}});
}})();
</script>"""
    og = img.get("url") if img.get("type") == "photo" else (SITE + build_events.poster(ev) if ev and build_events.poster(ev) else None)
    desc = a.get("standfirst") or (a["body"][0] if a["body"] else a["title"])
    # Short stories stay readable and shareable but are kept out of Google's index as thin pages
    return page(f"{a['title']} | Eleven", desc[:300], url, body, head, og_image=og, og_type="article",
                robots="noindex, follow" if brief else None)


def main():
    global STORIES
    arts = load_articles()
    STORIES = story_list(arts)
    global TOP
    TOP = top_stories(STORIES)
    json.dump([i["id"] for i in TOP], open(os.path.join(ROOT, "data", "top-stories.json"), "w"))
    os.makedirs(os.path.join(ROOT, "news"), exist_ok=True)
    for a in arts:
        others = [o for o in arts if o["slug"] != a["slug"]]
        open(os.path.join(ROOT, "news", a["slug"] + ".html"), "w", encoding="utf-8").write(article_page(a, others))

    items = "".join(f"""<li class="archive-item"><a href="/news/{e(a['slug'])}.html"><span class="tag" style="color:var(--{e(a['category'])}, var(--ink))">{e(a['category'])}</span>
<h2>{e(a['title'])}</h2><p>{e(a['standfirst'])}</p><time datetime="{e(a.get('published', a['date']))}">By {e(author_of(a)["name"])}, {pub_time(a)}</time></a></li>""" for a in arts)
    archive = f"""<main class="wrap"><section class="sched-head"><div><h1>News</h1><p class="lede">Every news story published on Eleven, newest first.</p></div></section>
<ul class="archive">{items or '<li class="empty">No news yet.</li>'}</ul></main>"""
    open(os.path.join(ROOT, "news", "index.html"), "w", encoding="utf-8").write(
        page("News | Eleven", "Every table tennis news story published on Eleven.", f"{SITE}/news/", archive, news_cur=True))

    index = {a.get("story_id", a["slug"]): {"slug": a["slug"], "url": f"/news/{a['slug']}.html", "published": a.get("published"),
                                            **({"video": a["videos"][0]["id"]} if a.get("videos") else {})} for a in arts}

    # Short stories without a full article get a short page of their own
    briefs = 0
    for s in NEWS.get("stories", []):
        if s["id"] in index:
            continue
        brief = {"slug": s["id"], "title": s["headline"], "standfirst": "", "category": s["category"], "date": s["date"],
                 "body": s.get("body") or [s["summary"]], "sources": s.get("sources", []), "author": s.get("author", "tom")}
        for k in ("lang", "image", "published", "matches", "videos", "draw", "social", "event"):
            if s.get(k):
                brief[k] = s[k]
        open(os.path.join(ROOT, "news", s["id"] + ".html"), "w", encoding="utf-8").write(article_page(brief, arts, brief=True))
        index[s["id"]] = {"slug": s["id"], "url": f"/news/{s['id']}.html", "brief": True,
                          **({"video": s["videos"][0]["id"]} if s.get("videos") else {})}
        briefs += 1
    json.dump(index, open(os.path.join(ROOT, "data", "article-index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    hubs = build_hubs(arts)

    open(os.path.join(ROOT, "about.html"), "w", encoding="utf-8").write(about_page())
    R = build_rankings.load()
    if R:
        with_article = {a.get("story_id") for a in arts}
        items = [(a.get("published", a["date"]), f"/news/{a['slug']}.html", " ".join([a["title"], a.get("standfirst", ""), *a["body"]])) for a in arts]
        items += [(s.get("published", s["date"]), f"/news/{s['id']}.html", " ".join([s["headline"], s["summary"], *(s.get("body") or [])]))
                  for s in NEWS.get("stories", []) if s["id"] not in with_article]
        items.sort(key=lambda x: x[0], reverse=True)
        desc = f'The official ITTF world table tennis rankings, {R["label"].split(", ", 1)[1]}: the top 100 men and women with points and movement.'
        open(os.path.join(ROOT, "rankings.html"), "w", encoding="utf-8").write(
            page("World rankings: top 100 men and women | Eleven", desc, f"{SITE}/rankings.html", build_rankings.body(R, items)))
    open(os.path.join(ROOT, "contact.html"), "w", encoding="utf-8").write(contact_page())

    today = dt.date.today().isoformat()
    urls = [(f"{SITE}/", today), (f"{SITE}/schedule.html", today), (f"{SITE}/rankings.html", today), (f"{SITE}/about.html", today), (f"{SITE}/contact.html", today), (f"{SITE}/news/", arts[0]["date"] if arts else today)]
    urls += [(f"{SITE}/news/{a['slug']}.html", a.get("modified", a["date"])[:10]) for a in arts]
    urls += [(f"{SITE}/events/", today)] + [(f"{SITE}/events/{h}.html", today) for h in hubs]
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


def build_hubs(arts):
    """Event hub pages, their calendars, the events index and data/event-index.json."""
    os.makedirs(os.path.join(ROOT, "events"), exist_ok=True)
    schedule = json.load(open(os.path.join(ROOT, "data", "schedule.json"), encoding="utf-8"))
    today = dt.datetime.now(UK).date().isoformat()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    with_article = {a.get("story_id") for a in arts}
    for ev in EVENTS["events"]:
        items = []
        for a in arts:
            if event_of(a) is ev:
                items.append((a, f"/news/{a['slug']}.html", a.get("published", a["date"]), f"By {author_of(a)['name']}, {pub_time(a)}"))
        for s in NEWS.get("stories", []):
            if s.get("event") == ev["id"] and s["id"] not in with_article:
                items.append((s, f"/news/{s['id']}.html", s.get("published", s["date"]), f"By {author_of(s)['name']}, {pub_time(s)}"))
        items.sort(key=lambda x: x[2], reverse=True)
        body = build_events.hub(ev, items, schedule, today, NEWS)
        place = ev.get("venue") or ev["city"]
        desc = f'{ev["name"]} {ev["year"]}, {build_events.dates(ev)}, {place}: results, draw, schedule and news.'
        poster = build_events.poster(ev)
        open(os.path.join(ROOT, "events", ev["id"] + ".html"), "w", encoding="utf-8").write(
            page(f'{ev["name"]} {ev["year"]}: results, draw and schedule | Eleven', desc, f'{SITE}/events/{ev["id"]}.html', body,
                 og_image=SITE + poster if poster else None))
        if ev.get("start"):
            open(os.path.join(ROOT, "events", ev["id"] + ".ics"), "w", encoding="utf-8", newline="").write(build_events.calendar(ev, schedule, SITE, stamp))
    open(os.path.join(ROOT, "events", "index.html"), "w", encoding="utf-8").write(
        page("Events | Eleven", "Major table tennis tournaments: draws, results, schedules and news.", f"{SITE}/events/", build_events.index_page(EVENTS, today)))
    json.dump(build_events.event_index(EVENTS), open(os.path.join(ROOT, "data", "event-index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return [ev["id"] for ev in EVENTS["events"]]


def about_page():
    team = []
    for key, role in (("tom", "Editor, equipment"), ("michael", "International"), ("michelle", "England and clubs")):
        au = AUTHORS.get(key)
        if not au:
            continue
        team.append(f'''<section class="panel author"><div class="author-head">{avatar(au, 56)}<div><p class="small-label">{role}</p>
<h3 class="panel-title">{e(au["name"])}</h3></div></div>{f'<p class="author-bio">{e(au["bio"])}</p>' if au.get("bio") else ""}</section>''')
    body = f"""<main class="wrap info-wrap">
<section class="sched-head"><div><h1>About Eleven</h1>
<p class="lede">Table tennis news, results, rankings and fixtures from around the world, in one place and in English.</p></div></section>
<div class="info-grid"><div class="info-body">
<h2>Why Eleven exists</h2>
<p>Table tennis is one of the most played sports in the world, but its news is scattered. The biggest stories often break first in Chinese, Japanese or Korean, results sit on federation sites, and club competitions from the China Super League to the Bundesliga rarely reach English-language readers at all.</p>
<p>Eleven brings that together: international tournaments, the English game, the major club leagues and equipment news, alongside live results, the ITTF world rankings and a schedule you can add to your own calendar.</p>
<h2>How we report</h2>
<p>We follow coverage from federations, organisers and media in English, Chinese, Japanese, Korean, German and French. Stories that rely mainly on non-English sources are marked as translated, and every story lists the sources it draws on so you can read the original reporting.</p>
<p>We keep what has been confirmed separate from what has been reported, and say who reported it. Rankings come from the official ITTF list, and fixtures from organisers' published schedules.</p>
<h2>Corrections</h2>
<p>If we get something wrong, we want to know. Tell us through the <a href="/contact.html">contact page</a> and we will check it and correct the story. Significant corrections are noted on the story.</p>
<h2>Photos and illustrations</h2>
<p>Photos are used under Creative Commons and other free licences, with the photographer and licence credited on each image. Illustrations are drawn for Eleven.</p>
</div>
<aside class="info-side"><h2 class="section-title">The team</h2>{"".join(team)}</aside></div>
</main>"""
    return page("About | Eleven", "About Eleven: table tennis news, results, rankings and fixtures from around the world.", f"{SITE}/about.html", body)


def contact_page():
    key = NEWS.get("contact", {}).get("web3forms_key", "")
    body = f"""<main class="wrap info-wrap">
<section class="sched-head"><div><h1>Contact</h1>
<p class="lede">Story tips, corrections, advertising or anything else. Send us a message and we'll get back to you.</p></div></section>
<div class="info-grid"><div>
<form class="panel contact-form" id="contact-form" data-key="{e(key)}" novalidate>
  <input type="hidden" name="subject" value="New message from Eleven">
  <input type="checkbox" name="botcheck" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
  <label>Your name<input name="name" required autocomplete="name"></label>
  <label>Email<input name="email" type="email" required autocomplete="email" placeholder="name@example.com"></label>
  <label>What's it about?<select name="topic">
    <option>General enquiry</option><option>Story tip</option><option>Correction</option><option>Advertising</option></select></label>
  <label>Message<textarea name="message" rows="6" required></textarea></label>
  <p class="form-error" id="form-error" role="alert" hidden></p>
  <button class="btn btn-primary" type="submit">Send message</button>
  <p class="form-done" id="form-done" role="status" hidden>Message sent. Thanks, we'll reply as soon as we can.</p>
</form></div>
<aside class="info-side">
<section class="panel"><h2 class="panel-title">Corrections</h2><p class="author-bio">Choose "Correction", include the link to the story and tell us what needs fixing.</p></section>
<section class="panel" id="advertise"><h2 class="panel-title">Advertise with Eleven</h2><p class="author-bio">Eleven reaches table tennis players and fans across the UK and beyond. Choose "Advertising" and tell us what you have in mind.</p></section>
</aside></div>
</main>
<script>
(function () {{
  const form = document.getElementById("contact-form"), err = document.getElementById("form-error"), done = document.getElementById("form-done");
  const topic = new URLSearchParams(location.search).get("topic") || (location.hash === "#advertise" ? "Advertising" : "");
  if (topic) [...form.topic.options].forEach((o) => {{ if (o.text === topic) o.selected = true; }});
  const show = (m) => {{ err.textContent = m; err.hidden = !m; }};
  form.addEventListener("input", () => show(""));
  form.addEventListener("submit", async (ev) => {{
    ev.preventDefault();
    if (!form.name.value.trim()) return show("Enter your name.");
    if (!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(form.email.value)) return show("Enter a valid email address.");
    if (!form.message.value.trim()) return show("Write a message first.");
    if (!form.dataset.key) return show("The contact form isn't switched on yet. Please try again soon.");
    const data = new FormData(form); data.append("access_key", form.dataset.key);
    data.set("subject", "Eleven: " + form.topic.value);
    const btn = form.querySelector("button"); btn.disabled = true; btn.textContent = "Sending";
    try {{
      const r = await fetch("https://api.web3forms.com/submit", {{ method: "POST", body: data }}).then((x) => x.json());
      if (!r.success) throw new Error(r.message);
      form.querySelectorAll("label, button").forEach((x) => x.hidden = true); done.hidden = false;
    }} catch (e) {{ show("Your message didn't send. Check your connection and try again."); btn.disabled = false; btn.textContent = "Send message"; }}
  }});
}})();
</script>"""
    return page("Contact | Eleven", "Contact Eleven with story tips, corrections or advertising enquiries.", f"{SITE}/contact.html", body)


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
