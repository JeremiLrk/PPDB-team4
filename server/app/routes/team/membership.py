from flask import Blueprint, request, jsonify, Response, abort

from server.extensions import db
from server.app.decorators import login_required
from server.app.models.account import Account
from server.app.models.player import Player, PlayerTeam
from server.app.models.team import TeamManagerTeam, TeamManager

from server.app.utils.promote import promote_to_team_manager, promote_to_player
from ._helpers import (
    _get_team_or_404,
    _resolve_target,
    _search_accounts,
    _handle_team_after_last_manager_removed
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
    team = _get_team_or_404(team_id)

    _can_edit_managers_or_403(account.resolved_role, team)

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


@membership_bp.route("/<int:team_id>/players", methods=["POST"])
@login_required
def add_player_to_team(account: Account, team_id: int):
    """POST /api/teams/<team_id>/players — add player."""
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

    promote_to_player(target)

    assoc = PlayerTeam(player_id=target.player.id, team_id=team.id)
    db.session.add(assoc)
    db.session.commit()

    return jsonify({
        "message": "Player added successfully.",
        "player": target.to_dict(include = ["player"])
    }), 200


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

    db.session.delete(assoc)
    db.session.commit()
    return jsonify({
        "message": "Player removed successfully."
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