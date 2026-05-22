"""
Seeding order:
  1. sport_type        (inline, get-or-create)
  2. account_role      (inline, get-or-create)
  3. clubs             (7 clubs across different sports and cities)
  4. accounts          (club owners + team managers)
  5. teams             (4-5 teams per club, all with managers)
  6. ladders           (14+ ladders, 2 per club minimum)
  7. ladder_team       (every team registered in at least 1 ladder)
  8. matches           (all 5 status types + disputed per ladder, 20+ each)
  9. player demo data  (unchanged from original)
"""

import datetime
import hashlib
from werkzeug.security import generate_password_hash
from server.extensions import db
from server.app.models.availability_block import AvailabilityBlock
from server.app.models.sport_type import SportType
from server.app.models.match_rule import MatchRuleSet
from server.app.models.account import Account, TeamManager, Administrator
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
from server.app.models.match import (
    MatchAccepted, MatchCancelled, MatchPlayed, MatchProposal,
    MatchRejected, MatchScoreSubmission, MatchStatus, SubmissionRole,
    teams_share_players,
)
from server.app.services.weekly_match_proposal_service import (
    generate_weekly_match_proposals, next_week_start,
)

TAG = "[seed:teams_and_users]"
DEFAULT_SEED_GENDER = "other"


# ---------------------------------------------------------------------------
# Generic helpers (unchanged from original)
# ---------------------------------------------------------------------------

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


def _fake_phone_for_email(email: str) -> str:
    digest = hashlib.sha1(email.encode("utf-8")).hexdigest()
    return f"+32 470 {digest[0:2]} {digest[2:4]} {digest[4:6]}"


def make_account(
    first: str,
    last: str,
    email: str,
    role: AccountRole,
    password: str = "Password123!",
    force_password_update: bool = False,
    gender: str = DEFAULT_SEED_GENDER,
    phone: str | None = None,
) -> tuple:
    """Returns (account, created: bool)."""
    existing = Account.query.filter_by(email=email).first()
    if existing:
        if force_password_update:
            existing.password_hash = generate_password_hash(password)
        desired_phone = phone or _fake_phone_for_email(email)
        if existing.gender != gender:
            existing.gender = gender
        if existing.phone != desired_phone:
            existing.phone = desired_phone
        return existing, False
    desired_phone = phone or _fake_phone_for_email(email)
    acc = Account(
        first_name=first,
        last_name=last,
        email=email,
        password_hash=generate_password_hash(password),
        account_role_id=role.id,
        date_of_birth=datetime.date(1990, 1, 1),
        gender=gender,
        phone=desired_phone,
        is_verified=True,
    )
    db.session.add(acc)
    db.session.flush()
    return acc, True


def make_manager(account: Account) -> tuple:
    if account.team_manager:
        return account.team_manager, False
    tm = TeamManager(id=account.id)
    db.session.add(tm)
    db.session.flush()
    return tm, True


def make_player(account: Account) -> tuple:
    if account.player:
        return account.player, False
    p = Player(id=account.id)
    db.session.add(p)
    db.session.flush()
    return p, True


def make_team(name: str, sport: SportType, club_id=None, verbose: bool = True) -> tuple:
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
    if team_manager.club_owner:
        return team_manager.club_owner, False
    owner = ClubOwner(id=team_manager.id)
    db.session.add(owner)
    db.session.flush()
    return owner, True


def make_admin(account: Account, access_level: int = 1) -> tuple:
    existing = Administrator.query.filter_by(id=account.id).first()
    if existing:
        existing.access_level = access_level
        db.session.flush()
        return existing, False
    admin = Administrator(id=account.id, access_level=access_level)
    db.session.add(admin)
    db.session.flush()
    return admin, True


def ensure_owner_of_club(club_owner: ClubOwner, club: Club) -> bool:
    existing = ClubOwnerClub.query.filter_by(
        club_owner_id=club_owner.id, club_id=club.id
    ).first()
    if existing:
        return False
    db.session.add(ClubOwnerClub(
        club_owner_id=club_owner.id,
        club_id=club.id,
        can_rename=True,
        can_change_description=True,
        can_manage_match=True,
        can_add_club_players=True,
        can_add_club_owners=True,
        can_add_club_rule=True,
    ))
    db.session.flush()
    return True


def assign_manager_to_team(
    tm: TeamManager,
    team: Team,
    can_rename: bool = True,
    can_delete: bool = True,
    can_edit_players: bool = True,
    can_edit_managers: bool = True,
    can_manage_match: bool = True,
) -> bool:
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
    existing = PlayerTeam.query.filter_by(
        player_id=player.id, team_id=team.id
    ).first()
    if existing:
        return False
    db.session.add(PlayerTeam(player_id=player.id, team_id=team.id))
    db.session.flush()
    return True


def ensure_player_on_team(account: Account, team: Team) -> bool:
    player, _ = make_player(account)
    return assign_player_to_team(player, team)


def ensure_team_players_in_club(team: Team, club: Club) -> int:
    created = 0
    player_ids = [row.player_id for row in PlayerTeam.query.filter_by(team_id=team.id).all()]
    for pid in player_ids:
        if not ClubPlayer.query.filter_by(club_id=club.id, player_id=pid).first():
            db.session.add(ClubPlayer(club_id=club.id, player_id=pid))
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


def get_match_ruleset_id(name: str, fallback: int | None = None) -> int | None:
    ruleset = MatchRuleSet.query.filter(db.func.lower(MatchRuleSet.name) == name.lower()).first()
    if ruleset:
        return int(ruleset.id)
    return fallback


def get_or_create_ladder(
    club_id, name, description, sport_type_id,
    ladder_rating_function_id, ruleset_id=None,
) -> tuple:
    existing = Ladder.query.filter_by(club_id=club_id, name=name).first()
    if existing:
        updated = False
        for attr, val in [
            ("description", description),
            ("sport_type_id", sport_type_id),
            ("ladder_rating_function_id", ladder_rating_function_id),
            ("ruleset_id", ruleset_id),
        ]:
            if val is not None and getattr(existing, attr) != val:
                setattr(existing, attr, val)
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


def get_or_create_ladder_team(
    ladder_id, team_id, rank, rating, matches_played
) -> tuple:
    existing = LadderTeam.query.filter_by(
        ladder_id=ladder_id, team_id=team_id
    ).first()
    if existing:
        updated = False
        for attr, val in [
            ("rank", rank), ("rating", rating), ("matches_played", matches_played)
        ]:
            if getattr(existing, attr) != val:
                setattr(existing, attr, val)
                updated = True
        return existing, updated
    row = LadderTeam(
        ladder_id=ladder_id, team_id=team_id,
        rank=rank, rating=rating, matches_played=matches_played,
    )
    db.session.add(row)
    db.session.flush()
    return row, True


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


def _next_occurrence_date(
    weekday: int, reference_date: datetime.date | None = None
) -> datetime.date:
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

    if any(v is None for v in [weekday, start_time, end_time, start_at, end_at]):
        raise ValueError(
            "Availability block requires either datetimes or weekly recurrence fields."
        )

    norm_st = start_time.replace(microsecond=0)
    norm_et = end_time.replace(microsecond=0)

    existing = AvailabilityBlock.query.filter_by(
        user_id=user_id, weekday=weekday,
        start_time=norm_st, end_time=norm_et,
    ).first()
    if existing:
        return existing, False

    block = AvailabilityBlock(
        user_id=user_id, weekday=weekday,
        start_time=norm_st, end_time=norm_et,
        start_at=start_at, end_at=end_at,
    )
    db.session.add(block)
    db.session.flush()
    return block, True


