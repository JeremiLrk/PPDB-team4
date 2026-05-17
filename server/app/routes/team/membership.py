from flask import Blueprint, request, jsonify, Response, abort
from datetime import datetime, timezone

from server.extensions import cache, db
from server.app.decorators import login_required
from server.app.models.account import Account
from server.app.models.player import Player, PlayerTeam
from server.app.models.team import TeamManagerTeam, TeamManager
from server.app.models.team_join_request import TeamJoinRequest

from server.app.utils.promote import promote_to_team_manager, promote_to_player
from server.app.models.match import MatchProposal, MatchStatus
from server.app.models.ladder_team import LadderTeam
from ._helpers import (
    _get_team_or_404,
    _resolve_target,
    _search_accounts,
    _handle_team_after_last_manager_removed,
    _ladders_exceeding_max_after_add,
    _ladders_violating_min_after_remove,
)
from ._permissions import (
    _can_edit_players_or_403,
    _can_edit_managers_or_403, _get_permissions
)

membership_bp = Blueprint("team_membership", __name__)


@membership_bp.route("/<int:team_id>/managers", methods=["POST"])
@login_required
def add_manager_to_team(account: Account, team_id: int) -> tuple[Response, int]:
    """POST /api/teams/<team_id>/managers — Add a manager."""
    team = _get_team_or_404(team_id)

    _can_edit_managers_or_403(account.resolved_role, team)

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    target= _resolve_target(data.get("accountId"))

    if target.team_manager:
        already = any(a.team_id == team.id for a in target.team_manager.team_associations)
        if already:
            abort(409, description="This account is already a manager of this team.")

    promote_to_team_manager(target)

    # Default permissions for a new manager
    can_rename         = data.get("canRename", True)
    can_delete         = data.get("canDelete", True)
    can_edit_players   = data.get("canEditPlayers", True)
    can_edit_managers  = data.get("canEditManagers", True)
    assoc = TeamManagerTeam(
        team_manager_id=target.team_manager.id,
        team_id=team.id,
        can_rename=can_rename,
        can_delete=can_delete,
        can_edit_players=can_edit_players,
        can_edit_managers=can_edit_managers,
    )
    db.session.add(assoc)
    db.session.commit()

    return jsonify({
        "message": "Manager added successfully.",
        "manager": target.team_manager.to_dict()
    }), 201


@membership_bp.route("/<int:team_id>/managers/<int:account_id>", methods=["DELETE"])
@login_required
def remove_manager_from_team(account: Account, team_id: int, account_id: int):
    """DELETE /api/teams/<team_id>/managers/<account_id>."""

    resolved = account.resolved_role

    team = _get_team_or_404(team_id)

    _can_edit_managers_or_403(resolved, team)

    target = _resolve_target(account_id)

    assoc = next(
        (a for a in (target.team_manager.team_associations if target.team_manager else [])
         if a.team_id == team.id),
        None
    )
    if not assoc:
        abort(404, description="This account is not a manager of this team.")

    db.session.delete(assoc)
    db.session.flush()

    _handle_team_after_last_manager_removed(team)
    db.session.commit()

    return jsonify({
        "message": "Manager removed successfully."
    }), 200


@membership_bp.route("/<int:team_id>/players", methods=["GET"])
def get_team_players(team_id: int):
    """GET /api/teams/<team_id>/players — list of team players."""

    # Call to check if this team exists
    team = _get_team_or_404(team_id)

    players = (
        db.session.query(Account)
        .join(Player, Player.id == Account.id)
        .join(PlayerTeam, PlayerTeam.player_id == Player.id)
        .filter(PlayerTeam.team_id == team_id)
        .order_by(Account.last_name.asc(), Account.first_name.asc(), Account.id.asc())
        .all()
    )
    total = len(players)

    return jsonify({
        "teamId": team_id,
        "total": total,
        "players": [a.to_dict(include = ["player"]) for a in players]
    }), 200


@membership_bp.route("/<int:team_id>/members", methods=["GET"])
def get_team_members(team_id: int):
    """GET /api/teams/<team_id>/members — public list of team members (name only, no personal info)."""
    _get_team_or_404(team_id)

    players = (
        db.session.query(Account)
        .join(Player, Player.id == Account.id)
        .join(PlayerTeam, PlayerTeam.player_id == Player.id)
        .filter(PlayerTeam.team_id == team_id)
        .order_by(Account.last_name.asc(), Account.first_name.asc(), Account.id.asc())
        .all()
    )

    return jsonify({
        "teamId": team_id,
        "total": len(players),
        "members": [
            {"firstName": a.first_name, "lastName": a.last_name}
            for a in players
        ],
    }), 200


