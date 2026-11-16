"""Videos for The Chop: YouTube videos from official channels whose titles name one of the chosen defenders.

Sources and players: data/chop/video-sources.json ({"players": [...], "channels": [{"name", "handle", "id"}]}).
Archive: data/chop/videos.json, newest first, never trimmed ({"id", "title", "channel", "date", "players"}).
Each run reads every channel's feed (the latest 15 uploads, with exact dates) and searches the channel for each player
(older videos too); a video found by search gets its publish date from its watch page once.
Runs from .github/workflows/chop-videos.yml; Cloudflare's build turns the archive into /defensive/videos.html.
"""
import json, os, re, time, datetime as dt, html, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "chop", "video-sources.json")
OUT = os.path.join(ROOT, "data", "chop", "videos.json")
HEAD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9", "Cookie": "CONSENT=YES+1; SOCS=CAI"}


def get(url):
    req = urllib.request.Request(url, headers=HEAD)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def words(s):
    return set(re.findall(r"[a-z]+", s.lower()))


def who(title, players):
    w = words(title)
    return [p for p in players if words(p) <= w]


def feed(cid):
    t = get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    out = []
    for en in ET.fromstring(t).findall("a:entry", ns):
        out.append({"id": en.find("yt:videoId", ns).text, "title": en.find("a:title", ns).text or "",
                    "date": (en.find("a:published", ns).text or "")[:19]})
    return out


def search(handle, q):
    t = get(f"https://www.youtube.com/{handle}/search?query={urllib.parse.quote(q)}")
    out = []
    for m in re.finditer(r'"videoRenderer":\{"videoId":"([\w-]{11})".{0,3000}?"title":\{"runs":\[\{"text":"((?:[^"\\]|\\.)*)"', t):
        try:
            title = json.loads(f'"{m[2]}"')
        except Exception:
            title = m[2]
        chunk = t[m.start():m.start() + 20000].split('"videoRenderer":{', 2)[1] if t.count('"videoRenderer":{', m.start()) else ""
        rel = re.search(r'"publishedTimeText":\{"simpleText":"([^"]*)"', chunk)
        out.append({"id": m[1], "title": title, "ago": rel[1] if rel else ""})
    return out


UNIT = {"second": 1 / 86400, "minute": 1 / 1440, "hour": 1 / 24, "day": 1, "week": 7, "wk": 7, "month": 30.4, "mo": 30.4, "year": 365.25, "yr": 365.25}


def from_ago(ago):
    """'3 days ago', '8 mo ago', 'Streamed 1 year ago' -> an approximate date (YouTube search shows no exact one)."""
    m = re.search(r"(\d+)\s*(second|minute|hour|day|week|wk|month|mo|year|yr)", ago or "")
    if not m:
        return None
    d = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=int(m[1]) * UNIT[m[2]])
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def published(vid):
    t = get(f"https://www.youtube.com/watch?v={vid}")
    m = (re.search(r'"publishDate":"([^"]+)"', t) or re.search(r'"uploadDate":"([^"]+)"', t)
         or re.search(r'itemprop="(?:datePublished|uploadDate)" content="([^"]+)"', t))
    return m[1][:19] if m else None


def main():
    cfg = json.load(open(SRC, encoding="utf-8"))
    players = cfg["players"]
    have = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else []
    by_id = {v["id"]: v for v in have}
    added = 0
    tries = 12   # watch pages for exact dates: a few a run, YouTube answers 429 to more
    for ch in cfg["channels"]:
        found = {}
        try:
            for v in feed(ch["id"]):
                found[v["id"]] = v
        except Exception as err:
            print("feed", ch["name"], err)
        for p in players:
            # Full name, then surname alone (YouTube's channel search sometimes returns nothing for the full name)
            for q in (p, p.split()[-1]):
                try:
                    for v in search(ch["handle"], q):
                        found.setdefault(v["id"], v)
                except Exception as err:
                    print("search", ch["name"], q, err)
                time.sleep(1)
        for vid, v in found.items():
            ps = who(html.unescape(v["title"]), players)
            if not ps:
                continue
            if vid in by_id:
                x = by_id[vid]
                x["players"] = sorted(set(x.get("players", [])) | set(ps))
                if x.get("approx") and v.get("date"):     # the feed has the exact date
                    x["date"] = v["date"]; x.pop("approx", None)
                continue
            d, approx = v.get("date"), False
            if not d:
                d, approx = from_ago(v.get("ago")), True
            if not d:
                continue
            by_id[vid] = {"id": vid, "title": html.unescape(v["title"]), "channel": ch["name"], "date": d, "players": ps}
            if approx:
                by_id[vid]["approx"] = True
            added += 1
    # Exact dates for search finds, a few a run
    for x in by_id.values():
        if x.get("approx") and tries > 0:
            tries -= 1
            try:
                d = published(x["id"])
            except Exception as err:
                print("date", x["id"], err)
                tries = 0
                continue
            if d:
                x["date"] = d; x.pop("approx", None)
            time.sleep(4)
    allv = sorted(by_id.values(), key=lambda v: v["date"], reverse=True)
    json.dump(allv, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(OUT, "a").write("\n")
    print(f"chop videos: {added} new, {len(allv)} in all")


if __name__ == "__main__":
    main()
