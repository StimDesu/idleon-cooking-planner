# IdleOn Cooking Planner

A Legends of Idleon cooking (World 4) planner. Load your save and the page shows your kitchens and spices, which meal to level next, which spices find a new recipe fastest, and what to spend or keep your meals for.

The page picks English or Russian from your browser language; the EN/RU switch in the corner overrides it. Things you haven't unlocked yet (meals, kitchens, spices, jewels) stay hidden until you tick “Show locked things”.

## What it does

- **Kitchens and spices.** All owned kitchens with what they cook or search, Speed/Fire/Luck levels, the spice and amount the next upgrade costs (and whether you have it), cooking speed, fire speed and luck. Richelin kitchens are marked.
- **What to level next.** A greedy plan for a goal: cooking speed, or any meal bonus (damage, breeding odds, lab EXP…). Each step takes the level-up with the best gain per hour of cooking, spends the meals you already own first, and shows the cooking time and the running total. Speed meals can be mixed in when they pay off.
- **Meals.** Every found meal: level, meals owned, next level cost, how long all kitchens need to cook the rest, the bonus now and per level, ribbon and mastery, how many to keep and how many are free to spend.
- **New recipes.** For every undiscovered meal: the best spice combo among the spices you own, the kitchen, the chance per try, the time per try and the expected time. Also the best combos for “any new meal” and the state of kitchens searching right now (claim now or wait).
- **Spending and stockpiling.** Lab jewels and chips that cost meals and spices (bought, ready or missing), the Triagulon Turkey stockpile, the kitchen achievements, idle kitchens, free meals.

## Accuracy

Everything is computed from the save, no numbers from the game screen are needed. The “Where the speed comes from” card shows every multiplier of the kitchen speed and fire speed (kitchen upgrades, meals, Diamond Chef bubble, vials, stamps, arcade, vault, cards, star sign, artifacts, atoms, Summoning, Menagerie, talents…), the meal max level, the meal bonus multiplier and the costs, each ported from the game code.

Not counted yet: the current vote (it lives on the server), W5 caverns (Monument, Lamp, Bolaia), Exalted stamps, bonus talent levels, Emperor/Godshard sets, shiny pets, Minehead. The save doesn't say which Lab Mainframe bonuses are connected, so bought jewels and the Mainframe bonuses count as active while the Lab box is ticked. Character-bound bonuses (star sign, Farming level) use the character picked in that card; by default the one with the fastest kitchen.

## How to get your save

**By username.** Publish your profile on [idleonefficiency.com](https://www.idleonefficiency.com), then type your IdleOn username and press “Load by username”. A link with the username after `#` opens that profile directly.

**By raw data.** Paste or open a raw save export. Both a flat export and `{ "data": {...} }` work. The page reads `Cooking`, `Meals`, `Ribbon`, `CookMaster`, `Lab`, `Sailing`, `GemItemsPurchased`, `OptLacc`, `AchieveReg`, `Dream`, `Lv0_N` and the storage for ladles. A pasted save stays in your browser.

## Data from the game

Every number, list and icon comes from the Steam game files: `tools/extract.py` reads `N.js` and `default.pak` from `resources/app.asar` (or `app.asar.ru-backup` if the Russian translation is installed). The formulas are ported from the game code. [COOKING.md](COOKING.md) is a short reference (in Russian) of the mechanics, the save keys and tips from the guides.

After a game update:

```
python tools/extract.py --game "D:\Games\SteamLibrary\steamapps\common\Legends of Idleon"
python build.py
```

`index.html` is generated from `src/template.html` and `src/data.json`; edit the template, not the page. Python 3 with Pillow is needed for the extraction, nothing for the page itself.

Legends of Idleon and its art belong to Lavaflame2. This is an unofficial fan tool.