# ---------------------------------------------------------------------------
# Match-seeding helpers (new)
# ---------------------------------------------------------------------------

def _week(offset: int) -> datetime.date:
    """Return a Monday date offset weeks from next Monday."""
    base = next_week_start()
    return base + datetime.timedelta(weeks=offset)


def _dt(date: datetime.date, hour: int = 14, minute: int = 0) -> datetime.datetime:
    return datetime.datetime.combine(date, datetime.time(hour, minute))


def _make_proposal(
    *,
    team1_id: int,
    team2_id: int,
    sport_type_id: int,
    ladder_id: int,
    proposed_by_user_id: int,
    week_start_date: datetime.date,
    proposed_start_at: datetime.datetime,
    proposed_end_at: datetime.datetime,
    location: str | None = None,
    status_id: int = MatchStatus.PENDING,
) -> MatchProposal | None:
    """
    Create a MatchProposal only if none exists yet for this
    (ladder_id, team1_id, team2_id, week_start_date) combination.
    Teams are stored in ascending id order to match the unique constraint.
    Returns the new proposal or None if it already existed.
    """
    t1, t2 = sorted((team1_id, team2_id))
    existing = MatchProposal.query.filter_by(
        ladder_id=ladder_id,
        team1_id=t1,
        team2_id=t2,
        week_start_date=week_start_date,
    ).first()
    if existing:
        return None
    team1 = db.session.get(Team, t1)
    team2 = db.session.get(Team, t2)
    if teams_share_players(team1, team2):
        return None
    proposal = MatchProposal(
        proposed_by_user_id=proposed_by_user_id,
        sport_type_id=sport_type_id,
        ladder_id=ladder_id,
        team1_id=t1,
        team2_id=t2,
        status_id=status_id,
        week_start_date=week_start_date,
        proposed_start_at=proposed_start_at,
        proposed_end_at=proposed_end_at,
        location=location,
    )
    db.session.add(proposal)
    db.session.flush()
    return proposal


def _make_pending(proposal: MatchProposal) -> None:
    """Ensure proposal is in pending state (no extensions)."""
    proposal.status_id = MatchStatus.PENDING
    for model in (MatchAccepted, MatchRejected, MatchCancelled, MatchPlayed):
        row = db.session.get(model, proposal.id)
        if row:
            db.session.delete(row)
    for sub in list(proposal.score_submissions):
        db.session.delete(sub)
    db.session.flush()


def _make_accepted(proposal: MatchProposal, by_user_id: int) -> None:
    proposal.status_id = MatchStatus.ACCEPTED
    for model in (MatchRejected, MatchCancelled):
        row = db.session.get(model, proposal.id)
        if row:
            db.session.delete(row)
    if not db.session.get(MatchAccepted, proposal.id):
        db.session.add(MatchAccepted(
            id=proposal.id,
            response_by_user_id=by_user_id,
            response_text="Accepted.",
        ))
    db.session.flush()


def _make_rejected(proposal: MatchProposal, by_user_id: int) -> None:
    proposal.status_id = MatchStatus.REJECTED
    for model in (MatchAccepted, MatchCancelled):
        row = db.session.get(model, proposal.id)
        if row:
            db.session.delete(row)
    if not db.session.get(MatchRejected, proposal.id):
        db.session.add(MatchRejected(
            id=proposal.id,
            response_by_user_id=by_user_id,
            response_text="Cannot make it.",
        ))
    db.session.flush()


def _make_cancelled(proposal: MatchProposal, reason: str = "Schedule conflict") -> None:
    proposal.status_id = MatchStatus.CANCELLED
    if not db.session.get(MatchCancelled, proposal.id):
        db.session.add(MatchCancelled(id=proposal.id, reason=reason))
    db.session.flush()


def _make_played(
    proposal: MatchProposal,
    score_t1: int,
    score_t2: int,
    by_user_id: int,
) -> None:
    """Write a directly resolved MatchPlayed row (legacy single-step flow)."""
    proposal.status_id = MatchStatus.PLAYED
    if not db.session.get(MatchPlayed, proposal.id):
        db.session.add(MatchPlayed(
            id=proposal.id,
            score_team1=score_t1,
            score_team2=score_t2,
        ))
    for sub in list(proposal.score_submissions):
        db.session.delete(sub)
    db.session.flush()


def _make_disputed(
    proposal: MatchProposal,
    by_user1_id: int,
    by_user2_id: int,
) -> None:
    """
    Two-sided score submission with disagreeing scores -> disputed state.
    Proposal stays ACCEPTED; no MatchPlayed row is created.
    """
    proposal.status_id = MatchStatus.ACCEPTED
    for model in (MatchRejected, MatchCancelled, MatchPlayed):
        row = db.session.get(model, proposal.id)
        if row:
            db.session.delete(row)
    # Ensure acceptance extension exists
    if not db.session.get(MatchAccepted, proposal.id):
        db.session.add(MatchAccepted(
            id=proposal.id,
            response_by_user_id=by_user2_id,
            response_text="Accepted.",
        ))
    # Clear any existing submissions for this match
    for sub in list(proposal.score_submissions):
        db.session.delete(sub)
    db.session.flush()

    # Submit two different scores
    db.session.add(MatchScoreSubmission(
        match_id=proposal.id,
        submitted_by=by_user1_id,
        submitted_by_role=SubmissionRole.TEAM1_SIDE.value,
        score_team1=3,
        score_team2=1,
        submitted_at=datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=2),
    ))
    db.session.add(MatchScoreSubmission(
        match_id=proposal.id,
        submitted_by=by_user2_id,
        submitted_by_role=SubmissionRole.TEAM2_SIDE.value,
        score_team1=2,
        score_team2=2,
        submitted_at=datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1),
    ))
    db.session.flush()


