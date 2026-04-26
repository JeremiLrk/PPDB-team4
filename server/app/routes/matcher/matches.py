from flask import Blueprint, request, jsonify, abort, Response

from server.app.routes.matcher._helpers import (
    _get_team_or_404,
    _get_proposal_or_404,
)
from server.app.routes.matcher._permissions import (
    _can_manage_match,
    _can_manage_either_team,
)
from server.extensions import db
from server.app.decorators.login_required import login_required
from server.app.models.account import Account

from server.app.models.match import (
    MatchProposal,
    MatchAccepted,
    MatchRejected,
    MatchPlayed,
    MatchCancelled,
    MatchStatus,
)
from server.app.services.elo_service import apply_elo_for_match_result


matches_core_bp = Blueprint("matches_core", __name__)


# ===========================================================================
# POST /api/matches  — create proposal
# ===========================================================================

@matches_core_bp.route("", methods=["POST"])
@login_required
def create_match_proposal(account: Account) -> tuple[Response, int]:
    """
    POST /api/matches
    Body: { team1Id, team2Id, sportTypeId, rulesetId?, location?, venueTypeId? }

    Allowed for: Administrator, ClubOwner (with can_create_match), TeamManager of either team.
    """
    resolved = account.resolved_role

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    team1_id = data.get("team1Id")
    team2_id = data.get("team2Id")
    sport_type_id = data.get("sportTypeId")

    if not team1_id or not team2_id:
        abort(422, description="Fields 'team1Id' and 'team2Id' are required.")
    if not sport_type_id:
        abort(422, description="Field 'sportTypeId' is required.")
    if team1_id == team2_id:
        abort(422, description="A team cannot play against itself.")

    team1 = _get_team_or_404(team1_id)
    team2 = _get_team_or_404(team2_id)

    if not _can_manage_either_team(resolved, team1, team2):
        abort(403, description="Forbidden: you do not have permission to create a match for these teams.")

    ruleset_id    = data.get("rulesetId")
    rule_snapshot = data.get("ruleSnapshot")  # NEW: optional JSONB snapshot of ruleset at proposal time
    location      = data.get("location", "").strip() or None
    venue_type_id = data.get("venueTypeId")

    proposal = MatchProposal(
        sport_type_id = sport_type_id,
        rule_snapshot = rule_snapshot,
        ruleset_id    = ruleset_id,
        team1_id      = team1_id,
        team2_id      = team2_id,
        status_id     = MatchStatus.PENDING,
        location      = location,
        venue_type_id = venue_type_id,
    )
    db.session.add(proposal)
    db.session.commit()

    return jsonify({
        "message": "Match proposal created successfully.",
        "match":   proposal.to_dict(),
    }), 201


# ===========================================================================
# POST /api/matches/<id>/accept
# ===========================================================================

@matches_core_bp.route("/<int:match_id>/accept", methods=["POST"])
@login_required
def accept_match(account: Account, match_id: int) -> tuple[Response, int]:
    """
    POST /api/matches/<id>/accept
    Body (optional): { responseText? }

    Only managers of team2 (or Administrator) may accept.
    Match must be in 'pending' status.
    """
    resolved = account.resolved_role
    proposal = _get_proposal_or_404(match_id)

    if proposal.status_id != MatchStatus.PENDING:
        abort(409, description=f"Match is not pending (current status: {proposal.status.name}).")

    team2 = _get_team_or_404(proposal.team2_id)
    if not _can_manage_match(resolved, team2):
        abort(403, description="Forbidden: only managers of the challenged team may accept.")

    data          = request.get_json(silent=True) or {}
    response_text = data.get("responseText", "").strip() or None

    proposal.status_id = MatchStatus.ACCEPTED
    accepted = MatchAccepted(
        id                  = proposal.id,
        response_by_user_id = account.id,
        response_text       = response_text,
    )
    db.session.add(accepted)
    db.session.commit()

    return jsonify({
        "message": "Match accepted.",
        "match":   proposal.to_dict_full(),
    }), 200


# ===========================================================================
# POST /api/matches/<id>/reject
# ===========================================================================

@matches_core_bp.route("/<int:match_id>/reject", methods=["POST"])
@login_required
def reject_match(account: Account, match_id: int) -> tuple[Response, int]:
    """
    POST /api/matches/<id>/reject
    Body (optional): { responseText? }

    Only managers of team2 (or Administrator) may reject.
    Match must be in 'pending' status.
    """
    resolved = account.resolved_role
    proposal = _get_proposal_or_404(match_id)

    if proposal.status_id != MatchStatus.PENDING:
        abort(409, description=f"Match is not pending (current status: {proposal.status.name}).")

    team2 = _get_team_or_404(proposal.team2_id)
    if not _can_manage_match(resolved, team2):
        abort(403, description="Forbidden: only managers of the challenged team may reject.")

    data          = request.get_json(silent=True) or {}
    response_text = data.get("responseText", "").strip() or None

    proposal.status_id = MatchStatus.REJECTED
    rejected = MatchRejected(
        id                  = proposal.id,
        response_by_user_id = account.id,
        response_text       = response_text,
    )
    db.session.add(rejected)
    db.session.commit()

    return jsonify({
        "message": "Match rejected.",
        "match":   proposal.to_dict_full(),
    }), 200


# ===========================================================================
# POST /api/matches/<id>/result/check  — dry-run, warns if result exists
# ===========================================================================

