"""
score.py — Score-submission routes for the matcher blueprint.

Endpoints
---------
POST /api/matches/<id>/score
    Submit a score for a match.  The caller's role (team1_side,
    team2_side, ladder_admin) is resolved automatically from their
    account permissions.  If both team sides agree (or a ladder_admin
    submits), the match is finalized automatically.

GET  /api/matches/<id>/score
    Return all score submissions and the current score_status for a match.

GET  /api/matches/disputed
    Return all matches currently in 'disputed' state that the caller
    is authorised to adjudicate.
"""

from flask import Blueprint, jsonify, request

from server.app.decorators.login_required import login_required
from server.app.models.match import (
    MatchProposal,
    get_disputed_matches_resolvable_by,
)
from server.app.services.match_score_service import (
    ScoreSubmissionError,
    submit_score,
)
from server.extensions import db

score_bp = Blueprint("score", __name__)


# ---------------------------------------------------------------------------
# POST /api/matches/<id>/score  — submit a score
# ---------------------------------------------------------------------------

@score_bp.post("/<int:match_id>/score")
@login_required
def post_score(account, match_id: int):
    """Submit a score for match *match_id*.

    Body (JSON)
    -----------
    score_team1 : int   required, >= 0
    score_team2 : int   required, >= 0

    The caller's SubmissionRole is resolved from their permissions:
      - ClubOwner/Admin whose club owns the ladder → 'ladder_admin'
        (only accepted when scores from both team sides disagree)
      - manager/owner of team1 → 'team1_side'
      - manager/owner of team2 → 'team2_side'

    Responses
    ---------
    201  Submission recorded; includes finalized=true when match was
         automatically closed.
    409  Submission already exists for this role, or match already finalized.
    403  Caller has no valid role for this match.
    422  Invalid payload.
    """
    proposal = MatchProposal.query.filter_by(id=match_id).with_for_update().first()
    if not proposal:
        return jsonify({"message": "Match not found."}), 404

    data = request.get_json() or {}

    try:
        score_team1 = int(data["score_team1"])
        score_team2 = int(data["score_team2"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"message": "score_team1 and score_team2 are required integers."}), 422

    try:
        submission, finalized = submit_score(proposal, account, score_team1, score_team2)
    except ScoreSubmissionError as exc:
        return jsonify({"message": str(exc)}), exc.status_code

    db.session.commit()

    return jsonify({
        "submission": submission.to_dict(),
        "scoreStatus": proposal.score_status,
        "finalized": finalized,
        "resolvedScore": proposal.get_resolved_score() if finalized else None,
    }), 201


# ---------------------------------------------------------------------------
# GET /api/matches/<id>/score  — retrieve submissions + status
# ---------------------------------------------------------------------------

@score_bp.get("/<int:match_id>/score")
@login_required
def get_score(account, match_id: int):
    """Return score submissions and score_status for *match_id*.

    Responses
    ---------
    200  {"scoreStatus": str, "submissions": [...], "resolvedScore": dict|null}
    403  Caller has no visibility into this match.
    404  Match not found.
    """
    proposal = MatchProposal.query.filter_by(id=match_id).first()
    if not proposal:
        return jsonify({"message": "Match not found."}), 404

    if not proposal.can_be_managed_by(account):
        return jsonify({"message": "Forbidden."}), 403

    return jsonify({
        "matchId":      proposal.id,
        "scoreStatus":  proposal.score_status,
        "submissions":  [s.to_dict() for s in proposal.score_submissions],
        "resolvedScore": proposal.get_resolved_score(),
    }), 200


# ---------------------------------------------------------------------------
# GET /api/matches/disputed  — list disputed matches the caller can resolve
# ---------------------------------------------------------------------------

@score_bp.get("/disputed")
@login_required
def list_disputed(account):
    """Return all disputed matches that *account* can adjudicate.

    Only matches where the caller passes can_adjudicate_score() are
    returned; an ordinary team manager will always receive an empty list.

    Responses
    ---------
    200  {"matches": [...], "total": int}
    """
    matches = get_disputed_matches_resolvable_by(account)
    return jsonify({
        "matches": [m.to_dict_full() for m in matches],
        "total": len(matches),
    }), 200