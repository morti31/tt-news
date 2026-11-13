"""Site-wide switches in data/switches.json. "wtt": false turns off everything that takes data from World Table Tennis:
the WTT sync, the match and ranking-breakdown syncs, live scores and point by point (worker.js), and the ranking
breakdown on player profiles. Data already saved stays on the site until removed by hand."""
import json, os

PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "data", "switches.json")


def on(name):
    try:
        return json.load(open(PATH, encoding="utf-8")).get(name, True) is not False
    except (OSError, ValueError):
        return True
