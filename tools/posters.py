"""Eleven's own event posters: a consistent, professional identity for each tournament.

These are Eleven's designs, not imitations of any organiser's branding: Eleven's typeface, the
prestige-tier colours used on the schedule, and abstract table tennis geometry. The event's name
appears as plain text, which is fine; organisers' logos, marks and livery are never used.

Usage: python3 tools/posters.py            (writes img/posters/<event id>.svg for events in data/events.json)
"""
import html, json, math, os

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W, H = 1600, 900
FONT = "'Bricolage Grotesque', 'Arial Narrow', sans-serif"

# Colour by competition level, matching the schedule's prestige tiers
TIERS = {
    "world": ("#c8102e", "#7d0a1d"),        # World Championships, Olympics, World Cups
    "smash": ("#f37021", "#9a3b08"),        # Grand Smashes
    "champions": ("#2f5fd0", "#132a66"),    # WTT Champions and WTT Finals
    "continental": ("#0f7a65", "#063a30"),  # Asian, European, Pan American, African championships
    "star": ("#2aa198", "#0e4a46"),         # WTT Star Contender
    "contender": ("#5b6575", "#262c36"),    # WTT Contender
    "club": ("#23895c", "#0b3a26"),         # Club competitions
}


def _type(lines, x, y, size, fill, weight=800, stretch=75, anchor="start", spacing=-0.01, gap=0.92):
    out = []
    for i, line in enumerate(lines):
        out.append(f'<text x="{x}" y="{y + i * size * gap:.0f}" font-family="{FONT}" font-weight="{weight}" '
                   f'font-size="{size}" style="font-stretch:{stretch}%;font-variation-settings:\'wdth\' {stretch}" '
                   f'letter-spacing="{spacing}em" fill="{fill}" text-anchor="{anchor}">{e(line)}</text>')
    return "\n".join(out)


def _small(text, x, y, fill, size=26, weight=600, anchor="start", spacing=0.02, opacity=1):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-weight="{weight}" font-size="{size}" '
            f'letter-spacing="{spacing}em" fill="{fill}" fill-opacity="{opacity}" text-anchor="{anchor}">{e(text)}</text>')


def _wordmark(x, y, fill, size=30):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-weight="800" font-size="{size}" fill="{fill}" text-anchor="end">Eleven</text>'
            f'<circle cx="{x + size * 0.22}" cy="{y - size * 0.62}" r="{size * 0.14}" fill="#f37021"/>')


def _fit(lines, width, cap):
    """Size condensed heavy type to fill a given width (about 0.34em per character at 75% width)."""
    longest = max(len(l) for l in lines)
    return int(min(cap, width / (0.34 * longest)))


def swiss(ev):
    """A: flat colour field, monumental condensed type, ball and flight path, information grid."""
    c, dark = TIERS[ev["tier"]]
    size = _fit(ev["title"] + [ev["year"]], 1100, 270)
    b = [f'<rect width="{W}" height="{H}" fill="{c}"/>']
    b.append(f'<rect x="0" y="{H - 230}" width="{W}" height="230" fill="{dark}" fill-opacity=".28"/>')
    b.append(f'<path d="M1180 640 Q1280 330 1370 470 Q1420 300 1462 270" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="3" stroke-dasharray="2 13" stroke-linecap="round"/>')
    b.append(f'<circle cx="1470" cy="200" r="64" fill="#fff"/>')
    b.append(f'<path d="M1426 176 A52 52 0 0 1 1478 146" fill="none" stroke="{c}" stroke-opacity=".3" stroke-width="5" stroke-linecap="round"/>')
    b.append(_small(ev["series"], 96, 142, "#fff", 36, 700, spacing=0.03))
    b.append(f'<rect x="96" y="166" width="72" height="6" fill="#fff"/>')
    b.append(_type(ev["title"], 84, 168 + size * 0.86, size, "#fff", gap=0.86))
    b.append(_type([ev["year"]], 84, 168 + size * 0.86 * (len(ev["title"]) + 1), size, dark, gap=0.86))
    cols = [("Dates", ev["dates"]), ("Venue", ev["venue"]), ("Events", ev["events"])]
    for i, (k, v) in enumerate(cols):
        x = 96 + i * 420
        b.append(_small(k, x, H - 140, "#fff", 22, 600, opacity=.7))
        b.append(_small(v, x, H - 94, "#fff", 32, 700))
    b.append(_wordmark(W - 96, H - 94, "#fff", 30))
    return b


