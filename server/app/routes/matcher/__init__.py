from flask import Blueprint
from .matches import matches_core_bp
from .list import matches_list_bp
from .score import score_bp


matches_bp = Blueprint("matches", __name__, url_prefix="/api/matches")

matches_bp.register_blueprint(matches_core_bp)
matches_bp.register_blueprint(matches_list_bp)
matches_bp.register_blueprint(score_bp)
