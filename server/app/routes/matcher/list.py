from flask import Blueprint, Response, request, jsonify

from server.app.decorators import login_required
from server.app.models.account import Account, Administrator
from server.app.models.match import MatchProposal, MatchStatus
from server.app.routes.matcher._helpers import _parse_pagination, _team_ids_managed_by
from server.extensions import db

matches_list_bp = Blueprint("matches_list", __name__)

# ===========================================================================
# GET /api/matches/active  — accepted matches not yet played/cancelled
# ===========================================================================

@matches_list_bp.route("/active", methods=["GET"])
def get_active_matches() -> tuple[Response, int]:
    """
    GET /api/matches/active?from=0&to=20
    Returns all proposals with status=accepted (public).
    """
    offset, limit = _parse_pagination(request.args)

    base  = MatchProposal.query.filter_by(status_id=MatchStatus.ACCEPTED)
    total = base.count()
    items = base.order_by(MatchProposal.id.desc()).offset(offset).limit(limit).all()

    return jsonify({
        "total":   total,
        "from":    offset,
        "to":      offset + len(items),
        "matches": [m.to_dict_full() for m in items],
    }), 200


# ===========================================================================
# GET /api/matches/played  — finished matches with a score
# ===========================================================================

@matches_list_bp.route("/played", methods=["GET"])
def get_played_matches() -> tuple[Response, int]:
    """
    GET /api/matches/played?from=0&to=20
    Returns all proposals with status=played (public).
    """
    offset, limit = _parse_pagination(request.args)

    base  = MatchProposal.query.filter_by(status_id=MatchStatus.PLAYED)
    total = base.count()
    items = base.order_by(MatchProposal.id.desc()).offset(offset).limit(limit).all()

    return jsonify({
        "total":   total,
        "from":    offset,
        "to":      offset + len(items),
        "matches": [m.to_dict_full() for m in items],
    }), 200


# ===========================================================================
# GET /api/matches/pending  — proposals the current user can accept/reject
# ===========================================================================

@matches_list_bp.route("/pending", methods=["GET"])
@login_required
def get_pending_matches(account: Account) -> tuple[Response, int]:
    """
    GET /api/matches/pending?from=0&to=20
    Returns proposals with status=pending where the current user manages team2.
    Administrator sees all pending proposals.
    """
    resolved      = account.resolved_role
    offset, limit = _parse_pagination(request.args)

    base = MatchProposal.query.filter_by(status_id=MatchStatus.PENDING)

    if not isinstance(resolved, Administrator):
        managed_ids = _team_ids_managed_by(resolved)
        if not managed_ids:
            return jsonify({"total": 0, "from": offset, "to": offset, "matches": []}), 200
        base = base.filter(MatchProposal.team2_id.in_(managed_ids))

    total = base.count()
    items = base.order_by(MatchProposal.id.desc()).offset(offset).limit(limit).all()

    return jsonify({
        "total":   total,
        "from":    offset,
        "to":      offset + len(items),
        "matches": [m.to_dict() for m in items],
    }), 200


# ===========================================================================
# GET /api/matches/awaiting-result  — accepted matches needing a result
# ===========================================================================

@matches_list_bp.route("/awaiting-result", methods=["GET"])
@login_required
def get_awaiting_result_matches(account: Account) -> tuple[Response, int]:
    """
    GET /api/matches/awaiting-result?from=0&to=20
    Returns accepted matches where current user manages team1 or team2.
    Administrator sees all.
    """
    resolved      = account.resolved_role
    offset, limit = _parse_pagination(request.args)

    base = MatchProposal.query.filter_by(status_id=MatchStatus.ACCEPTED)

    if not isinstance(resolved, Administrator):
        managed_ids = _team_ids_managed_by(resolved)
        if not managed_ids:
            return jsonify({"total": 0, "from": offset, "to": offset, "matches": []}), 200
        base = base.filter(
            db.or_(
                MatchProposal.team1_id.in_(managed_ids),
                MatchProposal.team2_id.in_(managed_ids),
            )
        )

    total = base.count()
    items = base.order_by(MatchProposal.id.desc()).offset(offset).limit(limit).all()

    return jsonify({
        "total":   total,
        "from":    offset,
        "to":      offset + len(items),
        "matches": [m.to_dict_full() for m in items],
    }), 200