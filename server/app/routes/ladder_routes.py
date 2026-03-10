from flask import Blueprint
from server.app.services.ladder_service import get_all_ladder

ladder_bp = Blueprint("ladders", __name__, url_prefix="/api")

@ladder_bp.get("/ladders")
def get_ladders():
    ladders = get_all_ladder()
    return [
        {
            "id": l.id,
            "name": l.name,
            "description": l.description,
            "sport_type_id": l.sport_type,
            "ruleset_id": l.rule_set,
            "ladder_rating_function_id": l.ladder_rating_function_id
        }
        for l in ladders
    ]