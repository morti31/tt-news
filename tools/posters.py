"""Eleven's own event posters: a consistent, professional identity for each tournament.

These are Eleven's designs, not imitations of any organiser's branding: Eleven's typeface, the
prestige-tier colours used on the schedule, and abstract table tennis geometry. The event's name
appears as plain text, which is fine; organisers' logos, marks and livery are never used.

Usage: python3 tools/posters.py [event id ...]   (renders img/posters/<event id>.jpg for events in data/events.json)
       python3 tools/posters.py --need           exit 0 if some event has no poster yet (used by the WTT sync workflow)
       python3 tools/posters.py --missing        render only the events that have no poster yet
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
    "hall-lights.jpg": ("ARTO SURAJ", "https://unsplash.com/photos/empty-indoor-sports-arena-with-spectator-seating-_XlTp6nHbm0", "xMidYMid"),
    "seats-rows.jpg": ("Reed Mok", "https://unsplash.com/photos/teal-and-blue-chair-landscape-photography-9oduzVzk8LQ", "xMidYMid"),
    "seats-blue.jpg": ("Reed Mok", "https://unsplash.com/photos/teal-and-blue-chair-landscape-photography-9oduzVzk8LQ", "xMidYMid"),
    "seats-dark.jpg": ("Milan Csizmadia", "https://unsplash.com/photos/black-and-white-piano-keys-WDLTwagtvSo", "xMidYMid"),
    "stadium-seats.jpg": ("Winston Tjia", "https://unsplash.com/photos/a-stadium-filled-with-lots-of-empty-seats-4gX2Jj9zDBY", "xMidYMid"),
    "dome-seats.jpg": ("TAKAHIRO NISHIZONO", "https://unsplash.com/photos/stadium-seats-under-metal-dome-V06_qJzPt54", "xMidYMid"),
}
# Photos are close crops of seating, lights or stands: never a whole stadium, so no poster
# suggests a venue the event isn't played in
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
    """HTML credit line for the photo used on an event's poster (posters with no photo say so)."""
    if look(ev) in ("arena", "court", "ticket", "atlas"):
        return "Poster by Eleven."
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
    cols = ev.get("cols") or (("Dates", date_range(ev)), ("Venue", place(ev)), ("Events", ev["events"]))
    colw = (R - L) / 3
    for i, (k, v) in enumerate(cols):
        x = L + i * colw
        b.append(label(k, x, y + 42, ink, 14, opacity=.55))
        for j, ln in enumerate(_wrap(v, 20)[:2]):
            b.append(t(ln, x, y + 76 + j * 28, 22, ink, 600))
    if ev.get("strap"):     # leagues and news topics: a line of text where an event has its days
        b.append(f'<rect x="{L}" y="690" width="{R - L}" height="1" fill="{ink}" fill-opacity=".35"/>')
        b.append(t(ev["strap"], L, 800, fit(ev["strap"], R - L, 84, -0.02), ink, 300, track=-0.02))
    else:
        b += _days(ev, uid, L, R, 690, H - 64, ink)
    b.append(label("Eleven event series" if not ev.get("strap") else "Eleven", L, H - 26, ink, 12, opacity=.45))
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
    base = PH + 112 + size * 0.73
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
    c, deep = colours(ev)
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
    c, deep = colours(ev)
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




# ---------------------------------------------------------------------------------------------------------------
# One look per kind of event (agreed 11 November 2026). Every look keeps Eleven's branding: the wordmark, Bricolage
# Grotesque, the small two-colour bar, upper-case spaced labels and a fine grain. What changes is the composition.
#   World events (Worlds, Olympics, World Cup)    grid       paper and a duotone arena photo (the original)
#   Grand Smash                                   arena      night bowl, monumental centred type
#   WTT Champions, WTT Finals                     court      the table in perspective, type set left
#   Star Contender                                split      a tall photo strip beside a solid colour field
#   Contender and Feeder                          ticket     typographic, paper stock, a ticket with a stub
#   Continental championships and Games           atlas      the region's colour with a graticule and a located dot
#   Club leagues                                  landmark   the country's landmark, full bleed, in the league's colour
#   World rankings                                ladder     the ranking as bars
#   News topics                                   bulletin   ink, a bold word, the ball
# ---------------------------------------------------------------------------------------------------------------

