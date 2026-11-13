"""Event hub pages: one page per major tournament, plus the events index.

Called from build_site.py. Input: data/events.json (hub events and poster details), data/schedule.json
(fixtures), data/news.json and data/articles/*.json (stories and articles with "event": "<hub id>").
Output: events/<id>.html, events/<id>.ics, events/index.html, data/event-index.json.
"""
import json, os, datetime as dt, html
import components
import match_centre
import posters

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TIER_NAMES = {"world": "World event", "smash": "Grand Smash", "champions": "WTT Champions level", "continental": "Continental championships",
              "star": "WTT Star Contender", "contender": "WTT Contender", "club": "Club competition"}


# Events without the top players: off the homepage's "Major events" row, and no champions panel under the top stories
MINOR = {"WTT Feeder", "WTT Contender"}


def load():
    path = os.path.join(ROOT, "data", "events.json")
    data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {"events": []}
    posters.assign_variants(data["events"])   # same photo and colour choices as the rendered posters
    return data


def credit(ev):
    return posters.credit(ev)


def _v(p):
    """/<p>?v=<content hash>: a re-rendered poster gets a new address, so browsers and the CDN never show an old one."""
    import hashlib
    return f"/{p}?v={hashlib.md5(open(os.path.join(ROOT, p), 'rb').read()).hexdigest()[:8]}"


def tile(ev):
    p = f"img/posters/{ev['id']}-sq.jpg"
    return _v(p) if os.path.exists(os.path.join(ROOT, p)) else None


def picture(ev, alt, link=None):
    """The poster as a responsive image: the square version on phones, the wide one elsewhere."""
    sq = tile(ev)
    src = f'<source media="(max-width: 600px)" srcset="{sq}" width="1000" height="1000">' if sq else ""
    img = f'<picture>{src}<img src="{poster(ev)}" alt="{e(alt)}" width="1600" height="900"></picture>'
    return f'<a href="{link}">{img}</a>' if link else img


def poster(ev):
    p = f"img/posters/{ev['id']}.jpg"
    return _v(p) if os.path.exists(os.path.join(ROOT, p)) else None


def dates(ev):
    if ev.get("dates_text") or not ev.get("start"):
        return ev.get("dates_text", "")
    a, b = dt.date.fromisoformat(ev["start"]), dt.date.fromisoformat(ev["end"])
    if a == b:
        return f"{a.day} {a:%B %Y}"
    return f"{a.day} to {b.day} {b:%B %Y}" if a.month == b.month else f"{a.day} {a:%B} to {b.day} {b:%B %Y}"


def status(ev, today):
    end = ev.get("end")
    if components.champions(ev.get("draw")) and ev.get("start") and ev["start"] <= today:
        return "past"   # every final played: the tournament is over, even on the last day
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
            "wtt": ev.get("wtt_id"), "series": ev["series"], **({"minor": 1} if ev.get("series") in MINOR else {}), "city": ev["city"], "venue": ev.get("venue"), "start": ev.get("start"),
            "end": ev.get("end"), "group": ev["group"], "stream_q": ev.get("stream_q") or f'{ev["city"]} {ev["year"]}', "colour": c, "tint": bg, "tint_rule": rule, "tint_ink": ink,
            "champions": components.champions(ev.get("draw"))}


def event_index(data):
    """Hub lookup for the homepage and widgets, keyed by hub id and by schedule id. Every page loads this file, so it
    holds only what those scripts can use: events that are coming up or ended in the last 400 days."""
    out = {}
    cutoff = (dt.date.today() - dt.timedelta(days=400)).isoformat()
    recent = (dt.date.today() - dt.timedelta(days=14)).isoformat()
    for ev in data["events"]:
        if (ev.get("end") or "9999") < cutoff:
            continue
        out[ev["id"]] = index_entry(ev)
        if (ev.get("end") or "9999") < recent:
            out[ev["id"]]["champions"] = []   # only used to tell that an event on now (or just over) has finished
        if ev.get("schedule_id"):
            out[ev["schedule_id"]] = out[ev["id"]]
    return out


