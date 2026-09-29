"""Shared helpers for generating Horadric Cube "buy a specific unique/set item" recipes.

No pandas / notebook dependency by design -- plain csv + stdlib only.
"""
import csv

DATA_DIR = 'data'

# Ordered El (cheapest) -> Zod (priciest). Index 0 == tier 1.
RUNES = [
    ('r01', 'El'), ('r02', 'Eld'), ('r03', 'Tir'), ('r04', 'Nef'), ('r05', 'Eth'),
    ('r06', 'Ith'), ('r07', 'Tal'), ('r08', 'Ral'), ('r09', 'Ort'), ('r10', 'Thul'),
    ('r11', 'Amn'), ('r12', 'Sol'), ('r13', 'Shael'), ('r14', 'Dol'), ('r15', 'Hel'),
    ('r16', 'Io'), ('r17', 'Lum'), ('r18', 'Ko'), ('r19', 'Fal'), ('r20', 'Lem'),
    ('r21', 'Pul'), ('r22', 'Um'), ('r23', 'Mal'), ('r24', 'Ist'), ('r25', 'Gul'),
    ('r26', 'Vex'), ('r27', 'Ohm'), ('r28', 'Lo'), ('r29', 'Sur'), ('r30', 'Ber'),
    ('r31', 'Jah'), ('r32', 'Cham'), ('r33', 'Zod'),
]
NUM_TIERS = len(RUNES)  # 33
RUNE_NAME_TO_TIER = {name.lower(): i + 1 for i, (code, name) in enumerate(RUNES)}


def resolve_tier(name_field, tier_field):
    """The rune *name* column is what a human actually edits, so it's treated
    as authoritative when present and valid; the numeric tier column is a
    cache of that, kept in sync. Falls back to the numeric field only if the
    name is blank or unrecognized.
    """
    name = (name_field or '').strip().lower()
    if name in RUNE_NAME_TO_TIER:
        return RUNE_NAME_TO_TIER[name]
    tier = (tier_field or '').strip()
    return int(tier) if tier.isdigit() else None

# Base names in set_items.csv that don't match armor.txt/weapons.txt spelling exactly.
BASE_NAME_ALIASES = {
    'Sabre': 'Saber',
    'Ornate Plate': 'Ornate Armor',
}

# Jewels/charms live in misc.txt, which isn't part of this mod's local data set,
# so they're not resolvable via armor.txt/weapons.txt -- just display names.
MISC_BASE_NAMES = {
    'jew': 'Jewel',
    'cm1': 'Small Charm',
    'cm2': 'Large Charm',
    'cm3': 'Grand Charm',
}

# Unique items whose base code is a quest-reward-only item (e.g. Amulet of the
# Viper) that never exists as a plain white/normal-quality base -- a forward
# "base + rune" recipe for these can never actually be fed, so they're
# excluded from the catalog rather than shipping a dead recipe.
QUEST_ONLY_UNIQUE_CODES = {'vip', 'msf', 'hst', 'qf1', 'qf2', 'qhr', 'qey', 'qbr', 'leg'}

# Charms/rings/amulets/jewels basically never drop as true white (no-affix)
# items -- rare, and rarer still with more Magic Find -- so forward recipes
# for these accept any quality. Every other item type is restricted to a
# genuinely white base (low/normal/superior, not magic/rare/unique/set/crafted).
QUALITY_EXEMPT_CODES = {'amu', 'rin', 'jew', 'cm1', 'cm2', 'cm3', 'cm4'}
WHITE_QUALITY_TIERS = ['nor', 'hiq', 'low']  # normal, superior, low quality

# Item categories that can never be ethereal in Diablo II, regardless of source.
NON_ETH_TYPES = {'bow', 'xbow'}
NON_ETH_CODES = {'7cr'}  # Phase Blade

# Cheap, always-purchasable filler items used as the recipe's 3rd input. None of
# these are used elsewhere in cubemain.txt in a way that could collide with a
# 3-input base+rune+filler recipe. The default filler is index 0; when two items
# share the same (base_code, ethereal state, rune tier), each gets a distinct
# filler from this pool instead of bumping either item's rune price.
FILLER_POOL = [
    'isc', 'tsc', 'ibk', 'tbk', 'key',
    'hp1', 'mp1', 'hp2', 'mp2', 'hp3', 'mp3', 'hp4',
]
FILLER_CODE = FILLER_POOL[0]  # Scroll of Identify

FILLER_NAMES = {
    'isc': 'Scroll of Identify',
    'tsc': 'Scroll of Town Portal',
    'ibk': 'Tome of Identify',
    'tbk': 'Tome of Town Portal',
    'key': 'Key',
    'hp1': 'Minor Healing Potion',
    'mp1': 'Minor Mana Potion',
    'hp2': 'Light Healing Potion',
    'mp2': 'Light Mana Potion',
    'hp3': 'Healing Potion',
    'mp3': 'Mana Potion',
    'hp4': 'Greater Healing Potion',
}

