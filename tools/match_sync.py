"""Eleven's match database: every senior match at WTT and ITTF events, from WTT's official results.

Runs on GitHub Actions (.github/workflows/match-sync.yml), nightly, and commits:
  data/matches/events.json     event id -> name, dates, number of matches, done
  data/matches/<year>.json     the matches of that year (compact, see below)
  data/matches/players.json    ITTF id -> [name as WTT spells it, association]
  data/players/wtt.json        WTT's own player record for profiled and top-100 players (birth date, hand, grip, stats)
  data/ranking-history.json    the world top 100 each week, appended when data/rankings.json changes

A match: {"e": event id, "k": MS|WS|MD|WD|XD|MT|WT|XT, "r": round code (FNL, SFNL, QFNL, 8FNL, R32 ...), "d": UTC start,
          "p": [[ids side A], [ids side B]], "s": [games A, games B], "g": "11-7,9-11,..." (side A first),
          "w": 0 or 1 (winner side), "du": "00:55:33", "wo": 1 for a walkover, "tm": 1 for a match inside a team tie}

Usage: python3 tools/match_sync.py                 nightly: events on now, recent and new ids
       python3 tools/match_sync.py --backfill A B  every event id from A to B (one-off)
"""
import json, os, sys, re, time, datetime as dt, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LIVE = "https://wtt-website-api-vm-frontdoor-hhaec5epbhdyfugz.a01.azurefd.net/liveeventsapi/api/cms"
CMS = "https://wtt-website-api-vm-frontdoor-hhaec5epbhdyfugz.a01.azurefd.net/primary/api/cms"
HEADERS = {"Origin": "https://www.worldtabletennis.com", "Referer": "https://www.worldtabletennis.com/", "User-Agent": "Mozilla/5.0 (Eleven table tennis news)"}
FIRST_YEAR = 2021   # WTT's first season
SKIP_NAMES = re.compile(r"Youth|U1[0-9]|U2[01]|Junior|Cadet|Para |Veteran|Masters|Hopes|Development", re.I)
MDIR = os.path.join(ROOT, "data", "matches")


def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
                return json.load(r)
        except Exception as err:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def load(path, default):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


def save(path, data, indent=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))
        f.write("\n")


def utc(s):
    """'10/11/2026 10:00:00' -> '2026-10-11T10:00:00Z'"""
    try:
        return dt.datetime.strptime(s, "%m/%d/%Y %H:%M:%S").strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def compact(r, players):
    """One WTT result -> a match record, or None (youth, unplayed, a team tie itself)."""
    code = r.get("documentCode") or ""
    if len(code) < 30 or not code.startswith("TTE"):
        return None
    if code[11:22].strip("-"):      # age category (U19, U15 ...): not senior
        return None
    if (r.get("fullResults") or "").upper() != "OFFICIAL":
        return None
    mc = r.get("match_card") or {}
    sides = mc.get("competitiors") or mc.get("competitors") or []
    if len(sides) != 2:
        return None
    ids = []
    for c in sides:
        ps = [p for p in (c.get("players") or []) if p.get("playerId")]
        if not 1 <= len(ps) <= 2:
            return None             # a team tie, or no players
        ids.append([p["playerId"] for p in ps])
        for p in ps:
            players[p["playerId"]] = [p.get("playerName") or c.get("competitiorName"), p.get("playerOrgCode") or c.get("competitiorOrg")]
    gender, kind = code[3], code[4:11]
    k = {"SINGLES": "S", "DOUBLES": "D", "TEAM---": "T"}.get(kind, "?")
    if kind.startswith("TEAM"):
        k = "T"
    if k == "?" or gender not in "MWX":
        return None
    m = {"e": str(r.get("eventId")), "k": gender + k, "r": code[22:26].strip("-"), "p": ids}
    when = utc((mc.get("matchDateTime") or {}).get("startDateUTC") or "")
    if when:
        m["d"] = when
    elif r.get("startDateLocal"):
        m["d"] = r["startDateLocal"][:19] + "L"   # local time only
    irm = [c.get("irm") if (c.get("irm") or "").upper() not in ("", "OK") else None for c in sides]
    ov = (mc.get("resultOverallScores") or mc.get("overallScores") or "").split("-")
    try:
        s = [int(ov[0]), int(ov[1])]
    except Exception:
        s = None
    if any(irm):
        m["wo"] = 1
        m["w"] = 1 if irm[0] else 0
    elif s and s[0] != s[1]:
        m["s"] = s
        m["w"] = 0 if s[0] > s[1] else 1
    else:
        return None
    g = mc.get("resultsGameScores") or mc.get("gameScores") or ""
    g = ",".join(x for x in g.split(",") if x and x != "0-0")
    if g and not m.get("wo"):
        m["g"] = g
    du = (mc.get("matchDateTime") or {}).get("duration")
    if du and du != "00:00:00":
        m["du"] = du
    if k == "S" and (mc.get("teamParentData") or (mc.get("teamMatchNo") not in (None, "0", 0))):
        m["tm"] = 1
    if gender + k in ("MT", "WT", "XT"):
        m["tm"] = 1
    return m


