"""British Clubs League (Table Tennis England), Premier divisions, from TT Leagues (british.ttleagues.com).
--explore prints what the API returns, for setting up."""
import json, sys, urllib.request, urllib.error

API = "https://ttleagues-api.azurewebsites.net/api/"   # the front-door address answers 403 to scripts
HEAD = {"Tenant": "british.ttleagues.com", "Entry": "1", "Accept": "application/json",
        "Origin": "https://british.ttleagues.com", "Referer": "https://british.ttleagues.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def get(path):
    req = urllib.request.Request(path if path.startswith("http") else API + path, headers=HEAD)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def explore():
    for p in sys.argv[2:] or ["leagues/2131", "divisions/6041", "divisions/6041/standings", "divisions/6041/matches"]:
        try:
            d = get(p)
            print("==", p, json.dumps(d)[:40000])
        except urllib.error.HTTPError as err:
            print("==", p, "ERR", err, err.read()[:300])
        except Exception as err:
            print("==", p, "ERR", err)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--explore"]:
        explore()
