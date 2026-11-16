"""The "Explained" block: one to three Guide pieces matched to the page they sit on.

Every rule lives here, so new events, leagues and guides fit in without touching the page builders.
A guide can also name pages itself with "pages": ["rankings", "event:WTT", "league:bundesliga", "player", ...]
in data/guides/<slug>.json; those are added after the rules below.
One guide shows as a wide banner; two or three as a row of cards (a sideways scroll on phones).
"""
import html
import build_guides

e = html.escape
_G = None

# Page -> guides, best first. Missing guides are skipped, so a rule can name a guide before it is written.
RULES = {
    "rankings": ["how-table-tennis-world-rankings-work", "wtt-event-tiers-explained", "olympic-table-tennis-qualification"],
    "rankings-doubles": ["doubles-rules-explained"],
    "player": ["how-table-tennis-world-rankings-work", "professional-table-tennis-leagues"],
    "player-kit": ["table-tennis-blades-explained"],
    "events": ["wtt-event-tiers-explained", "table-tennis-season-calendar", "where-to-watch-table-tennis"],
    "clubs": ["professional-table-tennis-leagues", "team-table-tennis-format"],
    "league": ["professional-table-tennis-leagues", "team-table-tennis-format"],
    "league:champions-league": ["ettu-champions-league-explained"],
}
EVENT_SERIES = [   # (words in the event's series or group, guides)
    ("World Team Championships", ["world-table-tennis-championships-explained", "team-table-tennis-format"]),
    ("World Championships", ["world-table-tennis-championships-explained"]),
    ("Mixed Team World Cup", ["table-tennis-world-cup-explained", "team-table-tennis-format"]),
    ("World Cup", ["table-tennis-world-cup-explained"]),
    ("WTT Finals", ["table-tennis-world-cup-explained", "wtt-event-tiers-explained"]),
    ("Olympic", ["olympic-table-tennis-qualification"]),
    ("Team Championships", ["team-table-tennis-format"]),
    ("WTT", ["wtt-event-tiers-explained"]),
    ("Continental", ["ittf-and-wtt-explained"]),
]
EVENT_ALWAYS = ["where-to-watch-table-tennis", "table-tennis-scoring-explained"]

SHELF_ICON = {   # small drawings for the card tiles, by Guide shelf
    "start": '<circle cx="32" cy="32" r="14"/><path d="M22 26c6 3 14 3 20 0" />',
    "pro": '<path d="M22 14h20v10a10 10 0 0 1-20 0zM22 18h-6a6 6 0 0 0 6 8M42 18h6a6 6 0 0 1-6 8M32 34v8M24 48h16M27 42h10v6H27z"/>',
    "clubs": '<path d="M16 48V26l16-10 16 10v22M24 48V34h16v14M16 48h32"/>',
    "kit": '<circle cx="28" cy="26" r="13"/><path d="M36 35l10 12M43 50l6-5"/><circle cx="48" cy="18" r="4"/>',
    "styles": '<path d="M14 44c10-22 26-22 36-6M44 30l6 8-9 2"/><circle cx="16" cy="44" r="3"/>',
    "words": '<path d="M16 46l9-26 9 26M19 38h12M38 46V30h7a5 5 0 0 1 0 10h-7"/>',
}


def guides():
    global _G
    if _G is None:
        plan, gs = build_guides.load()
        shelf = {it["slug"]: sh["key"] for sh in plan.get("shelves", []) for it in sh["items"]}
        for s, g in gs.items():
            g["_shelf"] = shelf.get(s) or g.get("shelf") or "pro"
        _G = gs
    return _G


def pick(keys, extra=(), n=3):
    gs, out = guides(), []
    tagged = [s for s, g in gs.items() if set(g.get("pages") or []) & set(keys)]
    for k in keys:
        for s in RULES.get(k, []):
            if s in gs and s not in out:
                out.append(s)
    for s in list(extra) + tagged:
        if s in gs and s not in out:
            out.append(s)
    return out[:n]


def for_event(ev):
    text = f'{ev.get("series", "")} {ev.get("group", "")} {ev.get("name", "")}'
    seen = []
    for words, gl in EVENT_SERIES:
        if words.lower() in text.lower():
            seen += gl
            break
    keys = ["event", "event:" + ev.get("group", ""), "event:" + ev.get("series", "")]
    return pick(keys, seen + EVENT_ALWAYS)


