"""Every story Eleven has published stays published. Eleven is a news site and its archive is permanent.

data/story-ledger.json keeps a copy of every story card that has ever been in data/news.json ("stories", by id) and
the few taken out on purpose ("retired": id -> why, e.g. merged into a fuller article with a redirect, or removed
under the under-15 rule at Tom's request). On every build, any story in the ledger that is missing from news.json and
not retired is put back, and the build says so. Upgrading a story to a full article keeps its card (the article's
"story_id" points to it), so an upgrade is never a reason to remove one.
"""
import json, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NEWS = os.path.join(ROOT, "data", "news.json")
LEDGER = os.path.join(ROOT, "data", "story-ledger.json")


def check():
    news = json.load(open(NEWS, encoding="utf-8"))
    led = json.load(open(LEDGER, encoding="utf-8")) if os.path.exists(LEDGER) else {"retired": {}, "stories": {}}
    have = {s["id"] for s in news["stories"]}
    back = [s for i, s in led["stories"].items() if i not in have and i not in led["retired"]]
    for s in back:
        news["stories"].append(s)
        print(f"ledger: story {s['id']} was missing from news.json and has been put back")
    for s in news["stories"]:
        led["stories"][s["id"]] = s   # the latest version of every live story
    if back:
        json.dump(news, open(NEWS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(NEWS, "a", encoding="utf-8").write("\n")
    json.dump(led, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return back
