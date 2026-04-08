from flask import Blueprint, request, jsonify
from server.app.models.account import Account, Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.team import Team, TeamManager
from server.app.decorators.login_required import login_required
from server.extensions import db
from ._helpers import _parse_pagination

my_teams_bp = Blueprint("team_my", __name__)


@my_teams_bp.route("/my", methods=["GET"])
@login_required
def get_my_teams(account: Account):
    """
    GET /api/teams/my?from=0&to=20&sort=name
    Команди якими керує поточний акаунт.
    Administrator бачить всі. ClubOwner — клубні + прямо керовані.
    TeamManager — лише керовані. Інші — порожній список.
    """
    offset, limit, sort_col = _parse_pagination(request.args)

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
    GET /api/teams/my-all?from=0&to=20&sort=name
    Всі команди де акаунт задіяний — як менеджер, власник клубу або гравець.
    """
    offset, limit, sort_col = _parse_pagination(request.args)

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