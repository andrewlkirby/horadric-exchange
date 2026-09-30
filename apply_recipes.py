"""Phase B: read prices.csv and append the resulting cube recipes to
data/cubemain.txt.

Every forward recipe is (base item + rune + filler item) -> named item. When
two items would otherwise collide -- same base code, same ethereal state, same
rune tier -- each gets a distinct filler item instead of bumping either one's
rune price, so the priced-in market value from prices.csv is never silently
altered.

Every item also gets a reverse ("salvage") recipe: named item + Scroll of
Identify -> base item + rune (via cubemain.txt's 'output b' slot, which
produces a second item alongside the first). The item's exact name is already
globally unique, so no filler-pool disambiguation is needed on this side --
one fixed filler is enough. The reverse recipe always refunds the *normal*
recipe's ingredients, even for items that also have a pricier ethereal-input
variant -- salvaging doesn't try to detect whether the specific item instance
in the cube happened to be crafted via that route.

Usage: python apply_recipes.py
"""
import csv
import os
import shutil

from cube_common import (
    CUBEMAIN_HEADER, FILLER_POOL, FILLER_NAMES, NUM_TIERS, QUALITY_EXEMPT_CODES, RUNES,
    WHITE_QUALITY_TIERS, blank_row, resolve_tier,
)

CUBEMAIN_PATH = 'data/cubemain.txt'
VANILLA_PATH = 'data/cubemain.vanilla.txt'  # untouched original -- never overwritten after creation
BACKUP_PATH = 'data/cubemain.backup.txt'    # convenience copy of the last build, safe to inspect/diff
REVERSE_FILLER = FILLER_POOL[0]  # isc -- item name alone already disambiguates


