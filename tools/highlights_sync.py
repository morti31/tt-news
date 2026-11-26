"""WTT's match highlights for the home page's Watch section: data/wtt-highlights.json.

The Cloudflare worker (/api/highlights) reads WTT's YouTube channel live, but YouTube sometimes answers the worker with a
page that lists no videos, and then Watch fell back to the hand-picked clips in news.json, weeks old. GitHub's runners
do get the channel, so this script (run every 30 minutes by .github/workflows/highlights-sync.yml, started by Pulse)
saves the channel's newest match highlights as a static file the page can always read.

Titles look like "Chen Yi vs Peng Yu-Han | WS R32 | #WTTMontpellier 2026". Each saved clip:
{"id", "title" ("Chen Yi v Peng Yu-Han, women's singles last 32"), "gender" (M, W or X), "tag" ("WTTMontpellier 2026"),
 "date" (YYYY-MM-DD, only for clips in the channel's RSS feed, else null)}, newest first.
The file is left alone when YouTube lists nothing, so a bad fetch never wipes it. Exit code 1 if nothing could be read at all.
"""
import json, os, re, sys, datetime as dt, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "wtt-highlights.json")
CHANNEL = "https://www.youtube.com/@WTTGlobal"
CHANNEL_ID = "UC9ckyA_A3MfXUa0ttxMoIZw"
HEAD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9", "Cookie": "CONSENT=YES+1; SOCS=CAI"}
EVENTS = {"MS": ("M", "men's singles"), "WS": ("W", "women's singles"), "MD": ("M", "men's doubles"),
          "WD": ("W", "women's doubles"), "XD": ("X", "mixed doubles")}
ROUNDS = {"F": "final", "Final": "final", "SF": "semi-final", "QF": "quarter-final", "R16": "last 16", "R32": "last 32", "R64": "last 64"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEAD), timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def tab_videos():
    html = ""
    for u in (CHANNEL + "/videos", CHANNEL + "/videos?hl=en&gl=GB"):
        try:
            html = get(u)
        except Exception as e:
            print("tab fetch failed:", u, e)
            continue
        if '"lockupViewModel":{' in html:
            break
    out = []
    for chunk in html.split('"lockupViewModel":{')[1:]:
        vid = re.search(r'"contentId":"([\w-]{11})"', chunk)
        title = re.search(r'"lockupMetadataViewModel":\{"title":\{"content":"((?:[^"\\]|\\.)*)"', chunk)
        if vid and title:
            try:
                t = json.loads('"%s"' % title.group(1))
            except Exception:
                t = title.group(1)
            out.append({"id": vid.group(1), "title": t, "date": None})
    return out


def rss_videos():
    try:
        root = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"))
    except Exception as e:
        print("rss fetch failed:", e)
        return []
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    return [{"id": en.find("yt:videoId", ns).text, "title": en.find("a:title", ns).text or "",
             "date": (en.find("a:published", ns).text or "")[:10]} for en in root.findall("a:entry", ns)]


def parse(v):
    parts = [x.strip() for x in v["title"].split("|")]
    if len(parts) < 3 or not re.search(r" vs ", parts[0], re.I) or re.match(r"(LIVE|FULL MATCH)", v["title"], re.I):
        return None
    code, *rest = parts[1].split()
    if code not in EVENTS:
        return None
    rnd = " ".join(rest)
    m = re.match(r"#?(\w+)(?:\s+(\d{4}))?", parts[-1])   # "#WTTMuscat 2026" (WTT sometimes types "2026o"): hashtag and year only
    if not m:
        return None
    tag = m.group(1) + (" " + m.group(2) if m.group(2) else "")
    gender, name = EVENTS[code]
    title = re.sub(r" vs ", " v ", parts[0], flags=re.I) + ", " + name + " " + ROUNDS.get(rnd, rnd)
    return {"id": v["id"], "title": title.strip(), "gender": gender, "tag": tag, "date": v.get("date")}


def main():
    tab, rss = tab_videos(), rss_videos()
    dates = {v["id"]: v["date"] for v in rss}
    seen, vids = set(), []
    for v in tab + rss:           # the tab is newest first and longer; the feed adds exact dates and covers a tab that failed
        if v["id"] in seen:
            continue
        seen.add(v["id"])
        v["date"] = v["date"] or dates.get(v["id"])
        p = parse(v)
        if p:
            vids.append(p)
    print(f"tab {len(tab)} videos, feed {len(rss)}, {len(vids)} match highlights")
    if not vids:
        print("nothing read: leaving the file as it is")
        return 1 if not os.path.exists(OUT) else 0
    out = {"updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "channel": "World Table Tennis", "videos": vids[:60]}
    old = {}
    try:
        old = json.load(open(OUT))
    except Exception:
        pass
    if old.get("videos") == out["videos"]:
        print("no change")
        return 0
    with open(OUT, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
