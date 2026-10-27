"""Fetch an official WTT draw (with results so far) into data/draws/<event_id>.json.

Usage: python3 tools/fetch_draw.py <wtt_event_id> "<event name>" [utc_offset_hours]
Example: python3 tools/fetch_draw.py 3250 "WTT Champions Montpellier" 1

WTT publishes local match times; pass the host city's UTC offset so times are stored in UTC.
If the WTT API can't be reached, the existing file is left untouched (exit code 1).
"""
import json, os, sys, urllib.request, datetime as dt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API = "https://wtt-website-api-vm-frontdoor-hhaec5epbhdyfugz.a01.azurefd.net/liveeventsapi/api/cms/GetBrackets/{eid}/{code}"
SUBEVENTS = {"men": ("Men's singles", "TTEMSINGLES-------------------------------"),
             "women": ("Women's singles", "TTEWSINGLES-------------------------------")}
ROUNDS = {"R64-": "Round of 64", "R32-": "Round of 32", "8FNL": "Round of 16", "QFNL": "Quarter-finals", "SFNL": "Semi-finals", "FNL-": "Final"}
FAMILY_FIRST = {"CHN", "TPE", "KOR", "HKG", "MAC", "PRK"}
# WTT data drops accents and uses its own forms for some names
FIXES = {"Felix Lebrun": "Félix Lebrun", "Anton Kallberg": "Anton Källberg", "Joao Geraldo": "João Geraldo",
         "Bernadette Szocs": "Bernadette Szőcs", "Ying Han": "Han Ying", "Peng Yu-Han": "Peng Yu-han"}


def cap(s):
    out, up = [], True
    for ch in s.lower():
        out.append(ch.upper() if up else ch)
        up = ch in " -"
    return "".join(out)


def player(c):
    if not c:
        return None
    a = c["Composition"]["Athlete"][0]["Description"]
    fam, giv = cap(a["FamilyName"]), a["GivenName"]
    name = f"{fam} {giv}" if c["Organization"] in FAMILY_FIRST else f"{giv} {fam}"
    name = FIXES.get(name, name)
    p = {"name": name, "nat": c["Organization"]}
    if c.get("Seed") and c["Seed"] <= 8:
        p["seed"] = c["Seed"]
    return p


def fetch(eid, code):
    req = urllib.request.Request(API.format(eid=eid, code=code), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def convert(j, offset):
    rounds = []
    for rd in reversed(j["Competition"]["Bracket"][0]["BracketItems"]):
        matches = []
        for m in sorted(rd["BracketItem"], key=lambda x: x["Order"]):
            places = sorted(m["CompetitorPlace"], key=lambda p: p["Pos"])
            when = None
            if m.get("Date") and m.get("Time"):
                local = dt.datetime.fromisoformat(f'{m["Date"]}T{m["Time"]}')
                when = (local - dt.timedelta(hours=offset)).strftime("%Y-%m-%dT%H:%M:00Z")
            players, winner = [], None
            for i, p in enumerate(places):
                players.append(player(p.get("Competitor")))
                if p.get("Wlt") == "W":
                    winner = i
            match = {"players": players}
            if when:
                match["when"] = when
            if m.get("Result"):
                match["score"] = m["Result"]
            if winner is not None:
                match["winner"] = winner
            matches.append(match)
        rounds.append({"round": ROUNDS.get(rd["Code"], rd["Code"]), "matches": matches})
    return rounds


def main():
    eid, name = sys.argv[1], sys.argv[2]
    offset = float(sys.argv[3]) if len(sys.argv) > 3 else 0
    path = os.path.join(ROOT, "data", "draws", f"{eid}.json")
    try:
        events = {k: {"name": label, "rounds": convert(fetch(eid, code), offset)} for k, (label, code) in SUBEVENTS.items()}
    except Exception as err:
        print(f"Couldn't reach the WTT draw for event {eid}: {err}. Left {path} unchanged.")
        sys.exit(1)
    data = {"event": name, "wtt_event_id": eid, "source": f"https://www.worldtabletennis.com/eventInfo?eventId={eid}&selectedTab=Draws",
            "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z"), "events": events}
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
