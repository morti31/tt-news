"""Scans Google News and table tennis sites for recent headlines and writes a digest for the update runs.

Run by .github/workflows/news-scan.yml (hourly) on GitHub's servers, which can reach sites the update
sandbox cannot. The digest is pushed to the `scan` branch as scan/digest.json and scan/digest.md.
The update run reads it with `git fetch origin scan` (see UPDATE.md, step 2).

    python3 tools/news_scan.py <output directory>

Only headlines, links, outlets and dates are kept, never article text.
"""
import json, os, sys, re, urllib.request, urllib.parse, datetime as dt
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
HOURS = 60  # keep items from the last 60 hours

# Google News searches: (label, query, language/region parameters). `when:2d` limits to two days.
GN = [
    ("en-GB", "table tennis when:2d", "hl=en-GB&gl=GB&ceid=GB:en"),
    ("en-US", "table tennis when:2d", "hl=en-US&gl=US&ceid=US:en"),
    ("en-IN", "table tennis when:2d", "hl=en-IN&gl=IN&ceid=IN:en"),
    ("en", "WTT Champions Frankfurt when:2d", "hl=en-GB&gl=GB&ceid=GB:en"),
    ("en", "WTT table tennis withdraws OR wins OR beats when:2d", "hl=en-GB&gl=GB&ceid=GB:en"),
    ("en", "Youth Olympic Games Dakar table tennis when:3d", "hl=en-GB&gl=GB&ceid=GB:en"),
    ("en", "ITTF OR ETTU OR \"Table Tennis England\" when:3d", "hl=en-GB&gl=GB&ceid=GB:en"),
    ("en", "ping pong OR \"table tennis\" bat OR rubber OR racket review when:7d", "hl=en-GB&gl=GB&ceid=GB:en"),
    ("zh", "乒乓球 when:2d", "hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
    ("zh", "国乒 when:2d", "hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
    ("zh", "乒超联赛 when:3d", "hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
    ("zh-TW", "桌球 when:2d", "hl=zh-TW&gl=TW&ceid=TW:zh-Hant"),
    ("ja", "卓球 when:2d", "hl=ja&gl=JP&ceid=JP:ja"),
    ("ja", "Tリーグ 卓球 when:3d", "hl=ja&gl=JP&ceid=JP:ja"),
    ("ko", "탁구 when:2d", "hl=ko&gl=KR&ceid=KR:ko"),
    ("de", "Tischtennis when:2d", "hl=de&gl=DE&ceid=DE:de"),
    ("de", "TTBL Tischtennis Bundesliga when:3d", "hl=de&gl=DE&ceid=DE:de"),
    ("fr", "tennis de table when:2d", "hl=fr&gl=FR&ceid=FR:fr"),
    ("fr", "tennis de table Lebrun when:3d", "hl=fr&gl=FR&ceid=FR:fr"),
    ("es", "tenis de mesa when:2d", "hl=es&gl=ES&ceid=ES:es"),
    ("pt", "tênis de mesa Calderano when:3d", "hl=pt-BR&gl=BR&ceid=BR:pt-419"),
    # site-limited searches for outlets without a usable feed
    ("de", "site:tischtennis.de when:3d", "hl=de&gl=DE&ceid=DE:de"),
    ("de", "site:mytischtennis.de when:3d", "hl=de&gl=DE&ceid=DE:de"),
    ("de", "site:ttbl.de when:3d", "hl=de&gl=DE&ceid=DE:de"),
    ("ja", "site:jtta.or.jp OR site:tleague.jp OR site:spread-sports.jp when:3d", "hl=ja&gl=JP&ceid=JP:ja"),
    ("fr", "site:fftt.com when:3d", "hl=fr&gl=FR&ceid=FR:fr"),
    ("en", "site:worldtabletennis.com when:3d", "hl=en-GB&gl=GB&ceid=GB:en"),
    ("en", "site:ittf.com when:3d", "hl=en-GB&gl=GB&ceid=GB:en"),
    ("en", "site:ettu.org when:3d", "hl=en-GB&gl=GB&ceid=GB:en"),
    ("en", "site:tabletennisengland.co.uk when:3d", "hl=en-GB&gl=GB&ceid=GB:en"),
    ("en", "site:butterflyonline.com OR site:mltt.com OR site:tabletennisdaily.com when:3d", "hl=en-GB&gl=GB&ceid=GB:en"),
]

# Sites' own feeds (WordPress sites publish /feed/). Failures are recorded, not fatal.
FEEDS = [
    "https://www.ittf.com/feed/",
    "https://www.ettu.org/feed/",
    "https://www.tabletennisengland.co.uk/feed/",
    "https://butterflyonline.com/feed/",
    "https://pingsunday.com/feed/",
    "https://www.tischtennis.de/news.rss",
    "https://www.mytischtennis.de/news/top-sport.rss",
    "https://www.ttbl.de/rss",
    "https://www.worldtabletennis.com/rss",
    "https://www.tabletennisdaily.com/forum/forums/-/index.rss",
    "https://www.fftt.com/feed/",
    "https://tleague.jp/feed/",
    "https://www.ktta.or.kr/rss",
]

# WTT live API: official results and schedule for events on now (Dakar Youth Olympic Games, current WTT events)
WTT = "https://wtt-website-api-vm-frontdoor-hhaec5epbhdyfugz.a01.azurefd.net/liveeventsapi/api/cms"


def get(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def when(text):
    try:
        d = parsedate_to_datetime(text)
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except Exception:
        pass
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def parse(xml, label):
    """RSS 2.0 and Atom; returns [{title, url, source, published, via}]."""
    root = ET.fromstring(xml)
    out = []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for it in root.iter("item"):
        src = it.find("source")
        out.append({"title": (it.findtext("title") or "").strip(), "url": (it.findtext("link") or "").strip(),
                    "source": (src.text if src is not None else "") or "", "published": it.findtext("pubDate") or "", "via": label})
    for en in root.findall("a:entry", ns):
        link = en.find("a:link", ns)
        out.append({"title": (en.findtext("a:title", namespaces=ns) or "").strip(), "url": link.get("href") if link is not None else "",
                    "source": "", "published": en.findtext("a:updated", namespaces=ns) or en.findtext("a:published", namespaces=ns) or "", "via": label})
    return out


def main(outdir):
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=HOURS)
    items, status = {}, []

    def add(rows):
        for r in rows:
            if not r["title"] or not r["url"]:
                continue
            d = when(r["published"])
            if d and d < cutoff:
                continue
            r["published"] = d.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ") if d else ""
            key = re.sub(r"\W+", "", r["title"].lower())[:80]
            items.setdefault(key, r)

    for lang, q, params in GN:
        url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(q) + "&" + params
        try:
            rows = parse(get(url), f"Google News ({lang}): {q}")
            add(rows); status.append({"source": f"gn {lang} {q}", "ok": True, "items": len(rows)})
        except Exception as e:
            status.append({"source": f"gn {lang} {q}", "ok": False, "error": str(e)[:120]})
    for url in FEEDS:
        try:
            rows = parse(get(url), url)
            for r in rows:
                r["source"] = r["source"] or urllib.parse.urlparse(url).netloc
            add(rows); status.append({"source": url, "ok": True, "items": len(rows)})
        except Exception as e:
            status.append({"source": url, "ok": False, "error": str(e)[:120]})

    # Official WTT data for events on now (ids read from the site's own events file when present)
    wtt = {}
    ids = ["3219"]
    try:
        ev = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data", "events.json"), encoding="utf-8"))
        for h in (ev["events"] if isinstance(ev, dict) else ev):
            if h.get("wtt_id") and h.get("start", "") <= (now + dt.timedelta(days=2)).strftime("%Y-%m-%d") and h.get("end", "") >= (now - dt.timedelta(days=1)).strftime("%Y-%m-%d"):
                ids.append(str(h["wtt_id"]))
    except Exception:
        pass
    for i in dict.fromkeys(ids):
        for name, path in (("results", f"GetOfficialResult?EventId={i}&include_match_card=true&take=100"), ("schedule", f"GetEventSchedule/{i}")):
            try:
                body = get(f"{WTT}/{path}", {"Origin": "https://www.worldtabletennis.com", "Referer": "https://www.worldtabletennis.com/"})
                wtt[f"{i}/{name}"] = json.loads(body) if body.strip() else None
                status.append({"source": f"wtt {i} {name}", "ok": True, "bytes": len(body)})
            except Exception as e:
                status.append({"source": f"wtt {i} {name}", "ok": False, "error": str(e)[:120]})

    rows = sorted(items.values(), key=lambda r: r["published"], reverse=True)
    os.makedirs(outdir, exist_ok=True)
    json.dump({"generated": now.strftime("%Y-%m-%dT%H:%MZ"), "window_hours": HOURS, "items": rows, "status": status},
              open(os.path.join(outdir, "digest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(wtt, open(os.path.join(outdir, "wtt.json"), "w", encoding="utf-8"), ensure_ascii=False)
    with open(os.path.join(outdir, "digest.md"), "w", encoding="utf-8") as f:
        f.write(f"# News scan {now:%Y-%m-%d %H:%M} UTC, last {HOURS} hours, {len(rows)} headlines\n\n")
        for r in rows:
            f.write(f"- {r['published']} | {r['source']} | {r['title']} | {r['url']}\n")
        f.write("\n## Source status\n\n")
        for s in status:
            f.write(f"- {'ok ' if s['ok'] else 'FAIL'} {s['source']} {s.get('items', s.get('bytes', ''))} {s.get('error', '')}\n")
    print(f"{len(rows)} headlines; {sum(s['ok'] for s in status)}/{len(status)} sources ok")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "scan")
