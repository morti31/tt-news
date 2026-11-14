"""The doubles world rankings on the site (data/doubles-rankings.json, from tools/doubles_rankings.py): every ranked
player with their gender and each pair they are ranked in. Used by the roster (everyone ranked gets a page), the stub
writer, the rankings page and player profiles."""
import json, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EVENTS = (("women", "Women's doubles"), ("men", "Men's doubles"), ("mixed", "Mixed doubles"))


def load():
    p = os.path.join(ROOT, "data", "doubles-rankings.json")
    try:
        return json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def players(D=None, singles=None):
    """{ittf_id: {"name", "nat", "gender", "pairs": [(event key, pair)]}}. Gender from men's or women's doubles or the
    singles ranking; a mixed-only player is the opposite of a partner whose gender is known."""
    D = D if D is not None else load()
    out = {}
    for key, _ in EVENTS:
        for pair in D.get(key, []):
            for p in pair["players"]:
                if not p.get("ittf_id"):
                    continue
                r = out.setdefault(p["ittf_id"], {"name": p["name"], "nat": p["nat"], "gender": None, "pairs": []})
                r["pairs"].append((key, pair))
                if key != "mixed":
                    r["gender"] = "M" if key == "men" else "W"
    for g, code in (("men", "M"), ("women", "W")):
        for p in (singles or {}).get(g, []):
            if p.get("ittf_id") in out and not out[p["ittf_id"]]["gender"]:
                out[p["ittf_id"]]["gender"] = code
    for _ in range(2):
        for pair in D.get("mixed", []):
            ps = [out.get(p.get("ittf_id")) for p in pair["players"]]
            if len(ps) == 2 and all(ps):
                a, b = ps
                if a["gender"] and not b["gender"]:
                    b["gender"] = "W" if a["gender"] == "M" else "M"
                elif b["gender"] and not a["gender"]:
                    a["gender"] = "W" if b["gender"] == "M" else "M"
    return out
