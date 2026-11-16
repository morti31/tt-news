"""The Chop, by Eleven: a site about defensive table tennis (choppers and other defenders).

Lives at /defensive/ on eleventabletennis.com until defensive.eleventabletennis.com is pointed at it (UPDATE.md, "The Chop").
It writes no news of its own. It links to stories about defenders elsewhere (and on Eleven, marked as such), and builds
rankings, form and fixtures for the defenders from the data Eleven already keeps.

Inputs
  data/chop/players.json   the defenders: [{"name", "ittf_id", "gender": "M"|"W", "style": "chopper"|"defender"|"pimples",
                           "note", "status": "approved"|"draft", "sources": [url]}]. Only Tom approves names (status).
  data/chop/links.json     the reading list: [{"url", "title", "source", "date", "summary", "players": [names], "kind":
                           "news"|"analysis"|"history"|"video", "eleven": true for Eleven's own pieces}]
  data/rankings.json, data/doubles-rankings.json, data/matches (form), data/draws (next matches in tournaments),
  data/clubs and data/clubs/squads (next club matches), data/news.json and data/articles (Eleven's pieces)
Output
  defensive/index.html, defensive/rankings.html, defensive/calendar.html, defensive/reading.html,
  defensive/players/<slug>.html, defensive/chop.css (copied from tools/chop.css), defensive/sitemap.xml
"""
import datetime as dt, glob, html, json, os, re, shutil, unicodedata

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "defensive")
BASE = "/defensive"          # becomes "" once the subdomain serves the folder at its root
SITE = "https://eleventabletennis.com/defensive"
ELEVEN = "https://eleventabletennis.com"
STYLE = {"chopper": "Classical chopper", "modern": "Modern defender", "allround": "Defensive all-rounder"}
STYLE_ABOUT = {"chopper": "defends from well back with heavy backspin and variation, attacking now and then",
               "modern": "chops, but counter-attacks and plays topspin as a regular part of the game",
               "allround": "defends closer to the table with blocks, pushes and long pimples, and disrupts rather than chops"}


def tag(style, link=True):
    lab = STYLE.get(style)
    if not lab:
        return ""
    t = f'<span class="ch-style ch-style-{e(style)}">{e(lab)}</span>'
    return f'<a class="ch-style-a" href="{BASE}/rankings.html#styles" title="{e(STYLE_ABOUT[style])}">{t}</a>' if link else t
ROUNDS = {"FNL": "Final", "SFNL": "Semi-final", "QFNL": "Quarter-final", "R16": "Last 16", "R32": "Last 32", "R64": "Last 64", "R128": "Last 128"}


def load(path, default):
    try:
        return json.load(open(os.path.join(ROOT, path), encoding="utf-8"))
    except Exception:
        return default


def slug(n):
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", n).strip("-")


def key(n):
    n = unicodedata.normalize("NFKD", n or "").encode("ascii", "ignore").decode().lower()
    return " ".join(sorted(re.findall(r"[a-z]+", n)))


def day(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day} {d:%b %Y}"


def page(title, desc, path, body, active=""):
    nav = "".join(f'<a href="{BASE}{href}"{" aria-current=\"page\"" if k == active else ""}>{lab}</a>'
                  for k, href, lab in (("home", "/", "Home"), ("rankings", "/rankings.html", "Defenders"),
                                       ("calendar", "/calendar.html", "Calendar"), ("reading", "/reading.html", "Reading"),
                                       ("legends", "/legends.html", "Legends")))
    return f"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:site_name" content="The Chop">
