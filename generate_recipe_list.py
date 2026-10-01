"""Generate human-readable recipe lists from the custom recipes appended to
data/cubemain.txt (everything after the untouched vanilla rows).

Usage: python generate_recipe_list.py
Output: recipes.txt (plain text), recipes.md (GitHub-flavored tables)
"""
import csv

from cube_common import RUNES, FILLER_NAMES

VANILLA_PATH = 'data/cubemain.vanilla.txt'
CUBEMAIN_PATH = 'data/cubemain.txt'
PRICES_PATH = 'prices.csv'
TXT_PATH = 'recipes.txt'
MD_PATH = 'recipes.md'

RUNE_NAME_BY_CODE = {code: name for code, name in RUNES}


def load_prices():
    """item name -> its prices.csv row, for kind + base_name lookups."""
    return {row['item']: row for row in csv.DictReader(open(PRICES_PATH, encoding='utf-8'))}


def load_recipes():
    with open(VANILLA_PATH, encoding='utf-8') as f:
        n_vanilla = sum(1 for _ in f) - 1  # minus header

    rows = list(csv.DictReader(open(CUBEMAIN_PATH, encoding='utf-8'), delimiter='\t'))
    custom = rows[n_vanilla:]

    all_forward = [r for r in custom if r['numinputs'] == '3']
    # Non-exempt items get one raw recipe per white-quality tier (nor/hiq/low)
    # -- correct for the game data, but redundant to show 3x in a human list.
    # Collapse back to one representative line per (item, ethereal-state).
    seen = set()
    forward = []
    for r in sorted(all_forward, key=lambda r: r['output'].lower()):
        key = (r['output'], r['mod 1'] == 'ethereal', r['input 2'], r['input 3'])
        if key in seen:
            continue
        seen.add(key)
        forward.append(r)

    reverse = sorted(
        (r for r in custom if r['numinputs'] == '2' and r['output b']),
        key=lambda r: r['input 1'].lower(),
    )
    return forward, reverse


NOTE = (
    'NOTE: recipes match the base item by type and ethereal state, plus a '
    'quality rule that depends on the item: for charms/rings/amulets/jewels, '
    'ANY quality works (low/normal/superior/magic/rare/crafted) since these '
    'almost never drop as true white items. For everything else, the base '
    'must be genuinely white (low, normal, or superior quality) -- magic, '
    'rare, crafted, and already-unique/set items do NOT satisfy the recipe. '
    'For the always-any-quality category, a DIFFERENT unique/set item '
    'sharing the same base type also satisfies the recipe and gets '
    'destroyed for the same result -- double check what you feed in.'
)


def forward_line(r, prices):
    """Clean display text for a forward recipe -- built from the structured
    fields rather than the raw per-quality-tier description in cubemain.txt,
    since that description names only one of the (possibly three) white
    quality tiers this recipe was collapsed from.
    """
    base_name = prices[r['output']]['base_name']
    if 'eth' in r['input 1'].split(','):
        base_name += ' (Ethereal)'
    rune_name = RUNE_NAME_BY_CODE.get(r['input 2'], r['input 2'])
    filler = FILLER_NAMES.get(r['input 3'], r['input 3'])
    suffix = ' (eth)' if r['mod 1'] == 'ethereal' else ''
    return f"{base_name} + {rune_name} Rune + {filler} -> {r['output']}{suffix}"


