"""
Seeding order:
  1. sport_type        (if not present)
  2. account_role      (if not present)
  3. account            team_manager  -> team  -> team_manager_team
  4. account           -> player        -> player_team
"""

import datetime
from werkzeug.security import generate_password_hash
from server.extensions import db
from server.app.models.sport_type import SportType
from server.app.models.account import Account, TeamManager
from server.app.models.account_role import AccountRole
from server.app.models.player import Player
from server.app.models.team import Team

TAG = "[seed:teams_and_users]"


#  Helpers 

def _get_or_create_role(name: str) -> AccountRole:
  role = AccountRole.query.filter_by(name=name).first()
  if role:
    print(f"{TAG}   role '{name}' already exists (id={role.id}), skipping")
  else:
    role = AccountRole(name=name)
    db.session.add(role)
    db.session.flush()
    print(f"{TAG}   role '{name}' created (id={role.id})")
  return role


def _get_or_create_sport(name: str, min_p: int, max_p: int) -> SportType:
  sport = SportType.query.filter_by(name=name).first()
  if sport:
    print(f"{TAG}   sport '{name}' already exists (id={sport.id}), skipping")
  else:
    sport = SportType(
      name=name,
      minimum_number_of_players_on_a_team=min_p,
      maximum_number_of_players_per_team=max_p,
    )
    db.session.add(sport)
    db.session.flush()
    print(f"{TAG}   sport '{name}' created (id={sport.id}, min={min_p}, max={max_p})")
  return sport


def _make_account(first: str, last: str, email: str, role: AccountRole) -> tuple:
  """Returns (account, created: bool)."""
  existing = Account.query.filter_by(email=email).first()
  if existing:
    return existing, False
  acc = Account(
    first_name=first,
    last_name=last,
    email=email,
    password_hash=generate_password_hash("Password123!"),
    account_role_id=role.id,
    date_of_birth=datetime.date(1995, 1, 1),
  )
  db.session.add(acc)
  db.session.flush()
  return acc, True


def _make_manager(account: Account) -> tuple:
  """Returns (team_manager, created: bool)."""
  if account.team_manager:
    return account.team_manager, False
  tm = TeamManager(id=account.id)
  db.session.add(tm)
  db.session.flush()
  return tm, True


def _make_player(account: Account) -> tuple:
  """Returns (player, created: bool)."""
  if account.player:
    return account.player, False
  p = Player(id=account.id)
  db.session.add(p)
  db.session.flush()
  return p, True


def _make_team(name: str, sport: SportType, club_id=None) -> tuple:
  """Returns (team, created: bool)."""
  existing = Team.query.filter_by(name=name, club_id=club_id).first()
  if existing:
    return existing, False
  team = Team(name=name, sport_type_id=sport.id, club_id=club_id)
  db.session.add(team)
  db.session.flush()
  return team, True


#  Main seed 

