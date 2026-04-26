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
from server.app.models.match_rule import MatchRuleSet
from server.app.models.account import Account, TeamManager
from server.app.models.account_role import AccountRole
from server.app.models.club import Club
from server.app.models.club_join_request import ClubJoinRequest
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


def get_or_create_club(
    name: str,
    sport_type_id: int | None = None,
    description: str | None = None,
    city: str | None = None,
) -> tuple:
  """Returns (club, created: bool)."""
  existing = Club.query.filter_by(name=name).first()
  if existing:
    updated = False
    if sport_type_id is not None and existing.sport_type_id != sport_type_id:
      existing.sport_type_id = sport_type_id
      updated = True
    if description is not None and existing.description != description:
      existing.description = description
      updated = True
    if city is not None and existing.city != city:
      existing.city = city
      updated = True
    if updated:
      db.session.flush()
    return existing, False
  club = Club(
    name=name,
    description=description or "Demo club",
    sport_type_id=sport_type_id,
    city=city or "Antwerp",
  )
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
  elo = LadderRatingFunction.query.filter(
    db.func.lower(LadderRatingFunction.name) == "elo"
  ).first()
  if elo:
    return int(elo.id)

  existing = LadderRatingFunction.query.order_by(LadderRatingFunction.id.asc()).first()
  if existing:
    existing.name = "ELO"
    db.session.flush()
    return int(existing.id)

  created = LadderRatingFunction(name="ELO")
  db.session.add(created)
  db.session.flush()
  return int(created.id)


def ensure_default_match_ruleset() -> int | None:
  existing = MatchRuleSet.query.order_by(MatchRuleSet.id.asc()).first()
  if existing:
    return int(existing.id)
  return None


def get_or_create_ladder(
    club_id,
    name,
    description,
    sport_type_id,
    ladder_rating_function_id,
    ruleset_id=None,
) -> tuple:
  existing = Ladder.query.filter_by(club_id=club_id, name=name).first()
  if existing:
    updated = False
    if description is not None and existing.description != description:
      existing.description = description
      updated = True
    if sport_type_id is not None and existing.sport_type_id != sport_type_id:
      existing.sport_type_id = sport_type_id
      updated = True
    if ladder_rating_function_id is not None and existing.ladder_rating_function_id != ladder_rating_function_id:
      existing.ladder_rating_function_id = ladder_rating_function_id
      updated = True
    if existing.ruleset_id != ruleset_id:
      existing.ruleset_id = ruleset_id
      updated = True
    if updated:
      db.session.flush()
    return existing, False
  ladder = Ladder(
    club_id=club_id,
    name=name,
    description=description,
    sport_type_id=sport_type_id,
    ruleset_id=ruleset_id,
    ladder_rating_function_id=ladder_rating_function_id,
  )
  db.session.add(ladder)
  db.session.flush()
  return ladder, True


