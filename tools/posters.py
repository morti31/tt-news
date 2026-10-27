"""Eleven's own event posters: a consistent, professional identity for each tournament.

These are Eleven's designs, not imitations of any organiser's branding: Eleven's typeface, the
prestige-tier colours used on the schedule, and abstract table tennis geometry. The event's name
appears as plain text, which is fine; organisers' logos, marks and livery are never used.

Usage: python3 tools/posters.py [event id ...]   (renders img/posters/<event id>.jpg for events in data/events.json)
"""
import datetime as dt
import html, json, os

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W, H = 1600, 900
FONT = "'Bricolage Grotesque', 'Arial Narrow', sans-serif"
CAP = 0.385  # average advance of a heavy condensed capital, in em

# Colour by competition level, matching the schedule's prestige tiers: (main, deep)
TIERS = {
    "world": ("#d4213d", "#5c0716"),
    "smash": ("#f37021", "#5e2205"),
    "champions": ("#3a66e0", "#0c1a45"),
    "continental": ("#12917a", "#032b24"),
    "star": ("#2aa198", "#073532"),
    "contender": ("#6b7586", "#1a1e26"),
    "club": ("#23895c", "#06291b"),
}


def t(text, x, y, size, fill="#fff", weight=600, anchor="start", track=0, stretch=100, opacity=1, upper=False, extra=""):
    text = text.upper() if upper else text
    fs = f"font-stretch:{stretch}%;font-variation-settings:'wdth' {stretch}" if stretch != 100 else ""
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-family="{FONT}" font-size="{size:.0f}" font-weight="{weight}" '
            f'letter-spacing="{track}em" fill="{fill}" fill-opacity="{opacity}" text-anchor="{anchor}" style="{fs}" {extra}>{e(text)}</text>')


def label(text, x, y, fill="#fff", size=17, anchor="start", opacity=.72):
    return t(text, x, y, size, fill, 600, anchor, 0.2, opacity=opacity, upper=True)


def fit(text, width, cap, track=0.0):
    return min(cap, width / (len(text) * (CAP + track)))


def wordmark(x, y, fill="#fff", size=26, anchor="end"):
    return t("Eleven", x, y, size, fill, 800, anchor, -0.01)


def grain(uid, opacity=.07, dark=False):
    v = "0" if dark else "1"
    return (f'<filter id="{uid}-n" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/>'
            f'<feColorMatrix values="0 0 0 0 {v} 0 0 0 0 {v} 0 0 0 0 {v} 0 0 0 1.2 -.35"/></filter>',
            f'<rect width="{W}" height="{H}" filter="url(#{uid}-n)" opacity="{opacity}"/>')


def place(ev):
    return ev.get("venue") or f'{ev["city"]}, {ev["country"]}'


def days(ev):
    if not ev.get("start"):
        return []
    a, b = (dt.date.fromisoformat(ev[k]) for k in ("start", "end"))
    return [a + dt.timedelta(n) for n in range((b - a).days + 1)]


def date_range(ev):
    if ev.get("dates_text"):
        return ev["dates_text"]
    a, b = (dt.date.fromisoformat(ev[k]) for k in ("start", "end"))
    if a.month == b.month:
        return f"{a.day} to {b.day} {b:%b %Y}"
    return f"{a.day} {a:%b} to {b.day} {b:%b %Y}"


