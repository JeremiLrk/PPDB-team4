"""
Personal team views and join-request actions.

These routes back the "my teams", "my all teams", and join-request tabs in
the frontend dashboard and team management screens.
"""

from flask import Blueprint, request, jsonify, abort
from server.app.models.account import Account, Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.team import Team, TeamManager
from server.app.decorators.login_required import login_required
from server.extensions import db
from ._helpers import parse_pagination, resolve_target, get_team_or_404
from ._permissions import can_manage_join_request_or_403
from ...models.player import PlayerTeam
from ...models.team_join_request import TeamJoinRequest
from ...utils.promote import promote_to_player

my_teams_bp = Blueprint("team_my", __name__)


@my_teams_bp.route("/my", methods=["GET"])
@login_required
def get_my_teams(account: Account):
    """
    Return the teams managed by the current account.
    """
    offset, limit, sort_col = parse_pagination(request.args)

    resolved = account.resolved_role

    if isinstance(resolved, Administrator):
        base_query = Team.query

    elif isinstance(resolved, ClubOwner):
        club_ids    = [c.id for c in resolved.clubs]
        managed_ids = [t.id for t in resolved.team_manager.teams]
        base_query  = Team.query.filter(
            db.or_(Team.club_id.in_(club_ids), Team.id.in_(managed_ids))
        )

    elif isinstance(resolved, TeamManager):
        managed_ids = [t.id for t in resolved.teams]
        base_query  = Team.query.filter(Team.id.in_(managed_ids))

    else:
        return jsonify({
            "total": 0,
            "from": offset,
            "to": offset,
            "teams": []
        }), 200

    total = base_query.count()
    teams = base_query.order_by(sort_col).offset(offset).limit(limit).all()

    return jsonify({
        "total": total,
        "from": offset,
        "to": offset + len(teams),
        "teams": [t.to_dict() for t in teams]
    }), 200


@my_teams_bp.route("/my-all", methods=["GET"])
@login_required
def get_my_all_teams(account: Account):
    """
    Return every team where the account is involved.
    """
    offset, limit, sort_col = parse_pagination(request.args)

    resolved = account.resolved_role

    if isinstance(resolved, Administrator):
        total = Team.query.count()
        teams = Team.query.order_by(sort_col).offset(offset).limit(limit).all()
        return jsonify({
            "total": total,
            "from": offset,
            "to": offset + len(teams),
            "teams": [t.to_dict() for t in teams]
        }), 200

    team_ids: set[int] = set()

    if isinstance(resolved, ClubOwner):
        for club in resolved.clubs:
            for t in club.teams:
                team_ids.add(t.id)
        if resolved.team_manager:
            for t in resolved.team_manager.teams:
                team_ids.add(t.id)
    elif isinstance(resolved, TeamManager):
        for t in resolved.teams:
            team_ids.add(t.id)

    if account.player is not None:
        for t in account.player.teams:
            team_ids.add(t.id)

    if not team_ids:
        return jsonify({
            "total": 0,
            "from": offset,
            "to": offset,
            "teams": []
        }), 200

    base_query = Team.query.filter(Team.id.in_(team_ids))
    total = base_query.count()
    teams = base_query.order_by(sort_col).offset(offset).limit(limit).all()

    return jsonify({
        "total": total,
        "from": offset,
        "to": offset + len(teams),
        "teams": [t.to_dict() for t in teams]
    }), 200

@my_teams_bp.route("/<int:team_id>/players/join-requests/<int:request_id>/accept", methods=["POST"])
@login_required
def accept_player_join_request(account: Account, team_id: int, request_id: int):
    """Accept a player join request."""
    team = get_team_or_404(team_id)
    resolved = account.resolved_role

    join_request = db.session.query(TeamJoinRequest).filter(
        TeamJoinRequest.id == request_id,
        TeamJoinRequest.team_id == team_id,
        ).first()

    if not join_request:
        abort(404, description="Join request not found.")

    can_manage_join_request_or_403(resolved, join_request, team)

    if join_request.status != "pending":
        abort(409, description="Join request is not in pending status.")

    join_request.status = "accepted"
    db.session.flush()

    target = resolve_target(join_request.user_id)
    promote_to_player(target)

    assoc = PlayerTeam(player_id=target.player.id, team_id=team.id)
    db.session.add(assoc)
    db.session.commit()

    return jsonify({
        "message": "Player join request accepted successfully.",
        "request": join_request.serialize()
    }), 200


@my_teams_bp.route("/<int:team_id>/players/join-requests/<int:request_id>/reject", methods=["POST"])
@login_required
def reject_player_join_request(account: Account, team_id: int, request_id: int):
    """Reject a player join request."""
    team = get_team_or_404(team_id)
    resolved = account.resolved_role

    join_request = db.session.query(TeamJoinRequest).filter(
        TeamJoinRequest.id == request_id,
        TeamJoinRequest.team_id == team_id,
        ).first()

    if not join_request:
        abort(404, description="Join request not found.")

    can_manage_join_request_or_403(resolved, join_request, team)

    if join_request.status != "pending":
        abort(409, description="Join request is not in pending status.")

    join_request.status = "rejected"
    db.session.commit()

    return jsonify({
        "message": "Player join request rejected successfully.",
        "request": join_request.serialize()
    }), 200

@my_teams_bp.route("/my-join-requests", methods=["GET"])
@login_required
def get_my_join_requests(account: Account):
    """Return the pending join requests sent by the current user."""

    requests = (
        db.session.query(TeamJoinRequest)
        .filter(
            TeamJoinRequest.user_id == account.id,
            TeamJoinRequest.status == "pending",
            )
        .order_by(TeamJoinRequest.date.desc())
        .all()
    )

    return jsonify({
        "total": len(requests),
        "joinRequests": [r.serialize() for r in requests],
    }), 200
