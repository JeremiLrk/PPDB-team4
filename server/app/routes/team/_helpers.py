from typing import Any

from flask import abort
from sqlalchemy import func
from server.extensions import db
from server.app.models.account import Account, AccountRole
from server.app.models.team import Team, TeamManagerTeam, TeamManager
from server.app.models.player import PlayerTeam
from server.app.models.team_join_request import TeamJoinRequest
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam


def _get_team_or_404(team_id: int) -> Team:
    team = Team.query.get(team_id)
    if not team:
        abort(404, description="Team not found.")
    return team


def _resolve_target(account_id: int) -> Account:
    """Finds an account by ID or returns an error."""
    if not account_id:
        abort(422, description="Field 'accountId' is required.")
    target = Account.query.get(account_id)
    if not target:
        abort(404, description="Account not found.")
    return target


def _parse_pagination(args) -> tuple[int, int, Any]:
    """
    Retrieves pagination parameters from the query string.
    ?from=0&to=20&sort=name|id
    Returns (offset, limit, sort_col, error).
    """
    try:
        offset = int(args.get("from", 0))
        to     = int(args.get("to",   20))
    except ValueError:
        abort(422, description="'from' and 'to' must be integers.")

    if offset < 0 or to < offset:
        abort(422, description="'from' must be >= 0 and 'to' must be >= 'from'.")

    limit = to - offset

    sort = args.get("sort", "id")
    if sort == "name":
        sort_col = Team.name.asc()
    elif sort == "id":
        sort_col = Team.id.asc()
    else:
        abort(422, description="'sort' must be 'id' or 'name'.")

    return offset, limit, sort_col


def _handle_team_after_last_manager_removed(team: Team) -> None:
    """
    Called after the last manager is removed from a team WITHOUT a club.
    Promotes a random player to manager, or removes the team.
    """
    if team.club_id is not None:
        return

    remaining_count = db.session.execute(
        db.select(db.func.count())
        .select_from(TeamManagerTeam)
        .where(TeamManagerTeam.team_id == team.id)
    ).scalar()

    if remaining_count > 0:
        return

    if team.players:
        random_player = team.players[0]
        account = random_player.account

        tm_role = AccountRole.query.filter_by(name="team_manager").first()
        new_tm  = TeamManager(id=account.id)
        db.session.add(new_tm)
        account.account_role_id = tm_role.id
        db.session.flush()

        assoc = TeamManagerTeam(
            team_manager_id=new_tm.id,
            team_id=team.id,
            can_rename=True,
            can_delete=True,
            can_edit_players=True,
            can_edit_managers=True,
        )
        db.session.add(assoc)
    else:
        db.session.delete(team)


def _search_accounts(q: str, exclude_player_ids: set[int]) -> list[Account]:
    """
    Search for accounts containing the string “q”, excluding players who have already been added.

    Match priority:
      1. Exact match by id       (q — integer)
      2. Exact match by email    (case-insensitive)
      3. Trigram similarity >= 0.3 by first_name or last_name
         (requires pg_trgm; fallback — ILIKE)
    """

    q = q.strip()
    if not q:
        return []

    not_excluded = ~Account.id.in_(exclude_player_ids)

    try:
        target_id = int(q)
        account = (
            db.session.query(Account)
            .filter(not_excluded, Account.id == target_id)
            .first()
        )
        if account:
            return [account]
    except ValueError:
        pass

    account = (
        db.session.query(Account)
        .filter(not_excluded, func.lower(Account.email) == q.lower())
        .first()
    )
    if account:
        return [account]

    SIMILARITY_THRESHOLD = 0.3
    try:
        sim_first = func.similarity(Account.first_name, q)
        sim_last  = func.similarity(Account.last_name,  q)
        best_sim  = func.greatest(sim_first, sim_last)

        return (
            db.session.query(Account)
            .filter(not_excluded, best_sim >= SIMILARITY_THRESHOLD)
            .order_by(best_sim.desc(), Account.id.asc())
            .limit(50)
            .all()
        )
    except Exception:
        db.session.rollback()
        pattern = f"%{q}%"
        return (
            db.session.query(Account)
            .filter(
                not_excluded,
                db.or_(
                    Account.first_name.ilike(pattern),
                    Account.last_name.ilike(pattern),
                    Account.email.ilike(pattern),
                )
            )
            .order_by(Account.last_name.asc(), Account.first_name.asc())
            .limit(50)
            .all()
        )

# ---------------------------------------------------------------------------
# count confirmed (accepted) players in a team
# ---------------------------------------------------------------------------

def _count_confirmed_players(team_id: int) -> int:
    """Returns the number of players who are already members of the team."""
    return (
        db.session.query(func.count())
        .select_from(PlayerTeam)
        .filter(PlayerTeam.team_id == team_id)
        .scalar()
    )


# ---------------------------------------------------------------------------
# count effective players (confirmed + pending join requests)
# ---------------------------------------------------------------------------

def _count_effective_players(team_id: int) -> int:
    """Returns confirmed players + players with a pending join request.

    This reflects the realistic future roster size once all pending
    requests are accepted.
    """
    confirmed = _count_confirmed_players(team_id)

    pending = (
        db.session.query(func.count())
        .select_from(TeamJoinRequest)
        .filter(
            TeamJoinRequest.team_id == team_id,
            TeamJoinRequest.status == "pending",
            )
        .scalar()
    )

    return confirmed + pending


# ---------------------------------------------------------------------------
# ladders that would exceed max players after adding one more
# ---------------------------------------------------------------------------

def _ladders_exceeding_max_after_add(team_id: int) -> list[Ladder]:
    """Returns every Ladder the team participates in where adding one more
    player would exceed the sport type's maximum_number_of_players_per_team.

    Uses _count_effective_players(team_id) + 1 as the projected roster size,
    so pending join requests are already accounted for.
    """
    projected = _count_effective_players(team_id) + 1

    team = db.session.get(Team, team_id)
    if team is None or team.sport_type is None:
        return []

    max_players = team.sport_type.maximum_number_of_players_per_team
    if max_players is None:
        # No cap defined for this sport — nothing can be exceeded.
        return []

    if projected <= max_players:
        return []

    # Fetch every ladder this team is enrolled in.
    ladders = (
        db.session.query(Ladder)
        .join(LadderTeam, LadderTeam.ladder_id == Ladder.id)
        .filter(LadderTeam.team_id == team_id)
        .all()
    )

    return ladders

# ---------------------------------------------------------------------------
# Helper : ladders that would violate min players after removing one
# ---------------------------------------------------------------------------

def _ladders_violating_min_after_remove(team_id: int) -> list[Ladder]:
    """Returns every Ladder the team participates in where removing one player
    would drop below the sport type's minimum_number_of_players_on_a_team.

    Uses _count_effective_players(team_id) - 1 as the projected roster size,
    so pending join requests are already accounted for.
    """
    projected = _count_effective_players(team_id) - 1

    team = db.session.get(Team, team_id)
    if team is None or team.sport_type is None:
        return []

    min_players = team.sport_type.minimum_number_of_players_on_a_team
    if min_players is None:
        # No minimum defined for this sport — nothing can be violated.
        return []

    if projected >= min_players:
        return []

    # Fetch every ladder this team is enrolled in.
    ladders = (
        db.session.query(Ladder)
        .join(LadderTeam, LadderTeam.ladder_id == Ladder.id)
        .filter(LadderTeam.team_id == team_id)
        .all()
    )

    return ladders