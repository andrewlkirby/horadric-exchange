"""Build data/item-names.json: the game's item-name string table plus display
names for the 8 renamed Rainbow Facet jewels.

A unique's 'index' in uniqueitems.txt doubles as the key the game looks up in
item-names.json for its displayed name. The renamed facets (see
rename_rainbow_facets.py) have no entry there, so without this file the game
shows its fallback name, "An Evil Force".

D2R replaces a string file wholesale rather than merging it, so the mod has to
ship the *complete* table. Extract the vanilla one from your install first
(e.g. with CascView: data/local/lng/strings/item-names.json) and save it as
data/item-names.vanilla.json, then run:

    python build_strings.py

Re-extract and re-run after a game patch, or the mod will mask any strings
Blizzard changed.
"""
import json
import os

from cube_common import read_tsv

VANILLA_PATH = 'data/item-names.vanilla.json'
OUT_PATH = 'data/item-names.json'
FACET_KEY = 'Rainbow Facet'


def main():
    if not os.path.exists(VANILLA_PATH):
        raise SystemExit(f'{VANILLA_PATH} not found -- extract item-names.json from your '
                         f'D2R install first (see the top of this script).')
    with open(VANILLA_PATH, encoding='utf-8-sig') as f:
        entries = json.load(f)

    by_key = {e['Key']: e for e in entries}
    facet = by_key.get(FACET_KEY)
    if not facet:
        raise SystemExit(f'No "{FACET_KEY}" entry in {VANILLA_PATH} -- is this item-names.json?')
    langs = [k for k in facet if k not in ('id', 'Key')]

    # Rows without a base code are section headers ("Expansion", ...), not items.
    indices = [r['index'].strip() for r in read_tsv('data/uniqueitems.txt')
               if r.get('index', '').strip() and r.get('code', '').strip()]
    facets = [n for n in indices if n.startswith(FACET_KEY + ' (')]
    assert len(facets) == 8, facets

    next_id = max(e['id'] for e in entries) + 1
    for name in facets:
        suffix = name[len(FACET_KEY):]  # " (Hit Power - Lightning)"
        entry = by_key.get(name)
        if not entry:
            entry = {'id': next_id, 'Key': name}
            next_id += 1
            entries.append(entry)
            by_key[name] = entry
        for lang in langs:
            entry[lang] = facet[lang] + suffix

    with open(OUT_PATH, 'w', encoding='utf-8-sig', newline='\n') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f'Wrote {OUT_PATH}: {len(entries)} strings, {len(facets)} Rainbow Facet names.')

    missing = sorted(set(indices) - set(by_key))
    if missing:
        print(f'\nWARNING: {len(missing)} unique index name(s) have no string and will show '
              f'as "An Evil Force" in game: {missing}')


if __name__ == '__main__':
    main()
