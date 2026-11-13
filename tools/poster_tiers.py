"""Tiered posters for 2026 onwards: the poster says what kind of event it is and how big it is.

Every event gets a star rating (the same one the schedule shows) and its competition type as the headline.
The look grows more sophisticated with the stars:
  1-2 stars  Feeder, Contender: the paper ticket (tools/posters.py ticket), now with the type and stars on it
  3 stars    Star Contender: duotone photo strip beside a deep colour field, silver hairlines and silver stars
  4 stars    WTT Champions, WTT Finals, continental championships and Games: near-black, a photo across most
             of the poster, a fine gold and silver frame, silver type headline and gold stars
  4.5 stars  Grand Smash: the same layout as 5 stars in "vermilion": all red, black stars, brush circle and seal
  5 stars    World Cup, World Championships, Olympics: "lacquer" (five_lacquer): near-black, an ink-wash
             photo in a fine frame, a red brush circle, five red stars over a red type headline, a red seal with the
             year; the World Championships and the Olympics also carry a laurel emblem (Eleven's own drawing; no
             organiser marks, no Olympic rings). Always these colours.
Colours (posters.colours): Feeders always grey, the WTT Finals always gold; Contenders, Star Contenders, Champions and
continental events take turns through posters.ROTATION so no two neighbours in a series match.

Used by tools/posters.py for events dated 2026 or later; older posters are left as they were.
"""
import math

P = None   # tools/posters.py, set by bind()


def bind(mod):
    """posters.py hands itself over, so the two share one set of helpers (no circular import)."""
    global P, e, t, label, fit, wordmark, grain, W, H, TW, TH
    P = mod
    e, t, label, fit, wordmark, grain = mod.e, mod.t, mod.label, mod.fit, mod.wordmark, mod.grain
    W, H, TW, TH = mod.W, mod.H, mod.TW, mod.TH

GOLD = ("#7a5a12", "#c99a2e", "#f6e3a1", "#b8862a", "#f1d68a")
SILVER = ("#6d7480", "#b9c0cb", "#f4f6f9", "#9aa2ae", "#e3e7ee")


def stars(ev):
    """Stars, 1 to 5 (Grand Smashes 4.5). Matches the schedule (schedule.js STARS)."""
    s, tier = ev.get("series", ""), ev.get("tier")
    if s == "WTT Feeder":
        return 1
    if tier == "contender":
        return 2
    if tier == "star":
        return 3
    if tier in ("champions", "continental"):
        return 4
    if tier == "smash":
        return 4.5
    if tier == "world":
        return 5
    return 2


def type_name(ev):
    """The headline: what kind of competition this is."""
    s = ev.get("series", "")
    names = {"WTT Grand Smash": "Grand Smash", "WTT Champions": "WTT Champions", "WTT Star Contender": "Star Contender",
             "WTT Contender": "WTT Contender", "WTT Feeder": "WTT Feeder", "WTT Finals": "WTT Finals", "ITTF World Cup": "World Cup"}
    return names.get(s, s)


def emblem_kind(ev):
    s = ev.get("series", "") + " " + ev.get("name", "")
    if "Olympic" in s:
        return "olympic"
    if "World Championships" in s or "World Team Championships" in s:
        return "worlds"
    return None


def foil(uid, key, cols, vertical=False):
    x2, y2 = ("0", "1") if vertical else ("1", ".35")
    stops = "".join(f'<stop offset="{i / (len(cols) - 1):.2f}" stop-color="{c}"/>' for i, c in enumerate(cols))
    return f'<linearGradient id="{uid}-{key}" x1="0" y1="0" x2="{x2}" y2="{y2}">{stops}</linearGradient>'


