"""The rankings page: the official ITTF top 400, women and men on tabs.

Called from build_site.py. Input: data/rankings.json (from tools/rankings.py). Output: the page body.
"""
import html, json, os
import components
import ranking_moves
import doubles as doubles_data

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
    D = doubles_data.load()

    def pair_who(pr):
        return '<span class="rk-pair">' + "".join(f'<span class="rk-pp">{who(p)}</span>' for p in pr["players"]) + "</span>"

    def dtable(key, title):
        top = D[key][0]["points"] or 1
        rows = "".join(
            f'<tr data-q="{e(" ".join(p["name"] + " " + p["nat"] for p in pr["players"]).lower())}"><td class="rk-pos">{pr["rank"]}</td><td class="rk-mv">{move(pr)}</td>'
            f'<td>{pair_who(pr)}</td><td class="rk-pts">{pr["points"]:,}<span class="rk-bar" style="width:{100 * pr["points"] / top:.1f}%"></span></td></tr>'
            for pr in D[key])
        return (f'<section class="panel rk-list" data-g="{key}"><h3 class="panel-title">{title}</h3>'
                f'<table class="rk-table"><thead><tr><th scope="col">Rank</th><th scope="col"><span class="sr-only">Movement</span></th>'
                f'<th scope="col">Pair</th><th scope="col">Points</th></tr></thead><tbody data-page="50">{rows}</tbody></table></section>')

    def dlisting(pairs, empty):
        li = "".join(f'<li><span class="rk-now">{pr["rank"]}</span><span class="rk-mid">{pair_who(pr)}</span>{move(pr)}</li>' for pr in pairs)
        return f'<ul class="rk-movers">{li or f"<li>{empty}</li>"}</ul>'

    def dpanel(key, word, title):
        if not D.get(key):
            return ""
        lead = D[key][0]
        ups = sorted((x for x in D[key] if x["prev"] and x["prev"] > x["rank"]), key=lambda x: (x["rank"] - x["prev"], x["rank"]))[:3]
        home_ = [x for x in D[key] if any(p["nat"] in ("ENG", "SCO", "WAL") for p in x["players"])]
        leader_html = (f'<div class="rk-leader"><p class="small-label">{word} world No. 1</p><p class="rk-leader-name rk-leader-pair">{pair_who(lead)}</p>'
                       f'<p class="rk-leader-pts"><b>{lead["points"]:,}</b> points</p></div>')
        return (f'<section class="pl-panel rk-panel" id="{key}-d" role="tabpanel" hidden><h2 class="sr-only">{title}</h2>'
                f'<div class="rk-three rk-three-d">{leader_html}'
                f'<section class="panel"><h3 class="panel-title">Biggest climbers</h3>{dlisting(ups, "No climbers this week")}</section>'
                f'<section class="panel"><h3 class="panel-title">Home nations</h3>{dlisting(home_, "No pairs in the top 200")}</section></div>'
                f'{dtable(key, title)}</section>')

    def panel(key, word, title):
        return (f'<section class="pl-panel rk-panel" id="{key}" role="tabpanel"><h2 class="sr-only">{word}</h2>'
                f'<div class="rk-three">{leader(key, f"{word} world No. 1")}'
                f'<section class="panel"><h3 class="panel-title">Biggest climbers</h3>{climbers(key)}</section>'
                f'<section class="panel"><h3 class="panel-title">Points dropping off soon</h3>{defending(key)}</section>'
                f'<section class="panel"><h3 class="panel-title">Home nations</h3>{home(key)}</section></div>'
                f'{table(key, title)}</section>')

    dlabel = D.get("label", "")
    return f"""<main class="wrap rk">
<section class="sched-head"><div><h1>World rankings</h1>
<p class="lede">The official ITTF world rankings: the top {n} men and women in singles and the top 200 pairs in doubles, with points and this week's movement. Select a player for their <a href="/players/">full profile</a>.</p></div></section>
<div class="rk-bar-top">
  <div class="pl-tabs" role="tablist" aria-label="Rankings"><button role="tab" data-g="women" aria-selected="true">Women</button><button role="tab" data-g="men" aria-selected="false">Men</button>{'<button role="tab" data-g="mixed" aria-selected="false">Mixed doubles</button>' if D.get("mixed") else ""}</div>
  <label class="rk-search"><span class="sr-only">Find a player or country</span><input id="rk-q" type="search" placeholder="Find a player or country, e.g. ENG" autocomplete="off"></label>
</div>
{'<div class="toggle sched-filter rk-kind" role="group" aria-label="Singles or doubles"><button data-k="s" aria-pressed="true">Singles</button><button data-k="d" aria-pressed="false">Doubles</button></div>' if D.get("men") else ""}
{panel("women", "Women's", "Women's singles")}
{panel("men", "Men's", "Men's singles")}
{dpanel("women", "Women's doubles", "Women's doubles")}
{dpanel("men", "Men's doubles", "Men's doubles")}
{dpanel("mixed", "Mixed doubles", "Mixed doubles")}
<p class="small">Source: <a href="{e(R["url"])}" rel="noopener">ITTF world ranking on World Table Tennis</a> ({e(label)}{f"; doubles: {e(dlabel.split(', ', 1)[-1])}" if dlabel else ""}). Player and country names link to every Eleven story about them.</p>
</main>
<script>
(function () {{
  const q = document.getElementById("rk-q");
  q.addEventListener("input", () => {{
    const v = q.value.trim().toLowerCase();
    document.querySelectorAll(".rk-table tbody tr").forEach((tr) => {{ tr.hidden = !!v && !tr.dataset.q.includes(v); }});
    document.querySelectorAll(".rk-list").forEach((s) => s.classList.toggle("pg-all", !!v));   // a search shows every match, not one page
  }});
  const tabs = [...document.querySelectorAll(".rk .pl-tabs button")], kinds = [...document.querySelectorAll(".rk-kind button")];
  const kindBar = document.querySelector(".rk-kind");
  let G = "women", K = "s";
  function show() {{
    if (G === "mixed") K = "d";
    tabs.forEach((t) => t.setAttribute("aria-selected", String(t.dataset.g === G)));
    kinds.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.k === K)));
    if (kindBar) kindBar.hidden = G === "mixed";
    const id = K === "d" ? G + "-d" : G;
    document.querySelectorAll(".rk-panel").forEach((p) => {{ p.hidden = p.id !== id; }});
    history.replaceState(null, "", "#" + (G === "mixed" ? "mixed" : G + (K === "d" ? "-doubles" : "")));
  }}
  tabs.forEach((t) => t.addEventListener("click", () => {{ G = t.dataset.g; if (G !== "mixed" && K === "d" && !document.getElementById(G + "-d")) K = "s"; show(); }}));
  kinds.forEach((b) => b.addEventListener("click", () => {{ K = b.dataset.k; show(); }}));
  const h = location.hash.slice(1);
  if (h === "mixed") G = "mixed"; else if (h.startsWith("men")) G = "men";
  if (h.endsWith("-doubles")) K = "d";
  show();
}})();
</script>""" + components.PAGER
