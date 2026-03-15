from flask import Blueprint
from server.app.services.ladders_service import get_all_club_ladders
from server.app.models.team import Team
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.models import db

ladders_bp = Blueprint("ladders", __name__, url_prefix="/api")

@ladders_bp.get("/clubs/<int:club_id>/ladders")
def get_ladders(club_id):
    ladders = get_all_club_ladders(club_id)
    return [
        {
            "id": l.id,
            "club_id": l.club_id,
            "name": l.name,
            "description": l.description,
            "sport_type_id": l.sport_type_id,
            "ruleset_id": l.ruleset_id,
            "ladder_rating_function_id": l.ladder_rating_function_id
        }
        for l in ladders
    ]

@ladders_bp.get("/clubs/<int:club_id>/top-players")
def get_top_players(club_id: int, limit: int = 3):
    results = (
        db.session.query(Team, LadderTeam)
        .join(LadderTeam, Team.id == LadderTeam.team_id)
        .join(Ladder, Ladder.id == LadderTeam.ladder_id)
        .filter(Ladder.club_id == club_id)
        .order_by(LadderTeam.rating.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": team.id,
            "name": team.name,
            "rating": ladder_team.rating,
        }
        for team, ladder_team in results
    ]
