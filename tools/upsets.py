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

    out = []

    def add(w, l, when, comp, rnd, score, games, url, wid=None, lid=None):
        rw_ = by_id.get(wid) if wid else None
        rw_ = rw_ or by_name.get(key(w))
        rl_ = (by_id.get(lid) if lid else None) or by_name.get(key(l))
        if not rl_:
            return
        rw, rl = (rw_ or {}).get("rank", UNRANKED), rl_["rank"]
        lv = level(rw, rl)
        if not lv:
            return
        on = dt.date.fromisoformat(when[:10])
        aw = age(wid, on) if wid and wid in born else age(key(w), on)
        al = age(lid, on) if lid and lid in born else age(key(l), on)
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
        if games and len(games.split(",")) in (5, 7) and score and abs(score[0] - score[1]) == 1:
            angles.append("won in a deciding game")
        if score and min(score) == 0:
            angles.append("did not drop a game")
        out.append({"level": lv, "when": when, "competition": comp, "round": rnd,
                    "winner": {"name": rw_["name"] if rw_ else names.fix(w), "rank": rw if rw_ else None, "age": aw},
                    "loser": {"name": rl_["name"], "rank": rl, "age": al},
                    "score": f"{score[0]}-{score[1]}" if score else "", "games": games or "", "angles": angles, "url": url})

    # WTT and ITTF events
    P = load("data/matches/players.json", {})
    E = load("data/matches/events.json", {})
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "matches", "[0-9]*.json")))[-1:]:
        for m in load(os.path.relpath(f, ROOT), []):
            if (m.get("d") or "") < since or m.get("k") not in ("MS", "WS") or len(m["p"][0]) != 1:
                continue
            ev = E.get(m["e"], {})
            if re.search(r"youth|junior|cadet|U1\d|U2\d", ev.get("name", ""), re.I):
                continue
            w, l = m["w"], 1 - m["w"]
            wid, lid = m["p"][w][0], m["p"][l][0]
            nm = lambda i: names.from_wtt(*(P.get(i) or ["", ""]))
            sc = m.get("s")
            add(nm(wid), nm(lid), m["d"], ev.get("name", ""), ROUNDS.get(m.get("r"), ""), [sc[w], sc[l]] if sc else None,
                m.get("g"), "", wid, lid)
    # Club leagues
    for lg, label in (("tleague", "T.League"), ("ttbl", "Bundesliga")):
        LP = load(f"data/leagues/{lg}/players.json", {})
        seasons = sorted(glob.glob(os.path.join(ROOT, "data", "leagues", lg, "20*.json")))
        for f in seasons[-1:]:
            for t in load(os.path.relpath(f, ROOT), {}).get("ties", []):
                if (t.get("d") or "") < since:
                    continue
                for r in t.get("r", []):
                    if r.get("k") != "S" or r.get("w") is None:
                        continue
                    w, l = r["w"], 1 - r["w"]
                    nm = lambda i: names.from_wtt((LP.get(i) or {}).get("name", ""), "JPN" if lg == "tleague" else "")
                    sc = r.get("s")
                    add(nm(r["p"][w][0]), nm(r["p"][l][0]), t["d"], f'{label}: {t["home"]} v {t["away"]}', "",
                        [sc[w], sc[l]] if sc else None, r.get("g"), t.get("url", ""))
    order = {"shock": 0, "upset": 1, "notable": 2}
    out.sort(key=lambda u: (order[u["level"]], u["loser"]["rank"], -(u["winner"]["rank"] or UNRANKED)))
    json.dump({"updated": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%MZ"), "days": days, "upsets": out},
              open(os.path.join(ROOT, "data", "upsets.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    for u in main(int(sys.argv[1]) if len(sys.argv) > 1 else 4):
        print(u["level"], u["winner"], "beat", u["loser"], u["competition"], u["angles"])
