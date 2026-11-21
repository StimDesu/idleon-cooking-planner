"""Index of every bonus source in the game code: which list, which row, what text, which stat key.

    python tools/bonus_index.py [--game "<Legends of Idleon folder>"]        -> docs/bonus_index.json + docs/bonus_index.md
    python tools/bonus_index.py --find "cook"                                -> print matching sources

How it works: N.js keeps game data as `X.<Name>=function(){return [...]}` list literals. Bonus rows carry a text
with a `{` or `}` placeholder (the number) like "+{%_Meal_Cooking_Speed". Every literal is walked, every string
with a placeholder is recorded with its list name and row path, plus the other short identifier-like strings of
the same row (these are usually the stat key the code reads, e.g. "MealCook" for a vial, "Mcook" for a meal).
Item definitions (stamps, obols, cards…) are read too: their `desc_line*` fields hold the same kind of text.
The result answers "where can stat X come from"; the formulas that turn levels into values live in
docs/GAME_FORMULAS.md.
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
from gamecode import read_game, literal  # noqa: E402
import items as itemdefs  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLACE = re.compile(r"[{}]")
KEYLIKE = re.compile(r"^[A-Za-z0-9]{2,24}$")


def walk(v, path, out, row):
    if isinstance(v, list):
        for i, x in enumerate(v):
            # a "row" is the innermost list that holds strings
            walk(x, path + [i], out, v if any(isinstance(y, str) for y in v) else row)
    elif isinstance(v, str) and PLACE.search(v) and "_" in v:
        keys = [y for y in (row or []) if isinstance(y, str) and KEYLIKE.match(y) and not y.isdigit()]
        out.append((path, v, keys[:6]))


def build(njs):
    names = sorted(set(re.findall(r"\.(\w+)=function\(\)\{return\[", njs)))
    res = []
    for n in names:
        try:
            v = literal(njs, n)
        except Exception:
            continue
        found = []
        walk(v, [], found, None)
        for path, text, keys in found:
            res.append({"src": n, "at": path, "text": text.replace("_", " "), "keys": keys})
    for k, d in itemdefs.parse(njs).items():
        for f in ("desc_line1", "desc_line2", "desc_line3", "desc_line4"):
            t = str(d.get(f, ""))
            if PLACE.search(t) and t != "Filler":
                res.append({"src": "item:" + k, "at": [f], "text": t.replace("_", " "), "keys": [d.get("Type", "")]})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=r"D:\Games\SteamLibrary\steamapps\common\Legends of Idleon")
    ap.add_argument("--find")
    a = ap.parse_args()
    path = os.path.join(ROOT, "docs", "bonus_index.json")
    if a.find:
        idx = json.load(open(path, encoding="utf-8"))
        q = a.find.lower()
        sys.stdout.reconfigure(encoding="utf-8")
        for r in idx:
            if q in r["text"].lower() or any(q in k.lower() for k in r["keys"]):
                print(f'{r["src"]}{r["at"]}  {r["text"]}  {r["keys"]}')
        return
    njs, _ = read_game(a.game)
    res = build(njs)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(res, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    by = {}
    for r in res:
        by.setdefault(r["src"].split(":")[0] if r["src"].startswith("item:") else r["src"], 0)
        by[r["src"].split(":")[0] if r["src"].startswith("item:") else r["src"]] += 1
    with open(os.path.join(ROOT, "docs", "bonus_index.md"), "w", encoding="utf-8") as f:
        f.write("# Bonus source index (generated)\n\nMade by `python tools/bonus_index.py`; search with `--find <text>`.\n"
                f"{len(res)} bonus texts in {len(by)} lists.\n\n| List | Rows with a bonus text |\n|---|---|\n")
        for k, v in sorted(by.items(), key=lambda x: -x[1]):
            f.write(f"| {k} | {v} |\n")
    print(len(res), "bonus texts in", len(by), "lists")


if __name__ == "__main__":
    main()