# Continental championships take the colour of their continent, so Lima and Tashkent never match
REGIONS = {
    "Asia": ("#12917a", "#032b24"),
    "Americas": ("#7a3cf0", "#1c0b46"),
    "Europe": ("#0a84c4", "#04263b"),
    "Africa": ("#d98a00", "#3a2200"),
    "Oceania": ("#00a39b", "#00302e"),
}
# Flashes of colour: several accent pairs per colour, rotated so neighbouring posters differ
ACCENTS = {
    "#d4213d": [("#ffb81c", "#ff5a1f"), ("#2f6bff", "#ffb81c"), ("#ff4f9a", "#ffd23f")],
    "#f37021": [("#ff2d7a", "#7b2ff7"), ("#ffd23f", "#ff2d7a"), ("#2f6bff", "#ff2d7a")],
    "#3a66e0": [("#ff5a1f", "#ffb81c"), ("#ff4f9a", "#ff8a00"), ("#d9f03c", "#22c3a6")],
    "#12917a": [("#ffb81c", "#ff4f7b"), ("#ff6a1f", "#ffd23f"), ("#c7f03c", "#2fb4ff")],
    "#7a3cf0": [("#ff8a00", "#ff2d7a"), ("#d9f03c", "#ff8a00"), ("#2fe0c8", "#ffd23f")],
    "#0a84c4": [("#ffd23f", "#ff5a1f"), ("#ff4f9a", "#ffd23f"), ("#c7f03c", "#ff8a00")],
    "#d98a00": [("#ff2d55", "#7b2ff7"), ("#2f6bff", "#ff2d55"), ("#12c2a0", "#ff2d55")],
    "#00a39b": [("#ff8a00", "#ffd23f"), ("#ff4f9a", "#ff8a00"), ("#2f6bff", "#ffd23f")],
    "#2aa198": [("#ff7a00", "#d9f03c"), ("#ff4f9a", "#ffd23f"), ("#2f6bff", "#ff7a00")],
    "#6b7586": [("#3ad1c0", "#ff5a1f"), ("#ffd23f", "#ff4f9a"), ("#c7f03c", "#2fb4ff")],
    "#23895c": [("#f2c230", "#ff5a1f"), ("#ff4f9a", "#ffd23f"), ("#2fb4ff", "#f2c230")],
}
# Licensed photos (Unsplash Licence); align is the crop focus inside the panel
PHOTOS = {
    "arena-hall.jpg": ("ARTO SURAJ", "https://unsplash.com/photos/empty-indoor-sports-arena-with-spectator-seating-_XlTp6nHbm0", "xMidYMin"),
    "seats-rows.jpg": ("Reed Mok", "https://unsplash.com/photos/teal-and-blue-chair-landscape-photography-9oduzVzk8LQ", "xMidYMid"),
    "seats-dark.jpg": ("Milan Csizmadia", "https://unsplash.com/photos/black-and-white-piano-keys-WDLTwagtvSo", "xMidYMid"),
    "stadium-roof.jpg": ("Winston Tjia", "https://unsplash.com/photos/a-stadium-filled-with-lots-of-empty-seats-4gX2Jj9zDBY", "xMidYMin"),
    "arena-above.jpg": ("Tim Trad", "https://unsplash.com/photos/white-and-red-airplane-on-top-of-stadium-during-night-time-3PdOKrfzrYM", "xMidYMid"),
    "dome.jpg": ("TAKAHIRO NISHIZONO", "https://unsplash.com/photos/stadium-seats-under-metal-dome-V06_qJzPt54", "xMidYMin"),
}
LAYOUTS = 3


def palette(ev):
    if ev["tier"] == "continental" and ev.get("region") in REGIONS:
        return REGIONS[ev["region"]]
    return TIERS[ev["tier"]]


def assign_variants(events):
    """Give each event a photo, accent pair and layout so that no two posters look alike.

    Works through events in file order (new events are appended, so existing posters keep their look).
    Each candidate is scored against earlier posters: sharing a colour and a photo costs most, then
    accents and layout; reusing a photo anywhere costs a little. Explicit "photo", "accent" or
    "layout" fields on an event override the choice.
    """
    import itertools, zlib
    done = []
    for ev in events:
        c = palette(ev)[0]
        n_acc = len(ACCENTS.get(c, [("#ff5a1f", "#ffb81c")]))
        best = None
        for photo, acc, lay in itertools.product(PHOTOS, range(n_acc), range(LAYOUTS)):
            if ev.get("photo") and photo != ev["photo"] or "accent" in ev and acc != ev["accent"] or "layout" in ev and lay != ev["layout"]:
                continue
            score = 0
            for o in done:
                same = o["c"] == c
                score += (6 if same else 1) * (o["photo"] == photo) + (3 if same else 0) * (o["acc"] == acc) + (2 if same else .3) * (o["lay"] == lay)
            tie = zlib.crc32(f'{ev["id"]}{photo}{acc}{lay}'.encode()) / 2 ** 32
            if best is None or (score, tie) < best[0]:
                best = ((score, tie), photo, acc, lay)
        _, photo, acc, lay = best
        ev["_v"] = {"photo": photo, "accent": acc, "layout": lay}
        done.append({"c": c, "photo": photo, "acc": acc, "lay": lay})
    return events


