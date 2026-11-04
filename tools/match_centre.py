"""Match centre for event pages: every match, by day, in the style of a live-score site.

One tab per day of the tournament. Each day lists its matches in order of play under its sessions,
with the time and table before a match, and the score and game scores after it. A filter shows all
matches or one event (women's or men's singles). Live scores and fresh results are added in the browser
by /live.js (rows carry data-key, the two players' names), and a played match opens point by point
(rows carry data-match, read by /matchpop.js).

Built from data/schedule.json (WTT's order of play and the session times) and data/draws/<id>.json
(players, seeds, scores and the times of played matches).
"""
import json, os, re, html, datetime as dt
import components

e = html.escape
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UK = components.UK
ROUNDS = {"last 64": "last 64", "last 32": "last 32", "last 16": "last 16", "quarter-finals": "quarter-final",
          "semi-finals": "semi-final", "final": "final"}


def key_of(names):
    return "|".join(sorted(n.strip().lower() for n in names))


def code_of(fid, wtt):
    """WTT's document code from a fixture id: 'wtt-3252-ttewsinglesr32001600' -> 'TTEWSINGLES-----------R32-001600----------'."""
    k = fid[len(f"wtt-{wtt}-"):].upper()
    if len(k) < 12 or not k[-6:].isdigit():
        return None
    return f"{k[:11]:-<22}{k[11:-6]}-{k[-6:]}".ljust(42, "-")


def _round(label):
    s = label.lower().replace("semifinal", "semi-final").replace("quarterfinal", "quarter-final")
    return ROUNDS.get(s, s)


def _gender(label):
    l = label.lower()
    return "w" if "women" in l else "x" if "mixed" in l else "m" if "men" in l else "o"