BRACKET_CODES = {"MS": "TTEMSINGLES", "WS": "TTEWSINGLES", "MD": "TTEMDOUBLES", "WD": "TTEWDOUBLES", "XD": "TTEXDOUBLES"}
BRACKET_NAMES = {"MS": "Men's Singles", "WS": "Women's Singles", "MD": "Men's Doubles", "WD": "Women's Doubles", "XD": "Mixed Doubles"}


def from_brackets(eid, players):
    """Older events have results without match cards: read their draws instead (main draw and qualifying)."""
    out = []
    for k, code in BRACKET_CODES.items():
        try:
            j = get(f"{LIVE}/GetBrackets/{eid}/{code.ljust(42, '-')}")
        except Exception:
            continue
        comp = j.get("Competition") or {}
        nm = ((comp.get("ExtendedInfos") or {}).get("SportDescription") or {}).get("EventName")
        if nm != BRACKET_NAMES[k]:
            continue
        for br in comp.get("Bracket") or []:
            for rd in br.get("BracketItems") or []:
                for it in rd.get("BracketItem") or []:
                    places = sorted(it.get("CompetitorPlace") or [], key=lambda x: x.get("Pos", 0))
                    if len(places) != 2 or not it.get("Result"):
                        continue
                    ids, ok = [], True
                    for pl in places:
                        c = pl.get("Competitor") or {}
                        ath = ((c.get("Composition") or {}).get("Athlete")) or []
                        if not 1 <= len(ath) <= 2:
                            ok = False
                            break
                        ids.append([a.get("Code") for a in ath])
                        for a in ath:
                            d = a.get("Description") or {}
                            players[a.get("Code")] = [f'{d.get("FamilyName", "")} {d.get("GivenName", "")}'.strip(), d.get("Organization") or c.get("Organization")]
                    if not ok or not all(all(x) for x in ids):
                        continue
                    head, _, rest = it["Result"].partition(" ")
                    try:
                        sc = [int(x) for x in head.split("-")]
                    except ValueError:
                        continue
                    wl = [pl.get("Wlt") for pl in places]
                    w = 0 if wl[0] == "W" else 1 if wl[1] == "W" else (0 if sc[0] > sc[1] else 1)
                    games = [g for g in re.findall(r"(\d+):(\d+)", rest) if g != ("0", "0")]
                    m = {"e": str(eid), "k": k, "r": (rd.get("Code") or "").strip("-"), "p": ids, "w": w}
                    if it.get("Date"):
                        m["d"] = f'{it["Date"]}T{it.get("Time") or "00:00"}:00L'
                    if games and all(sorted(g) == ["0", "11"] for g in games):
                        m["wo"] = 1
                    else:
                        m["s"] = sc
                        if games:
                            m["g"] = ",".join(f"{a}-{b}" for a, b in games)
                    if br.get("Code") == "PREL":
                        m["q"] = 1
                    out.append(m)
    return out


def event_name(eid):
    try:
        x = get(f"{LIVE}/GetEventName/{eid}")
        return (x[0].get("eventName") or "").strip() if x else None
    except Exception:
        return None