def _variant(ev):
    if "_v" not in ev:
        assign_variants([ev])
    v = ev["_v"]
    c, deep = palette(ev)
    a1, a2 = ACCENTS.get(c, [("#ff5a1f", "#ffb81c")])[v["accent"]]
    return c, deep, a1, a2, v["photo"], v["layout"]


def credit(ev):
    """HTML credit line for the photo used on an event's poster."""
    name, url, _ = PHOTOS[_variant(ev)[4]]
    return (f'Poster by Eleven. Photo: <a href="{url}" rel="noopener">{e(name)}</a>, '
            f'<a href="https://unsplash.com/license" rel="noopener">Unsplash Licence</a>')


def photo_href(name):
    import base64
    path = os.path.join(ROOT, "img", "posters", "photos", name)
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()


def _rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def _photo_defs(uid, c, deep, a1, a2, box):
    d, m = _rgb(deep), _rgb(c)
    hi = [min(1, x * .45 + .62) for x in m]   # highlights: the colour lifted towards white
    duo = "".join(f'<feFunc{ch} type="table" tableValues="{d[i] * .7:.3f} {d[i]:.3f} {m[i]:.3f} {hi[i]:.3f}"/>' for i, ch in enumerate("RGB"))
    x, y, w, h = box
    return (f'<filter id="{uid}-duo" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0"/>'
            f'<feComponentTransfer>{duo}</feComponentTransfer></filter>'
            f'<clipPath id="{uid}-panel"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>'
            f'<linearGradient id="{uid}-flash" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a1}"/><stop offset="1" stop-color="{a2}"/></linearGradient>'
            f'<linearGradient id="{uid}-shade" x1="0" y1="0" x2="0" y2="1"><stop offset=".45" stop-color="{deep}" stop-opacity="0"/><stop offset="1" stop-color="{deep}" stop-opacity=".85"/></linearGradient>')


def _flashes(uid, layout, box, a1, a2):
    """The colour shapes over the photo; three arrangements so posters side by side differ."""
    x, y, w, h = box
    s = min(w, h) / 560   # scale relative to the landscape panel
    out = []
    if layout == 0:     # ball top right, arcs rising from the bottom left
        out += [f'<circle cx="{x}" cy="{y + h}" r="{300 * s:.0f}" fill="none" stroke="{a1}" stroke-width="{34 * s:.0f}"/>',
                f'<circle cx="{x}" cy="{y + h}" r="{356 * s:.0f}" fill="none" stroke="{a2}" stroke-width="{6 * s:.1f}"/>',
                f'<circle cx="{x + w - 148 * s:.0f}" cy="{y + 214 * s:.0f}" r="{118 * s:.0f}" fill="url(#{uid}-flash)"/>',
                f'<circle cx="{x + w - 148 * s:.0f}" cy="{y + 214 * s:.0f}" r="{146 * s:.0f}" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="2"/>']
    elif layout == 1:   # arcs from the top right, ball low on the left
        out += [f'<circle cx="{x + w}" cy="{y}" r="{280 * s:.0f}" fill="none" stroke="{a1}" stroke-width="{34 * s:.0f}"/>',
                f'<circle cx="{x + w}" cy="{y}" r="{336 * s:.0f}" fill="none" stroke="{a2}" stroke-width="{6 * s:.1f}"/>',
                f'<circle cx="{x + 170 * s:.0f}" cy="{y + h * .58:.0f}" r="{104 * s:.0f}" fill="url(#{uid}-flash)"/>',
                f'<circle cx="{x + 170 * s:.0f}" cy="{y + h * .58:.0f}" r="{130 * s:.0f}" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="2"/>']
    else:               # two diagonal bands crossing the panel, small ball between them
        k = h * .55
        out += [f'<polygon points="{x},{y + h * .62:.0f} {x + w},{y + h * .62 - k:.0f} {x + w},{y + h * .62 - k + 54 * s:.0f} {x},{y + h * .62 + 54 * s:.0f}" fill="{a1}"/>',
                f'<polygon points="{x},{y + h * .62 + 84 * s:.0f} {x + w},{y + h * .62 - k + 84 * s:.0f} {x + w},{y + h * .62 - k + 96 * s:.0f} {x},{y + h * .62 + 96 * s:.0f}" fill="{a2}"/>',
                f'<circle cx="{x + w * .68:.0f}" cy="{y + h * .2:.0f}" r="{66 * s:.0f}" fill="url(#{uid}-flash)"/>']
    return out


