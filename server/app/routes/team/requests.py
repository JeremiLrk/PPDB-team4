from flask import Blueprint, request, abort, jsonify

from server.app.models.account import Account
from server.app.decorators import login_required
from server.app.models.player import PlayerTeam, Player
from server.app.models.team import TeamManagerTeam, TeamManager
from server.app.models.team_join_request import TeamJoinRequest
from server.app.routes.team._helpers import (
    get_team_or_404,
    search_accounts,
    ladders_exceeding_max_after_add,
    resolve_target,
    ladders_violating_min_after_remove,
)
from server.app.routes.team._permissions import can_edit_players_or_403, get_permissions, can_edit_managers_or_403
from server.extensions import cache, db

requests_bp = Blueprint("team_requests", __name__)



@requests_bp.route("/<int:team_id>/my-permissions", methods=["GET"])
@login_required
def get_my_permissions(account: Account, team_id: int):
    """GET /api/teams/<team_id>/my-permissions — returns current user's permissions for the team."""
    team = get_team_or_404(team_id)
    permissions = get_permissions(account.resolved_role, team)
    return jsonify({
        "teamId":      team_id,
        "permissions": permissions,
    }), 200


@requests_bp.route("/<int:team_id>/players", methods=["GET"])
@cache.memoize(timeout=300)
def get_team_players(team_id: int):
    """GET /api/teams/<team_id>/players — list of team players."""

    # Call to check if this team exists
    team = get_team_or_404(team_id)

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


@requests_bp.route("/<int:team_id>/members", methods=["GET"])
def get_team_members(team_id: int):
    """GET /api/teams/<team_id>/members — public list of team members (name only, no personal info)."""
    get_team_or_404(team_id)

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


@requests_bp.route("/<int:team_id>/players/search", methods=["GET"])
@login_required
@cache.memoize(timeout=90)
def search_accounts_not_in_team(account: Account, team_id: int):
    """GET /api/teams/<team_id>/players/search?q=<string>."""
    team = get_team_or_404(team_id)

    can_edit_players_or_403(account.resolved_role, team)

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

    matches = search_accounts(q, exclude_ids)
    return jsonify({
        "teamId": team_id,
        "q": q,
        "results": [a.to_dict() for a in matches]
    }), 200


@requests_bp.route("/<int:team_id>/managers/search", methods=["GET"])
@login_required
@cache.memoize(timeout=90)
def search_accounts_not_manager_of_team(account: Account, team_id: int):
    """GET /api/teams/<team_id>/managers/search?q=<string>.

    Returns a list of accounts that are NOT yet managers of this team.
    Only available to those with the can_edit_managers permission for this team.
    """
    team = get_team_or_404(team_id)

    can_edit_managers_or_403(account.resolved_role, team)

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

    matches = search_accounts(q, exclude_ids)
    return jsonify({
        "teamId":  team_id,
        "q":       q,
        "results": [a.to_dict() for a in matches],
    }), 200


@requests_bp.route("/<int:team_id>/managers", methods=["GET"])
@cache.memoize(timeout=300)
def get_team_managers(team_id: int):
    """GET /api/teams/<team_id>/managers — a list of team managers with their rights."""
    team = get_team_or_404(team_id)

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


@requests_bp.route("/<int:team_id>/players/check-max-exceeded", methods=["POST"])
@login_required
def check_player_add_exceeds_ladder_max(account: Account, team_id: int):
    """POST /api/teams/<team_id>/players/check-max-exceeded

    Returns 409 with the names of every ladder where adding one more player
    would exceed the sport type's maximum_number_of_players_per_team.
    Returns 200 when no constraint would be violated.
    """
    team = get_team_or_404(team_id)

    can_edit_players_or_403(account.resolved_role, team)

    violating = ladders_exceeding_max_after_add(team_id)
    if violating:
        return jsonify({
            "message": "Adding a player would exceed the maximum roster size for one or more ladders.",
            "ladders": [l.name for l in violating]
        }), 409

    return jsonify({"message": "Adding a player will not violate any ladder roster maximum."}), 200


@requests_bp.route("/<int:team_id>/players/<int:account_id>/check-min-violated", methods=["DELETE"])
@login_required
def check_player_remove_violates_ladder_min(account: Account, team_id: int, account_id: int):
    """DELETE /api/teams/<team_id>/players/<account_id>/check-min-violated

    Returns 409 with the names of every ladder where removing this player
    would drop the team below the sport type's minimum_number_of_players_on_a_team.
    Returns 200 when no constraint would be violated.

    Uses DELETE so that the client can use the same account_id segment
    as the force-remove sibling route.
    """
    team = get_team_or_404(team_id)

    can_edit_players_or_403(account.resolved_role, team)

    # Verify the player is actually in this team before checking constraints.
    target = resolve_target(account_id)
    assoc = next(
        (a for a in (target.player.playerteam_associations if target.player else [])
         if a.team_id == team.id),
        None
    )
    if not assoc:
        abort(404, description="This account is not a player in this team.")

    violating = ladders_violating_min_after_remove(team_id)
    if violating:
        return jsonify({
            "message": "Removing this player would drop the team below the minimum roster size for one or more ladders.",
            "ladders": [l.name for l in violating]
        }), 409

    return jsonify({"message": "Removing this player will not violate any ladder roster minimum."}), 200
