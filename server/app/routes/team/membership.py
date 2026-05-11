from flask import Blueprint, request, jsonify, Response, abort
from datetime import datetime, timezone

from server.extensions import cache, db
from server.app.decorators import login_required
from server.app.models.account import Account
from server.app.models.player import Player, PlayerTeam
from server.app.models.team import TeamManagerTeam, TeamManager
from server.app.models.team_join_request import TeamJoinRequest

from server.app.utils.promote import promote_to_team_manager, promote_to_player
from server.app.models.match import MatchProposal, MatchStatus, cancel_unplayed_matches_for_team
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
from .requests import get_team_players, get_team_managers

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

    cache.delete_memoized(get_team_managers, team_id)

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

    cache.delete_memoized(get_team_managers, team_id)

    return jsonify({
        "message": "Manager removed successfully."
    }), 200


@membership_bp.route("/<int:team_id>/players", methods=["POST"])
@login_required
def add_player_to_team(account: Account, team_id: int):
    """POST /api/teams/<team_id>/players — send player join request.

    If adding the player would exceed the maximum roster size in one or more
    ladders the team is enrolled in, the response is HTTP 202 with a warning
    listing the affected ladders.  The client must re-send the request with
    the query parameter confirmDropLadders=true to proceed; doing so removes
    the team from every affected ladder and cancels all of its unplayed
    matches there before creating the join request.
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

    # Determine which ladders would exceed max roster size after the addition.
    exceeding_ladders = _ladders_exceeding_max_after_add(team_id)

    if exceeding_ladders:
        confirm = data.get("confirmDropLadders", False) == True
        if not confirm:
            # Warn the client; no DB changes made yet.
            return jsonify({
                "message": "Adding this player would exceed the maximum roster size in one or more ladders.",
                "warning": "exceeds_max_players",
                "ladders": [{"id": l.id, "name": l.name} for l in exceeding_ladders],
                "requireConfirm": True,
            }), 202

        # Client confirmed: leave the affected ladders and cancel unplayed matches.
        exceeding_ladder_ids = [l.id for l in exceeding_ladders]

        cancel_unplayed_matches_for_team(
            team_id=team_id,
            ladder_ids=exceeding_ladder_ids,
            reason="Team exceeded maximum roster size and was removed from ladder.",
        )

        db.session.query(LadderTeam).filter(
            LadderTeam.team_id == team_id,
            LadderTeam.ladder_id.in_(exceeding_ladder_ids),
            ).delete(synchronize_session="fetch")

    promote_to_player(target)

    join_request = TeamJoinRequest(
        team_id=team.id,
        user_id=target.id,
        date=datetime.now(timezone.utc),
        status="pending",
    )
    db.session.add(join_request)
    db.session.commit()

    cache.delete_memoized(get_team_players, team_id)

    response_body = {
        "message": "Player join request created successfully.",
        "request": join_request.serialize(),
    }
    if exceeding_ladders:
        response_body["droppedFromLadders"] = [
            {"id": l.id, "name": l.name} for l in exceeding_ladders
        ]

    return jsonify(response_body), 201


@membership_bp.route("/<int:team_id>/players/<int:account_id>", methods=["DELETE"])
@login_required
def remove_player_from_team(account: Account, team_id: int, account_id: int):
    """DELETE /api/teams/<team_id>/players/<account_id>.

    If removing the player would drop the team below the minimum roster size
    in one or more ladders the team is enrolled in, the response is HTTP 202
    with a warning listing the affected ladders.  The client must re-send the
    request with the query parameter confirmDropLadders=true to proceed; doing
    so removes the team from every affected ladder and cancels all of its
    unplayed matches there before removing the player.
    """
    team = _get_team_or_404(team_id)
    resolved = account.resolved_role

    _can_edit_players_or_403(resolved, team)

    target = _resolve_target(account_id)

    assoc = next(
        (a for a in (target.player.playerteam_associations if target.player else [])
         if a.team_id == team.id),
        None,
    )
    if not assoc:
        abort(404, description="This account is not a player in this team.")

    # Determine which ladders would violate minimum roster size after the removal.
    violating_ladders = _ladders_violating_min_after_remove(team_id)

    if violating_ladders:
        confirm = request.args.get("confirmDropLadders", False) == True
        if not confirm:
            # Warn the client; no DB changes made yet.
            return jsonify({
                "message": "Removing this player would drop the team below the minimum roster size in one or more ladders.",
                "warning": "violates_min_players",
                "ladders": [{"id": l.id, "name": l.name} for l in violating_ladders],
                "requireConfirm": True,
            }), 202

        # Client confirmed: leave the affected ladders and cancel unplayed matches.
        violating_ladder_ids = [l.id for l in violating_ladders]

        cancel_unplayed_matches_for_team(
            team_id=team_id,
            ladder_ids=violating_ladder_ids,
            reason="Team dropped below minimum roster size and was removed from ladder.",
        )

        db.session.query(LadderTeam).filter(
            LadderTeam.team_id == team_id,
            LadderTeam.ladder_id.in_(violating_ladder_ids),
            ).delete(synchronize_session="fetch")

    db.session.delete(assoc)
    db.session.commit()

    cache.delete_memoized(get_team_players, team_id)

    response_body = {"message": "Player removed successfully."}
    if violating_ladders:
        response_body["droppedFromLadders"] = [
            {"id": l.id, "name": l.name} for l in violating_ladders
        ]

    return jsonify(response_body), 200

