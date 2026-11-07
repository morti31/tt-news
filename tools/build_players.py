"""Player profiles: /players/<slug>.html for every player with a bio file in data/players, and /players/ (the index).

Called from build_site.py. Inputs:
  data/players/<slug>.json     the bio file (researched; see UPDATE.md "Player profiles")
  data/players/wtt.json        WTT's own record (date of birth, hand, grip, best rank), from tools/match_sync.py
  data/matches/*.json          Eleven's match database, from tools/match_sync.py
  data/rankings.json, data/ranking-history.json
  the stories and their tags (build_site.make_tags), the event pages (events.json)
"""
import glob, html, json, os, re, datetime as dt
import components

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FAMILY_FIRST = {"CHN", "TPE", "KOR", "HKG", "MAC", "PRK"}
FIXES = {"Felix Lebrun": "Félix Lebrun", "Anton Kallberg": "Anton Källberg", "Joao Geraldo": "João Geraldo", "Bernadette Szocs": "Bernadette Szőcs",
         "Ying Han": "Han Ying", "Peng Yu-Han": "Peng Yu-han", "Jian Zeng": "Zeng Jian", "Feng Yi-Hsin": "Feng Yi-hsin", "Bo Fang": "Fang Bo",
         "Leo De Nodrest": "Léo de Nodrest", "Truls Moregardh": "Truls Moregard"}
ROUNDS = {"FNL": "Final", "SFNL": "Semi-final", "QFNL": "Quarter-final", "8FNL": "Last 16", "R16": "Last 16", "R32": "Last 32", "R64": "Last 64",
          "R128": "Last 128", "BRNZ": "Bronze match"}
KINDS = {"MS": "Men's singles", "WS": "Women's singles", "MD": "Men's doubles", "WD": "Women's doubles", "XD": "Mixed doubles",
         "MT": "Men's team", "WT": "Women's team", "XT": "Mixed team"}
LEVELS = [("WTT Finals", r"WTT Finals|Cup Finals"), ("World Championships", r"World (Team )?(Table Tennis )?Championships"),
          ("World Cup", r"World Cup"), ("Olympic Games", r"Olympic"), ("Grand Smash", r"Smash"), ("WTT Champions", r"WTT Champions"),
          ("WTT Star Contender", r"Star Contender"), ("WTT Contender", r"WTT Contender"), ("WTT Feeder", r"Feeder")]


CATEGORIES = ["Olympic Games", "World Championships", "World Team Championships", "World Cup", "WTT Finals", "Grand Smash",
              "Continental and multi-sport", "WTT tour", "Other"]
TIMELINE_ROWS = ["Olympic Games", "World Championships", "World Team Championships", "World Cup", "WTT Finals", "Singapore Smash", "Saudi Smash", "China Smash",
                 "United States Smash", "Europe Smash"]
# Years each competition was held in the WTT era, where the match database can't tell (Olympics aren't in WTT's results)
HELD_FIXED = {"Olympic Games": {2021, 2024}, "World Championships": {2021, 2023, 2025}, "World Team Championships": {2022, 2024, 2026}, "World Cup": {2024, 2025, 2026}}
ROUND_SHORT = {"FNL": "F", "SFNL": "SF", "QFNL": "QF", "8FNL": "R16", "R16": "R16", "R32": "R32", "R64": "R64", "R128": "R128", "BRNZ": "SF"}
ROUND_RANK = {"W": 10, "F": 9, "SF": 8, "QF": 7, "R16": 6, "R32": 5, "R64": 4, "R128": 3, "Grp": 2, "Q": 1}


def smash_name(n):
    m = re.search(r"(Singapore|Saudi|China|United States|US|Europe)\s+Smash", n)
    if m:
        return ("United States" if m.group(1) == "US" else m.group(1)) + " Smash"
    return "Grand Smash"


def category(n):
    if re.search(r"Olympic", n) and "Youth" not in n:
        return "Olympic Games"
    if re.search(r"World (Team )?(Table Tennis )?Championships", n):
        return "World Team Championships" if "Team" in n or n.strip().endswith("team") else "World Championships"
    if re.search(r"World Cup", n) and "Mixed Team" not in n and "mixed team" not in n:
        return "World Cup"
    if re.search(r"WTT Finals|Cup Finals", n):
        return "WTT Finals"
    if "Smash" in n:
        return "Grand Smash"
    if re.search(r"Asian|European|Americas|African|Oceania|Pan American|Commonwealth|Europe Top", n):
        return "Continental and multi-sport"
    if re.search(r"WTT|Contender|Feeder|Champions", n):
        return "WTT tour"
    return "Other"


