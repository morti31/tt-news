"""Who gets a player page, and who stays plain text.

Called from build_site.py straight after the stories are tagged, before any page is written, so tag chips,
squads, the match popup and the rankings widget all agree on the same list.

The rules (agreed 9 November 2026):
  1. Age comes first. Under 16: never a page. 16 or 17: only if they already play senior events (the senior
     test below). No date of birth on record: only if they pass the senior test. Age is worked out on every
     build, so a held-back player gets a page on their own once old enough.
  2. Youth events (U11 to U21, junior, cadet, hopes, youth) never count towards anything and never make a tag.
  3. Adults (18 and over) need one of: the senior test, a place in a club league squad we cover, or a written bio.
     The senior test is: in the senior world top 100 now or at any point on record, or a senior main-draw match
     at WTT Contender level or higher (qualifying does not count).
  4. A player who does not qualify appears as plain text everywhere: no link, no tag chip, no tag page.
  5. Pages stay once made (nothing here removes an adult because their ranking dropped), except when the age
     rule makes them ineligible.
  6. Overrides 1 to 3 (agreed 11 November 2026): every player in the world rankings shown on the site (the top 400)
     gets a page, whatever their age.

Output: Roster.pages {tag slug: player dict}, Roster.blocked {tag slugs that must not link}, Roster.urls.
"""
import glob, json, os, re, unicodedata, datetime as dt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
YOUTH = re.compile(r"\b(Youth|Junior|Cadet|Hopes|Mini|U-?(1[0-9]|2[01])|Under[- ]?(1[0-9]|2[01]))\b", re.I)
SENIOR = re.compile(r"WTT Finals|Cup Finals|World (Team )?(Table Tennis )?Championships|World Cup|Olympic|Smash|WTT Champions|Star Contender|WTT Contender")


def key(n):
    n = unicodedata.normalize("NFKD", n or "").encode("ascii", "ignore").decode().lower()
    n = re.sub(r"([aeiou])\1", r"\1", n)   # Ryuusei and Ryusei, Ohshima and Oshima: one player
    n = n.replace("oh", "o")
    return " ".join(sorted(re.findall(r"[a-z]+", n)))


def slugify(s):
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def age_on(born, today=None):
    if not born:
        return None
    b = dt.date.fromisoformat(born)
    t = today or dt.date.today()
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


def decide(age, senior, squad, bio, youth=False):
    """(allowed, reason). The whole policy in one place. youth: the player has a youth-event record, so with no
    date of birth they could be under 16; they wait until WTT's record (fetched by tools/match_sync.py) gives one."""
    if age is not None and age < 16:
        return False, "under 16"
    if age is not None and age < 18:
        return (True, "16 or 17, plays senior events") if senior else (False, "16 or 17, no senior events")
    if age is None and youth:
        return False, "age not on record and a youth-event record: waiting for a date of birth"
    if age is None:
        return (True, "senior player, age not on record") if senior else (False, "no date of birth and no senior record")
    if senior or squad or bio:
        return True, "adult"
    return False, "adult, not enough of a record"


def wtt_born(d):
    return f"{d[6:10]}-{d[0:2]}-{d[3:5]}" if d and len(d) >= 10 else None