def _md(text):
    """Escape a paragraph and turn [words](/url) into links."""
    import re
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', e(text))


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
        rows = "".join(f'<li><time datetime="{e(f["start"])}" data-lt="hm">{_uk(f["start"]):%H:%M}</time><span>{e(_cap(f["name"].removeprefix(prefix)))}</span></li>' for f in items)
        out.append(f'<div class="fx-day"><h3>{d:%A} {d.day} {d:%B}</h3><ul class="fx-list">{rows}</ul></div>')
    return f'<section class="hub-sec" id="schedule"><h2 class="section-title">Schedule</h2><p class="small"><span data-tz-note>Times are UK time.</span> Times are approximate: sessions and matches can start late or run over. Session and match times from the organiser and published order of play.</p>{"".join(out)}</section>'


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
    where = ev["city"] if ev["city"] == ev["country"] else f'{ev["city"]}, {ev["country"]}'
    place = f'{ev["venue"]}, {where}' if ev.get("venue") else where
    live = ""
    cal = f'<a class="btn" href="/events/{ev["id"]}.ics">Add to calendar</a>' if ev.get("start") and st != "past" else ""

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
                    '<h2 class="section-title"><span class="lv-dot"></span>Live now</h2><div class="lv-now"></div><p class="small lv-note"></p></section>')
    champs = (components.champions(ev.get("draw")) or ev.get("champions") or []) if st == "past" else []
    champ_sec = ""
    if champs:
        def final_line(c):
            if c.get("walkover"):
                return f'Won the final against {e(c["runner_up"]["name"])} by walkover'
            if c.get("note") and not c["runner_up"].get("name"):
                return e(c["note"])
            if not c.get("score"):
                return f'Beat {e(c["runner_up"]["name"])} in the final'
            return f'Beat {e(c["runner_up"]["name"])} {e(c["score"])} in the final<span>{e(c["games"])}</span>'
        plural = lambda c: "s" if (" / " in c["champion"]["name"] or "team" in c["event"].lower() or "doubles" in c["event"].lower()) else ""
        cards = "".join(f'''<div class="champ"><span class="champ-ev">{e(c["event"])} champion{plural(c)}</span>
<p class="champ-name">{components.flag(c["champion"].get("nat"))}{e(c["champion"]["name"])}</p>
<p class="champ-final">{final_line(c)}</p></div>''' for c in champs)
        champ_sec = (f'<section class="hub-sec champs-sec" id="champions"><h2 class="section-title">Champions</h2>'
                     f'<div class="champs" style="--tier:{TIERS.get(ev["tier"], "#17202b")}">{cards}</div></section>')
    # How it was won: a short account of a finished event, for events Eleven did not cover day by day
    story_sec = ""
    if ev.get("story") and st == "past":
        paras = "".join(f"<p>{_md(p)}</p>" for p in ev["story"])
        story_sec = f'<section class="hub-sec hub-story" id="story"><h2 class="section-title">How it was won</h2>{paras}</section>'
    # Matches: every match by day, with times, scores and point by point (replaces the results board and schedule)
    mc = match_centre.section(ev, schedule, today) if ev.get("start") and (ev.get("wtt_id") or ev.get("draw")) else ""
    results = "" if mc else (f'<section class="hub-sec" id="results"><h2 class="section-title">Results</h2>{board}</section>' if matches else "")
    draw = components.draw(ev.get("draw"))
    draw = f'<section class="hub-sec" id="draw">{draw}</section>' if draw else ""
    vids, vseen = [], set()
    for it, *_ in items:
        for v in it.get("videos") or []:
            if v["id"] not in vseen:
                vseen.add(v["id"])
                vids.append(v)
    # Always present, so the homepage's Highlights link lands here even before the first video
    watch = (f'<section class="hub-sec" id="watch">{components.videos(vids)}</section>' if vids else "" if st == "past" else
             '<section class="hub-sec" id="watch"><h2 class="section-title">Highlights</h2><p class="hub-empty">WTT highlights will appear here as matches are played.</p></section>')
    stories = "".join(f'''<li class="archive-item"><a href="{e(url)}"><h3>{e(it.get("title") or it.get("headline"))}</h3>
<p>{e(it.get("standfirst") or it.get("summary", ""))}</p><time>{e(byline)}</time></a></li>''' for it, url, pub, byline in items)
    news_sec = f'<section class="hub-sec" id="news"><h2 class="section-title">News</h2><ul class="archive hub-news">{stories}</ul></section>' if items else ""
    fixtures = "" if mc else _fixtures(ev, schedule)
    empty = "" if (mc or results or draw or fixtures or items or champ_sec or story_sec) else '<p class="hub-empty">The draw, schedule and news will appear here as the event approaches.</p>'
    jump = "".join(f'<a href="#{k}">{v}</a>' for k, v, sec in (("champions", "Champions", champ_sec), ("story", "How it was won", story_sec), ("live", "Live", "" if mc else live_sec), ("matches", "Matches", mc), ("results", "Results", results), ("draw", "Draw", draw), ("schedule", "Schedule", fixtures),
                                                                ("watch", "Watch", watch), ("news", "News", news_sec)) if sec)
    facts = "".join(f"<dt>{k}</dt><dd>{e(v)}</dd>" for k, v in (("Dates", dates(ev)), ("Venue", place), ("Events", ev.get("events", "")),
                                                                   ("Level", ev.get("level") or TIER_NAMES.get(ev["tier"], ""))) if v)
    # The sidebar sits beside the first sections only (live scores and results, or whatever comes first);
    # the long sections (draw, schedule, highlights, news) run full width below it, so there is no
    # empty column on the right.
    order = [x for x in (champ_sec, story_sec, live_sec, mc, results, draw, fixtures, watch, news_sec) if x]
    top = [x for x in (champ_sec, story_sec, live_sec, mc, results) if x] or order[:1]
    top_html = empty + "".join(top)
    below_html = "".join(x for x in order if x not in top)
    body = f"""<main class="wrap hub">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/events/">Events</a> / {e(ev["group"])}</nav>
<div class="hub-top{" has-poster" if hero else ""}">{hero}
<header class="hub-head" style="--tier:{TIERS.get(ev["tier"], "#17202b")}">
  <div><p class="hub-kicker">{pill}<span>{e(ev["group"])}</span></p>
  <h1>{e(ev["name"])} {e(ev["year"])}</h1>
  <p class="hub-meta">{e(dates(ev))}<span aria-hidden="true"> · </span>{e(place)}</p></div>
  <div class="hub-actions">{live}{cal}</div>
</header></div>
{f'<nav class="hub-jump" aria-label="On this page">{jump}</nav>' if jump else ""}
<div class="hub-grid"><div class="hub-main">
{top_html}
</div>
<aside class="article-side">
  <section class="panel hub-facts"><h2 class="panel-title">Event guide</h2><dl>{facts}</dl></section>
  <div class="ad ad-side" data-ad="sidebar"></div>
  <section class="panel"><h2 class="panel-title">Coming up</h2><ul id="events" class="events" data-count="5"></ul>
    <a class="panel-link" href="/events/">All events</a></section>
</aside></div>
{f'<div class="hub-full">{below_html}</div>' if below_html else ""}
</main>
{components.SCRIPT if (vids or ev.get("draw") or mc) else ""}
{'<script src="/live.js" defer></script>' if (live_sec or (mc and ev.get("wtt_id"))) else ""}"""
    return body


