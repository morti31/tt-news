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


def grid(ev, uid):
    """A, Grid: paper stock, an exact typographic grid, the tournament laid out like a timetable."""
    c, deep = TIERS[ev["tier"]]
    ink, paper, L, R = "#121417", "#f3f1ec", 96, 1504
    defs, noise = grain(uid, .05, dark=True)
    title = ev["city"].upper()
    size = fit(title, R - L, 360, -0.005)
    b = [f"<defs>{defs}</defs>", f'<rect width="{W}" height="{H}" fill="{paper}"/>']
    b.append(label(ev["series"], L, 92, ink, 18, opacity=1))
    b.append(label(f'{ev["city"]}, {ev["country"]}', R, 92, ink, 18, "end", .6))
    b.append(f'<rect x="{L}" y="112" width="{R - L}" height="2" fill="{ink}"/>')
    base = 128 + size * 0.73
    b.append(t(title, L - size * 0.02, base, size, ink, 800, track=-0.005, stretch=75))
    y = base + 44
    b.append(f'<rect x="{L}" y="{y:.0f}" width="{R - L}" height="1" fill="{ink}" fill-opacity=".35"/>')
    cols = (("Dates", date_range(ev)), ("Venue", place(ev)), ("Events", ev["events"]))
    for i, (k, v) in enumerate(cols):
        x = L + i * 380
        b.append(label(k, x, y + 46, ink, 15, opacity=.55))
        b.append(t(v, x, y + 84, 26, ink, 600))
    b.append(t(ev["year"], R, y + 84, 56, c, 300, "end", -0.02))
    ds = days(ev)
    top, cw = 700, (R - L) / max(1, len(ds))
    b.append(f'<rect x="{L}" y="{top}" width="{R - L}" height="1" fill="{ink}" fill-opacity=".35"/>')
    for i, d in enumerate(ds):
        x = L + i * cw
        last = i == len(ds) - 1
        if last:
            b.append(f'<rect x="{x:.0f}" y="{top}" width="{cw:.0f}" height="{H - top - 60}" fill="{c}"/>')
        elif i:
            b.append(f'<rect x="{x:.0f}" y="{top + 20}" width="1" height="{H - top - 100}" fill="{ink}" fill-opacity=".18"/>')
        col = "#fff" if last else ink
        b.append(label(f"{d:%a}" + ("  Finals" if last else ""), x + 20, top + 40, col, 14, opacity=.9 if last else .55))
        b.append(t(f"{d.day:02d}", x + 16, top + 128, 92, col, 300, track=-0.03))
    b.append(wordmark(R, H - 22, ink, 20))
    b.append(label("Eleven event series", L, H - 24, ink, 12, opacity=.45))
    b.append(noise)
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


STYLES = {"grid": grid, "arena": arena, "court": court}


def svg(ev, style):
    uid = f'{ev["id"]}-{style}'
    body = "\n".join(STYLES[style](ev, uid))
    lbl = f'{ev["series"]} {ev["city"]} {ev["year"]} poster by Eleven'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{e(lbl)}">\n{body}\n</svg>\n'


def main(only=None):
    """Render every hub event's poster to img/posters/<id>.jpg (needs Playwright, so run it locally, not at deploy)."""
    data = json.load(open(os.path.join(ROOT, "data", "events.json"), encoding="utf-8"))
    out = os.path.join(ROOT, "img", "posters")
    os.makedirs(out, exist_ok=True)
    font = os.path.join(ROOT, "tools", "BricolageGrotesque-variable.woff2")
    import base64
    b64 = base64.b64encode(open(font, "rb").read()).decode()
    css = (f"@font-face{{font-family:'Bricolage Grotesque';src:url(data:font/woff2;base64,{b64}) format('woff2');font-weight:200 800;font-stretch:75% 100%}}"
           "html,body{margin:0;background:#000}svg{display:block;width:1600px;height:900px}")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": W, "height": H})
        for ev in data["events"]:
            if only and ev["id"] not in only:
                continue
            pg.set_content(f"<html><head><style>{css}</style></head><body>{svg(ev, ev.get('style', data.get('style', 'arena')))}</body></html>")
            pg.evaluate("document.fonts.ready.then(() => document.fonts.size)")
            pg.wait_for_timeout(300)
            pg.screenshot(path=os.path.join(out, f'{ev["id"]}.jpg'), type="jpeg", quality=86)
            print("poster:", ev["id"])
        browser.close()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:] or None)
