# Horadric Exchange

An offline Diablo II: Resurrected data mod. Adds Horadric Cube recipes to
craft a specific unique/set item from a base item + a rune (priced to roughly
match the item's market value), and to salvage a unique/set item back into
its base + rune.

- **826 crafting recipes** -- `base item + rune + filler item -> named unique/set item`
- **509 salvage recipes** -- `named unique/set item + filler item -> base item + rune`

See **[recipes.md](recipes.md)** for the full list (also available as plain
text in `recipes.txt`). See `prices_README.txt` if you want to re-price items
and regenerate the recipes yourself (`build_prices.py` / `apply_recipes.py`).

## What's actually in the mod

Only two files are modified from vanilla:

- `data/uniqueitems.txt` -- 8 "Rainbow Facet" jewels renamed to distinguish
  their otherwise-identical in-game names (e.g. "Rainbow Facet (Hit Power -
  Lightning)"), so each can be targeted individually.
- `data/cubemain.txt` -- the 1335 recipes above, appended after all of the
  original vanilla recipes (which are untouched).

Every other file in `data/` (armor.txt, weapons.txt, etc.) is reference data
this mod's tooling reads from -- none of it needs to be installed.

## Install

D2R has official mod support built in. You only need to copy a few files from
this repo into a mod folder and launch with a flag.

1. Find your D2R install directory, e.g.:
   - Battle.net: `C:\Program Files (x86)\Diablo II Resurrected`
   - Steam: `...\Steam\steamapps\common\Diablo II Resurrected`

2. Create this folder structure inside it (create `mods` if it doesn't exist):

   ```
   <D2R install>\mods\HoradricExchange\HoradricExchange.mpq\data\global\excel\
   ```

   The `.mpq` in the folder name is required even though it's a plain folder,
   not an archive -- that's how D2R recognizes an unpacked mod.

3. Copy these two files into that `excel` folder:
   - `data/uniqueitems.txt`
   - `data/cubemain.txt`

4. Copy `data/modinfo.json` from this repo to:

   ```
   <D2R install>\mods\HoradricExchange\HoradricExchange.mpq\modinfo.json
   ```

   Its contents are:

   ```json
   {
     "name": "HoradricExchange",
     "savepath": "HoradricExchange"
   }
   ```

   `savepath` gives the mod its own separate save folder, so mod characters
   don't mix with your normal ones.

5. Launch the game with `-mod HoradricExchange -txt` added to the launch
   command:
   - **Steam**: right-click Diablo II: Resurrected in your library -> Properties
     -> General -> Launch Options -> enter `-mod HoradricExchange -txt`
   - **Battle.net**: click the gear icon next to the Play button -> Game
     Settings -> Additional command line arguments -> enter
     `-mod HoradricExchange -txt`
   - **Shortcut**: right-click the shortcut -> Properties -> append
     `-mod HoradricExchange -txt` to the end of the Target field (outside the
     quotes around the .exe path)

6. Launch the game. A successful mod load shows in the bottom-left corner of
   the main menu as `Mod: HoradricExchange`.

You can rename `HoradricExchange` to anything -- just use the same name
consistently for the folder, `modinfo.json`, and the `-mod` flag.

## Usage

Recipes match the base item by its **item type and ethereal state**, plus a
quality restriction that depends on the item category:

- **Charms, rings, amulets, and jewels:** any quality works (low, normal,
  superior, magic, rare, crafted). These almost never drop as true white
  items -- rare, and rarer still with more Magic Find -- so the recipe
  accepts whatever quality you can actually find.
- **Everything else:** the base must be genuinely white -- low quality,
  normal, or superior. Magic, rare, crafted, or already-unique/set items of
  that base do **not** satisfy the recipe.

Bases marked "(Ethereal)" require an ethereal version of that base; all
others require a non-ethereal one.

**Be careful what you feed a recipe.** For the always-any-quality category
(charms/rings/amulets/jewels), a *different* unique or set item that happens
to share the same base type (e.g. Nagelring and The Stone of Jordan both use
a plain Ring) also satisfies the recipe -- and gets destroyed for the same
output you'd get from a worthless plain item. Double-check you're using a
common item, not something valuable, before confirming a transmute. See
[recipes.md](recipes.md) for exactly which base type each recipe needs.
