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
# Every other draw an event can have. fetch_draw.py --all tries them all and keeps the ones WTT has.
ALL_SUBEVENTS = {"women": ("Women's singles", "TTEWSINGLES"), "men": ("Men's singles", "TTEMSINGLES"),
                 "wdoubles": ("Women's doubles", "TTEWDOUBLES"), "mdoubles": ("Men's doubles", "TTEMDOUBLES"),
                 "mixed": ("Mixed doubles", "TTEXDOUBLES"), "wteam": ("Women's team", "TTEWTEAM"), "mteam": ("Men's team", "TTEMTEAM"),
                 "xteam": ("Mixed team", "TTEXTEAM")}
ROUNDS = {"R64-": "Last 64", "R32-": "Last 32", "8FNL": "Last 16", "QFNL": "Quarter-finals", "SFNL": "Semi-finals", "FNL-": "Final"}
FAMILY_FIRST = {"CHN", "TPE", "KOR", "HKG", "MAC", "PRK"}
# WTT data drops accents and uses its own forms for some names
FIXES = {"Felix Lebrun": "Félix Lebrun", "Anton Kallberg": "Anton Källberg", "Joao Geraldo": "João Geraldo",
         "Bernadette Szocs": "Bernadette Szőcs", "Ying Han": "Han Ying", "Peng Yu-Han": "Peng Yu-han",
         "Jian Zeng": "Zeng Jian", "Feng Yi-Hsin": "Feng Yi-hsin", "Bo Fang": "Fang Bo", "Leo De Nodrest": "Léo de Nodrest",
         "Truls Moregardh": "Truls Moregard"}


def cap(s):
    out, up = [], True
    for ch in s.lower():
        out.append(ch.upper() if up else ch)
        up = ch in " -"
    return "".join(out)


TEAMS = {"CHN": "China", "JPN": "Japan", "KOR": "South Korea", "TPE": "Chinese Taipei", "HKG": "Hong Kong", "GER": "Germany", "FRA": "France",
         "SWE": "Sweden", "ROU": "Romania", "ENG": "England", "POR": "Portugal", "BRA": "Brazil", "USA": "United States", "IND": "India",
         "EGY": "Egypt", "SGP": "Singapore", "AUT": "Austria", "POL": "Poland", "SLO": "Slovenia", "CRO": "Croatia", "DEN": "Denmark",
         "PUR": "Puerto Rico", "THA": "Thailand", "ITA": "Italy", "ESP": "Spain", "NGR": "Nigeria", "KAZ": "Kazakhstan", "CZE": "Czech Republic",
         "HUN": "Hungary", "SVK": "Slovakia", "UKR": "Ukraine", "LUX": "Luxembourg", "NED": "Netherlands", "BEL": "Belgium", "CAN": "Canada",
         "MEX": "Mexico", "ARG": "Argentina", "CHI": "Chile", "AUS": "Australia", "IRI": "Iran", "TUR": "Turkey", "SRB": "Serbia", "WAL": "Wales",
         "SCO": "Scotland", "IRL": "Ireland", "MAS": "Malaysia", "VIE": "Vietnam", "PRK": "North Korea", "ALG": "Algeria", "TUN": "Tunisia",
         "FIN": "Finland", "NOR": "Norway", "SUI": "Switzerland", "GRE": "Greece", "LTU": "Lithuania", "MDA": "Moldova", "ISR": "Israel",
         "UZB": "Uzbekistan", "PER": "Peru", "COL": "Colombia", "CUB": "Cuba", "DOM": "Dominican Republic", "ECU": "Ecuador", "NZL": "New Zealand",
         "MAC": "Macao", "INA": "Indonesia", "PHI": "Philippines", "QAT": "Qatar", "KSA": "Saudi Arabia", "MGL": "Mongolia", "SRI": "Sri Lanka",
         "RSA": "South Africa", "CMR": "Cameroon", "GHA": "Ghana", "SEN": "Senegal", "MAR": "Morocco", "BUL": "Bulgaria", "LAT": "Latvia",
         "EST": "Estonia", "BIH": "Bosnia and Herzegovina", "MKD": "North Macedonia", "MNE": "Montenegro", "AZE": "Azerbaijan", "GEO": "Georgia",
         "ARM": "Armenia", "BLR": "Belarus", "AIN": "Neutral athletes", "FIJ": "Fiji", "VAN": "Vanuatu", "TAH": "Tahiti", "GUA": "Guatemala",
         "VEN": "Venezuela", "PAR": "Paraguay", "URU": "Uruguay", "CRC": "Costa Rica", "PAN": "Panama", "BAN": "Bangladesh", "NEP": "Nepal",
         "PAK": "Pakistan", "JOR": "Jordan", "IRQ": "Iraq", "SYR": "Syria", "LBN": "Lebanon", "UAE": "United Arab Emirates", "BRN": "Bahrain",
         "KUW": "Kuwait", "OMA": "Oman", "YEM": "Yemen", "KGZ": "Kyrgyzstan", "TJK": "Tajikistan", "TKM": "Turkmenistan"}


