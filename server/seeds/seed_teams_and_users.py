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
from server.app.models.account import Account, TeamManager
from server.app.models.account_role import AccountRole
from server.app.models.club import Club
from server.app.models.club_player import ClubPlayer
from server.app.models.club_owner import ClubOwner
from server.app.models.club_owner_club import ClubOwnerClub
from server.app.models.player import Player, PlayerTeam
from server.app.models.team import Team, TeamManager, TeamManagerTeam
from server.app.models.ladder import Ladder, LadderRatingFunction
from server.app.models.ladder_team import LadderTeam
from server.app.models.match import MatchAccepted, MatchCancelled, MatchProposal, MatchRejected, MatchStatus
from server.app.services.weekly_match_proposal_service import generate_weekly_match_proposals, next_week_start

TAG = "[seed:teams_and_users]"


# -- Helpers -------------------------------------------------------------------

def log(msg: str, verbose: bool) -> None:
  if verbose:
    print(msg)


def get_or_create_role(name: str, verbose: bool = True) -> AccountRole:
  role = AccountRole.query.filter_by(name=name).first()
  if role:
    log(f"{TAG}   role '{name}' already exists (id={role.id}), skipping", verbose)
  else:
    role = AccountRole(name=name)
    db.session.add(role)
    db.session.flush()
    log(f"{TAG}   role '{name}' created (id={role.id})", verbose)
  return role


def get_or_create_sport(name: str, min_p: int, max_p: int, verbose: bool = True) -> SportType:
  sport = SportType.query.filter_by(name=name).first()
  if sport:
    log(f"{TAG}   sport '{name}' already exists (id={sport.id}), skipping", verbose)
  else:
    sport = SportType(
      name=name,
      minimum_number_of_players_on_a_team=min_p,
      maximum_number_of_players_per_team=max_p,
    )
    db.session.add(sport)
    db.session.flush()
    log(f"{TAG}   sport '{name}' created (id={sport.id}, min={min_p}, max={max_p})", verbose)
  return sport


