"""Shocks and upsets: singles results where the ranking gap makes the result news in itself.

Reads the WTT match database (data/matches) and the club leagues (data/leagues), compares each singles winner
with the loser in the current world rankings, and writes data/upsets.json for the news runs (see STYLE.md,
"Shocks and upsets"). Called from build_site.py; run on its own with `python3 tools/upsets.py [days]`.

Levels, from the loser's ranking and the gap:
  shock    the loser is a top-10 player and the winner is outside the top 100, or the loser is top 3 and the winner
           outside the top 50, or the winner is ranked at least 25 times lower (loser in the top 20)
  upset    the loser is top 50 and the winner ranked at least 5 times lower, or a top-10 loser to someone outside the top 30
  notable  the loser is top 100 and the winner ranked at least 3 times lower
Unranked winners count as ranked 1,000. "angles" lists what else makes it a story (age, round, a deciding game).
"""
import datetime as dt, glob, json, os, re, sys, unicodedata

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import names

UNRANKED = 1000
ROUNDS = {"FNL": "final", "SFNL": "semi-final", "QFNL": "quarter-final", "R16": "last 16"}


def key(n):
    n = unicodedata.normalize("NFKD", n or "").encode("ascii", "ignore").decode().lower()
    return " ".join(sorted(re.findall(r"[a-z]+", n)))


def load(p, default):
    try:
        return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))
    except Exception:
        return default


def level(rw, rl):
    if rl <= 10 and rw > 100 or rl <= 3 and rw > 50 or rl <= 20 and rw >= 25 * rl:
        return "shock"
    if rl <= 50 and rw >= 5 * rl or rl <= 10 and rw > 30:
        return "upset"
    if rl <= 100 and rw >= 3 * rl:
        return "notable"
    return None