def timeline_row(n):
    c = category(n)
    if c == "Grand Smash":
        sn = smash_name(n)
        return sn if sn in TIMELINE_ROWS else None
    if c in ("Olympic Games", "World Championships", "World Team Championships", "World Cup", "WTT Finals"):
        return c
    return None


def slugify(s):
    import unicodedata
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def load(path, default):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


def wtt_name(raw, org):
    """'LIN Yun-Ju' + TPE -> 'Lin Yun-Ju'; 'LEBRUN Felix' + FRA -> 'Félix Lebrun'."""
    words = (raw or "").split()
    fam = " ".join(w[:1] + w[1:].lower() if w.isupper() else w for w in words if w.isupper() or w.replace("-", "").isupper())
    giv = " ".join(w for w in words if not (w.isupper() or w.replace("-", "").isupper()))
    fam = "-".join(p[:1].upper() + p[1:] for p in fam.split("-"))
    name = f"{fam} {giv}" if org in FAMILY_FIRST else f"{giv} {fam}"
    name = name.strip()
    return FIXES.get(name, name)


def clean_event(n):
    n = re.sub(r"\s+[Pp]resented [Bb]y.*$", "", n or "")
    n = re.sub(r"\s+-\s+President.*$", "", n)
    n = re.sub(r"Men[’']s (&|and) Women[’']s ", "", n)
    n = n.replace("ITTF ", "").replace("World Team Table Tennis Championships Finals", "World Team Championships")
    return n.strip()


def level(name):
    for lab, rx in LEVELS:
        if re.search(rx, name):
            return lab
    return "Other"


def round_name(r):
    if r in ROUNDS:
        return ROUNDS[r]
    if r.startswith("GP") or r.startswith("RR"):
        return "Group"
    m = re.match(r"RND(\d)", r)
    return f"Qualifying round {m.group(1)}" if m else r


class DB:
    def __init__(self):
        mdir = os.path.join(ROOT, "data", "matches")
        self.events = load(os.path.join(mdir, "events.json"), {})
        self.players = load(os.path.join(mdir, "players.json"), {})
        self.matches = []
        for f in sorted(glob.glob(os.path.join(mdir, "[0-9][0-9][0-9][0-9].json"))):
            self.matches += load(f, [])
        self.by_player = {}
        for m in self.matches:
            for side in m["p"]:
                for pid in side:
                    self.by_player.setdefault(pid, []).append(m)

    def name(self, pid, profiles):
        if pid in profiles:
            return profiles[pid]["name"]
        raw, org = (self.players.get(pid) or [None, None])
        return wtt_name(raw, org) if raw else pid

    def org(self, pid):
        return (self.players.get(pid) or [None, None])[1]


def age(born):
    if not born:
        return None
    b = dt.date.fromisoformat(born)
    t = dt.date.today()
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


def long_date(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day} {d:%B %Y}"


def short_date(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day} {d:%b %Y}"


def player_card(p, rank=None, size="big"):
    """Eleven's player card: navy or plum base, the association's flag faded into the top corner, the orange stripe and the full name. No photo."""
    code = components.FLAGS.get((p.get("nat") or "").upper())
    bg = f'<span class="fi fi-{code} pc-flag" aria-hidden="true"></span>' if code else ""
    rk = f'<span class="pc-rank">No. {rank}</span>' if rank else ""
    g = e(p.get("gender") or "M").lower()
    return (f'<div class="pcard pcard-{size} pc-{g}" aria-hidden="true">{bg}'
            f'<span class="pc-name"><span class="pc-n2">{e(p["name"])}</span></span>'
            f'<span class="pc-foot">{components.flag(p.get("nat"))}<span class="pc-nat">{e(p.get("nat") or "")}</span>{rk}</span></div>')


