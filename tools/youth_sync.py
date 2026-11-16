"""Youth results for player profiles: WTT Youth and ITTF junior events, under-17 categories and older only.

Kept apart from the senior match database (tools/match_sync.py), so news, records, upsets and the senior
results on profiles are unchanged. Profiles on Eleven and The Chop show them in their own "Youth events" list,
which explains ranking points earned at youth events (WTT Youth Contenders award world ranking points).

Eleven's age rule (UPDATE.md): no coverage of under-15 level on Eleven, so its profiles skip U15 results ("a": "U15").
Tom approved U15 results for The Chop's defenders (16 Nov 2026). U13 and U11 are never stored.

Writes data/matches/youth/<year>.json (matches in match_sync's format, plus "a": the age category, e.g. "U19")
and data/matches/youth/events.json (event id -> name, dates, n, done).
Runs from .github/workflows/match-sync.yml after the senior sync: python3 tools/youth_sync.py [--backfill]
--backfill looks at every youth or junior event in data/matches/events.json since FROM_YEAR; otherwise only
those not yet done.
"""
import json, os, re, sys, datetime as dt

sys.path.insert(0, os.path.dirname(__file__))
import match_sync as ms

ROOT = ms.ROOT
YDIR = os.path.join(ROOT, "data", "matches", "youth")
FROM_YEAR = "2025"
KEEP = {"U15", "U17", "U19", "U21"}    # U15 approved by Tom (16 Nov 2026) for The Chop only; Eleven's own profiles show U17 and older
YOUTH = re.compile(r"Youth|Junior", re.I)
NOT = re.compile(r"Para |Veteran|Masters|Hopes|Development|^\s*(TEST|SIM)\b", re.I)


def compact_youth(r, players):
    code = r.get("documentCode") or ""
    if len(code) < 30 or not code.startswith("TTE"):
        return None
    cat = code[11:22].strip("-")
    if cat not in KEEP:
        return None
    r2 = dict(r)
    r2["documentCode"] = code[:11] + "-" * 11 + code[22:]   # let match_sync's parser read it as an open-age match
    m = ms.compact(r2, players)
    if m:
        m["a"] = cat
    return m


def main():
    import switches
    if not switches.on("wtt"):
        return
    os.makedirs(YDIR, exist_ok=True)
    senior = ms.load(os.path.join(ms.MDIR, "events.json"), {})
    evs = ms.load(os.path.join(YDIR, "events.json"), {})
    players = ms.load(os.path.join(ms.MDIR, "players.json"), {})
    years = {f[:4]: ms.load(os.path.join(YDIR, f), []) for f in os.listdir(YDIR) if re.fullmatch(r"\d{4}\.json", f)}
    cands = [k for k, v in senior.items() if YOUTH.search(v.get("name") or "") and not NOT.search(v.get("name") or "")
             and ((v.get("end") or "") >= FROM_YEAR or (not v.get("end") and int(k) >= 2950))]
    if "--backfill" not in sys.argv:
        cands = [k for k in cands if not evs.get(k, {}).get("done")]
    added = 0
    for eid in sorted(set(cands), key=int):
        try:
            rs = ms.get(f"{ms.LIVE}/GetOfficialResult?EventId={eid}&include_match_card=true&take=5000")
        except Exception as err:
            print(eid, err)
            continue
        got = [m for m in (compact_youth(r, players) for r in rs or []) if m]
        dates = sorted(m["d"][:10] for m in got if m.get("d"))
        ev = evs.setdefault(eid, {})
        ev.update({"name": senior.get(eid, {}).get("name", ""), "n": len(got), "start": dates[0] if dates else None, "end": dates[-1] if dates else None})
        ev["done"] = bool(dates) and dates[-1] < (dt.date.today() - dt.timedelta(days=3)).isoformat()
        if dates and dates[-1][:4] < FROM_YEAR:
            ev["done"] = True
            continue
        for y in years.values():
            y[:] = [m for m in y if m["e"] != eid]
        for m in got:
            years.setdefault((m.get("d") or ev["end"] or "0000")[:4], []).append(m)
        added += len(got)
        if got:
            print(f"{eid} {ev['name']}: {len(got)} youth matches")
    for y, lst in years.items():
        lst.sort(key=lambda m: (m.get("d") or "", m["e"]))
        ms.save(os.path.join(YDIR, f"{y}.json"), lst)
    ms.save(os.path.join(YDIR, "events.json"), dict(sorted(evs.items(), key=lambda kv: int(kv[0]))), indent=1)
    ms.save(os.path.join(ms.MDIR, "players.json"), dict(sorted(players.items())))
    print(f"youth: {added} matches")


if __name__ == "__main__":
    main()
