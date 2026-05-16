import os
from custom import getcustom
from game import setup, game
from altcricket import seri, statsdump

SCORECARDS_FOLDER = 'scorecards'


# ─── Standings helpers ────────────────────────────────────────────────────────

def make_standings(teams):
	"""Return a fresh standings dict keyed by team name."""
	return {
		t.name: {'played': 0, 'wins': 0, 'draws': 0, 'losses': 0}
		for t in teams
	}


def update_standings(standings, game_result):
	"""Update standings in-place after a completed game."""
	home = game_result.home.name
	away = game_result.away.name
	win  = game_result.win

	for name in (home, away):
		standings[name]['played'] += 1
		if win in ('Draw', 'Tie'):
			standings[name]['draws'] += 1
		elif win.name == name:
			standings[name]['wins'] += 1
		else:
			standings[name]['losses'] += 1


def sort_standings(standings):
	"""Return standings rows sorted by wins desc, then draws as tiebreaker."""
	return sorted(
		standings.items(),
		key=lambda item: item[1]['wins'] + item[1]['draws'] / 1000,
		reverse=True,
	)


def print_standings(standings, header=None):
	"""Print a formatted standings table."""
	if header:
		print(header)
	print()
	width = max(len(name) for name in standings) + 2
	print(f"  {'Team':<{width}} {'P':>4} {'W':>4} {'D':>4} {'L':>4}")
	print(f"  {'─' * width} {'─':>4} {'─':>4} {'─':>4} {'─':>4}")
	for name, row in sort_standings(standings):
		print(f"  {name:<{width}} {row['played']:>4} {row['wins']:>4} "
			  f"{row['draws']:>4} {row['losses']:>4}")
	print()


# ─── League runner ────────────────────────────────────────────────────────────

def league(teams, rounds):
	"""
	Run a round-robin league.

	teams  — list of team objects (each with .name and .active)
	rounds — how many times each pair plays each other
	"""
	# ── Set up scorecards folder ──
	os.makedirs(SCORECARDS_FOLDER, exist_ok=True)
	for f in os.listdir(SCORECARDS_FOLDER):
		os.remove(os.path.join(SCORECARDS_FOLDER, f))

	# ── Initialise series tracker ──
	# seri.__init__ has a known bug where it assigns to local variables
	# instead of self, leaving all lists at class level.  Explicitly reset
	# every list as an instance attribute here.
	s = seri()
	s.results = []
	s.inns    = []
	s.bowls   = []
	s.players = []
	for t in teams:
		s.players.extend(t.active)

	standings = make_standings(teams)
	game_number = 1

	for round_num in range(1, rounds + 1):
		print()
		print('═' * 60)
		if rounds > 1:
			print(f'  Round {round_num} of {rounds}')
		else:
			print('  League fixtures')
		print('═' * 60)

		for home in teams:
			for away in teams:
				if away is home:
					continue

				print()
				g = setup(home.name, away.name)
				g.home.active = home.active
				g.away.active = away.active
				g.no = game_number

				result = game(g)

				s.results.append(result)
				s.inns.extend(result.inns)
				s.bowls.extend(result.bowls)
				game_number += 1

				update_standings(standings, result)
				print_standings(standings)

	# ── Full results ──
	print()
	print('═' * 60)
	print('  All results')
	print('═' * 60)
	print()
	for r in s.results:
		r.gamedesc()

	# ── Final standings ──
	print_standings(standings, header='\n  Final standings')

	# ── Batting summary ──
	s.players.sort(key=lambda p: p.runs, reverse=True)
	print('  Top run-scorers:')
	for p in s.players:
		if p.batav > 50 or p in s.players[:10]:
			print(f'    {p.name} ({p.team})  {p.runs} runs @ {p.batav}', end=',  ')
	print()
	print()

	# ── Bowling summary ──
	s.players.sort(key=lambda p: p.wickets, reverse=True)
	print('  Top wicket-takers:')
	for p in s.players:
		if (p.bowlav < 25 and p.wickets > 10) or p in s.players[:10]:
			print(f'    {p.name} ({p.team})  {p.wickets} wkts @ {p.bowlav}', end=',  ')
	print()
	print()

	# ── Man of the series ──
	def mots_score(p):
		team_wins = standings.get(p.team, {}).get('wins', 0)
		return 20 * p.wickets + p.runs + 100 * team_wins

	s.players.sort(key=mots_score, reverse=True)
	print(f'  Man of the series: {s.players[0].name} ({s.players[0].team})')
	print()

	statsdump(s.players, s.inns, s.bowls, SCORECARDS_FOLDER)


# ─── Input helpers ────────────────────────────────────────────────────────────

def get_int(prompt, lo=None, hi=None):
	"""Prompt until the user enters a valid integer within [lo, hi]."""
	while True:
		raw = input(prompt).strip()
		try:
			n = int(raw)
		except ValueError:
			print('  Please enter a whole number.')
			continue
		if lo is not None and n < lo:
			print(f'  Must be at least {lo}.')
			continue
		if hi is not None and n > hi:
			print(f'  Must be at most {hi}.')
			continue
		return n


def teamnumber():
	return get_int('Number of teams in league (minimum 2): ', lo=2)


def gamenumber():
	return get_int('How many times should each pair play? (minimum 1): ', lo=1)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
	print('Custom League')
	print()

	num_teams = teamnumber()
	teams = []
	for i in range(num_teams):
		print(f'\n  Select team {i + 1} of {num_teams}')
		t = getcustom(already_chosen=[team.name for team in teams])
		teams.append(t)

	rounds = gamenumber()

	league(teams, rounds)