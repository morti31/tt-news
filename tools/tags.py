"""Tags: tournaments, players, countries, clubs and leagues, found automatically in every story.

Called from build_site.py. A tag comes from the text of a story (title, standfirst, body, match cards and the
story's event), so every old and new story is tagged on each build with no extra work. To add or force a tag by
hand, put "tags": ["Name", ...] on the article or story. To add a name the build cannot know (a competition, a
player outside the top 100), add it to data/tag-registry.json (see UPDATE.md).

Output (used by build_site.py): Tagger.tags_for(item) -> up to 3 display tags, Tagger.pages() -> every tag with its stories.
"""
import datetime as dt
import json, os, re, unicodedata

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

TYPES = {"tournament": "Tournament", "player": "Player", "country": "Country", "club": "Club or league"}
TYPE_ORDER = ["tournament", "player", "club", "country"]
MAX_TAGS = 3

# Competitions that have no event hub page. (name, aliases)
COMPETITIONS = [
    ("Youth Olympic Games", ["Youth Olympic Games", "Youth Olympics", "YOG"]),
    ("Olympic Games", ["(?<!Youth )Olympic Games", "(?<!Youth )Olympics"]),
    ("World Team Championships", ["World Team Championships", "World Team Table Tennis Championships"]),
    ("World Championships", ["World Table Tennis Championships", "World Championships"]),
    ("European Championships", ["European Championships"]),
    ("African Championships", ["African Championships"]),
    ("Asian Championships", ["Asian Championships"]),
    ("Americas Championships", ["Americas Championships"]),
    ("Asian Games", ["Asian Games"]),
    ("Commonwealth Games", ["Commonwealth Games"]),
    ("World Para Championships", ["World Para Championships", "Para World Championships"]),
    ("Mixed Team World Cup", ["Mixed Team World Cup"]),
    ("World Cup", ["Table Tennis World Cup"]),
    ("Europe Top 16", ["Europe Top 16", "European Top 16"]),
    ("All Japan Championships", ["All Japan Championships", "All-Japan Championships"]),
    ("ETTU Champions League", ["ETTU Champions League", "Champions League"]),
    ("WTT Finals", ["WTT Finals"]),
    ("WTT Grand Smash", ["Grand Smash", "WTT Grand Smash"]),
]
WTT_RX = re.compile(r"WTT (Champions|Star Contender|Contender|Feeder|Smash)((?: [A-Z][\wÀ-ž]+)?)")
WTT_STOP = {"Series", "Tour", "Event", "Events", "Finals", "Final", "Cup", "Level", "Calendar", "Week", "Day", "Is", "Are", "And", "The", "In", "At", "Has", "Have", "Will", "Was", "Players", "Player"}

COUNTRIES = {
    "CHN": ("China", ["China", "Chinese"]), "JPN": ("Japan", ["Japan", "Japanese"]), "GER": ("Germany", ["Germany", "German"]),
    "FRA": ("France", ["France", "French"]), "SWE": ("Sweden", ["Sweden", "Swedish"]), "KOR": ("South Korea", ["South Korea", "South Korean", "Korea Republic"]),
    "TPE": ("Chinese Taipei", ["Chinese Taipei"]), "HKG": ("Hong Kong", ["Hong Kong"]), "ENG": ("England", ["England", "English"]),
    "SCO": ("Scotland", ["Scotland", "Scottish"]), "WAL": ("Wales", ["Wales", "Welsh"]), "NIR": ("Northern Ireland", ["Northern Ireland"]),
    "EGY": ("Egypt", ["Egypt", "Egyptian"]), "BRA": ("Brazil", ["Brazil", "Brazilian"]), "USA": ("United States", ["United States", "USA", "American"]),
    "IND": ("India", ["India", "Indian"]), "ROU": ("Romania", ["Romania", "Romanian"]), "POL": ("Poland", ["Poland", "Polish"]),
    "AUT": ("Austria", ["Austria", "Austrian"]), "DEN": ("Denmark", ["Denmark", "Danish"]), "POR": ("Portugal", ["Portugal", "Portuguese"]),
    "SLO": ("Slovenia", ["Slovenia", "Slovenian"]), "CRO": ("Croatia", ["Croatia", "Croatian"]), "CZE": ("Czech Republic", ["Czech Republic", "Czechia", "Czech"]),
    "HUN": ("Hungary", ["Hungary", "Hungarian"]), "SGP": ("Singapore", ["Singapore"]), "THA": ("Thailand", ["Thailand", "Thai"]),
    "CAN": ("Canada", ["Canada", "Canadian"]), "PUR": ("Puerto Rico", ["Puerto Rico"]), "NGR": ("Nigeria", ["Nigeria", "Nigerian"]),
    "TUN": ("Tunisia", ["Tunisia", "Tunisian"]), "ALG": ("Algeria", ["Algeria", "Algerian"]), "COL": ("Colombia", ["Colombia", "Colombian"]),
    "ARG": ("Argentina", ["Argentina", "Argentinian"]), "CHI": ("Chile", ["Chile", "Chilean"]), "VEN": ("Venezuela", ["Venezuela", "Venezuelan"]),
    "ITA": ("Italy", ["Italy", "Italian"]), "ESP": ("Spain", ["Spain", "Spanish"]), "BEL": ("Belgium", ["Belgium", "Belgian"]),
    "NED": ("Netherlands", ["Netherlands", "Dutch"]), "LUX": ("Luxembourg", ["Luxembourg"]), "SVK": ("Slovakia", ["Slovakia", "Slovak"]),
    "SRB": ("Serbia", ["Serbia", "Serbian"]), "TUR": ("Turkey", ["Turkey", "Turkish", "Türkiye"]), "UKR": ("Ukraine", ["Ukraine", "Ukrainian"]),
    "KAZ": ("Kazakhstan", ["Kazakhstan"]), "UZB": ("Uzbekistan", ["Uzbekistan"]), "AUS": ("Australia", ["Australia", "Australian"]),
    "PRK": ("North Korea", ["North Korea", "North Korean"]), "IRI": ("Iran", ["Iran", "Iranian"]), "SEN": ("Senegal", ["Senegal", "Senegalese"]),
}
# Words that look like a country but are not (Chinese Taipei is masked before China is searched)
MASK = [re.compile(r"Chinese Taipei"), re.compile(r"South Korea|North Korea")]


