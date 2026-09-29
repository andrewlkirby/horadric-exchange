"""Phase A: build prices.csv -- one editable row per unique/set item.

Usage: python build_prices.py
Output: prices.csv (review/edit this, then run apply_recipes.py)
"""
import csv

from cube_common import (
    read_tsv, load_base_tables, is_etherealizable, level_to_tier, RUNES,
    MISC_BASE_NAMES, QUEST_ONLY_UNIQUE_CODES,
)

# Curated overrides: item name -> forced rune tier (1=El .. 33=Zod).
# First-pass judgment calls for items whose trade value isn't well captured by
# item level alone. Everything here is still editable in prices.csv afterward.
TIER_OVERRIDES = {
    # Rings / amulets / jewelry (cheap bases, high value)
    'The Stone of Jordan': 27,
    "Bul Katho's Wedding Band": 20,
    'Raven Frost': 18,
    "Nature's Peace": 6,
    "Mara's Kaleidoscope": 26,
    "Highlord's Wrath": 24,
    'Saracen\'s Chance': 8,
    'Atma\'s Scarab': 9,
    # Helms
    "Harlequin Crest": 29,
    "Crown of Ages": 22,
    "Griffon's Eye": 21,
    "Vampiregaze": 17,
    "Andariel's Visage": 25,
    "Veil of Steel": 20,
    # Body armor
    "Shaftstop": 12,
    "Duriel's Shell": 11,
    "Skin of the Vipermagi": 14,
    # Belts
    "Arachnid Mesh": 23,
    "String of Ears": 10,
    "Verdugo's Hearty Cord": 16,
    "Goldwrap": 4,
    # Boots
    "Wartraveler": 15,
    "Gorerider": 17,
    "Sandstorm Trek": 13,
    "Waterwalk": 9,
    # Gloves
    "Magefist": 8,
    "Frostburn": 8,
    "Chance Guards": 6,
    "Steelrend": 12,
    # Weapons
    "Windforce": 24,
    "Buriza-Do Kyanon": 19,
    "Titan's Revenge": 18,
    "Doombringer": 16,
    "The Grandfather": 25,
    "Azurewrath": 19,
    "Deaths's Web": 22,
    "The Reaper's Toll": 21,
    "Ribcracker": 10,
    "Wizardspike": 8,
    "Cutthroat1": 14,
    "The Oculus": 21,
    "Stormlash": 15,
    "Schaefer's Hammer": 15,
    "Baranar's Star": 9,
    # Shields
    "Stormshield": 20,
    "Homunculus": 12,
}


PROP_COLS = [f'prop{i}' for i in range(1, 13)]


def unique_rows(name2code):
    rows = []
    for row in read_tsv('data/uniqueitems.txt'):
        if row.get('enabled', '').strip() != '1':
            continue
        name = row.get('index', '').strip()
        code = row.get('code', '').strip()
        if not name or not code:
            continue
        if code in QUEST_ONLY_UNIQUE_CODES:
            continue  # no plain/white version of this base ever exists
        lvl_raw = row.get('lvl', '').strip()
        level = int(lvl_raw) if lvl_raw.isdigit() else 0
        # A handful of uniques (Ethereal Edge, Ghostflame, ...) are innately
        # ethereal via a 'prop = ethereal' entry -- the output is ethereal no
        # matter what quality base feeds the recipe, so a separate pricier
        # "ethereal input" recipe would be redundant and misleading.
        forced_eth = any(row.get(pc, '').strip() == 'ethereal' for pc in PROP_COLS)
        rows.append({
            'item': name, 'kind': 'unique', 'base_code': code, 'level': level,
            'forced_eth': forced_eth,
        })
    return rows


def set_rows(name2code):
    rows = []
    for row in csv.DictReader(open('set_items.csv', encoding='utf-8')):
        name = row['Item'].strip()
        base_name = row['Base Item'].strip()
        code = name2code.get(base_name)
        if not code:
            print(f'WARNING: no base code for set item "{name}" (base "{base_name}") -- skipped')
            continue
        rows.append({'item': name, 'kind': 'set', 'base_code': code, 'base_name': base_name})
    return rows


def main():
    name2code, code2info = load_base_tables()
    code2name = {c: n for n, c in name2code.items()}

    items = unique_rows(name2code)
    for r in items:
        r['base_name'] = code2name.get(r['base_code']) or MISC_BASE_NAMES.get(r['base_code'], r['base_code'])
    items += set_rows(name2code)

    out_rows = []
    for r in items:
        code = r['base_code']
        info = code2info.get(code, {})
        level = r.get('level', info.get('level', 0))
        base_tier = level_to_tier(level)
        tier = TIER_OVERRIDES.get(r['item'], base_tier)
        tier = max(1, min(len(RUNES), tier))

        etherealizable = 0
        eth_tier = ''
        note = ''
        if r['kind'] == 'unique' and is_etherealizable(code, code2info):
            if r.get('forced_eth'):
                note = 'innately ethereal (prop=ethereal) -- no separate ethereal-input recipe needed'
            else:
                etherealizable = 1
                eth_tier = min(len(RUNES), tier + 2)

        out_rows.append({
            'item': r['item'],
            'kind': r['kind'],
            'base_code': code,
            'base_name': r.get('base_name', code),
            'etherealizable': etherealizable,
            'rune_tier': tier,
            'rune': RUNES[tier - 1][1],
            'rune_eth_tier': eth_tier,
            'rune_eth': RUNES[eth_tier - 1][1] if eth_tier else '',
            'include': 1,
            'note': note,
        })

    # Sanity check: an item name shared by two entries can never be reliably
    # targeted by a named cube output, since the game can't tell them apart
    # either. This should be empty -- the one known case (Rainbow Facet's 8
    # identically-named variants) was fixed at the source; see
    # rename_rainbow_facets.py.
    name_counts = {}
    for r in out_rows:
        name_counts[(r['kind'], r['item'])] = name_counts.get((r['kind'], r['item']), 0) + 1
    ambiguous = sorted({r['item'] for r in out_rows if name_counts[(r['kind'], r['item'])] > 1})
    for r in out_rows:
        if r['item'] in ambiguous:
            r['include'] = 0
            r['note'] = 'AMBIGUOUS: shares its in-game name with another entry -- fix the name collision at the source, then re-run'

    out_rows.sort(key=lambda r: (r['kind'], r['base_code'], -r['rune_tier']))

    with open('prices.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=[
            'item', 'kind', 'base_code', 'base_name', 'etherealizable',
            'rune_tier', 'rune', 'rune_eth_tier', 'rune_eth', 'include', 'note',
        ])
        w.writeheader()
        w.writerows(out_rows)

    n_uni = sum(1 for r in out_rows if r['kind'] == 'unique')
    n_set = sum(1 for r in out_rows if r['kind'] == 'set')
    n_eth = sum(1 for r in out_rows if r['etherealizable'])
    print(f'Wrote prices.csv: {len(out_rows)} items ({n_uni} unique, {n_set} set), '
          f'{n_eth} eligible for an ethereal variant.')
    if ambiguous:
        print(f'\n{len(set(ambiguous))} item name(s) are ambiguous in the base game data '
              f'and were set to include=0 (occurs {len(ambiguous)} times): '
              f'{sorted(set(ambiguous))}')
        print('These share one in-game display name across multiple distinct unique '
              'entries, so a cube recipe cannot reliably target just one of them.')
    print('\nReview/edit prices.csv, then run: python apply_recipes.py')


if __name__ == '__main__':
    main()
