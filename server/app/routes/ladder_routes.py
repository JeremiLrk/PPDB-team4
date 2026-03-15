from flask import Blueprint
from server.app.services.ladder_service import get_all_players_ladder

ladder_bp = Blueprint("ladder", __name__, url_prefix="/api")

@ladder_bp.get("/clubs/<int:club_id>/ladders/<int:ladder_id>")
def get_players(club_id, ladder_id):
    rows = get_all_players_ladder(ladder_id)
    return [
        {
            "id": team.id,
            "name": team.name,
            "rating": ladder_team.rating
        }
        for team, ladder_team in rows
    ]
