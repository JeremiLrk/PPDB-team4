from flask import Blueprint, request, jsonify, abort, Response

from server.extensions import db
from server.app.decorators.login_required import login_required
from server.app.models.account import Account
from server.app.models.match_rule import MatchRuleSet, VALID_MATCH_FORMATS, VALID_THIRD_SET_FORMATS, VALID_DEUCE_RULES, VALID_GAME_FORMATS

rule_sets_bp = Blueprint("match_rule_sets", __name__)


def _get_rule_set_or_404(set_id: int) -> MatchRuleSet:
    rs = MatchRuleSet.query.get(set_id)
    if not rs:
        abort(404, description="Match rule set not found.")
    return rs


def _is_owner(resolved, rule_set: MatchRuleSet) -> bool:
    from server.app.models.account import Administrator
    if isinstance(resolved, Administrator):
        return True
    return getattr(resolved, "id", None) == rule_set.creator_id


def _extract_settings(data: dict) -> dict:
    """Validate and extract ruleset settings from request JSON."""
    match_format = data.get("matchFormat", "best_of_3")
    if match_format not in VALID_MATCH_FORMATS:
        abort(422, description=f"Invalid matchFormat. Choose from: {', '.join(VALID_MATCH_FORMATS)}.")

    third_set_format = data.get("thirdSetFormat", "super_tiebreak")
    if third_set_format not in VALID_THIRD_SET_FORMATS:
        abort(422, description=f"Invalid thirdSetFormat. Choose from: {', '.join(VALID_THIRD_SET_FORMATS)}.")

    deuce_rule = data.get("deuceRule", "advantage")
    if deuce_rule not in VALID_DEUCE_RULES:
        abort(422, description=f"Invalid deuceRule. Choose from: {', '.join(VALID_DEUCE_RULES)}.")

    game_format = data.get("gameFormat", "doubles")
    if game_format not in VALID_GAME_FORMATS:
        abort(422, description=f"Invalid gameFormat. Choose from: {', '.join(VALID_GAME_FORMATS)}.")

    timed_duration_minutes = None
    if match_format == "timed":
        raw = data.get("timedDurationMinutes")
        if raw is None:
            abort(422, description="Field 'timedDurationMinutes' is required when matchFormat is 'timed'.")
        try:
            timed_duration_minutes = int(raw)
        except (TypeError, ValueError):
            abort(422, description="'timedDurationMinutes' must be an integer.")
        if timed_duration_minutes <= 0:
            abort(422, description="'timedDurationMinutes' must be positive.")

    pro_set_games = None
    if match_format == "pro_set":
        raw = data.get("proSetGames", 8)
        try:
            pro_set_games = int(raw)
        except (TypeError, ValueError):
            abort(422, description="'proSetGames' must be an integer.")
        if pro_set_games <= 0:
            abort(422, description="'proSetGames' must be positive.")

    return {
        "match_format":           match_format,
        "timed_duration_minutes": timed_duration_minutes,
        "pro_set_games":          pro_set_games,
        "third_set_format":       third_set_format,
        "deuce_rule":             deuce_rule,
        "game_format":            game_format,
    }


# ---------------------------------------------------------------------------
# Public read endpoints
# ---------------------------------------------------------------------------

@rule_sets_bp.route("/<int:set_id>", methods=["GET"])
def get_rule_set(set_id: int) -> tuple[Response, int]:
    return jsonify({"ruleSet": _get_rule_set_or_404(set_id).to_dict()}), 200


@rule_sets_bp.route("", methods=["GET"])
def get_rule_sets() -> tuple[Response, int]:
    try:
        offset = int(request.args.get("from", 0))
        to     = int(request.args.get("to",   20))
    except ValueError:
        abort(422, description="'from' and 'to' must be integers.")

    if offset < 0 or to < offset:
        abort(422, description="'from' must be >= 0 and 'to' must be >= 'from'.")

    base      = MatchRuleSet.query.filter_by(can_be_used_by_others=True)
    total     = base.count()
    rule_sets = base.order_by(MatchRuleSet.id.asc()).offset(offset).limit(to - offset).all()

    return jsonify({
        "total":    total,
        "from":     offset,
        "to":       offset + len(rule_sets),
        "ruleSets": [rs.to_dict() for rs in rule_sets],
    }), 200


# ---------------------------------------------------------------------------
# Authenticated write endpoints
# ---------------------------------------------------------------------------

@rule_sets_bp.route("", methods=["POST"])
@login_required
def create_rule_set(account: Account) -> tuple[Response, int]:
    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    name = data.get("name", "").strip()
    if not name:
        abort(422, description="Field 'name' is required.")

    settings = _extract_settings(data)

    resolved = account.resolved_role
    rule_set = MatchRuleSet(
        name                  = name,
        description           = data.get("description", "").strip() or None,
        can_be_used_by_others = bool(data.get("canBeUsedByOthers", True)),
        creator_id            = resolved.id,
        club_id               = data.get("clubId"),
        **settings,
    )
    db.session.add(rule_set)
    db.session.commit()

    return jsonify({"message": "Match rule set created.", "ruleSet": rule_set.to_dict()}), 201


@rule_sets_bp.route("/<int:set_id>", methods=["PUT"])
@login_required
def update_rule_set(account: Account, set_id: int) -> tuple[Response, int]:
    rule_set = _get_rule_set_or_404(set_id)
    if not _is_owner(account.resolved_role, rule_set):
        abort(403, description="Forbidden: you are not the owner of this rule set.")

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    name = data.get("name", "").strip()
    if not name:
        abort(422, description="Field 'name' is required.")

    settings = _extract_settings(data)

    rule_set.name                  = name
    rule_set.description           = data.get("description", "").strip() or None
    rule_set.can_be_used_by_others = bool(data.get("canBeUsedByOthers", rule_set.can_be_used_by_others))
    for key, value in settings.items():
        setattr(rule_set, key, value)

    db.session.commit()
    return jsonify({"message": "Match rule set updated.", "ruleSet": rule_set.to_dict()}), 200


@rule_sets_bp.route("/<int:set_id>", methods=["DELETE"])
@login_required
def delete_rule_set(account: Account, set_id: int) -> tuple[Response, int]:
    rule_set = _get_rule_set_or_404(set_id)
    if not _is_owner(account.resolved_role, rule_set):
        abort(403, description="Forbidden: you are not the owner of this rule set.")

    db.session.delete(rule_set)
    db.session.commit()
    return jsonify({"message": "Match rule set deleted."}), 200