LANDMARKS = {   # Unsplash Licence; credit: (photographer, page)
    "berlin-brandenburg-gate.jpg": ("Maximilian Brol", "https://unsplash.com/photos/brandenburg-gate-in-berlin-A9dp22dRULI", "Brandenburg Gate, Berlin"),
    "tokyo-tower.jpg": ("ZHENYU LUO", "https://unsplash.com/photos/tokyo-tower-glows-brightly-among-city-buildings-xpburpKFWUs", "Tokyo Tower"),
    "paris-eiffel-tower.jpg": ("Chris Karidis", "https://unsplash.com/photos/eiffel-tower-paris-france-nnzkZNYWHaU", "Eiffel Tower, Paris"),
    "beijing-temple-of-heaven.jpg": ("Charles Gao", "https://unsplash.com/photos/brown-and-gray-roof-house-xagzUq7d4q4", "Temple of Heaven, Beijing"),
    "new-york-statue-of-liberty.jpg": ("Brandon Mowinkel", "https://unsplash.com/photos/UGi_Ng56FRI", "Statue of Liberty, New York"),
    "mumbai-gateway-of-india.jpg": ("Daniel Dara", "https://unsplash.com/photos/a-large-stone-building-with-gateway-of-india-in-the-background-Ub8Z0UsaWIw", "Gateway of India, Mumbai"),
    "brussels-atomium.jpg": ("Cosmin Serban", "https://unsplash.com/photos/atomium-brussels-belgium-JAEog_jEAo0", "Atomium, Brussels"),
    "london-big-ben.jpg": ("Tom Athawes", "https://unsplash.com/photos/big-ben-in-london-Wb6smx3Z9uI", "Elizabeth Tower, London"),
}
LEAGUE_LANDMARK = {"bundesliga": "berlin-brandenburg-gate.jpg", "t-league": "tokyo-tower.jpg", "pro-a": "paris-eiffel-tower.jpg",
                   "super-league": "beijing-temple-of-heaven.jpg", "mltt": "new-york-statue-of-liberty.jpg", "utt": "mumbai-gateway-of-india.jpg",
                   "champions-league": "brussels-atomium.jpg"}
# Palettes for kinds of event that share a tier: (main, deep)
SERIES_COLOURS = {"WTT Finals": ("#c99a2e", "#1b1405"), "WTT Feeder": ("#e2582b", "#2a0f05"), "WTT Invitational": ("#3a66e0", "#0c1a45")}


def tiered(ev):
    """2026 onwards: the star-rated posters (tools/poster_tiers.py). Earlier events keep their original posters."""
    y = str(ev.get("year") or "")
    return y.isdigit() and int(y) >= 2026 and ev.get("tier") != "club"


def look(ev):
    """Which composition an event (or a league or topic poster) gets."""
    if ev.get("look"):
        return ev["look"]
    if tiered(ev):
        return {3: "three", 4: "four", 4.5: "five_vermilion", 5: "five_lacquer"}.get(poster_tiers.stars(ev), "ticket")
    s, tier = ev.get("series", ""), ev.get("tier")
    if tier == "smash":
        return "arena"
    if tier == "champions":
        return "court"
    if tier == "star":
        return "split"
    if tier == "contender":
        return "ticket"
    if tier == "continental":
        return "atlas"
    return "grid"


# 2026 onwards: Feeders are always grey, the Finals always gold, 5-star events always the lacquer look; Contenders,
# Star Contenders, Champions and continental events take turns through these, so a series never repeats back to back
ROTATION = [("#3a66e0", "#0c1a45"), ("#2aa198", "#073532"), ("#7a3cf0", "#1c0b46"), ("#d4213d", "#5c0716"),
            ("#d98a00", "#3a2200"), ("#c2337a", "#3d0a24"), ("#e2582b", "#2a0f05"), ("#4f7a2a", "#16210b")]
FEEDER_GREY = ("#6b7586", "#1a1e26")
_ROT = {}


