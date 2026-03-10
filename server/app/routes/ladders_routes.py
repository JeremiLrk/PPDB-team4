from flask import Blueprint
from server.app.services.ladders_service import get_all_club_ladders

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
            "sport_type_id": l.sport_type,
            "ruleset_id": l.rule_set,
            "ladder_rating_function_id": l.ladder_rating_function_id
        }
        for l in ladders
    ]