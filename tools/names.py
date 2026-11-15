"""One place for how Eleven writes player names. Every tool that turns WTT's "FAMILY Given" into a name uses this, and
the worker (live scores, match popup) reads the same rules from data/names-live.json, which the build writes.

  data/names.json   family_first: associations whose players keep the family name first (Chinese, Korean ...)
                    fixes: WTT's spelling -> Eleven's (accents, Fang Bo for a Chinese-born player who plays for Kazakhstan)
  data/players/*    a player's profile name wins over the same words in reverse order, so a player like Fang Bo is
                    never "Bo Fang" anywhere once he has a profile, whatever association he plays for.
"""
import glob, json, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_cfg = json.load(open(os.path.join(ROOT, "data", "names.json"), encoding="utf-8"))
FAMILY_FIRST = set(_cfg["family_first"])
FIXES = dict(_cfg["fixes"])
_swap = None


def swaps():
    """{reversed profile name: profile name} for every two-part profile name whose reverse is not itself a profile."""
    global _swap
    if _swap is None:
        names = set()
        for f in glob.glob(os.path.join(ROOT, "data", "players", "*.json")):
            if os.path.basename(f) in ("wtt.json", "wanted.json"):
                continue
            try:
                n = json.load(open(f, encoding="utf-8")).get("name")
            except Exception:
                continue
            if n:
                names.add(n)
        _swap = {}
        for n in names:
            w = n.split(" ")
            if len(w) == 2:
                r = f"{w[1]} {w[0]}"
                if r not in names:
                    _swap[r] = n
    return _swap


def fix(name):
    name = (name or "").strip()
    if not name:
        return name
    name = FIXES.get(name, name)
    return swaps().get(name, name)


def cap(s):
    out, up = [], True
    for ch in s.lower():
        out.append(ch.upper() if up else ch)
        up = ch in " -"
    return "".join(out)


def from_wtt(raw, org):
    """'LIN Yun-Ju' + TPE -> 'Lin Yun-Ju'; 'LEBRUN Felix' + FRA -> 'Félix Lebrun'; 'FANG Bo' + KAZ -> 'Fang Bo'."""
    words = (raw or "").split()
    fam = " ".join(cap(w) for w in words if w.isupper() or w.replace("-", "").isupper())
    giv = " ".join(w for w in words if not (w.isupper() or w.replace("-", "").isupper()))
    return fix(f"{fam} {giv}" if org in FAMILY_FIRST else f"{giv} {fam}")


def write_live():
    """data/names-live.json for the worker and the browser: the same rules in one small file."""
    json.dump({"family_first": sorted(FAMILY_FIRST), "fixes": {**swaps(), **FIXES}}, open(os.path.join(ROOT, "data", "names-live.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))


def check(texts):
    """Name warnings for the build: a profiled player written in reverse order anywhere in the given (label, text) pairs."""
    sw = swaps()
    rx = re.compile(r"\b(" + "|".join(re.escape(k) for k in sorted(sw, key=len, reverse=True)) + r")\b") if sw else None
    out = []
    for label, t in texts:
        for m in (rx.finditer(t or "") if rx else []):
            out.append(f"{label}: '{m.group(1)}' should be '{sw[m.group(1)]}'")
    return out