def write_txt(forward, reverse, prices):
    lines = [NOTE, '']
    lines.append(f'CRAFTING RECIPES ({len(forward)})')
    lines.append('Base item + rune + filler item -> named unique/set item')
    lines.append('=' * 70)
    for r in forward:
        lines.append(forward_line(r, prices))

    lines.append('')
    lines.append(f'SALVAGE RECIPES ({len(reverse)})')
    lines.append('Named unique/set item + filler item -> base item + rune')
    lines.append('=' * 70)
    for r in reverse:
        lines.append(r['description'])

    with open(TXT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def forward_table(rows, prices):
    lines = ['| Item | Base Item | Rune | Filler Item |', '|---|---|---|---|']
    for r in rows:
        base_name = prices[r['output']]['base_name']
        if 'eth' in r['input 1'].split(','):
            base_name += ' (Ethereal)'
        rune_name = RUNE_NAME_BY_CODE.get(r['input 2'], r['input 2'])
        filler = FILLER_NAMES.get(r['input 3'], r['input 3'])
        lines.append(f"| {r['output']} | {base_name} | {rune_name} | {filler} |")
    return lines


def reverse_table(rows, prices):
    lines = ['| Item | Base Item Returned | Rune Returned |', '|---|---|---|']
    for r in rows:
        item = r['input 1']
        base_name = prices[item]['base_name']
        rune_name = RUNE_NAME_BY_CODE.get(r['output b'], r['output b'])
        lines.append(f"| {item} | {base_name} | {rune_name} |")
    return lines


def md_section(title, subtitle, rows, table_fn, prices, key_fn):
    lines = [f'## {title} ({len(rows)})', '', subtitle, '']
    for kind, label in (('unique', 'Unique Items'), ('set', 'Set Items')):
        group = [r for r in rows if prices.get(key_fn(r), {}).get('kind') == kind]
        if not group:
            continue
        lines.append('<details>')
        lines.append(f'<summary><strong>{label} ({len(group)})</strong></summary>')
        lines.append('')
        lines.extend(table_fn(group, prices))
        lines.append('')
        lines.append('</details>')
        lines.append('')
    return lines


def by_rune_section(forward, prices):
    """Crafting recipes regrouped by rune (low -> high), one collapsible block
    per rune, so "what can I make with this rune?" doesn't mean scanning the
    whole alphabetical table. Markdown can't run scripts, so this stands in
    for a filter.
    """
    by_code = {}
    for r in forward:
        by_code.setdefault(r['input 2'], []).append(r)

    present = [(code, name) for code, name in RUNES if code in by_code]
    lines = ['## Crafting Recipes by Rune', '']
    lines.append('Jump to: ' + ' &middot; '.join(
        f'[{name}](#{name.lower()}-rune-{len(by_code[code])})' for code, name in present
    ))
    lines.append('')
    for code, name in present:
        group = by_code[code]
        lines.append(f'### {name} Rune ({len(group)})')
        lines.append('')
        lines.append('<details>')
        lines.append(f'<summary>Show {len(group)} recipes</summary>')
        lines.append('')
        lines.extend(forward_table(group, prices))
        lines.append('')
        lines.append('</details>')
        lines.append('')
    return lines


def write_md(forward, reverse, prices):
    lines = ['# Horadric Exchange -- Recipe List', '']
    lines.append(
        'Recipes match the base item by **type and ethereal state**, plus a '
        'quality rule that depends on the item:'
    )
    lines.append('')
    lines.append(
        '- **Charms, rings, amulets, jewels:** any quality works (low, '
        'normal, superior, magic, rare, crafted) -- these almost never drop '
        'as true white items, so the recipe accepts whatever you can find.'
    )
    lines.append(
        '- **Everything else:** the base must be genuinely white -- low '
        'quality, normal, or superior. Magic, rare, crafted, or '
        'already-unique/set items do **not** satisfy the recipe.'
    )
    lines.append('')
    lines.append(
        '"(Ethereal)" bases require an ethereal version of that base; all '
        'others require a non-ethereal one.'
    )
    lines.append('')
    lines.append(
        '> **Careful:** for the always-any-quality category '
        '(charms/rings/amulets/jewels), a *different* unique/set item that '
        'happens to share the same base type also satisfies the recipe and '
        'gets destroyed for the same result -- double check what you feed in.'
    )
    lines.append('')
    lines.append(
        'Looking for a specific item? Use your browser\'s find (Ctrl+F). '
        'Have a rune and want to know what it makes? See '
        '[Crafting Recipes by Rune](#crafting-recipes-by-rune).'
    )
    lines.append('')
    lines.extend(md_section(
        'Crafting Recipes','Base item + rune + filler item &rarr; named unique/set item',
        forward, forward_table, prices, key_fn=lambda r: r['output'],
    ))
    lines.extend(md_section(
        'Salvage Recipes', 'Named unique/set item + filler item &rarr; base item + rune',
        reverse, reverse_table, prices, key_fn=lambda r: r['input 1'],
    ))
    lines.extend(by_rune_section(forward, prices))

    with open(MD_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def main():
    forward, reverse = load_recipes()
    prices = load_prices()
    write_txt(forward, reverse, prices)
    write_md(forward, reverse, prices)
    print(f'Wrote {TXT_PATH} and {MD_PATH}: {len(forward)} crafting recipes, {len(reverse)} salvage recipes')


if __name__ == '__main__':
    main()