def star_row(x, y, n, size, fill, gap=1.35, anchor="start", total=None, empty=None):
    """n filled stars (of `total`, the rest drawn as outlines if `empty` is a colour)."""
    total = total or math.ceil(n)
    w = size * gap * (total - 1) + size
    x0 = x - w if anchor == "end" else x - w / 2 if anchor == "middle" else x
    out = []
    for k in range(total):
        cx, cy, r = x0 + size / 2 + k * size * gap, y - size / 2, size / 2
        pts = " ".join(f"{cx + (r if j % 2 == 0 else r * .42) * math.sin(math.pi * j / 5):.1f},{cy - (r if j % 2 == 0 else r * .42) * math.cos(math.pi * j / 5):.1f}"
                       for j in range(10))
        if k + 1 <= n:
            out.append(f'<polygon points="{pts}" fill="{fill}"/>')
        elif k < n:   # a half star: the left half filled, the outline (or a faint copy) behind it
            cid = f"half{cx:.0f}x{cy:.0f}y{size:.0f}"
            back = f'<polygon points="{pts}" fill="none" stroke="{empty}" stroke-width="1.5"/>' if empty else f'<polygon points="{pts}" fill="{fill}" fill-opacity=".28"/>'
            out.append(f'{back}<clipPath id="{cid}"><rect x="{cx - r - 1:.1f}" y="{cy - r - 1:.1f}" width="{r + 1:.1f}" height="{2 * r + 2:.1f}"/></clipPath>'
                       f'<polygon points="{pts}" fill="{fill}" clip-path="url(#{cid})"/>')
        elif empty:
            out.append(f'<polygon points="{pts}" fill="none" stroke="{empty}" stroke-width="1.5"/>')
    return "".join(out)


def laurel(cx, cy, r, fill):
    """Two laurel branches rising round a ball: Eleven's emblem for the World Championships and the Olympics."""
    R = r * .78
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r * .30:.1f}" fill="none" stroke="{fill}" stroke-width="{r * .045:.1f}"/>',
           f'<circle cx="{cx}" cy="{cy}" r="{r * .17:.1f}" fill="{fill}"/>']
    for s in (-1, 1):
        # the stem: an arc from under the ball up the side
        a0, a1 = math.radians(-80), math.radians(55)
        x0, y0 = cx + s * R * math.cos(a0), cy - R * math.sin(a0)
        x1, y1 = cx + s * R * math.cos(a1), cy - R * math.sin(a1)
        out.append(f'<path d="M{x0:.1f} {y0:.1f} A{R:.1f} {R:.1f} 0 0 {0 if s > 0 else 1} {x1:.1f} {y1:.1f}" fill="none" stroke="{fill}" stroke-width="{r * .035:.1f}"/>')
        for k in range(8):
            a = math.radians(-70 + k * 17)
            px, py = cx + s * R * math.cos(a), cy - R * math.sin(a)
            tang = math.degrees(math.atan2(-s * math.cos(a), -math.sin(a) * 1)) if False else None
            # leaf points outwards and upwards along the stem
            ang = (90 - math.degrees(a)) * s + (-35 if s > 0 else 35)
            for side in (-1, 1):
                off = r * .11
                lx, ly = px + side * off * math.cos(a) * s, py - side * off * math.sin(a)
                out.append(f'<ellipse cx="{lx:.1f}" cy="{ly:.1f}" rx="{r * .055:.1f}" ry="{r * .15:.1f}" fill="{fill}" transform="rotate({ang + side * 28 * s:.0f} {lx:.1f} {ly:.1f})"/>')
    return "".join(out)


def _photo(ev):
    return P._variant(ev)[4]


def _mono(uid, dark, light, key="mono", contrast=1.0):
    d, l = P._rgb(dark), P._rgb(light)
    tv = "".join(f'<feFunc{ch} type="table" tableValues="{d[i]:.3f} {d[i] + (l[i] - d[i]) * .45:.3f} {l[i]:.3f}"/>' for i, ch in enumerate("RGB"))
    return (f'<filter id="{uid}-{key}" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0"/>'
            f'<feComponentTransfer><feFuncR type="linear" slope="{contrast}" intercept="{(1 - contrast) / 2}"/><feFuncG type="linear" slope="{contrast}" intercept="{(1 - contrast) / 2}"/>'
            f'<feFuncB type="linear" slope="{contrast}" intercept="{(1 - contrast) / 2}"/></feComponentTransfer><feComponentTransfer>{tv}</feComponentTransfer></filter>')


