"""
Routes for MatchRuleSet:
  POST   /api/match-rule-sets                                          — create a set
  DELETE /api/match-rule-sets/<set_id>                                 — delete a set
  PATCH  /api/match-rule-sets/<set_id>/name                            — rename a set
  PATCH  /api/match-rule-sets/<set_id>/description                     — change description
  POST   /api/match-rule-sets/<set_id>/rules                           — add a rule to a set
  DELETE /api/match-rule-sets/<set_id>/rules/<rule_id>                 — remove rule from set
  GET    /api/match-rule-sets/<set_id>                                 — get a set (public)
  GET    /api/match-rule-sets                                          — list sets (public)
"""

from flask import Blueprint, request, jsonify, abort, Response

from server.extensions import db
from server.app.decorators.login_required import login_required
from server.app.models.account import Account
from server.app.models.match_rule import MatchRuleSet, MatchRuleSetRule
from ._helpers import (
    _get_rule_or_404,
    _get_rule_set_or_404,
    _is_owner_of_rule_set,
    _can_use_rule,
)

rule_sets_bp = Blueprint("match_rule_sets", __name__)


# ---------------------------------------------------------------------------
# Public read endpoints
# ---------------------------------------------------------------------------

@rule_sets_bp.route("/<int:set_id>", methods=["GET"])
def get_rule_set(set_id: int) -> tuple[Response, int]:
    """GET /api/match-rule-sets/<set_id> — public."""
    rule_set = _get_rule_set_or_404(set_id)
    return jsonify({"ruleSet": rule_set.to_dict()}), 200


@rule_sets_bp.route("", methods=["GET"])
def get_rule_sets() -> tuple[Response, int]:
    """GET /api/match-rule-sets?from=0&to=20 — lists publicly usable rule sets."""
    try:
        offset = int(request.args.get("from", 0))
        to     = int(request.args.get("to",   20))
    except ValueError:
        abort(422, description="'from' and 'to' must be integers.")

    if offset < 0 or to < offset:
        abort(422, description="'from' must be >= 0 and 'to' must be >= 'from'.")

    limit = to - offset

    base     = MatchRuleSet.query.filter_by(can_be_used_by_others=True)
    total    = base.count()
    rule_sets = base.order_by(MatchRuleSet.id.asc()).offset(offset).limit(limit).all()

    return jsonify({
        "total":    total,
        "from":     offset,
        "to":       offset + len(rule_sets),
        "ruleSets": [rs.to_dict() for rs in rule_sets],
    }), 200


# ---------------------------------------------------------------------------
# Authenticated write endpoints — set lifecycle
# ---------------------------------------------------------------------------

@rule_sets_bp.route("", methods=["POST"])
@login_required
def create_rule_set(account: Account) -> tuple[Response, int]:
    """POST /api/match-rule-sets — create a new match rule set."""
    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    name = data.get("name", "").strip()
    if not name:
        abort(422, description="Field 'name' is required.")

    description           = data.get("description", "").strip() or None
    can_be_used_by_others = bool(data.get("canBeUsedByOthers", True))
    club_id               = data.get("clubId")

    resolved   = account.resolved_role
    creator_id = resolved.id

    rule_set = MatchRuleSet(
        name=name,
        description=description,
        can_be_used_by_others=can_be_used_by_others,
        creator_id=creator_id,
        club_id=club_id,
    )
    db.session.add(rule_set)
    db.session.commit()

    return jsonify({
        "message": "Match rule set created successfully.",
        "ruleSet": rule_set.to_dict(),
    }), 201


@rule_sets_bp.route("/<int:set_id>", methods=["DELETE"])
@login_required
def delete_rule_set(account: Account, set_id: int) -> tuple[Response, int]:
    """DELETE /api/match-rule-sets/<set_id> — delete a rule set (owner or admin)."""
    rule_set = _get_rule_set_or_404(set_id)
    resolved = account.resolved_role

    if not _is_owner_of_rule_set(resolved, rule_set):
        abort(403, description="Forbidden: you are not the owner of this rule set.")

    db.session.delete(rule_set)
    db.session.commit()

    return jsonify({"message": "Match rule set deleted successfully."}), 200