@membership_bp.route("/<int:team_id>/players", methods=["POST"])
@login_required
def add_player_to_team(account: Account, team_id: int):
    """POST /api/teams/<team_id>/players — send player join request."""
    team = _get_team_or_404(team_id)
    resolved = account.resolved_role

    _can_edit_players_or_403(resolved, team)

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    target = _resolve_target(data.get("accountId"))

    if target.player:
        already = any(a.team_id == team.id for a in target.player.playerteam_associations)
        if already:
            abort(409, description="This account is already a player in this team.")

    # Check for an existing PENDING request — a new row can always be inserted
    # because the PK is now `id`; uniqueness of pending requests is enforced by
    # the partial unique index uq_team_join_request_pending (team_id, user_id)
    # WHERE status = 'pending'.
    active_request = db.session.query(TeamJoinRequest).filter(
        TeamJoinRequest.team_id == team.id,
        TeamJoinRequest.user_id == target.id,
        TeamJoinRequest.status == "pending",
        ).first()

    if active_request:
        abort(409, description="Join request for this player to this team already exists.")

    # Check if adding player would exceed ladder size limits
    exceeding_ladders = _ladders_exceeding_max_after_add(team_id)

    confirm_exceed = request.args.get("confirmExceed", "").lower() == "true"

    if exceeding_ladders and not confirm_exceed:
        # Return warning instead of error
        return jsonify({
            "message": "Adding this player would exceed team size limits in active ladders.",
            "warning": "exceeds_max_players",
            "ladders": [{"id": l.id, "name": l.name} for l in exceeding_ladders],
            "requireConfirm": True
        }), 202

    promote_to_player(target)

    join_request = TeamJoinRequest(
        team_id=team.id,
        user_id=target.id,
        date=datetime.now(timezone.utc),
        status="pending",
    )
    db.session.add(join_request)
    db.session.commit()

    return jsonify({
        "message": "Player join request created successfully.",
        "request": join_request.serialize()
    }), 201


@membership_bp.route("/<int:team_id>/players/<int:account_id>", methods=["DELETE"])
@login_required
def remove_player_from_team(account: Account, team_id: int, account_id: int):
    """DELETE /api/teams/<team_id>/players/<account_id>."""
    team = _get_team_or_404(team_id)
    resolved = account.resolved_role

    _can_edit_players_or_403(resolved, team)

    target = _resolve_target(account_id)

    assoc = next(
        (a for a in (target.player.playerteam_associations if target.player else [])
         if a.team_id == team.id),
        None
    )
    if not assoc:
        abort(404, description="This account is not a player in this team.")

    # Check if removing player would violate minimum roster size in active ladders
    violating_ladders = _ladders_violating_min_after_remove(team_id)

    # Get confirmation flag from query parameters
    confirm_remove = request.args.get("confirmViolate", "").lower() == "true"

    if violating_ladders and not confirm_remove:
        # Return warning instead of error
        return jsonify({
            "message": "Removing this player would drop below minimum team size in active ladders.",
            "warning": "violates_min_players",
            "ladders": [{"id": l.id, "name": l.name} for l in violating_ladders],
            "requireConfirm": True
        }), 202

    db.session.delete(assoc)
    db.session.commit()

    return jsonify({
        "message": "Player removed successfully."
    }), 200


@membership_bp.route("/<int:team_id>/players/check-max-exceeded", methods=["POST"])
@login_required
def check_player_add_exceeds_ladder_max(account: Account, team_id: int):
    """POST /api/teams/<team_id>/players/check-max-exceeded

    Returns 409 with the names of every ladder where adding one more player
    would exceed the sport type's maximum_number_of_players_per_team.
    Returns 200 when no constraint would be violated.
    """
    team = _get_team_or_404(team_id)

    _can_edit_players_or_403(account.resolved_role, team)

    violating = _ladders_exceeding_max_after_add(team_id)
    if violating:
        return jsonify({
            "message": "Adding a player would exceed the maximum roster size for one or more ladders.",
            "ladders": [l.name for l in violating]
        }), 409

    return jsonify({"message": "Adding a player will not violate any ladder roster maximum."}), 200