def one(a, org):
    fam, giv = cap(a["FamilyName"]), a["GivenName"]
    name = f"{fam} {giv}" if org in FAMILY_FIRST else f"{giv} {fam}"
    return FIXES.get(name.strip(), name.strip())


def player(c):
    """A player, a doubles pair ("A / B") or a team (its country name)."""
    if not c:
        return None
    org = c.get("Organization") or ""
    ath = ((c.get("Composition") or {}).get("Athlete")) or []
    if c.get("Type") == "T" and len(ath) > 2 or not ath:
        name = TEAMS.get(org, org)
    else:
        name = " / ".join(one(a["Description"], a["Description"].get("Organization") or org) for a in ath[:2])
    p = {"name": name, "nat": org}
    if c.get("Seed") and c["Seed"] <= 8:
        p["seed"] = c["Seed"]
    return p


def fetch(eid, code):
    # WTT's API answers only requests that look like its own website's (Origin and Referer), and only from some networks
    # (GitHub's runners, not most cloud hosts). An event with no such draw gets an empty 204 reply.
    req = urllib.request.Request(API.format(eid=eid, code=code), headers={
        "Origin": "https://www.worldtabletennis.com", "Referer": "https://www.worldtabletennis.com/",
        "User-Agent": "Mozilla/5.0 (Eleven)", "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
    if body[:2] == b"\x1f\x8b":
        import gzip
        body = gzip.decompress(body)
    return json.loads(body.decode("utf-8-sig"))


def convert(j, offset):
    rounds = []
    def is_team(m):
        return any((p.get("Competitor") or {}).get("Type") == "T" and len((((p.get("Competitor") or {}).get("Composition") or {}).get("Athlete")) or []) > 2
                   for p in m["CompetitorPlace"])
    for rd in reversed(j["Competition"]["Bracket"][0]["BracketItems"]):
        matches = []
        items = rd["BracketItem"]
        if any(is_team(m) for m in items):   # team events also list the ties' individual matches: keep the ties only
            items = [m for m in items if m["Code"].endswith("0000")]
        for m in sorted(items, key=lambda x: x["Order"]):
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
                team = any(((p.get("Competitor") or {}).get("Type") == "T" and len(((p.get("Competitor") or {}).get("Composition") or {}).get("Athlete") or []) > 2) for p in places)
                match["score"] = m["Result"].split(" ")[0] if team else m["Result"]
            if winner is not None:
                match["winner"] = winner
            matches.append(match)
        rounds.append({"round": ROUNDS.get(rd["Code"], rd["Code"]), "matches": matches})
    return rounds


API_NAMES = {"women": "Women's Singles", "men": "Men's Singles", "wdoubles": "Women's Doubles", "mdoubles": "Men's Doubles",
             "mixed": "Mixed Doubles", "wteam": "Women's Teams", "mteam": "Men's Teams", "xteam": "Mixed Teams"}


def fetch_all(eid, offset):
    """Every draw WTT has for an event. WTT answers an unknown draw code with another draw, so each reply's event name is checked."""
    events = {}
    for k, (label, code) in ALL_SUBEVENTS.items():
        try:
            j = fetch(eid, code.ljust(42, "-"))
        except Exception:
            continue
        comp = j.get("Competition") or {}
        name = ((comp.get("ExtendedInfos") or {}).get("SportDescription") or {}).get("EventName")
        if not comp.get("Bracket") or name != API_NAMES[k]:
            continue
        events[k] = {"name": label, "rounds": convert(j, offset)}
    if not {"women", "men"} & set(events) and not any("team" in k for k in events):
        raise RuntimeError("no draws found")
    return events


def main():
    eid, name = sys.argv[1], sys.argv[2]
    args = [a for a in sys.argv if a != "--all"]
    offset = float(args[3]) if len(args) > 3 else 0
    path = os.path.join(ROOT, "data", "draws", f"{eid}.json")
    try:
        if "--all" in sys.argv:
            events = fetch_all(eid, offset)
        else:
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