def _info(ev, L, R, y, ink, lab_ink, rule, size=22, cols=None):
    cols = cols or (("Dates", P.date_range(ev)), ("Venue", P.place(ev)), ("Events", ev.get("events") or ""))
    out = [f'<rect x="{L}" y="{y}" width="{R - L}" height="1" fill="{rule}"/>']
    n = len(cols)
    for i, (k, v) in enumerate(cols):
        x = L + i * (R - L) / n
        out.append(label(k, x, y + 42, lab_ink, 13, opacity=1))
        for j, ln in enumerate(P._wrap(v, 22 if n == 3 else 30)[:2]):
            out.append(t(ln, x, y + 76 + j * 28, size, ink, 500))
    return out


# ---------------------------------------------------------------- 3 stars: Star Contender
def three(ev, uid):
    c, deep = P.colours(ev)
    photo = _photo(ev)
    defs, noise = grain(uid, .05)
    S = 600
    L, R = S + 96, W - 96
    head = type_name(ev).upper()
    city = ev["city"].upper()
    hs = fit(head, R - L, 64, 0.06)   # kept below the 4-star headline: the type grows with the stars
    cs = fit(city, R - L - 230, 190, -0.005)   # room for the year on the right
    b = [f'<defs>{defs}{P._duo(uid, c, deep)}{foil(uid, "sv", SILVER)}<clipPath id="{uid}-s"><rect width="{S}" height="{H}"/></clipPath></defs>',
         f'<rect width="{W}" height="{H}" fill="{deep}"/>',
         f'<g clip-path="url(#{uid}-s)"><image href="{P.photo_href(photo)}" x="-220" y="0" width="{S + 440}" height="{H}" preserveAspectRatio="xMidYMid slice" filter="url(#{uid}-duo)"/></g>',
         f'<rect x="{S}" y="0" width="3" height="{H}" fill="url(#{uid}-sv)"/>',
         wordmark(R, 96, "#fff", 26),
         star_row(L, 98, 3, 30, f"url(#{uid}-sv)", total=5, empty="#ffffff55"),
         label(f'{ev.get("name", "")} {ev.get("year", "")}'.strip(), L, 160, "#fff", 16, opacity=.7)]
    y = 196 + hs * .73
    b.append(t(head, L, y, hs, f"url(#{uid}-sv)", 600, track=0.06, stretch=85))
    y2 = y + 34 + cs * .73
    b.append(t(city, L - cs * .02, y2, cs, "#fff", 800, track=-0.005, stretch=75))
    b.append(t(ev["year"], R, y2, 64, "#fff", 300, "end", -0.02, opacity=.85))
    b += _info(ev, L, R, 700, "#fff", "#ffffff8c", "url(#" + uid + "-sv)")
    b.append(noise)
    return b


# ---------------------------------------------------------------- 4 stars: Champions, Finals, continental
def four(ev, uid):
    c, deep = P.colours(ev)
    gold_first = ev.get("series") == "WTT Finals"
    photo = _photo(ev)
    defs, noise = grain(uid, .045)
    base = "#0a0e16"
    L, R = 120, W - 120
    head = type_name(ev).upper()
    city = ev["city"].upper()
    hs = fit(head, 840, 92, 0.08)
    cs = fit(city, 980, 230, -0.005)
    head_fill = f"url(#{uid}-{'gd' if gold_first else 'sv'})"
    b = [f'<defs>{defs}{_mono(uid, base, c if not gold_first else "#9c7a2c")}{foil(uid, "gd", GOLD)}{foil(uid, "sv", SILVER)}'
         f'<linearGradient id="{uid}-fade" x1="0" y1="0" x2="1" y2="0"><stop offset=".22" stop-color="{base}"/><stop offset=".72" stop-color="{base}" stop-opacity=".25"/><stop offset="1" stop-color="{base}" stop-opacity=".05"/></linearGradient>'
         f'<linearGradient id="{uid}-tint" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="{c}" stop-opacity=".0"/><stop offset="1" stop-color="{c}" stop-opacity=".35"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="{base}"/>',
         f'<image href="{P.photo_href(photo)}" x="300" y="0" width="{W - 300}" height="{H}" preserveAspectRatio="xMidYMid slice" filter="url(#{uid}-mono)" opacity=".7"/>',
         f'<rect width="{W}" height="{H}" fill="url(#{uid}-tint)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#{uid}-fade)"/>',
         # frame: a fine gold rule inset, a silver one inside it
         f'<rect x="40" y="40" width="{W - 80}" height="{H - 80}" fill="none" stroke="url(#{uid}-gd)" stroke-width="2"/>',
         f'<rect x="52" y="52" width="{W - 104}" height="{H - 104}" fill="none" stroke="url(#{uid}-sv)" stroke-opacity=".45" stroke-width="1"/>',
         star_row(L, 142, 4, 30, f"url(#{uid}-gd)", total=5, empty="#ffffff40"),
         wordmark(R, 140, "#fff", 26),
         label(f'{ev.get("name", "")} {ev.get("year", "")}'.strip(), L, 200, "#fff", 16, opacity=.65)]
    y = 236 + hs * .73
    b.append(t(head, L, y, hs, head_fill, 600, track=0.04, stretch=85))
    b.append(f'<rect x="{L}" y="{y + 26:.0f}" width="180" height="3" fill="url(#{uid}-gd)"/>')
    y2 = y + 62 + cs * .73
    b.append(t(city, L - cs * .02, y2, cs, "#fff", 800, track=-0.005, stretch=75))
    b.append(t(ev["year"], L, y2 + 84, 64, "none", 300, track=-0.01, extra=f'stroke="url(#{uid}-gd)" stroke-width="1.6"'))
    b += _info(ev, L, R, 712, "#fff", "#ffffff80", f"url(#{uid}-sv)", 21)
    b.append(noise)
    return b


