"""Builds src/data.json and the sprite sheets in img/ from the installed Steam game.

    python tools/extract.py [--game "<Legends of Idleon folder>"] [--ru <IdleOn-Rusificator/translation>]

Everything comes from the game files (N.js and lib/default.pak inside resources/app.asar):
  * MealINFO            - meal name, cook requirement, bonus per level, bonus text, bonus category;
  * RANDOlist[49]       - the meal each single spice gives in "New Recipe";
  * RANDOlist[50]       - base odds of the 1st, 2nd, ... possible recipe of a spice combo;
  * RANDOlist[53]       - Pet Arena waves needed for each arena bonus (bonus 7 = -50% kitchen costs);
  * TerritoryInfo       - Breeding territory names (spice N comes from territory N);
  * JewelDesc, ChipDesc - Lab jewels and chips that cost meals and spices;
  * ArtifactInfo 13/17  - Triagulon (speed per power of 10 Turkeys) and Causticolumn (meal max level);
  * icons CookingM*, CookingSpice*, Ribbon*, CookingF*, Ladle from default.pak.
Formulas (CookingR, MealBonusesS, RibbonBonus, ...) are ported by hand into src/template.html.
Russian texts are optional and come from the IdleOn-Rusificator dictionaries.
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
from gamecode import read_game, literal, Assets  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def clean(s):
    return s.replace("_", " ").replace("|", " ").strip()


def num(s):
    f = float(s)
    return int(f) if f.is_integer() and abs(f) < 1e15 else f


def sheet(assets, names, cell, cols, out):
    """Packs images into a grid of fixed cells (top-left aligned, no scaling) and returns cols."""
    from PIL import Image
    rows = (len(names) + cols - 1) // cols
    img = Image.new("RGBA", (cols * cell[0], rows * cell[1]))
    for n, name in enumerate(names):
        im = assets.image("assets/data/%s.png" % name)
        x, y = (n % cols) * cell[0], (n // cols) * cell[1]
        img.paste(im, (x + (cell[0] - im.width) // 2, y + (cell[1] - im.height) // 2))
    img.save(os.path.join(ROOT, "img", out), optimize=True)
    print("img/%s: %d icons %s" % (out, len(names), img.size))
    return {"w": cell[0], "h": cell[1], "cols": cols}


def game_mbs_letters(assets):
    """Number2Letter as stored in assets/data/game.mbs: a list of 1-char strings ('_', a..z, A..Z)."""
    import gzip
    e = assets.ent["assets/data/game.mbs"]
    raw = assets.pak[e["position"]:e["position"] + e["length"]]
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    i = raw.find(b"Number2Letter")
    m = re.search(rb"(?:\x00\x00\x00\x01(.))+", raw[i:i + 2000])
    return [c.decode() for c in re.findall(rb"\x00\x00\x00\x01(.)", m.group(0))]


def account_calc(njs, rl, assets):
    """Constants for the account-wide multipliers of CookingSPEED / CookingFIRE / meal bonus / max level."""
    import items as itemdefs  # noqa: F401  (item definitions: stamps)
    L = lambda n: literal(njs, n)
    alch = L("AlchemyDescription")
    fx = lambda r: [num(r[1]), num(r[2]), r[3]]          # x1, x2, formula type of ArbitraryCode5Inputs
    vials = {}
    for i, r in enumerate(alch[4]):
        key = r[11] if len(r) > 11 else ""
        if key in ("MealCook", "RecCook", "Kcosts", "6CookSpd", "6turtle"):
            vials.setdefault(key, []).append([i] + fx(r))
    stamps = {}
    for k, d in itemdefs.parse(njs).items():
        m = re.match(r"Stamp([ABC])(\d+)$", k)
        f = str(d.get("desc_line1", "")).split(",")
        if m and f[0] in ("MealCook", "RecipeCook"):
            stamps[f[0]] = ["ABC".index(m.group(1)), int(m.group(2)) - 1, f[1], num(f[2]), num(f[3]), num(f[4]), num(f[10])]
    cards = {r[0]: num(r[2]) for grp in L("CardStuff") for r in grp if isinstance(r, list) and len(r) > 2 and r[0] in ("Boss4A", "w6c1")}
    se = L("SummonEnemies")
    comp = L("CompanionDB")
    uv = L("UpgradeVault")
    tal = L("TalentDescriptions")
    sig = L("SigilDesc")[18]
    arc = L("ArcadeShopInfo")
    letters = game_mbs_letters(assets)
    tourny = [x for row in L("TournyStuff") for x in row]
    return {
        "n2l": letters + tourny,
        "diamondChef": fx(alch[3][17]), "vials": vials, "vialCount": len(alch[4]), "stamps": stamps,
        "arcade": {i: fx(arc[i]) for i in (28, 54)},
        "atom8": num(L("AtomInfo")[8][4]),
        "vault": {i: num(uv[i][5]) for i in (42, 54, 61, 89)},
        "talent59": fx([None] + tal[59][1][0:3]), "talent49": fx([None] + tal[49][1][0:3]),
        "cards": cards,
        "summon": {"name": se[0], "bonus": se[5], "val": se[7], "endBonus": se[9], "endVal": se[10]},
        "comp": {i: [num(comp[i][2]), num(comp[i][11])] for i in (27, 88, 162)},
        "research58": [num(x) for x in L("Research")[58]],
        "grim26": num(L("GrimoireUpg")[26][5]),
        "sigil18": [num(sig[3]), num(sig[4]), num(sig[8]), num(sig[10]), num(sig[12])],
        "crucWaves": [int(x) for x in rl[115]],
        "mapKills": [num(m[0][0]) for m in L("MapDetails")],
        "pristine": {t: num(re.search(r'NjTrP%s="([^"]+)"' % t, njs).group(1).split(" ")[3]) for t in ("8", "17")},  # CustomMaps NjEQ
        "starSigns": [s[0] for s in L("StarSigns")],
        "holes": {"mon": [num(x) for x in L("HolesInfo")[37]], "cosmo00": num(L("CosmoUpgrades")[0][0][0]),
                  "fount013": num(L("HoleFountUPG")[0][13][6]),
                  "lamp": [[num(v) for v in g.split(",")] for g in re.search(r'HoleozDT="([0-9,;]+)"', njs).group(1).split(";")]},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=r"D:\Games\SteamLibrary\steamapps\common\Legends of Idleon")
    ap.add_argument("--ru", default=os.path.join(ROOT, "..", "IdleOn-Rusificator", "translation"))
    a = ap.parse_args()

    njs, pakdata = read_game(a.game)
    assets = Assets(njs, pakdata)
    ru = {}
    if os.path.isdir(a.ru):
        for f in ("items.json", "lists.json", "code.json"):
            for k, v in json.load(open(os.path.join(a.ru, f), encoding="utf-8")).items():
                ru.setdefault(k, v)
    else:
        print("no Russian dictionaries at", a.ru)
    tr = lambda s: clean(ru[s]) if s in ru else None

    rl = literal(njs, "RANDOlist")
    meals = []
    for m in literal(njs, "MealINFO"):
        meals.append({"en": clean(m[0]), "ru": tr(m[0]), "req": num(m[1]), "base": num(m[2]),
                      "d": clean(m[3]), "dru": tr(m[3]), "cat": m[5]})
    terr = literal(njs, "TerritoryInfo")
    # Breeding("TerritoryID"): territory index i -> TerritoryInfo row i + floor((i + 86.1) / 100), so row 14 is skipped
    spices = []
    for i in range(30):
        row = i + (1 if i >= 14 else 0)
        name = terr[row][4] if row < len(terr) and terr[row][4] != "Filler_Filler" else None
        spices.append({"en": clean(name) if name else None, "ru": tr(name) if name else None})

    def costs(lst, n_name, n_meal, n_mq, n_spice, n_sq, n_desc, n_item=None, n_iq=None):
        out = []
        for r in lst:
            out.append({"en": clean(r[n_name]), "ru": tr(r[n_name]), "meal": int(r[n_meal][4:]), "mq": num(r[n_mq]),
                        "spice": int(r[n_spice][5:]), "sq": num(r[n_sq]), "d": clean(r[n_desc]), "dru": tr(r[n_desc]),
                        "item": r[n_item] if n_item is not None else None, "iq": num(r[n_iq]) if n_iq is not None else None})
        return out
    jewels = costs(literal(njs, "JewelDesc"), 11, 7, 8, 9, 10, 4, 5, 6)
    chips = costs(literal(njs, "ChipDesc"), 0, 5, 6, 7, 8, 2, 3, 4)
    art = literal(njs, "ArtifactInfo")

    calc = account_calc(njs, rl, assets)

    os.makedirs(os.path.join(ROOT, "img"), exist_ok=True)
    spr = {
        "meal": sheet(assets, ["CookingM%d" % i for i in range(len(meals))], (41, 32), 10, "meals.png"),
        "spice": sheet(assets, ["CookingSpice%d" % i for i in range(30)] + ["CookingSpiceNA"], (36, 36), 8, "spices.png"),
        "ribbon": sheet(assets, ["Ribbon%d" % i for i in range(28)], (42, 41), 7, "ribbons.png"),
        "fire": sheet(assets, ["CookingF%d" % i for i in range(12)], (37, 26), 12, "fire.png"),
    }
    assets.image("assets/data/Ladle.png").save(os.path.join(ROOT, "img", "ladle.png"))
    assets.image("assets/data/CookingM1.png").crop((8, 6, 40, 32)).save(os.path.join(ROOT, "img", "favicon.png"))

    acf = os.path.join(a.game, "..", "..", "appmanifest_1476970.acf")
    build = re.search(r'"buildid"\s+"(\d+)"', open(acf).read()).group(1) if os.path.exists(acf) else None
    data = {
        "build": build, "spr": spr, "meals": meals, "spices": spices,
        "single": [int(x) for x in rl[49]], "odds": [float(x) for x in rl[50]], "arenaWaves": [int(x) for x in rl[53]],
        "kitchenCoins": [0, 82e5, 75e6, 4e8, 8e9, 5e10, 213e10, 6e13, 2e15, 1e17],  # CookingNewKitchenCoinCost
        "jewels": jewels, "chips": chips,
        "triagulon": num(art[13][3]), "causticolumn": num(art[17][3]), "calc": calc,
        "ui": {k: tr(k) for k in ["New_Recipe_Chance:_Utmost_Certainty", "New_Recipe_Chance:_Almost_Certain",
                                   "New_Recipe_Chance:_Very_Likely", "New_Recipe_Chance:_Likely", "New_Recipe_Chance:_Unlikely",
                                   "New_Recipe_Chance:_Very_Unlikely", "New_Recipe_Chance:_Nearly_Impossible",
                                   "New_Recipe_Chance:_Currently_Impossible"]},
    }
    os.makedirs(os.path.join(ROOT, "src"), exist_ok=True)
    with open(os.path.join(ROOT, "src", "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("src/data.json: %d meals, %d spices, %d jewels, %d chips, build %s" % (len(meals), len(spices), len(jewels), len(chips), build))


if __name__ == "__main__":
    main()
