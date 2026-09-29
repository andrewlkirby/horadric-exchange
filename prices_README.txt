HOW TO EDIT prices.csv
=======================

Only these columns matter for editing. Everything else (base_code, base_name,
etherealizable) is derived from game data -- don't change it.

  rune_tier      Required. 1-33, where 1=El (cheapest) ... 33=Zod (priciest).
                 The "rune" column just shows the name for that number --
                 edit rune_tier, not rune.

  rune_eth_tier  Same idea, for the ethereal-input recipe. Blank = item has
                 no ethereal recipe (not an etherealizable base, or the item
                 is innately ethereal already -- see its note). Leave blank
                 if you don't want an eth recipe for it.

  include        1 = generate recipes for this item. 0 = skip it entirely
                 (no forward recipe, no reverse/salvage recipe).

  note           Informational only, ignored by the generator. Flags things
                 like "innately ethereal" -- read it before touching that row.

Do NOT edit: item, kind, base_code, base_name, etherealizable, rune, rune_eth.
The last two are just display names re-derived from the tier numbers when you
re-run the generator -- if you edit them by hand your change gets overwritten.

When you're done editing, run:

    python apply_recipes.py

Each run rebuilds data/cubemain.txt from scratch, starting over from the
untouched original (data/cubemain.vanilla.txt) and regenerating every recipe
from the current prices.csv, then also regenerates recipes.txt to match --
so it's safe to edit and re-run as many times as you want; nothing
accumulates or goes stale.