def seed_ladder_matches(
    *,
    ladder: Ladder,
    teams: list,           # list of Team objects registered in this ladder
    managers: list,        # list of Account objects (managers), one per team (same order)
    sport_type_id: int,
    proposed_by_user_id: int,
    week_offset_start: int,
    pending_count: int = 5,
    accepted_count: int = 5,
    rejected_count: int = 5,
    cancelled_count: int = 5,
    played_count: int = 5,
    disputed_count: int = 5,
) -> dict:
    """
    Seed all match types for one ladder.

    The function cycles through all (team_a, team_b) pairings and
    different week offsets to generate the requested counts.
    Returns a dict with counts per status type.
    """
    assert len(teams) >= 2, "At least 2 teams required to seed matches"
    assert len(managers) == len(teams), "managers list must align with teams list"

    # Build all ordered pairs
    pairs = []
    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            pairs.append((teams[i], teams[j], managers[i], managers[j]))

    counts = {
        "pending": 0, "accepted": 0, "rejected": 0,
        "cancelled": 0, "played": 0, "disputed": 0,
    }
    # Keep a bounded window: enough history for archiving, but never more than
    # 2 weeks ahead so the seeded proposals stay realistic.
    week_offsets = list(range(week_offset_start, week_offset_start + 10))
    pair_week_queue = [
        (t1, t2, m1, m2, _week(offset))
        for offset in week_offsets
        for (t1, t2, m1, m2) in pairs
    ]

    # The seed is idempotent, so on later startups most or all of these slots
    # may already exist. Build the missing-slot list once and iterate over it
    # deterministically instead of looping until a counter increments forever.
    existing_keys = {
        (row.team1_id, row.team2_id, row.week_start_date)
        for row in MatchProposal.query.filter_by(ladder_id=ladder.id)
        .with_entities(
            MatchProposal.team1_id,
            MatchProposal.team2_id,
            MatchProposal.week_start_date,
        )
        .all()
    }

    pair_has_shared_players: dict[tuple[int, int], bool] = {}
    available_slots = []
    for t1, t2, m1, m2, w in pair_week_queue:
        ordered_pair = tuple(sorted((t1.id, t2.id)))
        key = (ordered_pair[0], ordered_pair[1], w)
        if key in existing_keys:
            continue
        if ordered_pair not in pair_has_shared_players:
            pair_has_shared_players[ordered_pair] = teams_share_players(t1, t2)
        if pair_has_shared_players[ordered_pair]:
            continue
        available_slots.append((t1, t2, m1, m2, w))

    if not available_slots:
        return counts

    slot_index = 0

    def _take_slot():
        nonlocal slot_index
        if slot_index >= len(available_slots):
            return None
        slot = available_slots[slot_index]
        slot_index += 1
        return slot

    def _proposal(t1, t2, m1, w):
        start = _dt(w + datetime.timedelta(days=1), hour=14)
        return _make_proposal(
            team1_id=t1.id,
            team2_id=t2.id,
            sport_type_id=sport_type_id,
            ladder_id=ladder.id,
            proposed_by_user_id=m1.id,
            week_start_date=w,
            proposed_start_at=start,
            proposed_end_at=start + datetime.timedelta(hours=2),
            location=f"{ladder.name} Court",
    )

    # --- PENDING ---
    while counts["pending"] < pending_count:
        slot = _take_slot()
        if slot is None:
            break
        t1, t2, m1, m2, w = slot
        p = _proposal(t1, t2, m1, w)
        _make_pending(p)
        counts["pending"] += 1

    # --- ACCEPTED ---
    while counts["accepted"] < accepted_count:
        slot = _take_slot()
        if slot is None:
            break
        t1, t2, m1, m2, w = slot
        p = _proposal(t1, t2, m1, w)
        _make_accepted(p, by_user_id=m2.id)
        counts["accepted"] += 1

    # --- REJECTED ---
    while counts["rejected"] < rejected_count:
        slot = _take_slot()
        if slot is None:
            break
        t1, t2, m1, m2, w = slot
        p = _proposal(t1, t2, m1, w)
        _make_rejected(p, by_user_id=m2.id)
        counts["rejected"] += 1

    # --- CANCELLED ---
    while counts["cancelled"] < cancelled_count:
        slot = _take_slot()
        if slot is None:
            break
        t1, t2, m1, m2, w = slot
        p = _proposal(t1, t2, m1, w)
        _make_accepted(p, by_user_id=m2.id)
        _make_cancelled(p)
        counts["cancelled"] += 1

    # --- PLAYED ---
    while counts["played"] < played_count:
        slot = _take_slot()
        if slot is None:
            break
        t1, t2, m1, m2, w = slot
        p = _proposal(t1, t2, m1, w)
        _make_accepted(p, by_user_id=m2.id)
        _make_played(p, score_t1=2, score_t2=1, by_user_id=m1.id)
        counts["played"] += 1

    # --- DISPUTED ---
    while counts["disputed"] < disputed_count:
        slot = _take_slot()
        if slot is None:
            break
        t1, t2, m1, m2, w = slot
        p = _proposal(t1, t2, m1, w)
        _make_disputed(p, by_user1_id=m1.id, by_user2_id=m2.id)
        counts["disputed"] += 1

    return counts


# ---------------------------------------------------------------------------
# Original helpers required by player-demo section
# ---------------------------------------------------------------------------

def find_match_proposal(
    week_start_date: datetime.date, team1_id: int, team2_id: int
) -> MatchProposal | None:
    t1, t2 = sorted((team1_id, team2_id))
    return MatchProposal.query.filter_by(
        week_start_date=week_start_date, team1_id=t1, team2_id=t2,
    ).first()


def reset_demo_match_proposal_to_pending(
    week_start_date: datetime.date, team1_id: int, team2_id: int
) -> None:
    proposal = find_match_proposal(week_start_date, team1_id, team2_id)
    if not proposal:
        return
    _make_pending(proposal)


def set_match_proposal_pending(
    *,
    week_start_date: datetime.date,
    team1_id: int,
    team2_id: int,
    proposed_by_user_id: int | None = None,
) -> bool:
    proposal = find_match_proposal(week_start_date, team1_id, team2_id)
    if not proposal:
        return False
    _make_pending(proposal)
    if proposed_by_user_id is not None:
        proposal.proposed_by_user_id = proposed_by_user_id
    db.session.flush()
    return True


def set_match_proposal_accepted(
    *,
    week_start_date: datetime.date,
    team1_id: int,
    team2_id: int,
    accepted_by_user_id: int,
    response_text: str | None = None,
) -> bool:
    proposal = find_match_proposal(week_start_date, team1_id, team2_id)
    if not proposal:
        return False
    _make_accepted(proposal, by_user_id=accepted_by_user_id)
    accepted = db.session.get(MatchAccepted, proposal.id)
    if accepted and response_text:
        accepted.response_text = response_text
    db.session.flush()
    return True


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
    t1, t2 = sorted((team1_id, team2_id))
    if MatchProposal.query.filter_by(
        week_start_date=week_start_date, team1_id=t1, team2_id=t2
    ).first():
        return False
    team1 = db.session.get(Team, t1)
    team2 = db.session.get(Team, t2)
    if teams_share_players(team1, team2):
        return False
    db.session.add(MatchProposal(
        proposed_by_user_id=proposed_by_user_id,
        sport_type_id=sport_type_id,
        team1_id=t1,
        team2_id=t2,
        status_id=MatchStatus.PENDING,
        week_start_date=week_start_date,
        proposed_start_at=proposed_start_at,
        proposed_end_at=proposed_end_at,
        location=location,
    ))
    db.session.flush()
    return True


# ---------------------------------------------------------------------------
# Main seed
# ---------------------------------------------------------------------------