@matches_core_bp.route("/<int:match_id>/result/check", methods=["POST"])
@login_required
def check_match_result(account: Account, match_id: int) -> tuple[Response, int]:
    """
    POST /api/matches/<id>/result/check
    Body: { scoreTeam1, scoreTeam2, rating? }

    Validates the payload and warns (HTTP 200 with warning flag) if a result
    already exists. Does NOT write to the database.

    Allowed for: managers of team1 or team2, Administrator.
    """
    resolved = account.resolved_role
    proposal = _get_proposal_or_404(match_id)

    if proposal.status_id != MatchStatus.ACCEPTED:
        abort(409, description=f"Match is not in 'accepted' state (current: {proposal.status.name}).")

    team1 = _get_team_or_404(proposal.team1_id)
    team2 = _get_team_or_404(proposal.team2_id)

    if not (_can_manage_either_team(resolved, team1, team2)):
        abort(403, description="Forbidden: you must manage one of the teams to submit a result.")

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    score_team1 = data.get("scoreTeam1")
    score_team2 = data.get("scoreTeam2")
    if score_team1 is None or score_team2 is None:
        abort(422, description="Fields 'scoreTeam1' and 'scoreTeam2' are required.")
    if not isinstance(score_team1, int) or not isinstance(score_team2, int):
        abort(422, description="Scores must be integers.")
    if score_team1 < 0 or score_team2 < 0:
        abort(422, description="Scores must be non-negative.")

    already_exists = proposal.played is not None

    return jsonify({
        "valid":         True,
        "alreadyExists": already_exists,
        "warning":       "A result for this match already exists. Use POST /result to overwrite." if already_exists else None,
        "existingResult": proposal.played.to_dict() if already_exists else None,
    }), 200


# ===========================================================================
# POST /api/matches/<id>/result  — save result (overwrites if exists)
# ===========================================================================

@matches_core_bp.route("/<int:match_id>/result", methods=["POST"])
@login_required
def submit_match_result(account: Account, match_id: int) -> tuple[Response, int]:
    """
    POST /api/matches/<id>/result
    Body: { scoreTeam1, scoreTeam2, rating? }

    Saves the result unconditionally (overwrites any previous entry).
    Sets status to 'played'.

    Allowed for: managers of team1 or team2, Administrator.
    """
    resolved = account.resolved_role
    proposal = MatchProposal.query.filter_by(id=match_id).with_for_update().first()
    if not proposal:
        abort(404, description="Match proposal not found.")

    team1 = _get_team_or_404(proposal.team1_id)
    team2 = _get_team_or_404(proposal.team2_id)
    if not (_can_manage_either_team(resolved, team1, team2)):
        abort(403, description="Forbidden: you must manage one of the teams to submit a result.")

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    score_team1 = data.get("scoreTeam1")
    score_team2 = data.get("scoreTeam2")
    if score_team1 is None or score_team2 is None:
        abort(422, description="Fields 'scoreTeam1' and 'scoreTeam2' are required.")
    if not isinstance(score_team1, int) or not isinstance(score_team2, int):
        abort(422, description="Scores must be integers.")
    if score_team1 < 0 or score_team2 < 0:
        abort(422, description="Scores must be non-negative.")

    rating = data.get("rating")
    if rating is not None and not isinstance(rating, int):
        abort(422, description="Field 'rating' must be an integer.")

    if proposal.status_id == MatchStatus.PLAYED:
        if not proposal.played:
            abort(409, description="Match is already played.")

        same_result = (
            proposal.played.score_team1 == score_team1
            and proposal.played.score_team2 == score_team2
            and proposal.played.rating == rating
        )
        if same_result:
            return jsonify({
                "message": "Result already recorded; treated as idempotent retry.",
                "match": proposal.to_dict_full(),
            }), 200

        abort(409, description="A different result is already recorded for this match.")

    if proposal.status_id != MatchStatus.ACCEPTED:
        abort(409, description=f"Match is not in 'accepted' state (current: {proposal.status.name}).")

    played = MatchPlayed(
        id=proposal.id,
        score_team1=score_team1,
        score_team2=score_team2,
        rating=rating,
    )
    db.session.add(played)

    apply_elo_for_match_result(
        team1_id=proposal.team1_id,
        team2_id=proposal.team2_id,
        score_team1=score_team1,
        score_team2=score_team2,
    )

    proposal.status_id = MatchStatus.PLAYED
    db.session.commit()

    return jsonify({
        "message": "Match result submitted successfully.",
        "match":   proposal.to_dict_full(),
    }), 200


# ===========================================================================
# POST /api/matches/<id>/cancel
# ===========================================================================

@matches_core_bp.route("/<int:match_id>/cancel", methods=["POST"])
@login_required
def cancel_match(account: Account, match_id: int) -> tuple[Response, int]:
    """
    POST /api/matches/<id>/cancel
    Body (optional): { reason? }

    Cancels an already-accepted match.
    Only the proposing side (team1 managers) or Administrator may cancel.
    This is distinct from rejection (which is done by team2 on a pending proposal).
    """
    resolved = account.resolved_role
    proposal = _get_proposal_or_404(match_id)

    if proposal.status_id != MatchStatus.ACCEPTED:
        abort(409, description=f"Only accepted matches can be cancelled (current: {proposal.status.name}).")

    team1 = _get_team_or_404(proposal.team1_id)
    if not _can_manage_match(resolved, team1):
        abort(403, description="Forbidden: only managers of the proposing team (team1) may cancel.")

    data   = request.get_json(silent=True) or {}
    reason = data.get("reason", "").strip() or None

    proposal.status_id = MatchStatus.CANCELLED
    cancelled = MatchCancelled(
        id     = proposal.id,
        reason = reason,
    )
    db.session.add(cancelled)
    db.session.commit()

    return jsonify({
        "message": "Match cancelled.",
        "match":   proposal.to_dict_full(),
    }), 200

