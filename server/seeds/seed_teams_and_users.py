"""
Seeding order:
  1. sport_type        (inline, get-or-create)
  2. account_role      (inline, get-or-create)
  3. account  -> team_manager  -> TeamManagerTeam (association object)
  4. account  -> player        -> PlayerTeam      (association object)
  5. demo club + ladders
"""

import datetime
from werkzeug.security import generate_password_hash
from server.extensions import db
from server.app.models.availability_block import AvailabilityBlock
from server.app.models.sport_type import SportType
from server.app.models.account import Account, AccountRole
from server.app.models.club import Club
from server.app.models.club_owner import ClubOwner
from server.app.models.player import Player, PlayerTeam
from server.app.models.team import Team, TeamManager, TeamManagerTeam
from server.app.models.ladder import Ladder, LadderRatingFunction
from server.app.models.ladder_team import LadderTeam
from server.app.models.match import MatchAccepted, MatchCancelled, MatchProposal, MatchRejected, MatchStatus
from server.app.services.weekly_match_proposal_service import generate_weekly_match_proposals, next_week_start

TAG = "[seed:teams_and_users]"


# -- Helpers -------------------------------------------------------------------

def _log(msg: str, verbose: bool) -> None:
  if verbose:
    print(msg)


def _get_or_create_role(name: str, verbose: bool = True) -> AccountRole:
  role = AccountRole.query.filter_by(name=name).first()
  if role:
    _log(f"{TAG}   role '{name}' already exists (id={role.id}), skipping", verbose)
  else:
    role = AccountRole(name=name)
    db.session.add(role)
    db.session.flush()
    _log(f"{TAG}   role '{name}' created (id={role.id})", verbose)
  return role


def _get_or_create_sport(name: str, min_p: int, max_p: int, verbose: bool = True) -> SportType:
  sport = SportType.query.filter_by(name=name).first()
  if sport:
    _log(f"{TAG}   sport '{name}' already exists (id={sport.id}), skipping", verbose)
  else:
    sport = SportType(
      name=name,
      minimum_number_of_players_on_a_team=min_p,
      maximum_number_of_players_per_team=max_p,
    )
    db.session.add(sport)
    db.session.flush()
    _log(f"{TAG}   sport '{name}' created (id={sport.id}, min={min_p}, max={max_p})", verbose)
  return sport


