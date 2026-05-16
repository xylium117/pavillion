import os
import pickle
from callcricketnew import player, team, quickorder, listshow, playerwrite
from game import game, setup
from historical import series

CUSTOM_TEAMS_FILE = 'variables/customteams.txt'


# ─── File helpers ─────────────────────────────────────────────────────────────

def possible():
	"""Return (team_names, all_lines) from the custom teams file."""
	if not os.path.exists(CUSTOM_TEAMS_FILE):
		return [], []

	with open(CUSTOM_TEAMS_FILE) as f:
		lines = [line.rstrip('\n') for line in f]

	team_names = []
	for i, line in enumerate(lines):
		if line == '' and i + 1 < len(lines) and lines[i + 1] != '':
			team_names.append(lines[i + 1])

	return team_names, lines


def find(team_name, all_lines):
	"""Return the raw player lines belonging to team_name."""
	players = []
	reading = False
	for line in all_lines:
		if line == team_name:
			reading = True
			continue
		if reading:
			if line == '':
				break
			players.append(line)
	return players


def playermake(raw_line, t):
	"""Parse a playerwrite-formatted line and return a player object."""
	p = player()
	# Strip surrounding brackets and split on comma
	parts = raw_line[2:-3].split(',')
	p.name  = parts[0][:-1]          # strip trailing quote
	p.team  = t.name
	p.bat   = float(parts[1])
	p.bowl  = float(parts[2])
	p.tag   = parts[3][2:-1]         # strip leading space+quote and trailing quote
	p.first = int(parts[4])
	p.last  = int(parts[5])
	p.sr    = float(parts[6])
	p.er    = float(parts[7])
	p.capt  = int(parts[8])
	# Ensure instance-level lists so players don't share class-level state
	p.inns      = []
	p.bowls     = []
	p.captgames = []
	return p


def getplayers():
	"""Load and return all players from the pickle database."""
	with open('players', 'rb') as f:
		return pickle.load(f)


# ─── Team loading ─────────────────────────────────────────────────────────────

def load(t, already_chosen):
	"""Interactively select a saved custom team and populate t."""
	available, all_lines = possible()

	if not available:
		print('No saved custom teams found.')
		return None

	# Hide teams already picked in this session
	choices = [name for name in available if name not in already_chosen]

	if not choices:
		print('All saved teams have already been selected.')
		return None

	while True:
		t.name = input('Select a team from: {} -- '.format(listshow(choices))).strip()
		if t.name in choices:
			break
		print('  Invalid selection, please try again.')

	for raw_line in find(t.name, all_lines):
		t.active.append(playermake(raw_line, t))

	return t


# ─── Team building ────────────────────────────────────────────────────────────

def _show_roster(active):
	"""Print the current squad."""
	if not active:
		print('  (no players yet)')
		return
	print(f'  Current squad ({len(active)}):')
	for i, p in enumerate(active, 1):
		bowl = '' if p.bowl >= 490 else f'  bowl {p.bowl}'
		print(f'    {i:>2}. {p.name:<22} {p.team:<14} {p.tag}{bowl}')


def _pick_from_matches(team_obj, matches, db_players):
	"""
	Given a list of matching player objects, let the user choose one,
	then append it to team_obj.active.  Returns True on success.
	"""
	if len(matches) == 1:
		chosen = matches[0]
	else:
		print('  Multiple matches:')
		for i, p in enumerate(matches, 1):
			print(f'    {i}. {p.name} ({p.team}, {p.tag}, '
				  f'{p.first}-{p.last})')
		raw = input('  Enter number to select (or Enter to cancel): ').strip()
		if not raw:
			return False
		try:
			chosen = matches[int(raw) - 1]
		except (ValueError, IndexError):
			print('  Invalid selection.')
			return False

	# Guard against duplicates
	if chosen in team_obj.active:
		print(f'  {chosen.name} is already in the squad.')
		return False

	chosen.team = team_obj.name
	team_obj.active.append(chosen)
	print(f'  ✓ {chosen.name} added  '
		  f'(bat {chosen.bat}, bowl {chosen.bowl}, {chosen.tag})')
	return True


def make(team_obj):
	"""Interactively build a new custom team from the player database."""
	db = getplayers()
	add_more = True   # explicit flag; no reliance on undefined variable

	while len(team_obj.active) < 11 or add_more:
		print()
		_show_roster(team_obj.active)

		if len(team_obj.active) >= 11:
			ans = input("\nType 'y' to add another player, or Enter to finish: ").strip()
			if ans.lower() != 'y':
				break

		query = input("Player name to search (or Enter to cancel): ").strip()
		if not query:
			if len(team_obj.active) >= 11:
				break
			print('  You need at least 11 players.')
			continue

		exact   = [p for p in db if p.name == query]
		partial = [p for p in db if query.lower() in p.name.lower() and p not in exact]

		if exact:
			_pick_from_matches(team_obj, exact, db)
		elif partial:
			print(f'  No exact match. Did you mean: {listshow([p.name for p in partial])}')
		else:
			print('  Player not found.')

	# Persist the new team
	os.makedirs(os.path.dirname(CUSTOM_TEAMS_FILE), exist_ok=True)
	with open(CUSTOM_TEAMS_FILE, 'a') as f:
		f.write('\n')
		f.write(team_obj.name + '\n')
		for p in team_obj.active:
			f.write(playerwrite(p) + '\n')

	print(f'\n  Team "{team_obj.name}" saved ({len(team_obj.active)} players).')
	return team_obj


# ─── Entry point ──────────────────────────────────────────────────────────────

def getcustom(already_chosen=None):
	"""
	Ask the user to load or create a custom team and return it.

	already_chosen: list of team names already selected this session,
	                used to prevent picking the same saved team twice.
	"""
	if already_chosen is None:
		already_chosen = []

	while True:
		o = input("Type 'l' to load a saved custom team, "
				  "or 'n' to create a new one: ").strip().lower()
		if o in ('l', 'n'):
			break

	if o == 'l':
		t = team()
		result = load(t, already_chosen)
		if result is None:
			# Fall back to creating a new team if load failed
			print('Falling back to new team creation.')
			o = 'n'
		else:
			print()
			return result

	if o == 'n':
		while True:
			name = input('Team name: ').strip()
			if name:
				break
			print('  Name cannot be empty.')
		t = team()
		t.name = name
		make(t)

	print()
	return t


# ─── Standalone: play a series ────────────────────────────────────────────────

if __name__ == '__main__':
	chosen_names = []
	teams = []
	for _ in range(2):
		t = getcustom(already_chosen=chosen_names)
		teams.append(t)
		chosen_names.append(t.name)

	series(teams[0].name, teams[1].name, teams[0].active, teams[1].active)