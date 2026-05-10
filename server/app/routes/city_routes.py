from flask import Blueprint, jsonify, request

from server.app.services.city_service import search_cities

city_bp = Blueprint("cities", __name__, url_prefix="/api")


@city_bp.get("/cities/search")
def search_city():
    query = request.args.get("q", "")
    if not query.strip():
        return jsonify({"cities": []}), 200

    try:
        cities = search_cities(query)
    except RuntimeError as exc:
        return jsonify({"message": str(exc)}), 500
    except Exception:
        return jsonify({"message": "Failed to search cities."}), 502

    return jsonify({"cities": cities}), 200
