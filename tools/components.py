"""Match centre components for article and story pages: scoreboard, draw bracket and video highlights.

Data shapes (all optional on an article in data/articles/*.json or a story in data/news.json):

"matches": [                                   # first match is shown large; the rest as compact results
  {"label": "Men's singles final", "event": "Asian Championships, Tashkent",
   "sides": [{"name": "Tomokazu Harimoto", "nat": "JPN"}, {"name": "Li Tianyang", "nat": "CHN"}],
   "score": [3, 2],                            # games (singles) or rubbers (team), in side order
   "games": [[1, 11], [9, 11], [11, 7]],        # optional point scores per game, in side order
   "rubbers": [                                 # team ties only: each rubber has the same shape
     {"sides": [{"name": "Zhou Qihao"}, {"name": "Kang Dong-soo"}], "score": [3, 1], "games": [[11, 8], ...]}]}]

"draw": "3250"                                  # file in data/draws/, refreshed during the event

"videos": [{"id": "4waydbwXrog", "title": "...", "channel": "TT11TV"}]   # YouTube IDs, official or rights-holder channels only
"""
import html, json, os, datetime as dt

e = html.escape
# ITTF country codes to flag-icons codes. TPE (competes under its Olympic flag) and
# neutral athletes (RUS, BLR, AIN) deliberately get no flag, just the code.
FLAGS = {"CHN": "cn", "JPN": "jp", "KOR": "kr", "PRK": "kp", "HKG": "hk", "MAC": "mo", "SGP": "sg", "IND": "in", "IRI": "ir", "KAZ": "kz", "UZB": "uz", "THA": "th", "MAS": "my", "INA": "id", "VIE": "vn", "PHI": "ph", "QAT": "qa", "KSA": "sa", "UAE": "ae", "BRN": "bh", "EGY": "eg", "NGR": "ng", "ALG": "dz", "TUN": "tn", "MAR": "ma", "RSA": "za", "FRA": "fr", "GER": "de", "SWE": "se", "DEN": "dk", "NOR": "no", "FIN": "fi", "ENG": "gb-eng", "SCO": "gb-sct", "WAL": "gb-wls", "GBR": "gb", "IRL": "ie", "POR": "pt", "ESP": "es", "ITA": "it", "AUT": "at", "SUI": "ch", "BEL": "be", "NED": "nl", "LUX": "lu", "POL": "pl", "CZE": "cz", "SVK": "sk", "SLO": "si", "CRO": "hr", "SRB": "rs", "BIH": "ba", "MNE": "me", "MKD": "mk", "GRE": "gr", "TUR": "tr", "ROU": "ro", "HUN": "hu", "BUL": "bg", "UKR": "ua", "MDA": "md", "LTU": "lt", "LAT": "lv", "EST": "ee", "ISR": "il", "BRA": "br", "ARG": "ar", "CHI": "cl", "PER": "pe", "COL": "co", "VEN": "ve", "ECU": "ec", "URU": "uy", "PAR": "py", "MEX": "mx", "CUB": "cu", "DOM": "do", "PUR": "pr", "GUA": "gt", "CAN": "ca", "USA": "us", "AUS": "au", "NZL": "nz", "FIJ": "fj"}


def flag(code):
    f = FLAGS.get((code or "").upper())
    return f'<span class="fi fi-{f}" aria-hidden="true"></span>' if f else ""


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

try:
    from zoneinfo import ZoneInfo
    UK = ZoneInfo("Europe/London")
except Exception:
    UK = dt.timezone.utc


def _winner(score):
    if not score or len(score) != 2 or score[0] == score[1]:
        return None
    return 0 if score[0] > score[1] else 1


def _side(p, won, align):
    nat = f'<span class="sb-nat">{flag(p.get("nat"))}{e(p.get("nat", ""))}</span>' if p.get("nat") else ""
    return f'<div class="sb-side {align}{" won" if won else ""}"><span class="sb-name">{e(p["name"])}</span>{nat}</div>'


def _games_table(m):
    games = m.get("games") or []
    if not games:
        return ""
    head = "".join(f"<th scope=\"col\">{i + 1}</th>" for i in range(len(games)))
    rows = ""
    for s, p in enumerate(m["sides"]):
        cells = "".join(f'<td class="{"g-won" if g[s] > g[1 - s] else ""}">{g[s]}</td>' for g in games)
        rows += f'<tr><th scope="row">{e(p["name"])}</th>{cells}</tr>'
    return f'<div class="sb-games-wrap"><table class="sb-games"><caption class="sr-only">Points per game</caption><thead><tr><th scope="col">Game</th>{head}</tr></thead><tbody>{rows}</tbody></table></div>'


def _chips(games):
    if not games:
        return ""
    return '<span class="chips">' + "".join(f'<span class="chip">{g[0]}–{g[1]}</span>' for g in games) + "</span>"