ICONS = {   # a drawing per subject, matched on the guide's slug; the shelf's drawing otherwise
    "ranking": '<path d="M12 50h40M18 50V34h8v16M28 50V20h8v30M38 50V28h8v22"/>',
    "tiers": '<path d="M32 12L52 50H12z M19 37h26M25 25h14"/>',
    "olympic": '<circle cx="20" cy="28" r="8"/><circle cx="32" cy="28" r="8"/><circle cx="44" cy="28" r="8"/><circle cx="26" cy="38" r="8"/><circle cx="38" cy="38" r="8"/>',
    "world-cup": SHELF_ICON["pro"], "championships": SHELF_ICON["pro"],
    "leagues": SHELF_ICON["clubs"], "champions-league": '<path d="M32 12l16 6v12c0 10-7 18-16 22-9-4-16-12-16-22V18z M26 32l5 5 9-10"/>',
    "team": '<circle cx="22" cy="24" r="6"/><circle cx="42" cy="24" r="6"/><path d="M12 48c0-8 4-13 10-13s10 5 10 13M32 48c0-8 4-13 10-13s10 5 10 13"/>',
    "watch": '<rect x="10" y="16" width="44" height="28" rx="3"/><path d="M24 52h16M32 44v8M28 25l10 5-10 5z"/>',
    "calendar": '<rect x="12" y="16" width="40" height="34" rx="3"/><path d="M12 26h40M22 11v9M42 11v9M20 34h6M30 34h6M40 34h4M20 42h6M30 42h6"/>',
    "scoring": '<rect x="10" y="18" width="44" height="28" rx="3"/><path d="M32 18v28M20 27v10M41 27h6v5h-6v5h6"/>',
    "doubles": '<circle cx="24" cy="30" r="9"/><circle cx="40" cy="34" r="9"/>',
    "serve": '<circle cx="32" cy="16" r="5"/><path d="M32 26v8M20 48c4-6 20-6 24 0M16 40h32"/>',
    "ittf": '<circle cx="32" cy="32" r="18"/><path d="M14 32h36M32 14c-7 8-7 28 0 36M32 14c7 8 7 28 0 36"/>',
    "blades": SHELF_ICON["kit"], "rubbers": '<rect x="16" y="14" width="32" height="36" rx="16"/><path d="M22 24h20M22 32h20M22 40h20"/>',
    "sponge": '<rect x="14" y="22" width="36" height="20" rx="3"/><circle cx="22" cy="30" r="2"/><circle cx="32" cy="34" r="2"/><circle cx="42" cy="29" r="2"/>',
    "england": '<path d="M32 12l16 6v12c0 10-7 18-16 22-9-4-16-12-16-22V18z M32 18v28M20 30h24"/>',
    "club": SHELF_ICON["clubs"], "rules": '<rect x="16" y="12" width="32" height="40" rx="3"/><path d="M23 22h18M23 30h18M23 38h12"/>',
}


def tile(g):
    slug = g["slug"]
    art = next((v for k, v in ICONS.items() if k in slug), SHELF_ICON.get(g["_shelf"], SHELF_ICON["pro"]))
    return (f'<span class="xp-tile xp-{e(g["_shelf"])}" aria-hidden="true"><svg viewBox="8 8 48 48" fill="none" stroke="currentColor" '
            f'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">{art}</svg></span>')


def block(slugs, where="bottom"):
    gs = guides()
    slugs = [s for s in slugs if s in gs]
    if not slugs:
        return ""
    mins = lambda g: f'{build_guides.minutes(g)} min read'
    if len(slugs) == 1:
        g = gs[slugs[0]]
        return (f'<section class="xp xp-one xp-{where}" aria-label="Explained"><a href="/guide/{e(g["slug"])}.html">{tile(g)}'
                f'<span class="xp-txt"><span class="xp-k">Explained</span><span class="xp-h">{e(g["title"])}</span>'
                f'<span class="xp-s">{e(g["summary"])}</span><span class="xp-go">Read the guide <span aria-hidden="true">→</span>'
                f'<span class="xp-m">{mins(g)}</span></span></span></a></section>')
    cards = "".join(f'<li><a href="/guide/{e(gs[s]["slug"])}.html">{tile(gs[s])}<span class="xp-h">{e(gs[s]["title"])}</span>'
                    f'<span class="xp-s">{e(gs[s]["summary"])}</span><span class="xp-m">{mins(gs[s])}</span></a></li>' for s in slugs)
    return (f'<section class="xp xp-{where}" aria-labelledby="xp-{where}-h"><h2 class="section-title" id="xp-{where}-h">Explained</h2>'
            f'<ul class="xp-cards">{cards}</ul></section>')


# ---- Related analysis: Eleven's long reads matched to the page, by shared tags first and then by words
_A = []   # [{url, title, summary, published, cover, all}] for every Analysis piece, newest first

HUB_WORDS = {   # pages that are about a subject rather than one player, event or league
    "rankings": ["ranking", "world no", "top 10", "top 100", "average age", "prize money"],
    "events": ["calendar", "wtt", "workload", "prize money", "tournament", "events"],
    "clubs": ["league", "club", "bundesliga", "super league", "membership"],
}


def set_items(items, feats):
    """items: build_site's tagged stories (with "all" tag slugs); feats: Analysis article url -> {"cover", "related"}.

    Where an Analysis piece appears, strongest first:
      1. its "related" field (in data/articles/<slug>.json), written with the piece:
         {"players": [profile names], "events": [words of an event's name or series, e.g. "WTT Champions",
          "World Championships"], "leagues": [league slugs], "pages": ["rankings", "events", "clubs", "players"]}
         "players" puts it on those profiles, "events" on every event page whose name or series contains the words,
         "leagues" on those league pages, "pages" on those index pages (and "players" there means every profile).
      2. tags it shares with the page's subject (the automatic tagging of every article)
      3. the page subject's name in its title or standfirst
    """
    global _A
    _A = sorted(({**it, "cover": feats[it["url"]]["cover"], "related": feats[it["url"]].get("related") or {}}
                 for it in items if it["url"] in feats), key=lambda it: it.get("published") or "", reverse=True)


