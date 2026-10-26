"""Writes a pull request description that shows each article in full, ready to read and merge.

Usage: python3 tools/review_body.py data/articles/a.json data/articles/b.json ... > body.md
"""
import json, sys

files = sys.argv[1:]
out = [f"**{len(files)} article{'s' if len(files) != 1 else ''} waiting.** Read below, then tap **Merge pull request** at the bottom to publish them all. "
       "To drop one, ask Claude to remove it, or close this request to publish none.\n"]
for i, f in enumerate(files, 1):
    a = json.load(open(f, encoding="utf-8"))
    words = sum(len(p.split()) for p in a["body"])
    tags = [a["category"], f"{words} words", "by " + {"michael": "Michael Dobbs", "michelle": "Michelle Nemeth"}.get(a.get("author"), "Tom Mortimer")] + ([f"translated from {a['lang']}"] if a.get("lang") else [])
    out.append("---\n")
    out.append(f"### {i}. {a['title']}\n")
    out.append(f"_{' · '.join(tags)}_\n")
    out.append(f"**{a['standfirst']}**\n")
    out += [p + "\n" for p in a["body"]]
    out.append("Sources: " + ", ".join(f"[{s['name']}]({s['url']})" for s in a["sources"]) + "\n")
out.append("---\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n")
print("\n".join(out))