def _uk(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(UK)


def _people(draw):
    out = {}
    path = os.path.join(ROOT, "data", "rankings.json")
    if os.path.exists(path):
        rk = json.load(open(path, encoding="utf-8"))
        for g in ("men", "women"):
            for p in rk.get(g, []):
                out[p["name"].lower()] = {"nat": p["nat"], "rank": p["rank"]}
    for ev in (draw or {}).get("events", {}).values():
        for r in ev.get("rounds", []):
            for m in r.get("matches", []):
                for p in m.get("players") or []:
                    if p and p.get("name"):
                        out.setdefault(p["name"].lower(), {}).update({k: p[k] for k in ("nat", "seed") if p.get(k)})
    return out


def _parse_score(score, winner):
    """'3-2 (11:8,11:8,3:11,10:12,11:2)' -> ([3, 2], [[11, 8], ...]) from the first player's side."""
    if not score:
        return None, []
    head, _, rest = score.partition(" ")
    try:
        sets = [int(x) for x in head.replace("–", "-").split("-")]
    except ValueError:
        return None, []
    games = [[int(a), int(b)] for a, b in re.findall(r"(\d+):(\d+)", rest) if (a, b) != ("0", "0")]
    return sets, games


def rows(ev, schedule):
    """Every known match of the event as a dict, with a time where one is known."""
    wtt = ev.get("wtt_id") or ev.get("draw")
    draw = None
    if ev.get("draw"):
        path = os.path.join(ROOT, "data", "draws", f'{ev["draw"]}.json')
        draw = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None
    people = _people(draw)
    sid = ev.get("schedule_id")
    fx = [f for f in schedule.get("fixtures", []) if sid and f.get("event_id") == sid]
    sessions = [f for f in fx if not f["id"].startswith("wtt-") and " v " not in f["name"]]

    # The draw, by pair of players
    drawn = {}
    for g, dev in ((draw or {}).get("events") or {}).items():
        for r in dev.get("rounds", []):
            for m in r.get("matches", []):
                ps = m.get("players") or []
                if len(ps) == 2 and all(ps):
                    drawn[key_of([p["name"] for p in ps])] = {"event": dev["name"], "round": _round(r["round"]), "m": m}

    # One table in use: name the venue instead of "Table 1"
    tables = {f.get("detail") for f in fx if f.get("detail")}
    venue = ev.get("venue") if len(tables) <= 1 else None
    out, used = [], set()
    prefix = ev["name"] + ": "
    for f in fx:
        if not (wtt and f["id"].startswith(f"wtt-{wtt}-")):
            continue
        rest = f["name"].removeprefix(prefix)
        if " v " in rest.split(", ")[0]:
            pair, *lab = rest.split(", ")
            names = [n.strip() for n in pair.split(" v ")]
        else:   # players not known yet: "Women's Singles, Semifinal, Match 1"
            names, lab = [], [x for x in rest.split(", ") if not x.lower().startswith("match ")]
        label = ", ".join(lab)
        k = key_of(names) if names else None
        d = drawn.get(k) if k else None
        if k:
            used.add(k)
        sets, games = _parse_score((d or {}).get("m", {}).get("score"), (d or {}).get("m", {}).get("winner"))
        out.append({"when": f["start"], "table": venue or f.get("detail") or "", "code": f.get("code") or code_of(f["id"], wtt),
                    "event": (lab[0][:1].upper() + lab[0][1:]) if lab else "", "round": _round(lab[1]) if len(lab) > 1 else "",
                    "players": [{"name": n, **people.get(n.lower(), {})} for n in names], "key": k,
                    "sets": sets, "games": games, "winner": (d or {}).get("m", {}).get("winner")})
    # Played matches whose order-of-play entry has gone: time and score from the draw
    for k, d in drawn.items():
        m = d["m"]
        if k in used or not m.get("when"):
            continue
        sets, games = _parse_score(m.get("score"), m.get("winner"))
        out.append({"when": m["when"], "table": "", "code": None, "event": d["event"], "round": d["round"],
                    "players": [{**people.get(p["name"].lower(), {}), **p} for p in m["players"]], "key": k,
                    "sets": sets, "games": games, "winner": m.get("winner")})
    return sorted(out, key=lambda r: r["when"]), sessions


def _player(p, won):
    if not p:
        return '<span class="mc-p tbd">To be decided</span>'
    rank = f'<span class="wr" title="World No {p["rank"]}">{p["rank"]}</span>' if p.get("rank") else ""
    return f'<span class="mc-p{" won" if won else ""}">{components.flag(p.get("nat"))}<span class="nm">{e(p["name"])}</span>{rank}</span>'


def _row(r, wtt):
    t = _uk(r["when"])
    played = r["sets"] is not None and r["winner"] in (0, 1)
    ps = r["players"] + [None] * (2 - len(r["players"]))
    names = "".join(_player(p, played and r["winner"] == i) for i, p in enumerate(ps[:2]))
    sets = "".join(f'<b class="{"won" if played and r["winner"] == i else ""}">{r["sets"][i] if played else ""}</b>' for i in range(2))
    games = "".join(f'<span><i class="{"w" if g[0] > g[1] else ""}">{g[0]}</i><i class="{"w" if g[1] > g[0] else ""}">{g[1]}</i></span>' for g in r["games"]) if played else ""
    label = " · ".join(x for x in (f'{r["event"]}, {r["round"]}' if r["round"] else r["event"], r["table"]) if x)
    attrs = f' data-key="{e(r["key"])}"' if r["key"] else ""
    if r["code"] and r["key"]:
        attrs += f' data-match="{e(str(wtt))}|{e(r["code"])}" tabindex="0" role="button"'
    status = "Result" if played else f"{t:%H:%M}"
    return f'''<li class="mc-row{" done" if played else ""}" data-g="{_gender(r["event"])}"{attrs}>
<span class="mc-time"><time datetime="{e(r["when"])}" data-lt="hm">{status}</time></span>
<span class="mc-main"><span class="mc-label">{e(label)}</span>{names}</span>
<span class="mc-sets">{sets}</span><span class="mc-games">{games}</span></li>'''


def section(ev, schedule, today_iso=None):
    """The Matches section, or "" if there is nothing to show."""
    matches, sessions = rows(ev, schedule)
    if not matches:
        return ""
    wtt = ev.get("wtt_id") or ev.get("draw")
    start, end = dt.date.fromisoformat(ev["start"]), dt.date.fromisoformat(ev["end"])
    days = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
    today = dt.date.fromisoformat(today_iso) if today_iso else dt.datetime.now(UK).date()
    pick = today if start <= today <= end else (start if today < start else end)
    by_day = {d: [] for d in days}
    for r in matches:
        d = _uk(r["when"]).date()
        if d in by_day:
            by_day[d].append(r)
    sess_by_day = {d: sorted((s for s in sessions if _uk(s["start"]).date() == d), key=lambda s: s["start"]) for d in days}

    tabs, panels = [], []
    for d in days:
        n = len(by_day[d])
        sel = d == pick
        tabs.append(f'<button type="button" role="tab" data-day="{d.isoformat()}" aria-selected="{str(sel).lower()}">'
                    f'<span>{"Today" if d == today else f"{d:%a}"}</span><b>{d.day} {d:%b}</b><small>{n} match{"es" if n != 1 else ""}</small></button>')
        items, ss = [], sess_by_day[d]
        for i, s in enumerate(ss):   # matches under the session they fall in
            nxt = _uk(ss[i + 1]["start"]) if i + 1 < len(ss) else None
            mine = [r for r in by_day[d] if _uk(r["when"]) >= _uk(s["start"]) - dt.timedelta(minutes=5) and (nxt is None or _uk(r["when"]) < nxt - dt.timedelta(minutes=5))]
            name = s["name"].removeprefix(ev["name"] + ": ")
            name = name[:1].upper() + name[1:]
            items.append(f'<li class="mc-sess"><span>{e(name)}</span><time datetime="{e(s["start"])}" data-lt="hm">{_uk(s["start"]):%H:%M}</time></li>')
            items += [_row(r, wtt) for r in mine]
        if not ss:
            items += [_row(r, wtt) for r in by_day[d]]
        else:   # anything before the first session
            first = _uk(ss[0]["start"]) - dt.timedelta(minutes=5)
            early = [r for r in by_day[d] if _uk(r["when"]) < first]
            items = [_row(r, wtt) for r in early] + items
        note = "" if by_day[d] else '<p class="mc-empty">The matches for this day appear here once WTT publishes the order of play, usually the evening before.</p>'
        panels.append(f'<div class="mc-day" role="tabpanel" data-day="{d.isoformat()}"{"" if d == pick else " hidden"}><ol class="mc-list">{"".join(items)}</ol>{note}</div>')

    genders = {_gender(r["event"]) for r in matches} - {"o"}
    names = {"w": "Women's singles", "m": "Men's singles", "x": "Mixed"}
    filt = ""
    if len(genders) > 1:
        filt = '<div class="toggle mc-filter" role="group" aria-label="Show">' + '<button type="button" data-g="all" aria-pressed="true">All</button>' + "".join(
            f'<button type="button" data-g="{g}" aria-pressed="false">{names[g]}</button>' for g in ("w", "m", "x") if g in genders) + "</div>"
    return f'''<section class="hub-sec mc" id="matches" aria-labelledby="matches-h"{f' data-wtt="{e(str(ev["wtt_id"]))}"' if ev.get("wtt_id") else ""}>
<div class="mc-head"><h2 class="section-title" id="matches-h">Matches</h2>{filt}</div>
<div class="mc-tabs" role="tablist" aria-label="Day">{"".join(tabs)}</div>
{"".join(panels)}
<p class="small mc-note"><span data-tz-note>Times are UK time.</span> Times are approximate: matches can start late or run over, so a match may not have started when its time passes. Tap a played match for point by point. Order of play and results from World Table Tennis.</p>
</section>'''
