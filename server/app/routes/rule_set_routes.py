from flask import Blueprint, jsonify
from server.app.models.match_rule import MatchRuleSet

rule_set_bp = Blueprint("rule_set", __name__, url_prefix="/api")

@rule_set_bp.get("/rule-sets")
def get_rule_sets():
    rule_sets = MatchRuleSet.query.order_by(MatchRuleSet.name).all()
    return jsonify({
        "ruleSets": [
            {
                "id": rs.id,
                "name": rs.name,
                "description": rs.description
            }
            for rs in rule_sets
        ]
    }), 200