def build(page, site, tag_items, tag_url, hubs, R):
    """Writes players/<slug>.html and players/index.html. Returns sitemap rows and {ittf id: url} for links elsewhere."""
    profiles = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "players", "*.json"))):
        if os.path.basename(f) == "wtt.json":
            continue
        p = json.load(open(f, encoding="utf-8"))
        p["slug"] = os.path.splitext(os.path.basename(f))[0]
        profiles[p["ittf_id"]] = p
    if not profiles:
        return [], {}
    wtt = load(os.path.join(ROOT, "data", "players", "wtt.json"), {})
    hist = load(os.path.join(ROOT, "data", "ranking-history.json"), {"weeks": {}})
    db = DB()
    hub_by_wtt = {str(h.get("wtt_id") or h.get("draw")): h for h in hubs.values() if h.get("wtt_id") or h.get("draw")}
    ranks = {}
    for g in ("men", "women"):
        for p in (R or {}).get(g, []):
            ranks[p.get("ittf_id")] = p
    urls = {pid: f"/players/{p['slug']}.html" for pid, p in profiles.items()}
    os.makedirs(os.path.join(ROOT, "players"), exist_ok=True)
    for old in glob.glob(os.path.join(ROOT, "players", "*.html")):
        os.remove(old)
    out_urls = []

    def who(pid):
        n = db.name(pid, profiles)
        f = components.flag(db.org(pid) or (profiles.get(pid) or {}).get("nat"))
        return f'{f}<a href="{urls[pid]}">{e(n)}</a>' if pid in urls else f'{f}{e(n)}'

    def ev_link(eid):
        ev = db.events.get(eid) or {}
        nm = clean_event(ev.get("name") or f"Event {eid}")
        h = hub_by_wtt.get(eid)
        return f'<a href="/events/{h["id"]}.html">{e(nm)}</a>' if h else e(nm)

    for pid, p in profiles.items():
        ms = sorted(db.by_player.get(pid, []), key=lambda m: m.get("d") or "", reverse=True)

        def side_of(m):
            return 0 if pid in m["p"][0] else 1

        def won(m):
            return m.get("w") == side_of(m)

        singles = [m for m in ms if m["k"][1] in "S" and not m.get("wo")]
        team_s = [m for m in ms if m["k"][1] == "T" and len(m["p"][0]) == 1 and not m.get("wo")]
        doubles = [m for m in ms if m["k"][1] == "D" and not m.get("wo")]
        rk = ranks.get(pid)
        w = wtt.get(pid, {})
        born = p.get("born") or (lambda d: f"{d[6:10]}-{d[0:2]}-{d[3:5]}" if d and len(d) >= 10 else None)(w.get("dob"))
        hand = p.get("hand") or (w.get("hand") or "").replace(" Hand", "") or None
        grip = p.get("grip")   # WTT's grip field is unreliable (it lists Dang Qiu as penhold), so only researched values
        ms_stat = next((s for s in w.get("stats", []) if s.get("SubeventCode") in ("MS", "WS")), {})
        best = None
        if ms_stat.get("best_rank"):
            try:
                best = f'No. {ms_stat["best_rank"]} ({dt.date(int(ms_stat["best_rank_year"]), int(ms_stat["best_rank_month"]), 1):%B %Y})'
            except Exception:
                best = f'No. {ms_stat["best_rank"]}'
        # Career high: from Eleven's weekly ranking history (WTT's own "best rank" field is unreliable)
        career_high = None
        hist_ranks = [(wk, row[1]) for wk, gs in sorted(hist.get("weeks", {}).items()) for g in gs.values() for row in g if row[0] == pid]
        if hist_ranks and len(hist_ranks) >= 8:
            r_best = min(r for _, r in hist_ranks)
            first = next(wk for wk, r in hist_ranks if r == r_best)
            career_high = f"No. {r_best} ({dt.date.fromisoformat(first):%B %Y}, since records began)"
        now = [c for c in p.get("clubs") or [] if c.get("current")]
        club_txt = "; ".join(c["club"] + (f' ({c["league"]})' if c.get("league") else "") for c in now) or None

        # ---- header
        mv = ""
        if rk and rk.get("prev"):
            d = rk["prev"] - rk["rank"]
            mv = f' <span class="mv {"up" if d > 0 else "down" if d < 0 else "same"}">{"▲" + str(d) if d > 0 else "▼" + str(-d) if d < 0 else "–"}</span>'
        facts = [("World ranking", f'No. {rk["rank"]}, {rk["points"]:,} points' if rk else "Outside the top 100"),
                 ("Career high", career_high), ("Age", f'{age(born)} (born {long_date(born)})' if born else None),
                 ("Birthplace", p.get("birthplace")), ("Height", f'{p["height_cm"]} cm' if p.get("height_cm") else None),
                 ("Plays", ", ".join(x for x in (f"{hand}-handed" if hand else None, grip) if x) or None),
                 ("Style", p.get("style")), ("Coach", p.get("coach")),
                 ("Clubs" if len(now) > 1 else "Club", club_txt)]
        dl = "".join(f"<dt>{k}</dt><dd>{e(v)}</dd>" for k, v in facts if v)
        head = f'''<header class="pl-head">{player_card(p, rk["rank"] if rk else None)}
<div class="pl-id"><p class="small-label">{"Men" if p.get("gender") == "M" else "Women"} · {components.flag(p.get("nat"))} {e(p.get("nat") or "")}</p>
<h1>{e(p["name"])}</h1>
<p class="pl-rank">{f'World No. {rk["rank"]}{mv}' if rk else "Outside the world top 100"}</p></div>
<dl class="pl-facts">{dl}</dl></header>'''

        # ---- season by season (singles, with team-event singles counted separately)
        years = sorted({(m.get("d") or "")[:4] for m in ms if m.get("d")}, reverse=True)
        rows, chart = [], []
        for y in years:
            s = [m for m in singles if (m.get("d") or "")[:4] == y]
            d_ = [m for m in doubles if (m.get("d") or "")[:4] == y]
            if not s and not d_:
                continue
            sw = sum(won(m) for m in s)
            dw = sum(won(m) for m in d_)
            titles = sum(1 for m in s if m["r"] == "FNL" and won(m))
            finals = sum(1 for m in s if m["r"] == "FNL")
            pct = round(100 * sw / len(s)) if s else None
            rows.append(f'<tr><th scope="row">{y}</th><td>{len(s)}</td><td>{sw}-{len(s) - sw}</td><td><b>{f"{pct}%" if pct is not None else "–"}</b></td>'
                        f'<td>{titles}</td><td>{finals}</td><td>{f"{dw}-{len(d_) - dw}" if d_ else "–"}</td></tr>')
            if pct is not None:
                chart.append((y, pct, len(s)))
        bars = "".join(f'<div class="pl-bar"><span class="pl-bar-y">{y}</span><span class="pl-bar-t"><span class="pl-bar-f" style="width:{pc}%"></span></span>'
                       f'<span class="pl-bar-v">{pc}%<small> of {n}</small></span></div>' for y, pc, n in sorted(chart))
        season = (f'<section class="hub-sec" id="seasons"><h2 class="section-title">Season by season</h2>'
                  f'<div class="pl-bars" aria-label="Singles win percentage by year">{bars}</div>'
                  f'<div class="table-scroll"><table class="pl-table"><thead><tr><th scope="col">Year</th><th scope="col">Singles</th><th scope="col">Won-lost</th><th scope="col">Win %</th>'
                  f'<th scope="col">Titles</th><th scope="col">Finals</th><th scope="col">Doubles</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
                  f'<p class="small">WTT and ITTF events from {min(years) if years else ""}, main draw and qualifying, walkovers left out. Team-event matches are listed under recent matches but not counted here.</p></section>') if rows else ""

        # ---- recent matches
        def mrow(m):
            sd = side_of(m)
            opp = m["p"][1 - sd]
            partner = [x for x in m["p"][sd] if x != pid]
            res = "W" if won(m) else "L"
            sc = "w/o" if m.get("wo") else (f'{m["s"][sd]}-{m["s"][1 - sd]}' if m.get("s") else "")
            games = ""
            if m.get("g"):
                gs = [g.split("-") for g in m["g"].split(",")]
                games = ", ".join(f"{a}-{b}" if sd == 0 else f"{b}-{a}" for a, b in gs if a and b)
            when = (m.get("d") or "")[:10]
            what = KINDS.get(m["k"], m["k"]) + (", " + round_name(m["r"]) if m.get("r") else "")
            with_ = f' <span class="pl-with">with {" / ".join(who(x) for x in partner)}</span>' if partner else ""
            return (f'<tr class="{"pl-w" if res == "W" else "pl-l"}"><td class="pl-date">{e(short_date(when)) if when else ""}</td>'
                    f'<td>{ev_link(m["e"])}<span class="pl-sub">{e(what)}</span></td>'
                    f'<td>{" / ".join(who(x) for x in opp)}{with_}</td><td class="pl-res"><b>{res}</b> {e(sc)}<span class="pl-sub">{e(games)}</span></td></tr>')
        recent = ms[:20]
        recent_sec = (f'<section class="hub-sec" id="matches"><h2 class="section-title">Recent matches</h2><div class="table-scroll"><table class="pl-table pl-matches"><thead><tr>'
                      f'<th scope="col">Date</th><th scope="col">Event</th><th scope="col">Opponent</th><th scope="col">Result</th></tr></thead><tbody>{"".join(mrow(m) for m in recent)}</tbody></table></div>'
                      f'<p class="small">Official results from World Table Tennis. Times are UK dates.</p></section>') if recent else ""

        # ---- honours: championship medals (researched) and titles (from the database), the Grand Smashes on their own
        medal = {"Gold": "g", "Silver": "s", "Bronze": "b", "Winner": "g", "Runner-up": "s", "Semi-final": "b"}
        groups, seen_h = {}, set()

        def add(cat, year, label, result, link=None):
            key = (cat, year, label.lower())
            if key in seen_h:
                return
            seen_h.add(key)
            groups.setdefault(cat, []).append((year, label, result, link))
        for h in p.get("honours") or []:
            comp, _, disc = h["event"].partition(", ")
            cat = category(comp)
            label = (comp + " " if cat in ("Grand Smash", "Continental and multi-sport", "Other") else "") + (disc or "")
            add(cat, h["year"], label.strip() or ("Team" if cat == "World Team Championships" else comp), h["result"])
        for m in ms:
            if m["r"] != "FNL" or not won(m) or m["k"][1] not in "SD":
                continue
            nm = clean_event((db.events.get(m["e"]) or {}).get("name") or "")
            cat = category(nm)
            yr = int((m.get("d") or "0000")[:4])
            disc = KINDS.get(m["k"], "").split(" ", 1)[1] if " " in KINDS.get(m["k"], "") else ""
            if cat in ("Grand Smash",):
                label = smash_name(nm) + " " + disc
            elif cat == "WTT tour":
                label = re.sub(r"\s*\d{4}$", "", nm) + " " + disc
            else:
                label = disc
            add(cat, yr, label.strip(), "Gold", ev_link(m["e"]))

        def hli(x, cat):
            year, label, result, link = x
            res = result
            if cat in ("Grand Smash", "WTT Finals", "WTT tour"):
                res = {"Gold": "Winner", "Silver": "Runner-up", "Bronze": "Semi-final"}.get(result, result)
            lab = e(label[:1].upper() + label[1:])
            if link:
                lab = f'{lab} <span class="pl-sub">{link}</span>'
            return f'<li><span class="md md-{medal.get(res, "x")}">{e(res)}</span> <b>{year}</b> {lab}</li>'
        cats = [c for c in CATEGORIES if c in groups]
        hon_html = "".join(f'<div class="pl-tgroup"><h3>{e(c)} <span>{len(groups[c])}</span></h3><ul>{"".join(hli(x, c) for x in sorted(groups[c], key=lambda x: -x[0]))}</ul></div>' for c in cats)

        # ---- performance timeline (singles), like a tennis player's Grand Slam table
        rows_t, yrs = {}, set()
        for m in singles:
            nm = clean_event((db.events.get(m["e"]) or {}).get("name") or "")
            row = timeline_row(nm)
            if not row:
                continue
            yr = int((m.get("d") or "0000")[:4])
            yrs.add(yr)
            cur = rows_t.setdefault(row, {}).get(yr)
            res = "W" if m["r"] == "FNL" and won(m) else ROUND_SHORT.get(m["r"], "Q" if m["r"].startswith("RND") else "Grp" if m["r"][:2] in ("GP", "RR") else m["r"])
            if cur is None or ROUND_RANK.get(res, 0) > ROUND_RANK.get(cur, 0):
                rows_t[row][yr] = res
        # World Team Championships: the team's finish, from the rubbers the player played (medals below add W, F and SF)
        for m in team_s:
            nm = clean_event((db.events.get(m["e"]) or {}).get("name") or "")
            if timeline_row(nm) != "World Team Championships":
                continue
            yr = int((m.get("d") or "0000")[:4])
            res = "F" if m["r"] == "FNL" else ROUND_SHORT.get(m["r"], "Grp" if m["r"][:2] in ("GP", "RR") else None)
            if not res:
                continue
            yrs.add(yr)
            cur = rows_t.setdefault("World Team Championships", {}).get(yr)
            if cur is None or ROUND_RANK.get(res, 0) > ROUND_RANK.get(cur, 0):
                rows_t["World Team Championships"][yr] = res
        for h in p.get("honours") or []:
            comp, _, disc = h["event"].partition(", ")
            if disc and disc.lower() != "singles" and "Team Championships" not in comp:
                continue
            row = timeline_row(comp)
            if not row:
                continue
            res = {"Gold": "W", "Silver": "F", "Bronze": "SF"}.get(h["result"])
            if res and (h["year"] not in rows_t.get(row, {}) or ROUND_RANK.get(res, 0) > ROUND_RANK.get(rows_t[row][h["year"]], 0)):
                rows_t.setdefault(row, {})[h["year"]] = res
                yrs.add(h["year"])
        timeline = ""
        if rows_t:
            ylist = list(range(max(min(yrs), dt.date.today().year - 6), dt.date.today().year + 1))
            order_rows = [r for r in TIMELINE_ROWS if r in rows_t]
            # which competitions were held in which years: fixed list, or any event of that name in the match database
            covered = {int(v["start"][:4]) for v in db.events.values() if v.get("n") and v.get("start")}
            held = {r: set(ys) for r, ys in HELD_FIXED.items()}
            for v in db.events.values():
                if v.get("n") and v.get("start"):
                    rr = timeline_row(clean_event(v.get("name") or ""))
                    if rr and rr not in HELD_FIXED:
                        held.setdefault(rr, set()).add(int(v["start"][:4]))

            for v in load(os.path.join(ROOT, "data", "schedule.json"), {}).get("events", []):   # events still to come this year
                rr = timeline_row(v.get("name") or "")
                if rr and v.get("start"):
                    held.setdefault(rr, set()).add(int(v["start"][:4]))
            for h in hubs.values():
                rr = timeline_row(h.get("name") or "")
                if rr and h.get("start"):
                    held.setdefault(rr, set()).add(int(h["start"][:4]))

            def cell(r, y):
                v = rows_t[r].get(y)
                if v:
                    return f'<td class="tl-{v.lower()}">{v}</td>'
                if (r in HELD_FIXED or y in covered) and y not in held.get(r, set()) and y <= dt.date.today().year:
                    return '<td class="tl-nh">Not held</td>'
                return '<td class="tl-x">–</td>'
            head_t = "".join(f'<th scope="col">{y}</th>' for y in ylist)
            body_t = ""
            for r in order_rows:
                cells = "".join(cell(r, y) for y in ylist)
                wins = sum(1 for v in rows_t[r].values() if v == "W")
                body_t += f'<tr><th scope="row">{e(r)}</th>{cells}<td class="tl-tot">{wins}</td></tr>'
            timeline = (f'<h3 class="pl-h3">At the majors and Grand Smashes</h3><div class="table-scroll"><table class="pl-tl"><thead><tr><th scope="col"></th>{head_t}<th scope="col">Titles</th></tr></thead>'
                        f'<tbody>{body_t}</tbody></table></div><p class="small">W won, F final, SF semi-final, QF quarter-final, R16 last 16 and so on; Grp group stage, Q qualifying, – did not play or no record, Not held: no event that year. Singles, except the World Team Championships, which show the team\'s finish in years the player played or won a medal. '
                        f'Full results from {min(y for y in yrs if any(y in v for v in rows_t.values()))} from World Table Tennis\'s records; earlier years show medals only.</p>')
        titles_sec = ""
        if hon_html or timeline:
            titles_sec = f'<section class="hub-sec" id="honours"><h2 class="section-title">Honours</h2>{timeline}<div class="pl-tgroups">{hon_html}</div></section>'

        # ---- head to head with the players met most
        h2h = {}
        for m in singles + team_s:
            o = m["p"][1 - side_of(m)][0]
            a = h2h.setdefault(o, [0, 0])
            a[0 if won(m) else 1] += 1
        top = sorted(h2h.items(), key=lambda kv: (-(kv[1][0] + kv[1][1]), -kv[1][0]))[:10]
        h2h_sec = (f'<section class="hub-sec" id="h2h"><h2 class="section-title">Head to head</h2><p class="small">Singles against the players met most often.</p>'
                   f'<ul class="pl-h2h">{"".join(f"<li><span>{who(o)}</span><b>{w_}-{l_}</b></li>" for o, (w_, l_) in top)}</ul></section>') if top else ""

        # ---- ranking history
        pts = []
        for wk, gs in sorted(hist.get("weeks", {}).items()):
            for g in gs.values():
                for row in g:
                    if row[0] == pid:
                        pts.append((wk, row[1]))
        rank_sec = ""
        if len(pts) >= 4:
            lo, hi = 1, max(r for _, r in pts)
            W_, H_ = 640, 160
            xs = [24 + i * (W_ - 48) / (len(pts) - 1) for i in range(len(pts))]
            ys = [16 + (r - lo) / max(1, hi - lo) * (H_ - 40) for _, r in pts]
            path = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in zip(xs, ys))
            rank_sec = (f'<section class="hub-sec" id="ranking"><h2 class="section-title">World ranking</h2><svg class="pl-rk" viewBox="0 0 {W_} {H_}" role="img" aria-label="World ranking by week">'
                        f'<path d="{path}" fill="none" stroke="currentColor" stroke-width="2"/></svg><p class="small">Weekly world ranking since {long_date(pts[0][0])}. Higher is better.</p></section>')

        # ---- clubs, equipment
        clubs = p.get("clubs") or []
        club_sec = ""
        if clubs:
            lis = "".join(f'<li><b>{e(c["club"])}</b>{" · " + e(c["league"]) if c.get("league") else ""}<span class="pl-sub">{e(" to ".join(x for x in (c.get("from"), c.get("to")) if x) or ("Current" if c.get("current") else ""))}</span></li>' for c in reversed(clubs))
            club_sec = f'<section class="panel"><h2 class="panel-title">Clubs</h2><ul class="pl-list">{lis}</ul></section>'
        eq = p.get("equipment") or {}
        eq_rows = [(k, eq.get(x)) for k, x in (("Blade", "blade"), ("Forehand", "forehand"), ("Backhand", "backhand"), ("Sponsor", "sponsor")) if eq.get(x)]
        eq_sec = ""
        if eq_rows:
            src = f' <a href="{e(eq["source"])}" rel="noopener">Source</a>' if eq.get("source") else ""
            eq_sec = (f'<section class="panel"><h2 class="panel-title">Equipment</h2><dl class="pl-facts pl-eq">{"".join(f"<dt>{k}</dt><dd>{e(v)}</dd>" for k, v in eq_rows)}</dl>'
                      f'<p class="small">Last confirmed {long_date(eq["confirmed"])}.{src} Players change equipment, so this can go out of date.</p></section>')

        # ---- news
        tslug = slugify(p["name"])
        news = [it for it in tag_items if tslug in it["all"]]
        news.sort(key=lambda it: it["published"], reverse=True)
        news_sec = ""
        if news:
            lis = "".join(f'<li><a href="{e(it["url"])}">{e(it["title"])}</a><span class="meta">{e(it["when"])}</span></li>' for it in news[:8])
            more = f'<a class="panel-link" href="{tag_url(tslug)}">All {len(news)} stories</a>' if len(news) > 8 else ""
            news_sec = f'<section class="panel"><h2 class="panel-title">Latest news</h2><ul class="pl-news">{lis}</ul>{more}</section>'

        notes = "".join(f"<p>{e(n)}</p>" for n in p.get("notes") or [])
        def host(u):
            return re.sub(r"^https?://(www[.])?", "", u).split("/")[0]
        srcs = ", ".join(f'<a href="{e(u)}" rel="noopener">{e(host(u))}</a>' for u in p.get("sources") or [])
        jump = "".join(f'<a href="#{k}">{v}</a>' for k, v, sec in (("matches", "Matches", recent_sec), ("seasons", "Seasons", season), ("honours", "Honours", titles_sec),
                                                                   ("h2h", "Head to head", h2h_sec), ("ranking", "Ranking", rank_sec)) if sec)
        body = f'''<main class="wrap pl-page">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/players/">Players</a> / {e(p["name"])}</nav>
{head}
{f'<nav class="hub-jump" aria-label="On this page">{jump}</nav>' if jump else ""}
<div class="hub-grid"><div class="hub-main">
{notes and f'<section class="hub-sec pl-notes">{notes}</section>'}
{recent_sec}{season}{titles_sec}{h2h_sec}{rank_sec}
<p class="small pl-src">Results, rankings and playing details from World Table Tennis. Biography, clubs, equipment and championship medals from {srcs or "published sources"}, checked {long_date(p.get("checked", dt.date.today().isoformat()))}.</p>
</div>
<aside class="article-side">{news_sec}{club_sec}{eq_sec}<div class="ad ad-side" data-ad="sidebar"></div></aside></div>
</main>
{components.SCRIPT}'''
        title = f'{p["name"]}: profile, results, rankings and titles | Eleven'
        desc = f'{p["name"]} ({p.get("nat")}): world ranking, recent results, season-by-season record, titles, head to heads and news.'
        open(os.path.join(ROOT, "players", p["slug"] + ".html"), "w", encoding="utf-8").write(page(title, desc, f"{site}/players/{p['slug']}.html", body))
        out_urls.append((f"{site}/players/{p['slug']}.html", dt.date.today().isoformat()))

    # ---- index
    def group(g):
        ps = sorted((p for p in profiles.values() if p.get("gender") == g), key=lambda p: ((ranks.get(p["ittf_id"]) or {}).get("rank", 999), p["name"]))
        top = [p for p in ps if (ranks.get(p["ittf_id"]) or {}).get("rank", 999) <= 10]
        rest = [p for p in ps if p not in top]
        cards = "".join(f'<li class="pl-tile"><a href="/players/{p["slug"]}.html">{player_card(p, (ranks.get(p["ittf_id"]) or {}).get("rank"), "small")}'
                        f'<span class="sr-only">{e(p["name"])}</span></a></li>' for p in top)
        lis = "".join(f'<li><span class="rk-pos">{(ranks.get(p["ittf_id"]) or {}).get("rank", "")}</span>{components.flag(p.get("nat"))}'
                      f'<a href="/players/{p["slug"]}.html">{e(p["name"])}</a><span class="rk-nat">{e(p.get("nat") or "")}</span></li>' for p in rest)
        return f'<ul class="pl-tiles">{cards}</ul>' + (f'<ul class="pl-all">{lis}</ul>' if lis else "")
    idx = f'''<main class="wrap pl-page">{components.subnav("players", "/players/")}<section class="sched-head"><div><h1>Players</h1>
<p class="lede">Every player in the world top 100: results, season-by-season records, titles, head to heads and the latest news.</p></div></section>
<div class="pl-tabs" role="tablist" aria-label="Rankings"><button role="tab" id="t-women" aria-controls="women" aria-selected="true">Women</button><button role="tab" id="t-men" aria-controls="men" aria-selected="false">Men</button></div>
<section class="hub-sec pl-panel" id="women" role="tabpanel" aria-labelledby="t-women"><h2 class="sr-only">Women</h2>{group("W")}</section>
<section class="hub-sec pl-panel" id="men" role="tabpanel" aria-labelledby="t-men"><h2 class="sr-only">Men</h2>{group("M")}</section>
<script>(function(){{var tabs=document.querySelectorAll('.pl-tabs button');function show(id){{tabs.forEach(function(t){{var on=t.getAttribute('aria-controls')===id;t.setAttribute('aria-selected',on);document.getElementById(t.getAttribute('aria-controls')).hidden=!on;}});}}
tabs.forEach(function(t){{t.addEventListener('click',function(){{var id=t.getAttribute('aria-controls');show(id);history.replaceState(null,'','#'+id);}});}});show(location.hash==='#men'?'men':'women');}})();</script></main>'''
    open(os.path.join(ROOT, "players", "index.html"), "w", encoding="utf-8").write(
        page("Players: profiles of the world's best | Eleven", "Profiles of the top table tennis players: results, records, titles and news.", f"{site}/players/", idx))
    out_urls.append((f"{site}/players/", dt.date.today().isoformat()))
    return out_urls, urls