def _make_account(
    first: str,
    last: str,
    email: str,
    role: AccountRole,
    password: str = "Password123!",
    force_password_update: bool = False,
) -> tuple:
  """Returns (account, created: bool)."""
  existing = Account.query.filter_by(email=email).first()
  if existing:
    if force_password_update:
      existing.password_hash = generate_password_hash(password)
    return existing, False
  acc = Account(
    first_name=first,
    last_name=last,
    email=email,
    password_hash=generate_password_hash(password),
    account_role_id=role.id,
    date_of_birth=datetime.date(1995, 1, 1),
    is_verified=True,
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


def _make_team(name: str, sport: SportType, club_id=None, verbose: bool = True) -> tuple:
  """Returns (team, created: bool)."""
  existing = Team.query.filter_by(name=name, club_id=club_id).first()
  if existing:
    _log(f"{TAG}   team '{name}' already exists (id={existing.id}), skipping", verbose)
    return existing, False
  team = Team(name=name, sport_type_id=sport.id, club_id=club_id)
  db.session.add(team)
  db.session.flush()
  _log(f"{TAG}   team '{name}' created (id={team.id}, sport={sport.name})", verbose)
  return team, True


def _get_or_create_club(name: str, sport_type_id: int | None = None) -> tuple:
  """Returns (club, created: bool)."""
  existing = Club.query.filter_by(name=name).first()
  if existing:
    return existing, False
  club = Club(name=name, description="test club", sport_type_id=sport_type_id, city="Antwerp")
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


def _assign_manager_to_team(
    tm: TeamManager,
    team: Team,
    can_rename: bool = True,
    can_delete: bool = True,
    can_edit_players: bool = True,
    can_edit_managers: bool = True,
) -> bool:
  """
  Creates a TeamManagerTeam association if it doesn't exist yet.
  Returns True if created, False if it already existed.

  NOTE: TeamManager.teams is a @property (read-only computed list).
  We must insert the association object directly — .append() does not work.
  """
  existing = TeamManagerTeam.query.filter_by(
    team_manager_id=tm.id, team_id=team.id
  ).first()
  if existing:
    return False
  assoc = TeamManagerTeam(
    team_manager_id=tm.id,
    team_id=team.id,
    can_rename=can_rename,
    can_delete=can_delete,
    can_edit_players=can_edit_players,
    can_edit_managers=can_edit_managers,
  )
  db.session.add(assoc)
  db.session.flush()
  return True


def _assign_player_to_team(player: Player, team: Team) -> bool:
  """
  Creates a PlayerTeam association if it doesn't exist yet.
  Returns True if created, False if it already existed.

  NOTE: Player.teams is a @property (read-only computed list).
  We must insert the association object directly — .append() does not work.
  """
  existing = PlayerTeam.query.filter_by(
    player_id=player.id, team_id=team.id
  ).first()
  if existing:
    return False
  assoc = PlayerTeam(player_id=player.id, team_id=team.id)
  db.session.add(assoc)
  db.session.flush()
  return True


def _ensure_default_ladder_rating_function() -> int:
  existing = LadderRatingFunction.query.order_by(LadderRatingFunction.id.asc()).first()
  if existing:
    return int(existing.id)
  created = LadderRatingFunction(name="ELO")
  db.session.add(created)
  db.session.flush()
  return int(created.id)


def _get_or_create_ladder(club_id, name, description, sport_type_id, ladder_rating_function_id) -> tuple:
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


def _get_or_create_ladder_team(ladder_id, team_id, rank, rating, matches_played) -> tuple:
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
  row = LadderTeam(ladder_id=ladder_id, team_id=team_id, rank=rank, rating=rating, matches_played=matches_played)
  db.session.add(row)
  db.session.flush()
  return row, True


def _get_or_create_availability_block(user_id: int, start_at: datetime.datetime, end_at: datetime.datetime) -> tuple:
  existing = AvailabilityBlock.query.filter_by(user_id=user_id, start_at=start_at, end_at=end_at).first()
  if existing:
    return existing, False
  block = AvailabilityBlock(user_id=user_id, start_at=start_at, end_at=end_at)
  db.session.add(block)
  db.session.flush()
  return block, True


def _reset_proposal_to_pending(week_start_date: datetime.date, team1_id: int, team2_id: int):
  ordered_team1_id, ordered_team2_id = sorted((team1_id, team2_id))
  proposal = MatchProposal.query.filter_by(
    week_start_date=week_start_date,
    team1_id=ordered_team1_id,
    team2_id=ordered_team2_id,
  ).first()
  if not proposal:
    return

  pending_status = MatchStatus.query.filter(MatchStatus.name.ilike("pending")).first()
  if pending_status:
    proposal.status_id = pending_status.id

  for model in (MatchAccepted, MatchRejected, MatchCancelled):
    row = db.session.get(model, proposal.id)
    if row:
      db.session.delete(row)
  db.session.flush()


# -- Main seed -----------------------------------------------------------------

def seed_teams_and_users(verbose: bool = True):
  _log(f"{TAG} Starting seed", verbose)

  # 1. Roles
  _log(f"{TAG} [1/6] Seeding account roles...", verbose)
  try:
    role_manager = _get_or_create_role("team_manager", verbose)
    role_player  = _get_or_create_role("player", verbose)
    _get_or_create_role("user", verbose)
  except Exception as e:
    print(f"{TAG} ERROR seeding roles: {e}")
    db.session.rollback()
    raise
  _log(f"{TAG} [1/6] Roles OK", verbose)

  # 2. Sport types
  _log(f"{TAG} [2/6] Seeding sport types...", verbose)
  try:
    football   = _get_or_create_sport("Football",   11, 23, verbose)
    basketball = _get_or_create_sport("Basketball",  5, 12, verbose)
    volleyball = _get_or_create_sport("Volleyball",  6, 14, verbose)
    tennis     = _get_or_create_sport("Tennis",      1,  4, verbose)
    hockey     = _get_or_create_sport("Hockey",     11, 22, verbose)
  except Exception as e:
    print(f"{TAG} ERROR seeding sport types: {e}")
    db.session.rollback()
    raise
  _log(f"{TAG} [2/6] Sport types OK", verbose)

  # 3. Teams
  _log(f"{TAG} [3/6] Seeding teams...", verbose)
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
      team, created = _make_team(name, sport, verbose=verbose)
      teams.append(team)
      if created:
        teams_created += 1
      else:
        teams_skipped += 1
  except Exception as e:
    print(f"{TAG} ERROR seeding teams: {e}")
    db.session.rollback()
    raise
  _log(f"{TAG} [3/6] Teams OK — created: {teams_created}, skipped: {teams_skipped}", verbose)

  # 4. Managers
  _log(f"{TAG} [4/6] Seeding managers...", verbose)
  MANAGERS = [
    ("Liam",    "Carter",     "liam.carter@example.com"),
    ("Noah",    "Brooks",     "noah.brooks@example.com"),
    ("Oliver",  "Hayes",      "oliver.hayes@example.com"),
    ("Elijah",  "Foster",     "elijah.foster@example.com"),
    ("James",   "Ward",       "james.ward@example.com"),
    ("Aiden",   "Cox",        "aiden.cox@example.com"),
    ("Lucas",   "Griffin",    "lucas.griffin@example.com"),
    ("Mason",   "Reed",       "mason.reed@example.com"),
    ("Ethan",   "Bell",       "ethan.bell@example.com"),
    ("Logan",   "Howard",     "logan.howard@example.com"),
    ("Jacob",   "Price",      "jacob.price@example.com"),
    ("Ryan",    "Barnes",     "ryan.barnes@example.com"),
    ("Daniel",  "Ross",       "daniel.ross@example.com"),
    ("Jack",    "Henderson",  "jack.henderson@example.com"),
    ("Owen",    "Coleman",    "owen.coleman@example.com"),
    ("Samuel",  "Jenkins",    "samuel.jenkins@example.com"),
    ("Wyatt",   "Perry",      "wyatt.perry@example.com"),
    ("Dylan",   "Powell",     "dylan.powell@example.com"),
    ("Caleb",   "Long",       "caleb.long@example.com"),
    ("Hunter",  "Patterson",  "hunter.patterson@example.com"),
    ("Evan",    "Hughes",     "evan.hughes@example.com"),
    ("Nathan",  "Flores",     "nathan.flores@example.com"),
    ("Connor",  "Washington", "connor.washington@example.com"),
    ("Luke",    "Butler",     "luke.butler@example.com"),
    ("Gavin",   "Simmons",    "gavin.simmons@example.com"),
  ]
  mgr_created = 0
  mgr_skipped = 0
  try:
    for i, (first, last, email) in enumerate(MANAGERS):
      team = teams[i]
      acc, acc_created = _make_account(first, last, email, role_manager)
      if not acc_created:
        _log(f"{TAG}   account '{email}' already exists (id={acc.id}), skipping", verbose)
        mgr_skipped += 1
        continue
      tm, tm_created = _make_manager(acc)
      if not tm_created:
        _log(f"{TAG}   team_manager for '{email}' already exists, skipping", verbose)
        mgr_skipped += 1
        continue
      assigned = _assign_manager_to_team(tm, team)
      if assigned:
        _log(f"{TAG}   manager {first} {last} (id={acc.id}) -> team '{team.name}' (id={team.id})", verbose)
      else:
        _log(f"{TAG}   manager {first} {last} already assigned to '{team.name}', skipping", verbose)
      mgr_created += 1
  except Exception as e:
    print(f"{TAG} ERROR seeding managers: {e}")
    db.session.rollback()
    raise
  _log(f"{TAG} [4/6] Managers OK — created: {mgr_created}, skipped: {mgr_skipped}", verbose)

  # 5. Players
  _log(f"{TAG} [5/6] Seeding players...", verbose)
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
        _log(f"{TAG}   account '{email}' already exists (id={acc.id}), skipping", verbose)
        plr_skipped += 1
        continue
      player, plr_ok = _make_player(acc)
      if not plr_ok:
        _log(f"{TAG}   player for '{email}' already exists, skipping", verbose)
        plr_skipped += 1
        continue
      assigned_names = []
      for idx in team_indices:
        if idx >= len(teams):
          print(f"{TAG}   WARNING: team index {idx} out of range, skipping")
          continue
        if _assign_player_to_team(player, teams[idx]):
          assigned_names.append(teams[idx].name)
      _log(f"{TAG}   player {first} {last} (id={acc.id}) -> teams: {assigned_names}", verbose)
      plr_created += 1
  except Exception as e:
    print(f"{TAG} ERROR seeding players: {e}")
    db.session.rollback()
    raise
  _log(f"{TAG} [5/6] Players OK — created: {plr_created}, skipped: {plr_skipped}", verbose)

  # 6. Demo club + ladders
  _log(f"{TAG} [6/6] Seeding demo club data...", verbose)
  try:
    demo_acc, demo_acc_created = _make_account(
      "Jeremi",
      "Lorek",
      "jeremilorek@outlook.com",
      role=role_manager,
      password="qwertyuiop",
      force_password_update=True,
    )
    _log(f"{TAG}   demo account {'created' if demo_acc_created else 'already exists'} (id={demo_acc.id})", verbose)
    if not demo_acc.is_verified:
      demo_acc.is_verified = True
      _log(f"{TAG}   demo account verification enabled", verbose)

    demo_tm, demo_tm_created = _make_manager(demo_acc)
    _log(f"{TAG}   demo team_manager {'created' if demo_tm_created else 'already exists'} (id={demo_tm.id})", verbose)

    demo_owner, demo_owner_created = _make_club_owner(demo_tm)
    _log(f"{TAG}   demo club_owner {'created' if demo_owner_created else 'already exists'} (id={demo_owner.id})", verbose)

    demo_club, demo_club_created = _get_or_create_club("NetRank Club", sport_type_id=tennis.id)
    _log(f"{TAG}   demo club {'created' if demo_club_created else 'already exists'} (id={demo_club.id})", verbose)

    if demo_club not in demo_owner.clubs:
      demo_owner.clubs.append(demo_club)
      _log(f"{TAG}   linked owner {demo_owner.id} -> club {demo_club.id}", verbose)

    men_team,    _ = _make_team("NetRank Aces",    tennis, club_id=demo_club.id, verbose=verbose)
    junior_team, _ = _make_team("NetRank Juniors", tennis, club_id=demo_club.id, verbose=verbose)

    _assign_manager_to_team(demo_tm, men_team)
    _assign_manager_to_team(demo_tm, junior_team)

    rating_fn_id = _ensure_default_ladder_rating_function()
    men_ladder,    _ = _get_or_create_ladder(demo_club.id, "Men's Singles", "Demo ladder for men's singles", tennis.id, rating_fn_id)
    junior_ladder, _ = _get_or_create_ladder(demo_club.id, "U14 Singles",   "Demo ladder for U14 singles",   tennis.id, rating_fn_id)

    _get_or_create_ladder_team(men_ladder.id,    men_team.id,    rank=1, rating=1260, matches_played=15)
    _get_or_create_ladder_team(men_ladder.id,    junior_team.id, rank=2, rating=1180, matches_played=12)
    _get_or_create_ladder_team(junior_ladder.id, junior_team.id, rank=1, rating=1215, matches_played=10)
    _get_or_create_ladder_team(junior_ladder.id, men_team.id,    rank=2, rating=1100, matches_played=8)
    _log(f"{TAG}   demo ladder standings upserted", verbose)

    demo_week_start = next_week_start()
    avail_start = datetime.datetime.combine(
      demo_week_start + datetime.timedelta(days=1),
      datetime.time(hour=18, minute=0),
    )
    avail_end = avail_start + datetime.timedelta(hours=2)

    player_demo_club, _ = _get_or_create_club("Player Demo Club", sport_type_id=tennis.id)
    player_demo_a, _ = _make_team("Player Demo A", tennis, club_id=player_demo_club.id, verbose=verbose)
    player_demo_b, _ = _make_team("Player Demo B", tennis, club_id=player_demo_club.id, verbose=verbose)

    player_demo_ladder, _ = _get_or_create_ladder(
      player_demo_club.id,
      "Player Demo Singles",
      "Demo ladder where Jeremi is only a player",
      tennis.id,
      rating_fn_id,
    )
    _get_or_create_ladder_team(player_demo_ladder.id, player_demo_a.id, rank=1, rating=1110, matches_played=3)
    _get_or_create_ladder_team(player_demo_ladder.id, player_demo_b.id, rank=2, rating=1090, matches_played=3)

    demo_player, _ = _make_player(demo_acc)
    _assign_player_to_team(demo_player, player_demo_a)

    opponent_acc, _ = _make_account("Robin", "Vermeulen", "robin.vermeulen@example.com", role_player)
    opponent_player, _ = _make_player(opponent_acc)
    _assign_player_to_team(opponent_player, player_demo_b)

    _get_or_create_availability_block(demo_acc.id, avail_start, avail_end)
    _get_or_create_availability_block(
      opponent_acc.id,
      avail_start + datetime.timedelta(minutes=30),
      avail_end,
    )

    generation_result = generate_weekly_match_proposals(
      proposed_by_user_id=demo_acc.id,
      week_start_date=demo_week_start,
      ladder_id=player_demo_ladder.id,
      managed_team_ids=None,
      duration_minutes=60,
      location="Player Demo Court 1",
    )
    _reset_proposal_to_pending(
      week_start_date=demo_week_start,
      team1_id=player_demo_a.id,
      team2_id=player_demo_b.id,
    )
    _log(
      f"{TAG}   player-demo weekly proposals generated: "
      f"created={generation_result['created_count']}, skipped={generation_result['skipped_count']}",
      verbose,
    )

  except Exception as e:
    print(f"{TAG} ERROR seeding demo club data: {e}")
    db.session.rollback()
    raise
  _log(f"{TAG} [6/6] Demo club data OK", verbose)

  # Commit
  _log(f"{TAG} Committing to database...", verbose)
  try:
    db.session.commit()
  except Exception as e:
    print(f"{TAG} ERROR during commit: {e}")
    db.session.rollback()
    raise

  print(f"{TAG} Seed complete — teams: {teams_created}/{teams_created + teams_skipped}, managers: {mgr_created}/{mgr_created + mgr_skipped}, players: {plr_created}/{plr_created + plr_skipped}")
