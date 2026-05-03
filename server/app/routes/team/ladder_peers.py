"""
GET /api/teams/<team_id>/ladder-peers?ladder_id=<ladder_id>

Returns every team that shares the given ladder with <team_id>,
excluding <team_id> itself, ordered by rank then rating.

Responses
---------
200  { ladderId, teamId, peers: [{ id, name, clubId, clubName, sportTypeId,
                                   rank, rating, matchesPlayed }] }
400  ladder_id query parameter is missing or not an integer
404  team not found | ladder not found | team is not a member of that ladder
"""

from flask import Blueprint, jsonify, abort, request

from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.models.team import Team
from server.extensions import db

ladder_peers_bp = Blueprint("ladder_peers", __name__)


@ladder_peers_bp.route("/<int:team_id>/ladder-peers", methods=["GET"])
def get_ladder_peers(team_id: int):
    """
    GET /api/teams/<team_id>/ladder-peers?ladder_id=<ladder_id>

    Returns all teams registered in <ladder_id> except <team_id> itself,
    ordered by ladder rank ascending (ties broken by rating desc, then id asc).
    Public endpoint — no authentication required.
    """
    # ------------------------------------------------------------------
    # 1. Parse and validate query parameter
    # ------------------------------------------------------------------
    raw_ladder_id = request.args.get("ladder_id")
    if not raw_ladder_id:
        abort(400, description="Query parameter 'ladder_id' is required.")

    try:
        ladder_id = int(raw_ladder_id)
    except ValueError:
        abort(400, description="Query parameter 'ladder_id' must be an integer.")

    # ------------------------------------------------------------------
    # 2. Verify that both the team and the ladder exist
    # ------------------------------------------------------------------
    focal_team = Team.query.get(team_id)
    if not focal_team:
        abort(404, description=f"Team {team_id} not found.")

    ladder = Ladder.query.get(ladder_id)
    if not ladder:
        abort(404, description=f"Ladder {ladder_id} not found.")

    # ------------------------------------------------------------------
    # 3. Verify that the focal team is a member of the ladder
    # ------------------------------------------------------------------
    focal_row = LadderTeam.query.filter_by(
        ladder_id=ladder_id,
        team_id=team_id,
    ).first()
    if not focal_row:
        abort(
            404,
            description=f"Team {team_id} is not a member of ladder {ladder_id}.",
        )

    # ------------------------------------------------------------------
    # 4. Fetch all other teams in the same ladder
    # ------------------------------------------------------------------
    rows = (
        db.session.query(Team, LadderTeam)
        .join(LadderTeam, Team.id == LadderTeam.team_id)
        .filter(
            LadderTeam.ladder_id == ladder_id,
            LadderTeam.team_id   != team_id,
        )
        .order_by(
            LadderTeam.rank.asc(),
            LadderTeam.rating.desc(),
            Team.id.asc(),
        )
        .all()
    )

    peers = [
        {
            "id":            team.id,
            "name":          team.name,
            "clubId":        team.club_id,
            "clubName":      team.club.name if team.club else None,
            "sportTypeId":   team.sport_type_id,
            "rank":          ladder_row.rank,
            "rating":        ladder_row.rating,
            "matchesPlayed": ladder_row.matches_played,
        }
        for team, ladder_row in rows
    ]

    return jsonify({
        "ladderId": ladder_id,
        "teamId":   team_id,
        "peers":    peers,
    }), 200