@membership_bp.route("/<int:team_id>/players/add-drop-exceeding-ladders", methods=["POST"])
@login_required
def add_player_dropping_exceeding_ladders(account: Account, team_id: int):
    """POST /api/teams/<team_id>/players/add-drop-exceeding-ladders

    Adds a player (via join request) and, for every ladder where the new roster
    size would exceed the sport type's maximum_number_of_players_per_team,
    removes the team from that ladder and deletes all its pending or accepted
    match proposals in that ladder.
    """
    team = _get_team_or_404(team_id)
    resolved = account.resolved_role

    _can_edit_players_or_403(resolved, team)

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    target = _resolve_target(data.get("accountId"))

    if target.player:
        already = any(a.team_id == team.id for a in target.player.playerteam_associations)
        if already:
            abort(409, description="This account is already a player in this team.")

    # Check for an existing PENDING request using the same active-request logic
    # used in add_player_to_team — PK is now `id`, partial unique index enforces
    # that only one pending row per (team_id, user_id) exists at a time.
    active_request = db.session.query(TeamJoinRequest).filter(
        TeamJoinRequest.team_id == team.id,
        TeamJoinRequest.user_id == target.id,
        TeamJoinRequest.status == "pending",
        ).first()

    if active_request:
        abort(409, description="Join request for this player to this team already exists.")

    # Determine violating ladders BEFORE the join request is created so that
    # _count_effective_players still reflects the current state.
    violating_ladders = _ladders_exceeding_max_after_add(team_id)

    active_statuses = [MatchStatus.PENDING, MatchStatus.ACCEPTED]
    for ladder in violating_ladders:
        # Delete all pending/accepted matches for this team in this ladder.
        active_matches = (
            db.session.query(MatchProposal)
            .filter(
                MatchProposal.ladder_id == ladder.id,
                MatchProposal.status_id.in_(active_statuses),
                db.or_(
                    MatchProposal.team1_id == team_id,
                    MatchProposal.team2_id == team_id,
                    )
            )
            .all()
        )
        for match in active_matches:
            db.session.delete(match)

        # Remove the team from this ladder.
        ladder_team = (
            db.session.query(LadderTeam)
            .filter(LadderTeam.ladder_id == ladder.id, LadderTeam.team_id == team_id)
            .first()
        )
        if ladder_team:
            db.session.delete(ladder_team)

    promote_to_player(target)

    join_request = TeamJoinRequest(
        team_id=team.id,
        user_id=target.id,
        date=datetime.now(timezone.utc),
        status="pending"
    )
    db.session.add(join_request)
    db.session.commit()

    dropped_names = [l.name for l in violating_ladders]
    return jsonify({
        "message": "Player join request created successfully.",
        "request": join_request.serialize(),
        "droppedFromLadders": dropped_names
    }), 201


@membership_bp.route("/<int:team_id>/players/<int:account_id>/check-min-violated", methods=["DELETE"])
@login_required
def check_player_remove_violates_ladder_min(account: Account, team_id: int, account_id: int):
    """DELETE /api/teams/<team_id>/players/<account_id>/check-min-violated

    Returns 409 with the names of every ladder where removing this player
    would drop the team below the sport type's minimum_number_of_players_on_a_team.
    Returns 200 when no constraint would be violated.

    Uses DELETE so that the client can use the same account_id segment
    as the force-remove sibling route.
    """
    team = _get_team_or_404(team_id)

    _can_edit_players_or_403(account.resolved_role, team)

    # Verify the player is actually in this team before checking constraints.
    target = _resolve_target(account_id)
    assoc = next(
        (a for a in (target.player.playerteam_associations if target.player else [])
         if a.team_id == team.id),
        None
    )
    if not assoc:
        abort(404, description="This account is not a player in this team.")

    violating = _ladders_violating_min_after_remove(team_id)
    if violating:
        return jsonify({
            "message": "Removing this player would drop the team below the minimum roster size for one or more ladders.",
            "ladders": [l.name for l in violating]
        }), 409

    return jsonify({"message": "Removing this player will not violate any ladder roster minimum."}), 200


@membership_bp.route("/<int:team_id>/players/<int:account_id>/remove-drop-violated-ladders", methods=["DELETE"])
@login_required
def remove_player_dropping_violated_ladders(account: Account, team_id: int, account_id: int):
    """DELETE /api/teams/<team_id>/players/<account_id>/remove-drop-violated-ladders

    Removes the player from the team and, for every ladder where the removal
    would drop the team below the minimum roster size, also removes the team
    from that ladder and deletes all its pending or accepted match proposals
    in that ladder.
    """
    team = _get_team_or_404(team_id)

    _can_edit_players_or_403(account.resolved_role, team)

    target = _resolve_target(account_id)

    assoc = next(
        (a for a in (target.player.playerteam_associations if target.player else [])
         if a.team_id == team.id),
        None
    )
    if not assoc:
        abort(404, description="This account is not a player in this team.")

    # Determine which ladders will violate the minimum BEFORE deleting.
    violating_ladders = _ladders_violating_min_after_remove(team_id)

    active_statuses = [MatchStatus.PENDING, MatchStatus.ACCEPTED]
    for ladder in violating_ladders:
        # Delete all pending/accepted matches for this team in this ladder.
        active_matches = (
            db.session.query(MatchProposal)
            .filter(
                MatchProposal.ladder_id == ladder.id,
                MatchProposal.status_id.in_(active_statuses),
                db.or_(
                    MatchProposal.team1_id == team_id,
                    MatchProposal.team2_id == team_id,
                    )
            )
            .all()
        )
        for match in active_matches:
            db.session.delete(match)

        # Remove the team from this ladder.
        ladder_team = (
            db.session.query(LadderTeam)
            .filter(LadderTeam.ladder_id == ladder.id, LadderTeam.team_id == team_id)
            .first()
        )
        if ladder_team:
            db.session.delete(ladder_team)

    db.session.delete(assoc)
    db.session.commit()

    dropped_names = [l.name for l in violating_ladders]
    return jsonify({
        "message": "Player removed successfully.",
        "droppedFromLadders": dropped_names
    }), 200