def load_existing_signatures():
    """(numinputs, sorted tuple of input strings) for every recipe already in the file."""
    sigs = set()
    with open(CUBEMAIN_PATH, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            n = row.get('numinputs', '').strip()
            if not n.isdigit():
                continue
            inputs = tuple(sorted(
                row.get(f'input {i}', '').strip() for i in range(1, 8)
            ))
            sigs.add((n, inputs))
    return sigs


def assign_fillers(items):
    """items: list of item names sharing an identical (base, eth, tier) key.
    Returns {item: filler_code}, all distinct. Falls back to reusing the pool
    (which would create a real collision) only if the group outgrows it --
    that's reported as an error, not silently swallowed.
    """
    ordered = sorted(items)
    if len(ordered) > len(FILLER_POOL):
        raise SystemExit(
            f'Collision group {ordered!r} has {len(ordered)} members but only '
            f'{len(FILLER_POOL)} filler items are available -- add more to FILLER_POOL.'
        )
    return {item: FILLER_POOL[i] for i, item in enumerate(ordered)}


def build_row(description, base_code, quality, base_qualifier, rune_code, filler_code,
              output_name, eth_output=False):
    row = blank_row()
    row['description'] = description
    row['numinputs'] = '3'
    parts = [base_code] + [p for p in (quality, base_qualifier) if p]
    row['input 1'] = ','.join(parts)
    row['input 2'] = rune_code
    row['input 3'] = filler_code
    row['output'] = output_name
    # 'lvl' is an absolute item level; 'ilvl' is a % of the input item's level,
    # which leaves low-level bases below the unique's qlvl and yields a rare.
    row['lvl'] = '99'
    if eth_output:
        row['mod 1'] = 'ethereal'
        row['mod 1 min'] = '1'
        row['mod 1 max'] = '1'
    return row


def build_reverse_row(description, item_name, base_code, rune_code):
    row = blank_row()
    row['description'] = description
    row['numinputs'] = '2'
    row['input 1'] = item_name
    row['input 2'] = REVERSE_FILLER
    row['output'] = base_code
    row['output b'] = rune_code
    return row


def normalize_tiers(rows):
    """The 'rune'/'rune_eth' NAME columns are what a human actually edits;
    the numeric 'rune_tier'/'rune_eth_tier' columns are what the rest of the
    pipeline reads. Treat the name as authoritative when it parses, resync
    the number to match, and report every correction so a stale edit never
    silently fails to take effect.
    """
    corrections = []
    for r in rows:
        tier = resolve_tier(r.get('rune'), r.get('rune_tier'))
        if tier is None:
            raise SystemExit(f"prices.csv: item {r['item']!r} has no valid rune or rune_tier")
        tier = max(1, min(NUM_TIERS, tier))
        if r.get('rune_tier', '').strip() != str(tier) or r.get('rune', '').strip() != RUNES[tier - 1][1]:
            corrections.append((r['item'], 'rune', r.get('rune_tier'), r.get('rune'), tier, RUNES[tier - 1][1]))
        r['rune_tier'], r['rune'] = str(tier), RUNES[tier - 1][1]

        if r.get('etherealizable', '0').strip() != '1':
            # Not eligible for an ethereal recipe -- ignore/clear anything here
            # (e.g. spreadsheet fill-down artifacts like a stray '"' ditto mark).
            if r.get('rune_eth') or r.get('rune_eth_tier'):
                corrections.append((r['item'], 'rune_eth (cleared, not etherealizable)',
                                     r.get('rune_eth_tier'), r.get('rune_eth'), '', ''))
            r['rune_eth_tier'], r['rune_eth'] = '', ''
            continue

        eth_name = (r.get('rune_eth') or '').strip()
        eth_tier_raw = (r.get('rune_eth_tier') or '').strip()
        if eth_name or eth_tier_raw:
            eth_tier = resolve_tier(eth_name, eth_tier_raw)
            if eth_tier is None:
                raise SystemExit(f"prices.csv: item {r['item']!r} has an invalid rune_eth/rune_eth_tier")
            eth_tier = max(1, min(NUM_TIERS, eth_tier))
            if eth_tier_raw != str(eth_tier) or eth_name != RUNES[eth_tier - 1][1]:
                corrections.append((r['item'], 'rune_eth', eth_tier_raw, eth_name, eth_tier, RUNES[eth_tier - 1][1]))
            r['rune_eth_tier'], r['rune_eth'] = str(eth_tier), RUNES[eth_tier - 1][1]
    return corrections


def main():
    # Always regenerate from the untouched original -- never append onto a
    # file that may already contain a previous (possibly stale) generation.
    if not os.path.exists(VANILLA_PATH):
        shutil.copyfile(CUBEMAIN_PATH, VANILLA_PATH)
        print(f'First run: saved untouched original as {VANILLA_PATH}')
    shutil.copyfile(VANILLA_PATH, CUBEMAIN_PATH)

    all_rows = list(csv.DictReader(open('prices.csv', encoding='utf-8')))
    corrections = normalize_tiers(all_rows)
    if corrections:
        with open('prices.csv', 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=all_rows[0].keys())
            w.writeheader()
            w.writerows(all_rows)
        print(f'Corrected {len(corrections)} stale rune_tier/rune_eth_tier number(s) in prices.csv '
              f'to match the rune NAME you edited:')
        for item, field, old_tier, old_name, new_tier, new_name in corrections:
            print(f'  {item} [{field}]: tier {old_tier!r} ({old_name!r} stale) -> tier {new_tier} ({new_name})')
        print()

    rows = [r for r in all_rows if r.get('include', '1').strip() == '1']

    # --- normal recipes: resolve (base_code, tier) collisions via filler ---
    normal_groups = {}
    for r in rows:
        key = (r['base_code'], int(r['rune_tier']))
        normal_groups.setdefault(key, []).append(r['item'])

    normal_filler = {}
    for key, items in normal_groups.items():
        normal_filler.update(assign_fillers(items))

    # --- ethereal recipes: resolve (base_code, tier) collisions via filler ---
    eth_rows = [r for r in rows if r.get('etherealizable', '0').strip() == '1'
                and r.get('rune_eth_tier', '').strip()]
    eth_groups = {}
    for r in eth_rows:
        key = (r['base_code'], int(r['rune_eth_tier']))
        eth_groups.setdefault(key, []).append(r['item'])

    eth_filler = {}
    for key, items in eth_groups.items():
        eth_filler.update(assign_fillers(items))

    # --- build rows ---
    existing_sigs = load_existing_signatures()
    new_rows = []
    seen_sigs = set()
    skipped = []

    def try_add(row):
        inputs = tuple(sorted(row.get(f'input {i}', '').strip() for i in range(1, 8)))
        sig = (row['numinputs'], inputs)
        if sig in existing_sigs or sig in seen_sigs:
            skipped.append(row['description'])
            return
        seen_sigs.add(sig)
        new_rows.append(row)

    QUALITY_LABEL = {'nor': 'Normal', 'hiq': 'Superior', 'low': 'Low Quality'}

    def qualities_for(base_code):
        # Charms/rings/amulets/jewels basically never drop white, so any
        # quality is accepted. Everything else is restricted to a genuinely
        # white base -- emitted as one recipe per white-quality tier, since
        # cubemain.txt qualifiers AND together and can't express "any of".
        return [None] if base_code in QUALITY_EXEMPT_CODES else WHITE_QUALITY_TIERS

    for r in rows:
        item, base_code, base_name = r['item'], r['base_code'], r['base_name']

        if item in eth_filler:
            rune_code, rune_name = RUNES[int(r['rune_eth_tier']) - 1]
            filler = eth_filler[item]
            for quality in qualities_for(base_code):
                tag = f'Ethereal, {QUALITY_LABEL[quality]}' if quality else 'Ethereal'
                try_add(build_row(
                    f'{base_name} ({tag}) + {rune_name} Rune + '
                    f'{FILLER_NAMES[filler]} -> {item} (eth)',
                    base_code, quality, 'eth', rune_code, filler, item, eth_output=True,
                ))

        rune_code, rune_name = RUNES[int(r['rune_tier']) - 1]
        filler = normal_filler[item]
        for quality in qualities_for(base_code):
            tag = f' ({QUALITY_LABEL[quality]})' if quality else ''
            try_add(build_row(
                f'{base_name}{tag} + {rune_name} Rune + {FILLER_NAMES[filler]} -> {item}',
                base_code, quality, 'noe', rune_code, filler, item, eth_output=False,
            ))

        try_add(build_reverse_row(
            f'{item} + {FILLER_NAMES[REVERSE_FILLER]} -> {base_name} + {rune_name} Rune',
            item, base_code, rune_code,
        ))

    # --- write output ---
    with open(CUBEMAIN_PATH, 'a', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CUBEMAIN_HEADER, delimiter='\t')
        for row in new_rows:
            w.writerow(row)
    shutil.copyfile(CUBEMAIN_PATH, BACKUP_PATH)

    multi = {k: v for k, v in normal_groups.items() if len(v) > 1}
    multi.update({k: v for k, v in eth_groups.items() if len(v) > 1})

    n_reverse = sum(1 for row in new_rows if row['numinputs'] == '2' and row['output b'])
    print(f'Rebuilt {CUBEMAIN_PATH} from {VANILLA_PATH} '
          f'({len(new_rows)} recipes: {len(new_rows) - n_reverse} forward, {n_reverse} reverse/salvage)')
    print(f'Copy of the result saved to {BACKUP_PATH}')
    print(f'\n{len(multi)} (base, tier) collision(s) resolved via distinct filler items:')
    for (base_code, tier), items in sorted(multi.items(), key=lambda kv: -len(kv[1])):
        print(f'  {base_code} @ tier {tier} ({RUNES[tier-1][1]}): {items}')
    if skipped:
        print(f'\nSkipped {len(skipped)} duplicate signature(s) (should be 0):')
        for s in skipped:
            print(' ', s)

    print()
    import generate_recipe_list
    generate_recipe_list.main()


if __name__ == '__main__':
    main()