def rotation_colour(ev):
    if not _ROT:
        evs = json.load(open(os.path.join(ROOT, "data", "events.json"), encoding="utf-8"))["events"]
        groups = {}
        for x in sorted((x for x in evs if tiered(x)), key=lambda x: (x.get("start") or "", x["id"])):
            k = x.get("tier") if x.get("tier") in ("contender", "star", "champions", "continental") else None
            if k:
                groups.setdefault(k, []).append(x["id"])
        for k, ids in groups.items():
            off = {"contender": 0, "star": 3, "champions": 5, "continental": 6}[k]
            for i, xid in enumerate(ids):
                _ROT[xid] = ROTATION[(i * 3 + off) % len(ROTATION)]   # step 3: neighbours differ strongly
    return _ROT.get(ev["id"], ROTATION[sum(map(ord, ev["id"])) % len(ROTATION)])


def colours(ev):
    if tiered(ev) and ev.get("tier") != "club" and not ev.get("colours"):
        if ev.get("series") == "WTT Feeder":
            return FEEDER_GREY
        if ev.get("series") in SERIES_COLOURS:
            return SERIES_COLOURS[ev["series"]]
        if ev.get("tier") in ("contender", "star", "champions", "continental"):
            return rotation_colour(ev)
    if ev.get("series") in SERIES_COLOURS:
        return SERIES_COLOURS[ev["series"]]
    return palette(ev)


def landmark_href(name):
    import base64
    path = os.path.join(ROOT, "img", "posters", "photos", "landmarks", name)
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()


def _duo(uid, c, deep, key="duo", lift=.62):
    d, m = _rgb(deep), _rgb(c)
    hi = [min(1, x * .45 + lift) for x in m]
    tv = "".join(f'<feFunc{ch} type="table" tableValues="{d[i] * .7:.3f} {d[i]:.3f} {m[i]:.3f} {hi[i]:.3f}"/>' for i, ch in enumerate("RGB"))
    return f'<filter id="{uid}-{key}" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0"/><feComponentTransfer>{tv}</feComponentTransfer></filter>'


def _bars(x, y, a, b, w=40, h=8):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{a}"/><rect x="{x + w}" y="{y}" width="{w}" height="{h}" fill="{b}"/>'


def split(ev, uid):
    """Star Contender: a tall duotone photo strip on the left, a solid field of the tier colour on the right."""
    c, deep, a1, a2, photo, layout = _variant(ev)
    c, deep = colours(ev)
    defs, noise = grain(uid, .06)
    P = 620                                   # photo strip width
    L, R = P + 90, W - 90
    title = ev["city"].upper()
    size = fit(title, R - L, 230, -0.005)
    b = [f'<defs>{defs}{_duo(uid, c, deep)}<clipPath id="{uid}-strip"><rect x="0" y="0" width="{P}" height="{H}"/></clipPath>'
         f'<linearGradient id="{uid}-fl" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a1}"/><stop offset="1" stop-color="{a2}"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="{deep}"/>',
         f'<g clip-path="url(#{uid}-strip)"><image href="{photo_href(photo)}" x="-200" y="0" width="{P + 400}" height="{H}" preserveAspectRatio="xMidYMid slice" filter="url(#{uid}-duo)"/></g>',
         f'<rect x="{P}" y="0" width="14" height="{H}" fill="url(#{uid}-fl)"/>',
         f'<circle cx="{P - 170}" cy="{H * .5:.0f}" r="80" fill="url(#{uid}-fl)"/><circle cx="{P - 170}" cy="{H * .5:.0f}" r="106" fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="2"/>',
         wordmark(R, 96, "#fff", 26),
         _bars(L, 82, a1, "#fff", 36, 7),
         label(ev["series"], L, 140, "#fff", 18, opacity=.9)]
    base = 190 + size * .73
    b.append(t(title, L - size * .02, base, size, "#fff", 800, track=-0.005, stretch=75))
    b.append(t(ev["year"], L, base + 120, 120, "none", 700, track=-0.02, extra='stroke="#fff" stroke-width="2.5"'))
    y = 700
    b.append(f'<rect x="{L}" y="{y}" width="{R - L}" height="1" fill="#fff" fill-opacity=".3"/>')
    for i, (k, v) in enumerate((("Dates", date_range(ev)), ("Venue", place(ev)), ("Events", ev["events"]))):
        x = L + i * (R - L) / 3
        b.append(label(k, x, y + 44, "#fff", 13, opacity=.55))
        for j, ln in enumerate(_wrap(v, 18)[:2]):
            b.append(t(ln, x, y + 78 + j * 28, 22, "#fff", 600))
    b.append(noise)
    return b