@membership_bp.route("/<int:team_id>/players/search", methods=["GET"])
@login_required
def search_accounts_not_in_team(account: Account, team_id: int):
    """GET /api/teams/<team_id>/players/search?q=<string>."""
    team = _get_team_or_404(team_id)

    _can_edit_players_or_403(account.resolved_role, team)

    q = request.args.get("q", "").strip()
    if not q:
        abort(400, description="Query parameter 'q' is required.")

    existing = db.session.execute(
        db.select(PlayerTeam.player_id).where(PlayerTeam.team_id == team_id)
    ).fetchall()
    exclude_ids = {row.player_id for row in existing}

    pending_requests = db.session.execute(
        db.select(TeamJoinRequest.user_id).where(
            TeamJoinRequest.team_id == team_id,
            TeamJoinRequest.status == "pending"
        )
    ).fetchall()
    pending_ids = {row.user_id for row in pending_requests}

    exclude_ids = exclude_ids.union(pending_ids)

    matches = _search_accounts(q, exclude_ids)
    return jsonify({
        "teamId": team_id,
        "q": q,
        "results": [a.to_dict() for a in matches]
    }), 200


@membership_bp.route("/<int:team_id>/my-permissions", methods=["GET"])
@login_required
def get_my_permissions(account: Account, team_id: int):
    """GET /api/teams/<team_id>/my-permissions — returns current user's permissions for the team."""
    team = _get_team_or_404(team_id)
    permissions = _get_permissions(account.resolved_role, team)
    return jsonify({
        "teamId":      team_id,
        "permissions": permissions,
    }), 200


@membership_bp.route("/<int:team_id>/managers/search", methods=["GET"])
@login_required
def search_accounts_not_manager_of_team(account: Account, team_id: int):
    """GET /api/teams/<team_id>/managers/search?q=<string>.

    Returns a list of accounts that are NOT yet managers of this team.
    Only available to those with the can_edit_managers permission for this team.
    """
    team = _get_team_or_404(team_id)

    _can_edit_managers_or_403(account.resolved_role, team)

    q = request.args.get("q", "").strip()
    if not q:
        abort(400, description="Query parameter 'q' is required.")

    # IDs of accounts that are already managers of this team.
    # team_manager.id == account.id (PK — shared with account)
    existing = db.session.execute(
        db.select(TeamManagerTeam.team_manager_id)
        .where(TeamManagerTeam.team_id == team_id)
    ).fetchall()
    exclude_ids = {row.team_manager_id for row in existing}

    matches = _search_accounts(q, exclude_ids)
    return jsonify({
        "teamId":  team_id,
        "q":       q,
        "results": [a.to_dict() for a in matches],
    }), 200

@membership_bp.route("/<int:team_id>/managers", methods=["GET"])
def get_team_managers(team_id: int):
    """GET /api/teams/<team_id>/managers — a list of team managers with their rights."""
    team = _get_team_or_404(team_id)

    # Load manager accounts along with their association (rights)
    rows = (
        db.session.query(Account, TeamManagerTeam)
        .join(TeamManager, TeamManager.id == Account.id)
        .join(TeamManagerTeam, TeamManagerTeam.team_manager_id == TeamManager.id)
        .filter(TeamManagerTeam.team_id == team_id)
        .order_by(Account.last_name.asc(), Account.first_name.asc(), Account.id.asc())
        .all()
    )

    managers = []
    for account, assoc in rows:
        d = account.to_dict()
        # Add this manager's rights to the team
        d["permissions"] = {
            "canRename":       assoc.can_rename,
            "canDelete":       assoc.can_delete,
            "canEditPlayers":  assoc.can_edit_players,
            "canEditManagers": assoc.can_edit_managers,
        }
        managers.append(d)

    return jsonify({
        "teamId":   team_id,
        "total":    len(managers),
        "managers": managers,
    }), 200

