"""Cover images for features: one big number or phrase in Eleven's poster style.

Each feature in data/articles/ with "category": "Features" can have
    "cover": {"stat": "1 in 4", "label": "of the world's top 100 learned the game in China", "colour": "#3a66e0"}
Usage: python3 tools/feature_cover.py <slug> [<slug> ...]   (writes img/features/<slug>.jpg; needs Playwright)
"""
import base64, html, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
e = html.escape
W, H = 1600, 900


def svg(a):
    c = a.get("cover") or {}
    colour = c.get("colour", "#3a66e0")
    stat, label, kind = c.get("stat", ""), c.get("label", a["title"]), a.get("kind", "Feature")
    size = 330 if len(stat) <= 4 else 250 if len(stat) <= 7 else 170
    words, lines = label.split(), [""]
    for w in words:   # wrap the label at roughly 30 characters
        if len(lines[-1]) + len(w) > 30 and lines[-1]:
            lines.append(w)
        else:
            lines[-1] = (lines[-1] + " " + w).strip()
    font = "'Bricolage Grotesque', sans-serif"
    label_svg = "".join(f'<text x="96" y="{620 + i * 58}" font-family="{font}" font-size="48" font-weight="600" fill="#121417">{e(l)}</text>' for i, l in enumerate(lines[:4]))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
<defs><linearGradient id="f" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff5a1f"/><stop offset="1" stop-color="#ffb81c"/></linearGradient></defs>
<rect width="{W}" height="{H}" fill="#f3f1ec"/>
<rect x="1180" y="0" width="420" height="{H}" fill="{colour}"/>
<circle cx="1180" cy="{H}" r="300" fill="none" stroke="url(#f)" stroke-width="34"/>
<circle cx="1390" cy="230" r="110" fill="url(#f)"/>
<rect x="1180" y="0" width="10" height="{H}" fill="#ff5a1f"/>
<rect x="96" y="96" width="40" height="8" fill="#ff5a1f"/><rect x="136" y="96" width="40" height="8" fill="{colour}"/>
<text x="96" y="150" font-family="{font}" font-size="22" font-weight="700" letter-spacing="4" fill="#121417">{e(kind.upper())} · ELEVEN</text>
<rect x="96" y="172" width="1000" height="2" fill="#121417"/>
<text x="84" y="{200 + size * 0.78:.0f}" font-family="{font}" font-size="{size}" font-weight="800" style="font-stretch:75%;font-variation-settings:'wdth' 75" fill="#121417">{e(stat)}</text>
{label_svg}
<text x="1504" y="840" font-family="{font}" font-size="30" font-weight="800" fill="#fff" text-anchor="end">Eleven</text>
</svg>"""


def main(slugs):
    from playwright.sync_api import sync_playwright
    font = base64.b64encode(open(os.path.join(ROOT, "tools", "BricolageGrotesque-variable.woff2"), "rb").read()).decode()
    css = f"@font-face{{font-family:'Bricolage Grotesque';src:url(data:font/woff2;base64,{font}) format('woff2');font-weight:200 800;font-stretch:75% 100%}}html,body{{margin:0}}svg{{display:block;width:{W}px;height:{H}px}}"
    os.makedirs(os.path.join(ROOT, "img", "features"), exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        for slug in slugs:
            a = json.load(open(os.path.join(ROOT, "data", "articles", f"{slug}.json"), encoding="utf-8"))
            pg.set_content(f"<html><head><style>{css}</style></head><body>{svg(a)}</body></html>")
            pg.evaluate("document.fonts.ready.then(() => 1)")
            pg.wait_for_timeout(300)
            pg.screenshot(path=os.path.join(ROOT, "img", "features", f"{slug}.jpg"), type="jpeg", quality=86)
            print("cover:", slug)
        b.close()


if __name__ == "__main__":
    main(sys.argv[1:])