def ticket(ev, uid):
    """Contender and Feeder: no photo. Paper stock and a ticket: the city, the days as a row of numbers, a stub."""
    c, deep = colours(ev)
    ink, paper = "#121417", "#f3f1ec"
    defs, noise = grain(uid, .05, dark=True)
    X0, Y0, X1, Y1 = 80, 80, W - 80, H - 80
    S = X1 - 330                               # where the stub begins
    title = ev["city"].upper()
    size = fit(title, S - X0 - 120, 210, -0.005)
    b = [f'<defs>{defs}</defs>', f'<rect width="{W}" height="{H}" fill="{c}"/>',
         # the ticket, with notches where the stub tears off
         f'<path d="M{X0} {Y0} H{S - 26} A26 26 0 0 0 {S + 26} {Y0} H{X1} V{Y1} H{S + 26} A26 26 0 0 0 {S - 26} {Y1} H{X0} Z" fill="{paper}"/>',
         f'<line x1="{S}" y1="{Y0 + 40}" x2="{S}" y2="{Y1 - 40}" stroke="{ink}" stroke-opacity=".35" stroke-width="2" stroke-dasharray="2 12" stroke-linecap="round"/>']
    L = X0 + 64
    b.append(_bars(L, Y0 + 58, c, ink, 36, 7))
    if tiered(ev):
        b += poster_tiers.ticket_marks(ev, uid, X0, Y0, S, ink)
        b.append(t(poster_tiers.type_name(ev).upper(), L, Y0 + 124, 40, ink, 700, track=0.04, stretch=85))
        size = min(size, 190)
        base = Y0 + 160 + size * .73
    else:
        b.append(label(ev["series"], L, Y0 + 112, ink, 18, opacity=1))
        base = Y0 + 140 + size * .73
    b.append(t(title, L - size * .02, base, size, ink, 800, track=-0.005, stretch=75))
    b.append(t(f'{ev["country"]}', L, base + 56, 26, ink, 500, opacity=.7))
    ds = days(ev)
    if ds:
        top, cw = Y1 - 230, (S - 60 - L) / max(len(ds), 5)
        b.append(f'<rect x="{L}" y="{top}" width="{S - 60 - L}" height="1" fill="{ink}" fill-opacity=".3"/>')
        for i, d in enumerate(ds):
            x = L + i * cw
            last = i == len(ds) - 1
            b.append(label(f"{d:%a}", x, top + 40, ink, 13, opacity=.9 if last else .5))
            b.append(t(f"{d.day:02d}", x - 2, top + 122, min(78, cw * .7), c if last else ink, 700 if last else 300, track=-0.03))
    # the stub: year, month, Eleven
    sx = S + 60
    b.append(label("Admit one", sx, Y0 + 90, ink, 13, opacity=.55))
    b.append(t(ev["year"], sx - 4, Y0 + 220, 112, ink, 800, track=-0.03, stretch=75))
    if ds:
        b.append(t(f"{ds[0]:%B}".upper(), sx, Y0 + 270, 26, ink, 700, track=0.12))
    b.append(f'<circle cx="{sx + 92}" cy="{Y1 - 210}" r="80" fill="none" stroke="{c}" stroke-width="4"/>')
    b.append(f'<circle cx="{sx + 92}" cy="{Y1 - 210}" r="64" fill="{c}"/>')
    word = ev["series"].replace("WTT ", "").upper()
    b.append(t(word, sx + 92, Y1 - 204, min(20, 100 / (len(word) * .62)), "#fff", 800, "middle", 0.06))
    b.append(wordmark(X1 - 52, Y1 - 52, ink, 26))
    b.append(noise)
    return b


def _coords(ev):
    import re as _re
    m = _re.findall(r"([\d.]+)° ([NSEW])", ev.get("coords") or "")
    if len(m) < 2:
        return None
    lat = float(m[0][0]) * (1 if m[0][1] == "N" else -1)
    lon = float(m[1][0]) * (1 if m[1][1] == "E" else -1)
    return lat, lon