class Roster:
    def __init__(self, tg, items, rankings, db):
        self.db = db
        bios = {}
        for f in sorted(glob.glob(os.path.join(ROOT, "data", "players", "*.json"))):
            if os.path.basename(f) in ("wtt.json", "wanted.json"):
                continue
            p = json.load(open(f, encoding="utf-8"))
            p["slug"] = os.path.splitext(os.path.basename(f))[0]
            bios[p["ittf_id"]] = p
        wtt = json.load(open(os.path.join(ROOT, "data", "players", "wtt.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "data", "players", "wtt.json")) else {}
        hist = json.load(open(os.path.join(ROOT, "data", "ranking-history.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "data", "ranking-history.json")) else {"weeks": {}}
        ever100 = {row[0] for gs in hist.get("weeks", {}).values() for g in gs.values() for row in g if row[1] <= 100}
        ranked, listed = {}, set()
        for g in ("men", "women"):
            listed.update(p["ittf_id"] for p in (rankings or {}).get(g, []) if p.get("ittf_id"))   # anyone in the world rankings on the site gets a page, whatever their age
            for p in (rankings or {}).get(g, []):
                if p.get("ittf_id") and p["rank"] <= 100:   # the senior test is the world top 100, however long the list on the site
                    ranked[p["ittf_id"]] = (p, "M" if g == "men" else "W")
        import doubles   # everyone in the doubles world rankings on the site gets a page too
        listed.update(doubles.players(singles=rankings).keys())
        squad = set()
        for f in glob.glob(os.path.join(ROOT, "data", "clubs", "squads", "*.json")):
            for t in json.load(open(f, encoding="utf-8")).get("teams", []):
                squad.update(key(p["name"]) for p in t.get("players", []))
        by_key = {}
        for pid, (raw, org) in db.players.items():
            by_key.setdefault(key(raw), []).append((pid, org))

        def ittf_for(name, nat):
            hit = by_key.get(key(name), [])
            if nat and len(hit) > 1:
                hit = [h for h in hit if h[1] == nat]
            return hit[0][0] if len(hit) == 1 else None

        def senior_draw(pid):
            for m in db.by_player.get(pid, []):
                nm = (db.events.get(m["e"]) or {}).get("name") or ""
                if YOUTH.search(nm) or m.get("q") or m["r"].startswith(("RND", "QER", "Q")):
                    continue
                if SENIOR.search(nm):
                    return True
            return False

        def youth_matches(pid):
            return any(YOUTH.search((db.events.get(m["e"]) or {}).get("name") or "") for m in db.by_player.get(pid, []))

        youth_tags = {s for s, t in tg.tags.items() if t["type"] == "tournament" and YOUTH.search(t["name"])}
        stories, youth_story = {}, set()
        for it in items:
            for s in it["all"]:
                stories[s] = stories.get(s, 0) + 1
            if youth_tags & set(it["all"]):
                youth_story.update(it["all"])

        # Candidates: every written bio, and every player tag with at least one story
        cands = {}
        for pid, p in bios.items():
            cands[slugify(p["name"])] = {"pid": pid, "bio": p, "name": p["name"], "nat": p.get("nat"), "gender": p.get("gender")}
        for slug, t in tg.tags.items():
            if t["type"] != "player" or slug in cands or not stories.get(slug):
                continue
            pid = None
            for g in ("men", "women"):
                r = (t.get("rank") or {}).get(g)
                if r and r.get("ittf_id"):
                    pid = r["ittf_id"]
            pid = pid or ittf_for(t["name"], t.get("nat"))
            if pid in bios:   # the tag is a spelling of a player who already has a bio
                cands[slug] = {**cands[slugify(bios[pid]["name"])], "alias": True}
                continue
            cands[slug] = {"pid": pid, "bio": None, "name": t["name"], "nat": t.get("nat") or (db.org(pid) if pid else None), "gender": None}

        self.pages, self.blocked, self.why, self.need_dob = {}, set(), {}, set()
        for slug, c in cands.items():
            pid = c["pid"]
            bio = c["bio"]
            born = (bio or {}).get("born") or (wtt_born((wtt.get(pid) or {}).get("dob")) if pid else None)
            a = age_on(born)
            best = next((x.get("best_rank") for x in (wtt.get(pid) or {}).get("stats", []) if x.get("SubeventCode") in ("MS", "WS")), None) if pid else None
            senior = bool(pid) and (pid in ranked or pid in ever100 or (best is not None and str(best).isdigit() and int(best) <= 100) or senior_draw(pid))
            youth = slug in youth_story or (bool(pid) and youth_matches(pid))
            ok, why = (True, "in the world rankings on the site") if pid in listed else decide(a, senior, key(c["name"]) in squad, bool(bio), youth)
            if a is None and pid:
                self.need_dob.add(pid)
            self.why[slug] = why
            if not ok:
                self.blocked.add(slug)
                continue
            if c.get("alias"):
                continue
            g = c["gender"] or (ranked.get(pid, (None, None))[1] if pid else None)
            if not g and pid:
                ks = [m["k"] for m in db.by_player.get(pid, [])]
                g = "W" if sum(k[0] == "W" for k in ks) > sum(k[0] == "M" for k in ks) else "M" if ks else None
            if bio:
                p = bio
            else:
                p = {"name": c["name"], "nat": c["nat"], "gender": g, "ittf_id": pid, "slug": slug, "generated": True}
                if born:
                    p["born"] = born
            self.pages[slug] = p
        # Player tags with no stories are never shown anyway; still block the ones the rules exclude, for safety
        for slug, t in tg.tags.items():
            if t["type"] == "player" and slug not in cands:
                self.why[slug] = "no stories"
        self.urls = {slug: f"/players/{p['slug']}.html" for slug, p in self.pages.items()}
        for slug, c in cands.items():   # alias tags point at the bio's page
            if c.get("alias") and slug not in self.blocked:
                self.urls[slug] = f"/players/{c['bio']['slug']}.html"

    def write_wanted(self):
        """ITTF ids whose date of birth we need: tools/match_sync.py fetches WTT's record for them on its next run."""
        path = os.path.join(ROOT, "data", "players", "wanted.json")
        json.dump(sorted(self.need_dob), open(path, "w", encoding="utf-8"))

    def by_name(self):
        """{display name: url} for profiles.json (squads, the match popup, the rankings widget)."""
        return {p["name"]: f"/players/{p['slug']}.html" for p in self.pages.values()}