def make_account(
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


def make_manager(account: Account) -> tuple:
  """Returns (team_manager, created: bool)."""
  if account.team_manager:
    return account.team_manager, False
  tm = TeamManager(id=account.id)
  db.session.add(tm)
  db.session.flush()
  return tm, True


def make_player(account: Account) -> tuple:
  """Returns (player, created: bool)."""
  if account.player:
    return account.player, False
  p = Player(id=account.id)
  db.session.add(p)
  db.session.flush()
  return p, True


def make_team(name: str, sport: SportType, club_id=None, verbose: bool = True) -> tuple:
  """Returns (team, created: bool)."""
  existing = Team.query.filter_by(name=name, club_id=club_id).first()
  if existing:
    log(f"{TAG}   team '{name}' already exists (id={existing.id}), skipping", verbose)
    return existing, False
  team = Team(name=name, sport_type_id=sport.id, club_id=club_id)
  db.session.add(team)
  db.session.flush()
  log(f"{TAG}   team '{name}' created (id={team.id}, sport={sport.name})", verbose)
  return team, True


def get_or_create_club(name: str, sport_type_id: int | None = None) -> tuple:
  """Returns (club, created: bool)."""
  existing = Club.query.filter_by(name=name).first()
  if existing:
    return existing, False
  club = Club(name=name, description="test club", sport_type_id=sport_type_id, city="Antwerp")
  db.session.add(club)
  db.session.flush()
  return club, True


def make_club_owner(team_manager: TeamManager) -> tuple:
  """Returns (club_owner, created: bool)."""
  if team_manager.club_owner:
    return team_manager.club_owner, False
  owner = ClubOwner(id=team_manager.id)
  db.session.add(owner)
  db.session.flush()
  return owner, True


def ensure_owner_of_club(club_owner: ClubOwner, club: Club) -> bool:
  existing = ClubOwnerClub.query.filter_by(club_owner_id=club_owner.id, club_id=club.id).first()
  if existing:
    return False
  db.session.add(
    ClubOwnerClub(
      club_owner_id=club_owner.id,
      club_id=club.id,
      can_rename=True,
      can_change_description=True,
      can_manage_match=True,
      can_add_club_players=True,
      can_add_club_owners=True,
      can_add_club_rule=True,
    )
  )
  db.session.flush()
  return True


def assign_manager_to_team(
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


def assign_player_to_team(player: Player, team: Team) -> bool:
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


def ensure_player_on_team(account: Account, team: Team) -> bool:
  player, _ = make_player(account)
  return assign_player_to_team(player, team)


def ensure_team_players_in_club(team: Team, club: Club) -> int:
  created = 0
  player_ids = [row.player_id for row in PlayerTeam.query.filter_by(team_id=team.id).all()]
  for player_id in player_ids:
    existing = ClubPlayer.query.filter_by(club_id=club.id, player_id=player_id).first()
    if existing:
      continue
    db.session.add(ClubPlayer(club_id=club.id, player_id=player_id))
    created += 1
  db.session.flush()
  return created


def ensure_default_ladder_rating_function() -> int:
  existing = LadderRatingFunction.query.order_by(LadderRatingFunction.id.asc()).first()
  if existing:
    return int(existing.id)
  created = LadderRatingFunction(name="ELO")
  db.session.add(created)
  db.session.flush()
  return int(created.id)


def get_or_create_ladder(club_id, name, description, sport_type_id, ladder_rating_function_id) -> tuple:
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


def get_or_create_ladder_team(ladder_id, team_id, rank, rating, matches_played) -> tuple:
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


def _next_occurrence_date(weekday: int, reference_date: datetime.date | None = None) -> datetime.date:
  current_date = reference_date or datetime.date.today()
  days_ahead = (weekday - current_date.weekday()) % 7
  if days_ahead == 0:
    days_ahead = 7
  return current_date + datetime.timedelta(days=days_ahead)


def get_or_create_availability_block(
    user_id: int,
    start_at: datetime.datetime | None = None,
    end_at: datetime.datetime | None = None,
    *,
    weekday: int | None = None,
    start_time: datetime.time | None = None,
    end_time: datetime.time | None = None,
) -> tuple:
  if weekday is None and start_at is not None and end_at is not None:
    weekday = start_at.weekday()
    start_time = start_at.time().replace(microsecond=0)
    end_time = end_at.time().replace(microsecond=0)
  elif weekday is not None and start_time is not None and end_time is not None:
    if start_at is None or end_at is None:
      block_date = _next_occurrence_date(weekday)
      start_at = datetime.datetime.combine(block_date, start_time)
      end_at = datetime.datetime.combine(block_date, end_time)

  if weekday is None or start_time is None or end_time is None or start_at is None or end_at is None:
    raise ValueError("Availability block requires either datetimes or weekly recurrence fields.")

  existing = AvailabilityBlock.query.filter_by(
    user_id=user_id,
    weekday=weekday,
    start_time=start_time,
    end_time=end_time,
  ).first()
  if existing:
    return existing, False
  block = AvailabilityBlock(
    user_id=user_id,
    weekday=weekday,
    start_time=start_time,
    end_time=end_time,
    start_at=start_at,
    end_at=end_at,
  )
  db.session.add(block)
  db.session.flush()
  return block, True


def reset_proposal_to_pending(week_start_date: datetime.date, team1_id: int, team2_id: int):
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


def ensure_pending_proposal(
    *,
    week_start_date: datetime.date,
    team1_id: int,
    team2_id: int,
    proposed_by_user_id: int,
    sport_type_id: int,
    proposed_start_at: datetime.datetime,
    proposed_end_at: datetime.datetime,
    location: str | None = None,
) -> bool:
  ordered_team1_id, ordered_team2_id = sorted((team1_id, team2_id))
  existing = MatchProposal.query.filter_by(
    week_start_date=week_start_date,
    team1_id=ordered_team1_id,
    team2_id=ordered_team2_id,
  ).first()
  if existing:
    return False

  db.session.add(
    MatchProposal(
      proposed_by_user_id=proposed_by_user_id,
      sport_type_id=sport_type_id,
      ruleset_id=None,
      team1_id=ordered_team1_id,
      team2_id=ordered_team2_id,
      status_id=MatchStatus.PENDING,
      week_start_date=week_start_date,
      proposed_start_at=proposed_start_at,
      proposed_end_at=proposed_end_at,
      location=location,
    )
  )
  db.session.flush()
  return True


def reset_demo_match_proposal_to_pending(week_start_date: datetime.date, team1_id: int, team2_id: int):
  reset_proposal_to_pending(week_start_date=week_start_date, team1_id=team1_id, team2_id=team2_id)


def find_match_proposal(week_start_date: datetime.date, team1_id: int, team2_id: int):
  ordered_team1_id, ordered_team2_id = sorted((team1_id, team2_id))
  return MatchProposal.query.filter_by(
    week_start_date=week_start_date,
    team1_id=ordered_team1_id,
    team2_id=ordered_team2_id,
  ).first()


def set_match_proposal_pending(
    *,
    week_start_date: datetime.date,
    team1_id: int,
    team2_id: int,
    proposed_by_user_id: int | None = None,
):
  proposal = find_match_proposal(week_start_date=week_start_date, team1_id=team1_id, team2_id=team2_id)
  if not proposal:
    return False

  proposal.status_id = MatchStatus.PENDING
  if proposed_by_user_id is not None:
    proposal.proposed_by_user_id = proposed_by_user_id

  for model in (MatchAccepted, MatchRejected, MatchCancelled):
    row = db.session.get(model, proposal.id)
    if row:
      db.session.delete(row)
  db.session.flush()
  return True


def set_match_proposal_accepted(
    *,
    week_start_date: datetime.date,
    team1_id: int,
    team2_id: int,
    accepted_by_user_id: int,
    response_text: str | None = None,
):
  proposal = find_match_proposal(week_start_date=week_start_date, team1_id=team1_id, team2_id=team2_id)
  if not proposal:
    return False

  proposal.status_id = MatchStatus.ACCEPTED

  accepted = db.session.get(MatchAccepted, proposal.id)
  if not accepted:
    accepted = MatchAccepted(id=proposal.id)
    db.session.add(accepted)
  accepted.response_by_user_id = accepted_by_user_id
  accepted.response_text = response_text

  for model in (MatchRejected, MatchCancelled):
    row = db.session.get(model, proposal.id)
    if row:
      db.session.delete(row)

  db.session.flush()
  return True


def delete_demo_match_proposal(week_start_date: datetime.date, team1_id: int, team2_id: int):
  ordered_team1_id, ordered_team2_id = sorted((team1_id, team2_id))
  proposal = MatchProposal.query.filter_by(
    week_start_date=week_start_date,
    team1_id=ordered_team1_id,
    team2_id=ordered_team2_id,
  ).first()
  if not proposal:
    return

  for model in (MatchAccepted, MatchRejected, MatchCancelled):
    row = db.session.get(model, proposal.id)
    if row:
      db.session.delete(row)
  db.session.delete(proposal)
  db.session.flush()


# -- Main seed -----------------------------------------------------------------

def seed_teams_and_users(verbose: bool = True):
  log(f"{TAG} Starting seed", verbose)

  # 1. Roles
  log(f"{TAG} [1/6] Seeding account roles...", verbose)
  try:
    role_manager = get_or_create_role("team_manager", verbose)
    role_player  = get_or_create_role("player", verbose)
    get_or_create_role("user", verbose)
  except Exception as e:
    print(f"{TAG} ERROR seeding roles: {e}")
    db.session.rollback()
    raise
  log(f"{TAG} [1/6] Roles OK", verbose)

  # 2. Sport types
  log(f"{TAG} [2/6] Seeding sport types...", verbose)
  try:
    football   = get_or_create_sport("Football",   11, 23, verbose)
    basketball = get_or_create_sport("Basketball",  5, 12, verbose)
    volleyball = get_or_create_sport("Volleyball",  6, 14, verbose)
    tennis     = get_or_create_sport("Tennis",      1,  4, verbose)
    hockey     = get_or_create_sport("Hockey",     11, 22, verbose)
  except Exception as e:
    print(f"{TAG} ERROR seeding sport types: {e}")
    db.session.rollback()
    raise
  log(f"{TAG} [2/6] Sport types OK", verbose)

  # 3. Teams
  log(f"{TAG} [3/6] Seeding teams...", verbose)
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
      team, created = make_team(name, sport, verbose=verbose)
      teams.append(team)
      if created:
        teams_created += 1
      else:
        teams_skipped += 1
  except Exception as e:
    print(f"{TAG} ERROR seeding teams: {e}")
    db.session.rollback()
    raise
  log(f"{TAG} [3/6] Teams OK — created: {teams_created}, skipped: {teams_skipped}", verbose)

  # 4. Managers
  log(f"{TAG} [4/6] Seeding managers...", verbose)
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
      acc, acc_created = make_account(first, last, email, role_manager)
      if not acc_created:
        log(f"{TAG}   account '{email}' already exists (id={acc.id}), skipping", verbose)
        mgr_skipped += 1
        continue
      tm, tm_created = make_manager(acc)
      if not tm_created:
        log(f"{TAG}   team_manager for '{email}' already exists, skipping", verbose)
        mgr_skipped += 1
        continue
      assigned = assign_manager_to_team(tm, team)
      if assigned:
        log(f"{TAG}   manager {first} {last} (id={acc.id}) -> team '{team.name}' (id={team.id})", verbose)
      else:
        log(f"{TAG}   manager {first} {last} already assigned to '{team.name}', skipping", verbose)
      mgr_created += 1
  except Exception as e:
    print(f"{TAG} ERROR seeding managers: {e}")
    db.session.rollback()
    raise
  log(f"{TAG} [4/6] Managers OK — created: {mgr_created}, skipped: {mgr_skipped}", verbose)

  # 5. Players
  log(f"{TAG} [5/6] Seeding players...", verbose)
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
      acc, acc_created = make_account(first, last, email, role_player)
      if not acc_created:
        log(f"{TAG}   account '{email}' already exists (id={acc.id}), skipping", verbose)
        plr_skipped += 1
        continue
      player, plr_ok = make_player(acc)
      if not plr_ok:
        log(f"{TAG}   player for '{email}' already exists, skipping", verbose)
        plr_skipped += 1
        continue
      assigned_names = []
      for idx in team_indices:
        if idx >= len(teams):
          print(f"{TAG}   WARNING: team index {idx} out of range, skipping")
          continue
        if assign_player_to_team(player, teams[idx]):
          assigned_names.append(teams[idx].name)
      log(f"{TAG}   player {first} {last} (id={acc.id}) -> teams: {assigned_names}", verbose)
      plr_created += 1
  except Exception as e:
    print(f"{TAG} ERROR seeding players: {e}")
    db.session.rollback()
    raise
  log(f"{TAG} [5/6] Players OK — created: {plr_created}, skipped: {plr_skipped}", verbose)

  # 6. Demo club + ladders
  log(f"{TAG} [6/6] Seeding demo club data...", verbose)
  try:
    demo_acc, demo_acc_created = make_account(
      "Jeremi",
      "Lorek",
      "jeremilorek@outlook.com",
      role=role_manager,
      password="qwertyuiop",
      force_password_update=True,
    )
    log(f"{TAG}   demo account {'created' if demo_acc_created else 'already exists'} (id={demo_acc.id})", verbose)
    if not demo_acc.is_verified:
      demo_acc.is_verified = True
      log(f"{TAG}   demo account verification enabled", verbose)

    demo_tm, demo_tm_created = make_manager(demo_acc)
    log(f"{TAG}   demo team_manager {'created' if demo_tm_created else 'already exists'} (id={demo_tm.id})", verbose)

    demo_owner, demo_owner_created = make_club_owner(demo_tm)
    log(f"{TAG}   demo club_owner {'created' if demo_owner_created else 'already exists'} (id={demo_owner.id})", verbose)

    demo_club, demo_club_created = get_or_create_club("NetRank Club", sport_type_id=tennis.id)
    log(f"{TAG}   demo club {'created' if demo_club_created else 'already exists'} (id={demo_club.id})", verbose)

    if ensure_owner_of_club(demo_owner, demo_club):
      log(f"{TAG}   linked owner {demo_owner.id} -> club {demo_club.id}", verbose)

    men_team,    _ = make_team("NetRank Aces",    tennis, club_id=demo_club.id, verbose=verbose)
    junior_team, _ = make_team("NetRank Juniors", tennis, club_id=demo_club.id, verbose=verbose)

    assign_manager_to_team(demo_tm, men_team)
    assign_manager_to_team(demo_tm, junior_team)

    rating_fn_id = ensure_default_ladder_rating_function()
    men_ladder,    _ = get_or_create_ladder(demo_club.id, "Men's Singles", "Demo ladder for men's singles", tennis.id, rating_fn_id)
    junior_ladder, _ = get_or_create_ladder(demo_club.id, "U14 Singles",   "Demo ladder for U14 singles",   tennis.id, rating_fn_id)

    get_or_create_ladder_team(men_ladder.id,    men_team.id,    rank=1, rating=1260, matches_played=15)
    get_or_create_ladder_team(men_ladder.id,    junior_team.id, rank=2, rating=1180, matches_played=12)
    get_or_create_ladder_team(junior_ladder.id, junior_team.id, rank=1, rating=1215, matches_played=10)
    get_or_create_ladder_team(junior_ladder.id, men_team.id,    rank=2, rating=1100, matches_played=8)
    log(f"{TAG}   demo ladder standings upserted", verbose)

    demo_week_start = next_week_start()
    avail_start = datetime.datetime.combine(
      demo_week_start + datetime.timedelta(days=1),
      datetime.time(hour=18, minute=0),
    )
    avail_end = avail_start + datetime.timedelta(hours=2)

    player_demo_club, _ = get_or_create_club("Player Demo Club", sport_type_id=tennis.id)
    player_demo_a, _ = make_team("Player Demo A", tennis, club_id=player_demo_club.id, verbose=verbose)
    player_demo_b, _ = make_team("Player Demo B", tennis, club_id=player_demo_club.id, verbose=verbose)

    player_demo_ladder, _ = get_or_create_ladder(
      player_demo_club.id,
      "Player Demo Singles",
      "Demo ladder where Jeremi is only a player",
      tennis.id,
      rating_fn_id,
    )
    get_or_create_ladder_team(player_demo_ladder.id, player_demo_a.id, rank=1, rating=1110, matches_played=3)
    get_or_create_ladder_team(player_demo_ladder.id, player_demo_b.id, rank=2, rating=1090, matches_played=3)

    demo_player, _ = make_player(demo_acc)
    assign_player_to_team(demo_player, player_demo_a)

    opponent_acc, _ = make_account("Robin", "Vermeulen", "robin.vermeulen@example.com", role_player)
    opponent_player, _ = make_player(opponent_acc)
    assign_player_to_team(opponent_player, player_demo_b)

    get_or_create_availability_block(demo_acc.id, avail_start, avail_end)
    get_or_create_availability_block(
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
    reset_proposal_to_pending(
      week_start_date=demo_week_start,
      team1_id=player_demo_a.id,
      team2_id=player_demo_b.id,
    )
    log(
      f"{TAG}   player-demo weekly proposals generated: "
      f"created={generation_result['created_count']}, skipped={generation_result['skipped_count']}",
      verbose,
    )

    demo_week_start = next_week_start()
    demo_availability_start = datetime.datetime.combine(
      demo_week_start + datetime.timedelta(days=1),
      datetime.time(hour=18, minute=0),
    )
    demo_availability_end = demo_availability_start + datetime.timedelta(hours=2)

    aces_player_acc, _ = make_account(
      first="Nora",
      last="Vandenberg",
      email="nora.vandenberg@example.com",
      role=role_player,
    )
    juniors_player_acc, _ = make_account(
      first="Milo",
      last="Peeters",
      email="milo.peeters@example.com",
      role=role_player,
    )
    ensure_player_on_team(aces_player_acc, men_team)
    ensure_player_on_team(juniors_player_acc, junior_team)

    club_player_count = 0
    club_player_count += ensure_team_players_in_club(men_team, demo_club)
    club_player_count += ensure_team_players_in_club(junior_team, demo_club)
    print(f"{TAG}   demo club memberships upserted for team players (added={club_player_count})")

    get_or_create_availability_block(
      user_id=aces_player_acc.id,
      start_at=demo_availability_start,
      end_at=demo_availability_end,
    )
    get_or_create_availability_block(
      user_id=juniors_player_acc.id,
      start_at=demo_availability_start + datetime.timedelta(minutes=30),
      end_at=demo_availability_end,
    )
    print(
      f"{TAG}   demo availability added for weekly match generation "
      f"({demo_availability_start.isoformat()} -> {demo_availability_end.isoformat()})"
    )

    db.session.flush()
    generation_result = generate_weekly_match_proposals(
      proposed_by_user_id=demo_acc.id,
      week_start_date=demo_week_start,
      ladder_id=men_ladder.id,
      managed_team_ids=None,
      duration_minutes=60,
      location="NetRank Court 1",
    )
    reset_demo_match_proposal_to_pending(
      week_start_date=demo_week_start,
      team1_id=men_team.id,
      team2_id=junior_team.id,
    )
    print(
      f"{TAG}   weekly match proposals generated: "
      f"created={generation_result['created_count']}, skipped={generation_result['skipped_count']}"
    )

    old_player_demo_team = Team.query.filter_by(
      name="NetRank Challengers",
      club_id=demo_club.id,
    ).first()
    if demo_acc.player and old_player_demo_team in demo_acc.player.teams:
      demo_acc.player.teams.remove(old_player_demo_team)
      print(f"{TAG}   removed demo player from old owned-club player-only team")
    if demo_acc.player and men_team in demo_acc.player.teams:
      demo_acc.player.teams.remove(men_team)
      print(f"{TAG}   removed demo player from managed NetRank team")
    if old_player_demo_team:
      delete_demo_match_proposal(
        week_start_date=demo_week_start,
        team1_id=old_player_demo_team.id,
        team2_id=junior_team.id,
      )

    player_demo_club, player_demo_club_created = get_or_create_club("Player Demo Club")
    if player_demo_club_created:
      print(f"{TAG}   player demo club created (id={player_demo_club.id})")
    else:
      print(f"{TAG}   player demo club already exists (id={player_demo_club.id}), skipping")

    player_demo_team, player_demo_team_created = make_team(
      "Player Demo A",
      tennis,
      club_id=player_demo_club.id,
    )
    if player_demo_team_created:
      print(f"{TAG}   team '{player_demo_team.name}' created in player demo club")
    else:
      print(f"{TAG}   team '{player_demo_team.name}' already exists in player demo club, skipping")

    player_demo_opponent, player_demo_opponent_created = make_team(
      "Player Demo B",
      tennis,
      club_id=player_demo_club.id,
    )
    if player_demo_opponent_created:
      print(f"{TAG}   team '{player_demo_opponent.name}' created in player demo club")
    else:
      print(f"{TAG}   team '{player_demo_opponent.name}' already exists in player demo club, skipping")

    player_demo_ladder, player_demo_ladder_created = get_or_create_ladder(
      club_id=player_demo_club.id,
      name="Player Demo Singles",
      description="Demo ladder where Jeremi is only a player",
      sport_type_id=tennis.id,
      ladder_rating_function_id=rating_fn_id,
    )
    if player_demo_ladder_created:
      print(f"{TAG}   ladder '{player_demo_ladder.name}' created")
    else:
      print(f"{TAG}   ladder '{player_demo_ladder.name}' already exists, skipping")

    get_or_create_ladder_team(
      ladder_id=player_demo_ladder.id,
      team_id=player_demo_team.id,
      rank=1,
      rating=1110,
      matches_played=3,
    )
    get_or_create_ladder_team(
      ladder_id=player_demo_ladder.id,
      team_id=player_demo_opponent.id,
      rank=2,
      rating=1090,
      matches_played=3,
    )

    opponent_acc, _ = make_account(
      first="Robin",
      last="Vermeulen",
      email="robin.vermeulen@example.com",
      role=role_player,
    )
    ensure_player_on_team(demo_acc, player_demo_team)
    ensure_player_on_team(opponent_acc, player_demo_opponent)
    ensure_team_players_in_club(player_demo_team, player_demo_club)
    ensure_team_players_in_club(player_demo_opponent, player_demo_club)

    player_demo_weeks = [demo_week_start + datetime.timedelta(days=7 * i) for i in range(3)]
    total_created = 0
    total_skipped = 0

    for week_start in player_demo_weeks:
      weekly_start = datetime.datetime.combine(
        week_start + datetime.timedelta(days=1),
        datetime.time(hour=18, minute=0),
      )
      weekly_end = weekly_start + datetime.timedelta(hours=2)

      get_or_create_availability_block(
        user_id=demo_acc.id,
        start_at=weekly_start,
        end_at=weekly_end,
      )
      get_or_create_availability_block(
        user_id=opponent_acc.id,
        start_at=weekly_start + datetime.timedelta(minutes=15),
        end_at=weekly_end,
      )

      player_demo_generation_result = generate_weekly_match_proposals(
        proposed_by_user_id=demo_acc.id,
        week_start_date=week_start,
        ladder_id=player_demo_ladder.id,
        managed_team_ids=None,
        duration_minutes=60,
        location="Player Demo Court 1",
      )
      reset_demo_match_proposal_to_pending(
        week_start_date=week_start,
        team1_id=player_demo_team.id,
        team2_id=player_demo_opponent.id,
      )
      total_created += player_demo_generation_result["created_count"]
      total_skipped += player_demo_generation_result["skipped_count"]

    print(
      f"{TAG}   player-only weekly match proposals generated for {len(player_demo_weeks)} weeks: "
      f"created={total_created}, skipped={total_skipped}"
    )

    # Deterministic demo scenarios for manual UI testing with Jeremi's account:
    # 1) Pending proposal (proposed by opponent) that Jeremi can accept manually.
    # 2) Already accepted proposal (accepted by opponent) visible in Upcoming Matches.
    if player_demo_weeks:
      pending_week = player_demo_weeks[0]
      accepted_week = player_demo_weeks[1] if len(player_demo_weeks) > 1 else player_demo_weeks[0]

      if set_match_proposal_pending(
        week_start_date=pending_week,
        team1_id=player_demo_team.id,
        team2_id=player_demo_opponent.id,
        proposed_by_user_id=opponent_acc.id,
      ):
        log(
          f"{TAG}   ensured pending player-demo request (opponent proposed) for week {pending_week.isoformat()}",
          verbose,
        )

      if set_match_proposal_accepted(
        week_start_date=accepted_week,
        team1_id=player_demo_team.id,
        team2_id=player_demo_opponent.id,
        accepted_by_user_id=opponent_acc.id,
        response_text="Accepted by opponent for demo upcoming-matches visibility",
      ):
        log(
          f"{TAG}   ensured accepted player-demo request for week {accepted_week.isoformat()}",
          verbose,
        )

    # ------------------------------------------------------------------
    # Additional fictional clubs / ladders / players for richer demo data
    # ------------------------------------------------------------------
    typo_acc, _ = make_account(
      first="Jeremi",
      last="Lorek",
      email="jeremilorek@ooutlo.com",
      role=role_manager,
      password="qwertyuiop",
      force_password_update=True,
    )
    if not typo_acc.is_verified:
      typo_acc.is_verified = True
    typo_tm, _ = make_manager(typo_acc)
    typo_owner, _ = make_club_owner(typo_tm)

    harbor_club, _ = get_or_create_club("Harbor City Racquet Club", sport_type_id=tennis.id)
    quayside_club, _ = get_or_create_club("Quayside Smash Society", sport_type_id=tennis.id)
    summit_club, _ = get_or_create_club("Summit Hoops Collective", sport_type_id=basketball.id)

    ensure_owner_of_club(demo_owner, harbor_club)
    ensure_owner_of_club(demo_owner, quayside_club)
    ensure_owner_of_club(typo_owner, harbor_club)
    ensure_owner_of_club(typo_owner, summit_club)

    harbor_aces, _ = make_team("Harbor Aces", tennis, club_id=harbor_club.id, verbose=verbose)
    dockside_topspin, _ = make_team("Dockside Topspin", tennis, club_id=harbor_club.id, verbose=verbose)
    marina_smash, _ = make_team("Marina Smash", tennis, club_id=harbor_club.id, verbose=verbose)
    pierline_rally, _ = make_team("Pierline Rally", tennis, club_id=harbor_club.id, verbose=verbose)

    quayside_comets, _ = make_team("Quayside Comets", tennis, club_id=quayside_club.id, verbose=verbose)
    shipyard_spinners, _ = make_team("Shipyard Spinners", tennis, club_id=quayside_club.id, verbose=verbose)
    tidecourt_titans, _ = make_team("Tidecourt Titans", tennis, club_id=quayside_club.id, verbose=verbose)
    harborline_blitz, _ = make_team("Harborline Blitz", tennis, club_id=quayside_club.id, verbose=verbose)

    summit_stars, _ = make_team("Summit Stars", basketball, club_id=summit_club.id, verbose=verbose)
    ridge_runners, _ = make_team("Ridge Runners", basketball, club_id=summit_club.id, verbose=verbose)
    apex_allstars, _ = make_team("Apex All-Stars", basketball, club_id=summit_club.id, verbose=verbose)
    terrace_tornadoes, _ = make_team("Terrace Tornadoes", basketball, club_id=summit_club.id, verbose=verbose)

    assign_manager_to_team(demo_tm, harbor_aces)
    assign_manager_to_team(demo_tm, marina_smash)
    assign_manager_to_team(typo_tm, dockside_topspin)
    assign_manager_to_team(typo_tm, summit_stars)

    harbor_open_ladder, _ = get_or_create_ladder(
      harbor_club.id,
      "Harbor Open Singles",
      "Competitive singles ladder for Harbor club",
      tennis.id,
      rating_fn_id,
    )
    harbor_community_ladder, _ = get_or_create_ladder(
      harbor_club.id,
      "Harbor Community Singles",
      "Community ladder with matchmaking requests",
      tennis.id,
      rating_fn_id,
    )
    quayside_ladder, _ = get_or_create_ladder(
      quayside_club.id,
      "Quayside Sunday Singles",
      "Sunday challenge ladder",
      tennis.id,
      rating_fn_id,
    )
    summit_ladder, _ = get_or_create_ladder(
      summit_club.id,
      "Summit 5v5 League",
      "Basketball league ladder",
      basketball.id,
      rating_fn_id,
    )

    get_or_create_ladder_team(harbor_open_ladder.id, harbor_aces.id, rank=1, rating=1325, matches_played=17)
    get_or_create_ladder_team(harbor_open_ladder.id, dockside_topspin.id, rank=2, rating=1288, matches_played=14)
    get_or_create_ladder_team(harbor_open_ladder.id, marina_smash.id, rank=3, rating=1245, matches_played=12)
    get_or_create_ladder_team(harbor_open_ladder.id, pierline_rally.id, rank=4, rating=1205, matches_played=10)

    get_or_create_ladder_team(harbor_community_ladder.id, dockside_topspin.id, rank=1, rating=1170, matches_played=4)
    get_or_create_ladder_team(harbor_community_ladder.id, marina_smash.id, rank=2, rating=1140, matches_played=4)

    get_or_create_ladder_team(quayside_ladder.id, quayside_comets.id, rank=1, rating=1260, matches_played=9)
    get_or_create_ladder_team(quayside_ladder.id, shipyard_spinners.id, rank=2, rating=1220, matches_played=9)
    get_or_create_ladder_team(quayside_ladder.id, tidecourt_titans.id, rank=3, rating=1180, matches_played=8)
    get_or_create_ladder_team(quayside_ladder.id, harborline_blitz.id, rank=4, rating=1150, matches_played=8)

    get_or_create_ladder_team(summit_ladder.id, summit_stars.id, rank=1, rating=1300, matches_played=11)
    get_or_create_ladder_team(summit_ladder.id, ridge_runners.id, rank=2, rating=1260, matches_played=11)
    get_or_create_ladder_team(summit_ladder.id, apex_allstars.id, rank=3, rating=1215, matches_played=10)
    get_or_create_ladder_team(summit_ladder.id, terrace_tornadoes.id, rank=4, rating=1180, matches_played=10)

    # Ensure both of your accounts are present in club contexts.
    ensure_player_on_team(demo_acc, harbor_aces)
    ensure_player_on_team(typo_acc, dockside_topspin)

    rival_acc, _ = make_account(
      first="Sophie",
      last="Lambert",
      email="sophie.lambert@example.com",
      role=role_player,
    )
    ensure_player_on_team(rival_acc, marina_smash)

    ensure_team_players_in_club(harbor_aces, harbor_club)
    ensure_team_players_in_club(dockside_topspin, harbor_club)
    ensure_team_players_in_club(marina_smash, harbor_club)
    ensure_team_players_in_club(pierline_rally, harbor_club)

    request_week = next_week_start()
    request_start = datetime.datetime.combine(
      request_week + datetime.timedelta(days=2),
      datetime.time(hour=19, minute=0),
    )
    request_end = request_start + datetime.timedelta(hours=2)

    get_or_create_availability_block(typo_acc.id, request_start, request_end)
    get_or_create_availability_block(rival_acc.id, request_start + datetime.timedelta(minutes=20), request_end)

    harbor_request_result = generate_weekly_match_proposals(
      proposed_by_user_id=demo_acc.id,
      week_start_date=request_week,
      ladder_id=harbor_community_ladder.id,
      managed_team_ids=None,
      duration_minutes=60,
      location="Harbor Court 2",
    )
    reset_proposal_to_pending(
      week_start_date=request_week,
      team1_id=dockside_topspin.id,
      team2_id=marina_smash.id,
    )
    if ensure_pending_proposal(
      week_start_date=request_week,
      team1_id=dockside_topspin.id,
      team2_id=marina_smash.id,
      proposed_by_user_id=demo_acc.id,
      sport_type_id=tennis.id,
      proposed_start_at=request_start,
      proposed_end_at=request_start + datetime.timedelta(minutes=60),
      location="Harbor Court 2",
    ):
      log(f"{TAG}   ensured pending harbor request for Dockside Topspin vs Marina Smash", verbose)
    log(
      f"{TAG}   harbor community proposals generated: "
      f"created={harbor_request_result['created_count']}, skipped={harbor_request_result['skipped_count']}",
      verbose,
    )

  except Exception as e:
    print(f"{TAG} ERROR seeding demo club data: {e}")
    db.session.rollback()
    raise
  log(f"{TAG} [6/6] Demo club data OK", verbose)

  # Commit
  log(f"{TAG} Committing to database...", verbose)
  try:
    db.session.commit()
  except Exception as e:
    print(f"{TAG} ERROR during commit: {e}")
    db.session.rollback()
    raise

  print(f"{TAG} Seed complete — teams: {teams_created}/{teams_created + teams_skipped}, managers: {mgr_created}/{mgr_created + mgr_skipped}, players: {plr_created}/{plr_created + plr_skipped}")