def atlas(ev, uid):
    """Continental championships and Games: the region's colour, a graticule, and a dot where the event is played."""
    c, deep = colours(ev)
    defs, noise = grain(uid, .07)
    title = ev["city"].upper()
    size = fit(title, 860, 230, -0.005)
    b = [f'<defs>{defs}<radialGradient id="{uid}-g" cx="72%" cy="40%" r="70%"><stop offset="0" stop-color="{c}"/><stop offset="1" stop-color="{deep}"/></radialGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#{uid}-g)"/>']
    # graticule on the right two thirds: an equirectangular slice of the world
    gx0, gx1, gy0, gy1 = 640, W, 0, H
    for lon in range(-180, 181, 15):
        x = gx0 + (lon + 180) / 360 * (gx1 - gx0)
        b.append(f'<line x1="{x:.0f}" y1="{gy0}" x2="{x:.0f}" y2="{gy1}" stroke="#fff" stroke-opacity="{.22 if lon % 45 == 0 else .08}" stroke-width="1"/>')
    for lat in range(-75, 76, 15):
        y = gy0 + (90 - lat) / 180 * (gy1 - gy0)
        b.append(f'<line x1="{gx0}" y1="{y:.0f}" x2="{gx1}" y2="{y:.0f}" stroke="#fff" stroke-opacity="{.22 if lat == 0 else .08}" stroke-width="1"/>')
    p = _coords(ev)
    if p:
        x = gx0 + (p[1] + 180) / 360 * (gx1 - gx0)
        y = gy0 + (90 - p[0]) / 180 * (gy1 - gy0)
        b.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="70" fill="#fff" fill-opacity=".08"/><circle cx="{x:.0f}" cy="{y:.0f}" r="36" fill="none" stroke="#fff" stroke-width="2"/>'
                 f'<circle cx="{x:.0f}" cy="{y:.0f}" r="12" fill="#ff5a1f"/>')
        b.append(label(ev["coords"], x + 56, y + 6, "#fff", 13, opacity=.8))
    L = 96
    b.append(wordmark(L, 96, "#fff", 26, "start"))
    b.append(_bars(L, 150, "#ff5a1f", "#fff", 36, 7))
    b.append(label(ev.get("region") or ev["series"], L, 205, "#fff", 18, opacity=.9))
    base = 240 + size * .73
    b.append(t(title, L - size * .02, base, size, "#fff", 800, track=-0.005, stretch=75))
    b.append(t(ev["series"], L, base + 70, 34, "#fff", 600))
    b.append(t(ev["year"], L, base + 200, 120, "#fff", 200, track=-0.03, opacity=.95))
    y = H - 110
    b.append(f'<rect x="{L}" y="{y - 46}" width="520" height="1" fill="#fff" fill-opacity=".3"/>')
    b.append(label(f'{date_range(ev)}  ·  {place(ev)}', L, y, "#fff", 15, opacity=.85))
    b.append(noise)
    return b


def landmark(ev, uid):
    """Club leagues (and England): the country's landmark, full bleed, toned in the league's colour."""
    c, deep = ev.get("colours") or TIERS["club"]
    a1 = ev.get("accent", "#ffb81c")
    photo = ev["landmark"]
    defs, noise = grain(uid, .07)
    title = ev["name"].upper()
    size = fit(title, 1240, 210, -0.005)
    b = [f'<defs>{defs}{_duo(uid, c, deep, lift=.7)}'
         f'<linearGradient id="{uid}-sh" x1="0" y1="0" x2="0" y2="1"><stop offset=".25" stop-color="{deep}" stop-opacity="0"/><stop offset="1" stop-color="{deep}" stop-opacity=".95"/></linearGradient>'
         f'<linearGradient id="{uid}-sl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{deep}" stop-opacity=".75"/><stop offset=".6" stop-color="{deep}" stop-opacity="0"/></linearGradient></defs>',
         f'<image href="{landmark_href(photo)}" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="{ev.get("align", "xMidYMid")} slice" filter="url(#{uid}-duo)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#{uid}-sh)"/>', f'<rect width="{W}" height="{H}" fill="url(#{uid}-sl)"/>']
    L = 96
    b.append(wordmark(L, 96, "#fff", 26, "start"))
    b.append(label(ev.get("kicker", "Club table tennis"), W - 96, 92, "#fff", 15, "end", .85))
    base = H - 230
    b.append(_bars(L, base - size * .73 - 70, a1, "#fff", 40, 8))
    b.append(t(title, L - size * .02, base, size, "#fff", 800, track=-0.005, stretch=75))
    b.append(f'<rect x="{L}" y="{base + 46}" width="{W - 2 * L}" height="1" fill="#fff" fill-opacity=".35"/>')
    for i, (k, v) in enumerate(ev["cols"]):
        x = L + i * (W - 2 * L) / 3
        b.append(label(k, x, base + 92, "#fff", 13, opacity=.6))
        b.append(t(v, x, base + 128, 24, "#fff", 600))
    b.append(noise)
    return b