# ---------------------------------------------------------------- 5 stars: Smash, World Cup, Worlds, Olympics
def five(ev, uid):
    photo = _photo(ev)
    defs, noise = grain(uid, .045)
    base = "#070605"
    cx = W / 2
    head = type_name(ev).upper()
    city = ev["city"].upper()
    emb = emblem_kind(ev)
    hs = fit(head, 960, 96, 0.14)
    cs = fit(city, 1160, 250, -0.005)
    g = f"url(#{uid}-gd)"
    b = [f'<defs>{defs}{_mono(uid, base, "#c9a24a")}{foil(uid, "gd", GOLD)}{foil(uid, "gv", GOLD, True)}'
         f'<radialGradient id="{uid}-vig" cx=".5" cy=".46" r=".75"><stop offset=".25" stop-color="{base}" stop-opacity=".25"/><stop offset=".8" stop-color="{base}" stop-opacity=".9"/><stop offset="1" stop-color="{base}"/></radialGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="{base}"/>',
         f'<image href="{P.photo_href(photo)}" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice" filter="url(#{uid}-mono)" opacity=".75"/>',
         f'<rect width="{W}" height="{H}" fill="url(#{uid}-vig)"/>',
         f'<rect x="36" y="36" width="{W - 72}" height="{H - 72}" fill="none" stroke="{g}" stroke-width="2.5"/>',
         f'<rect x="50" y="50" width="{W - 100}" height="{H - 100}" fill="none" stroke="{g}" stroke-opacity=".5" stroke-width="1"/>']
    for x, y, sx, sy in ((36, 36, 1, 1), (W - 36, 36, -1, 1), (36, H - 36, 1, -1), (W - 36, H - 36, -1, -1)):   # corner marks
        b.append(f'<path d="M{x} {y + sy * 70} V{y} H{x + sx * 70}" fill="none" stroke="{g}" stroke-width="7"/>')
    top = 118
    if emb:
        b.append(laurel(cx, 150, 74, g))
        top = 262
    b.append(star_row(cx, top, 5, 34, g, anchor="middle"))
    y = top + 40 + hs * .73
    b.append(t(head, cx, y, hs, g, 600, "middle", 0.08, stretch=85))
    y2 = y + 40 + cs * .73
    b.append(t(city, cx, y2, cs, "#fff", 800, "middle", -0.005, stretch=75))
    sub = ev.get("name", "") if ev.get("name", "").upper() not in (head, f"{head} {city}") else ""
    b.append(t(f'{sub} {ev.get("year", "")}'.strip().upper(), cx, y2 + 64, 22, g, 600, "middle", 0.24))
    yb = H - 128
    b.append(f'<rect x="{cx - 420}" y="{yb - 44}" width="840" height="1" fill="{g}"/>')
    b.append(t(f'{P.date_range(ev)}   ·   {P.place(ev)}', cx, yb, 24, "#fff", 500, "middle", 0.04, opacity=.92))
    b.append(wordmark(W - 96, H - 92, "#fff", 24))
    b.append(noise)
    return b


