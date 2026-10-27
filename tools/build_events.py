"""Event hub pages: one page per major tournament, plus the events index.

Called from build_site.py. Input: data/events.json (hub events and poster details), data/schedule.json
(fixtures), data/news.json and data/articles/*.json (stories and articles with "event": "<hub id>").
Output: events/<id>.html, events/<id>.ics, events/index.html, data/event-index.json.
"""
import json, os, datetime as dt, html
import components
import posters

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TIER_NAMES = {"world": "World event", "smash": "Grand Smash", "champions": "WTT Champions level", "continental": "Continental championships",
              "star": "WTT Star Contender", "contender": "WTT Contender", "club": "Club competition"}


def load():
    path = os.path.join(ROOT, "data", "events.json")
    data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {"events": []}
    posters.assign_variants(data["events"])   # same photo and colour choices as the rendered posters
    return data


def credit(ev):
    return posters.credit(ev)


def tile(ev):
    p = f"img/posters/{ev['id']}-sq.jpg"
    return "/" + p if os.path.exists(os.path.join(ROOT, p)) else None


def picture(ev, alt, link=None):
    """The poster as a responsive image: the square version on phones, the wide one elsewhere."""
    sq = tile(ev)
    src = f'<source media="(max-width: 600px)" srcset="{sq}" width="1000" height="1000">' if sq else ""
    img = f'<picture>{src}<img src="{poster(ev)}" alt="{e(alt)}" width="1600" height="900"></picture>'
    return f'<a href="{link}">{img}</a>' if link else img


def poster(ev):
    p = f"img/posters/{ev['id']}.jpg"
    return "/" + p if os.path.exists(os.path.join(ROOT, p)) else None


def dates(ev):
    if ev.get("dates_text") or not ev.get("start"):
        return ev.get("dates_text", "")
    a, b = dt.date.fromisoformat(ev["start"]), dt.date.fromisoformat(ev["end"])
    if a == b:
        return f"{a.day} {a:%B %Y}"
    return f"{a.day} to {b.day} {b:%B %Y}" if a.month == b.month else f"{a.day} {a:%B} to {b.day} {b:%B %Y}"


def status(ev, today):
    end = ev.get("end")
    if ev.get("start") and ev["start"] <= today <= end:
        return "now"
    return "past" if end and end < today else "next"


# Soft tints for the homepage's "on now" section, by poster colour: (background, rule, text)
TINTS = {"#d4213d": ("#fcedef", "#f2d3d8", "#5c0716"), "#f37021": ("#fdf1e8", "#f6dcc8", "#5e2205"),
         "#3a66e0": ("#eef2fb", "#d5ddf2", "#13235b"), "#12917a": ("#eaf6f2", "#cfe8df", "#063a30"),
         "#7a3cf0": ("#f2edfc", "#ddd1f6", "#2a1063"), "#0a84c4": ("#e9f4fa", "#cbe3f1", "#04263b"),
         "#d98a00": ("#fbf3e3", "#f0dfba", "#3a2200"), "#00a39b": ("#e7f6f5", "#c7e8e6", "#00302e"),
         "#2aa198": ("#e8f6f4", "#cbe9e5", "#0e4a46"), "#6b7586": ("#f1f2f5", "#dcdfe5", "#262c36"),
         "#23895c": ("#e9f5ef", "#cde7da", "#0b3a26")}


def index_entry(ev):
    c = posters.palette(ev)[0]
    bg, rule, ink = TINTS.get(c, ("#f1f3f7", "#dde1e8", "#111418"))
    return {"url": f"/events/{ev['id']}.html", "name": ev["name"], "year": ev["year"], "poster": poster(ev), "tile": tile(ev),
            "wtt": ev.get("wtt_id"), "series": ev["series"], "city": ev["city"], "venue": ev.get("venue"), "start": ev.get("start"),
            "end": ev.get("end"), "group": ev["group"], "stream_q": ev.get("stream_q") or f'{ev["city"]} {ev["year"]}', "colour": c, "tint": bg, "tint_rule": rule, "tint_ink": ink}


