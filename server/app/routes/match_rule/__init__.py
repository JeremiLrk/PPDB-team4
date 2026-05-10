from flask import Blueprint
from .rule_sets import rule_sets_bp

match_rule_set_bp = Blueprint("match_rule_set", __name__, url_prefix="/api/match-rule-sets")
match_rule_set_bp.register_blueprint(rule_sets_bp)

# Kept for backward-compatibility — no individual rules anymore
match_rule_bp = Blueprint("match_rule", __name__, url_prefix="/api/match-rules")