<link rel="icon" href="{BASE}/chop.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,600..800&family=Figtree:wght@400;500;600&family=Inter+Tight:wght@500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="{BASE}/chop.css?v={VER}">
</head><body>
<header class="ch-mast"><div class="ch-wrap ch-mast-in">
<a class="ch-mark" href="{BASE}/" aria-label="The Chop home"><svg viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="18" class="ch-mark-ball"/><path d="M6 27 34 13" class="ch-mark-cut"/></svg><span>The Chop</span></a>
<a class="ch-by" href="{ELEVEN}/">by Eleven</a>
<nav class="ch-nav" aria-label="Sections">{nav}</nav></div></header>
<main class="ch-wrap">{body}</main>
<footer class="ch-foot"><div class="ch-wrap"><p><b>The Chop</b> follows the defenders of table tennis: the choppers, the blockers and the players who win from the back of the court. It writes no news of its own; every story here links to the publication that wrote it.</p>
<p>Rankings, results and fixtures from <a href="{ELEVEN}/">Eleven</a>, which takes them from World Table Tennis and the leagues. <a href="{ELEVEN}/contact.html">Contact</a></p></div></footer>
<script src="{BASE}/chop.js?v={VER}" defer></script>
</body></html>"""


VER = "1"


def build():
    global VER
    players = [p for p in load("data/chop/players.json", []) if p.get("status") in ("approved", "draft")]
    links = load("data/chop/links.json", [])
    R = load("data/rankings.json", {})
    rk = {str(r["ittf_id"]): r for g in ("men", "women") for r in R.get(g, [])}
    D = load("data/doubles-rankings.json", {})
    prof = load("data/profiles.json", {})
    now = dt.datetime.now(dt.timezone.utc)
    today = now.date().isoformat()

    # Match database: every singles match of each defender, newest first
    P = load("data/matches/players.json", {})
    E = load("data/matches/events.json", {})
    ids = {p["ittf_id"] for p in players if p.get("ittf_id")}
    ms = {i: [] for i in ids}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "matches", "[0-9]*.json")))[-3:]:
        for m in load(os.path.relpath(f, ROOT), []):
            if m.get("k") not in ("MS", "WS") or len(m["p"][0]) != 1 or m.get("w") not in (0, 1):
                continue
            for side in (0, 1):
                pid = m["p"][side][0]
                if pid in ms:
                    ms[pid].append((m, side))
    for v in ms.values():
        v.sort(key=lambda t: t[0].get("d") or "", reverse=True)

    # Titles: finals won at senior events, singles and doubles, from every season in the match database
    KIND = {"MS": "men's singles", "WS": "women's singles", "MD": "men's doubles", "WD": "women's doubles", "XD": "mixed doubles"}
    titles = {i: [] for i in ids}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "matches", "[0-9]*.json"))):
        for m in load(os.path.relpath(f, ROOT), []):
            if m.get("r") != "FNL" or m.get("w") not in (0, 1) or m.get("k") not in KIND:
                continue
            evn = (E.get(m["e"]) or {}).get("name", "")
            if re.search(r"youth|junior|cadet|U1\d|U2\d|hopes", evn, re.I):
                continue
            for pid in m["p"][m["w"]]:
                if pid in titles:
                    titles[pid].append(((m.get("d") or "")[:4], re.sub(r"\s+Presented by.*$", "", evn), KIND[m["k"]]))
    # Clubs: every squad Eleven keeps that lists the player
    clubs = {p["name"]: [] for p in players}
    for sq in glob.glob(os.path.join(ROOT, "data", "clubs", "squads", "*.json")):
        s_ = load(os.path.relpath(sq, ROOT), {})
        for t in s_.get("teams", []):
            for x in t.get("players", []):
                n = {key(q["name"]): q["name"] for q in players}.get(key(x.get("name")))
                if n:
                    clubs[n].append((t["team"], (s_.get("source") or {}).get("name", "")))

    import names as names_mod

    def nm(i):
        r = rk.get(i)
        if r:
            return r["name"]
        raw = P.get(i)
        return names_mod.from_wtt(*raw) if raw else "Unknown"

    def ev_name(i):
        n = (E.get(i) or {}).get("name", "")
        return re.sub(r"\s+Presented by.*$", "", n)

    # Next matches: tournament draws with a time and no score, then club fixtures through the squads
    nxt = {p["name"]: [] for p in players}
    pk = {key(p["name"]): p["name"] for p in players}
    for f in glob.glob(os.path.join(ROOT, "data", "draws", "*.json")):
        d = load(os.path.relpath(f, ROOT), {})
        title = re.sub(r"\s+Presented by.*$", "", (d.get("event") or {}).get("name", "") if isinstance(d.get("event"), dict) else str(d.get("event") or ""))
        for ev in (d.get("events") or {}).values():
            for rd in ev.get("rounds", []):
                for m in rd.get("matches", []):
                    w = m.get("when") or ""
                    if m.get("score") or not w or w < now.isoformat()[:19]:
                        continue
                    pl = m.get("players") or []
                    for i, x in enumerate(pl):
                        n = pk.get(key(x.get("name")))
                        if n and len(pl) == 2:
                            o = pl[1 - i]
                            nxt[n].append({"when": w, "what": f'{title or "Tournament"}, {ev.get("name", "")}, {rd.get("round", "")}',
                                           "v": o.get("name", "TBC"), "nat": o.get("nat", "")})
    for sq in glob.glob(os.path.join(ROOT, "data", "clubs", "squads", "*.json")):
        cid = os.path.basename(sq)[:-5]
        s = load(os.path.relpath(sq, ROOT), {})
        c = load(f"data/clubs/{cid}.json", {})
        for t in s.get("teams", []):
            for x in t.get("players", []):
                n = pk.get(key(x.get("name")))
                if not n:
                    continue
                tn = key(t["team"])
                for m in c.get("matches", []):
                    if m.get("status") == "finished" or (m.get("when") or "") < now.isoformat()[:19]:
                        continue
                    for side, other in (("home", "away"), ("away", "home")):
                        mn = key(m.get(side) or "")
                        if mn and (mn == tn or set(mn.split()) <= set(tn.split()) or set(tn.split()) <= set(mn.split())) and m.get(other):
                            nxt[n].append({"when": m["when"], "what": f'{s.get("source", {}).get("name") or cid}: {m["home"]} v {m["away"]}',
                                           "v": "", "nat": "", "club": True, "day": m.get("date_only")})
    for k_, v in nxt.items():
        u = {}
        for x in v:
            u.setdefault((x["when"], x["what"]), x)
        nxt[k_] = sorted(u.values(), key=lambda x: x["when"])

    def form(p):
        rows = ms.get(p.get("ittf_id"), [])
        last = rows[:10]
        wl = "".join("W" if m["w"] == side else "L" for m, side in last)
        yr = [(m, s) for m, s in rows if (m.get("d") or "")[:4] == today[:4]]
        won = sum(1 for m, s in yr if m["w"] == s)
        return last, wl, (won, len(yr) - won)

    def res_row(m, side):
        won = m["w"] == side
        o = m["p"][1 - side][0]
        sc = m.get("s") or [0, 0]
        orr = rk.get(o)
        return (f'<li class="{"w" if won else "l"}"><span class="ch-res">{"W" if won else "L"} {sc[side]}-{sc[1 - side]}</span>'
                f'<span class="ch-opp">{e(nm(o))}{f" <small>No {orr["rank"]}</small>" if orr else ""}</span>'
                f'<span class="ch-ev">{e(ev_name(m["e"]))}{", " + ROUNDS[m["r"]] if m.get("r") in ROUNDS else ""} · {day(m["d"])}</span></li>')

    def chip(wl):
        return "".join(f'<i class="{"w" if c == "W" else "l"}" title="{"Won" if c == "W" else "Lost"}">{c}</i>' for c in reversed(wl))

    def rank_of(p):
        return rk.get(p.get("ittf_id") or "")

    def move(r):
        if not r or not r.get("prev"):
            return ""
        d_ = r["prev"] - r["rank"]
        return f'<span class="ch-mv {"up" if d_ > 0 else "dn" if d_ < 0 else ""}">{("+" if d_ > 0 else "") + str(d_) if d_ else "="}</span>'

    def flag(nat):
        import components
        return components.flag(nat)

    def plink(p):
        return f'{BASE}/players/{slug(p["name"])}.html'

    os.makedirs(os.path.join(OUT, "players"), exist_ok=True)
    shutil.copy(os.path.join(ROOT, "tools", "chop.css"), os.path.join(OUT, "chop.css"))
    shutil.copy(os.path.join(ROOT, "tools", "chop.js"), os.path.join(OUT, "chop.js"))
    shutil.copy(os.path.join(ROOT, "tools", "chop.svg"), os.path.join(OUT, "chop.svg"))
    import hashlib
    VER = hashlib.md5((open(os.path.join(OUT, "chop.css"), "rb").read() + open(os.path.join(OUT, "chop.js"), "rb").read())).hexdigest()[:8]

    # Eleven's own pieces about defenders: articles and stories that name a defender with a defensive word, or are about defence
    def_words = re.compile(r"\b(chop|chopper|choppers|chopping|defender|defenders|defensive|defence|backspin)\b", re.I)
    eleven = []
    seen = {l["url"] for l in links}
    for f in glob.glob(os.path.join(ROOT, "data", "articles", "*.json")):
        a = load(os.path.relpath(f, ROOT), {})
        txt = " ".join([a.get("title", ""), a.get("standfirst", "")] + a.get("body", []))
        head = a.get("title", "") + " " + a.get("standfirst", "")
        if len(def_words.findall(txt)) >= 6 or (len(def_words.findall(txt)) >= 2 and any(p["name"] in head for p in players)):
            url = f'{ELEVEN}/news/{a["slug"]}.html'
            if url not in seen:
                who = [p["name"] for p in players if p["name"] in txt]
                eleven.append({"url": url, "title": a["title"], "source": "Eleven", "date": (a.get("published") or a.get("date", ""))[:10],
                               "summary": a.get("standfirst", ""), "players": who, "kind": "analysis" if a.get("category") == "Features" else "news", "eleven": True})
    # Eleven is at most a quarter of what The Chop shows: its newest pieces up to a third of the outside links
    eleven.sort(key=lambda l: l.get("date") or "", reverse=True)
    eleven = eleven[:len(links) // 3]
    allinks = sorted(links + eleven, key=lambda l: l.get("date") or "", reverse=True)

    def capped(rows, n):
        """The first n rows with Eleven's pieces spread out: at most one in every four places (2nd, 6th, 10th...)."""
        ext = [l for l in rows if not l.get("eleven")]
        el = [l for l in rows if l.get("eleven")]
        out = []
        while len(out) < n and (ext or el):
            if len(out) % 4 == 1 and el:
                out.append(el.pop(0))
            elif ext:
                out.append(ext.pop(0))
            else:
                break
        return out

    def link_li(l, show_players=True):
        who = [p for p in players if p["name"] in (l.get("players") or [])]
        tags = "".join(f'<a class="ch-tag" href="{plink(p)}">{e(p["name"])}</a>' for p in who) if show_players else ""
        src = f'<span class="ch-src{" ch-eleven" if l.get("eleven") else ""}">{e(l.get("source", ""))}</span>'
        return (f'<li class="ch-link"><a class="ch-link-a" href="{e(l["url"])}"{"" if l.get("eleven") else " rel=\"noopener\" target=\"_blank\""}>'
                f'<span class="ch-link-meta">{src}<span>{e(l.get("kind", "news").capitalize())}</span>{f"<time>{day(l["date"])}</time>" if l.get("date") else ""}</span>'
                f'<span class="ch-link-t">{e(l["title"])}</span><span class="ch-link-s">{e(l.get("summary", ""))}</span></a>'
                f'{f"<span class=\"ch-tags\">{tags}</span>" if tags else ""}</li>')

    # ---- Rankings
    def table(g):
        rows = sorted((p for p in players if p.get("gender") == g and rank_of(p)), key=lambda p: rank_of(p)["rank"])
        out = []
        for i, p in enumerate(rows, 1):
            r = rank_of(p)
            _, wl, rec = form(p)
            out.append(f'<tr><td class="ch-n">{i}</td><td class="ch-wr">{r["rank"]}{move(r)}</td>'
                       f'<td><a href="{plink(p)}">{flag(r.get("nat"))}{e(p["name"])}</a><span class="ch-sty">{tag(p.get("style"))}</span></td>'
                       f'<td class="ch-pts">{r.get("points", 0):,}</td><td class="ch-frm">{chip(wl[:5])}</td><td class="ch-rec">{rec[0]}-{rec[1]}</td></tr>')
        return rows, ("<table class=\"ch-table\"><thead><tr><th>#</th><th>World</th><th>Player</th><th>Points</th><th>Form</th>"
                      f"<th title=\"Singles won and lost in {today[:4]}\">{today[:4]}</th></tr></thead><tbody>{''.join(out)}</tbody></table>")

    wrows, wtab = table("W")
    mrows, mtab = table("M")
    dd = []
    did = {p["ittf_id"] for p in players}
    for g, lab in (("women", "Women's doubles"), ("men", "Men's doubles"), ("mixed", "Mixed doubles")):
        prs = [x for x in D.get(g, []) if any(pl.get("ittf_id") in did for pl in x["players"])]
        if prs:
            li = "".join(f'<tr><td class="ch-wr">{x["rank"]}</td><td>' + " / ".join(
                (f'<a href="{plink(next(p for p in players if p["ittf_id"] == pl.get("ittf_id")))}"><b>{e(pl["name"])}</b></a>' if pl.get("ittf_id") in did else e(pl["name"]))
                for pl in x["players"]) + f'</td><td class="ch-pts">{x.get("points", 0):,}</td></tr>' for x in prs)
            dd.append(f'<section class="ch-sec"><h3>{lab}</h3><table class="ch-table"><thead><tr><th>World</th><th>Pair</th><th>Points</th></tr></thead><tbody>{li}</tbody></table></section>')
    rbody = f"""<section class="ch-head"><h1>The defenders</h1>
<p class="ch-lede">Every defensive player in the world top 1,000, ranked by their place in the ITTF world rankings ({e(R.get("label", ""))}), with their last five results and this year's record.</p></section>
<div class="ch-tabs" role="tablist"><button role="tab" aria-selected="true" data-t="W">Women ({len(wrows)})</button><button role="tab" aria-selected="false" data-t="M">Men ({len(mrows)})</button><button role="tab" aria-selected="false" data-t="D">Doubles</button></div>
<div class="ch-panel" data-p="W">{wtab}</div><div class="ch-panel" data-p="M" hidden>{mtab}</div>
<div class="ch-panel" data-p="D" hidden><p class="ch-small">Pairs in the doubles world rankings with at least one defender, the defender in bold.</p>{"".join(dd) or "<p>No ranked pairs.</p>"}</div>
<section class="ch-sec" id="styles"><h2>The styles</h2><dl class="ch-styles">{"".join(f"<div><dt>{tag(k, False)}</dt><dd>{e(v[0].upper() + v[1:])}.</dd></div>" for k, v in STYLE_ABOUT.items())}</dl>
<p class="ch-small">Long pimples alone don't make a defender: players who attack with long pimples or anti-spin are not included. Rankings from the <a href="{ELEVEN}/rankings.html">ITTF world rankings on Eleven</a>.</p></section>"""
    open(os.path.join(OUT, "rankings.html"), "w", encoding="utf-8").write(page(
        "Defensive table tennis players: rankings and form | The Chop", "Every chopper and defender in the table tennis world top 1,000: rankings, form and records.", "/rankings.html", rbody, "rankings"))

    # ---- Player pages
    for p in players:
        r = rank_of(p)
        last, wl, rec = form(p)
        nx = nxt.get(p["name"], [])[:5]
        mine = capped([l for l in allinks if p["name"] in (l.get("players") or [])], 12)
        es = next((v for k, v in prof.items() if k == p["name"]), None)
        bio = load(f"data/players/{slug(p['name'])}.json", {}) if es else {}
        hon = [(str(h.get("year", "")), f'{h.get("event", "")}', h.get("result", "")) for h in bio.get("honours") or []]
        tl = sorted(set(titles.get(p.get("ittf_id"), [])), key=lambda t: (t[0], "singles" in t[2]), reverse=True)
        hon_html = "".join(f'<li><span class="ch-yr">{e(y)}</span><span><b>{e(r)}</b> {e(ev)}</span></li>' for y, ev, r in sorted(hon, reverse=True))
        hon_html += "".join(f'<li><span class="ch-yr">{e(y)}</span><span><b>Winner</b> {e(ev)}, {e(k_)}</span></li>' for y, ev, k_ in tl[:12])
        cl = clubs.get(p["name"], []) or [(c.get("club"), c.get("league", "")) for c in bio.get("clubs") or [] if c.get("current")]
        wd_html = "".join(f'<li><q>{e(w["text"])}</q> <a href="{e(w["url"])}" rel="noopener" target="_blank">{e(w["source"])}</a></li>' for w in p.get("wording") or [])
        prov = "" if p.get("subtype_confirmed") else '<p class="ch-small">The sources confirm a defensive style; which of the three types fits best is our provisional call until a source describes the game in more detail.</p>'
        cl_html = "".join(f'<li><b>{e(c)}</b>{f" <span>{e(lg)}</span>" if lg else ""}</li>' for c, lg in cl)
        nxt_html = "".join(f'<li><time datetime="{e(x["when"])}">{day(x["when"]) if x.get("day") else dt.datetime.fromisoformat(x["when"].replace("Z", "+00:00")).strftime("%a %-d %b, %H:%M")} UK</time>'
                           f'<span>{e(x["what"])}{f" v <b>{e(x["v"])}</b>" if x.get("v") else ""}</span></li>' for x in nx)
        body = f"""<p class="ch-crumbs"><a href="{BASE}/rankings.html">The defenders</a> / {e(p["name"])}</p>
<section class="ch-phead"><div><p class="ch-kick">{tag(p.get("style"))}</p><h1>{flag(r.get("nat") if r else "")}{e(p["name"])}</h1>
<p class="ch-lede">{e(p.get("note", ""))}</p></div>
<dl class="ch-facts"><div><dt>World ranking</dt><dd>{f'No {r["rank"]}{move(r)}' if r else "Unranked"}</dd></div>
<div><dt>Points</dt><dd>{f'{r["points"]:,}' if r else "-"}</dd></div><div><dt>{today[:4]} record</dt><dd>{rec[0]}-{rec[1]}</dd></div>
<div><dt>Last 10</dt><dd class="ch-frm">{chip(wl) or "-"}</dd></div></dl></section>
<div class="ch-grid"><section class="ch-sec"><h2>Recent results</h2><ul class="ch-results">{"".join(res_row(m, s) for m, s in last) or "<li>No results on record.</li>"}</ul></section>
<section class="ch-sec"><h2>Next matches</h2><ul class="ch-next">{nxt_html or "<li>No match scheduled in Eleven's tournament draws or club fixtures yet.</li>"}</ul>
{f'<p class="ch-small"><a href="{ELEVEN}{es}">Full profile on Eleven</a>: titles, head to heads and ranking history.</p>' if es else ""}</section></div>
<div class="ch-grid"><section class="ch-sec"><h2>Honours and titles</h2>{f'<ul class="ch-hon">{hon_html}</ul>' if hon_html else "<p class='ch-small'>No major medals or senior titles on record yet.</p>"}</section>
<section class="ch-sec"><h2>Club</h2>{f'<ul class="ch-clubs">{cl_html}</ul>' if cl_html else "<p class='ch-small'>No club in the leagues Eleven follows.</p>"}</section></div>
{f'<section class="ch-sec"><h2>How the sources describe the style</h2><ul class="ch-quotes">{wd_html}</ul>{prov}</section>' if wd_html else ""}
<section class="ch-sec"><h2>Reading</h2>{f'<ul class="ch-links">{"".join(link_li(l, False) for l in mine)}</ul>' if mine else "<p>No stories linked yet.</p>"}</section>"""
        open(os.path.join(OUT, "players", slug(p["name"]) + ".html"), "w", encoding="utf-8").write(page(
            f'{p["name"]}: {STYLE.get(p.get("style"), "defender").lower()}, rankings and form | The Chop',
            f'{p["name"]}, {STYLE.get(p.get("style"), "defender").lower()}: world ranking, recent results, next matches and stories.',
            f'/players/{slug(p["name"])}.html', body))

    # ---- Calendar
    cal = []
    for p in players:
        for x in nxt.get(p["name"], []):
            cal.append((x["when"], p, x))
    cal.sort(key=lambda t: t[0])
    seen_c, rows = set(), []
    for w, p, x in cal:
        k = (w, p["name"])
        if k in seen_c:
            continue
        seen_c.add(k)
        rows.append(f'<li><time datetime="{e(w)}" data-ch-when>{day(w)}</time><a href="{plink(p)}"><b>{e(p["name"])}</b></a> {tag(p.get("style"), False)}'
                    f'<span>{e(x["what"])}{f" v {e(x["v"])}" if x.get("v") else ""}</span></li>')
    cbody = f"""<section class="ch-head"><h1>Calendar</h1><p class="ch-lede">The next matches for the defenders, from the tournament draws and the club leagues Eleven follows. Times are UK time.</p></section>
<ul class="ch-cal">{"".join(rows) or "<li>Nothing scheduled yet.</li>"}</ul>"""
    open(os.path.join(OUT, "calendar.html"), "w", encoding="utf-8").write(page(
        "When the defenders play next | The Chop", "Upcoming matches for table tennis's choppers and defenders, in tournaments and club leagues.", "/calendar.html", cbody, "calendar"))

    # ---- Reading
    kinds = [("all", "All")] + [(k, k.capitalize()) for k in ("news", "analysis", "history", "video") if any(l.get("kind") == k for l in allinks)]
    rbody = f"""<section class="ch-head"><h1>Reading</h1><p class="ch-lede">The best writing on defensive table tennis: news, analysis and history from around the game, with a line from us on each.</p></section>
<div class="ch-tabs ch-filter" role="group">{"".join(f'<button aria-pressed="{str(k == "all").lower()}" data-k="{k}">{lab}</button>' for k, lab in kinds)}</div>
<ul class="ch-links">{"".join(link_li(l).replace('<li class="ch-link">', f'<li class="ch-link" data-k="{e(l.get("kind", "news"))}">', 1) for l in allinks)}</ul>"""
    open(os.path.join(OUT, "reading.html"), "w", encoding="utf-8").write(page(
        "Reading: choppers and defensive table tennis | The Chop", "News, analysis and history of defensive table tennis and its choppers, from around the web.", "/reading.html", rbody, "reading"))

    # ---- Legends: the great defenders of the past, from data/chop/legends.json
    legends = load("data/chop/legends.json", [])
    import components
    lg_html = "".join(
        f'<li class="ch-legend"><div class="ch-legend-h"><h2>{components.flag(l.get("nat"))}{e(l["name"])}</h2>{tag(l.get("style"))}</div>'
        f'<p class="ch-era">{e(l.get("era", ""))}</p><p>{e(l["summary"])}</p>'
        + "".join(f'<a class="ch-more" href="{e(u)}" rel="noopener" target="_blank">Source</a> ' for u in l.get("sources", [])[:1])
        + (lambda mine: f'<ul class="ch-links">{"".join(link_li(x, False) for x in mine)}</ul>' if mine else "")(
            [x for x in allinks if x.get("kind") == "history" and l["name"].split()[-1] in x["title"] + x.get("summary", "")][:3])
        + "</li>" for l in legends)
    lbody = f"""<section class="ch-head"><h1>Legends</h1><p class="ch-lede">The great defenders of the past, from Richard Bergmann's world titles in the 1930s to the choppers who kept the style alive in the modern game.</p></section>
<ul class="ch-legends">{lg_html}</ul>"""
    open(os.path.join(OUT, "legends.html"), "w", encoding="utf-8").write(page(
        "Legends of defensive table tennis | The Chop", "The great choppers and defenders in table tennis history, from Richard Bergmann to Joo Se-hyuk.", "/legends.html", lbody, "legends"))

    # ---- Home
    week = [(w, p, x) for w, p, x in cal if w <= (now + dt.timedelta(days=7)).isoformat()]
    recent = []
    for p in players:
        for m, s in ms.get(p.get("ittf_id"), [])[:3]:
            if (m.get("d") or "") >= (now - dt.timedelta(days=10)).isoformat()[:19]:
                recent.append((m["d"], p, m, s))
    recent.sort(key=lambda t: t[0], reverse=True)
    best = []
    for d_, p, m, s in recent:
        o = rk.get(m["p"][1 - s][0])
        if m["w"] == s:
            best.append((o["rank"] if o else 9999, d_, p, m, s))
    best.sort(key=lambda t: t[0])
    top_w = wrows[:5]
    top_m = mrows[:5]
    mini = lambda rows: "".join(f'<li><span class="ch-wr">{rank_of(p)["rank"]}</span><a href="{plink(p)}">{e(p["name"])}</a>{tag(p.get("style"), False)}</li>' for p in rows)
    hbody = f"""<section class="ch-hero"><h1>The game from the back of the court</h1>
<p class="ch-lede">Choppers and defenders: who they are, how they are playing and the best writing about them. {len(wrows)} women and {len(mrows)} men in the world top 1,000 play this way.</p></section>
<div class="ch-home">
<section class="ch-sec ch-main"><h2>Latest reading</h2><ul class="ch-links">{"".join(link_li(l) for l in capped(allinks, 12))}</ul><a class="ch-more" href="{BASE}/reading.html">All reading</a></section>
<aside class="ch-side">
<section class="ch-sec"><h2>Top defenders</h2><h3>Women</h3><ol class="ch-mini">{mini(top_w)}</ol><h3>Men</h3><ol class="ch-mini">{mini(top_m)}</ol><a class="ch-more" href="{BASE}/rankings.html">All the defenders</a></section>
<section class="ch-sec"><h2>Best recent wins</h2><ul class="ch-results">{"".join(f'<li class="w"><a href="{plink(p)}"><b>{e(p["name"])}</b></a> {res_row(m, s)[len("<li class=\"w\">"):-5]}</li>' for _, _, p, m, s in best[:5]) or "<li>No wins by defenders in the last 10 days.</li>"}</ul></section>
<section class="ch-sec"><h2>This week</h2><ul class="ch-cal">{"".join(f'<li><time>{day(w)}</time><a href="{plink(p)}"><b>{e(p["name"])}</b></a><span>{e(x["what"])}</span></li>' for w, p, x in week[:6]) or "<li>No defenders scheduled this week.</li>"}</ul><a class="ch-more" href="{BASE}/calendar.html">Full calendar</a></section>
</aside></div>"""
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page(
        "The Chop: choppers and defensive table tennis", "Choppers and defenders in table tennis: rankings, form, fixtures and the best writing about them, by Eleven.", "/", hbody, "home"))

    urls = ["/", "/rankings.html", "/calendar.html", "/reading.html", "/legends.html"] + [f'/players/{slug(p["name"])}.html' for p in players]
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls) + "</urlset>")
    return len(players), len(allinks)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    print("The Chop:", build())
