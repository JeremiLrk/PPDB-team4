"""
Match proposal lifecycle routes.

This blueprint owns the main proposal workflow: create, accept, reject,
check, submit, and cancel match proposals.
"""

from flask import Blueprint, request, jsonify, abort, Response

from server.app.routes.matcher._helpers import (
    get_team_or_404,
    get_proposal_or_404,
)
from server.app.routes.matcher._permissions import (
    can_manage_match,
    can_manage_either_team,
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
    teams_share_players,
)
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.services.elo_service import apply_elo_for_match_result


matches_core_bp = Blueprint("matches_core", __name__)


# ===========================================================================
# POST /api/matches  — create proposal
# ===========================================================================

@matches_core_bp.route("", methods=["POST"])
@login_required
def create_match_proposal(account: Account) -> tuple[Response, int]:
    """
    Create a new match proposal.
    """
    resolved = account.resolved_role

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    team1_id = data.get("team1Id")
    team2_id = data.get("team2Id")
    sport_type_id = data.get("sportTypeId")
    ladder_id = data.get("ladderId")

    if not team1_id or not team2_id:
        abort(422, description="Fields 'team1Id' and 'team2Id' are required.")
    if team1_id == team2_id:
        abort(422, description="A team cannot play against itself.")

    team1 = get_team_or_404(team1_id)
    team2 = get_team_or_404(team2_id)

    ladder = None
    if ladder_id is not None:
        try:
            ladder_id = int(ladder_id)
        except (TypeError, ValueError):
            abort(422, description="Field 'ladderId' must be an integer.")

        ladder = Ladder.query.get(ladder_id)
        if not ladder:
            abort(404, description=f"Ladder {ladder_id} not found.")

        ladder_team_ids = {
            row.team_id
            for row in LadderTeam.query.filter(LadderTeam.ladder_id == ladder.id).all()
        }
        if team1.id not in ladder_team_ids or team2.id not in ladder_team_ids:
            abort(422, description="Both teams must be registered in the selected ladder.")

        if not sport_type_id:
            sport_type_id = ladder.sport_type_id

    if not sport_type_id:
        abort(422, description="Field 'sportTypeId' is required when no ladder sport is available.")

    try:
        sport_type_id = int(sport_type_id)
    except (TypeError, ValueError):
        abort(422, description="Field 'sportTypeId' must be an integer.")

    if ladder and ladder.sport_type_id and sport_type_id != int(ladder.sport_type_id):
        abort(422, description="Field 'sportTypeId' must match the selected ladder sport.")
    if team1.sport_type_id and sport_type_id != int(team1.sport_type_id):
        abort(422, description="Field 'sportTypeId' must match team1 sport type.")
    if team2.sport_type_id and sport_type_id != int(team2.sport_type_id):
        abort(422, description="Field 'sportTypeId' must match team2 sport type.")

    if not can_manage_either_team(resolved, team1, team2):
        abort(403, description="Forbidden: you do not have permission to create a match for these teams.")
    if teams_share_players(team1, team2):
        abort(422, description="A match proposal cannot include the same player on both teams.")

    ruleset_id    = data.get("rulesetId") or (ladder.ruleset_id if ladder else None)
    rule_snapshot = data.get("ruleSnapshot")  # NEW: optional JSONB snapshot of ruleset at proposal time
    location      = data.get("location", "").strip() or None
    venue_type_id = data.get("venueTypeId")

    proposal = MatchProposal(
        sport_type_id = sport_type_id,
        rule_snapshot = rule_snapshot,
        ruleset_id    = ruleset_id,
        ladder_id     = ladder_id,
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
    Accept a pending match proposal.
    """
    resolved = account.resolved_role
    proposal = get_proposal_or_404(match_id)

    if proposal.status_id != MatchStatus.PENDING:
        abort(409, description=f"Match is not pending (current status: {proposal.status.name}).")

    team2 = get_team_or_404(proposal.team2_id)
    if not can_manage_match(resolved, team2):
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
    Reject a pending match proposal.
    """
    resolved = account.resolved_role
    proposal = get_proposal_or_404(match_id)

    if proposal.status_id != MatchStatus.PENDING:
        abort(409, description=f"Match is not pending (current status: {proposal.status.name}).")

    team2 = get_team_or_404(proposal.team2_id)
    if not can_manage_match(resolved, team2):
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
    Validate a proposed match result without saving it.
    """
    resolved = account.resolved_role
    proposal = get_proposal_or_404(match_id)

    if proposal.status_id != MatchStatus.ACCEPTED:
        abort(409, description=f"Match is not in 'accepted' state (current: {proposal.status.name}).")

    team1 = get_team_or_404(proposal.team1_id)
    team2 = get_team_or_404(proposal.team2_id)

    if not (can_manage_either_team(resolved, team1, team2)):
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
    Save the final match result and apply Elo updates.
    """
    resolved = account.resolved_role
    proposal = MatchProposal.query.filter_by(id=match_id).with_for_update().first()
    if not proposal:
        abort(404, description="Match proposal not found.")

    team1 = get_team_or_404(proposal.team1_id)
    team2 = get_team_or_404(proposal.team2_id)
    if not (can_manage_either_team(resolved, team1, team2)):
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
    Cancel an accepted match proposal.
    """
    resolved = account.resolved_role
    proposal = get_proposal_or_404(match_id)

    if proposal.status_id != MatchStatus.ACCEPTED:
        abort(409, description=f"Only accepted matches can be cancelled (current: {proposal.status.name}).")

    team1 = get_team_or_404(proposal.team1_id)
    if not can_manage_match(resolved, team1):
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