# ---------------------------------------------------------------- squares (phones and small slots)
def square(ev, uid):
    n = stars(ev)
    photo = _photo(ev)
    c, deep = P.colours(ev)
    defs, noise = grain(uid, .045)
    head = type_name(ev).upper()
    city = ev["city"].upper()
    L, R = 70, TW - 70
    if n >= 5:
        base, g = "#070605", f"url(#{uid}-gd)"
        b = [f'<defs>{defs}{_mono(uid, base, "#c9a24a")}{foil(uid, "gd", GOLD)}'
             f'<radialGradient id="{uid}-vig" cx=".5" cy=".42" r=".8"><stop offset=".2" stop-color="{base}" stop-opacity=".3"/><stop offset=".85" stop-color="{base}"/></radialGradient></defs>',
             f'<rect width="{TW}" height="{TH}" fill="{base}"/>',
             f'<image href="{P.photo_href(photo)}" x="0" y="0" width="{TW}" height="{TH}" preserveAspectRatio="xMidYMid slice" filter="url(#{uid}-mono)" opacity=".75"/>',
             f'<rect width="{TW}" height="{TH}" fill="url(#{uid}-vig)"/>',
             f'<rect x="30" y="30" width="{TW - 60}" height="{TH - 60}" fill="none" stroke="{g}" stroke-width="2.5"/>']
        for x, y, sx, sy in ((30, 30, 1, 1), (TW - 30, 30, -1, 1), (30, TH - 30, 1, -1), (TW - 30, TH - 30, -1, -1)):
            b.append(f'<path d="M{x} {y + sy * 56} V{y} H{x + sx * 56}" fill="none" stroke="{g}" stroke-width="6"/>')
        top = 150
        if emblem_kind(ev):
            b.append(laurel(TW / 2, 150, 70, g))
            top = 280
        hs, cs = fit(head, 720, 84, 0.14), fit(city, 860, 210, -0.005)
        b.append(star_row(TW / 2, top, 5, 34, g, anchor="middle"))
        y = top + 36 + hs * .73
        b.append(t(head, TW / 2, y, hs, g, 600, "middle", 0.08, stretch=85))
        y2 = y + 34 + cs * .73
        b.append(t(city, TW / 2, y2, cs, "#fff", 800, "middle", -0.005, stretch=75))
        b.append(f'<rect x="{TW / 2 - 300}" y="{y2 + 46:.0f}" width="600" height="1" fill="{g}"/>')
        b.append(t(P.date_range(ev), TW / 2, y2 + 100, 32, "#fff", 500, "middle", 0.02))
        b.append(t(P.place(ev).upper(), TW / 2, y2 + 146, 17, g, 600, "middle", 0.2))
        b.append(wordmark(TW / 2, TH - 70, "#fff", 26, "middle"))
    else:
        four_ = n == 4
        base = "#0a0e16" if four_ else deep
        gold_first = ev.get("series") == "WTT Finals"
        head_fill = f"url(#{uid}-{'gd' if (four_ and gold_first) else 'sv'})"
        b = [f'<defs>{defs}{_mono(uid, base, c)}{foil(uid, "gd", GOLD)}{foil(uid, "sv", SILVER)}'
             f'<linearGradient id="{uid}-fade" x1="0" y1="0" x2="0" y2="1"><stop offset=".25" stop-color="{base}" stop-opacity=".1"/><stop offset=".6" stop-color="{base}"/></linearGradient></defs>',
             f'<rect width="{TW}" height="{TH}" fill="{base}"/>',
             f'<image href="{P.photo_href(photo)}" x="0" y="0" width="{TW}" height="{TH * .7:.0f}" preserveAspectRatio="xMidYMid slice" filter="url(#{uid}-mono)" opacity="{.6 if four_ else .9}"/>',
             f'<rect width="{TW}" height="{TH}" fill="url(#{uid}-fade)"/>']
        if four_:
            b.append(f'<rect x="30" y="30" width="{TW - 60}" height="{TH - 60}" fill="none" stroke="url(#{uid}-gd)" stroke-width="2"/>')
        b.append(star_row(L, 120, n, 30, f"url(#{uid}-{'gd' if four_ else 'sv'})", total=5, empty="#ffffff45"))
        b.append(wordmark(R, 118, "#fff", 26))
        hs, cs = fit(head, (R - L) * .86, 84 if four_ else 58, 0.08), fit(city, R - L, 200, -0.005)
        y = 520 + hs * .73
        b.append(t(head, L, y, hs, head_fill, 600, track=0.06, stretch=85))
        y2 = y + 30 + cs * .73
        b.append(t(city, L - cs * .02, y2, cs, "#fff", 800, track=-0.005, stretch=75))
        b.append(f'<rect x="{L}" y="{y2 + 40:.0f}" width="{R - L}" height="1" fill="url(#{uid}-sv)"/>')
        b.append(t(P.date_range(ev), L, y2 + 92, 32, "#fff", 500))
        b.append(label(P.place(ev), L, y2 + 134, "#fff", 17, opacity=.6))
    b.append(noise)
    return b


