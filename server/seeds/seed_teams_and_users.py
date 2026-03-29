"""
Seeding order:
  1. sport_type        (if not present)
  2. account_role      (if not present)
  3. account            team_manager  -> team  -> team_manager_team
  4. account           -> player        -> player_team
"""

import datetime
from sqlalchemy import text
from werkzeug.security import generate_password_hash
from server.extensions import db
from server.app.models.sport_type import SportType
from server.app.models.account import Account, AccountRole, TeamManager, Player, ClubOwner
from server.app.models.club import Club
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
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


def _get_or_create_club(name: str) -> tuple:
  """Returns (club, created: bool)."""
  existing = Club.query.filter_by(name=name).first()
  if existing:
    return existing, False
  club = Club(name=name)
  db.session.add(club)
  db.session.flush()
  return club, True


def _make_club_owner(team_manager: TeamManager) -> tuple:
  """Returns (club_owner, created: bool)."""
  if team_manager.club_owner:
    return team_manager.club_owner, False
  owner = ClubOwner(id=team_manager.id)
  db.session.add(owner)
  db.session.flush()
  return owner, True


def _ensure_default_ladder_rating_function() -> int:
  """
  Ensures there is at least one ladder rating function row and returns its id.
  Uses SQL directly because there is no ORM model for this table.
  """
  existing_id = db.session.execute(
    text("SELECT id FROM ladder_rating_function ORDER BY id ASC LIMIT 1")
  ).scalar()
  if existing_id:
    return int(existing_id)

  created_id = db.session.execute(
    text("INSERT INTO ladder_rating_function (name) VALUES (:name) RETURNING id"),
    {"name": "ELO"},
  ).scalar_one()
  return int(created_id)


def _get_or_create_ladder(
  club_id: int,
  name: str,
  description: str,
  sport_type_id: int,
  ladder_rating_function_id: int,
) -> tuple:
  """Returns (ladder, created: bool)."""
  existing = Ladder.query.filter_by(club_id=club_id, name=name).first()
  if existing:
    return existing, False

  ladder = Ladder(
    club_id=club_id,
    name=name,
    description=description,
    sport_type_id=sport_type_id,
    ruleset_id=None,
    ladder_rating_function_id=ladder_rating_function_id,
  )
  db.session.add(ladder)
  db.session.flush()
  return ladder, True