def grid(ev, uid):
    """D, Grid: paper stock and a timetable grid, beside a duotone arena photo with flashes of colour."""
    c, deep, a1, a2, photo, layout = _variant(ev)
    ink, paper, L, R, P = "#121417", "#f3f1ec", 96, 936, 1000   # P: where the photo panel starts
    defs, noise = grain(uid, .05, dark=True)
    title = ev["city"].upper()
    size = fit(title, R - L, 250, -0.005)
    box = (P, 0, W - P, H)
    b = [f'<defs>{defs}{_photo_defs(uid, c, deep, a1, a2, box)}</defs>', f'<rect width="{W}" height="{H}" fill="{paper}"/>']
    b.append(f'<g clip-path="url(#{uid}-panel)">')
    b.append(f'<image href="{photo_href(photo)}" x="{P}" y="0" width="{W - P}" height="{H}" preserveAspectRatio="{PHOTOS[photo][2]} slice" filter="url(#{uid}-duo)"/>')
    b.append(f'<rect x="{P}" y="0" width="{W - P}" height="{H}" fill="url(#{uid}-shade)"/>')
    b += _flashes(uid, layout, box, a1, a2)
    b.append("</g>")
    b.append(f'<rect x="{P}" y="0" width="10" height="{H}" fill="{a1}"/>')
    b.append(t(ev["year"], W - 64, H - 56, 168, "#fff", 300, "end", -0.03))
    b.append(t("Eleven", P + 52, 92, 26, "#fff", 800))
    if ev.get("coords"):
        b.append(label(ev["coords"], P + 52, 120, "#fff", 12, opacity=.7))
    # paper side
    b.append(f'<rect x="{L}" y="70" width="40" height="8" fill="{a1}"/><rect x="{L + 40}" y="70" width="40" height="8" fill="{c}"/>')
    b.append(label(ev["series"], L, 118, ink, 18, opacity=1))
    b.append(f'<rect x="{L}" y="138" width="{R - L}" height="2" fill="{ink}"/>')
    base = 156 + size * 0.73
    b.append(t(title, L - size * 0.02, base, size, ink, 800, track=-0.005, stretch=75))
    y = base + 40
    b.append(f'<rect x="{L}" y="{y:.0f}" width="{R - L}" height="1" fill="{ink}" fill-opacity=".35"/>')
    cols = (("Dates", date_range(ev)), ("Venue", place(ev)), ("Events", ev["events"]))
    colw = (R - L) / 3
    for i, (k, v) in enumerate(cols):
        x = L + i * colw
        b.append(label(k, x, y + 42, ink, 14, opacity=.55))
        for j, ln in enumerate(_wrap(v, 20)[:2]):
            b.append(t(ln, x, y + 76 + j * 28, 22, ink, 600))
    b += _days(ev, uid, L, R, 690, H - 64, ink)
    b.append(label("Eleven event series", L, H - 26, ink, 12, opacity=.45))
    b.append(noise)
    return b


def _wrap(v, n):
    lines = [""]
    for w_ in v.split():
        if len(lines[-1]) + len(w_) > n and lines[-1]:
            lines.append(w_)
        else:
            lines[-1] = (lines[-1] + " " + w_).strip()
    return lines


def _days(ev, uid, L, R, top, bottom, ink, big=84):
    b = [f'<rect x="{L}" y="{top}" width="{R - L}" height="1" fill="{ink}" fill-opacity=".35"/>']
    ds = days(ev)
    if not ds:
        b.append(t(date_range(ev), L, top + 110, big, ink, 300, track=-0.02))
        return b
    cw = (R - L) / len(ds)
    for i, dd in enumerate(ds):
        x = L + i * cw
        last = i == len(ds) - 1
        if last:
            b.append(f'<rect x="{x:.0f}" y="{top}" width="{cw:.0f}" height="{bottom - top}" fill="url(#{uid}-flash)"/>')
        elif i:
            b.append(f'<rect x="{x:.0f}" y="{top + 20}" width="1" height="{bottom - top - 40}" fill="{ink}" fill-opacity=".18"/>')
        b.append(label(f"{dd:%a}", x + 14, top + 36, ink, 13, opacity=.9 if last else .55))
        b.append(t(f"{dd.day:02d}", x + 10, top + 116, min(big, cw * .62), ink, 600 if last else 300, track=-0.03))
    b.append(label("Finals", L + (len(ds) - 1) * cw + 14, bottom - 18, ink, 12, opacity=.9))
    return b