def seed_teams_and_users():
  print(f"{TAG}  Starting seed ")

  #  Roles
  print(f"{TAG} [1/5] Seeding account roles...")
  try:
    role_manager = _get_or_create_role("team_manager")
    role_player  = _get_or_create_role("player")
    _get_or_create_role("user")
  except Exception as e:
    print(f"{TAG} ERROR seeding roles: {e}")
    db.session.rollback()
    raise
  print(f"{TAG} [1/5] Roles OK")

  #  Sport types
  print(f"{TAG} [2/5] Seeding sport types...")
  try:
    football   = _get_or_create_sport("Football",   11, 23)
    basketball = _get_or_create_sport("Basketball",  5, 12)
    volleyball = _get_or_create_sport("Volleyball",  6, 14)
    tennis     = _get_or_create_sport("Tennis",      1,  4)
    hockey     = _get_or_create_sport("Hockey",     11, 22)
  except Exception as e:
    print(f"{TAG} ERROR seeding sport types: {e}")
    db.session.rollback()
    raise
  print(f"{TAG} [2/5] Sport types OK")

  #  Teams
  print(f"{TAG} [3/5] Seeding teams...")

  TEAMS = [
    ("Red Hawks",         football),
    ("Blue Thunder",      football),
    ("Iron Wolves",       football),
    ("Golden Eagles",     football),
    ("Storm Riders",      football),
    ("Fast Breaks",       basketball),
    ("Sky Dunkers",       basketball),
    ("Net Crushers",      volleyball),
    ("Sand Smashers",     volleyball),
    ("Ace Spikers",       volleyball),
    ("Court Kings",       tennis),
    ("Baseline Bruisers", tennis),
    ("Ice Foxes",         hockey),
    ("Puck Predators",    hockey),
    ("Slap Shot Stars",   hockey),
    ("Neon Ninjas",       basketball),
    ("Turbo Falcons",     football),
    ("Cyber Strikers",    football),
    ("Phantom Eleven",    football),
    ("Desert Hawks",      football),
    ("Arctic Bears",      hockey),
    ("Urban Wolves",      football),
    ("Steel Tigers",      football),
    ("Velocity FC",       football),
    ("Rapid Rovers",      football),
  ]

  teams = []
  teams_created = 0
  teams_skipped = 0

  try:
    for name, sport in TEAMS:
      team, created = _make_team(name, sport)
      teams.append(team)
      if created:
        teams_created += 1
        print(f"{TAG}   team '{name}' created (id={team.id}, sport={sport.name})")
      else:
        teams_skipped += 1
        print(f"{TAG}   team '{name}' already exists (id={team.id}), skipping")
  except Exception as e:
    print(f"{TAG} ERROR seeding teams: {e}")
    db.session.rollback()
    raise

  print(f"{TAG} [3/5] Teams OK — created: {teams_created}, skipped: {teams_skipped}")

  #  Managers
  print(f"{TAG} [4/5] Seeding managers...")

  MANAGERS = [
    ("Liam",    "Carter",    "liam.carter@example.com"),
    ("Noah",    "Brooks",    "noah.brooks@example.com"),
    ("Oliver",  "Hayes",     "oliver.hayes@example.com"),
    ("Elijah",  "Foster",    "elijah.foster@example.com"),
    ("James",   "Ward",      "james.ward@example.com"),
    ("Aiden",   "Cox",       "aiden.cox@example.com"),
    ("Lucas",   "Griffin",   "lucas.griffin@example.com"),
    ("Mason",   "Reed",      "mason.reed@example.com"),
    ("Ethan",   "Bell",      "ethan.bell@example.com"),
    ("Logan",   "Howard",    "logan.howard@example.com"),
    ("Jacob",   "Price",     "jacob.price@example.com"),
    ("Ryan",    "Barnes",    "ryan.barnes@example.com"),
    ("Daniel",  "Ross",      "daniel.ross@example.com"),
    ("Jack",    "Henderson", "jack.henderson@example.com"),
    ("Owen",    "Coleman",   "owen.coleman@example.com"),
    ("Samuel",  "Jenkins",   "samuel.jenkins@example.com"),
    ("Wyatt",   "Perry",     "wyatt.perry@example.com"),
    ("Dylan",   "Powell",    "dylan.powell@example.com"),
    ("Caleb",   "Long",      "caleb.long@example.com"),
    ("Hunter",  "Patterson", "hunter.patterson@example.com"),
    ("Evan",    "Hughes",    "evan.hughes@example.com"),
    ("Nathan",  "Flores",    "nathan.flores@example.com"),
    ("Connor",  "Washington","connor.washington@example.com"),
    ("Luke",    "Butler",    "luke.butler@example.com"),
    ("Gavin",   "Simmons",   "gavin.simmons@example.com"),
  ]

  mgr_created = 0
  mgr_skipped = 0

  try:
    for i, (first, last, email) in enumerate(MANAGERS):
      team = teams[i]

      acc, acc_created = _make_account(first, last, email, role_manager)
      if not acc_created:
        print(f"{TAG}   account '{email}' already exists (id={acc.id}), skipping")
        mgr_skipped += 1
        continue

      tm, tm_created = _make_manager(acc)
      if not tm_created:
        print(f"{TAG}   team_manager for '{email}' already exists, skipping")
        mgr_skipped += 1
        continue

      if team not in tm.teams:
        tm.teams.append(team)
        print(f"{TAG}   manager {first} {last} (id={acc.id}) -> team '{team.name}' (id={team.id})")
      else:
        print(f"{TAG}   manager {first} {last} already assigned to '{team.name}', skipping")

      mgr_created += 1

  except Exception as e:
    print(f"{TAG} ERROR seeding managers: {e}")
    db.session.rollback()
    raise

  print(f"{TAG} [4/5] Managers OK — created: {mgr_created}, skipped: {mgr_skipped}")

  #  Players
  print(f"{TAG} [5/5] Seeding players...")

  PLAYERS = [
    ("Alice",  "Moore",     "alice.moore@example.com",     [0, 1]),
    ("Bob",    "Taylor",    "bob.taylor@example.com",      [0, 2]),
    ("Carol",  "Anderson",  "carol.anderson@example.com",  [1, 3]),
    ("Dave",   "Thomas",    "dave.thomas@example.com",     [1, 4]),
    ("Eve",    "Jackson",   "eve.jackson@example.com",     [2, 5]),
    ("Frank",  "White",     "frank.white@example.com",     [2, 6]),
    ("Grace",  "Harris",    "grace.harris@example.com",    [3, 7]),
    ("Henry",  "Martin",    "henry.martin@example.com",    [3, 8]),
    ("Iris",   "Garcia",    "iris.garcia@example.com",     [4, 9]),
    ("Jake",   "Martinez",  "jake.martinez@example.com",   [4, 10]),
    ("Karen",  "Robinson",  "karen.robinson@example.com",  [5, 11]),
    ("Leo",    "Clark",     "leo.clark@example.com",       [5, 12]),
    ("Mia",    "Rodriguez", "mia.rodriguez@example.com",   [6, 13]),
    ("Nick",   "Lewis",     "nick.lewis@example.com",      [6, 14]),
    ("Olivia", "Lee",       "olivia.lee@example.com",      [7, 15]),
    ("Paul",   "Walker",    "paul.walker@example.com",     [7, 16]),
    ("Quinn",  "Hall",      "quinn.hall@example.com",      [8, 17]),
    ("Rachel", "Allen",     "rachel.allen@example.com",    [8, 18]),
    ("Steve",  "Young",     "steve.young@example.com",     [9, 19]),
    ("Tina",   "Hernandez", "tina.hernandez@example.com",  [9, 20]),
    ("Uma",    "King",      "uma.king@example.com",        [10, 21]),
    ("Victor", "Wright",    "victor.wright@example.com",   [10, 22]),
    ("Wendy",  "Lopez",     "wendy.lopez@example.com",     [11, 23]),
    ("Xander", "Hill",      "xander.hill@example.com",     [11, 24]),
    ("Yara",   "Scott",     "yara.scott@example.com",      [12, 0]),
    ("Zack",   "Green",     "zack.green@example.com",      [12, 1]),
    ("Amy",    "Adams",     "amy.adams@example.com",       [13, 2]),
    ("Brian",  "Baker",     "brian.baker@example.com",     [13, 3]),
    ("Cindy",  "Nelson",    "cindy.nelson@example.com",    [14, 4]),
    ("Derek",  "Carter",    "derek.dcarter@example.com",   [14, 5]),
    ("Ella",   "Mitchell",  "ella.mitchell@example.com",   [15, 6]),
    ("Felix",  "Perez",     "felix.perez@example.com",     [15, 7]),
    ("Gina",   "Roberts",   "gina.roberts@example.com",    [16, 8]),
    ("Hank",   "Turner",    "hank.turner@example.com",     [16, 9]),
    ("Isla",   "Phillips",  "isla.phillips@example.com",   [17, 10]),
    ("Jason",  "Campbell",  "jason.campbell@example.com",  [17, 11]),
    ("Kim",    "Parker",    "kim.parker@example.com",      [18, 12]),
    ("Lars",   "Evans",     "lars.evans@example.com",      [18, 13]),
    ("Maya",   "Edwards",   "maya.edwards@example.com",    [19, 14]),
    ("Nate",   "Collins",   "nate.collins@example.com",    [19, 15]),
  ]

  plr_created = 0
  plr_skipped = 0

  try:
    for first, last, email, team_indices in PLAYERS:
      acc, acc_created = _make_account(first, last, email, role_player)
      if not acc_created:
        print(f"{TAG}   account '{email}' already exists (id={acc.id}), skipping")
        plr_skipped += 1
        continue

      player, plr_ok = _make_player(acc)
      if not plr_ok:
        print(f"{TAG}   player for '{email}' already exists, skipping")
        plr_skipped += 1
        continue

      assigned = []
      for idx in team_indices:
        if idx >= len(teams):
          print(f"{TAG}   WARNING: team index {idx} out of range, skipping")
          continue
        if teams[idx] not in player.teams:
          player.teams.append(teams[idx])
          assigned.append(teams[idx].name)

      print(f"{TAG}   player {first} {last} (id={acc.id}) -> teams: {assigned}")
      plr_created += 1

  except Exception as e:
    print(f"{TAG} ERROR seeding players: {e}")
    db.session.rollback()
    raise

  print(f"{TAG} [5/5] Players OK — created: {plr_created}, skipped: {plr_skipped}")

  #  Commit
  print(f"{TAG} Committing to database...")
  try:
    db.session.commit()
  except Exception as e:
    print(f"{TAG} ERROR during commit: {e}")
    db.session.rollback()
    raise

  print(f"{TAG}  Seed complete ")
  print(f"{TAG}    teams:    created={teams_created}, skipped={teams_skipped}")
  print(f"{TAG}    managers: created={mgr_created},  skipped={mgr_skipped}")
  print(f"{TAG}    players:  created={plr_created},  skipped={plr_skipped}")
  print(f"{TAG} ")