@rule_sets_bp.route("/<int:set_id>/name", methods=["PATCH"])
@login_required
def rename_rule_set(account: Account, set_id: int) -> tuple[Response, int]:
    """PATCH /api/match-rule-sets/<set_id>/name — rename a rule set."""
    rule_set = _get_rule_set_or_404(set_id)
    resolved = account.resolved_role

    if not _is_owner_of_rule_set(resolved, rule_set):
        abort(403, description="Forbidden: you are not the owner of this rule set.")

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    name = data.get("name", "").strip()
    if not name:
        abort(422, description="Field 'name' is required.")
    if name == rule_set.name:
        abort(422, description="New name is the same as the current name.")

    rule_set.name = name
    db.session.commit()

    return jsonify({
        "message": "Match rule set renamed successfully.",
        "ruleSet": rule_set.to_dict(),
    }), 200


@rule_sets_bp.route("/<int:set_id>/description", methods=["PATCH"])
@login_required
def update_rule_set_description(account: Account, set_id: int) -> tuple[Response, int]:
    """PATCH /api/match-rule-sets/<set_id>/description — change description."""
    rule_set = _get_rule_set_or_404(set_id)
    resolved = account.resolved_role

    if not _is_owner_of_rule_set(resolved, rule_set):
        abort(403, description="Forbidden: you are not the owner of this rule set.")

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    description = data.get("description", "").strip() or None

    if description == rule_set.description:
        abort(422, description="New description is the same as the current one.")

    rule_set.description = description
    db.session.commit()

    return jsonify({
        "message": "Match rule set description updated successfully.",
        "ruleSet": rule_set.to_dict(),
    }), 200


# ---------------------------------------------------------------------------
# Authenticated write endpoints — rule membership in set
# ---------------------------------------------------------------------------

@rule_sets_bp.route("/<int:set_id>/rules", methods=["POST"])
@login_required
def add_rule_to_set(account: Account, set_id: int) -> tuple[Response, int]:
    """POST /api/match-rule-sets/<set_id>/rules — add a rule to a set."""
    rule_set = _get_rule_set_or_404(set_id)
    resolved = account.resolved_role

    if not _is_owner_of_rule_set(resolved, rule_set):
        abort(403, description="Forbidden: you are not the owner of this rule set.")

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    rule_id = data.get("ruleId")
    if not rule_id:
        abort(422, description="Field 'ruleId' is required.")

    rule = _get_rule_or_404(rule_id)

    if not _can_use_rule(resolved, rule):
        abort(403, description="Forbidden: this rule is private and does not belong to you.")

    already = any(a.match_rule_id == rule.id for a in rule_set.rule_associations)
    if already:
        abort(409, description="This rule is already part of the rule set.")

    assoc = MatchRuleSetRule(
        match_rule_set_id=rule_set.id,
        match_rule_id=rule.id,
    )
    db.session.add(assoc)
    db.session.commit()

    return jsonify({
        "message": "Rule added to rule set successfully.",
        "ruleSet": rule_set.to_dict(),
    }), 201


@rule_sets_bp.route("/<int:set_id>/rules/<int:rule_id>", methods=["DELETE"])
@login_required
def remove_rule_from_set(account: Account, set_id: int, rule_id: int) -> tuple[Response, int]:
    """DELETE /api/match-rule-sets/<set_id>/rules/<rule_id> — remove rule from set."""
    rule_set = _get_rule_set_or_404(set_id)
    resolved = account.resolved_role

    if not _is_owner_of_rule_set(resolved, rule_set):
        abort(403, description="Forbidden: you are not the owner of this rule set.")

    assoc = next(
        (a for a in rule_set.rule_associations if a.match_rule_id == rule_id),
        None,
    )
    if assoc is None:
        abort(404, description="Rule is not part of this rule set.")

    db.session.delete(assoc)
    db.session.commit()

    return jsonify({
        "message": "Rule removed from rule set successfully.",
        "ruleSet": rule_set.to_dict(),
    }), 200