TIERS = {"world": "#d4213d", "smash": "#f37021", "champions": "#3a66e0", "continental": "#12917a", "star": "#2aa198", "contender": "#6b7586", "club": "#23895c"}


def index_page(data, today):
    """Upcoming and Past tabs. Upcoming: on now, the next three tournaments as posters, then every later event as a slim row by
    month (majors as large black rows, 4-star events a little larger than the rest). Past: the same rows, a year at a time."""
    import poster_tiers
    groups = data.get("groups", ["WTT Series", "Majors", "Continental"])

    def short(ev):
        if not ev.get("start"):
            return ev.get("dates_text", "")
        a, b = dt.date.fromisoformat(ev["start"]), dt.date.fromisoformat(ev["end"])
        return f"{a.day} {a:%b}" if a == b else f"{a.day} {a:%b} to {b.day} {b:%b}"

    def stars(ev):
        n = poster_tiers.stars(ev)
        full = int(n)
        return (f'<span class="ev-stars" aria-label="{n:g} stars">' + "★" * full + ("<i>★</i>" if n > full else "")
                + f'<i class="off">{"★" * (5 - full - (1 if n > full else 0))}</i></span>')

    def attrs(ev):
        return f'data-g="{e(ev["group"])}" data-s="{e(ev.get("series", ""))}"'

    def label(ev):
        return ev["series"] if ev.get("series") else ev["group"]

    def row(ev):
        n = poster_tiers.stars(ev)
        size = "major" if ev["group"] == "Majors" else "big" if n >= 4 else "small"
        img = poster(ev)
        return f"""<li class="evl-row ev-{size} ev-item" {attrs(ev)}><a href="/events/{ev["id"]}.html">
{f'<img src="{img}" alt="" loading="lazy" width="1600" height="900">' if img else '<span class="ev-noimg"></span>'}
<span class="ev-txt"><span class="ev-kicker">{'<b class="ev-major">Major</b>' if size == "major" else ""}{e(label(ev))}</span>
<span class="ev-name">{e(ev["name"])}</span><span class="ev-city">{e(ev["city"])}</span></span>
<span class="ev-when">{stars(ev)}<span class="ev-dates">{e(short(ev))}</span></span></a></li>"""

    def months(evs, newest_first=False):
        out, cur = [], None
        for ev in evs:
            d = dt.date.fromisoformat(ev.get("start") or ev.get("end"))
            key = (d.year, d.month)
            if key != cur:
                if cur:
                    out.append("</ul></div>")
                cur = key
                out.append(f'<div class="ev-month"><h3 class="ev-month-h">{d:%B %Y}</h3><ul class="ev-rows">')
            out.append(row(ev))
        if cur:
            out.append("</ul></div>")
        return "".join(out)

    by_start = lambda ev: ev.get("start") or ev.get("end")
    now = sorted((ev for ev in data["events"] if status(ev, today) == "now"), key=by_start)
    nxt = sorted((ev for ev in data["events"] if status(ev, today) == "next"), key=by_start)
    past = sorted((ev for ev in data["events"] if status(ev, today) == "past"), key=by_start, reverse=True)

    on = "".join(f"""<li class="ev-now ev-item" {attrs(ev)}><a href="/events/{ev["id"]}.html">
{f'<img src="{poster(ev)}" alt="" width="1600" height="900">' if poster(ev) else ""}
<span class="ev-txt"><span class="ev-live"><span class="live-dot"></span>On now</span><span class="ev-name">{e(ev["name"])}</span>
<span class="ev-city">{e(short(ev))} · Draw, results and schedule</span></span></a></li>""" for ev in now)
    feat = "".join(f"""<li class="ev-feat ev-item{' is-major' if ev['group'] == 'Majors' else ''}" {attrs(ev)}><a href="/events/{ev["id"]}.html">
{f'<img src="{poster(ev)}" alt="" width="1600" height="900">' if poster(ev) else ""}
<span class="ev-txt">{stars(ev)}<span class="ev-name">{e(ev["name"])}</span><span class="ev-city">{e(short(ev))} · {e(ev["city"])}</span></span></a></li>""" for ev in nxt[:3])

    upcoming = ""
    if on:
        upcoming += f'<section class="hub-sec ev-sec"><h2 class="section-title">On now</h2><ul class="ev-nows">{on}</ul></section>'
    if feat:
        upcoming += f'<section class="hub-sec ev-sec"><h2 class="section-title">Next up</h2><ul class="ev-feats">{feat}</ul></section>'
    if nxt[3:]:
        upcoming += f'<section class="hub-sec ev-sec"><h2 class="section-title">Later</h2>{months(nxt[3:])}</section>'

    years = {}
    for ev in past:
        years.setdefault(dt.date.fromisoformat(by_start(ev)).year, []).append(ev)
    year_nav = ('<nav class="hub-jump ev-years" aria-label="Years">' + "".join(f'<a href="#y{y}">{y}</a>' for y in years) + "</nav>") if len(years) > 1 else ""
    past_html = year_nav + "".join(f'<section class="hub-sec ev-year ev-sec" id="y{y}"><h2 class="section-title">{y} <span class="ev-count">{len(evs)} event{"s" if len(evs) != 1 else ""}</span></h2>{months(evs)}</section>'
                                   for y, evs in years.items())

    filt = "".join(f'<button data-g="{e(g)}" aria-pressed="false">{e(g)}</button>' for g in groups)
    order = ["WTT Grand Smash", "WTT Finals", "WTT Champions", "WTT Star Contender", "WTT Contender", "WTT Feeder"]
    present = {ev.get("series") for ev in data["events"] if ev["group"] == "WTT Series"}
    levels = "".join(f'<button data-s="{e(x)}" aria-pressed="false">{e(x.replace("WTT ", "", 1))}</button>' for x in order if x in present)
    return f"""<main class="wrap">
<section class="sched-head"><div><h1>Events</h1><p class="lede">Draws, results, schedules and news for every tournament.</p></div></section>
<div class="ev-tabs" role="tablist"><a href="#upcoming" role="tab" data-tab="upcoming" aria-selected="true">Upcoming</a><a href="#past" role="tab" data-tab="past" aria-selected="false">Past events</a></div>
<div class="toggle sched-filter ev-filter" role="group" aria-label="Filter events"><button data-g="" aria-pressed="true">All</button>{filt}</div>
<div class="toggle sched-filter ev-levels" role="group" aria-label="Filter WTT events by level" hidden><button data-s="" aria-pressed="true">All WTT</button>{levels}</div>
<div class="ev-panel" id="upcoming">{upcoming}</div>
<div class="ev-panel" id="past" hidden>{past_html}<p class="hub-empty ev-none" hidden>No events of this kind that year.</p></div>
<p class="hub-empty ev-none-up" hidden>No upcoming events of this kind yet.</p>
<p class="small">The full calendar, including club competitions, is on the <a href="/schedule.html">schedule</a>.</p>
</main>
<script>
let G = "", S = "", Y = "", T = "upcoming";
const levels = document.querySelector(".ev-levels");
const years = [...document.querySelectorAll(".ev-year")], ytabs = [...document.querySelectorAll(".ev-years a")];
function fromHash() {{
  const h = location.hash.slice(1);
  if (h === "past" || years.some((s) => s.id === h)) T = "past"; else if (h === "upcoming" || !h) T = "upcoming";
  if (years.some((s) => s.id === h)) Y = h;
  if (!Y && years[0]) Y = years[0].id;
}}
function apply() {{
  document.querySelectorAll(".ev-tabs a").forEach((a) => a.setAttribute("aria-selected", String(a.dataset.tab === T)));
  document.getElementById("upcoming").hidden = T !== "upcoming";
  document.getElementById("past").hidden = T !== "past";
  levels.hidden = G !== "WTT Series";
  document.querySelectorAll(".ev-filter button").forEach((x) => x.setAttribute("aria-pressed", String(x.dataset.g === G)));
  levels.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x.dataset.s === S)));
  document.querySelectorAll(".ev-item").forEach((c) => {{ c.hidden = (!!G && c.dataset.g !== G) || (!!S && c.dataset.s !== S); }});
  document.querySelectorAll(".ev-month").forEach((m) => {{ m.hidden = ![...m.querySelectorAll(".ev-item")].some((c) => !c.hidden); }});
  document.querySelectorAll("#upcoming .ev-sec").forEach((s) => {{ s.hidden = ![...s.querySelectorAll(".ev-item")].some((c) => !c.hidden); }});
  document.querySelector(".ev-none-up").hidden = T !== "upcoming" || [...document.querySelectorAll("#upcoming .ev-item")].some((c) => !c.hidden);
  let any = true;
  years.forEach((sec) => {{
    const has = [...sec.querySelectorAll(".ev-month")].some((m) => !m.hidden);
    sec.hidden = !has || (ytabs.length > 0 && sec.id !== Y);
    if (sec.id === Y) any = has;
    const tab = ytabs.find((a) => a.getAttribute("href") === "#" + sec.id);
    if (tab) {{ tab.setAttribute("aria-selected", String(sec.id === Y)); tab.classList.toggle("none", !has); }}
  }});
  document.querySelector(".ev-none").hidden = any;
}}
document.querySelectorAll(".ev-tabs a").forEach((a) => a.addEventListener("click", (ev) => {{
  ev.preventDefault(); T = a.dataset.tab; history.replaceState(null, "", "#" + T); apply();
}}));
ytabs.forEach((a) => a.addEventListener("click", (ev) => {{
  ev.preventDefault(); Y = a.getAttribute("href").slice(1); history.replaceState(null, "", "#" + Y); apply();
}}));
window.addEventListener("hashchange", () => {{ fromHash(); apply(); }});
fromHash(); apply();
document.querySelector(".ev-filter").addEventListener("click", (ev) => {{
  const b = ev.target.closest("button"); if (!b) return;
  G = b.dataset.g; S = ""; apply();
}});
levels.addEventListener("click", (ev) => {{
  const b = ev.target.closest("button"); if (!b) return;
  S = b.dataset.s; apply();
}});
</script>"""
