"""Builds calendar.ics (the subscribable feed) from data/schedule.json.

Run after every change to the schedule:  python3 tools/build_calendar.py
Tournaments become all-day events; fixtures with times become timed events in UTC.
UIDs are stable, so subscribers' calendars update in place instead of duplicating.
"""
import json, os, datetime as dt

ROOT = os.path.join(os.path.dirname(__file__), "..")
SITE = "https://tt-news.tommorti.workers.dev"
data = json.load(open(os.path.join(ROOT, "data", "schedule.json"), encoding="utf-8"))


def esc(s):
    return str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    """Fold long lines at 75 octets as the iCalendar spec requires."""
    out, b = [], line.encode("utf-8")
    while len(b) > 75:
        cut = 75 if not out else 74
        while (b[cut] & 0xC0) == 0x80:  # don't split a multi-byte character
            cut -= 1
        out.append(b[:cut].decode("utf-8"))
        b = b[cut:]
    out.append(b.decode("utf-8"))
    return "\r\n ".join(out)


stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
lines = [
    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Eleven//Table tennis calendar//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
    "X-WR-CALNAME:Eleven: table tennis", "X-WR-TIMEZONE:UTC",
    "X-WR-CALDESC:" + esc("Major table tennis tournaments, club competitions and session times. Updated by Eleven: " + SITE),
    "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H",
]

for e in data["events"]:
    start = dt.date.fromisoformat(e["start"])
    end = dt.date.fromisoformat(e["end"]) + dt.timedelta(days=1)  # DTEND is exclusive for all-day events
    place = ", ".join(x for x in (e.get("venue"), e.get("city"), e.get("country")) if x and x not in ("Europe", "Asia"))
    desc = f'{e["type"]}. ' + (f'Prestige {e["prestige"]}/5. ' if e.get("prestige") else "") + f"News, results and schedule: {SITE}/schedule.html"
    lines += ["BEGIN:VEVENT", f'UID:{e["id"]}@eleven-tt', f"DTSTAMP:{stamp}",
              f"DTSTART;VALUE=DATE:{start:%Y%m%d}", f"DTEND;VALUE=DATE:{end:%Y%m%d}",
              "SUMMARY:" + esc(e["name"]), "DESCRIPTION:" + esc(desc), "TRANSP:TRANSPARENT"]
    if place:
        lines.append("LOCATION:" + esc(place))
    lines.append("END:VEVENT")

for f in data.get("fixtures", []):
    s = dt.datetime.fromisoformat(f["start"].replace("Z", "+00:00"))
    en = dt.datetime.fromisoformat(f["end"].replace("Z", "+00:00")) if f.get("end") else s + dt.timedelta(hours=2)
    parent = next((e for e in data["events"] if e["id"] == f.get("event_id")), {})
    place = ", ".join(x for x in (parent.get("venue"), parent.get("city"), parent.get("country")) if x)
    desc = (f.get("detail", "") + " " if f.get("detail") else "") + "Live scores: https://www.worldtabletennis.com/"
    lines += ["BEGIN:VEVENT", f'UID:{f["id"]}@eleven-tt', f"DTSTAMP:{stamp}",
              f"DTSTART:{s:%Y%m%dT%H%M%SZ}", f"DTEND:{en:%Y%m%dT%H%M%SZ}",
              "SUMMARY:" + esc(f["name"]), "DESCRIPTION:" + esc(desc)]
    if place:
        lines.append("LOCATION:" + esc(place))
    lines.append("END:VEVENT")

lines.append("END:VCALENDAR")
with open(os.path.join(ROOT, "calendar.ics"), "w", encoding="utf-8", newline="") as fh:
    fh.write("\r\n".join(fold(l) for l in lines) + "\r\n")
print(f'calendar.ics: {len(data["events"])} events, {len(data.get("fixtures", []))} fixtures')
