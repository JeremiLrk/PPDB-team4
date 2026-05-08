"""
Backward-compatible helpers for legacy tests/imports.

The current team implementation lives under `server.app.routes.team.*`.
This module keeps older helper signatures available.
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from server.app.models.account import Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.team import TeamManager, Team

team__bp = Blueprint("team_", __name__, url_prefix="/api")


def _parse_pagination(args):
    try:
        offset = int(args.get("from", 0))
        to = int(args.get("to", 20))
    except ValueError:
        return None, None, None, (jsonify({"message": "'from' and 'to' must be integers."}), 422)

    if offset < 0 or to < offset:
        return None, None, None, (jsonify({"message": "'from' must be >= 0 and 'to' must be >= 'from'."}), 422)

    limit = to - offset

    sort = args.get("sort", "id")
    if sort == "name":
        from server.app.models.team import Team

        sort_col = Team.name.asc()
    elif sort == "id":
        from server.app.models.team import Team

        sort_col = Team.id.asc()
    else:
        return None, None, None, (jsonify({"message": "'sort' must be 'id' or 'name'."}), 422)

    return offset, limit, sort_col, None


def _can_edit_team(resolved, team):
    if isinstance(resolved, Administrator):
        return True
    if isinstance(resolved, ClubOwner):
        return team.club is not None and team.club in resolved.clubs
    if isinstance(resolved, TeamManager):
        # Legacy behavior: team managers may edit teams they manage only when
        # the team has no club owner context.
        return team in resolved.teams and team.club_id is None
    return False

@team__bp.get("/clubs/<int:club_id>/eligible-teams")
def get_eligible_teams(club_id):
    """
    Returns teams that either belong to this club OR are unaffiliated (club_id is NULL).
    """
    try:
        # Query teams where club_id matches or is None
        teams = Team.query.filter(
            or_(Team.club_id == club_id, Team.club_id == None)
        ).all()
        
        # Use the to_dict method from your Team model
        return jsonify({
            "teams": [t.to_dict() for t in teams]
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500