def seed_teams_and_users(verbose: bool = True) -> None:
    log(f"{TAG} Starting seed", verbose)

    # ------------------------------------------------------------------
    # 1. Roles
    # ------------------------------------------------------------------
    log(f"{TAG} [1/8] Seeding account roles...", verbose)
    try:
        role_manager = get_or_create_role("team_manager", verbose)
        role_player  = get_or_create_role("player", verbose)
        role_admin   = get_or_create_role("administrator", verbose)
        get_or_create_role("user", verbose)
    except Exception as e:
        print(f"{TAG} ERROR seeding roles: {e}")
        db.session.rollback()
        raise
    log(f"{TAG} [1/8] Roles OK", verbose)

    # ------------------------------------------------------------------
    # 2. Sport types
    # ------------------------------------------------------------------
    log(f"{TAG} [2/8] Seeding sport types...", verbose)
    try:
        football   = get_or_create_sport("Football",   11, 23, verbose)
        basketball = get_or_create_sport("Basketball",  5, 12, verbose)
        volleyball = get_or_create_sport("Volleyball",  6, 14, verbose)
        tennis     = get_or_create_sport("Tennis",      1,  4, verbose)
        padel      = get_or_create_sport("Padel",       2,  4, verbose)
        hockey     = get_or_create_sport("Hockey",     11, 22, verbose)
        squash     = get_or_create_sport("Squash",      1,  2, verbose)
    except Exception as e:
        print(f"{TAG} ERROR seeding sport types: {e}")
        db.session.rollback()
        raise
    log(f"{TAG} [2/8] Sport types OK", verbose)

    rating_fn_id = ensure_default_ladder_rating_function()
    ruleset_id   = ensure_default_match_ruleset()
    tennis_ruleset_id = get_match_ruleset_id("Standaard Tennis Enkel", ruleset_id)
    padel_ruleset_id = get_match_ruleset_id("Standaard Padel", ruleset_id)

    # ------------------------------------------------------------------
    # 3. Club owners (each will own one club)
    # ------------------------------------------------------------------
    log(f"{TAG} [3/8] Seeding clubs and owners...", verbose)

    OWNER_DATA = [
        # (first, last, email, password,   club_name,                  city,        sport)
        ("Jeremi",   "Lorek",     "jeremilorek@outlook.com",        "qwertyuiop",  "NetRank Club",             "Antwerp",  tennis),
        ("Nina",     "Jacobs",    "nina.jacobs@example.com",        "Password123!", "Antwerp Padel House",      "Antwerp",  padel),
        ("Stefan",   "Bauwens",   "stefan.bauwens@example.com",     "Password123!", "Brussels FC",              "Brussels", football),
        ("Lieselot", "Vermeersch","lieselot.vermeersch@example.com", "Password123!", "Ghent Volleyball Academy", "Ghent",    volleyball),
        ("Remi",     "Deschamps", "remi.deschamps@example.com",     "Password123!", "Bruges Basketball Club",   "Bruges",   basketball),
        ("Hilde",    "Goossens",  "hilde.goossens@example.com",     "Password123!", "Leuven Hockey Union",      "Leuven",   hockey),
        ("Axel",     "Fontaine",  "axel.fontaine@example.com",      "Password123!", "Liege Squash Centre",      "Liege",    squash),
    ]

    owners = []   # list of (Account, TeamManager, ClubOwner, Club, SportType)
    try:
        for first, last, email, pwd, club_name, city, sport in OWNER_DATA:
            gender = "male" if email == "jeremilorek@outlook.com" else DEFAULT_SEED_GENDER
            phone = "+32 470 11 22 33" if email == "jeremilorek@outlook.com" else None
            acc, _  = make_account(first, last, email, role_manager,
                                   password=pwd, force_password_update=True,
                                   gender=gender, phone=phone)
            if not acc.is_verified:
                acc.is_verified = True
            tm, _   = make_manager(acc)
            co, _   = make_club_owner(tm)
            club, _ = get_or_create_club(
                club_name, sport_type_id=sport.id, city=city,
                description=f"Official {sport.name} club based in {city}.",
            )
            ensure_owner_of_club(co, club)
            owners.append((acc, tm, co, club, sport))
            log(f"{TAG}   owner '{email}' -> club '{club_name}'", verbose)

        admin_acc, _ = make_account(
            "Admin",
            "Tester",
            "admin@netrank.test",
            role_admin,
            password="admin12345",
            force_password_update=True,
        )
        if not admin_acc.is_verified:
            admin_acc.is_verified = True
        make_admin(admin_acc, access_level=1)
        log(f"{TAG}   admin account 'admin@netrank.test' created/updated", verbose)
    except Exception as e:
        print(f"{TAG} ERROR seeding clubs/owners: {e}")
        db.session.rollback()
        raise

    # Also keep a "Player Demo Club" (no owner from OWNER_DATA)
    player_demo_club, _ = get_or_create_club(
        "Player Demo Club",
        sport_type_id=tennis.id,
        description="Player-focused club for match request and acceptance demo.",
        city="Ghent",
    )
    log(f"{TAG} [3/8] Clubs and owners OK", verbose)

    # ------------------------------------------------------------------
    # 4. Teams — 4 teams per club (28 total across 7 clubs + demo teams)
    # ------------------------------------------------------------------
    log(f"{TAG} [4/8] Seeding teams...", verbose)

    # (club_index, team_name)   — club_index maps into owners[]
    TEAM_SPECS = [
        # NetRank Club (tennis) - idx 0
        (0, "NetRank Aces"),
        (0, "NetRank Juniors"),
        (0, "NetRank Challengers"),
        (0, "NetRank Masters"),
        # Antwerp Padel House (padel) - idx 1
        (1, "Antwerp Padel Elite"),
        (1, "Scheldt Smashers"),
        (1, "South Court Pairs"),
        (1, "Riverside Ralliers"),
        # Brussels FC (football) - idx 2
        (2, "Brussels Blades"),
        (2, "Capital Kickers"),
        (2, "Atomium Athletic"),
        (2, "Grand Place United"),
        # Ghent Volleyball Academy (volleyball) - idx 3
        (3, "Ghent Spikers"),
        (3, "Leie Blockers"),
        (3, "Canal Jumpers"),
        (3, "Textile Tigers"),
        # Bruges Basketball Club (basketball) - idx 4
        (4, "Bruges Ballers"),
        (4, "Belfry Dunkers"),
        (4, "Swan Lake Shooters"),
        (4, "Market Square Mavs"),
        # Leuven Hockey Union (hockey) - idx 5
        (5, "Leuven Lions"),
        (5, "Stella Strikers"),
        (5, "KU Sticks"),
        (5, "Dyle Defenders"),
        # Liege Squash Centre (squash) - idx 6
        (6, "Liege Ralliers"),
        (6, "Meuse Mashers"),
        (6, "Ardennes Aces"),
        (6, "Citadel Smashers"),
    ]

    club_teams = {}  # club_index -> list of Team
    try:
        for club_idx, team_name in TEAM_SPECS:
            _, _, _, club, sport = owners[club_idx]
            team, _ = make_team(team_name, sport, club_id=club.id, verbose=verbose)
            club_teams.setdefault(club_idx, []).append(team)
    except Exception as e:
        print(f"{TAG} ERROR seeding teams: {e}")
        db.session.rollback()
        raise
    log(f"{TAG} [4/8] Teams OK", verbose)

    # ------------------------------------------------------------------
    # 5. Team managers — one dedicated manager per team
    # ------------------------------------------------------------------
    log(f"{TAG} [5/8] Seeding team managers...", verbose)

    MANAGER_EMAILS = [
        # Tennis (4)
        "mgr.aces@example.com",
        "mgr.juniors@example.com",
        "mgr.challengers@example.com",
        "mgr.masters@example.com",
        # Padel (4)
        "mgr.elite@example.com",
        "mgr.smashers@example.com",
        "mgr.southcourt@example.com",
        "mgr.riverside@example.com",
        # Football (4)
        "mgr.blades@example.com",
        "mgr.kickers@example.com",
        "mgr.atomium@example.com",
        "mgr.grandplace@example.com",
        # Volleyball (4)
        "mgr.spikers@example.com",
        "mgr.blockers@example.com",
        "mgr.jumpers@example.com",
        "mgr.tigers@example.com",
        # Basketball (4)
        "mgr.ballers@example.com",
        "mgr.dunkers@example.com",
        "mgr.shooters@example.com",
        "mgr.mavs@example.com",
        # Hockey (4)
        "mgr.lions@example.com",
        "mgr.stella@example.com",
        "mgr.kusticks@example.com",
        "mgr.dyle@example.com",
        # Squash (4)
        "mgr.ralliers@example.com",
        "mgr.meuse@example.com",
        "mgr.ardennes@example.com",
        "mgr.citadel@example.com",
    ]

    MANAGER_NAMES = [
        ("Liam", "Carter"), ("Noah", "Brooks"), ("Oliver", "Hayes"), ("Elijah", "Foster"),
        ("James", "Ward"),  ("Aiden", "Cox"),   ("Lucas", "Griffin"), ("Mason", "Reed"),
        ("Ethan", "Bell"),  ("Logan", "Howard"),("Jacob", "Price"),  ("Ryan", "Barnes"),
        ("Daniel", "Ross"), ("Jack", "Henderson"),("Owen", "Coleman"),("Samuel", "Jenkins"),
        ("Wyatt", "Perry"), ("Dylan", "Powell"),("Caleb", "Long"),  ("Hunter", "Patterson"),
        ("Evan", "Hughes"), ("Nathan", "Flores"),("Connor", "Washington"),("Luke", "Butler"),
        ("Gavin", "Simmons"),("Blake", "Murphy"),("Austin", "Rivera"),("Landon", "Cooper"),
    ]

    # Flat list of all teams in the same order as MANAGER_EMAILS
    all_teams_flat = []
    for ci in range(7):
        all_teams_flat.extend(club_teams[ci])

    team_managers = {}  # team.id -> Account
    try:
        for i, (email, (first, last)) in enumerate(zip(MANAGER_EMAILS, MANAGER_NAMES)):
            team = all_teams_flat[i]
            acc, _ = make_account(first, last, email, role_manager)
            tm, _  = make_manager(acc)
            assign_manager_to_team(tm, team)
            # Also let the club owner manage each team in their club
            club_idx = i // 4
            owner_tm = owners[club_idx][1]
            assign_manager_to_team(owner_tm, team)
            team_managers[team.id] = acc
            log(f"{TAG}   manager '{email}' -> '{team.name}'", verbose)
    except Exception as e:
        print(f"{TAG} ERROR seeding team managers: {e}")
        db.session.rollback()
        raise
    log(f"{TAG} [5/8] Team managers OK", verbose)

    TEAM_PLAYER_ROSTER = [
        ("Alice",  "Moore",     "alice.moore@example.com"),
        ("Bob",    "Taylor",    "bob.taylor@example.com"),
        ("Carol",  "Anderson",  "carol.anderson@example.com"),
        ("Dave",   "Thomas",    "dave.thomas@example.com"),
        ("Eve",    "Jackson",   "eve.jackson@example.com"),
        ("Frank",  "White",     "frank.white@example.com"),
        ("Grace",  "Harris",    "grace.harris@example.com"),
        ("Henry",  "Martin",    "henry.martin@example.com"),
        ("Iris",   "Garcia",    "iris.garcia@example.com"),
        ("Jake",   "Martinez",  "jake.martinez@example.com"),
        ("Karen",  "Robinson",  "karen.robinson@example.com"),
        ("Leo",    "Clark",     "leo.clark@example.com"),
        ("Mia",    "Rodriguez", "mia.rodriguez@example.com"),
        ("Nick",   "Lewis",     "nick.lewis@example.com"),
        ("Olivia", "Lee",       "olivia.lee@example.com"),
        ("Paul",   "Walker",    "paul.walker@example.com"),
        ("Quinn",  "Hall",      "quinn.hall@example.com"),
        ("Rachel", "Allen",     "rachel.allen@example.com"),
        ("Steve",  "Young",     "steve.young@example.com"),
        ("Tina",   "Hernandez", "tina.hernandez@example.com"),
        ("Uma",    "King",      "uma.king@example.com"),
        ("Victor", "Wright",    "victor.wright@example.com"),
        ("Wendy",  "Lopez",     "wendy.lopez@example.com"),
        ("Xander", "Hill",      "xander.hill@example.com"),
        ("Yara",   "Scott",     "yara.scott@example.com"),
        ("Zack",   "Green",     "zack.green@example.com"),
        ("Amy",    "Adams",     "amy.adams@example.com"),
        ("Brian",  "Baker",     "brian.baker@example.com"),
    ]
    try:
        for i, (team, (first_name, last_name, email)) in enumerate(zip(all_teams_flat, TEAM_PLAYER_ROSTER)):
            club_idx = i // 4
            acc, _ = make_account(first_name, last_name, email, role_player)
            ensure_player_on_team(acc, team)
            ensure_team_players_in_club(team, owners[club_idx][3])
            get_or_create_availability_block(
                acc.id,
                weekday=2,
                start_time=datetime.time(hour=18, minute=0),
                end_time=datetime.time(hour=20, minute=0),
            )
            log(f"{TAG}   player '{email}' -> '{team.name}'", verbose)

        padel_extra_players = [
            ("Paula", "De Smet", "paula.desmet@example.com"),
            ("Simon", "Verstraete", "simon.verstraete@example.com"),
            ("Tess", "Hermans", "tess.hermans@example.com"),
            ("Wout", "De Bruyne", "wout.debruyne@example.com"),
        ]
        for team, (first_name, last_name, email) in zip(club_teams[1], padel_extra_players):
            acc, _ = make_account(first_name, last_name, email, role_player)
            ensure_player_on_team(acc, team)
            ensure_team_players_in_club(team, owners[1][3])
            get_or_create_availability_block(
                acc.id,
                weekday=2,
                start_time=datetime.time(hour=18, minute=0),
                end_time=datetime.time(hour=20, minute=0),
            )
            log(f"{TAG}   extra padel player '{email}' -> '{team.name}'", verbose)
    except Exception as e:
        print(f"{TAG} ERROR seeding team players: {e}")
        db.session.rollback()
        raise
    log(f"{TAG} [5/8] Team players OK", verbose)

    # ------------------------------------------------------------------
    # 6. Ladders — 2 ladders per club = 14 total
    # ------------------------------------------------------------------
    log(f"{TAG} [6/8] Seeding ladders...", verbose)

    LADDER_SPECS = [
        # NetRank Club (tennis) - idx 0
        (0, "Men's Singles", "Primary competitive singles ladder using ELO."),
        (0, "U14 Singles",   "Junior development ladder with weekly fixtures."),
        # Antwerp Padel House (padel) - idx 1
        (1, "Padel Premier Ladder",    "Top padel ladder for advanced doubles teams."),
        (1, "Padel Community Ladder",  "Community padel ladder for friendly challenges."),
        # Brussels FC (football) - idx 2
        (2, "Brussels League Alpha",   "Top-tier football competition in Brussels."),
        (2, "Brussels League Beta",    "Development league for emerging football squads."),
        # Ghent Volleyball Academy (volleyball) - idx 3
        (3, "Ghent Open Ladder",       "Open volleyball ladder for all skill levels."),
        (3, "Ghent Elite Series",      "Elite competition for top volleyball teams."),
        # Bruges Basketball Club (basketball) - idx 4
        (4, "Bruges 3v3 Circuit",      "Fast-paced 3v3 basketball ladder."),
        (4, "Bruges Full Court League","Full 5v5 competitive basketball ladder."),
        # Leuven Hockey Union (hockey) - idx 5
        (5, "Leuven Field Hockey Cup", "Main outdoor field hockey ladder."),
        (5, "Leuven Indoor Series",    "Winter indoor hockey competition."),
        # Liege Squash Centre (squash) - idx 6
        (6, "Liege Open Squash",       "Open squash ladder for all club members."),
        (6, "Liege Masters Squash",    "Invitation-only masters squash ladder."),
    ]

    ladders = {}  # (club_idx, ladder_name) -> Ladder
    try:
        for club_idx, ladder_name, desc in LADDER_SPECS:
            _, _, _, club, sport = owners[club_idx]
            ladder_ruleset_id = tennis_ruleset_id if club_idx == 0 else padel_ruleset_id if club_idx == 1 else ruleset_id
            ladder, _ = get_or_create_ladder(
                club.id, ladder_name, desc, sport.id, rating_fn_id, ladder_ruleset_id,
            )
            ladders[(club_idx, ladder_name)] = ladder
            log(f"{TAG}   ladder '{ladder_name}' in club '{club.name}'", verbose)
    except Exception as e:
        print(f"{TAG} ERROR seeding ladders: {e}")
        db.session.rollback()
        raise
    log(f"{TAG} [6/8] Ladders OK — total: {len(ladders)}", verbose)

    # ------------------------------------------------------------------
    # 7. Register teams in ladders and seed all match types
    # ------------------------------------------------------------------
    log(f"{TAG} [7/8] Seeding ladder teams + matches...", verbose)

    # Each club has 2 ladders; we put all 4 teams in both ladders.
    # Ladder 0 (of the pair): teams 0+1+2+3
    # Ladder 1 (of the pair): teams 1+2+3+0 (rotate to give different pairings)
    LADDER_NAME_PAIRS = [
        ("Men's Singles",          "U14 Singles"),
        ("Padel Premier Ladder",   "Padel Community Ladder"),
        ("Brussels League Alpha",  "Brussels League Beta"),
        ("Ghent Open Ladder",      "Ghent Elite Series"),
        ("Bruges 3v3 Circuit",     "Bruges Full Court League"),
        ("Leuven Field Hockey Cup","Leuven Indoor Series"),
        ("Liege Open Squash",      "Liege Masters Squash"),
    ]

    RATINGS_A = [1300, 1250, 1200, 1150]
    RATINGS_B = [1280, 1220, 1180, 1130]

    total_matches = 0
    try:
        for club_idx, (name_a, name_b) in enumerate(LADDER_NAME_PAIRS):
            teams_in_club = club_teams[club_idx]          # 4 teams
            ladder_a = ladders[(club_idx, name_a)]
            ladder_b = ladders[(club_idx, name_b)]
            sport_id = owners[club_idx][4].id

            # Register all 4 teams in ladder A
            for rank, team in enumerate(teams_in_club, start=1):
                get_or_create_ladder_team(
                    ladder_a.id, team.id,
                    rank=rank, rating=RATINGS_A[rank - 1], matches_played=20,
                )

            # Register teams 1-3 + 0 (rotated) in ladder B
            rotated = teams_in_club[1:] + [teams_in_club[0]]
            for rank, team in enumerate(rotated, start=1):
                get_or_create_ladder_team(
                    ladder_b.id, team.id,
                    rank=rank, rating=RATINGS_B[rank - 1], matches_played=15,
                )

            # Resolve manager accounts for each team
            mgrs = [team_managers[t.id] for t in teams_in_club]
            rot_mgrs = [team_managers[t.id] for t in rotated]

            # Seed 20+ of each match type per ladder (30 total each type across both)
            for local_slot, (ladder, t_list, m_list) in enumerate([
                (ladder_a, teams_in_club, mgrs),
                (ladder_b, rotated, rot_mgrs),
            ]):
                week_offset_start = -137 + ((club_idx * 2 + local_slot) * 10)
                counts = seed_ladder_matches(
                    ladder=ladder,
                    teams=t_list,
                    managers=m_list,
                    sport_type_id=sport_id,
                    proposed_by_user_id=owners[club_idx][0].id,
                    week_offset_start=week_offset_start,
                    pending_count=10,
                    accepted_count=10,
                    rejected_count=10,
                    cancelled_count=10,
                    played_count=10,
                    disputed_count=10,
                )
                total_matches += sum(counts.values())
                log(
                    f"{TAG}   ladder '{ladder.name}': "
                    + ", ".join(f"{k}={v}" for k, v in counts.items()),
                    verbose,
                )

        # Give NetRank Club a few near-future proposals so Jeremi sees active
        # matches in the dashboard without opening the archived history.
        jeremi_acc = owners[0][0]
        jeremi_club = owners[0][3]
        jeremi_sport = owners[0][4]
        future_week_start = next_week_start()
        future_start = datetime.datetime.combine(
            future_week_start + datetime.timedelta(days=2),
            datetime.time(hour=18, minute=0),
        )
        future_end = future_start + datetime.timedelta(hours=1)
        future_pairs = [
            (club_teams[0][0], club_teams[0][1]),
            (club_teams[0][2], club_teams[0][3]),
            (club_teams[0][0], club_teams[0][2]),
        ]
        future_created = 0
        future_week_pairs = []
        for team1, team2 in future_pairs:
            future_week_pairs.append((team1, team2))
            if ensure_pending_proposal(
                week_start_date=future_week_start,
                team1_id=team1.id,
                team2_id=team2.id,
                proposed_by_user_id=jeremi_acc.id,
                sport_type_id=jeremi_sport.id,
                proposed_start_at=future_start,
                proposed_end_at=future_end,
                location=f"{jeremi_club.name} main court",
            ):
                future_created += 1
        if future_week_pairs:
            accepted_team1, accepted_team2 = future_week_pairs[0]
            set_match_proposal_accepted(
                week_start_date=future_week_start,
                team1_id=accepted_team1.id,
                team2_id=accepted_team2.id,
                accepted_by_user_id=team_managers[accepted_team2.id].id,
                response_text="Accepted by the opposing team manager for status demo.",
            )

        # Add more future fixtures for NetRank Club so the homepage has enough rows to exercise "load more".
        extra_future_matches = [
            # Keep the extra fixtures inside the seed window so weekly-proposal tests
            # still see the latest proposal week within the allowed range.
            (club_teams[0][1], club_teams[0][2], 0),
            (club_teams[0][2], club_teams[0][3], 0),
            (club_teams[0][0], club_teams[0][3], 1),
        ]
        extra_created = 0
        for team1, team2, week_offset in extra_future_matches:
            extra_week_start = future_week_start + datetime.timedelta(weeks=week_offset)
            extra_start = datetime.datetime.combine(
                extra_week_start + datetime.timedelta(days=2),
                datetime.time(hour=18, minute=0),
            )
            extra_end = extra_start + datetime.timedelta(hours=1)
            if ensure_pending_proposal(
                week_start_date=extra_week_start,
                team1_id=team1.id,
                team2_id=team2.id,
                proposed_by_user_id=jeremi_acc.id,
                sport_type_id=jeremi_sport.id,
                proposed_start_at=extra_start,
                proposed_end_at=extra_end,
                location=f"{jeremi_club.name} showcase court",
            ):
                extra_created += 1
                set_match_proposal_accepted(
                    week_start_date=extra_week_start,
                    team1_id=team1.id,
                    team2_id=team2.id,
                    accepted_by_user_id=team_managers[team2.id].id,
                    response_text="Accepted for club homepage demo.",
                )
        total_matches += future_created + extra_created
        log(
            f"{TAG}   future NetRank proposals: created={future_created + extra_created}, "
            f"week_start={future_week_start.isoformat()}",
            verbose,
        )
    except Exception as e:
        print(f"{TAG} ERROR seeding ladder teams/matches: {e}")
        db.session.rollback()
        raise
    log(f"{TAG} [7/8] Ladder teams + matches OK — total match records: {total_matches}", verbose)

    # ------------------------------------------------------------------
    # 8. Player demo section (preserved from original seed)
    # ------------------------------------------------------------------
    log(f"{TAG} [8/8] Seeding player demo data...", verbose)
    try:
        jeremi_acc = owners[0][0]  # jeremilorek@outlook.com
        asst_acc   = owners[1][0]  # nina.jacobs@example.com
        asst_tm    = owners[1][1]

        player_demo_team,     _ = make_team("Player Demo A", tennis, club_id=player_demo_club.id, verbose=verbose)
        player_demo_opponent, _ = make_team("Player Demo B", tennis, club_id=player_demo_club.id, verbose=verbose)
        assign_manager_to_team(asst_tm, player_demo_team)
        assign_manager_to_team(asst_tm, player_demo_opponent)

        player_demo_ladder, _ = get_or_create_ladder(
            club_id=player_demo_club.id,
            name="Player Demo Singles",
            description="Demo ladder where Jeremi is only a player.",
            sport_type_id=tennis.id,
            ladder_rating_function_id=rating_fn_id,
            ruleset_id=tennis_ruleset_id,
        )
        get_or_create_ladder_team(player_demo_ladder.id, player_demo_team.id,     rank=1, rating=1110, matches_played=3)
        get_or_create_ladder_team(player_demo_ladder.id, player_demo_opponent.id, rank=2, rating=1090, matches_played=3)

        opponent_acc, _ = make_account("Robin", "Vermeulen", "robin.vermeulen@example.com", role_player)
        ensure_player_on_team(jeremi_acc, player_demo_team)
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
            get_or_create_availability_block(jeremi_acc.id, weekly_start, weekly_end)
            get_or_create_availability_block(
                opponent_acc.id,
                weekly_start + datetime.timedelta(minutes=15),
                weekly_end,
            )
            result = generate_weekly_match_proposals(
                proposed_by_user_id=jeremi_acc.id,
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
            total_created += result["created_count"]
            total_skipped += result["skipped_count"]

        log(
            f"{TAG}   player demo proposals: "
            f"created={total_created}, skipped={total_skipped}",
            verbose,
        )

        if player_demo_weeks:
            set_match_proposal_pending(
                week_start_date=player_demo_weeks[0],
                team1_id=player_demo_team.id,
                team2_id=player_demo_opponent.id,
                proposed_by_user_id=opponent_acc.id,
            )
        if len(player_demo_weeks) > 1:
            set_match_proposal_accepted(
                week_start_date=player_demo_weeks[1],
                team1_id=player_demo_team.id,
                team2_id=player_demo_opponent.id,
                accepted_by_user_id=opponent_acc.id,
                response_text="Accepted by opponent for dashboard upcoming matches demo",
            )

        jeremi_team = club_teams[0][0]
        future_opponent_team = club_teams[0][2]
        future_match_date = datetime.date.today() + datetime.timedelta(days=3)
        future_match_week_start = future_match_date - datetime.timedelta(days=future_match_date.weekday())
        future_match_start = datetime.datetime.combine(
            future_match_date,
            datetime.time(hour=19, minute=0),
        )
        created_future_match = ensure_pending_proposal(
            week_start_date=future_match_week_start,
            team1_id=jeremi_team.id,
            team2_id=future_opponent_team.id,
            proposed_by_user_id=jeremi_acc.id,
            sport_type_id=tennis.id,
            proposed_start_at=future_match_start,
            proposed_end_at=future_match_start + datetime.timedelta(hours=1),
            location="NetRank Club Court 1",
        )
        if not created_future_match:
            set_match_proposal_pending(
                week_start_date=future_match_week_start,
                team1_id=jeremi_team.id,
                team2_id=future_opponent_team.id,
                proposed_by_user_id=jeremi_acc.id,
            )
        future_match = find_match_proposal(
            future_match_week_start,
            jeremi_team.id,
            future_opponent_team.id,
        )
        if future_match:
            future_match.proposed_by_user_id = jeremi_acc.id
            future_match.proposed_start_at = future_match_start
            future_match.proposed_end_at = future_match_start + datetime.timedelta(hours=1)
            future_match.location = "NetRank Club Court 1"
            future_match.sport_type_id = tennis.id

        lrk_manager_acc, _ = make_account(
            "LRK",
            "Manager",
            "lrk.j@outlook.com",
            role_manager,
            password="qwertyuiop",
            force_password_update=True,
        )
        fake_player_a, _ = make_account(
            "Manager",
            "DemoA",
            "manager.demo.a@example.com",
            role_player,
            password="Password123!",
            force_password_update=True,
        )
        fake_player_b, _ = make_account(
            "Manager",
            "DemoB",
            "manager.demo.b@example.com",
            role_player,
            password="Password123!",
            force_password_update=True,
        )
        lrk_acc, _ = make_account(
            "LRK",
            "Debug",
            "lrk.j@outlook.com",
            role_player,
            password="qwertyuiop",
            force_password_update=True,
        )

        # Manager-only demo fixture:
        # Jeremi is a club owner elsewhere in the seed, but this match should
        # still resolve through his team-manager relation for Player Demo Club.
        manager_demo_team_a, _ = make_team(
            "Manager Demo A",
            tennis,
            club_id=player_demo_club.id,
            verbose=verbose,
        )
        manager_demo_team_b, _ = make_team(
            "Manager Demo B",
            tennis,
            club_id=player_demo_club.id,
            verbose=verbose,
        )
        jeremi_manager = owners[0][1]
        lrk_manager, _ = make_manager(lrk_manager_acc)
        if not TeamManagerTeam.query.filter_by(team_manager_id=jeremi_manager.id, team_id=manager_demo_team_a.id).first():
            db.session.add(TeamManagerTeam(
                team_manager_id=jeremi_manager.id,
                team_id=manager_demo_team_a.id,
                can_rename=True,
                can_delete=True,
                can_edit_players=True,
                can_edit_managers=True,
                can_manage_match=True,
            ))
        if not TeamManagerTeam.query.filter_by(team_manager_id=lrk_manager.id, team_id=manager_demo_team_b.id).first():
            db.session.add(TeamManagerTeam(
                team_manager_id=lrk_manager.id,
                team_id=manager_demo_team_b.id,
                can_rename=True,
                can_delete=True,
                can_edit_players=True,
                can_edit_managers=True,
                can_manage_match=True,
            ))
        db.session.flush()

        manager_demo_ladder, _ = get_or_create_ladder(
            club_id=player_demo_club.id,
            name="Manager Demo Singles",
            description="Demo ladder where Jeremi and LRK are team managers but not club owners.",
            sport_type_id=tennis.id,
            ladder_rating_function_id=rating_fn_id,
            ruleset_id=tennis_ruleset_id,
        )
        get_or_create_ladder_team(manager_demo_ladder.id, manager_demo_team_a.id, rank=1, rating=1125, matches_played=0)
        get_or_create_ladder_team(manager_demo_ladder.id, manager_demo_team_b.id, rank=2, rating=1105, matches_played=0)
        ensure_player_on_team(fake_player_a, manager_demo_team_a)
        ensure_player_on_team(fake_player_b, manager_demo_team_b)
        ensure_team_players_in_club(manager_demo_team_a, player_demo_club)
        ensure_team_players_in_club(manager_demo_team_b, player_demo_club)

        manager_demo_week_start = demo_week_start + datetime.timedelta(days=14)
        manager_demo_start = datetime.datetime.combine(
            manager_demo_week_start + datetime.timedelta(days=2),
            datetime.time(hour=20, minute=0),
        )
        manager_demo_proposal = find_match_proposal(
            manager_demo_week_start,
            manager_demo_team_a.id,
            manager_demo_team_b.id,
        )
        if manager_demo_proposal is None:
            _make_proposal(
                team1_id=manager_demo_team_a.id,
                team2_id=manager_demo_team_b.id,
                sport_type_id=tennis.id,
                ladder_id=manager_demo_ladder.id,
                proposed_by_user_id=jeremi_acc.id,
                week_start_date=manager_demo_week_start,
                proposed_start_at=manager_demo_start,
                proposed_end_at=manager_demo_start + datetime.timedelta(hours=1),
                location="Manager Demo Court",
            )
            manager_demo_proposal = find_match_proposal(
                manager_demo_week_start,
                manager_demo_team_a.id,
                manager_demo_team_b.id,
            )
        if manager_demo_proposal:
            manager_demo_proposal.proposed_by_user_id = jeremi_acc.id
            manager_demo_proposal.ladder_id = manager_demo_ladder.id
            manager_demo_proposal.sport_type_id = tennis.id
            manager_demo_proposal.proposed_start_at = manager_demo_start
            manager_demo_proposal.proposed_end_at = manager_demo_start + datetime.timedelta(hours=1)
            manager_demo_proposal.location = "Manager Demo Court"
            _make_accepted(manager_demo_proposal, by_user_id=lrk_manager_acc.id)
        lrk_debug_team, _ = make_team(
            "LRK Debug Opponent",
            tennis,
            club_id=player_demo_club.id,
            verbose=verbose,
        )
        jeremi_debug_team, _ = make_team(
            "Jeremi Debug Player",
            tennis,
            club_id=player_demo_club.id,
            verbose=verbose,
        )
        ensure_player_on_team(jeremi_acc, jeremi_debug_team)
        ensure_player_on_team(lrk_acc, lrk_debug_team)
        ensure_team_players_in_club(jeremi_debug_team, player_demo_club)
        ensure_team_players_in_club(lrk_debug_team, player_demo_club)

        lrk_debug_ladder, _ = get_or_create_ladder(
            club_id=player_demo_club.id,
            name="LRK Debug Singles",
            description="Debug ladder for reproducing match proposal flows between Jeremi and LRK.",
            sport_type_id=tennis.id,
            ladder_rating_function_id=rating_fn_id,
            ruleset_id=tennis_ruleset_id,
        )
        get_or_create_ladder_team(lrk_debug_ladder.id, jeremi_debug_team.id, rank=1, rating=1100, matches_played=0)
        get_or_create_ladder_team(lrk_debug_ladder.id, lrk_debug_team.id, rank=2, rating=1100, matches_played=0)

        debug_week_start = demo_week_start
        debug_start = datetime.datetime.combine(
            debug_week_start + datetime.timedelta(days=2),
            datetime.time(hour=19, minute=0),
        )
        debug_end = debug_start + datetime.timedelta(hours=1)
        debug_proposal = _make_proposal(
            team1_id=jeremi_debug_team.id,
            team2_id=lrk_debug_team.id,
            sport_type_id=tennis.id,
            ladder_id=lrk_debug_ladder.id,
            proposed_by_user_id=jeremi_acc.id,
            week_start_date=debug_week_start,
            proposed_start_at=debug_start,
            proposed_end_at=debug_end,
            location="LRK Debug Court",
        )
        if not debug_proposal:
            debug_proposal = find_match_proposal(debug_week_start, jeremi_debug_team.id, lrk_debug_team.id)
        if debug_proposal:
            debug_proposal.proposed_by_user_id = jeremi_acc.id
            debug_proposal.ladder_id = lrk_debug_ladder.id
            debug_proposal.sport_type_id = tennis.id
            debug_proposal.proposed_start_at = debug_start
            debug_proposal.proposed_end_at = debug_end
            debug_proposal.location = "LRK Debug Court"
            _make_pending(debug_proposal)

        # Join requests for demo
        upsert_club_join_request(owners[0][3].id, opponent_acc.id, days_ago=2)

    except Exception as e:
        print(f"{TAG} ERROR seeding player demo data: {e}")
        db.session.rollback()
        raise
    log(f"{TAG} [8/8] Player demo data OK", verbose)

    # ------------------------------------------------------------------
    # Commit
    # ------------------------------------------------------------------
    log(f"{TAG} Committing to database...", verbose)
    try:
        db.session.commit()
    except Exception as e:
        print(f"{TAG} ERROR during commit: {e}")
        db.session.rollback()
        raise

    print(f"{TAG} Seed complete — 7 clubs, 14 ladders, 28 teams, {total_matches} match records")

    # ------------------------------------------------------------------
    # Print account summary
    # ------------------------------------------------------------------
    _print_account_summary(owners, MANAGER_EMAILS, MANAGER_NAMES, all_teams_flat)


def _print_account_summary(owners, manager_emails, manager_names, all_teams_flat):
    """Print a structured summary of all seeded accounts with club/match access."""
    print("\n" + "=" * 72)
    print("  SEEDED ACCOUNTS WITH CLUB / MATCH MANAGEMENT ACCESS")
    print("=" * 72)

    print("\n--- CLUB OWNERS (full club + match management) ---")
    OWNER_DATA_SUMMARY = [
        ("jeremilorek@outlook.com",        "qwertyuiop",   "NetRank Club"),
        ("nina.jacobs@example.com",        "Password123!", "Antwerp Padel House"),
        ("stefan.bauwens@example.com",     "Password123!", "Brussels FC"),
        ("lieselot.vermeersch@example.com","Password123!", "Ghent Volleyball Academy"),
        ("remi.deschamps@example.com",     "Password123!", "Bruges Basketball Club"),
        ("hilde.goossens@example.com",     "Password123!", "Leuven Hockey Union"),
        ("axel.fontaine@example.com",      "Password123!", "Liege Squash Centre"),
    ]
    for email, pwd, club_name in OWNER_DATA_SUMMARY:
        print(f"  email   : {email}")
        print(f"  password: {pwd}")
        print(f"  club    : {club_name}  (owner)")
        print()

    print("--- ADMIN TEST ACCOUNT ---")
    print("  email   : admin@netrank.test")
    print("  password: admin12345")
    print("  role    : administrator")
    print()

    print("--- TEAM MANAGERS (can propose + manage matches for their team) ---")
    for i, (email, (first, last)) in enumerate(zip(manager_emails, manager_names)):
        team = all_teams_flat[i]
        print(f"  {first:<10} {last:<14} | {email:<38} | Password123! | team: {team.name}")

    print("\n--- PLAYER DEMO ---")
    print("  email   : robin.vermeulen@example.com")
    print("  password: Password123!")
    print("  role    : player on 'Player Demo B'")
    print("=" * 72 + "\n")