def _compact(m, label=None):
    w = _winner(m.get("score"))
    a, b = m["sides"]
    score = f'{m["score"][0]}–{m["score"][1]}' if m.get("score") else "v"
    lab = label if label is not None else m.get("label", "")
    return f"""<div class="sb-row">
  {f'<span class="sb-row-label">{e(lab)}</span>' if lab else ""}
  <span class="sb-row-a{" won" if w == 0 else ""}">{e(a["name"])}{f' <small>{flag(a["nat"])}{e(a["nat"])}</small>' if a.get("nat") else ""}</span>
  <span class="sb-row-score">{score}</span>
  <span class="sb-row-b{" won" if w == 1 else ""}">{e(b["name"])}{f' <small>{flag(b["nat"])}{e(b["nat"])}</small>' if b.get("nat") else ""}</span>
  {_chips(m.get("games"))}
</div>"""


def _gender(m):
    label = (m.get("label") or "").lower()
    if label.startswith("women") or label.startswith("girls"):
        return "W"
    if label.startswith("men") or label.startswith("boys"):
        return "M"
    return None


def _detail(m):
    if m.get("rubbers"):
        return '<div class="sb-rubbers">' + "".join(_compact(r, label="") for r in m["rubbers"]) + "</div>"
    return _games_table(m)


def _headline(m, i=0, show_event=True, with_detail=True):
    w = _winner(m.get("score"))
    a, b = m["sides"]
    meta = "".join(f"<span>{e(x)}</span>" for x in (m.get("label"), m.get("event") if show_event else None) if x)
    s = m.get("score") or ["", ""]
    detail = _detail(m) if with_detail else ""
    return f"""<div class="sb-top h{i}">
    <div class="sb-meta">{meta}</div>
    <div class="sb-main">
      {_side(a, w == 0, "left")}
      <div class="sb-score" aria-label="{s[0]} to {s[1]}"><b>{s[0]}</b><i aria-hidden="true">–</i><b>{s[1]}</b></div>
      {_side(b, w == 1, "right")}
    </div>
    <p class="sb-status">{e(m.get("status", "Final result"))}</p>
  </div>
  <div class="sb-detail h{i}">{detail}</div>"""


def scoreboard(matches):
    """Headline result(s), then the rest as an equal-weight list.

    Rule: never give one gender's result prominence over the other. When a story
    covers both men's and women's events, the first men's and first women's results
    are shown side by side at the same size. A story about one gender's events only
    keeps a single headline.
    """
    if not matches:
        return ""
    men = next((m for m in matches if _gender(m) == "M"), None)
    women = next((m for m in matches if _gender(m) == "W"), None)
    if men and women:
        heads = [m for m in matches if m is men or m is women]  # keep the story's own order
    else:
        heads = [matches[0]]
    rest = [m for m in matches if not any(m is h for h in heads)]
    pair = len(heads) == 2
    # In a pair, extra detail sits under the cards only if both have it; otherwise it moves
    # down to the results list so neither headline outweighs the other.
    details_under = not pair or all(_detail(h) for h in heads)
    moved = "" if details_under else "".join(
        f'<h3 class="sb-sub">{e(h.get("label", ""))}: match by match</h3>{_detail(h)}' for h in heads if _detail(h))
    more = ""
    if rest or moved:
        more = '<div class="sb-more"><h2 class="sb-more-title">More results</h2>' + moved + "".join(_compact(x) for x in rest) + "</div>"
    event = next((h.get("event") for h in heads if h.get("event")), None)
    strip = f'<div class="sb-event">{e(event)}</div>' if pair and event else ""
    return f"""<section class="scoreboard{" sb-pair" if pair else ""}" aria-label="Results">
  {strip}
  <div class="sb-heads">{"".join(_headline(h, i, show_event=not pair, with_detail=details_under) for i, h in enumerate(heads))}</div>
  {more}
</section>"""


def _uk_time(iso):
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(UK)
    return f"{t:%a} {t.day} {t:%b}, {t:%H:%M}"


def _bracket(ev):
    cols = []
    for rd in ev["rounds"]:
        boxes = []
        for m in rd["matches"]:
            ps = m.get("players") or [None, None]
            scores = (m.get("score") or "").replace("–", "-").split("-") if m.get("score") else ["", ""]
            if len(scores) != 2:
                scores = ["", ""]
            rows = []
            for i, p in enumerate(ps):
                if not p:
                    rows.append('<div class="br-p pending"><span class="nm">To be decided</span></div>')
                    continue
                seed = f'<span class="seed">{p["seed"]}</span>' if p.get("seed") else '<span class="seed"></span>'
                won = " won" if m.get("winner") == i else (" lost" if m.get("winner") is not None else "")
                rows.append(f'<div class="br-p{won}">{seed}<span class="nm">{e(p["name"])}</span><span class="nat">{flag(p["nat"])}{e(p["nat"])}</span><span class="sc">{e(scores[i].strip())}</span></div>')
            when = f'<span class="br-when">{_uk_time(m["when"])}</span>' if m.get("when") and m.get("winner") is None else ""
            boxes.append(f'<div class="br-slot">{when}<div class="br-match">{"".join(rows)}</div></div>')
        cols.append(f'<div class="br-round"><h3>{e(rd["round"])}</h3><div class="br-matches">{"".join(boxes)}</div></div>')
    return "".join(cols)


