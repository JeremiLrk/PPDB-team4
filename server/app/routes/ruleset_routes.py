from flask import Blueprint, request, jsonify
from server.app.models.ladder import Rule, MatchRuleSet
from server.extensions import db

# Create the Blueprint
ruleset_bp = Blueprint('ruleset_routes', __name__, url_prefix='/api')

@ruleset_bp.route('/rules', methods=['GET'])
def get_rules():
    """Fetch all available individual rules."""
    rules = Rule.query.all()
    return jsonify([rule.to_dict() for rule in rules]), 200

@ruleset_bp.route('/rules', methods=['POST'])
def create_rule():
    """Create a new standalone rule (just a string)."""
    data = request.get_json()

    if not data or not data.get('content'):
        return jsonify({"error": "Rule content is required"}), 400

    new_rule = Rule(content=data.get('content'))
    db.session.add(new_rule)
    db.session.commit()

    return jsonify(new_rule.to_dict()), 201

@ruleset_bp.route('/rulesets', methods=['GET'])
def get_rulesets():
    """Fetch all rulesets and their attached rules."""
    # FIXED: Was RuleSet.query.all()
    rulesets = MatchRuleSet.query.all()
    return jsonify([rs.to_dict() for rs in rulesets]), 200

@ruleset_bp.route('/rulesets', methods=['POST'])
def create_ruleset():
    """Create a ruleset and attach existing rules to it."""
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({"error": "Ruleset name is required"}), 400

    # FIXED: Was RuleSet(name=...)
    new_ruleset = MatchRuleSet(name=data.get('name'))

    # Frontend sends an array of rule IDs: e.g., {"name": "Pro Rules", "rule_ids": [1, 2]}
    rule_ids = data.get('rule_ids', [])
    if rule_ids:
        rules_to_attach = Rule.query.filter(Rule.id.in_(rule_ids)).all()
        new_ruleset.rules.extend(rules_to_attach)

    db.session.add(new_ruleset)
    db.session.commit()

    return jsonify(new_ruleset.to_dict()), 201