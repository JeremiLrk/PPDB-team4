from flask import Blueprint, jsonify
from server.app.models.ladder import LadderRatingFunction
from server.extensions import cache

rating_function_bp = Blueprint("rating_function", __name__, url_prefix="/api")

@rating_function_bp.get("/rating-functions")
@cache.cached(timeout=600, key_prefix="rating_functions")
def get_rating_functions():
    functions = LadderRatingFunction.query.order_by(LadderRatingFunction.name).all()
    return jsonify({
        "ratingFunctions": [
            {
                "id": rf.id,
                "name": rf.name
            }
            for rf in functions
        ]
    }), 200