def draw(ref):
    if not ref:
        return ""
    path = os.path.join(ROOT, "data", "draws", f"{ref}.json")
    if not os.path.exists(path):
        return ""
    d = json.load(open(path, encoding="utf-8"))
    evs = list(d["events"].items())
    tabs = ""
    if len(evs) > 1:
        tabs = '<div class="toggle draw-toggle" role="group" aria-label="Draw">' + "".join(
            f'<button type="button" data-draw="{k}" aria-pressed="{"true" if i == 0 else "false"}">{e(v["name"])}</button>' for i, (k, v) in enumerate(evs)) + "</div>"
    panels = "".join(
        f'<div class="bracket" data-draw-panel="{k}"{"" if i == 0 else " hidden"} tabindex="0" aria-label="{e(v["name"])} draw">{_bracket(v)}</div>' for i, (k, v) in enumerate(evs))
    upd = dt.datetime.fromisoformat(d["updated"].replace("Z", "+00:00")).astimezone(UK)
    return f"""<section class="draw" aria-labelledby="draw-h">
  <div class="draw-head"><h2 id="draw-h">The draw</h2>{tabs}</div>
  <p class="draw-note">Seeds shown in grey. Times are UK time. Scroll sideways to follow each round.</p>
  {panels}
  <p class="draw-note">Official draw from <a href="{e(d["source"])}" rel="noopener">World Table Tennis</a>, updated {upd.day} {upd:%B}, {upd:%H:%M}.</p>
</section>"""


def thumb(vid):
    """HD thumbnail, falling back to the standard one if the upload has no HD version."""
    return (f'<img src="https://i.ytimg.com/vi/{e(vid)}/maxresdefault.jpg" alt="" '
            f'onerror="this.onerror=null;this.src=\'https://i.ytimg.com/vi/{e(vid)}/hqdefault.jpg\'">')


def video_hero(v):
    """Lead image for a story with official video: the video's own preview, playing in place."""
    return f"""<figure class="article-hero video-hero">
  <button type="button" class="yt" data-yt="{e(v['id'])}" aria-label="Play video: {e(v['title'])}">
    {thumb(v['id'])}<span class="yt-play" aria-hidden="true"></span>
    <span class="yt-label"><span class="yt-badge">Watch</span>{e(v['title'])}</span>
  </button>
  <figcaption>Video: {e(v.get('channel', 'YouTube'))}</figcaption>
</figure>"""


def videos(vs):
    if not vs:
        return ""
    items = "".join(f"""<figure class="video">
  <button type="button" class="yt" data-yt="{e(v['id'])}" aria-label="Play video: {e(v['title'])}">
    <img src="https://i.ytimg.com/vi/{e(v['id'])}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360">
    <span class="yt-play" aria-hidden="true"></span>
  </button>
  <figcaption>{e(v['title'])}<span>Video: {e(v.get('channel', 'YouTube'))}</span></figcaption>
</figure>""" for v in vs)
    return f'<section class="videos" aria-labelledby="vid-h"><h2 id="vid-h">Watch</h2><div class="video-grid{" one" if len(vs) == 1 else ""}">{items}</div></section>'


def social(posts):
    """Official Instagram or X posts, shown through each platform's own embed code (which keeps the
    photo with its owner and credits the account). Only official accounts: WTT, ITTF, federations,
    clubs, leagues and the players themselves."""
    if not posts:
        return ""
    items, scripts = [], set()
    for p in posts:
        url = e(p["url"])
        if p["platform"] == "instagram":
            items.append(f'<blockquote class="instagram-media" data-instgrm-permalink="{url}" data-instgrm-version="14"><a href="{url}" rel="noopener">View this post from {e(p.get("account", "Instagram"))} on Instagram</a></blockquote>')
            scripts.add('<script async src="https://www.instagram.com/embed.js"></script>')
        elif p["platform"] == "x":
            items.append(f'<blockquote class="twitter-tweet" data-dnt="true" data-conversation="none"><a href="{url}" rel="noopener">View this post from {e(p.get("account", "X"))} on X</a></blockquote>')
            scripts.add('<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>')
    return f'<section class="social" aria-labelledby="soc-h"><h2 id="soc-h">From the event</h2><div class="social-grid">{"".join(items)}</div>{"".join(sorted(scripts))}</section>'


SCRIPT = """<script>
document.addEventListener("click", function (ev) {
  var b = ev.target.closest(".yt");
  if (b) {
    var f = document.createElement("iframe");
    f.src = "https://www.youtube-nocookie.com/embed/" + b.dataset.yt + "?autoplay=1&rel=0";
    f.title = b.getAttribute("aria-label").replace("Play video: ", "");
    f.allow = "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share";
    f.allowFullscreen = true;
    b.replaceWith(f);
    return;
  }
  var t = ev.target.closest(".draw-toggle button");
  if (t) {
    var s = t.closest(".draw");
    s.querySelectorAll(".draw-toggle button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === t)); });
    s.querySelectorAll("[data-draw-panel]").forEach(function (p) { p.hidden = p.dataset.drawPanel !== t.dataset.draw; });
  }
});
</script>"""
