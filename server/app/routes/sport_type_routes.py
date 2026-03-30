from flask import Blueprint, jsonify
from server.app.models.sport_type import SportType

sport_type_bp = Blueprint("sport_type", __name__, url_prefix="/api/sport-types")

@sport_type_bp.route("", methods=["GET"])
def get_sport_types():
  sport_types = SportType.query.order_by(SportType.name).all()
  return jsonify({
    "sportTypes": [
      {
        "id":   st.id,
        "name": st.name,
        "minPlayers": st.minimum_number_of_players_on_a_team,
        "maxPlayers": st.maximum_number_of_players_per_team,
      }
      for st in sport_types
    ]
  }), 200