def event_index(data):
    """Hub lookup for the homepage and widgets, keyed by hub id and by schedule id."""
    out = {}
    for ev in data["events"]:
        out[ev["id"]] = index_entry(ev)
        if ev.get("schedule_id"):
            out[ev["schedule_id"]] = out[ev["id"]]
    return out


def _cap(s):
    return s[:1].upper() + s[1:]


def _uk(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(components.UK)


def _fixtures(ev, schedule):
    fx = sorted((f for f in schedule.get("fixtures", []) if ev.get("schedule_id") and f.get("event_id") == ev["schedule_id"]), key=lambda f: f["start"])
    if not fx:
        return ""
    days, out = {}, []
    for f in fx:
        days.setdefault(_uk(f["start"]).date(), []).append(f)
    prefix = ev["name"] + ": "
    for d, items in days.items():
        rows = "".join(f'<li><time datetime="{e(f["start"])}">{_uk(f["start"]):%H:%M}</time><span>{e(_cap(f["name"].removeprefix(prefix)))}</span></li>' for f in items)
        out.append(f'<div class="fx-day"><h3>{d:%A} {d.day} {d:%B}</h3><ul class="fx-list">{rows}</ul></div>')
    return f'<section class="hub-sec" id="schedule"><h2 class="section-title">Schedule</h2><p class="small">UK time. Session and match times from the organiser and published order of play.</p>{"".join(out)}</section>'


def _rank(m):
    lab = m.get("label", "").lower()
    if "semi" in lab:
        return 1
    if "quarter" in lab:
        return 2
    return 0 if "final" in lab else 3


def calendar(ev, schedule, site, stamp):
    """Per-event .ics with the tournament and its timed fixtures."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Eleven//Event calendar//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             f"X-WR-CALNAME:Eleven: {ev['name']} {ev['year']}", "REFRESH-INTERVAL;VALUE=DURATION:PT6H"]
    esc = lambda s: str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    place = esc(ev.get("venue") and f"{ev['venue']}, {ev['city']}, {ev['country']}" or f"{ev['city']}, {ev['country']}")
    if ev.get("start"):
        a, b = dt.date.fromisoformat(ev["start"]), dt.date.fromisoformat(ev["end"]) + dt.timedelta(days=1)
        lines += ["BEGIN:VEVENT", f"UID:{ev.get('schedule_id', ev['id'])}@eleven-tt", f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{a:%Y%m%d}",
                  f"DTEND;VALUE=DATE:{b:%Y%m%d}", "SUMMARY:" + esc(ev["name"]), "DESCRIPTION:" + esc(f"{site}/events/{ev['id']}.html"),
                  "LOCATION:" + place, "TRANSP:TRANSPARENT", "END:VEVENT"]
    for f in schedule.get("fixtures", []):
        if not ev.get("schedule_id") or f.get("event_id") != ev["schedule_id"]:
            continue
        s = dt.datetime.fromisoformat(f["start"].replace("Z", "+00:00"))
        en = dt.datetime.fromisoformat(f["end"].replace("Z", "+00:00")) if f.get("end") else s + dt.timedelta(hours=2)
        lines += ["BEGIN:VEVENT", f"UID:{f['id']}@eleven-tt", f"DTSTAMP:{stamp}", f"DTSTART:{s:%Y%m%dT%H%M%SZ}", f"DTEND:{en:%Y%m%dT%H%M%SZ}",
                  "SUMMARY:" + esc(f["name"]), "LOCATION:" + place, "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def hub(ev, items, schedule, today, news):
    """items: list of (story_or_article dict, url, published, author name), newest first."""
    st = status(ev, today)
    pill = {"now": '<span class="hub-status now">On now</span>', "next": '<span class="hub-status">Coming up</span>',
            "past": '<span class="hub-status past">Finished</span>'}[st]
    img = poster(ev)
    hero = f'<figure class="hub-poster">{picture(ev, ev["name"] + " " + ev["year"] + " poster")}<figcaption>{credit(ev)}</figcaption></figure>' if img else ""
    place = ev.get("venue") and f'{ev["venue"]}, {ev["city"]}, {ev["country"]}' or f'{ev["city"]}, {ev["country"]}'
    live = ""
    if st == "now" and ev.get("live"):
        live = f'<a class="btn btn-primary" href="{e(news.get("live_results_url", "https://www.worldtabletennis.com/"))}" rel="noopener">Live scores on WTT</a>'
    cal = f'<a class="btn" href="/events/{ev["id"]}.ics">Add to calendar</a>' if ev.get("start") else ""

    # Results: every match reported in this event's stories, finals first, each match once
    seen, matches = set(), []
    for it, *_ in items:
        for m in it.get("matches") or []:
            key = (m.get("label"), tuple(p["name"] for p in m.get("sides", [])))
            if key not in seen:
                seen.add(key)
                matches.append(m)
    matches.sort(key=_rank)
    # Equal prominence: big side-by-side cards only once there is both a men's and a women's result;
    # until then every result is listed at the same size
    genders = {components._gender(m) for m in matches}
    board = components.scoreboard(matches) if {"M", "W"} <= genders else (
        '<section class="scoreboard" aria-label="Results"><div class="sb-more">' + "".join(components._compact(m) for m in matches) + "</div></section>")
    # Live scores straight from WTT while the event is on (refreshed in the browser by /live.js)
    live_sec = ""
    if ev.get("wtt_id") and st != "past":
        live_sec = (f'<section class="hub-sec lv" id="live" data-wtt-live="{e(ev["wtt_id"])}" hidden>'
                    f'<div id="stream" class="hub-stream" data-stream-q="{e(ev.get("stream_q") or ev["city"] + " " + ev["year"])}" hidden></div>'
                    '<h2 class="section-title"><span class="lv-dot"></span>Live scores</h2><div class="lv-now"></div>'
                    '<h3 class="lv-sub">Latest results</h3><div class="lv-done lv-grid"></div><p class="small lv-note"></p></section>')
    results = f'<section class="hub-sec" id="results"><h2 class="section-title">{"Key results" if live_sec else "Results"}</h2>{board}</section>' if matches else ""
    draw = components.draw(ev.get("draw"))
    draw = f'<section class="hub-sec" id="draw">{draw}</section>' if draw else ""
    vids, vseen = [], set()
    for it, *_ in items:
        for v in it.get("videos") or []:
            if v["id"] not in vseen:
                vseen.add(v["id"])
                vids.append(v)
    watch = f'<section class="hub-sec" id="watch">{components.videos(vids)}</section>' if vids else ""
    stories = "".join(f'''<li class="archive-item"><a href="{e(url)}"><h3>{e(it.get("title") or it.get("headline"))}</h3>
<p>{e(it.get("standfirst") or it.get("summary", ""))}</p><time>{e(byline)}</time></a></li>''' for it, url, pub, byline in items)
    news_sec = f'<section class="hub-sec" id="news"><h2 class="section-title">News</h2><ul class="archive">{stories}</ul></section>' if items else ""
    fixtures = _fixtures(ev, schedule)
    empty = "" if (results or draw or fixtures or items) else '<p class="hub-empty">The draw, schedule and news will appear here as the event approaches.</p>'
    jump = "".join(f'<a href="#{k}">{v}</a>' for k, v, sec in (("live", "Live", live_sec), ("results", "Results", results), ("draw", "Draw", draw), ("schedule", "Schedule", fixtures),
                                                                ("watch", "Watch", watch), ("news", "News", news_sec)) if sec)
    facts = "".join(f"<dt>{k}</dt><dd>{e(v)}</dd>" for k, v in (("Dates", dates(ev)), ("Venue", place), ("Events", ev["events"]),
                                                                   ("Level", TIER_NAMES.get(ev["tier"], ""))) if v)
    body = f"""<main class="wrap hub">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/events/">Events</a> / {e(ev["group"])}</nav>
{hero}
<header class="hub-head" style="--tier:{TIERS.get(ev["tier"], "#17202b")}">
  <div><p class="hub-kicker">{pill}<span>{e(ev["group"])}</span></p>
  <h1>{e(ev["name"])} {e(ev["year"])}</h1>
  <p class="hub-meta">{e(dates(ev))}<span aria-hidden="true"> · </span>{e(place)}</p></div>
  <div class="hub-actions">{live}{cal}</div>
</header>
{f'<nav class="hub-jump" aria-label="On this page">{jump}</nav>' if jump else ""}
<div class="hub-grid"><div class="hub-main">
{empty}{live_sec}{results}{draw}{fixtures}{watch}{news_sec}
</div>
<aside class="article-side">
  <section class="panel hub-facts"><h2 class="panel-title">Event guide</h2><dl>{facts}</dl></section>
  <div class="ad ad-side" data-ad="sidebar"></div>
  <section class="panel"><h2 class="panel-title">Coming up</h2><ul id="events" class="events" data-count="5"></ul>
    <a class="panel-link" href="/events/">All events</a></section>
</aside></div>
</main>
{components.SCRIPT if (vids or ev.get("draw")) else ""}
{'<script src="/live.js" defer></script>' if live_sec else ""}"""
    return body


TIERS = {"world": "#d4213d", "smash": "#f37021", "champions": "#3a66e0", "continental": "#12917a", "star": "#2aa198", "contender": "#6b7586", "club": "#23895c"}


def index_page(data, today):
    sections = []
    groups = data.get("groups", ["WTT Series", "Majors", "Continental"])
    for key, title in (("now", "On now"), ("next", "Coming up"), ("past", "Recent")):
        evs = [ev for ev in data["events"] if status(ev, today) == key]
        evs.sort(key=lambda ev: (ev.get("start") or ev.get("end")), reverse=(key == "past"))
        if not evs:
            continue
        cards = "".join(f'''<li class="ev-card"><a href="/events/{ev["id"]}.html">
{f'<img src="{poster(ev)}" alt="" loading="lazy" width="1600" height="900">' if poster(ev) else ""}
<span class="ev-group" style="--tier:{TIERS.get(ev["tier"], "#17202b")}">{e(ev["group"])}</span>
<h3>{e(ev["name"])} {e(ev["year"])}</h3><p>{e(dates(ev))}, {e(ev["city"])}</p></a></li>''' for ev in evs)
        sections.append(f'<section class="hub-sec"><h2 class="section-title">{title}</h2><ul class="ev-cards">{cards}</ul></section>')
    filt = "".join(f'<button data-g="{e(g)}" aria-pressed="false">{e(g)}</button>' for g in groups)
    return f"""<main class="wrap">
<section class="sched-head"><div><h1>Events</h1><p class="lede">The major tournaments: draws, results, schedules and news in one place.</p></div></section>
<div class="toggle sched-filter ev-filter" role="group" aria-label="Filter events"><button data-g="" aria-pressed="true">All</button>{filt}</div>
{"".join(sections)}
<p class="small">The full calendar, including club competitions, is on the <a href="/schedule.html">schedule</a>.</p>
</main>
<script>
document.querySelector(".ev-filter").addEventListener("click", (ev) => {{
  const b = ev.target.closest("button"); if (!b) return;
  document.querySelectorAll(".ev-filter button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  document.querySelectorAll(".ev-card").forEach((c) => {{ c.hidden = !!b.dataset.g && c.querySelector(".ev-group").textContent !== b.dataset.g; }});
  document.querySelectorAll(".ev-cards").forEach((l) => {{ l.closest("section").hidden = ![...l.children].some((c) => !c.hidden); }});
}});
</script>"""
