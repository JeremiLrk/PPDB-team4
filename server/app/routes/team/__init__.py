from flask import Blueprint
from .core import core_bp
from .membership import membership_bp
from .my_teams import my_teams_bp
from .ladder_peers import ladder_peers_bp

team_bp = Blueprint("team", __name__, url_prefix="/api/teams")

team_bp.register_blueprint(core_bp)
team_bp.register_blueprint(membership_bp)
team_bp.register_blueprint(my_teams_bp)
team_bp.register_blueprint(ladder_peers_bp)
