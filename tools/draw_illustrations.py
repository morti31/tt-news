"""Generates the line-art illustrations for Eleven. All strokes use currentColor so they follow light/dark mode."""
import math, random, os

OUT = os.path.join(os.path.dirname(__file__), "..", "img", "cartoons")
W = 'stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"'


def svg(name, label, body, defs=""):
    s = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360" role="img" aria-label="{label}">
<defs>{defs}</defs>
<g {W} stroke-width="1.3">
{body}
</g>
</svg>
'''
    open(os.path.join(OUT, name + ".svg"), "w").write(s)


def hatch(pid, gap=4, angle=45, width=0.6):
    return (f'<pattern id="{pid}" width="{gap}" height="{gap}" patternUnits="userSpaceOnUse" patternTransform="rotate({angle})">'
            f'<line x1="0" y1="0" x2="0" y2="{gap}" stroke="currentColor" stroke-width="{width}"/></pattern>')


def table(x0=120, y0=300, length=400, depth_dx=20, depth_dy=14, legs=True):
    """A table seen from its long side, slightly from above."""
    x1 = x0 + length
    a, b = (x0 + depth_dx, y0), (x1 + depth_dx, y0)
    c, d = (x1, y0 + depth_dy), (x0, y0 + depth_dy)
    out = [f'<path d="M{a[0]} {a[1]} L{b[0]} {b[1]} L{c[0]} {c[1]} L{d[0]} {d[1]} Z" fill="var(--art-bg, #fff)" stroke-width="1.6"/>']
    # white line border inset and centre line
    out.append(f'<path d="M{a[0]+4} {a[1]+1.5} L{b[0]-4} {b[1]+1.5} L{c[0]-3} {c[1]-1.5} L{d[0]+3} {d[1]-1.5} Z" stroke-width=".6"/>')
    out.append(f'<line x1="{a[0]+4}" y1="{y0+depth_dy/2}" x2="{b[0]-4}" y2="{y0+depth_dy/2}" stroke-width=".5" transform="translate({-depth_dx/2} 0)"/>')
    # apron
    out.append(f'<path d="M{d[0]} {d[1]} L{c[0]} {c[1]} L{c[0]} {c[1]+5} L{d[0]} {d[1]+5} Z" fill="currentColor" stroke-width="1"/>')
    # net, edge-on across the depth
    mx = x0 + length / 2
    nb1, nb2 = (mx + depth_dx, y0), (mx, y0 + depth_dy)
    h = 13
    out.append(f'<path d="M{nb1[0]} {nb1[1]} L{nb1[0]} {nb1[1]-h} L{nb2[0]} {nb2[1]-h} L{nb2[0]} {nb2[1]}" stroke-width="1.2"/>')
    for i in range(1, 6):
        t = i / 6
        px, py = nb1[0] + (nb2[0] - nb1[0]) * t, nb1[1] + (nb2[1] - nb1[1]) * t
        out.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{py-h:.1f}" stroke-width=".4"/>')
    if legs:
        for lx in (x0 + 40, x1 - 40):
            out.append(f'<path d="M{lx-10} {y0+depth_dy+5} L{lx-14} {y0+depth_dy+44} M{lx+10} {y0+depth_dy+5} L{lx+14} {y0+depth_dy+44}" stroke-width="1.4"/>')
        out.append(f'<line x1="{x0+30}" y1="{y0+depth_dy+28}" x2="{x0+50}" y2="{y0+depth_dy+28}" stroke-width=".8"/>')
        out.append(f'<line x1="{x1-50}" y1="{y0+depth_dy+28}" x2="{x1-30}" y2="{y0+depth_dy+28}" stroke-width=".8"/>')
    return "\n".join(out)


def ball(cx, cy, r=5.5, arc_from=None):
    out = []
    if arc_from:
        fx, fy = arc_from
        qx, qy = (fx + cx) / 2, min(fy, cy) - 46
        out.append(f'<path d="M{fx} {fy} Q{qx} {qy} {cx} {cy}" stroke-width=".8" stroke-dasharray="1 5"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="var(--art-bg, #fff)" stroke-width="1.3"/>')
    out.append(f'<path d="M{cx-r*.5} {cy-r*.15} A{r*.6} {r*.6} 0 0 1 {cx+r*.2} {cy-r*.55}" stroke-width=".5"/>')
    return "\n".join(out)


def windows_grid(x, y, w, h, cols, rows, pad=6, sash=True):
    out = []
    cw, rh = (w - pad * (cols + 1)) / cols, (h - pad * (rows + 1)) / rows
    for i in range(cols):
        for j in range(rows):
            wx, wy = x + pad + i * (cw + pad), y + pad + j * (rh + pad)
            out.append(f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{cw:.1f}" height="{rh:.1f}" stroke-width=".7"/>')
            if sash:
                out.append(f'<line x1="{wx:.1f}" y1="{wy+rh/2:.1f}" x2="{wx+cw:.1f}" y2="{wy+rh/2:.1f}" stroke-width=".4"/>')
    return "\n".join(out)


# ---------------------------------------------------------------- Houston
def houston():
    random.seed(3)
    defs = (hatch("hou-h", 3.2, 0, .45) + hatch("hou-d", 3, 45, .5) +
            '<pattern id="hou-v" width="5" height="8" patternUnits="userSpaceOnUse"><line x1="2.5" y1="0" x2="2.5" y2="8" stroke="currentColor" stroke-width=".45"/></pattern>')
    b = []
    ground = 262
    towers = [  # x, width, top, kind
        (40, 44, 170, "flat"), (88, 30, 120, "spire"), (124, 52, 92, "gothic"), (182, 38, 140, "flat"),
        (226, 60, 64, "slant"), (292, 34, 150, "flat"), (332, 46, 104, "stepped"), (384, 30, 176, "flat"),
        (420, 50, 128, "gothic"), (476, 36, 188, "flat"), (518, 64, 150, "flat"), (588, 34, 200, "flat"),
    ]
    for x, w, top, kind in towers:
        fill = random.choice(["url(#hou-v)", "url(#hou-h)", "var(--art-bg, #fff)"])
        if kind == "slant":
            b.append(f'<path d="M{x} {ground} L{x} {top+28} L{x+w} {top} L{x+w} {ground} Z" fill="{fill}"/>')
        elif kind == "spire":
            b.append(f'<path d="M{x} {ground} L{x} {top} L{x+w/2} {top-34} L{x+w} {top} L{x+w} {ground} Z" fill="{fill}"/>')
            b.append(f'<line x1="{x+w/2}" y1="{top-34}" x2="{x+w/2}" y2="{top-54}" stroke-width=".8"/>')
        elif kind == "gothic":
            steps = [(0, 0), (6, -14), (12, -24), (w / 2, -40), (w - 12, -24), (w - 6, -14), (w, 0)]
            pts = " ".join(f"L{x+dx} {top+dy}" for dx, dy in steps)
            b.append(f'<path d="M{x} {ground} {pts} L{x+w} {ground} Z" fill="{fill}"/>')
        elif kind == "stepped":
            b.append(f'<path d="M{x} {ground} L{x} {top+20} L{x+8} {top+20} L{x+8} {top+8} L{x+16} {top+8} L{x+16} {top} L{x+w-16} {top} L{x+w-16} {top+8} L{x+w-8} {top+8} L{x+w-8} {top+20} L{x+w} {top+20} L{x+w} {ground} Z" fill="{fill}"/>')
        else:
            b.append(f'<rect x="{x}" y="{top}" width="{w}" height="{ground-top}" fill="{fill}"/>')
    b.append(f'<line x1="0" y1="{ground}" x2="640" y2="{ground}" stroke-width="1.4"/>')
    # sun disc low on the horizon, hatched
    b.insert(0, '<circle cx="520" cy="96" r="38" fill="url(#hou-d)" stroke-width=".8"/>')
    # freeway in front
    b.append('<path d="M0 278 L640 278 M0 284 L640 284" stroke-width=".8"/>')
    for x in range(10, 640, 46):
        b.append(f'<line x1="{x}" y1="284" x2="{x}" y2="300" stroke-width=".8"/>')
    b.append(table(120, 300, 400))
    b.append(ball(446, 276, arc_from=(196, 294)))
    svg("houston", "Line drawing of the Houston skyline with a table tennis table in the foreground", "\n".join(b), defs)


# ---------------------------------------------------------------- Wellingborough
def wellingborough():
    defs = hatch("wel-r", 3, 0, .5) + hatch("wel-s", 2.6, 0, .5) + hatch("wel-b", 4, 90, .35)
    b = []
    ground = 262
    # spire
    b.append(f'<rect x="296" y="128" width="48" height="{ground-128}" fill="url(#wel-b)"/>')
    b.append('<path d="M292 130 L320 22 L348 130 Z" fill="url(#wel-s)"/>')
    b.append('<path d="M314 52 L320 46 L326 52 L326 64 L314 64 Z" stroke-width=".7" fill="var(--art-bg, #fff)"/>')
    b.append('<path d="M310 170 Q320 156 330 170 L330 200 L310 200 Z" fill="currentColor"/>')
    b.append('<line x1="296" y1="140" x2="344" y2="140" stroke-width=".7"/>')
    # terraces
    houses_l = [(0, 160), (72, 150), (144, 164), (216, 156)]
    houses_r = [(344, 156), (416, 166), (488, 150), (560, 160)]
    for x, top in houses_l + houses_r:
        w = 72 if x not in (216, 344) else 80
        if x == 216: w = 80
        b.append(f'<rect x="{x}" y="{top}" width="{w}" height="{ground-top}" fill="var(--art-bg, #fff)"/>')
        b.append(f'<path d="M{x-3} {top} L{x+w/2} {top-32} L{x+w+3} {top} Z" fill="url(#wel-r)"/>')
        b.append(f'<rect x="{x+w-22}" y="{top-34}" width="10" height="18" fill="var(--art-bg, #fff)"/>')
        b.append(windows_grid(x + 6, top + 10, w - 12, 44, 2, 1, pad=8))
        b.append(f'<rect x="{x+w/2-9}" y="{ground-42}" width="18" height="42" fill="currentColor"/>')
        b.append(f'<path d="M{x+w/2-11} {ground-44} L{x+w/2+11} {ground-44}" stroke-width="1"/>')
        b.append(windows_grid(x + 6, ground - 44, w / 2 - 18, 36, 1, 1, pad=0))
    # chimneys smoke-free; bunting as a fine line with small pennants
    b.append('<path d="M0 108 Q150 140 292 112" stroke-width=".6"/>')
    b.append('<path d="M348 112 Q500 144 640 106" stroke-width=".6"/>')
    for x, y in [(24, 114), (64, 122), (104, 128), (144, 131), (184, 130), (224, 125), (264, 118), (376, 118), (416, 126), (456, 131), (496, 132), (536, 128), (576, 120), (616, 111)]:
        b.append(f'<path d="M{x-5} {y} L{x} {y+10} L{x+5} {y}" stroke-width=".6" fill="var(--art-bg, #fff)"/>')
    b.append(f'<line x1="0" y1="{ground}" x2="640" y2="{ground}" stroke-width="1.4"/>')
    b.append('<path d="M0 268 L640 268" stroke-width=".5"/>')
    b.append(table(120, 300, 400))
    # two trophies on the table
    for tx in (220, 420):
        b.append(f'<path d="M{tx-9} 278 L{tx+9} 278 Q{tx+9} 292 {tx} 294 Q{tx-9} 292 {tx-9} 278 Z" fill="var(--art-bg, #fff)" stroke-width="1.1"/>')
        b.append(f'<path d="M{tx-9} 281 Q{tx-15} 281 {tx-14} 286 Q{tx-13} 290 {tx-7} 290 M{tx+9} 281 Q{tx+15} 281 {tx+14} 286 Q{tx+13} 290 {tx+7} 290" stroke-width=".8"/>')
        b.append(f'<path d="M{tx-2} 294 L{tx+2} 294 L{tx+3} 300 L{tx-3} 300 Z M{tx-7} 300 L{tx+7} 300" stroke-width="1"/>')
    svg("wellingborough", "Line drawing of a Wellingborough street with terraced houses and a church spire, with two trophies on a table tennis table", "\n".join(b), defs)


# ---------------------------------------------------------------- Montpellier
def montpellier():
    defs = hatch("mon-r", 3, 0, .5) + hatch("mon-d", 3, 45, .5) + hatch("mon-v", 3.4, 90, .45)
    b = []
    ground = 262
    # Opéra Comédie: base arcade, columned upper storey, attic with statues
    x0, x1 = 150, 490
    b.append(f'<rect x="{x0}" y="96" width="{x1-x0}" height="{ground-96}" fill="var(--art-bg, #fff)" stroke-width="1.4"/>')
    b.append(f'<rect x="{x0-6}" y="88" width="{x1-x0+12}" height="8" fill="url(#mon-r)"/>')
    b.append(f'<path d="M{x0+40} 88 L{x0+40} 70 L{x1-40} 70 L{x1-40} 88" fill="url(#mon-v)"/>')
    for i in range(9):  # statues on the attic
        sx = x0 + 52 + i * ((x1 - x0 - 104) / 8)
        b.append(f'<path d="M{sx} 70 L{sx} 58 M{sx-2.5} 60 L{sx+2.5} 60" stroke-width="1.1"/><circle cx="{sx}" cy="55" r="2" fill="currentColor"/>')
    # cornice line between storeys
    b.append(f'<line x1="{x0}" y1="188" x2="{x1}" y2="188" stroke-width="1.2"/><line x1="{x0}" y1="192" x2="{x1}" y2="192" stroke-width=".6"/>')
    # upper storey columns and windows
    cols = 9
    step = (x1 - x0 - 20) / (cols - 1)
    for i in range(cols):
        cx = x0 + 10 + i * step
        b.append(f'<line x1="{cx-3}" y1="104" x2="{cx-3}" y2="184" stroke-width=".9"/><line x1="{cx+3}" y1="104" x2="{cx+3}" y2="184" stroke-width=".9"/>')
        b.append(f'<rect x="{cx-6}" y="100" width="12" height="4" stroke-width=".7"/>')
        if i < cols - 1:
            wx = cx + step / 2
            b.append(f'<path d="M{wx-9} 176 L{wx-9} 128 Q{wx} 116 {wx+9} 128 L{wx+9} 176 Z" fill="url(#mon-v)" stroke-width=".8"/>')
    # ground-floor arcade
    arches = 7
    aw = (x1 - x0) / arches
    for i in range(arches):
        ax = x0 + i * aw
        b.append(f'<path d="M{ax+8} {ground} L{ax+8} 224 Q{ax+aw/2} 200 {ax+aw-8} 224 L{ax+aw-8} {ground}" fill="url(#mon-d)" stroke-width="1"/>')
    # flanking buildings with shutters
    for x, w in ((0, 140), (500, 140)):
        b.append(f'<rect x="{x}" y="128" width="{w}" height="{ground-128}" fill="var(--art-bg, #fff)"/>')
        b.append(f'<line x1="{x}" y1="124" x2="{x+w}" y2="124" stroke-width="1.2"/>')
        b.append(windows_grid(x + 6, 140, w - 12, 100, 3, 2, pad=12, sash=False))
    b.append(f'<line x1="0" y1="{ground}" x2="640" y2="{ground}" stroke-width="1.4"/>')
    # fountain: basin, pedestal, water
    fx = 572
    b.append(f'<ellipse cx="{fx}" cy="300" rx="46" ry="9" fill="var(--art-bg, #fff)" stroke-width="1.2"/>')
    b.append(f'<path d="M{fx-46} 300 L{fx-44} 310 Q{fx} 322 {fx+44} 310 L{fx+46} 300" stroke-width="1.2"/>')
    b.append(f'<rect x="{fx-6}" y="244" width="12" height="54" fill="url(#mon-r)" stroke-width="1"/>')
    b.append(f'<ellipse cx="{fx}" cy="244" rx="20" ry="5" fill="var(--art-bg, #fff)"/>')
    b.append(f'<path d="M{fx} 239 Q{fx-14} 216 {fx-24} 246 M{fx} 239 Q{fx+14} 216 {fx+24} 246 M{fx} 239 L{fx} 222" stroke-width=".7" stroke-dasharray="2 2"/>')
    b.append(table(60, 300, 400))
    svg("montpellier", "Line drawing of the Opéra Comédie in Montpellier with a fountain, a table tennis table and an empty chair", "\n".join(b), defs)


# ---------------------------------------------------------------- Dimpled ball, as a technical drawing
def dimpled():
    b = []
    cx, cy, r = 230, 176, 112
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="var(--art-bg, #fff)" stroke-width="1.6"/>')
    # dimples: points on the visible hemisphere, orthographic projection, tilted
    tilt = math.radians(20)
    for lat_deg in range(-75, 90, 15):
        lat = math.radians(lat_deg)
        n = max(1, int(round(24 * math.cos(lat))))
        for k in range(n):
            lon = 2 * math.pi * k / n + (0.13 if lat_deg % 30 else 0)
            x, y, z = math.cos(lat) * math.sin(lon), math.sin(lat), math.cos(lat) * math.cos(lon)
            y, z = y * math.cos(tilt) - z * math.sin(tilt), y * math.sin(tilt) + z * math.cos(tilt)
            if z < 0.12:
                continue
            px, py = cx + x * r, cy - y * r
            dr = 7.2
            ang = math.degrees(math.atan2(-y, x))
            b.append(f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="{dr*z:.2f}" ry="{dr:.2f}" transform="rotate({ang:.1f} {px:.1f} {py:.1f})" stroke-width=".6"/>')
    # centre lines
    b.append(f'<path d="M{cx-r-18} {cy} L{cx+r+18} {cy} M{cx} {cy-r-18} L{cx} {cy+r+18}" stroke-width=".5" stroke-dasharray="10 3 2 3"/>')
    # dimension line
    y = cy + r + 34
    b.append(f'<path d="M{cx-r} {cy+r-40} L{cx-r} {y+6} M{cx+r} {cy+r-40} L{cx+r} {y+6}" stroke-width=".5"/>')
    b.append(f'<path d="M{cx-r+8} {y-4} L{cx-r} {y} L{cx-r+8} {y+4} M{cx-r} {y} L{cx+r} {y} M{cx+r-8} {y-4} L{cx+r} {y} L{cx+r-8} {y+4}" stroke-width=".7"/>')
    b.append(f'<text x="{cx}" y="{y-6}" text-anchor="middle" font-family="Figtree, system-ui, sans-serif" font-size="11" fill="currentColor" stroke="none" letter-spacing=".04em">40 mm</text>')
    # standard ball for comparison, and section view
    sx, sy, sr = 500, 150, 56
    b.append(f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="var(--art-bg, #fff)" stroke-width="1.3"/>')
    b.append(f'<path d="M{sx-sr*.55} {sy-sr*.1} A{sr*.6} {sr*.6} 0 0 1 {sx+sr*.1} {sy-sr*.55}" stroke-width=".5"/>')
    b.append(f'<path d="M{sx-sr} {sy} L{sx+sr} {sy}" stroke-width=".5" stroke-dasharray="10 3 2 3"/>')
    b.append(f'<text x="{sx}" y="{sy+sr+22}" text-anchor="middle" font-family="Figtree, system-ui, sans-serif" font-size="11" fill="currentColor" stroke="none">Standard ball</text>')
    b.append(f'<text x="{cx}" y="{cy-r-24}" text-anchor="middle" font-family="Figtree, system-ui, sans-serif" font-size="11" fill="currentColor" stroke="none">Dimpled concept</text>')
    svg("dimpled-ball", "Technical line drawing comparing a dimpled table tennis ball with a standard ball", "\n".join(b))


houston(); wellingborough(); montpellier(); dimpled()
print("done")