TW, TH = 1000, 1000


def tile(ev, uid):
    """Square version for small slots and phones: photo and colour above, the title and dates below."""
    c, deep, a1, a2, photo, layout = _variant(ev)
    ink, paper, L, R = "#121417", "#f3f1ec", 64, TW - 64
    PH = 470
    box = (0, 0, TW, PH)
    defs, _ = grain(uid, .05, dark=True)
    title = ev["city"].upper()
    size = fit(title, R - L, 230, -0.005)
    b = [f'<defs>{defs}{_photo_defs(uid, c, deep, a1, a2, box)}</defs>', f'<rect width="{TW}" height="{TH}" fill="{paper}"/>']
    b.append(f'<g clip-path="url(#{uid}-panel)">')
    b.append(f'<image href="{photo_href(photo)}" x="0" y="0" width="{TW}" height="{PH}" preserveAspectRatio="{PHOTOS[photo][2]} slice" filter="url(#{uid}-duo)"/>')
    b.append(f'<rect x="0" y="0" width="{TW}" height="{PH}" fill="url(#{uid}-shade)"/>')
    b += _flashes(uid, layout, box, a1, a2)
    b.append("</g>")
    b.append(f'<rect x="0" y="{PH}" width="{TW}" height="10" fill="{a1}"/>')
    b.append(t(ev["year"], R, PH - 40, 150, "#fff", 300, "end", -0.03))
    b.append(label(ev["series"], L, PH + 72, ink, 24, opacity=1))
    base = PH + 92 + size * 0.73
    b.append(t(title, L - size * 0.02, base, size, ink, 800, track=-0.005, stretch=75))
    b.append(f'<rect x="{L}" y="{base + 36:.0f}" width="{R - L}" height="2" fill="{ink}"/>')
    b.append(t(date_range(ev), L, base + 96, 38, ink, 600))
    b.append(label(place(ev), L, base + 142, ink, 20, opacity=.6))
    b.append(wordmark(R, base + 144, ink, 28))
    b.append(f'<rect x="{R - 120}" y="{base + 64:.0f}" width="60" height="12" fill="{a1}"/><rect x="{R - 60}" y="{base + 64:.0f}" width="60" height="12" fill="{c}"/>')
    b.append(_)
    return b