def fold(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).replace("ø", "o").replace("Ø", "O").replace("ł", "l").replace("ß", "ss")


def norm(s):
    return re.sub(r"[\s\-]+", " ", fold(s).lower()).strip()


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", fold(s).lower()).strip("-")


def word_rx(s, flags=re.I):
    if s.startswith("(?<!"):
        return re.compile(r"(?<![\w])" + s + r"(?![\w])", flags)
    """A phrase as a regex that ignores accents' presence, hyphen/space differences, and requires word edges."""
    parts = [re.escape(p) for p in re.split(r"[\s\-]+", fold(s).strip()) if p]
    return re.compile(r"(?<![\w])" + r"[\s\-]+".join(parts) + r"(?![\w])", flags)


class Tagger:
    def __init__(self, hubs, rankings, article_matches, club_leagues, club_teams, extra=None):
        self.tags = {}       # slug -> dict
        self.by_name = {}    # normalised name -> slug
        self.rx = []         # (slug, regex, kind)
        self.players = {}    # slug -> {"name","nat","tok"}
        self.family, self.editions, self.year_rx = {}, {}, {}   # event pages that share a name across years
        self._add_competitions(hubs)
        self._not_players = {norm(n) for _, (n, al) in COUNTRIES.items() for n in [n, *al]} | {norm(t) for t in club_teams}
        self._add_players(rankings, article_matches, extra or [])
        self._add_countries()
        self._add_clubs(club_leagues, club_teams)
        for r in extra or []:
            if r.get("type") != "player":
                self._add_extra(r)
        self.tok_owner = {}
        for slug, p in self.players.items():
            for t in p["tok"]:
                self.tok_owner.setdefault(t, set()).add(slug)

    # ----- registry -----
    def _slug(self, name, type_):
        base = slugify(name)
        s = base
        if s in self.tags and self.tags[s]["type"] != type_:
            s = f"{base}-{type_}"
        return s

    def _tag(self, name, type_, **kw):
        slug = kw.pop("slug", None) or self._slug(name, type_)
        if slug not in self.tags:
            self.tags[slug] = {"slug": slug, "name": name, "type": type_, **kw}
            self.by_name[norm(name)] = slug
        return slug

    def _add_competitions(self, hubs):
        for h in hubs:
            slug = self._tag(f'{h["name"]} {h["year"]}', "tournament", slug=h["id"], hub=h["id"], city=h.get("city"), country=h.get("country"),
                             start=h.get("start"), end=h.get("end"), venue=h.get("venue"))
            names = {h["name"], f'{h["name"]} {h["year"]}'}
            for n in names:
                self.rx.append((slug, word_rx(n), "tournament"))
            # Editions of one event ("WTT Feeder Düsseldorf" 2023, 2024, "Düsseldorf II" 2024 ...): see _one_edition
            fam = norm(re.sub(r"\s+[IVX]+$", "", h["name"]))
            self.family[slug] = fam
            self.editions.setdefault(fam, []).append(slug)
            self.year_rx[slug] = word_rx(f'{h["name"]} {h["year"]}')
        for name, aliases in COMPETITIONS:
            if norm(name) in self.by_name or any(norm(a) == norm(name) and norm(a) in self.by_name for a in aliases):
                pass
            hub = next((s for s, t in self.tags.items() if t.get("hub") and norm(t["name"]).startswith(norm(name))), None)
            slug = hub or self._tag(name, "tournament")
            for a in aliases:
                self.rx.append((slug, word_rx(a, 0 if a in ("YOG", "Champions League") else re.I), "tournament"))

    def _add_wtt(self, name):
        slug = self.by_name.get(norm(name)) or next((s for s, t in self.tags.items() if t.get("hub") and norm(t["name"]).startswith(norm(name))), None)
        return slug or self._tag(name, "tournament")

    def _add_players(self, rankings, article_matches, extra):
        seen = {}
        for g in ("men", "women"):
            for p in (rankings or {}).get(g, []):
                seen.setdefault(norm(p["name"]), {"name": p["name"], "nat": p["nat"], "rank": {g: p}})
                seen[norm(p["name"])].setdefault("rank", {})[g] = p
        for m in article_matches:
            for s in m.get("sides", []):
                for nm in re.split(r"\s*(?:/|&)\s*", s["name"]):
                    nm = nm.strip()
                    if len(nm.split()) >= 2 and norm(nm) not in seen and norm(nm) not in self._not_players:   # team matches name countries and clubs
                        seen[norm(nm)] = {"name": nm, "nat": s.get("nat"), "rank": {}}
        for r in extra:
            if r.get("type") == "player" and norm(r["name"]) not in seen:
                seen[norm(r["name"])] = {"name": r["name"], "nat": r.get("nat"), "rank": {}}
        for k, p in seen.items():
            slug = self._tag(p["name"], "player", nat=p["nat"], rank=p["rank"])
            self.rx.append((slug, word_rx(p["name"]), "player"))
            parts = p["name"].split()
            if len(parts) == 2:    # Han Ying and Ying Han are the same player
                self.rx.append((slug, word_rx(f"{parts[1]} {parts[0]}"), "player"))
            toks = {t for t in re.split(r"[\s\-]+", fold(p["name"])) if len(t) >= 5}
            self.players[slug] = {"name": p["name"], "nat": p["nat"], "tok": toks}

    def _add_countries(self):
        for code, (name, aliases) in COUNTRIES.items():
            slug = self._tag(name, "country", code=code)
            for a in aliases:
                self.rx.append((slug, word_rx(a, 0 if a == "USA" else re.I), "country"))

    def _add_clubs(self, leagues, teams):
        for lg in leagues:
            slug = self._tag(lg["name"], "club", league=lg["slug"], country=lg["country"], slug=lg["slug"])
            self.rx.append((slug, re.compile(lg["match"], re.I), "club"))
        for team in teams:
            if len(team) >= 6 and norm(team) not in self.by_name:
                slug = self._tag(team, "club")
                self.rx.append((slug, word_rx(team), "club"))

    def _add_extra(self, r):
        slug = self._tag(r["name"], r["type"], **{k: v for k, v in r.items() if k not in ("name", "type", "aliases")})
        for a in [r["name"], *r.get("aliases", [])]:
            self.rx.append((slug, word_rx(a), r["type"]))

    # ----- tagging -----
    def score(self, item):
        """item: title, standfirst, body (text), event (hub id or None), matches (list), manual (list of names).
        Returns {slug: score}."""
        title, stand, body = fold(item.get("title", "")), fold(item.get("standfirst", "")), fold(item.get("body", ""))
        def mask(s):
            for m in MASK:
                s = m.sub(lambda x: "_" * len(x.group(0)), s)
            return s
        mt, ms, mb = mask(title), mask(stand), mask(body)
        sc = {}
        def add(slug, v):
            sc[slug] = sc.get(slug, 0) + v
        for slug, rx, kind in self.rx:
            src = (title, stand, body) if kind != "country" else (mt, ms, mb)
            nt, ns, nb = len(rx.findall(src[0])), len(rx.findall(src[1])), len(rx.findall(src[2]))
            if not (nt or ns or nb):
                continue
            v = min(nt, 2) * 10 + min(ns, 2) * 4 + min(nb, 2 if kind == "country" else 6)
            if not (nt or ns):    # a name in the body alone does not make a tag, unless it comes up again and again
                if kind == "tournament" or (kind == "country" and nb < 6) or (kind == "club" and nb < 3) or (kind == "player" and nb < 2):
                    continue
            add(slug, v)
        # WTT events without a hub page ("WTT Feeder Chennai") and the story's own event
        for m in WTT_RX.finditer(fold(item.get("title", "") + " . " + item.get("standfirst", "") + " . " + item.get("body", ""))):
            city = m.group(2).strip()
            if city and city in WTT_STOP:
                city = ""
            nm = f"WTT {m.group(1)}" + (f" {city}" if city else "")
            if city and WTT_RX.search(fold(item.get("title", "") + " . " + item.get("standfirst", ""))):
                add(self._add_wtt(nm), 12)
        if item.get("event"):
            hub = next((s for s, t in self.tags.items() if t.get("hub") == item["event"]), None)
            if hub:
                add(hub, 40)
        for m in item.get("matches") or []:
            ev = m.get("event") or ""
            for slug, rx, kind in self.rx:
                if kind == "tournament" and rx.search(fold(ev)):
                    add(slug, 8)
            for s in m.get("sides", []):
                for nm in re.split(r"\s*(?:/|&)\s*", s["name"]):
                    slug = self.by_name.get(norm(nm.strip()))
                    if slug and sc.get(slug, 0) < 40:
                        add(slug, 1)
        # Surnames count once the player is clearly in the story (Harimoto after Tomokazu Harimoto)
        for slug in [s for s in sc if s in self.players]:
            for t in self.players[slug]["tok"]:
                owners = self.tok_owner.get(t, set())
                if len([o for o in owners if o in sc]) == 1:
                    r = re.compile(r"(?<![\w])" + re.escape(t) + r"(?![\w])")
                    add(slug, min(len(r.findall(title)), 2) * 10 + min(len(r.findall(stand)), 2) * 4 + min(len(r.findall(body)), 6))
        self._one_edition(sc, item, " . ".join((title, stand, body)))
        for nm in item.get("manual") or []:
            slug = self.by_name.get(norm(nm)) or self._tag(nm, "player")
            sc[slug] = sc.get(slug, 0) + 100
        return sc

    def _one_edition(self, sc, item, text):
        """An event's name without a year ("WTT Champions Frankfurt") matches every year's page. Keep the editions the
        story names with their year and the story's own event; failing those, the edition nearest the story's date."""
        day = (item.get("date") or "")[:10]
        try:
            when = dt.date.fromisoformat(day)
        except ValueError:
            when = dt.date.today()
        for fam in {self.family[s] for s in sc if s in self.family}:
            members = self.editions[fam]
            if len(members) < 2:
                continue
            scored = [s for s in members if s in sc]
            keep = {s for s in members if self.year_rx[s].search(text) or self.tags[s].get("hub") == item.get("event")}
            if not keep:
                def gap(s):
                    t = self.tags[s]
                    if not t.get("start"):
                        return (10 ** 6, "")
                    a, b = dt.date.fromisoformat(t["start"]), dt.date.fromisoformat(t.get("end") or t["start"])
                    return (0 if a <= when <= b else min(abs((a - when).days), abs((when - b).days)), -a.toordinal())
                keep = {min(members, key=gap)}
            best = max(sc[s] for s in scored)
            for s in scored:
                if s not in keep:
                    del sc[s]
            for s in keep:
                sc.setdefault(s, best)

    def pick(self, sc, n=MAX_TAGS):
        """Up to n tags, best first: the tournament, then the players, then the club or country."""
        ranked = sorted(sc, key=lambda s: -sc[s])
        by = {t: [s for s in ranked if self.tags[s]["type"] == t] for t in TYPES}
        out = []
        for slug in by["tournament"][:1] + by["player"][:1] + by["club"][:1]:
            out.append(slug)
        if len(by["tournament"]) > 1 and sc[by["tournament"][1]] >= 14 and by["tournament"][1] not in out:
            out.insert(1, by["tournament"][1])
        for slug in ranked:
            if len(out) >= n:
                break
            if slug not in out and (n > 3 or self.tags[slug]["type"] != "tournament") and not (n <= 3 and self.tags[slug]["type"] == "country" and any(self.tags[o]["type"] == "country" for o in out)):
                out.append(slug)
        out = out[:n]
        # Keep a country only when it is a main subject
        out.sort(key=lambda s: (TYPE_ORDER.index(self.tags[s]["type"]), -sc[s]))
        return out


def footer(tg, sc):
    """Every tag for the foot of an article: the best eight, plus every player named at least twice."""
    out = tg.pick(sc, 8)
    extra = [s for s in sorted(sc, key=lambda x: -sc[x]) if tg.tags[s]["type"] == "player" and sc[s] >= 2 and s not in out]
    out += extra
    out.sort(key=lambda s: (TYPE_ORDER.index(tg.tags[s]["type"]), -sc[s]))
    return out


def load_registry():
    p = os.path.join(ROOT, "data", "tag-registry.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []
