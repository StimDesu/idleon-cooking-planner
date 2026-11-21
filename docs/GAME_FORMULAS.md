# IdleOn: формулы и зависимости из кода игры

Рабочий справочник, чтобы не лезть в `N.js` каждый раз. Всё ниже взято из кода Steam-версии (билд **26365625**, ноябрь 2026). Проверено на аккаунте StimDesu: кухня 1 даёт 8.82 млн/ч при 8.83 млн/ч в игре, огонь 627 при 626, удача ×2.22 точно.

Обозначения:
- **[✓]** — перенесено в `src/template.html` и сверено с игрой.
- **[≈]** — перенесено упрощённо (что именно упрощено, написано рядом).
- **[—]** — найдено, но не перенесено.

Что где лежит:
- Список «откуда вообще может прийти бонус к X» — `docs/bonus_index.json`. Поиск: `python tools/bonus_index.py --find "<текст>"`.
- Как бонус считается — в этом файле.

---

## 0. Как читать код игры (быстрый старт)

**Где код**
- `resources/app.asar` → `distBuild/static/game/N.js` (~25 МБ, одна строка) и `lib/default.pak`.
- Если установлен Rusificator, читать `app.asar.ru-backup` (оригинал).
- Хелперы:
  - `tools/gamecode.py`: `read_game`, `literal(src, Name)`, `Assets`;
  - `tools/asar.py`, `tools/pak.py`.
- Нужен Python с Pillow; node не нужен.

**Списки данных** — `X.<Name>=function(){return [...]}`.
- Читаются через `literal(njs, "Name")`. Он сам раскрывает `"a b".split(" ")` и `"abc".split("")`.
- Нужные списки: `MealINFO`, `RANDOlist`, `AlchemyDescription`, `CardStuff`, `ArtifactInfo`, `AtomInfo`, `UpgradeVault`, `TalentDescriptions`, `StarSigns`, `SummonEnemies`, `CompanionDB`, `JewelDesc`, `ChipDesc`, `LabMainBonus`, `HolesInfo`, `CosmoUpgrades`, `HoleFountUPG`, `SigilDesc`, `GrimoireUpg`, `Research`, `MapDetails`, `TournyStuff`, `TerritoryInfo`, `ArcadeShopInfo`, `NinjaInfo`.

**Формулы** — функции вида `_customBlock_<Name>(e,t,i)`, ветка `if("Key"==e)`. Где искать:

| Функция | Что считает |
|---|---|
| `CookingR` | кулинария |
| `Summoning` / `Summoning2` | всякие `*Bonus` (VaultUpgBonus, WinBonus, RibbonBonus, CookMaster…) |
| `Holes` / `Holes2` | пещеры W5 |
| `Sailing` | артефакты |
| `Ninja` | Jade Emporium, Pristine charms |
| `Thingies` | Clam и прочее W7 |
| `TalentCalc(n)` | таланты-счётчики и сборка карт DNSM |
| `MainframeBonus` | лаборатория |
| `CauldronStats` | пузыри, флаконы |
| `StampBonusOfTypeX` | марки |
| `ArcadeBonus` | аркада |
| `GetTalentNumber` / `getbonus2` | таланты |

**Карта DNSM** (`DummyNumbersStatManager`) — кэш, который игра заполняет в `TalentCalc`:

| Ключ DNSM | Где строится | Что содержит |
|---|---|---|
| `AlchBubbles` | `TalentCalc(-2)` | бонусы пузырей по ключу |
| `AlchVials` | рядом с `AlchBubbles` | бонусы флаконов по ключу |
| `MealBonusesS` | `TalentCalc(-6)` | бонусы блюд по категориям |
| `LabMFbonuses` | `TalentCalc(-7)` | бонусы лаборатории |
| `CardBonusS` | — | карты |
| `StarSigns` | — | знаки зодиака |
| `StampBonuses_Map_Of_Val` | — | марки |
| `FamBonusQTYs` | `TalentCalc(-3)` | семейные бонусы |
| `CalcTalentMAP` | `TalentCalc(0)` | `arena`, `arenaCruc`, `[59]`, `[146]`, `"49_4"` и т.д. |

**Скрипты-помощники** лежат в scratchpad и при необходимости пишутся заново за минуту:
- `dump.py` — вырезает кусок кода по regex и заменяет `a.engine.getGameAttribute`→`G`, `c.asNumber`→`N`, `_customBlock_`→пусто;
- `ctx.py` — контекст вокруг найденного места.

grep по `N.js` с `.{0,N}` очень медленный (одна огромная строка) — искать через Python `re`.

**Атрибут `Number2Letter`** в `N.js` не задан: он лежит в `assets/data/game.mbs` внутри `default.pak`. Там 53 элемента (`_`, `a`..`z`, `A`..`Z`). При загрузке игра дописывает к нему все элементы `TournyStuff` (CJK-символы). Используется в строковых флагах сохранения: event shop `OptLacc[311]`, Jade Emporium `Ninja[102][9]`, super bits `Gaming[12]`, призма `OptLacc[384]`.
- Извлечение: `extract.py: game_mbs_letters()` + плоский `TournyStuff`.
- Проверка: `letter(i)` — символ с индексом i; бонус есть, если символ встречается в строке.

**`getLOG(x)`** = `ln(max(x,1)) / 2.30259`. Это **не точный log10**: на точных степенях 10 floor даёт на единицу меньше. Везде использовать именно его.

**`ArbitraryCode5Inputs(type, x1, x2, n)`** — универсальная формула уровня (в `template.html` это `f5`):

| type | формула |
|---|---|
| `add` | `x2≠0 ? ((x1+x2)/x2 + 0.5(n−1)) / (x1/x2) · n · x1 : x1·n` |
| `decay` | `x1·n/(n+x2)` |
| `decayMulti` | `1 + x1·n/(n+x2)` |
| `bigBase` | `x1 + x2·n` |
| `intervalAdd` | `x1 + ⌊n/x2⌋` |
| `reduce` | `x1 − x2·n` |
| `*Lower` | приращение за +1 уровень (для UI) |

---

## 1. Сохранение (raw JSON / профиль IE)

Значения часто — JSON-строка, а массивы бывают словарями `{"0":..,"1":..,"length":n}` (например `CauldronInfo`, `StampLv`). Читать через `asArr` + `at(arr, i)`, которая понимает оба вида.

> **Профиль по нику с CDN IdleOn Efficiency может отставать от игры.** Для сверки цифр брать raw JSON.

| Ключ | Что внутри |
|---|---|
| `Cooking[k]` | кухня: `[0]` статус (0 закрыта, 1 простаивает, 2 готовит, 3 рецепт), `[1]` блюдо, `[2..5]` специи, `[6]` Speed, `[7]` Fire, `[8]` Luck, `[10]` огонь |
| `Meals[0..3]` | уровни, прогресс, количество блюд, специи (−1 = специя закрыта) |
| `Ribbon[28+i]` | лента блюда i |
| `CookMaster` | `[0][i]` мастерство блюд, `[1][0]` ранг, `[1][3]` потрачено половников |
| `CauldronInfo[c][i]` | уровни пузырей (c=0..3: оранж, зелёный, фиолет, жёлтый); `[4][i]` — уровни флаконов |
| `CauldronP2W[4][1+2s]` | тир сигила s (≥3 → «purple sigil») |
| `StampLv[cat][i]` | уровень марки (cat 0=A, 1=B, 2=C); `StampLvM` — максимум |
| `ArcadeUpg[i]` | уровень улучшения аркады (101 = золото ×2, 102 = ×6) |
| `Cards0` | `{cardId: kills}` |
| `Sailing[3][i]` | тир артефакта i (0 нет, 1 найден, 2 ancient, …) |
| `Atoms[i]` | уровни атомов |
| `UpgVault[i]` | уровни хранилища (vault) |
| `Lab[0]` | позиции игроков в лаборатории |
| `Lab[1+n]` | чипы персонажа n (индексы ChipDesc) |
| `Lab[14][j]` | самоцвет j куплен (1) |
| `Lab[15][c]` | чипов c в хранилище |
| `GemItemsPurchased[i]` | `[120]` кухни Ришлен, `[11]` бонус Summoning |
| `OptLacc[i]` | `[89]` волна арены питомцев, `[193]` дней без апгрейда блюд, `[311]` event shop, `[319]` бесконечные победы Summoning, `[384]` призма-пузыри, `[453]` meritoc, `[464]` clam, `[594]` minehead, `[603]`/`[155]` принудительные уровни карт 7/6, `[628]` crucible |
| `AchieveReg[i]` | −1 = достижение получено |
| `Rift[0]` | уровень рифта (≥10 бесконечные знаки, >34 vial mastery, ≥45 карты 5★) |
| `Summon[1]` | список побеждённых врагов (имена из `SummonEnemies[0]`) |
| `companions` | `[{id, level}]` |
| `Ninja[102][9]` | купленные Jade Emporium (буквы Number2Letter) |
| `Ninja[107][t]` | pristine charm t |
| `Holes[i]` | пещеры W5: `[4]` cosmo, `[9]` ресурсы (`[9][2]` = Redstone), `[13][i]` улучшение i открыто, `[15][i]` уровень монумента, `[21]` лампа, `[31]`/`[32]` фонтан |
| `Menagerie` | `[2][i]` разблокировки, `[3][i]` уровни |
| `Grimoire[i]` | гримуар |
| `Spelunk[0][i]` | знания (lore) |
| `Territory[i]` | территории разведения: `[3]` = `"CookingSpice"+i` |
| `FarmCrop` | `{cropId: …}` (число ключей = открытые культуры) |
| `Dream[11]` | лимит скидки Best Plate |
| `WeeklyBoss["d_N"]` | −1 = облако N пройдено |
| `TaskZZ2[5][4]` | задание, влияющее на бонус Summoning |

| Ключ персонажа `_N` | Что внутри |
|---|---|
| `Lv0_N` | уровни навыков: `[10]` кулинария, `[16]` фермерство, `[18]` summoning |
| `SL_N` | `{talentId: level}` |
| `PVtStarSign_N` | `"58,12,_"` экипированные знаки |
| `KLA_N[map][0]` | осталось убить на карте; убито = `MapDetails[map][0][0] − KLA` |
| `CardEquip_N` | экипированные карты |
| `InventoryOrder_N` / `ItemQTY_N` | инвентарь |

---

## 2. Общие подсистемы (используются многими статами)