def _get_or_create_ladder_team(
  ladder_id: int,
  team_id: int,
  rank: int,
  rating: int,
  matches_played: int,
) -> tuple:
  """Returns (ladder_team, created: bool)."""
  existing = LadderTeam.query.filter_by(ladder_id=ladder_id, team_id=team_id).first()
  if existing:
    updated = False
    if existing.rank != rank:
      existing.rank = rank
      updated = True
    if existing.rating != rating:
      existing.rating = rating
      updated = True
    if existing.matches_played != matches_played:
      existing.matches_played = matches_played
      updated = True
    return existing, updated

  row = LadderTeam(
    ladder_id=ladder_id,
    team_id=team_id,
    rank=rank,
    rating=rating,
    matches_played=matches_played,
  )
  db.session.add(row)
  db.session.flush()
  return row, True


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

  #  Demo club + ladders
  print(f"{TAG} [6/6] Seeding demo club data...")
  try:
    demo_acc, demo_acc_created = _make_account(
      first="Nora",
      last="Clubowner",
      email="nora.clubowner@netrank.demo",
      role=role_manager,
    )
    if demo_acc_created:
      print(f"{TAG}   demo account created (id={demo_acc.id}, email={demo_acc.email})")
    else:
      print(f"{TAG}   demo account already exists (id={demo_acc.id}), skipping")

    demo_tm, demo_tm_created = _make_manager(demo_acc)
    if demo_tm_created:
      print(f"{TAG}   demo team_manager created (id={demo_tm.id})")
    else:
      print(f"{TAG}   demo team_manager already exists (id={demo_tm.id}), skipping")

    demo_owner, demo_owner_created = _make_club_owner(demo_tm)
    if demo_owner_created:
      print(f"{TAG}   demo club_owner created (id={demo_owner.id})")
    else:
      print(f"{TAG}   demo club_owner already exists (id={demo_owner.id}), skipping")

    demo_club, demo_club_created = _get_or_create_club("NetRank Club")
    if demo_club_created:
      print(f"{TAG}   demo club created (id={demo_club.id}, name='{demo_club.name}')")
    else:
      print(f"{TAG}   demo club already exists (id={demo_club.id}), skipping")

    if demo_club not in demo_owner.clubs:
      demo_owner.clubs.append(demo_club)
      print(f"{TAG}   linked owner {demo_owner.id} -> club {demo_club.id}")
    else:
      print(f"{TAG}   owner {demo_owner.id} already linked to club {demo_club.id}, skipping")

    men_team, men_team_created = _make_team("NetRank Aces", tennis, club_id=demo_club.id)
    if men_team_created:
      print(f"{TAG}   team '{men_team.name}' created in demo club")
    else:
      print(f"{TAG}   team '{men_team.name}' already exists in demo club, skipping")

    junior_team, junior_team_created = _make_team("NetRank Juniors", tennis, club_id=demo_club.id)
    if junior_team_created:
      print(f"{TAG}   team '{junior_team.name}' created in demo club")
    else:
      print(f"{TAG}   team '{junior_team.name}' already exists in demo club, skipping")

    if men_team not in demo_tm.teams:
      demo_tm.teams.append(men_team)
      print(f"{TAG}   manager {demo_tm.id} assigned to '{men_team.name}'")
    if junior_team not in demo_tm.teams:
      demo_tm.teams.append(junior_team)
      print(f"{TAG}   manager {demo_tm.id} assigned to '{junior_team.name}'")

    rating_fn_id = _ensure_default_ladder_rating_function()
    men_ladder, men_ladder_created = _get_or_create_ladder(
      club_id=demo_club.id,
      name="Men's Singles",
      description="Demo ladder for men's singles",
      sport_type_id=tennis.id,
      ladder_rating_function_id=rating_fn_id,
    )
    if men_ladder_created:
      print(f"{TAG}   ladder '{men_ladder.name}' created")
    else:
      print(f"{TAG}   ladder '{men_ladder.name}' already exists, skipping")

    junior_ladder, junior_ladder_created = _get_or_create_ladder(
      club_id=demo_club.id,
      name="U14 Singles",
      description="Demo ladder for U14 singles",
      sport_type_id=tennis.id,
      ladder_rating_function_id=rating_fn_id,
    )
    if junior_ladder_created:
      print(f"{TAG}   ladder '{junior_ladder.name}' created")
    else:
      print(f"{TAG}   ladder '{junior_ladder.name}' already exists, skipping")

    _get_or_create_ladder_team(
      ladder_id=men_ladder.id,
      team_id=men_team.id,
      rank=1,
      rating=1260,
      matches_played=15,
    )
    _get_or_create_ladder_team(
      ladder_id=men_ladder.id,
      team_id=junior_team.id,
      rank=2,
      rating=1180,
      matches_played=12,
    )
    _get_or_create_ladder_team(
      ladder_id=junior_ladder.id,
      team_id=junior_team.id,
      rank=1,
      rating=1215,
      matches_played=10,
    )
    _get_or_create_ladder_team(
      ladder_id=junior_ladder.id,
      team_id=men_team.id,
      rank=2,
      rating=1100,
      matches_played=8,
    )
    print(f"{TAG}   demo ladder standings upserted")

  except Exception as e:
    print(f"{TAG} ERROR seeding demo club data: {e}")
    db.session.rollback()
    raise

  print(f"{TAG} [6/6] Demo club data OK")

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