def ladder(ev, uid):
    """World rankings: the ranking drawn as bars, the longest first, on paper stock."""
    ink, paper, c = "#121417", "#f3f1ec", "#2f5fd0"
    defs, noise = grain(uid, .05, dark=True)
    b = [f'<defs>{defs}</defs>', f'<rect width="{W}" height="{H}" fill="{paper}"/>']
    L, R = 96, W - 96
    b.append(_bars(L, 82, "#ff5a1f", c, 40, 8))
    b.append(label("ITTF world ranking", L, 140, ink, 18, opacity=1))
    b.append(t("RANKINGS", L - 6, 340, 250, ink, 800, track=-0.005, stretch=75))
    b.append(t("Updated every week", L, 410, 34, ink, 300))
    widths = (1, .91, .87, .8, .74, .68, .63, .57, .52, .48)
    top, gap = 470, 36
    for i, wv in enumerate(widths):
        y = top + i * gap
        b.append(t(str(i + 1), L, y + 22, 20, ink, 700 if i == 0 else 400, opacity=1 if i == 0 else .6))
        b.append(f'<rect x="{L + 52}" y="{y + 6}" width="{(R - L - 52) * wv:.0f}" height="18" fill="{"#ff5a1f" if i == 0 else c}" fill-opacity="{1 if i < 3 else .55}"/>')
    b.append(wordmark(R, 96, ink, 26))
    b.append(noise)
    return b


def bulletin(ev, uid):
    """News topics: ink ground, one bold word, the ball, a strap line."""
    ink, paper = "#121417", "#f3f1ec"
    c = ev.get("colours", ("#2f5fd0", "#0c1a45"))[0]
    defs, noise = grain(uid, .08)
    title = ev["name"].upper()
    size = fit(title, 960, 300, -0.005)
    b = [f'<defs>{defs}<radialGradient id="{uid}-b" cx="35%" cy="30%" r="70%"><stop offset="0" stop-color="#ffd23f"/><stop offset="1" stop-color="#ff5a1f"/></radialGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="{ink}"/>',
         f'<rect x="0" y="{H - 200}" width="{W}" height="200" fill="{c}"/>',
         f'<circle cx="{W - 250}" cy="300" r="140" fill="url(#{uid}-b)"/><circle cx="{W - 250}" cy="300" r="172" fill="none" stroke="{paper}" stroke-opacity=".5" stroke-width="2"/>']
    L = 96
    b.append(wordmark(L, 96, paper, 26, "start"))
    b.append(label(ev["series"], L, 220, paper, 18, opacity=.8))
    b.append(t(title, L - size * .02, 250 + size * .73, size, paper, 800, track=-0.005, stretch=75))
    b.append(t(ev["strap"], L, H - 82, 52, "#fff", 300, track=-0.02))
    b.append(noise)
    return b