### Пузыри алхимии [✓ Diamond Chef]
- Значение: `f5(AlchemyDescription[c][i][3], [1], [2], CauldronInfo[c][i])`.
- Ключ бонуса — `AlchemyDescription[c][i][15]`, описание — `[9]`.
- **Призма**: если `OptLacc[384]` содержит `letter(c)+i+","`, значение × `max(1, PrismaBonusMult)`.
  - `PrismaBonusMult = min(5, 2 + (Arcane45 + Arcade54 + Sushi23 + Jelly36 + W6trophy + Palette28 + 0.2·purpleSigils + Exotic48 + Legend36 + 50·companion88)/100)`.
  - [≈] учтены `Arcade54`, `purpleSigils`, `companion88`.
- **Активные пузыри** (`[15]` содержит `"ACTIVE"`) работают только у персонажа, который их экипировал (`CauldronBubbles`). Пассивные работают всегда.
- **`Opassz` / `Gpassz` / `Ppassz`** умножают классовые пузыри (класс персонажа).
- **`MultiOr` / `MultiGr` / `MultiPu`** — пузыри-усилители: оранж (индексы 0,2,4,7,14), зелёный (0,6,9,12,14), фиолет (0,2,6,12,14).
- **Особые пузыри**:
  - `MealSpdz` (жёлтый #17, Diamond Chef) = значение ^ (число блюд ур. ≥11);
  - `W2/A2/M2/W4/A4/M4` × ⌊число карт/100⌋;
  - `W8` / `A9` × ⌊(GenInfo84 − 5000)/2000⌋…

### Флаконы [✓]
- Значение: `VialBonus(i) = (MF10==2 ? 2 : 1) · (1 + ((Rift>34 ? 2·maxedVials : 0) + Vault42)/100) · (1 + Meritoc20/100) · f5(AlchemyDescription[4][i])`.
- Уровень — `CauldronInfo[4][i]`. Ключ — `AlchemyDescription[4][i][11]`; значения с одинаковым ключом суммируются.
- `maxedVials` — число флаконов уровня ≥13.
- `MF10` — бонус мейнфрейма «My 1st Chemistry Set» (×2 всем флаконам).
- Для кулинарии:

| Ключ | Флаконы (индекс) |
|---|---|
| `MealCook` | 44, 55 |
| `RecCook` | 45 |
| `Kcosts` | 48 |
| `6CookSpd` | 68 (Firefly Grog) |
| `6turtle` | 74 (Turtle Tisane) |

### Марки [✓]
- `StampBonusOfTypeX(key)` = Σ по маркам, у которых `desc_line1` предмета `Stamp{A|B|C}{n}` начинается с `key`.
- Формула марки: `exalted · f5(type, x1, x2, OverLevel)`, где `desc_line1 = "key,type,x1,x2,maxLv?,…,[10]=skillIdx"`.
  - `exalted = 1 + StampDoubler/100`, если марка есть в `Compass[4]` [—].
  - `OverLevel`: если `[10]>0` (навыковая марка), уровень марки ограничивается уровнем навыка персонажа (`StampOverLevel`).
- Ключи со словом `Eff` умножаются на `max(1, Talent625)`.
- **×2**, если `MF7` («Certified Stamp Book») и категория A/B.
- **× (1 + Pristine17/100)** для A/B (25%).
- Кулинария: `MealCook` = StampB37 (индекс 36), `RecipeCook` = StampB38 (индекс 37), обе `add 2,0` → 2·уровень.

### Аркада [✓]
- `ArcadeBonus(i) = mult · f5(ArcadeShopInfo[i][3], [1], [2], ArcadeUpg[i])`.
- `mult` = 2 при уровне 101, 6 при 102; ещё ×2, если компаньон 27.

### Карты [✓]
- Уровень `CardLv(id)`:
  - kills = `Cards0[id]`;
  - уровень 1, если kills > 0;
  - для s = 0..(3 + 5★ + 6★): если `kills > req · (s+1+⌊s/3⌋+16⌊s/4⌋+100⌊s/5⌋)²`, то уровень s+2;
  - `req = CardStuff[..][2]`;
  - 5★, если `Rift[0]≥45`; 6★, если `Spelunk[0][2]≥1`;
  - `OptLacc[603]` / `[155]` поднимают уровень до 7 / 6.
- Бонус карты — `CardStuff[..][4] · уровень` (описание `[3]`).

### Артефакты [✓ 13, 17]
- `ArtifactBonus(i)` = `ArtifactInfo[i][3]` × множитель артефакта × тир.
  - Тир ≥2 удваивает, тир 3 утраивает и т.д. — проверка по `ArtifactInfo[i][5+2k]` == «…doubled/tripled…».
- Множитель артефакта:
  - 13 Triagulon: × `getLOG(Meals[2][0])` (Turkey на складе);
  - 17 Causticolumn: без множителя;
  - 1: × CalcTalentMAP[620];
  - 3: × Lv0[13];
  - 2, 10, 18, 20: × карты/500 …
- `ArtifactBonus(i, 1)` возвращает тировый множитель.

### Атомы [✓ 8]
- `AtomBonuses(i) = Atoms[i] · AtomInfo[i][4]`.
- `i=8`: `(1 + v/100)^(число блюд ур. ≥30)`.
- `i=0`: `min(90, v·OptLacc[134])`; `i=5`: `2·Σmax(0, TowerInfo[9+s]−50)`.

### Хранилище (vault) [✓]
- `VaultUpgBonus(t)`:
  - если `t` в списке {0,1,6,7,8,9,13,32,33,36,40,42,43,44,49,51,52,53,57,61,64,70,73,74,76,79,85,86,88,89}: `UpgVault[t] · UpgradeVault[t][5]` (для 0 и 60 особые формулы);
  - иначе по диапазону: `t<32` → ×(1+V32/100), `t<61` → ×(1+V61/100), `t<89` → ×(1+V89/100).
- Кулинария: `V54` (Kitchen Dream-mare) = `UpgVault[54]·6·(1+V61/100)` → множитель `(1+V54/100)`.

### Таланты [≈ без бонусных уровней]
- `GetTalentNumber(1,t)` = `f5(TalentDescriptions[t][1][2], [1][0], [1][1], SkillLevels[t] + AllTalentLV)` у **текущего** персонажа.
- `GetTalentNumber(2,t)` использует `[1][3..5]`.
- `getbonus2(1,t,-1)` — максимум по всем персонажам.
- Уровень берётся из `SL_N`; `AllTalentLV` (бонусные уровни от других систем) [—].
- Счётчики `CalcTalentMAP` (в `TalentCalc(0)`):
  - `[59]` = сумма уровней всех блюд;
  - `[146]` = min(карт с ≥1M убийств, GetTalentNumber(2,146));
  - `"49_4"` = карт с ≥100M убийств у выбранного персонажа;
  - `[209]` = карт с ≥1B.
- `TalentCalc(59) = pow(min(1.012, 1 + T59/100), CalcTalentMAP[59])`. В скорость готовки входит как **`(1 + TalentCalc(59)/100)`** — порядка ×1.01.
- `TalentEnh(146)` = `1.1^CalcTalentMAP["49_4"]`, если getbonus2(1,49) ≥ 125 (Voidwalker Enhancement Eclipse).

### Знаки зодиака [≈]
- `StarSigns` (DNSM) строится из экипированных знаков `PVtStarSign_N` текущего персонажа.
- Плюс бесконечные: первые `enabledStarSigns = Rift≥10 ? 5 + Shiny3 : 0` знаков из `StarSigns`, если открыты.
- Знак 58 «Gordonius Major»: +15% к скорости готовки.
- Чип Silkrode Nanochip (`Lab[1+n]` содержит 15) удваивает знаки [≈].

### Компаньоны [≈]
- `Companions(id)` = `CompanionDB[id][2]` (или `[11]` для улучшенного варианта).
- Список купленных — `companions` в сохранении. Когда брать `[11]`, точно не выяснено: сейчас при level ≥2.
- Полезные id:

| id | эффект |
|---|---|
| 27 | аркада ×2 |
| 87 | мастерство кулинарии |
| 88 | призма |
| 161 | голосование/meritoc |
| 162 | блюда в 5 раз дешевле и ×1.25 бонус |

### Победы в Summoning [✓]
- `b[bonusIdx] += SummonEnemies[7][idx]` для каждого побеждённого (имя в `Summon[1]`, не `rift*`); `bonusIdx = SummonEnemies[5][idx] − 1`.
- Бесконечные победы: r < `OptLacc[319]`, `SummonEnemies[9]` / `[10]` с индексом r mod 40.
- `WinBonus(t)`:
  - t ∈ {20,22,24,31}: `b[t]`;
  - t=19: 3.5·b·mult;
  - 20..33: b·mult;
  - иначе: 3.5·b·mult.
- `mult = (1+Pristine8/100)·(1+10·Gem11/100)·(1+(Art32 + min(10,Tasks[2][5][4]) + ach379 + ach373 + Win31 + EmperorBon8 + GODSHARD_SET + 50·ban_i)/100)`.
- Кулинария: `WinBonus(15)` — скорость; `WinBonus(26)` — бонус блюд.

### Лаборатория (мейнфрейм) [≈]
- `MainframeBonus(i)`:
  - i < 100 — бонус `LabMainBonus[i]`: `[5]` если активен (`GenINFO[92][i]`), иначе `[4]`;
  - i ≥ 100 — самоцвет `JewelDesc[i−100][12] · MF8`;
  - 100 (Amethyst) ×2, если активны 101 и 102 (аналогично 103, 110, 112…).
- Связи мейнфрейма в сохранении **нет**: на странице есть галочка «купленное активно».
- Полезные индексы:

| Индекс | Бонус |
|---|---|
| 7 | марки ×2 |
| 8 | Spelunker Obol: ×1.5 самоцветам |
| 10 | флаконы ×2 |
| 17 | CropSC |
| 114 | Emerald Pyramite: `1·MF8·⌊сумма уровней кухонь/25⌋` % |
| 116 | Black Diamond: 16% к бонусам блюд |

### Пещеры W5 (Holes) [✓ часть]
- **Монумент**: `MonumentROGbonuses(t,i)` с `base = HolesInfo[37][10t+i]`, `lv = Holes[15][10t+i]`:
  - если `base < 30`: `lv·base·max(1, DN)`, иначе `0.1·⌈lv/(250+lv)·10⌉·base·max(1, DN)`;
  - `DN = (1 + Mon(t,9)/100 + Cosmo(0,0)/100) · (1 + Fountain(t,13)/100)` (при `i≠9`);
  - `Cosmo(0,0) = ⌊CosmoUpgrades[0][0][0]·Holes[4][0]⌋` (25·уровень);
  - `Fountain(t,i) = round(MarbleBon·Holes[31][t][i]·HoleFountUPG[t][i][6])`, где `MarbleBon = 1` или `1.5+0.5·Holes[32][t][i]`;
  - кулинария: `(0,2)`, у StimDesu 610 × 10 × 1.25 → ×77.
- **`B_UPG(i)`** (`HolesBuildings`):
  - если `Holes[13][i] == 0` → 0;
  - 56: `1.3^⌊getLOG(Holes[9][2])⌋` (Redstone) — множитель скорости готовки;
  - 54: `1.2^⌊getLOG(Holes[9][15])⌋`;
  - 55: `10·⌊getLOG(Holes[9][11])⌋`;
  - 57: `20·⌊getLOG(Holes[9][1])⌋` …
- **Лампа**: `LampBonuses(t,i) = "25,10,8;15,40,10;20,35,12;5,1,1;2,2,2"[t][i] · Holes[21][min(11, 4+2t)] · (1+Zenith2/100)`.

### Прочее [✓ если не сказано иное]
- **Event shop**: `EventShopOwned(n)` = `OptLacc[311]` содержит `letter(n)`.
- **Jade Emporium**: `EmporiumBonus(n)` = `Ninja[102][9]` содержит `letter(n)`.
- **Super bits**: `SuperBitType(n)` = `Gaming[12]` содержит `letter(n)`.
- **Clam**: `ClamWorkBonus(n)` = `OptLacc[464] > n`.
- **Pristine charm**: `PristineBon(t)` = `Ninja[107][t]==1 ? NjEQ["NjTrP"+t][3] : 0` (8 → 30, 17 → 25).
- **Arena**: число порогов `RANDOlist[53]` ≤ `OptLacc[89]`; `PetArenaBonus(i) = arena > i`.
- **Crucible**: только при `Menagerie[2][8] ≥ 1`, пороги `RANDOlist[115]` ≤ `OptLacc[628]`.
- **Менажерея**: `BoostQTY(t) = Research[58][t]·Menagerie[3][t]`; `UnlockOwned(t) = Menagerie[2][t] ≥ 1`.
- **Гримуар**: `GrimoireUpgBonus(t) = Grimoire[t]·GrimoireUpg[t][5]` (× бонус 36 для большинства).
- **Сигил t**: тир по `CauldronP2W[4][1+2t]` (<−0.1 → 0, <0.5 → `[3]`, <1.5 → `[4]`, затем `[8]`, `[10]`, `[12]`) × `(1+Art16)·(1+Meritoc21/100)`.
- **Облако N**: `WeeklyBoss["d_N"] == −1`.
- **Голосование** `VotingBonusz(t)` [—]: работает только для активной категории (`GenINFO[36]` в клиенте). В `servervars` есть `voteCategories` / `votePercent`, но какая категория победила, однозначно не определить.

---

## 3. Кулинария

### Скорость готовки — `CookingR("CookingSPEED", k)`
Произведение множителей. Почти все из них есть на странице в «Откуда берётся скорость».
1. `10` — база.
2. `(1 + TalentCalc(59)/100)` [✓]
3. `max(1, CropSCbonus(3))` = `Emporium26 ? 1.1^(число культур)·CropSCbonMulti : 0` [≈ без CropSCbonMulti]
4. `max(1, TalentEnh(146))` [✓]
5. `(1 + EventShop53)` [✓]
6. `(1 + 9·Clam10)` [✓]
7. `(1 + Richelin)` — ×3, если `GemItemsPurchased[120] > k` [✓]
8. `(1 + Voting13/100)` [—]
9. `(1 + Vault54/100)` [✓]
10. `(1 + MealBonus(zMealFarm)·⌈(Farming+1)/50⌉/100)` — фермерство текущего персонажа [✓]
11. `max(1, MealSpdz)` [✓]
12. `max(1, Atom8)` [✓]
13. `(1 + MSA_Bonus(1)/100)` = `13·⌊waves/10⌋` при SuperBit13 [—]
14. `(1 + Speed/10)` [✓]
15. `(1 + Artifact13/100)` [✓]
16. `(9·Cruc5 + 20·Cruc12 + 1)` [✓]
17. `(1 + Minehead7/100)` [—]
18. `(1 + Arcade28/100)` [✓]
19. `(1 + vial 6turtle/100)` [✓]
20. `(1 + vial MealCook/100)` [✓]
21. `(1 + (Stamp MealCook + max(0, MF114))/100)` [✓]
22. `(1 + MealBonus(Mcook)/100)` [✓]
23. `(1 + StarSign58/100)` [≈]
24. `(1 + WinBonus15/100)` [✓]
25. `(1 + Menagerie BoostQTY4/100)` [✓]
26. `(1 + Monument(0,2)/100)` [✓]
27. `max(1, B_UPG56)` [✓]
28. `(1 + 5·CardLv(w6c1)/100)` [✓]
29. `(1 + Lamp(0,0)/100)` [✓]
30. `(1 + vial 6CookSpd/100)` [✓]
31. `max(1, MF100)` — Amethyst ×1.5 или ×3 при всех фиолетовых [≈]
32. `(1 + min(6·CardLv(Boss4A) + 20·ach225 + 10·ach224, 100)/100)` [✓]
33. `(1 + MealBonus(KitchenEff)·⌊(Speed+Fire+Luck)/10⌋/100)` — Cabbage [✓]

**Огонь** — `CookingFIRE`:
- `5 · (1+Richelin1) · Voting13 · MealSpdz · Atom8 · MSA1 · (1+Fire/10) · (1+vial RecCook/100) · (1+Stamp RecipeCook/100) · (1+Rcook/100) · (1+min(6·Boss4A, 50)/100) · KitchenEff`.
- Сверено с игрой: 627 против 626.

**Удача** — `CookingLUCK` = `1 + (5·Luck)^0.85/100` [✓ точно].

### Блюда
- **Бонус блюда**: `MealBonusesS[cat] += BonusMultiCook(i) · CookingMealBonusMultioo · RibbonBonus(Ribbon[28+i]) · Meals[0][i] · MealINFO[i][2]`.
  - Для категории `PxLine`: просто `уровень · база`.
  - `BonusMultiCook(i) = 1 + M/(M+5)`, где M = `CookMaster[0][i]`.
  - `CookingMealBonusMultioo = (1 + (MF116 + Shiny20)/100)·(1 + WinBonus26/100)·(1 + 25·Comp162/100)` [≈ без Shiny].
  - `RibbonBonus(t) = 1 + (⌊5t + ⌊t/2⌋(4+6.5⌊t/5⌋)⌋ + ⌊t/4⌋·EMPEROR_SET/4 + ⌊t/10⌋·Cloud73 + ⌊t/20⌋·Jelly60)/100` [≈ без сета/облака/jelly].
- **Цена уровня** `CookingMenuMealCosts(L)` = `max(.001, 1/max(1, 5·Comp162)) · 10^(22⌊(L+1000)/1111⌋) · 1/min(5, max(1, 1+10·ach233/100)) · max(.001, max(.58, .8−.22·Cloud33)^min(OptLacc[193], Dream[11])) · (10+L+L²) · (1.2+.05L)^L · (1+.4⌊(L+1000)/1111⌋)^L` [✓].
- **Макс. уровень** `CookingMealMaxLVlol = round(30 + Artifact17 + 10·Emp20 + 10·Emp21 + 30·Lore5 + min(20, Grimoire26) + 10·Menagerie20)` [✓].
- **Требование готовки**: `MealINFO[i][1]`. Готовка: `Meals[1][i] += SPEED/3600·dt`; при достижении req → `Meals[2][i] += …`.

### Кухни
- **Цена новой кухни**: 8.2M, 75M, 4e8, 8e9, 5e10, 2.13e12, 6e13, 2e15, 1e17 монет.
- **Специя улучшения**: `⌊2k + тип⌋` (0 Speed, 1 Fire, 2 Luck).
- **Количество специи**: `1 + 1/((1+(Kcosts+Sigil18)/100)·(1+30·Fractal2/100)·(1+KitchC/100)·(1+Richelin40/100)·(1+0.5·Arena7)) · (L+1+⌊max(0,L−10)/2⌋+max(0,L−30)^1.2) · 1.02^max(0,L−60)` [✓ без Fractal].
- **Специи приходят** с территорий: `Meals[3][s] += Territory[s][4]·(1+.5·SuperBit14)·(1+SuperBit17)` за сбор.

### Новые рецепты [✓]
- **Список рецептов** (`PossibleRecipes2`):
  - каждая специя s добавляет `RANDOlist[49][s]`;
  - сумма номеров специй S → `S<71 ? min(55,S) : S<87 ? min(65, S−14) : S−22`;
  - при S > 0.5 добавляются `min(число специй, 3)` соседних блюд (без дублей и без блюд из `RANDOlist[49]`);
  - список сортируется.
- **Огонь**: `FireREQ = 2·req(min(66, последнее))·25^max(0, последнее−66)`. Уровень огня L достигнут при `fire ≥ FireREQ·3^(L−1)`.
- **Шанс** j-й позиции: `RANDOlist[50][j]` × (для неоткрытого блюда) `Luck·1.5^L`. Бросок идёт от последней позиции к первой, до первого попадания.
- **Вывод**: забирать результат на огне 1 оптимально (×3 время против ×1.5 шанса).

### Мастерство кулинарии (W7, Rift 61) [—]
`CookMaster`, `ExpReqCook = 100·2.5^R·5^max(0,R−40)`, `ExpRateCook`, `BonusAmountcook`, `RankREQcook = [0,1,5,10,25,100,150,250,500]` — см. ветки `Summoning2` около `"ExpRateCook"`.

---

## 4. Карта зависимостей «что на что влияет» (кулинария)

| Источник (где качать) | Влияет на | Формула / сила |
|---|---|---|
| Speed кухни (специи) | скорость этой кухни | ×(1+L/10) |
| Fire кухни | огонь этой кухни | ×(1+L/10) |
| Luck кухни | шанс нового рецепта | 1+(5L)^0.85/100 |
| Все уровни кухни (Speed+Fire+Luck) | скорость и огонь через Cabbage; MF114 | ⌊Σ/10⌋·Cabbage%; ⌊Σ/25⌋% |
| Блюда Egg, Corndog, Soda, Double Cherry (`Mcook`) | скорость | +% аддитивно |
| Burned Mello (`zMealFarm`) | скорость | ×⌈(Farming+1)/50⌉ |
| Pie, Canopy (`Rcook`) | огонь | +% |
| Dango, Durian, Ratatouey (`KitchC`) | цена улучшений кухни | делитель |
| Турки на складе | скорость (Triagulon) | 15·тир·getLOG(турки) % |
| Число блюд ур. ≥11 | скорость и огонь (Diamond Chef) | бонус^N |
| Число блюд ур. ≥30 | скорость и огонь (Fluoride) | (1+атом%)^N |
| Сумма уровней блюд | скорость (талант 59) | ≈×1.01 |
| Redstone в пещерах | скорость (B_UPG 56) | 1.3^⌊getLOG⌋ |
| Монумент Bravery (0,2) | скорость | +lv·10·DN % |
| Хранилище 54 (+61, 89) | скорость | +6%/ур ×… |
| Аркада 28 | скорость | decay(40,100) |
| Марка B37 / B38 | скорость / огонь | 2·ур (×2 MF7) |
| Карта Boss4A | скорость (до +100% вместе с достижениями) и огонь (до +50%) | 6%/ур |
| Карта w6c1 | скорость | 5%/ур |
| Достижения 224 (5×Cabbage) и 225 (8×Pretzel) | скорость | +10 / +20 % |
| Ришлен (gem shop 120) | скорость ×3, огонь ×2, специи −40% | — |
| Black Diamond (самоцвет 16) | бонус всех блюд | +16% |
| Компаньон 162 | цена ×1/5, бонус ×1.25 | — |
| Causticolumn, Emporium 20/21, Lore 5, Grimoire 26, Menagerie 20 | макс. уровень блюд | +10/+10/+10/+30/≤20/+10 |

---

## 5. Как обновлять после патча игры

1. `python tools/extract.py` и `python build.py`.
   - Если извлечение упало: изменилась структура списка, смотреть traceback.
   - Ключевые индексы стоят в `account_calc()`: `AlchemyDescription[3][17]`, флаконы по ключу `[11]`, марки по ключу `desc_line1`, `ArcadeShopInfo[28/54]`, `UpgradeVault[42/54/61/89]`, `CardStuff` (Boss4A / w6c1), `CompanionDB[27/88/162]`, `HolesInfo[37]`, `CosmoUpgrades[0][0]`, `HoleFountUPG[0][13]`, `HoleozDT`.
2. `python tools/bonus_index.py` и diff `docs/bonus_index.json`. Новые строки с «Cook»/«Meal» означают новые источники; найти, где их ключ читается: `dump.py` по ключу.
3. Перепроверить формулу `CookingSPEED`: вырезать ветку (`dump.py CookingR`) и сравнить список множителей с разделом 3. Новый множитель — добавить в `acctCalc().spd` или в `kSpeedParts`.
4. **Регрессия**: загрузить свежий raw JSON StimDesu и сравнить кухню 1 со скриншотом «Kitchen Stats» в игре. На 21.11.2026 было 8.83M/h, 626/h, ×2.22.

---

## 6. Задел под «советчик по характеристике»

Цель: ввести характеристику (удача, скорость рыбалки, эффективность ловли насекомых, ширина линии в лаборатории…) и получить все места, где её можно поднять.

1. **Где искать источники** — `docs/bonus_index.json`: 7003 текста бонусов в 81 списке плюс описания предметов. Поиск по слову (`--find "line width"`) сразу даёт:
   - пузыри и флаконы с ключом;
   - марки (`item:Stamp*`);
   - карты, знаки, таланты, блюда, артефакты, атомы, самоцветы, чипы;
   - хранилище, аркаду, гримуар, компаньонов, задания и т.д.
2. **Как строка становится числом** — у каждого типа своя функция уровня (раздел 2): пузырь/флакон/талант/аркада через `f5`, марка через `f5` + overlevel, карта — уровень × `[4]`, артефакт — × тир, хранилище — × `[5]`, блюдо — `база·ур·…`.
3. **Как значение входит в характеристику** — найти итоговую функцию характеристики (как `CookingSPEED`) и выписать её множители. Подсказки:
   - ключи DNSM-карт (`AlchBubbles.h.KEY`, `AlchVials.h.KEY`, `StampBonusOfTypeX("KEY")`, `MealBonus("KEY")`, `CardBonusREAL`, `StarSigns.h.KEY`, `EtcBonuses("N")`) совпадают с ключами из индекса;
   - поиск `"KEY"` в `N.js` находит формулу, куда ключ входит.
4. **Предлагаемая структура данных советчика**: `stat → [{source_type, list, index, key, text, level_formula, current_level(save path), how_to_raise}]`. Индекс уже даёт первые 5 полей; формулы уровня — раздел 2; пути в сохранении — раздел 1.

---

## 7. Характеристики персонажа и шанс добычи — `TotalStats(e)` (порт: idleon-stat-finder)

Порт живёт в `D:\git\idleon-stat-finder\src\template.html`: `model()` (карты бонусов игры), `statFormula()`, `dropFormula()`.

**STR/AGI/WIS/LUK** [≈]:
- снаряжение + инструменты (`EquipmentOrder[0]` — 16 слотов, `[1]` — 8), item stat + `EquipmentMap` stat;
  × `(1 + (Tal(96|276|456|21) + Stamp("Pct<STAT>"))/100)`;
- оболы (`ScrollCircleINFO[43]`) × `(1 + (Tal(111|291|486|36) + 40·SuperBit2)/100)`;
- итог: `floor(Bubble("Total<STAT>") + Tal652 + Comp8 + (1 + %/100) · плоская_часть)`;
- `%` = Etc(57|25|58|17) + Etc46 + AllStatPCT + Pristine(4|1|10|5) + StarSign pct<STAT> (+ Tal 143/368/533 и пузыри W8/A9/M9 у STR/AGI/WIS);
- плоская часть: Tal(10..13), getbonus2(51..54), Stamp Base<STAT>/BaseAllStat, Etc(51..54), Fam(14|38|62|4), знаки, Card(9|7|5|2),
  Sigil(0..3), пузырь W4/A4/M4 (× ⌊карт/100⌋), Arcade(19..22), AllStat (почта 20a + блюда Stat + гильдия 1),
  почта (21b/22b/23b/15c/LUK), сияющие питомцы, сова, мерцание, TalentCalc(620) — [—].
- **Галереи W7** (трофеи, именные таблички, премиум-шапки, плащи) добавляют к статам и Etc — [—].

**Шанс добычи** `"Drop_Rarity"` [≈]:
- `LUKdr = LUK<1000 ? ((LUK+1)^0.37 − 1)/40 : (LUK−1000)/(LUK+2500)·0.5 + 0.297`;
- `DR = 1.4·LUKdr + (Σ слагаемых)/100 + 1`, при DR<5 + чип "dr" (не выше 5); +0.3 при `OptLacc[232]≥1`;
- далее множители: Card(101), Fam32, Comp168·0.3, Comp132, Etc99, Etc91, облако 69, Pristine3, флакон `7drMulto`, Comp26/160/50,
  тессеракт, статуя RG, менажерея, суши/желе, minehead, том, наборы, верстак [—].
- Σ: Tal279, Tal24, Tal655·OptLacc[189], Etc2+Etc102, пузырь DropRate, Card(10), CardSet 5/6, знак Drop, Guild10, Shrine4, Prayer(7),
  Sigil11, Arcade27, Comp3/50/132, Stamp DropRate, 5·Dream[10], карты mini5a/caveC/caveD/anni4Event1/luckEvent1, Ach377/381,
  Grim44, Vault18, Comp22/158/111; почта, shiny, WinBonus9, Tome2, Grid173, золотая еда, сова, Lank, голосование и др. [—].

**Вспомогательные** (все в `model()`):
- `AllTalentLV` (бонусные уровни талантов) = Tal149+374+539 + Ach291 + Fam68 + Comp1 + Dream[12] + 5·⌊(97+OptLacc232)/100⌋ + Grim39 + min(5, Arcane57) + супербит 47; [—] божество, сеты, super talents (Spelunk[20+n]).
- `StampBonusOfTypeX`: подстрока ключа в `desc_line1`; навыковые марки — `StampOverLevel` (≥3: `3+(st−3)·(lv/(st−3))^0.75`); ×2 MF7 для A/B; ×Pristine17 для A/B; ×Vault16 для BaseDmg/HP/Acc/Def; `Eff` × Tal625.
- `CardBonusS`: надетые `CardEquip` (10 слотов), чип card1/card2 удваивает слот 1/8, ключ = текст бонуса карты; `CardBonusREAL(n)` через `CustomMaps.IDforCardBonus`.
- `EtcBonuses(n)`: UQ-тексты надетого снаряжения/оболов через `IDforETCbonus`; чипы pend/key1/troph удваивают слоты 4/10/11.
- `StarSigns`: таблица знак → [ключ, число] вынимается regex-ом из `v.StarSigns` (61 из 94 знаков); бесконечные знаки при Rift≥10; чип "star" удваивает.
- `FamBonusQTYs[2·класс+I]`: максимум по персонажам по линии класса (`ReturnClasses`), уровень − `ClassAccountBonus[c][1]`.

**Опыт класса** `ExpMulti(0)` [≈] (порт: `expFormula()`):
- `LUKx = LUK<1000 ? ((LUK+1)^0.37−1)/30 : (LUK−1000)/(LUK+2500)·0.8 + 0.3963`;
- итог = верстак · (1+L3/100) · L5 · (1+Etc78/100) · (LUKx·(1+Tal35/100)/1.8 + Σ/100 + 1);
- Σ: Etc4, почта monsterExp, еда ClassEXP, знак MainXP, флаконы MonsterEXP, пузырь expACTIVE, Card(44), L2, Statue10, Tal632, Shrine5,
  SaltLick3, Prayer(0)+Prayer(2)−Prayer(9, проклятие), флурбо 2, Ach57+20·Ach357+3·Ach61+2·Ach124+5·Ach188+25·Ach286, Arcade12, Sigil8,
  shiny1, MSA4, getbonus2(55), L6;
- L2: самый низкий по уровню персонаж (строго ниже всех) получает 3·`TaskZZ2[0][2]` + Vault12 (и L3=50 при супербите 19); <50 ур. CardSet0;
  <120 ур. блюда Clexp; `WeeklyBoss.c` (≤150); +150/100/50 до 10/30/50 ур.; божество; CardSet5;
- L4 = Compass51 + B_UPG47 + WinBonus23 + Grim24 + Vault3 + Vault35·getLOG(OptLacc[345]) + B_UPG83;
- L6 = 2·CardLv(springEvent1) + Comp3+50+47+111+128 + OptLacc[421] + Stamp classxp + L4 + (сова, голосование, монумент, сеты, экзотика, друзья, мерцание, minehead) [—];
- L5 (множители): (1+9·Comp37)(1+Comp33)(1+4·Comp160)(1+Comp32)(1+0.4·Comp168)(1+Comp34)(1+Comp145)(1+min(.5,Comp128))(1+0.1·SuperBit63)·…,
  Etc84, Card(100), Arcade60, флакон `7classexp`, CardSet12, облако 70, 1.03^len(Spelunk[6]) при супербите 24; остальное [—].
- `StatueBonusGiven(t)` = lv·StatueInfo[t][3] × таланты группы (0,2,8,7: 112/127; 1,11,9,14: 292/307; 10,6,12,13: 487/472; 3,5,17: 37) × onyx (StuG≥2: 1+(100+Art30)/100) × zenith (≥3).