def rubbers(rs, players):
    """The individual matches inside team ties (WTT keeps them under teamParentData), so players' team-event
    records and the World Team Championships row of their profiles have who actually played."""
    out = []
    for r in rs or []:
        tp = (r.get("match_card") or {}).get("teamParentData") or {}
        for x in ((tp.get("extended_info") or {}).get("matches") or []):
            mr = x.get("match_result") or {}
            if not mr.get("documentCode") or (mr.get("resultStatus") or "").upper() not in ("OFFICIAL", ""):
                continue
            sides = mr.get("competitiors") or []
            n = [len([p for p in (c.get("players") or []) if p.get("playerId")]) for c in sides]
            if len(n) != 2 or n[0] != n[1] or n[0] not in (1, 2):
                continue
            m = compact({"documentCode": mr["documentCode"], "eventId": r.get("eventId"), "fullResults": "OFFICIAL",
                         "startDateLocal": r.get("startDateLocal"), "match_card": mr}, players)
            if m:
                m["k"] = m["k"][0] + ("S" if n[0] == 1 else "D")
                m["tm"] = 1
                out.append(m)
    return out


def sync_event(eid, events, years, players, senior_only=False):
    if senior_only:   # backfill: look at the name first and skip youth, para and veterans events without fetching their results
        ev0 = events.setdefault(eid, {})
        if not ev0.get("name"):
            ev0["name"] = event_name(eid) or ""
        if not ev0["name"] or SKIP_NAMES.search(ev0["name"]):
            ev0.update({"skip": True, "n": ev0.get("n", 0)})
            return 0
    rs = get(f"{LIVE}/GetOfficialResult?EventId={eid}&include_match_card=true&take=5000")
    ms = [m for m in (compact(r, players) for r in rs or []) if m]
    ms += rubbers(rs, players)
    if rs and len(ms) < len(rs) / 4:   # no match cards (older events): use the draws
        dates0 = sorted((r.get("startDateLocal") or "")[:4] for r in rs if r.get("startDateLocal"))
        if dates0 and int(dates0[-1]) >= FIRST_YEAR:
            ms = from_brackets(eid, players) or ms
    ev = events.setdefault(eid, {})
    if not ev.get("name"):
        ev["name"] = event_name(eid) or ""
    if not rs:
        ev.update({"n": 0, "done": False})
        return 0
    dates = sorted(m["d"][:10] for m in ms if m.get("d")) or sorted((r.get("startDateLocal") or "")[:10] for r in rs if r.get("startDateLocal"))
    ev.update({"start": dates[0] if dates else None, "end": dates[-1] if dates else None, "n": len(ms),
               "synced": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    ev["done"] = bool(dates) and dates[-1] < (dt.date.today() - dt.timedelta(days=3)).isoformat()
    if not dates or int(dates[-1][:4]) < FIRST_YEAR:
        ev["skip"] = True
        return 0
    # replace this event's matches in its year files
    for y in years.values():
        y[:] = [m for m in y if m["e"] != eid]
    for m in ms:
        yr = (m.get("d") or ev["end"])[:4]
        years.setdefault(yr, []).append(m)
    return len(ms)


def players_from_wtt(ids, out):
    """WTT's own record for each player: date of birth, hand, grip, and this year's stats."""
    for pid in ids:
        try:
            d = get(f"{CMS}/GetPlayersDataByID/{pid}")
        except Exception as err:
            print(f"player {pid}: {err}")
            continue
        pdata = ((d.get("additional_data") or {}).get("PlayerData") or [{}])[0]
        stats = (d.get("additional_data") or {}).get("StatsData") or []
        keep = ("SubeventCode", "StartDate", "best_rank", "best_rank_year", "best_rank_month", "total_matches", "total_wins", "total_losses",
                "tournament_wins", "finals_wins", "finals_losses")
        out[pid] = {"name": pdata.get("PlayerName"), "org": pdata.get("OrganizationCode"), "dob": (pdata.get("DOB") or "")[:10] or None,
                    "hand": pdata.get("Handedness"), "grip": pdata.get("Grip"), "style": pdata.get("Style"),
                    "stats": [{k: s.get(k) for k in keep} for s in stats],
                    "checked": dt.date.today().isoformat()}
        time.sleep(0.3)


def ranking_history():
    R = load(os.path.join(ROOT, "data", "rankings.json"), None)
    if not R:
        return False
    path = os.path.join(ROOT, "data", "ranking-history.json")
    H = load(path, {"weeks": {}})
    key = R["date"]
    if key in H["weeks"]:
        return False
    H["weeks"][key] = {g: [[p.get("ittf_id"), p["rank"], p["points"]] for p in R.get(g, [])] for g in ("men", "women")}
    H["weeks"] = dict(sorted(H["weeks"].items()))
    save(path, H)
    return True


def main():
    events = load(os.path.join(MDIR, "events.json"), {})
    players = load(os.path.join(MDIR, "players.json"), {})
    years = {}
    for f in os.listdir(MDIR) if os.path.isdir(MDIR) else []:
        if re.fullmatch(r"\d{4}\.json", f):
            years[f[:4]] = load(os.path.join(MDIR, f), [])
    today = dt.date.today().isoformat()
    if "--refill-empty" in sys.argv:   # events with results but no matches saved yet
        todo = [k for k, v in events.items() if not v.get("n") and v.get("end") and v["end"][:4] >= str(FIRST_YEAR)]
    elif "--backfill" in sys.argv:
        i = sys.argv.index("--backfill")
        todo = [str(x) for x in range(int(sys.argv[i + 1]), int(sys.argv[i + 2]) + 1)]
    else:
        known = [int(k) for k, v in events.items() if v.get("n")]
        top = max(known) if known else 3250
        todo = [k for k, v in events.items() if not v.get("done") and not v.get("skip")]
        todo += [str(x) for x in range(top - 30, top + 80) if str(x) not in events]
        # Feeders carry ranking points: pick up any an older backfill skipped by name
        for k, v in events.items():
            if v.get("skip") and not v.get("n") and "feeder" in (v.get("name") or "").lower():
                v.pop("skip")
                todo.append(k)
    todo = sorted(set(todo), key=int)
    added = 0
    for eid in todo:
        try:
            n = sync_event(eid, events, years, players, senior_only="--senior" in sys.argv)
        except Exception as err:
            print(f"{eid}: {err}")
            continue
        if n:
            print(f"{eid} {events[eid].get('name')}: {n} matches")
        added += n
    for y, ms in years.items():
        ms.sort(key=lambda m: (m.get("d") or "", m["e"]))
        save(os.path.join(MDIR, f"{y}.json"), ms)
    save(os.path.join(MDIR, "events.json"), dict(sorted(events.items(), key=lambda kv: int(kv[0]))), indent=1)
    save(os.path.join(MDIR, "players.json"), dict(sorted(players.items())))
    # WTT's player records: profiled players every run that lacks one, everyone in the top 100 on Mondays
    wpath = os.path.join(ROOT, "data", "players", "wtt.json")
    wtt = load(wpath, {})
    prof = [json.load(open(os.path.join(ROOT, "data", "players", f), encoding="utf-8")).get("ittf_id")
            for f in os.listdir(os.path.join(ROOT, "data", "players")) if f.endswith(".json") and f not in ("wtt.json", "wanted.json")] if os.path.isdir(os.path.join(ROOT, "data", "players")) else []
    R = load(os.path.join(ROOT, "data", "rankings.json"), {})
    top100 = [p.get("ittf_id") for g in ("men", "women") for p in R.get(g, []) if p.get("ittf_id")]
    # players the site build needs a date of birth for before it can give them a page (tools/people.py)
    wanted = [p for p in load(os.path.join(ROOT, "data", "players", "wanted.json"), []) if p not in wtt]
    want = [p for p in prof if p] + wanted + (top100 if dt.date.today().weekday() == 0 or "--players" in sys.argv else [])
    # profiled players are refreshed every Monday whatever their ranking, so a profile keeps updating after a player leaves the top 100
    want = [p for p in dict.fromkeys(want) if "--players" in sys.argv or p not in wtt or dt.date.today().weekday() == 0]
    if want:
        players_from_wtt(want, wtt)
        save(wpath, dict(sorted(wtt.items())), indent=1)
    ranking_history()
    print(f"done: {added} matches from {len(todo)} event ids")


if __name__ == "__main__":
    main()