def arena(ev, uid):
    """B, Arena: a night key visual, a lit bowl seen from the upper tier, centred monumental type."""
    c, deep = TIERS[ev["tier"]]
    defs, noise = grain(uid, .09)
    title = ev["city"].upper()
    size = fit(title, 1180, 260, 0.01)
    cx, cy = 800, 1010
    b = [f'<defs>{defs}'
         f'<radialGradient id="{uid}-spot" cx="50%" cy="-8%" r="85%"><stop offset="0" stop-color="{c}" stop-opacity=".85"/><stop offset=".45" stop-color="{deep}" stop-opacity=".9"/><stop offset="1" stop-color="#05070a"/></radialGradient>'
         f'<linearGradient id="{uid}-type" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#d9deea"/></linearGradient>'
         f'<radialGradient id="{uid}-ball" cx="38%" cy="32%" r="70%"><stop offset="0" stop-color="#fff"/><stop offset=".7" stop-color="#e9ecf2"/><stop offset="1" stop-color="#9aa3b4"/></radialGradient>'
         f'<filter id="{uid}-glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="14"/></filter>'
         f'<linearGradient id="{uid}-arc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c}" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>'
         f'</defs>',
         f'<rect width="{W}" height="{H}" fill="url(#{uid}-spot)"/>']
    for i, rx in enumerate(range(1500, 300, -130)):
        b.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{rx * .34:.0f}" fill="none" stroke="#fff" stroke-opacity="{.05 + i * .012:.3f}" stroke-width="1.5"/>')
    # one tier lit, ending in the ball
    rx, ry = 1110, 1110 * .34
    b.append(f'<path d="M{cx - rx} {cy} A{rx} {ry:.0f} 0 0 1 {cx + rx * .62:.0f} {cy - ry * .785:.0f}" fill="none" stroke="url(#{uid}-arc)" stroke-width="3"/>')
    bx, by = cx + rx * .62, cy - ry * .785
    b.append(f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="30" fill="#fff" opacity=".55" filter="url(#{uid}-glow)"/>')
    b.append(f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="15" fill="url(#{uid}-ball)"/>')
    b.append(wordmark(96, 86, "#fff", 24, "start"))
    if ev.get("coords"):
        b.append(label(ev["coords"], W - 96, 84, "#fff", 14, "end", .5))
    b.append(f'<rect x="{800 - 150}" y="250" width="40" height="2" fill="{c}"/><rect x="{800 + 110}" y="250" width="40" height="2" fill="{c}"/>')
    b.append(label(ev["series"], 800, 257, "#fff", 18, "middle", .9))
    b.append(t(title, 800, 300 + size * 0.73, size, f"url(#{uid}-type)", 800, "middle", 0.01, 75))
    b.append(t(ev["year"], 800, 300 + size * 0.73 + 74, 30, "#fff", 300, "middle", 0.6, opacity=.85))
    info = (date_range(ev), place(ev), ev["events"])
    xs = (800 - 440, 800, 800 + 440)
    for x, v in zip(xs, info):
        b.append(label(v, x, 812, "#fff", 15, "middle", .78))
    for x in (800 - 220, 800 + 220):
        b.append(f'<rect x="{x}" y="794" width="1" height="24" fill="#fff" fill-opacity=".3"/>')
    b.append(noise)
    return b


def court(ev, uid):
    """C, Court: the table in hard perspective under arena light, a ball in flight, type set left."""
    c, deep = TIERS[ev["tier"]]
    defs, noise = grain(uid, .08)
    title = ev["city"].upper()
    size = fit(title, 640, 230)
    # table corners: near left, near right (off canvas), far right, far left
    nl, nr, fr, fl = (860, 960), (2050, 960), (1500, 250), (1080, 250)
    def lerp(p, q, k): return (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k)
    k = 0.58  # net position in screen space (perspective puts it beyond halfway)
    ml, mr = lerp(nl, fl, k), lerp(nr, fr, k)
    cn, cf = lerp(nl, nr, .5), lerp(fl, fr, .5)
    b = [f'<defs>{defs}'
         f'<linearGradient id="{uid}-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{deep}"/><stop offset=".65" stop-color="{deep}"/><stop offset="1" stop-color="{c}" stop-opacity=".9"/></linearGradient>'
         f'<radialGradient id="{uid}-light" cx="78%" cy="20%" r="60%"><stop offset="0" stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
         f'<linearGradient id="{uid}-top" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{c}"/><stop offset="1" stop-color="{c}" stop-opacity=".55"/></linearGradient>'
         f'<linearGradient id="{uid}-trail" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".9"/></linearGradient>'
         f'<radialGradient id="{uid}-ball" cx="38%" cy="32%" r="70%"><stop offset="0" stop-color="#fff"/><stop offset=".7" stop-color="#eef0f4"/><stop offset="1" stop-color="#a3abba"/></radialGradient>'
         f'<filter id="{uid}-soft"><feGaussianBlur stdDeviation="8"/></filter>'
         f'</defs>',
         f'<rect width="{W}" height="{H}" fill="url(#{uid}-bg)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#{uid}-light)"/>']
    pts = lambda *ps: " ".join(f"{x:.0f},{y:.0f}" for x, y in ps)
    b.append(f'<polygon points="{pts(nl, nr, fr, fl)}" fill="url(#{uid}-top)"/>')
    b.append(f'<polygon points="{pts(nl, nr, fr, fl)}" fill="none" stroke="#fff" stroke-width="3" stroke-opacity=".95"/>')
    b.append(f'<line x1="{cn[0]:.0f}" y1="{cn[1]:.0f}" x2="{cf[0]:.0f}" y2="{cf[1]:.0f}" stroke="#fff" stroke-width="1.5" stroke-opacity=".8"/>')
    # net: a dark mesh band with a white tape
    b.append(f'<polygon points="{pts(ml, mr, (mr[0], mr[1] - 46), (ml[0], ml[1] - 34))}" fill="#05070a" fill-opacity=".55"/>')
    b.append(f'<line x1="{ml[0]:.0f}" y1="{ml[1] - 34:.0f}" x2="{mr[0]:.0f}" y2="{mr[1] - 46:.0f}" stroke="#fff" stroke-width="3"/>')
    # ball, its shadow and flight
    bx, by = 1300, 330
    b.append(f'<ellipse cx="{bx + 30}" cy="{by + 240}" rx="26" ry="8" fill="#000" opacity=".35" filter="url(#{uid}-soft)"/>')
    b.append(f'<path d="M{bx - 330} {by + 250} Q {bx - 150} {by - 40} {bx - 4} {by - 8} L {bx + 4} {by + 10} Q {bx - 150} {by + 10} {bx - 330} {by + 250} Z" fill="url(#{uid}-trail)" opacity=".5"/>')
    b.append(f'<circle cx="{bx}" cy="{by}" r="17" fill="url(#{uid}-ball)"/>')
    L = 96
    b.append(f'<rect x="{L}" y="104" width="44" height="3" fill="{c}"/>')
    b.append(label(ev["series"], L, 152, "#fff", 18, opacity=.9))
    base = 170 + size * 0.73
    b.append(t(title, L - size * 0.02, base, size, "#fff", 800, stretch=75))
    b.append(t(ev["year"], L, base + 96, 84, "#fff", 200, track=-0.02, opacity=.9))
    rows = (("Dates", date_range(ev)), ("Venue", place(ev)), ("Events", ev["events"]))
    for i, (k, v) in enumerate(rows):
        y = 640 + i * 66
        b.append(f'<rect x="{L}" y="{y}" width="600" height="1" fill="#fff" fill-opacity=".22"/>')
        b.append(label(k, L, y + 40, "#fff", 14, opacity=.55))
        b.append(t(v, L + 150, y + 41, 22, "#fff", 600))
    b.append(wordmark(W - 96, 88, "#fff", 24))
    b.append(noise)
    return b


STYLES = {"grid": grid, "arena": arena, "court": court, "tile": tile}


def svg(ev, style):
    uid = f'{ev["id"]}-{style}'
    body = "\n".join(STYLES[style](ev, uid))
    lbl = f'{ev["series"]} {ev["city"]} {ev["year"]} poster by Eleven'
    w, h = (TW, TH) if style == "tile" else (W, H)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{e(lbl)}">\n{body}\n</svg>\n'


def main(only=None):
    """Render every hub event's posters: img/posters/<id>.jpg (16:9) and <id>-sq.jpg (square, for phones and small slots).
    Needs Playwright, so run it locally or in an update run, not at deploy."""
    data = json.load(open(os.path.join(ROOT, "data", "events.json"), encoding="utf-8"))
    assign_variants(data["events"])
    out = os.path.join(ROOT, "img", "posters")
    os.makedirs(out, exist_ok=True)
    font = os.path.join(ROOT, "tools", "BricolageGrotesque-variable.woff2")
    import base64
    b64 = base64.b64encode(open(font, "rb").read()).decode()
    css = (f"@font-face{{font-family:'Bricolage Grotesque';src:url(data:font/woff2;base64,{b64}) format('woff2');font-weight:200 800;font-stretch:75% 100%}}"
           "html,body{margin:0;background:#000}svg{display:block}")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": W, "height": H})
        for ev in data["events"]:
            if only and ev["id"] not in only:
                continue
            for style, suffix, (w, h) in ((ev.get("style", data.get("style", "grid")), "", (W, H)), ("tile", "-sq", (TW, TH))):
                pg.set_viewport_size({"width": w, "height": h})
                pg.set_content(f"<html><head><style>{css} svg{{width:{w}px;height:{h}px}}</style></head><body>{svg(ev, style)}</body></html>")
                pg.evaluate("document.fonts.ready.then(() => document.fonts.size)")
                pg.wait_for_timeout(300)
                pg.screenshot(path=os.path.join(out, f'{ev["id"]}{suffix}.jpg'), type="jpeg", quality=84)
            print("poster:", ev["id"], ev["_v"])
        browser.close()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:] or None)
