"""
Routes for MatchRule:
  POST   /api/match-rules                        — create a rule
  DELETE /api/match-rules/<rule_id>              — delete a rule
  PATCH  /api/match-rules/<rule_id>/name         — rename a rule
  PATCH  /api/match-rules/<rule_id>/description  — change description
  GET    /api/match-rules/<rule_id>              — get a rule (public)
  GET    /api/match-rules                        — list rules (public)
"""

from flask import Blueprint, request, jsonify, abort, Response

from server.extensions import db
from server.app.decorators.login_required import login_required
from server.app.models.account import Account
from server.app.models.match_rule import MatchRule
from ._helpers import _get_rule_or_404, _is_owner_of_rule

rules_bp = Blueprint("match_rules", __name__)


# ---------------------------------------------------------------------------
# Public read endpoints
# ---------------------------------------------------------------------------

@rules_bp.route("/<int:rule_id>", methods=["GET"])
def get_rule(rule_id: int) -> tuple[Response, int]:
    """GET /api/match-rules/<rule_id> — public."""
    rule = _get_rule_or_404(rule_id)
    return jsonify({"rule": rule.to_dict()}), 200


@rules_bp.route("", methods=["GET"])
def get_rules() -> tuple[Response, int]:
    """GET /api/match-rules?from=0&to=20 — lists publicly usable rules."""
    try:
        offset = int(request.args.get("from", 0))
        to     = int(request.args.get("to",   20))
    except ValueError:
        abort(422, description="'from' and 'to' must be integers.")

    if offset < 0 or to < offset:
        abort(422, description="'from' must be >= 0 and 'to' must be >= 'from'.")

    limit = to - offset

    base  = MatchRule.query.filter_by(can_be_used_by_others=True)
    total = base.count()
    rules = base.order_by(MatchRule.id.asc()).offset(offset).limit(limit).all()

    return jsonify({
        "total": total,
        "from":  offset,
        "to":    offset + len(rules),
        "rules": [r.to_dict() for r in rules],
    }), 200


# ---------------------------------------------------------------------------
# Authenticated write endpoints
# ---------------------------------------------------------------------------

@rules_bp.route("", methods=["POST"])
@login_required
def create_rule(account: Account) -> tuple[Response, int]:
    """POST /api/match-rules — create a new match rule."""
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

    rule = MatchRule(
        name=name,
        description=description,
        can_be_used_by_others=can_be_used_by_others,
        creator_id=creator_id,
        club_id=club_id,
    )
    db.session.add(rule)
    db.session.commit()

    return jsonify({
        "message": "Match rule created successfully.",
        "rule":    rule.to_dict(),
    }), 201


@rules_bp.route("/<int:rule_id>", methods=["DELETE"])
@login_required
def delete_rule(account: Account, rule_id: int) -> tuple[Response, int]:
    """DELETE /api/match-rules/<rule_id> — delete a rule (owner or admin only)."""
    rule     = _get_rule_or_404(rule_id)
    resolved = account.resolved_role

    if not _is_owner_of_rule(resolved, rule):
        abort(403, description="Forbidden: you are not the owner of this rule.")

    db.session.delete(rule)
    db.session.commit()

    return jsonify({"message": "Match rule deleted successfully."}), 200


@rules_bp.route("/<int:rule_id>/name", methods=["PATCH"])
@login_required
def rename_rule(account: Account, rule_id: int) -> tuple[Response, int]:
    """PATCH /api/match-rules/<rule_id>/name — rename a rule."""
    rule     = _get_rule_or_404(rule_id)
    resolved = account.resolved_role

    if not _is_owner_of_rule(resolved, rule):
        abort(403, description="Forbidden: you are not the owner of this rule.")

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    name = data.get("name", "").strip()
    if not name:
        abort(422, description="Field 'name' is required.")
    if name == rule.name:
        abort(422, description="New name is the same as the current name.")

    rule.name = name
    db.session.commit()

    return jsonify({
        "message": "Match rule renamed successfully.",
        "rule":    rule.to_dict(),
    }), 200


@rules_bp.route("/<int:rule_id>/description", methods=["PATCH"])
@login_required
def update_rule_description(account: Account, rule_id: int) -> tuple[Response, int]:
    """PATCH /api/match-rules/<rule_id>/description — change description."""
    rule     = _get_rule_or_404(rule_id)
    resolved = account.resolved_role

    if not _is_owner_of_rule(resolved, rule):
        abort(403, description="Forbidden: you are not the owner of this rule.")

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    description = data.get("description", "").strip() or None

    if description == rule.description:
        abort(422, description="New description is the same as the current one.")

    rule.description = description
    db.session.commit()

    return jsonify({
        "message": "Match rule description updated successfully.",
        "rule":    rule.to_dict(),
    }), 200