def arena(ev):
    """B: night arena, one sweeping arc in the tier colour below the type, ghosted year."""
    c, dark = TIERS[ev["tier"]]
    size = _fit(ev["title"], 1100, 300)
    b = [f'<rect width="{W}" height="{H}" fill="#0b0f15"/>']
    for r, op in ((700, .05), (500, .06), (320, .08)):
        b.append(f'<circle cx="1260" cy="420" r="{r}" fill="{c}" fill-opacity="{op}"/>')
    b.append(_type([ev["year"]], W - 60, H - 40, 440, "none", 800, 75, "end", -0.03).replace('fill="none"', 'fill="none" stroke="#ffffff" stroke-opacity=".08" stroke-width="2"'))
    b.append(f'<path d="M-40 870 C 700 870, 1180 800, 1660 420" fill="none" stroke="{c}" stroke-width="22" stroke-linecap="round"/>')
    b.append(f'<circle cx="1487" cy="544" r="40" fill="#fff"/>')
    b.append(f'<rect x="96" y="110" width="72" height="6" fill="{c}"/>')
    b.append(_small(ev["series"], 96, 170, "#fff", 36, 700, spacing=0.03, opacity=.9))
    b.append(_type(ev["title"], 84, 190 + size * 0.86, size, "#fff", gap=0.86))
    y = 190 + size * 0.86 * len(ev["title"]) + 40
    b.append(_small(ev["dates"], 96, y + 30, "#fff", 40, 700))
    b.append(_small(f'{ev["venue"]}  /  {ev["events"]}', 96, y + 80, "#fff", 26, 500, opacity=.65))
    b.append(_wordmark(W - 96, 170, "#fff"))
    return b


def court(ev):
    """C: type on a dark field, the table from above cropped hard on the right."""
    c, dark = TIERS[ev["tier"]]
    size = _fit(ev["title"], 760, 280)
    b = [f'<rect width="{W}" height="{H}" fill="#0b0f15"/>']
    b.append(f'<g transform="rotate(-14 1300 400)">')
    b.append(f'<rect x="980" y="-120" width="900" height="1100" fill="{c}"/>')
    b.append(f'<rect x="1000" y="-100" width="860" height="1060" fill="none" stroke="#fff" stroke-width="10"/>')
    b.append(f'<line x1="1430" y1="-100" x2="1430" y2="960" stroke="#fff" stroke-width="4"/>')
    b.append(f'<rect x="960" y="430" width="940" height="26" fill="{dark}"/>')
    b.append(f'<rect x="960" y="424" width="940" height="8" fill="#fff"/>')
    b.append("</g>")
    b.append(f'<circle cx="1300" cy="250" r="38" fill="#fff"/>')
    b.append(f'<rect x="96" y="110" width="72" height="6" fill="{c}"/>')
    b.append(_small(ev["series"], 96, 170, "#fff", 36, 700, spacing=0.03))
    b.append(_type(ev["title"], 84, 190 + size * 0.86, size, "#fff", gap=0.86))
    for i, (k, v) in enumerate((("Dates", ev["dates"]), ("Venue", ev["venue"]), ("Events", ev["events"]))):
        b.append(_small(k, 96, H - 290 + i * 92, "#fff", 20, 600, opacity=.6))
        b.append(_small(v, 96, H - 254 + i * 92, "#fff", 30, 700))
    b.append(_wordmark(W - 96, H - 70, "#fff", 28))
    return b


STYLES = {"swiss": swiss, "arena": arena, "court": court}


def svg(ev, style):
    body = "\n".join(STYLES[style](ev))
    label = f'{ev["series"]} {" ".join(ev["title"])} poster by Eleven'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{e(label)}">\n{body}\n</svg>\n')


def main():
    path = os.path.join(ROOT, "data", "events.json")
    if not os.path.exists(path):
        return
    data = json.load(open(path, encoding="utf-8"))
    out = os.path.join(ROOT, "img", "posters")
    os.makedirs(out, exist_ok=True)
    for ev in data["events"]:
        open(os.path.join(out, f'{ev["id"]}.svg'), "w", encoding="utf-8").write(svg(ev, data.get("style", "swiss")))
    print(f'posters: {len(data["events"])}')


if __name__ == "__main__":
    main()
