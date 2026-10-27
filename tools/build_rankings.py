"""The rankings page: the official ITTF top 100, men and women side by side at equal weight.

Called from build_site.py. Input: data/rankings.json (from tools/rankings.py). Output: the page body.
"""
import html, json, os
import components

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load():
    path = os.path.join(ROOT, "data", "rankings.json")
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


def body(R, items):
    """items: (published, url, text) for every story and article, newest first, to link players to news."""

    def story(name):
        return next((u for _, u, txt in items if name in txt), None)

    def move(p):
        if p["prev"] is None:
            return '<span class="mv new">New</span>'
        d = p["prev"] - p["rank"]
        if d > 0:
            return f'<span class="mv up" aria-label="up {d}">▲{d}</span>'
        if d < 0:
            return f'<span class="mv down" aria-label="down {-d}">▼{-d}</span>'
        return '<span class="mv same" aria-label="no change">–</span>'

    def who(p):
        u = story(p["name"])
        n = f'<a href="{u}">{e(p["name"])}</a>' if u else e(p["name"])
        return f'{components.flag(p["nat"])}<span class="rk-name">{n}</span><span class="rk-nat">{e(p["nat"])}</span>'

    def table(key, title):
        top = R[key][0]["points"] or 1
        rows = "".join(
            f'<tr data-q="{e((p["name"] + " " + p["nat"]).lower())}"><td class="rk-pos">{p["rank"]}</td><td class="rk-mv">{move(p)}</td>'
            f'<td><span class="rk-player">{who(p)}</span></td><td class="rk-pts">{p["points"]:,}<span class="rk-bar" style="width:{100 * p["points"] / top:.1f}%"></span></td></tr>'
            for p in R[key])
        return (f'<section class="panel rk-list" data-g="{key}"><h2 class="panel-title">{title}</h2>'
                f'<table class="rk-table"><thead><tr><th scope="col">Rank</th><th scope="col"><span class="sr-only">Movement</span></th>'
                f'<th scope="col">Player</th><th scope="col">Points</th></tr></thead><tbody>{rows}</tbody></table></section>')

    def leader(key, title):
        p = R[key][0]
        return (f'<div class="rk-leader"><p class="small-label">{title}</p><p class="rk-leader-name">{who(p)}</p>'
                f'<p class="rk-leader-pts"><b>{p["points"]:,}</b> points</p></div>')

    def listing(players, empty):
        li = "".join(f'<li><span class="rk-now">{p["rank"]}</span><span class="rk-who">{who(p)}</span>{move(p)}</li>' for p in players)
        return f'<ul class="rk-movers">{li or f"<li>{empty}</li>"}</ul>'

    def climbers(key):
        ups = sorted((p for p in R[key] if p["prev"] and p["prev"] > p["rank"]), key=lambda p: (p["rank"] - p["prev"], p["rank"]))[:3]
        return listing(ups, "No climbers this week")

    def home(key):
        return listing([p for p in R[key] if p["nat"] in ("ENG", "SCO", "WAL")], "None in the top 100")

    label = R["label"]
    return f"""<main class="wrap rk">
<section class="sched-head"><div><h1>World rankings</h1>
<p class="lede">The official {e(label)}: the top 100 men and women, with ranking points and this week's movement.</p></div></section>
<div class="rk-two rk-leaders">{leader("men", "Men's world No. 1")}{leader("women", "Women's world No. 1")}</div>
<div class="rk-two">
  <section class="panel"><h2 class="panel-title">Biggest climbers</h2><div class="rk-two rk-inner"><div><h3>Men</h3>{climbers("men")}</div><div><h3>Women</h3>{climbers("women")}</div></div></section>
  <section class="panel"><h2 class="panel-title">Home nations in the top 100</h2><div class="rk-two rk-inner"><div><h3>Men</h3>{home("men")}</div><div><h3>Women</h3>{home("women")}</div></div></section>
</div>
<div class="rk-tools">
  <label class="rk-search"><span class="sr-only">Find a player or country</span><input id="rk-q" type="search" placeholder="Find a player or country, e.g. ENG" autocomplete="off"></label>
  <div class="toggle rk-toggle" role="group" aria-label="Show"><button data-g="men" aria-pressed="true">Men</button><button data-g="women" aria-pressed="false">Women</button></div>
</div>
<div class="rk-two rk-tables">{table("men", "Men's singles")}{table("women", "Women's singles")}</div>
<p class="small">Source: <a href="{e(R["url"])}" rel="noopener">ITTF world ranking on World Table Tennis</a>. Player names link to their latest story on Eleven.</p>
</main>
<script>
(function () {{
  const q = document.getElementById("rk-q");
  q.addEventListener("input", () => {{
    const v = q.value.trim().toLowerCase();
    document.querySelectorAll(".rk-table tbody tr").forEach((tr) => {{ tr.hidden = !!v && !tr.dataset.q.includes(v); }});
  }});
  const t = document.querySelector(".rk-toggle");
  t.addEventListener("click", (ev) => {{
    const b = ev.target.closest("button"); if (!b) return;
    t.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    document.querySelectorAll(".rk-list").forEach((s) => s.classList.toggle("rk-off", s.dataset.g !== b.dataset.g));
  }});
  document.querySelector('.rk-list[data-g="women"]').classList.add("rk-off");
}})();
</script>"""