def _rel_score(it, keys):
    r, s = it.get("related") or {}, 0
    for k in keys:
        kind, _, val = k.partition(":")
        v = val.lower()
        if kind == "page" and val in (r.get("pages") or []):
            s += 4
        elif kind == "player" and any(v == p.lower() for p in r.get("players") or []):
            s += 6
        elif kind == "player" and "players" in (r.get("pages") or []):
            s += 1
        elif kind == "event" and any(w.lower() in v for w in r.get("events") or []):
            s += 5
        elif kind == "league" and val in (r.get("leagues") or []):
            s += 6
    return s


def analysis(tags=(), words=(), exclude=None, n=2, keys=()):
    tags, words = set(tags), [w.lower() for w in words if w]
    scored = []
    for i, it in enumerate(_A):
        if exclude and it["url"].rstrip(".html") == exclude.rstrip(".html"):
            continue
        txt = f'{it["title"]} {it.get("summary", "")}'.lower()
        s = _rel_score(it, keys) + 3 * len(tags & set(it.get("all") or [])) + sum(1 for w in words if w in txt)
        if s >= 2 or (s and not keys):   # with page keys, a lone weak match (one shared word, "every profile") is not enough
            scored.append((-s, i, it))
    return [it for _, _, it in sorted(scored, key=lambda t: t[:2])[:n]]


def analysis_block(pieces, title="Analysis"):
    if not pieces:
        return ""
    cards = "".join(
        f'<li><a href="{e(it["url"])}"><span class="xa-pic"><img src="{e(it["cover"])}" alt="" loading="lazy" width="400" height="225"></span>'
        f'<span class="xa-k">Analysis</span><span class="xp-h">{e(it["title"])}</span><span class="xp-s">{e(it.get("summary", ""))}</span></a></li>'
        for it in pieces)
    return f'<section class="xp xa" aria-label="{e(title)}"><h2 class="section-title">{e(title)}</h2><ul class="xa-cards">{cards}</ul></section>'


def related(guide_slugs, tags=(), words=(), where="bottom", exclude=None):
    """The "Explained" guides, then up to two Analysis pieces on the same subject."""
    return block(guide_slugs, where) + analysis_block(analysis(tags, words, exclude))


def combined(guide_slugs, pieces, where="bottom", title="Go deeper"):
    """Guides and Analysis in one feature: Analysis pieces as picture cards, guides beside them as a compact list.
    Falls back to the plain guides block or the plain Analysis cards when one side is empty."""
    gs = guides()
    slugs = [s for s in guide_slugs if s in gs]
    if not pieces:
        return block(slugs, where)
    if not slugs:
        return analysis_block(pieces, title="Analysis")
    feats = "".join(
        f'<li><a href="{e(it["url"])}"><span class="xa-pic"><img src="{e(it["cover"])}" alt="" loading="lazy" width="400" height="225"></span>'
        f'<span class="xa-txt"><span class="xa-k">Analysis</span><span class="xp-h">{e(it["title"])}</span><span class="xp-s">{e(it.get("summary", ""))}</span></span></a></li>'
        for it in pieces)
    gl = "".join(
        f'<li><a href="/guide/{e(gs[s]["slug"])}.html">{tile(gs[s])}<span class="xp-txt"><span class="xp-k">Guide</span>'
        f'<span class="xp-h">{e(gs[s]["title"])}</span><span class="xp-m">{build_guides.minutes(gs[s])} min read</span></span></a></li>'
        for s in slugs)
    return (f'<section class="xp xc xp-{where}" aria-labelledby="xc-{where}-h"><h2 class="section-title" id="xc-{where}-h">{e(title)}</h2>'
            f'<div class="xc-grid{" xc-two" if len(pieces) > 1 else ""}"><ul class="xa-cards">{feats}</ul><ul class="xc-guides">{gl}</ul></div></section>')


def for_story(a, ev=None):
    """Guides for a news story: its event's, its league's, or its section's."""
    if ev:
        return for_event(ev)[:2]
    cat, lg = a.get("category"), a.get("league")
    if cat == "Clubs" or lg:
        return pick(["league:champions-league"] if lg == "champions-league" else ["league", "league:" + (lg or "")], n=2)
    if cat == "Equipment":
        return pick(["kit"], ["table-tennis-blades-explained", "table-tennis-rubbers-explained"], n=2)
    if cat == "England":
        return pick(["england"], ["table-tennis-england-explained", "find-a-table-tennis-club-england"], n=2)
    return pick(["news"], ["how-table-tennis-world-rankings-work", "table-tennis-scoring-explained"], n=2)