CUBEMAIN_HEADER = [
    'description', 'enabled', 'firstLadderSeason', 'lastLadderSeason', 'min diff', 'version',
    'op', 'param', 'value', 'class', 'numinputs', 'input 1', 'input 2', 'input 3', 'input 4',
    'input 5', 'input 6', 'input 7', 'output', 'lvl', 'plvl', 'ilvl', 'mod 1', 'mod 1 chance',
    'mod 1 param', 'mod 1 min', 'mod 1 max', 'mod 2', 'mod 2 chance', 'mod 2 param', 'mod 2 min',
    'mod 2 max', 'mod 3', 'mod 3 chance', 'mod 3 param', 'mod 3 min', 'mod 3 max', 'mod 4',
    'mod 4 chance', 'mod 4 param', 'mod 4 min', 'mod 4 max', 'mod 5', 'mod 5 chance',
    'mod 5 param', 'mod 5 min', 'mod 5 max', 'output b', 'b lvl', 'b plvl', 'b ilvl', 'b mod 1',
    'b mod 1 chance', 'b mod 1 param', 'b mod 1 min', 'b mod 1 max', 'b mod 2', 'b mod 2 chance',
    'b mod 2 param', 'b mod 2 min', 'b mod 2 max', 'b mod 3', 'b mod 3 chance', 'b mod 3 param',
    'b mod 3 min', 'b mod 3 max', 'b mod 4', 'b mod 4 chance', 'b mod 4 param', 'b mod 4 min',
    'b mod 4 max', 'b mod 5', 'b mod 5 chance', 'b mod 5 param', 'b mod 5 min', 'b mod 5 max',
    'output c', 'c lvl', 'c plvl', 'c ilvl', 'c mod 1', 'c mod 1 chance', 'c mod 1 param',
    'c mod 1 min', 'c mod 1 max', 'c mod 2', 'c mod 2 chance', 'c mod 2 param', 'c mod 2 min',
    'c mod 2 max', 'c mod 3', 'c mod 3 chance', 'c mod 3 param', 'c mod 3 min', 'c mod 3 max',
    'c mod 4', 'c mod 4 chance', 'c mod 4 param', 'c mod 4 min', 'c mod 4 max', 'c mod 5',
    'c mod 5 chance', 'c mod 5 param', 'c mod 5 min', 'c mod 5 max', '*eol',
]


def read_tsv(path):
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def load_base_tables():
    """Returns (name2code, code2info) for every armor/weapon base.

    code2info[code] = {'type': str, 'type2': str, 'level': int}
    """
    name2code = {}
    code2info = {}

    for row in read_tsv(f'{DATA_DIR}/armor.txt'):
        n, c = row.get('name', '').strip(), row.get('code', '').strip()
        if not n or not c:
            continue
        name2code[n] = c
        lvl = row.get('level', '').strip()
        code2info[c] = {
            'type': row.get('type', '').strip(),
            'type2': row.get('type2', '').strip(),
            'level': int(lvl) if lvl.isdigit() else 0,
        }

    for row in read_tsv(f'{DATA_DIR}/weapons.txt'):
        n, c = row.get('name', '').strip(), row.get('code', '').strip()
        if not n or not c:
            continue
        name2code[n] = c
        lvl = row.get('level', '').strip()
        code2info[c] = {
            'type': row.get('type', '').strip(),
            'type2': row.get('type2', '').strip(),
            'level': int(lvl) if lvl.isdigit() else 0,
        }

    # Rings/amulets live in misc.txt, which isn't part of this mod's local data set.
    name2code['Ring'] = 'rin'
    name2code['Amulet'] = 'amu'
    code2info['rin'] = {'type': 'ring', 'type2': '', 'level': 0}
    code2info['amu'] = {'type': 'amulet', 'type2': '', 'level': 0}

    for alias, real in BASE_NAME_ALIASES.items():
        if real in name2code:
            name2code[alias] = name2code[real]

    return name2code, code2info


def is_etherealizable(code, code2info):
    info = code2info.get(code)
    if not info:
        return False
    if code in NON_ETH_CODES:
        return False
    if info['type'] in NON_ETH_TYPES or info['type2'] in NON_ETH_TYPES:
        return False
    if info['type'] in ('ring', 'amulet'):
        return False
    return True


def level_to_tier(level, max_level=110):
    level = max(0, min(level, max_level))
    tier = round(level / max_level * NUM_TIERS)
    return max(1, min(NUM_TIERS, tier))


def blank_row():
    row = {h: '' for h in CUBEMAIN_HEADER}
    row['*eol'] = '0'
    row['enabled'] = '1'
    row['version'] = '100'
    return row