def ticket_marks(ev, uid, X0, Y0, S, ink):
    """1-2 stars: the ticket keeps its look and gains its stars, top right of the main ticket."""
    return [star_row(S - 60, Y0 + 66, stars(ev), 26, ink, anchor="end", total=5, empty=ink + "40")]


# ---------------------------------------------------------------- 5 stars, alternative: ink, paper and cinnabar
INK, PAPER, CINNABAR, STONE = "#1c1b19", "#efe9dd", "#c23a2b", "#8c8577"


def _enso(cx, cy, r, w, colour):
    """An open brush circle (the ball): a thick arc with a gap, tapering at both ends."""
    out = []
    steps = 60
    for k in range(steps):
        a0 = math.radians(-60 + k * 330 / steps)
        a1 = math.radians(-60 + (k + 1) * 330 / steps)
        frac = k / steps
        sw = w * (0.35 + 0.65 * math.sin(math.pi * min(1, frac * 1.15)))
        out.append(f'<path d="M{cx + r * math.cos(a0):.1f} {cy + r * math.sin(a0):.1f} A{r} {r} 0 0 1 {cx + r * math.cos(a1):.1f} {cy + r * math.sin(a1):.1f}" '
                   f'stroke="{colour}" stroke-width="{sw:.1f}" fill="none" stroke-linecap="round"/>')
    return "".join(out)


SCHEMES = {   # bg, ink (big type), accent (type line, brush circle, rule), seal, seal ink, label, photo dark, photo light, photo frame
    "paper": (PAPER, INK, CINNABAR, CINNABAR, PAPER, STONE, "#2a2825", "#e6dfd1", INK),
    "lacquer": ("#141211", "#f3ede1", "#e0402c", "#e0402c", "#f3ede1", "#9a9184", "#0d0c0b", "#b9b0a2", "#f3ede1"),
    "vermilion": ("#b8261b", "#fbf4e8", "#141211", "#141211", "#fbf4e8", "#f3c9b8", "#3a0b07", "#f0b8a6", "#fbf4e8"),
    # the 5-star look with every red turned to gold
    "gilt": ("#141211", "#f3ede1", "#c9a03a", "#c9a03a", "#141211", "#9a9184", "#0d0c0b", "#b9b0a2", "#f3ede1"),
    # Grand Smashes in their host's flag colours
    "smash_china": ("#b8261b", "#fbf4e8", "#e2b64a", "#e2b64a", "#8a1a12", "#f3c9b8", "#3a0b07", "#f0b8a6", "#fbf4e8"),
    "smash_europe": ("#123a8c", "#f4f1e8", "#d9b04a", "#d9b04a", "#0c2a66", "#b9c7e6", "#071a40", "#a9bbe0", "#f4f1e8"),
    "smash_usa": ("#1b2a5c", "#ffffff", "#c8202f", "#c8202f", "#ffffff", "#b9c2dc", "#0c1430", "#b4bdd6", "#ffffff"),
    "smash_singapore": ("#d0202c", "#ffffff", "#ffffff", "#ffffff", "#d0202c", "#f6c4c6", "#4a0a0e", "#f3b3b6", "#ffffff"),
    "smash_singapore_low": ("#ffffff", "#d0202c", "#d0202c", "#d0202c", "#ffffff", "#c46a70", "#4a0a0e", "#f3b3b6", "#d0202c"),
}

