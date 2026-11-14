"""The rankings page: the official ITTF top 400, women and men on tabs.

Called from build_site.py. Input: data/rankings.json (from tools/rankings.py). Output: the page body.
"""
import html, json, os
import components
import ranking_moves

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load():
    path = os.path.join(ROOT, "data", "rankings.json")
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


def body(R, items, links=None):
    """items: (published, url, text) for every story and article, newest first, to link players to news."""

    links = links or {"p": {}, "c": {}}
    import unicodedata
    def norm(n):
        return "".join(ch for ch in unicodedata.normalize("NFKD", n) if ch.isalnum()).lower()
    loose = {norm(k): v for k, v in links["p"].items()}   # profile names can differ from WTT's spelling in case or accents

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
        u, cu = links["p"].get(p["name"]) or loose.get(norm(p["name"])), links["c"].get(p["nat"])
        n = f'<a href="{u}">{e(p["name"])}</a>' if u else e(p["name"])
        nat = f'<a href="{cu}">{e(p["nat"])}</a>' if cu else e(p["nat"])
        return f'{components.flag(p["nat"])}<span class="rk-name">{n}</span><span class="rk-nat">{nat}</span>'

    def table(key, title):
        top = R[key][0]["points"] or 1
        rows = "".join(
            f'<tr data-q="{e((p["name"] + " " + p["nat"]).lower())}"><td class="rk-pos">{p["rank"]}</td><td class="rk-mv">{move(p)}</td>'
            f'<td><span class="rk-player">{who(p)}</span></td><td class="rk-pts">{p["points"]:,}<span class="rk-bar" style="width:{100 * p["points"] / top:.1f}%"></span></td></tr>'
            for p in R[key])
        return (f'<section class="panel rk-list" data-g="{key}"><h3 class="panel-title">{title}</h3>'
                f'<table class="rk-table"><thead><tr><th scope="col">Rank</th><th scope="col"><span class="sr-only">Movement</span></th>'
                f'<th scope="col">Player</th><th scope="col">Points</th></tr></thead><tbody data-page="50">{rows}</tbody></table></section>')

    def leader(key, title):
        p = R[key][0]
        return (f'<div class="rk-leader"><p class="small-label">{title}</p><p class="rk-leader-name">{who(p)}</p>'
                f'<p class="rk-leader-pts"><b>{p["points"]:,}</b> points</p></div>')

    def listing(players, empty, why=None, right=None):
        def li(p):
            sub = why(p) if why else ""
            body = f'<span class="rk-who">{who(p)}</span>' + (f'<span class="rk-why">{sub}</span>' if sub else "")
            return f'<li><span class="rk-now">{p["rank"]}</span><span class="rk-mid">{body}</span>{right(p) if right else move(p)}</li>'
        items = "".join(li(p) for p in players)
        return f'<ul class="rk-movers">{items or f"<li>{empty}</li>"}</ul>'

    def gained(p):
        ch = [c for c in ranking_moves.changes(p.get("ittf_id")) if c[0] > 0][:1]
        return e(f"{ch[0][0]:+,} · {ranking_moves.compact(ch[0][1])}") if ch else ""

    def climbers(key):
        ups = sorted((p for p in R[key] if p["prev"] and p["prev"] > p["rank"]), key=lambda p: (p["rank"] - p["prev"], p["rank"]))[:3]
        return listing(ups, "No climbers this week", why=gained)

    def defending(key):
        """The top 100 players with the most points dropping off in the next four weeks."""
        rows = []
        for p in R[key][:100]:
            d = ranking_moves.dropping(p.get("ittf_id"))
            if d:
                rows.append((sum(x[1] for x in d), p, d))
        rows.sort(key=lambda t: -t[0])
        rows = rows[:4]
        info = {id(p): d for _, p, d in rows}
        return listing([p for _, p, _ in rows], "Nothing dropping off in the next four weeks",
                       why=lambda p: e(f"{ranking_moves.day(info[id(p)][0][0])} · {ranking_moves.compact(info[id(p)][0][2])}"),
                       right=lambda p: f'<span class="mv down rk-drop">−{sum(x[1] for x in info[id(p)]):,}</span>')

    def home(key):
        return listing([p for p in R[key] if p["nat"] in ("ENG", "SCO", "WAL")], f"None in the top {len(R[key])}")

    label = R["label"]
    n = len(R["men"])

    def panel(key, word, title):
        return (f'<section class="pl-panel rk-panel" id="{key}" role="tabpanel" aria-labelledby="t-{key}"><h2 class="sr-only">{word}</h2>'
                f'<div class="rk-three">{leader(key, f"{word} world No. 1")}'
                f'<section class="panel"><h3 class="panel-title">Biggest climbers</h3>{climbers(key)}</section>'
                f'<section class="panel"><h3 class="panel-title">Points dropping off soon</h3>{defending(key)}</section>'
                f'<section class="panel"><h3 class="panel-title">Home nations</h3>{home(key)}</section></div>'
                f'{table(key, title)}</section>')

    return f"""<main class="wrap rk">
<section class="sched-head"><div><h1>World rankings</h1>
<p class="lede">The official {e(label)}: the top {n} men and women, with ranking points and this week's movement. Select a player for their <a href="/players/">full profile</a>.</p></div></section>
<div class="rk-bar-top">
  <div class="pl-tabs" role="tablist" aria-label="Rankings"><button role="tab" id="t-women" aria-controls="women" aria-selected="true">Women</button><button role="tab" id="t-men" aria-controls="men" aria-selected="false">Men</button></div>
  <label class="rk-search"><span class="sr-only">Find a player or country</span><input id="rk-q" type="search" placeholder="Find a player or country, e.g. ENG" autocomplete="off"></label>
</div>
{panel("women", "Women's", "Women's singles")}
{panel("men", "Men's", "Men's singles")}
<p class="small">Source: <a href="{e(R["url"])}" rel="noopener">ITTF world ranking on World Table Tennis</a>. Player and country names link to every Eleven story about them.</p>
</main>
<script>
(function () {{
  const q = document.getElementById("rk-q");
  q.addEventListener("input", () => {{
    const v = q.value.trim().toLowerCase();
    document.querySelectorAll(".rk-table tbody tr").forEach((tr) => {{ tr.hidden = !!v && !tr.dataset.q.includes(v); }});
    document.querySelectorAll(".rk-list").forEach((s) => s.classList.toggle("pg-all", !!v));   // a search shows every match, not one page
  }});
  const tabs = document.querySelectorAll(".rk .pl-tabs button");
  function show(id) {{ tabs.forEach((t) => {{ const on = t.getAttribute("aria-controls") === id; t.setAttribute("aria-selected", on); document.getElementById(t.getAttribute("aria-controls")).hidden = !on; }}); }}
  tabs.forEach((t) => t.addEventListener("click", () => {{ const id = t.getAttribute("aria-controls"); show(id); history.replaceState(null, "", "#" + id); }}));
  show(location.hash === "#men" ? "men" : "women");
}})();
</script>""" + components.PAGER
