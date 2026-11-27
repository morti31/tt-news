"""Prints "yes" when a tournament (not a club fixture) is on today, else "no". Reads data/schedule.json from stdin.
Used by the Pulse workflow to deploy every 30 minutes during tournaments and hourly otherwise."""
import sys, json, datetime as d
try:
    ev = json.load(sys.stdin).get("events", [])
    t = d.date.today().isoformat()
    print("yes" if any(e.get("start") and e["start"] <= t <= (e.get("end") or e["start"]) and e.get("series") != "Clubs" for e in ev) else "no")
except Exception:
    print("yes")