SMASH_SCHEME = {"china": "smash_china", "united states": "smash_usa", "usa": "smash_usa", "singapore": "smash_singapore"}


def smash_scheme(ev):
    """China red and gold, Singapore red and white, United States red, white and blue; Europe Smash (wherever it is held) blue and gold."""
    key = (ev.get("country") or "").lower()
    if "europe" in (ev.get("id", "") + ev.get("name", "")).lower():
        return "smash_europe"
    return SMASH_SCHEME.get(key, "smash_europe")


def _seal(x, y, s, n, year, fill=CINNABAR, ink=PAPER):
    """A square seal: the stars over the year."""
    out = [f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{fill}"/>',
           f'<rect x="{x + 7}" y="{y + 7}" width="{s - 14}" height="{s - 14}" fill="none" stroke="{ink}" stroke-opacity=".7" stroke-width="1.5"/>',
           star_row(x + s / 2, y + s * .36, n, s * .13, ink, gap=1.25, anchor="middle")]
    out.append(t(str(year), x + s / 2, y + s * .78, s * .27, ink, 700, "middle", 0.02, stretch=85))
    return "".join(out)


def five_ink(ev, uid, scheme="paper"):
    BG, FG, AC, SEAL, SINK, LAB, PD, PL, FR = SCHEMES[scheme]
    photo = _photo(ev)
    defs, noise = grain(uid, .06, dark=scheme == "paper")
    head = type_name(ev).upper()
    city = ev["city"].upper()
    L, PX0, PX1 = 150, 930, W - 90
    hs = fit(head, (PX0 - L - 120) * .85, 84, 0.12)
    cs = fit(city, PX0 - L - 40, 200, -0.005)
    b = [f'<defs>{defs}{_mono(uid, PD, PL, contrast=.8)}<clipPath id="{uid}-p"><rect x="{PX0}" y="90" width="{PX1 - PX0}" height="{H - 180}"/></clipPath></defs>',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<g clip-path="url(#{uid}-p)"><image href="{P.photo_href(photo)}" x="{PX0}" y="90" width="{PX1 - PX0}" height="{H - 180}" preserveAspectRatio="xMidYMid slice" filter="url(#{uid}-mono)"/></g>',
         f'<rect x="{PX0}" y="90" width="{PX1 - PX0}" height="{H - 180}" fill="none" stroke="{FR}" stroke-width="1"/>',
         _enso(PX0 + 10, 560, 150, 30, AC),
         f'<line x1="96" y1="90" x2="96" y2="{H - 90}" stroke="{AC}" stroke-width="3"/>',
         # the full name, running down the margin
         f'<g transform="translate(70 90) rotate(90)">{t((ev.get("name", "") + " " + str(ev.get("year", ""))).upper(), 0, 0, 15, LAB, 600, track=0.42)}</g>']
    emb = emblem_kind(ev)
    top = 150
    if emb:
        b.append(laurel(L + 52, 170, 52, AC))
        top = 270
    b.append(star_row(L, top, stars(ev), 40, AC, gap=1.3))
    yh = top + 30 + hs * .73
    b.append(t(head, L, yh, hs, AC, 700, track=0.06, stretch=85))
    b.append(f'<rect x="{L}" y="{yh + 26:.0f}" width="64" height="2" fill="{FG}"/>')
    y2 = yh + 56 + cs * .73
    b.append(t(city, L - cs * .02, y2, cs, FG, 800, track=-0.005, stretch=75))
    yb = H - 210
    b.append(f'<rect x="{L}" y="{yb}" width="{PX0 - L - 60}" height="1" fill="{FG}" fill-opacity=".5"/>')
    b.append(label("Dates", L, yb + 42, LAB, 13, opacity=1))
    b.append(t(P.date_range(ev), L, yb + 76, 24, FG, 500))
    b.append(label("Venue", L + 330, yb + 42, LAB, 13, opacity=1))
    for j, ln in enumerate(P._wrap(P.place(ev), 22)[:2]):
        b.append(t(ln, L + 330, yb + 76 + j * 28, 24, FG, 500))
    b.append(_seal(PX1 - 150, H - 240, 120, stars(ev), ev.get("year", ""), SEAL, SINK))
    b.append(wordmark(PX1 - 18, 70, FG, 24))
    b.append(noise)
    return b


