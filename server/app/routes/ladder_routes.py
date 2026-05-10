from flask import Blueprint, jsonify

from server.app.models.ladder import Ladder, LadderRatingFunction
from server.app.models.match_rule import MatchRuleSet
from server.app.models.sport_type import SportType
from server.app.services.ladder_service import get_all_players_ladder
from server.extensions import db

ladder_bp = Blueprint("ladder", __name__, url_prefix="/api")


@ladder_bp.get("/clubs/<int:club_id>/ladders/<int:ladder_id>/players")
def get_players(club_id, ladder_id):
    rows = get_all_players_ladder(ladder_id)
    return [
        {
            "id": team.id,
            "name": team.name,
            "rating": ladder_team.rating,
        }
        for team, ladder_team in rows
    ]


@ladder_bp.get("/clubs/<int:club_id>/ladders/<int:ladder_id>")
def get_ladder_rows(club_id, ladder_id):
    # Backward-compatible contract: this endpoint returns ladder rows.
    rows = get_all_players_ladder(ladder_id)
    return [
        {
            "id": team.id,
            "name": team.name,
            "rating": ladder_team.rating,
        }
        for team, ladder_team in rows
    ]


@ladder_bp.get("/clubs/<int:club_id>/ladders/<int:ladder_id>/details")
def get_ladder_details(club_id, ladder_id):
    result = (
        db.session.query(Ladder, SportType.name, MatchRuleSet, LadderRatingFunction.name)
        .outerjoin(SportType, Ladder.sport_type_id == SportType.id)
        .outerjoin(MatchRuleSet, Ladder.ruleset_id == MatchRuleSet.id)
        .outerjoin(LadderRatingFunction, Ladder.ladder_rating_function_id == LadderRatingFunction.id)
        .filter(Ladder.id == ladder_id, Ladder.club_id == club_id)
        .first()
    )

    if not result:
        return jsonify({"message": "Ladder not found"}), 404

    ladder, sport_name, rule_set, rating_func_name = result

    return jsonify(
        {
            "id": ladder.id,
            "name": ladder.name,
            "description": ladder.description,
            "sport_type": sport_name,
            "ruleset": rule_set.to_dict() if rule_set else None,
            "rating_function": rating_func_name,
        }
    )
