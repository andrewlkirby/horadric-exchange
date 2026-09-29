"""One-time fix: the 8 Rainbow Facet unique jewels all share the exact same
'index' (display) name in uniqueitems.txt, so no cube recipe -- or drop, for
that matter -- can be made to target one specifically. Give each variant a
distinct, descriptive name so recipes can be fully deterministic.
"""
import csv

PATH = 'data/uniqueitems.txt'

NAMES = {
    ('death-skill', 'Chain Lightning'): 'Rainbow Facet (Hit Power - Lightning)',
    ('death-skill', 'Blizzard'): 'Rainbow Facet (Hit Power - Cold)',
    ('death-skill', 'Meteor'): 'Rainbow Facet (Hit Power - Fire)',
    ('death-skill', 'Poison Nova'): 'Rainbow Facet (Hit Power - Poison)',
    ('levelup-skill', 'Nova'): 'Rainbow Facet (Level Up - Lightning)',
    ('levelup-skill', 'Frost Nova'): 'Rainbow Facet (Level Up - Cold)',
    ('levelup-skill', 'Blaze'): 'Rainbow Facet (Level Up - Fire)',
    ('levelup-skill', 'Venom'): 'Rainbow Facet (Level Up - Poison)',
}

with open(PATH, encoding='utf-8') as f:
    rows = list(csv.reader(f, delimiter='\t'))

header = rows[0]
prop4_i, par4_i = header.index('prop4'), header.index('par4')

changed = 0
for row in rows[1:]:
    if row[0].strip() != 'Rainbow Facet':
        continue
    key = (row[prop4_i].strip(), row[par4_i].strip())
    if key not in NAMES:
        raise SystemExit(f'Unrecognized Rainbow Facet variant: {key}')
    row[0] = NAMES[key]
    changed += 1

assert changed == 8, changed

with open(PATH, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\r\n')
    w.writerows(rows)

print(f'Renamed {changed} Rainbow Facet rows.')