def main(days=4):
    R = load("data/rankings.json", {})
    by_id, by_name = {}, {}
    for g in ("men", "women"):
        for r in R.get(g, []):
            by_id[str(r.get("ittf_id"))] = r
            by_name[key(r["name"])] = r
    born = {}
    for f in glob.glob(os.path.join(ROOT, "data", "players", "*.json")):
        try:
            p = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(p, dict) and p.get("born") and p.get("name"):
            born[key(p["name"])] = p["born"]
            if p.get("ittf_id"):
                born[str(p["ittf_id"])] = p["born"]
    wtt = load("data/players/wtt.json", {})
    for i, w in wtt.items():
        m = re.match(r"(\d\d)/(\d\d)/(\d{4})", w.get("dob") or "")
        if m and i not in born:
            born[i] = f"{m[3]}-{m[1]}-{m[2]}"
    today = dt.date.today()
    since = (dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(days=days)).isoformat()

    def age(k, on):
        b = born.get(k)
        if not b:
            return None
        b = dt.date.fromisoformat(b[:10])
        return on.year - b.year - ((on.month, on.day) < (b.month, b.day))

    out, lines = [], []

    # Head-to-head and streak history from the WTT match database (singles, every season on file)
    hist = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "matches", "[0-9]*.json"))):
        for m in load(os.path.relpath(f, ROOT), []):
            if m.get("k") in ("MS", "WS") and len(m["p"][0]) == 1 and m.get("w") in (0, 1) and m.get("d"):
                hist.append((m["d"], m["p"][m["w"]][0], m["p"][1 - m["w"]][0], m["e"]))
    hist.sort()
    E_ = load("data/matches/events.json", {})

    def history(wid, lid, when):
        """Labels that need earlier matches: streaks, revenge, a first top-10 win, a perfect week."""
        got = []
        before = [h for h in hist if h[0] < when]
        run = 0
        for d, a, b, ev in reversed(before):
            if a == wid:
                run += 1
            elif b == wid:
                break
        if run + 1 >= 10 and (run + 1) % 5 == 0:
            got.append(("streak", f"{run + 1}th win in a row"))
        lrun = 0
        for d, a, b, ev in reversed(before):
            if a == lid:
                lrun += 1
            elif b == lid:
                break
        if lrun >= 10:
            got.append(("streak", f"ended the loser's {lrun}-match winning run"))
        year_ago = (dt.datetime.fromisoformat(when[:19]) - dt.timedelta(days=365)).isoformat()
        prev = [h for h in before if h[0] >= year_ago and {h[1], h[2]} == {wid, lid}]
        if prev and prev[-1][1] == lid:
            got.append(("revenge", f"revenge for defeat at {(E_.get(prev[-1][3]) or {}).get('name', 'an earlier event')} ({prev[-1][0][:7]})"))
        rl = (by_id.get(lid) or {}).get("rank", UNRANKED)
        if rl <= 10 and not any(h[1] == wid and (by_id.get(h[2]) or {}).get("rank", UNRANKED) <= 10 for h in before):
            got.append(("first", "first win over a current top-10 player on record"))
        return got

    def labels(score, games, du, rw, rl):
        """Labels from the scoreline, the game-by-game points and the match length (STYLE.md, "Match labels")."""
        got = []
        if not score:
            return got
        need, gl = max(score), score[1]
        gs = [tuple(int(x) for x in g.split("-")) for g in (games or "").split(",") if re.match(r"^\d+-\d+$", g.strip())]
        gs = [g for g in gs if g != (0, 0)]
        deuce = sum(1 for a, b in gs if max(a, b) > 11)
        mins = None
        m_ = re.match(r"(\d+):(\d+)", du or "")
        if m_:
            mins = int(m_[1]) * 60 + int(m_[2])
        if gl == 0:
            if gs and all(a - b >= 6 for a, b in gs):
                got.append(("hammering", f"dropped {sum(b for a, b in gs)} points in {len(gs)} games"))
            else:
                got.append(("sweep", f"{need}-0" + (f", {deuce} of the games went to deuce" if deuce >= 2 else "")))
        ww = ll = worst = 0
        led = 0
        for a, b in gs:
            ww, ll = ww + (a > b), ll + (b > a)
            worst = max(worst, ll - ww)
            led = max(led, ll - ww if ll >= need - 1 else 0)
        if gs and worst >= 2:
            rev = need == 3 and [x > y for x, y in gs] == [False, False, True, True, True]
            got.append(("comeback", "reverse sweep: 0-2 to 3-2" if rev else f"came back from {worst} games down"))
        if gs and len(gs) == 2 * need - 1:
            a, b = gs[-1]
            got.append(("edged", ("five-game thriller" if need == 3 else "seven-game epic") + (f", decider {a}-{b}" if a - b <= 2 else "")))
        if any(max(a, b) == 11 and min(a, b) == 10 for a, b in gs):
            got.append(("sudden death", "a game settled on the T.League's sudden-death point at 10-10"))
        if (mins and mins >= (60 if need == 3 else 75)) or (deuce >= 3 and gl > 0):
            got.append(("ground out", ", ".join(x for x in [f"{mins} minutes" if mins else "", f"{deuce} deuce games" if deuce >= 2 else ""] if x)))
        if any(a == 11 and b == 0 for a, b in gs):
            got.append(("11-0 game", "won a game 11-0"))
        fav = rw < rl
        if fav and gs and len(gs) == 2 * need - 1 and rl >= 3 * rw:
            got.append(("scare", f"No {rw} pushed to a decider by No {rl if rl < UNRANKED else 'unranked'}"))
        if fav and not deuce and len(gs) < 2 * need - 1 and not any(k in ("hammering", "comeback") for k, _ in got):
            got.append(("routine", ""))
        return got

    def add(w, l, when, comp, rnd, score, games, url, wid=None, lid=None, du=None, ev=None):
        rw_ = by_id.get(wid) if wid else None
        rw_ = rw_ or by_name.get(key(w))
        rl_ = (by_id.get(lid) if lid else None) or by_name.get(key(l))
        rw, rl = (rw_ or {}).get("rank", UNRANKED), (rl_ or {}).get("rank", UNRANKED)
        on = dt.date.fromisoformat(when[:10])
        aw = age(wid, on) if wid and wid in born else age(key(w), on)
        al = age(lid, on) if lid and lid in born else age(key(l), on)
        lab = labels(score, games, du, rw, rl) + (history(wid, lid, when) if wid and lid else [])
        if rnd == "final" and ev and wid:
            mine = [h for h in hist if h[3] == ev and wid in (h[1], h[2])]
            if mine and all(h[1] == wid for h in mine) and gl0(ev, wid):
                lab.append(("perfect week", "won the title without dropping a game"))
        lv = level(rw, rl) if rl_ else None
        row = {"when": when, "competition": comp, "round": rnd,
               "winner": {"name": rw_["name"] if rw_ else names.fix(w), "rank": rw if rw_ else None, "age": aw},
               "loser": {"name": rl_["name"] if rl_ else names.fix(l), "rank": rl if rl_ else None, "age": al},
               "score": f"{score[0]}-{score[1]}" if score else "", "games": games or "", "url": url,
               "labels": [{"label": k, "detail": d} for k, d in lab]}
        if min(rw, rl) <= 300 or comp.startswith(("T.League", "Bundesliga")):
            if any(k != "routine" for k, _ in lab) or lv:
                lines.append({**row, "level": lv})
        if not lv:
            return
        angles = []
        if rl == 1:
            angles.append("beat the world No 1")
        elif rl <= 10:
            angles.append(f"beat a top-10 player (No {rl})")
        if aw is not None and aw <= 17:
            angles.append(f"winner is {aw}")
        if aw is not None and aw >= 35:
            angles.append(f"winner is {aw}")
        if aw is not None and al is not None and abs(aw - al) >= 10:
            angles.append(f"{abs(aw - al)}-year age gap")
        if rnd in ("final", "semi-final"):
            angles.append(f"in the {rnd}")
        angles += [d or k for k, d in lab if k != "routine"]
        out.append({**row, "level": lv, "angles": angles})

    GL = {}

    def gl0(ev, wid):
        """True when the player dropped no game in any singles match of the event."""
        if (ev, wid) not in GL:
            ok = True
            for f in sorted(glob.glob(os.path.join(ROOT, "data", "matches", "[0-9]*.json")))[-1:]:
                for m in load(os.path.relpath(f, ROOT), []):
                    if m.get("e") == ev and m.get("k") in ("MS", "WS") and wid in (m["p"][0] + m["p"][1]):
                        sc = m.get("s") or [0, 0]
                        side = 0 if wid in m["p"][0] else 1
                        if sc[1 - side] > 0:
                            ok = False
            GL[(ev, wid)] = ok
        return GL[(ev, wid)]

    # WTT and ITTF events
    P = load("data/matches/players.json", {})
    E = E_
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "matches", "[0-9]*.json")))[-1:]:
        for m in load(os.path.relpath(f, ROOT), []):
            if (m.get("d") or "") < since or m.get("k") not in ("MS", "WS") or len(m["p"][0]) != 1 or m.get("w") not in (0, 1):
                continue
            ev = E.get(m["e"], {})
            if re.search(r"youth|junior|cadet|U1\d|U2\d", ev.get("name", ""), re.I):
                continue
            w, l = m["w"], 1 - m["w"]
            wid, lid = m["p"][w][0], m["p"][l][0]
            nm = lambda i: names.from_wtt(*(P.get(i) or ["", ""]))
            sc = m.get("s")
            g = m.get("g") or ""
            if w == 1:
                g = ",".join("-".join(reversed(x.split("-"))) for x in g.split(",") if x)
            add(nm(wid), nm(lid), m["d"], ev.get("name", ""), ROUNDS.get(m.get("r"), ""), [sc[w], sc[l]] if sc else None,
                g, "", wid, lid, m.get("du"), m["e"])
    # Club leagues: each singles rubber, then the tie itself
    ties = []
    for lg, label in (("tleague", "T.League"), ("ttbl", "Bundesliga")):
        LP = load(f"data/leagues/{lg}/players.json", {})
        seasons = sorted(glob.glob(os.path.join(ROOT, "data", "leagues", lg, "20*.json")))
        for f in seasons[-1:]:
            for t in load(os.path.relpath(f, ROOT), {}).get("ties", []):
                if (t.get("d") or "") < since or t.get("st") != "done":
                    continue
                for r in t.get("r", []):
                    if r.get("k") != "S" or r.get("w") not in (0, 1):
                        continue
                    w, l = r["w"], 1 - r["w"]
                    nm = lambda i: names.from_wtt((LP.get(i) or {}).get("name", ""), "JPN" if lg == "tleague" else "")
                    if any(i.startswith("9999") for i in r["p"][0] + r["p"][1]) or not nm(r["p"][0][0]).strip() or not nm(r["p"][1][0]).strip():
                        continue   # a placeholder player (a walkover or an unnamed substitute)
                    sc = r.get("s")
                    g = r.get("g") or ""
                    if lg == "tleague":
                        # tleague.jp shows a game settled on the sudden-death point as 10-10 (or 10-9): give it to the side
                        # ahead, or at 10-10 to the rubber's winner, as 11-10, and recount the games
                        gg = []
                        for x in g.split(","):
                            if not re.match(r"^\d+-\d+$", x):
                                continue
                            a, b = (int(y) for y in x.split("-"))
                            if max(a, b) == 10:
                                if a > b or (a == b and w == 0):
                                    a, b = 11, 10
                                else:
                                    a, b = 10, 11
                                sudden = True
                            gg.append((a, b))
                        sc = [sum(a > b for a, b in gg), sum(b > a for a, b in gg)]
                        g = ",".join(f"{a}-{b}" for a, b in gg)
                        if max(sc) < 2:
                            continue   # an incomplete record
                    if w == 1:
                        g = ",".join("-".join(reversed(x.split("-"))) for x in g.split(",") if x)
                    add(nm(r["p"][w][0]), nm(r["p"][l][0]), t["d"], f'{label}: {t["home"]} v {t["away"]}', "",
                        [sc[w], sc[l]] if sc else None, g, t.get("url", ""))
                s_ = t.get("s") or [0, 0]
                if s_[0] == s_[1] or max(s_) < 3:
                    continue   # a draw, or a tie whose record is incomplete
                tw = 0 if s_[0] > s_[1] else 1
                need, tl = max(s_), min(s_)
                lab = []
                if tl == 0:
                    lab.append(("team whitewash", f"{need}-0"))
                if tl == need - 1:
                    lab.append(("final rubber", "decided in the last rubber"))
                a = b = worst = 0
                for r in t.get("r", []):
                    if r.get("w") not in (0, 1):
                        continue
                    a, b = a + (r["w"] == tw), b + (r["w"] != tw)
                    worst = max(worst, b - a)
                if worst >= 2:
                    lab.append(("team turnaround", f"came back from {worst} rubbers down"))
                if lab:
                    names_ = [t["home"], t["away"]]
                    ties.append({"when": t["d"], "competition": label, "winner": names_[tw], "loser": names_[1 - tw],
                                 "score": f"{need}-{tl}", "url": t.get("url", ""), "labels": [{"label": k, "detail": d} for k, d in lab]})
    order = {"shock": 0, "upset": 1, "notable": 2, None: 3}
    out.sort(key=lambda u: (order[u["level"]], u["loser"]["rank"] or UNRANKED, -(u["winner"]["rank"] or UNRANKED)))
    lines.sort(key=lambda u: (order[u["level"]], min(u["winner"]["rank"] or UNRANKED, u["loser"]["rank"] or UNRANKED)))
    json.dump({"updated": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%MZ"), "days": days,
               "upsets": out, "matches": lines[:120], "ties": ties},
              open(os.path.join(ROOT, "data", "upsets.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
    d = json.load(open(os.path.join(ROOT, "data", "upsets.json"), encoding="utf-8"))
    for u in d["matches"]:
        print(u["level"] or "-", u["winner"]["name"], u["winner"]["rank"], "bt", u["loser"]["name"], u["loser"]["rank"], u["score"], u["competition"][:40], [x["label"] + (": " + x["detail"] if x["detail"] else "") for x in u["labels"]])
    for t in d["ties"]:
        print("TIE", t["winner"], t["score"], t["loser"], [x["label"] for x in t["labels"]])
