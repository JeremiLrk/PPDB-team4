"""
Shared helper logic for team routes.

These helpers keep the team endpoints small by handling common lookups,
pagination, roster counting, and ladder-size checks in one place.
"""

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


def get_team_or_404(team_id: int) -> Team:
    """Load a team or abort with 404 if it does not exist."""
    team = Team.query.get(team_id)
    if not team:
        abort(404, description="Team not found.")
    return team


def resolve_target(account_id: int) -> Account:
    """Load an account or abort with a validation or 404 error."""
    if not account_id:
        abort(422, description="Field 'accountId' is required.")
    target = Account.query.get(account_id)
    if not target:
        abort(404, description="Account not found.")
    return target


def parse_pagination(args) -> tuple[int, int, Any]:
    """Parse the common from/to/sort pagination arguments."""
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


def handle_team_after_last_manager_removed(team: Team) -> None:
    """Promote a player or delete the team when the last manager is removed."""
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
        # Reuse the first available player so the team does not become unmanaged.
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


def search_accounts(q: str, exclude_player_ids: set[int]) -> list[Account]:
    """Search for accounts while excluding ids already attached to the team."""

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
            # Exact id matches are the strongest signal, so return immediately.
            return [account]
    except ValueError:
        pass

    account = (
        db.session.query(Account)
        .filter(not_excluded, func.lower(Account.email) == q.lower())
        .first()
    )
    if account:
        # Exact email matches are the next best lookup after ids.
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
        # If trigram matching is unavailable, fall back to simple pattern search.
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

def count_confirmed_players(team_id: int) -> int:
    """Count players who are already confirmed members of the team."""
    return (
        db.session.query(func.count())
        .select_from(PlayerTeam)
        .filter(PlayerTeam.team_id == team_id)
        .scalar()
    )


# ---------------------------------------------------------------------------
# count effective players (confirmed + pending join requests)
# ---------------------------------------------------------------------------

def count_effective_players(team_id: int) -> int:
    """Count confirmed players plus pending join requests for roster checks."""
    confirmed = count_confirmed_players(team_id)

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

def ladders_exceeding_max_after_add(team_id: int) -> list[Ladder]:
    """Return ladders that would exceed roster maximum after one more player."""
    projected = count_effective_players(team_id) + 1

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

def ladders_violating_min_after_remove(team_id: int) -> list[Ladder]:
    """Return ladders that would violate roster minimum after one player leaves."""
    projected = count_effective_players(team_id) - 1

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


# Compatibility aliases for older imports and tests.
_get_team_or_404 = get_team_or_404
_resolve_target = resolve_target
_parse_pagination = parse_pagination
_handle_team_after_last_manager_removed = handle_team_after_last_manager_removed
_search_accounts = search_accounts
_count_confirmed_players = count_confirmed_players
_count_effective_players = count_effective_players
_ladders_exceeding_max_after_add = ladders_exceeding_max_after_add
_ladders_violating_min_after_remove = ladders_violating_min_after_remove