def square_ink(ev, uid, scheme="paper"):
    BG, FG, AC, SEAL, SINK, LAB, PD, PL, FR = SCHEMES[scheme]
    photo = _photo(ev)
    defs, noise = grain(uid, .06, dark=scheme == "paper")
    head = type_name(ev).upper()
    city = ev["city"].upper()
    L, R = 80, TW - 80
    PH = 430
    hs, cs = fit(head, R - L, 64, 0.12), fit(city, R - L, 180, -0.005)
    b = [f'<defs>{defs}{_mono(uid, PD, PL, contrast=.8)}<clipPath id="{uid}-p"><rect x="{L}" y="80" width="{R - L}" height="{PH}"/></clipPath></defs>',
         f'<rect width="{TW}" height="{TH}" fill="{BG}"/>',
         f'<g clip-path="url(#{uid}-p)"><image href="{P.photo_href(photo)}" x="{L}" y="80" width="{R - L}" height="{PH}" preserveAspectRatio="xMidYMid slice" filter="url(#{uid}-mono)"/></g>',
         f'<rect x="{L}" y="80" width="{R - L}" height="{PH}" fill="none" stroke="{FR}" stroke-width="1"/>',
         _enso(R - 90, 170, 80, 20, AC)]
    if emblem_kind(ev):
        b.append(laurel(L + 70, 80 + PH / 2, 52, "#f3ede1"))
    b.append(star_row(L, 80 + PH + 64, stars(ev), 32, AC, gap=1.3))
    y = 80 + PH + 84 + hs * .73
    b.append(t(head, L, y, hs, AC, 700, track=0.06, stretch=85))
    y2 = y + 30 + cs * .73
    b.append(t(city, L - cs * .02, y2, cs, FG, 800, track=-0.005, stretch=75))
    b.append(t(P.date_range(ev), L, y2 + 64, 30, FG, 500))
    b.append(label(P.place(ev), L, y2 + 104, LAB, 17, opacity=1))
    b.append(_seal(R - 116, TH - 196, 116, stars(ev), ev.get("year", ""), SEAL, SINK))
    b.append(noise)
    return b


def five_lacquer(ev, uid):
    return five_ink(ev, uid, "lacquer")


def square_lacquer(ev, uid):
    return square_ink(ev, uid, "lacquer")


def _flag_halves(fn, ev, uid, w, h):
    """Singapore's flag: the poster drawn twice, red over white, the top half of one over the bottom half of the other."""
    top, low = fn(ev, uid, "smash_singapore"), fn(ev, uid + "-lo", "smash_singapore_low")
    return [f'<defs><clipPath id="{uid}-top"><rect width="{w}" height="{h / 2}"/></clipPath><clipPath id="{uid}-low"><rect y="{h / 2}" width="{w}" height="{h / 2}"/></clipPath></defs>',
            f'<g clip-path="url(#{uid}-top)">{"".join(top)}</g>', f'<g clip-path="url(#{uid}-low)">{"".join(low)}</g>']


def five_vermilion(ev, uid):
    sc = smash_scheme(ev)
    return _flag_halves(five_ink, ev, uid, W, H) if sc == "smash_singapore" else five_ink(ev, uid, sc)


def square_vermilion(ev, uid):
    sc = smash_scheme(ev)
    return _flag_halves(square_ink, ev, uid, TW, TH) if sc == "smash_singapore" else square_ink(ev, uid, sc)


def five_gilt(ev, uid):
    return five_ink(ev, uid, "gilt")


def square_gilt(ev, uid):
    return square_ink(ev, uid, "gilt")