def tile_for(ev, uid):
    """Square version: the photo looks keep the photo panel; ticket and atlas use a colour panel with their motif."""
    lk = look(ev)
    if lk == "five_lacquer":
        return poster_tiers.square_lacquer(ev, uid)
    if lk == "five_vermilion":
        return poster_tiers.square_vermilion(ev, uid)
    if lk in ("three", "four", "five"):
        return poster_tiers.square(ev, uid)
    if lk not in ("ticket", "atlas"):
        return tile(ev, uid)
    c, deep = colours(ev)
    ink, paper, L, R = "#121417", "#f3f1ec", 64, TW - 64
    PH = 470
    defs, _ = grain(uid, .05, dark=True)
    title = ev["city"].upper()
    size = fit(title, R - L, 230, -0.005)
    b = [f'<defs>{defs}</defs>', f'<rect width="{TW}" height="{TH}" fill="{paper}"/>', f'<rect width="{TW}" height="{PH}" fill="{c if lk == "ticket" else deep}"/>']
    if lk == "atlas":
        for k in range(0, TW + 1, 62):
            b.append(f'<line x1="{k}" y1="0" x2="{k}" y2="{PH}" stroke="#fff" stroke-opacity=".12"/>')
        for k in range(0, PH + 1, 62):
            b.append(f'<line x1="0" y1="{k}" x2="{TW}" y2="{k}" stroke="#fff" stroke-opacity=".12"/>')
        b.append(f'<circle cx="{TW * .62:.0f}" cy="{PH * .45:.0f}" r="34" fill="none" stroke="#fff" stroke-width="2"/><circle cx="{TW * .62:.0f}" cy="{PH * .45:.0f}" r="12" fill="#ff5a1f"/>')
    else:
        b.append(f'<path d="M{L} {PH - 60} H{R}" stroke="{paper}" stroke-opacity=".6" stroke-width="3" stroke-dasharray="3 16" stroke-linecap="round"/>')
        b.append(t(ev["series"].replace("WTT ", "").upper(), L, 150, 70, paper, 800, track=0.02, stretch=75))
        if tiered(ev):
            b.append(poster_tiers.star_row(R, 150, poster_tiers.stars(ev), 30, paper, anchor="end", total=5, empty=paper + "55"))
    b.append(t(ev["year"], R, PH - 40 if lk == "atlas" else PH - 110, 150, "#fff", 300, "end", -0.03))
    b.append(label(ev["series"], L, PH + 72, ink, 24, opacity=1))
    base = PH + 112 + size * 0.73
    b.append(t(title, L - size * 0.02, base, size, ink, 800, track=-0.005, stretch=75))
    b.append(f'<rect x="{L}" y="{base + 36:.0f}" width="{R - L}" height="2" fill="{ink}"/>')
    b.append(t(date_range(ev), L, base + 96, 38, ink, 600))
    b.append(label(place(ev), L, base + 142, ink, 20, opacity=.6))
    b.append(wordmark(R, base + 144, ink, 28))
    b.append(_)
    return b


import sys as _sys   # noqa: E402
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import poster_tiers   # noqa: E402
poster_tiers.bind(_sys.modules[__name__])

STYLES = {"five_lacquer": poster_tiers.five_lacquer, "square_lacquer": poster_tiers.square_lacquer, "five_vermilion": poster_tiers.five_vermilion, "square_vermilion": poster_tiers.square_vermilion, "five_gilt": poster_tiers.five_gilt, "square_gilt": poster_tiers.square_gilt, "five_ink": poster_tiers.five_ink, "square_ink": poster_tiers.square_ink, "three": poster_tiers.three, "four": poster_tiers.four, "five": poster_tiers.five, "grid": grid, "arena": arena, "court": court, "tile": tile, "split": split, "ticket": ticket, "atlas": atlas,
          "landmark": landmark, "ladder": ladder, "bulletin": bulletin, "tile_for": tile_for}


def svg(ev, style):
    uid = f'{ev["id"]}-{style}'
    body = "\n".join(STYLES[style](ev, uid))
    lbl = f'{ev["series"]} {ev["city"]} {ev["year"]} poster by Eleven'
    w, h = (TW, TH) if style in ("tile", "tile_for", "square_ink", "square_lacquer", "square_vermilion", "square_gilt") else (W, H)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{e(lbl)}">\n{body}\n</svg>\n'


