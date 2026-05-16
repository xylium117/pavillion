import pickle
import sys
from callcricketnew import player

# ─── Constants ────────────────────────────────────────────────────────────────

VALID_TAGS = [
    'OpenBat', 'Bat',
    'OpenWK',  'WK',
    'OpenFast','Fast',
    'OpenMed', 'Med',
    'OpenSpin','Spin',
    'PartFast','PartMed','PartSpin',
]

TAG_HINTS = {
    'OpenBat':  'opening batsman, no real bowling',
    'Bat':      'middle-order batsman, no real bowling',
    'OpenWK':   'opening wicketkeeper-batsman',
    'WK':       'wicketkeeper-batsman',
    'OpenFast': 'opening bat who also bowls fast',
    'Fast':     'main fast bowler',
    'OpenMed':  'opening bat who also bowls medium',
    'Med':      'main medium bowler',
    'OpenSpin': 'opening bat who also bowls spin',
    'Spin':     'main spin bowler',
    'PartFast': 'batsman with part-time fast bowling',
    'PartMed':  'batsman with part-time medium bowling',
    'PartSpin': 'batsman with part-time spin bowling',
}

TEAMS = [
    'England', 'Australia', 'South Africa', 'West Indies',
    'New Zealand', 'India', 'Pakistan', 'Sri Lanka',
    'Zimbabwe', 'Bangladesh', 'Afghanistan', 'Ireland',
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_players():
    try:
        with open('players', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print('No "players" file found — starting with an empty database.')
        return []
    except Exception as e:
        print(f'Error loading players: {e}')
        sys.exit(1)

def save_players(players):
    # Backup first
    try:
        with open('players', 'rb') as f:
            backup = f.read()
        with open('players.bak', 'wb') as f:
            f.write(backup)
    except FileNotFoundError:
        pass

    with open('players', 'wb') as f:
        pickle.dump(players, f)
    print(f'  Saved {len(players)} players to database (backup at players.bak).')

def get_str(prompt, required=True, default=None):
    while True:
        suffix = f' [{default}]' if default else ''
        val = input(f'{prompt}{suffix}: ').strip()
        if val == '' and default is not None:
            return default
        if val == '' and required:
            print('  Cannot be empty.')
            continue
        return val

def get_int(prompt, lo=None, hi=None, default=None):
    while True:
        suffix = f' [{default}]' if default is not None else ''
        val_str = input(f'{prompt}{suffix}: ').strip()
        if val_str == '' and default is not None:
            return default
        try:
            val = int(val_str)
        except ValueError:
            print('  Please enter a whole number.')
            continue
        if lo is not None and val < lo:
            print(f'  Must be ≥ {lo}')
            continue
        if hi is not None and val > hi:
            print(f'  Must be ≤ {hi}')
            continue
        return val

def get_float(prompt, lo=None, hi=None, default=None):
    while True:
        suffix = f' [{default}]' if default is not None else ''
        val_str = input(f'{prompt}{suffix}: ').strip()
        if val_str == '' and default is not None:
            return default
        try:
            val = float(val_str)
        except ValueError:
            print('  Please enter a number.')
            continue
        if lo is not None and val < lo:
            print(f'  Must be ≥ {lo}')
            continue
        if hi is not None and val > hi:
            print(f'  Must be ≤ {hi}')
            continue
        return val

def get_era_average(year):
    """Return the era batting average for a given year from eradata.txt."""
    try:
        with open('data/era/eradata.txt') as f:
            for line in f:
                x = line.strip().split(', ')
                if int(x[0]) == year:
                    return float(x[1])
    except Exception:
        pass
    return 30.0  # neutral fallback

def era_adjust_bat(raw_av, year):
    era = get_era_average(year)
    return round((30.0 / era) * raw_av, 2), era

def era_adjust_bowl(raw_av, year):
    era = get_era_average(year)
    return round((30.0 / era) * raw_av, 2), era

def is_bowler(tag):
    return any(t in tag for t in ['Fast', 'Med', 'Spin'])

def make_fresh_player():
    """
    Return a player instance with all list attributes initialised as fresh
    instance-level lists (not shared class-level ones).
    """
    p = player()
    p.inns      = []
    p.bowls     = []
    p.captgames = []
    p.games     = 0
    p.motm      = 0
    p.runs      = 0
    p.balls     = 0
    p.outs      = 0
    p.batav     = 0
    p.batsr     = 0
    p.fifties   = 0
    p.centuries = 0
    p.doubles   = 0
    p.HS        = 0
    p.HSNO      = ' '
    p.ballsbowled = 0
    p.overs     = 0
    p.maidens   = 0
    p.bowlruns  = 0
    p.wickets   = 0
    p.bowlav    = float('inf')
    p.bowler    = float('inf')
    p.bowlsr    = float('inf')
    p.fives     = 0
    p.tens      = 0
    p.BBR       = float('inf')
    p.BBW       = 0
    p.catches   = 0
    p.stumpings = 0
    p.innings   = ''
    p.bowling   = ''
    p.motmscore = 0
    p.mod       = 1
    p.status    = ''
    p.secondteam = ''
    p.dropdate  = 0
    p.age       = 0
    return p

def print_player(p, verbose=False):
    bowl_str = f'{p.bowl}' if is_bowler(p.tag) else 'n/a'
    print(f'  {p.name:<22} {p.team:<14} {p.tag:<12} '
          f'{p.first}-{p.last}  bat={p.bat}  bowl={bowl_str}  '
          f'sr={p.sr}  er={p.er}  capt={p.capt}')
    if verbose:
        print(f'    dob={p.dob}  basebat={p.basebat}  basebowl={p.basebowl}  '
              f'batform={p.batform}  bowlform={p.bowlform}')

# ─── Core actions ─────────────────────────────────────────────────────────────

def add_player(players):
    print('\n── Add New Player ──────────────────────────────────')

    p = make_fresh_player()

    # Name
    while True:
        p.name = get_str('Name')
        dupes = [x for x in players if x.name == p.name]
        if dupes:
            print(f'  Warning: {len(dupes)} player(s) named "{p.name}" already exist:')
            for d in dupes:
                print(f'    {d.name} ({d.team}, {d.first}-{d.last})')
            if get_str('Add anyway? (y/n)', default='n').lower() != 'y':
                continue
        break

    # Team
    print(f'\n  Known teams: {", ".join(TEAMS)}')
    p.team = get_str('Team (known team or custom name)')

    # Years
    print()
    p.first      = get_int('First year active  (e.g. 1990)', lo=1800, hi=2030)
    p.last       = get_int('Last year active   (e.g. 2010)', lo=p.first, hi=2030, default=p.first + 10)
    p.realfirst  = p.first
    p.reallast   = p.last
    p.end        = p.last
    p.debut      = str(p.first)

    default_dob  = p.first - 21
    p.dob        = get_int(f'Year of birth', lo=1800, hi=2020, default=default_dob)
    mid_year     = round((p.first + p.last) / 2)

    # Role / Tag
    print('\n  Roles:')
    for tag, hint in TAG_HINTS.items():
        print(f'    {tag:<12} — {hint}')
    while True:
        p.tag = get_str('\nRole')
        if p.tag in VALID_TAGS:
            break
        print(f'  Invalid role. Choose from: {", ".join(VALID_TAGS)}')

    # ── Batting ──
    print('\n── Batting ─────────────────────────────────────────')
    print('  Adjusted ratings are era-normalised to a baseline of avg=30.')
    print('  Typical: 15=tailender  25=lower-order  35=decent  45=good  55+=great')
    mode = ''
    while mode not in ('r', 'a'):
        mode = get_str("Enter as (r)aw career average or (a)djusted rating?").lower()

    if mode == 'r':
        raw = get_float('Raw career batting average', lo=0, hi=500)
        p.bat, era = era_adjust_bat(raw, mid_year)
        print(f'  Era average for {mid_year}: {era:.2f}  →  adjusted bat rating: {p.bat}')
    else:
        p.bat = get_float('Adjusted batting rating', lo=0, hi=100)

    # ── Bowling ──
    print('\n── Bowling ─────────────────────────────────────────')
    if not is_bowler(p.tag):
        print('  Non-bowler — setting bowling rating to 500 (default).')
        p.bowl = get_float('Bowling rating (500 = non-bowler)', lo=0, hi=500, default=500)
    else:
        print('  Adjusted ratings — lower is better.')
        print('  Typical: 20=excellent  28=very good  35=average  45=poor  500=non-bowler')
        mode = ''
        while mode not in ('r', 'a'):
            mode = get_str("Enter as (r)aw career average or (a)djusted rating?").lower()

        if mode == 'r':
            raw = get_float('Raw career bowling average', lo=0, hi=500)
            p.bowl, era = era_adjust_bowl(raw, mid_year)
            p.bowl = min(p.bowl, 500)
            print(f'  Era average for {mid_year}: {era:.2f}  →  adjusted bowl rating: {p.bowl}')
        else:
            p.bowl = get_float('Adjusted bowling rating (lower = better)', lo=0, hi=500)

    # ── Strike rate / economy ──
    print('\n── Batting Strike Rate ─────────────────────────────')
    print('  Runs per ball relative to era.  0.5=very slow  1.0=normal  1.5=attacking  2.0=slogger')
    p.sr = get_float('Strike rate multiplier', lo=0.5, hi=2.0, default=1.0)

    print('\n── Bowling Economy Rate ────────────────────────────')
    print('  Economy relative to era.  0.8=miserly  1.0=normal  1.2=expensive')
    p.er = get_float('Economy rate multiplier', lo=0.8, hi=1.2, default=1.0)

    # ── Captaincy ──
    print('\n── Captaincy ───────────────────────────────────────')
    print('  0 = never captain   1-4 = occasional   5-9 = regular   10+ = long-term captain')
    p.capt = get_int('Captaincy score', lo=0, hi=100, default=0)

    # ── Derived fields ──
    p.basebat   = p.bat
    p.basebowl  = p.bowl
    p.batform   = p.bat        # initial in-game form starts at base rating
    p.bowlform  = max(0.0, round((60 - p.bowl) * (p.bowl < 60), 2))

    # ── Summary & confirm ──
    print('\n── Summary ─────────────────────────────────────────')
    print_player(p, verbose=True)
    if get_str('\nAdd this player? (y/n)', default='y').lower() == 'y':
        players.append(p)
        print(f'  ✓ {p.name} added to database.')
        return True
    print('  Cancelled.')
    return False


def search_players(players, query=None):
    if query is None:
        query = get_str('Search by name or team').lower()
    results = [p for p in players
               if query in p.name.lower() or query in p.team.lower()]
    if not results:
        print('  No players found.')
    else:
        print(f'\n  {len(results)} result(s):')
        for i, p in enumerate(results, 1):
            print(f'  {i:>3}.', end=' ')
            print_player(p)
    return results


def edit_player(players):
    results = search_players(players)
    if not results:
        return False

    idx = get_int('Number to edit (0 to cancel)', lo=0, hi=len(results), default=0)
    if idx == 0:
        return False

    p = results[idx - 1]
    print(f'\nEditing: {p.name} ({p.team})')
    print('Editable fields: name  team  first  last  dob  tag  bat  bowl  sr  er  capt')

    field = get_str('Field to edit').lower()

    changed = True
    if field == 'name':
        p.name = get_str(f'New name', default=p.name)
    elif field == 'team':
        p.team = get_str(f'New team', default=p.team)
    elif field == 'first':
        p.first     = get_int('New first year', lo=1800, hi=2030, default=p.first)
        p.realfirst = p.first
        p.debut     = str(p.first)
    elif field == 'last':
        p.last     = get_int('New last year', lo=p.first, hi=2030, default=p.last)
        p.reallast = p.last
        p.end      = p.last
    elif field == 'dob':
        p.dob = get_int('New year of birth', lo=1800, hi=2020, default=p.dob)
    elif field == 'tag':
        print(f'  Roles: {", ".join(VALID_TAGS)}')
        new_tag = get_str(f'New role', default=p.tag)
        if new_tag in VALID_TAGS:
            p.tag = new_tag
        else:
            print('  Invalid role — keeping current.')
            changed = False
    elif field == 'bat':
        p.bat     = get_float('New adjusted bat rating', lo=0, hi=100, default=p.bat)
        p.basebat = p.bat
        p.batform = p.bat
    elif field == 'bowl':
        p.bowl     = get_float('New adjusted bowl rating (lower=better)', lo=0, hi=500, default=p.bowl)
        p.basebowl = p.bowl
        p.bowlform = max(0.0, round((60 - p.bowl) * (p.bowl < 60), 2))
    elif field == 'sr':
        p.sr = get_float('New SR multiplier (0.5-2.0)', lo=0.5, hi=2.0, default=p.sr)
    elif field == 'er':
        p.er = get_float('New ER multiplier (0.8-1.2)', lo=0.8, hi=1.2, default=p.er)
    elif field == 'capt':
        p.capt = get_int('New captaincy score', lo=0, hi=100, default=p.capt)
    else:
        print('  Unknown field — no changes made.')
        changed = False

    if changed:
        print(f'  ✓ {p.name} updated.')
    return changed


def delete_player(players):
    results = search_players(players)
    if not results:
        return False

    idx = get_int('Number to delete (0 to cancel)', lo=0, hi=len(results), default=0)
    if idx == 0:
        return False

    p = results[idx - 1]
    print_player(p, verbose=True)
    if get_str(f'Delete {p.name}? This cannot be undone. (y/n)', default='n').lower() == 'y':
        players.remove(p)
        print(f'  ✓ {p.name} deleted.')
        return True
    print('  Cancelled.')
    return False


def list_teams(players):
    counts = {}
    for p in players:
        counts[p.team] = counts.get(p.team, 0) + 1
    print(f'\n  {"Team":<22} Players')
    print(f'  {"─"*22} ───────')
    for team, n in sorted(counts.items()):
        print(f'  {team:<22} {n}')


def show_era_table():
    """Print a sample of era averages so the user can calibrate ratings."""
    print('\n  Year  Era avg   (use this to gauge how much to adjust raw stats)')
    print('  ─────────────────')
    try:
        with open('data/era/eradata.txt') as f:
            rows = [line.strip().split(', ') for line in f if line.strip()]
        # show every 10 years
        for row in rows:
            yr = int(row[0])
            if yr % 10 == 0:
                print(f'  {yr}    {float(row[1]):.2f}')
    except Exception:
        print('  (eradata.txt not found)')

# ─── Main loop ────────────────────────────────────────────────────────────────

MENU = """
Commands:
  a  — add a new player
  e  — edit an existing player
  d  — delete a player
  s  — search / browse players
  t  — list teams and player counts
  era— show era average table (helps calibrate ratings)
  q  — quit (you will be prompted to save)
"""

def main():
    print('═' * 52)
    print('  Cricket Player Database Editor')
    print('═' * 52)

    players  = load_players()
    print(f'  Loaded {len(players)} players.\n')

    modified = False

    while True:
        print(MENU)
        cmd = get_str('Command', required=False, default='').lower()

        if cmd == 'a':
            if add_player(players):
                modified = True

        elif cmd == 'e':
            if edit_player(players):
                modified = True

        elif cmd == 'd':
            if delete_player(players):
                modified = True

        elif cmd == 's':
            search_players(players)

        elif cmd == 't':
            list_teams(players)

        elif cmd == 'era':
            show_era_table()

        elif cmd == 'q':
            break

        else:
            if cmd:
                print('  Unknown command.')

    if modified:
        print()
        if get_str('Save changes? (y/n)', default='y').lower() == 'y':
            save_players(players)
        else:
            print('  Changes discarded.')
    else:
        print('  No changes made.')

    print('Done.')


if __name__ == '__main__':
    main()