def upsert_club_join_request(club_id: int, user_id: int, days_ago: int = 0) -> bool:
  existing = ClubJoinRequest.query.filter_by(club_id=club_id, user_id=user_id).first()
  requested_at = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days_ago)
  if existing:
    existing.date = requested_at
    db.session.flush()
    return False
  db.session.add(ClubJoinRequest(club_id=club_id, user_id=user_id, date=requested_at))
  db.session.flush()
  return True


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
    padel      = get_or_create_sport("Padel",       2,  4, verbose)
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
    rating_fn_id = ensure_default_ladder_rating_function()
    ruleset_id = ensure_default_match_ruleset()

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

    assistant_acc, _ = make_account(
      "Nina",
      "Jacobs",
      "nina.jacobs@example.com",
      role=role_manager,
    )
    assistant_tm, _ = make_manager(assistant_acc)
    assistant_owner, _ = make_club_owner(assistant_tm)

    demo_club, demo_club_created = get_or_create_club(
      "NetRank Club",
      sport_type_id=tennis.id,
      description="Premium club for competitive and academy tennis programs.",
      city="Antwerp",
    )
    log(f"{TAG}   demo club {'created' if demo_club_created else 'already exists'} (id={demo_club.id})", verbose)
    padel_club, _ = get_or_create_club(
      "Antwerp Padel House",
      sport_type_id=padel.id,
      description="Professional padel venue with league and community ladders.",
      city="Antwerp",
    )
    player_demo_club, _ = get_or_create_club(
      "Player Demo Club",
      sport_type_id=tennis.id,
      description="Player-focused club for match request and acceptance demo.",
      city="Ghent",
    )

    if ensure_owner_of_club(demo_owner, demo_club):
      log(f"{TAG}   linked owner {demo_owner.id} -> club {demo_club.id}", verbose)
    ensure_owner_of_club(assistant_owner, demo_club)
    ensure_owner_of_club(demo_owner, padel_club)
    ensure_owner_of_club(assistant_owner, padel_club)

    men_team, _ = make_team("NetRank Aces", tennis, club_id=demo_club.id, verbose=verbose)
    junior_team, _ = make_team("NetRank Juniors", tennis, club_id=demo_club.id, verbose=verbose)
    challenger_team, _ = make_team("NetRank Challengers", tennis, club_id=demo_club.id, verbose=verbose)

    assign_manager_to_team(demo_tm, men_team)
    assign_manager_to_team(demo_tm, junior_team)
    assign_manager_to_team(assistant_tm, challenger_team)

    aces_player_acc, _ = make_account("Nora", "Vandenberg", "nora.vandenberg@example.com", role_player)
    juniors_player_acc, _ = make_account("Milo", "Peeters", "milo.peeters@example.com", role_player)
    challengers_player_acc, _ = make_account("Lars", "Dekker", "lars.dekker@example.com", role_player)
    ensure_player_on_team(aces_player_acc, men_team)
    ensure_player_on_team(juniors_player_acc, junior_team)
    ensure_player_on_team(challengers_player_acc, challenger_team)
    ensure_team_players_in_club(men_team, demo_club)
    ensure_team_players_in_club(junior_team, demo_club)
    ensure_team_players_in_club(challenger_team, demo_club)

    men_ladder, _ = get_or_create_ladder(
      demo_club.id,
      "Men's Singles",
      "Primary competitive singles ladder using ELO.",
      tennis.id,
      rating_fn_id,
      ruleset_id=ruleset_id,
    )
    junior_ladder, _ = get_or_create_ladder(
      demo_club.id,
      "U14 Singles",
      "Junior development ladder with weekly fixtures.",
      tennis.id,
      rating_fn_id,
      ruleset_id=ruleset_id,
    )
    get_or_create_ladder_team(men_ladder.id, men_team.id, rank=1, rating=1290, matches_played=18)
    get_or_create_ladder_team(men_ladder.id, challenger_team.id, rank=2, rating=1230, matches_played=15)
    get_or_create_ladder_team(men_ladder.id, junior_team.id, rank=3, rating=1190, matches_played=13)
    get_or_create_ladder_team(junior_ladder.id, junior_team.id, rank=1, rating=1220, matches_played=11)
    get_or_create_ladder_team(junior_ladder.id, challenger_team.id, rank=2, rating=1160, matches_played=8)

    padel_alpha, _ = make_team("Antwerp Padel Elite", padel, club_id=padel_club.id, verbose=verbose)
    padel_bravo, _ = make_team("Scheldt Smashers", padel, club_id=padel_club.id, verbose=verbose)
    padel_charlie, _ = make_team("South Court Pairs", padel, club_id=padel_club.id, verbose=verbose)
    assign_manager_to_team(demo_tm, padel_alpha)
    assign_manager_to_team(assistant_tm, padel_bravo)
    assign_manager_to_team(assistant_tm, padel_charlie)

    padel_player_one, _ = make_account("Emma", "Claes", "emma.claes@example.com", role_player)
    padel_player_two, _ = make_account("Pieter", "Maes", "pieter.maes@example.com", role_player)
    padel_player_three, _ = make_account("Sanne", "Verhoeven", "sanne.verhoeven@example.com", role_player)
    ensure_player_on_team(padel_player_one, padel_alpha)
    ensure_player_on_team(padel_player_two, padel_bravo)
    ensure_player_on_team(padel_player_three, padel_charlie)
    ensure_team_players_in_club(padel_alpha, padel_club)
    ensure_team_players_in_club(padel_bravo, padel_club)
    ensure_team_players_in_club(padel_charlie, padel_club)

    padel_ladder, _ = get_or_create_ladder(
      padel_club.id,
      "Padel Premier Ladder",
      "Top padel ladder for advanced doubles teams.",
      padel.id,
      rating_fn_id,
      ruleset_id=ruleset_id,
    )
    community_padel_ladder, _ = get_or_create_ladder(
      padel_club.id,
      "Padel Community Ladder",
      "Community padel ladder for requests and friendly challenges.",
      padel.id,
      rating_fn_id,
      ruleset_id=ruleset_id,
    )
    get_or_create_ladder_team(padel_ladder.id, padel_alpha.id, rank=1, rating=1310, matches_played=16)
    get_or_create_ladder_team(padel_ladder.id, padel_bravo.id, rank=2, rating=1275, matches_played=14)
    get_or_create_ladder_team(padel_ladder.id, padel_charlie.id, rank=3, rating=1210, matches_played=10)
    get_or_create_ladder_team(community_padel_ladder.id, padel_bravo.id, rank=1, rating=1185, matches_played=6)
    get_or_create_ladder_team(community_padel_ladder.id, padel_charlie.id, rank=2, rating=1150, matches_played=5)

    player_demo_team, _ = make_team("Player Demo A", tennis, club_id=player_demo_club.id, verbose=verbose)
    player_demo_opponent, _ = make_team("Player Demo B", tennis, club_id=player_demo_club.id, verbose=verbose)
    assign_manager_to_team(assistant_tm, player_demo_team)
    assign_manager_to_team(assistant_tm, player_demo_opponent)

    player_demo_ladder, _ = get_or_create_ladder(
      club_id=player_demo_club.id,
      name="Player Demo Singles",
      description="Demo ladder where Jeremi is only a player.",
      sport_type_id=tennis.id,
      ladder_rating_function_id=rating_fn_id,
      ruleset_id=ruleset_id,
    )
    get_or_create_ladder_team(player_demo_ladder.id, player_demo_team.id, rank=1, rating=1110, matches_played=3)
    get_or_create_ladder_team(player_demo_ladder.id, player_demo_opponent.id, rank=2, rating=1090, matches_played=3)

    opponent_acc, _ = make_account("Robin", "Vermeulen", "robin.vermeulen@example.com", role_player)
    ensure_player_on_team(demo_acc, player_demo_team)
    ensure_player_on_team(opponent_acc, player_demo_opponent)
    ensure_team_players_in_club(player_demo_team, player_demo_club)
    ensure_team_players_in_club(player_demo_opponent, player_demo_club)

    demo_week_start = next_week_start()
    player_demo_weeks = [demo_week_start + datetime.timedelta(days=7 * i) for i in range(3)]
    total_created = 0
    total_skipped = 0
    for week_start in player_demo_weeks:
      weekly_start = datetime.datetime.combine(
        week_start + datetime.timedelta(days=1),
        datetime.time(hour=18, minute=0),
      )
      weekly_end = weekly_start + datetime.timedelta(hours=2)
      get_or_create_availability_block(demo_acc.id, weekly_start, weekly_end)
      get_or_create_availability_block(opponent_acc.id, weekly_start + datetime.timedelta(minutes=15), weekly_end)
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

    log(
      f"{TAG}   player demo proposals generated for {len(player_demo_weeks)} weeks: "
      f"created={total_created}, skipped={total_skipped}",
      verbose,
    )

    if player_demo_weeks:
      pending_week = player_demo_weeks[0]
      accepted_week = player_demo_weeks[1] if len(player_demo_weeks) > 1 else player_demo_weeks[0]
      set_match_proposal_pending(
        week_start_date=pending_week,
        team1_id=player_demo_team.id,
        team2_id=player_demo_opponent.id,
        proposed_by_user_id=opponent_acc.id,
      )
      set_match_proposal_accepted(
        week_start_date=accepted_week,
        team1_id=player_demo_team.id,
        team2_id=player_demo_opponent.id,
        accepted_by_user_id=opponent_acc.id,
        response_text="Accepted by opponent for dashboard upcoming matches demo",
      )

    owner_requester_one, _ = make_account("Victor", "Reynders", "victor.reynders@example.com", role_player)
    owner_requester_two, _ = make_account("Noemie", "Aerts", "noemie.aerts@example.com", role_player)
    owner_requester_three, _ = make_account("Tom", "Lenaerts", "tom.lenaerts@example.com", role_player)
    make_player(owner_requester_one)
    make_player(owner_requester_two)
    make_player(owner_requester_three)
    upsert_club_join_request(demo_club.id, owner_requester_one.id, days_ago=2)
    upsert_club_join_request(demo_club.id, owner_requester_two.id, days_ago=1)
    upsert_club_join_request(padel_club.id, owner_requester_three.id, days_ago=0)

    log(f"{TAG}   seeded professional tennis and padel demo clubs with owners, ladders, requests and match flows", verbose)

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