def extras():
    """Posters that are not for an event: one per club league and one per recurring news topic. The homepage's
    Latest cards use them for stories with no video or event poster, so every card has a picture.
    Rendered to img/posters/league-<slug>.jpg and img/posters/topic-<name>.jpg (python3 tools/posters.py --extras)."""
    import build_clubs
    out = []
    for lg in build_clubs.LEAGUES:
        comps = ", ".join(dict.fromkeys(c[2] for c in lg["comps"]))
        main = lg.get("colour") or "#23895c"
        deep = "#" + "".join(f"{int(int(main[k:k + 2], 16) * .22):02x}" for k in (1, 3, 5))
        out.append({"id": f'league-{lg["slug"]}', "name": lg["name"], "series": "Club table tennis", "city": lg["name"], "country": lg["country"],
                    "tier": "club", "year": "", "events": "", "look": "landmark", "landmark": LEAGUE_LANDMARK.get(lg["slug"], "brussels-atomium.jpg"),
                    "colours": (main, deep), "kicker": f'Club table tennis · {lg["country"]}',
                    "cols": (("Competitions", "Men and women" if len(lg["comps"]) > 1 else lg["comps"][0][1]), ("Country", lg["country"]), ("On Eleven", "Tables and results"))})
    out.append({"id": "topic-rankings", "name": "Rankings", "series": "ITTF world ranking", "city": "Rankings", "tier": "champions", "year": "", "events": "", "look": "ladder"})
    out.append({"id": "topic-england", "name": "England", "series": "Table tennis in England", "city": "England", "tier": "world", "year": "", "events": "",
                "look": "landmark", "landmark": "london-big-ben.jpg", "colours": ("#d4213d", "#2e0610"), "kicker": "News from home",
                "cols": (("Covers", "Players, leagues and clubs"), ("Governing body", "Table Tennis England"), ("On Eleven", "Results and reports"))})
    out.append({"id": "topic-equipment", "name": "Equipment", "series": "Blades, rubbers and balls", "city": "Equipment", "tier": "contender", "year": "", "events": "",
                "look": "bulletin", "colours": ("#6b7586", "#1a1e26"), "strap": "Kit, sponsors and the rules behind them"})
    out.append({"id": "topic-news", "name": "News", "series": "World table tennis", "city": "News", "tier": "champions", "year": "", "events": "",
                "look": "bulletin", "colours": ("#2f5fd0", "#0c1a45"), "strap": "Around the world, checked at source"})
    return out


def extra_credit(ev):
    """Credit line for an extra poster's landmark photo, if it has one."""
    if ev.get("landmark"):
        name, url, what = LANDMARKS[ev["landmark"]]
        return f"{what}. Photo: {name}, Unsplash Licence ({url})"
    return ""


def render_extras():
    evs = assign_variants(extras())
    out = os.path.join(ROOT, "img", "posters")
    font = os.path.join(ROOT, "tools", "BricolageGrotesque-variable.woff2")
    import base64
    b64 = base64.b64encode(open(font, "rb").read()).decode()
    css = (f"@font-face{{font-family:'Bricolage Grotesque';src:url(data:font/woff2;base64,{b64}) format('woff2');font-weight:200 800;font-stretch:75% 100%}}"
           "html,body{margin:0;background:#000}svg{display:block}")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": W, "height": H})
        for ev in evs:
            pg.set_content(f"<html><head><style>{css} svg{{width:{W}px;height:{H}px}}</style></head><body>{svg(ev, ev.get('look', 'grid'))}</body></html>")
            pg.evaluate("document.fonts.ready.then(() => document.fonts.size)")
            pg.wait_for_timeout(300)
            pg.screenshot(path=os.path.join(out, f'{ev["id"]}.jpg'), type="jpeg", quality=84)
            print("poster:", ev["id"], ev["_v"])
        browser.close()


def missing():
    data = json.load(open(os.path.join(ROOT, "data", "events.json"), encoding="utf-8"))
    out = os.path.join(ROOT, "img", "posters")
    return [ev["id"] for ev in data["events"] if not (os.path.exists(os.path.join(out, ev["id"] + ".jpg")) and os.path.exists(os.path.join(out, ev["id"] + "-sq.jpg")))]


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
            for style, suffix, (w, h) in ((ev.get("style") or look(ev), "", (W, H)), ("tile_for", "-sq", (TW, TH))):
                pg.set_viewport_size({"width": w, "height": h})
                pg.set_content(f"<html><head><style>{css} svg{{width:{w}px;height:{h}px}}</style></head><body>{svg(ev, style)}</body></html>")
                pg.evaluate("document.fonts.ready.then(() => document.fonts.size)")
                pg.wait_for_timeout(300)
                pg.screenshot(path=os.path.join(out, f'{ev["id"]}{suffix}.jpg'), type="jpeg", quality=84)
            print("poster:", ev["id"], ev["_v"])
        browser.close()


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--extras"]:
        sys.path.insert(0, os.path.dirname(__file__))
        render_extras()
        sys.exit(0)
    if sys.argv[1:] == ["--need"]:
        sys.exit(0 if missing() else 1)
    if sys.argv[1:] == ["--missing"]:
        todo = missing()
        if todo:
            main(todo)
    else:
        main(sys.argv[1:] or None)
