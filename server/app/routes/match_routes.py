from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from server.app.decorators.login_required import login_required
from server.app.models.account import Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.match import (
    MatchAccepted,
    MatchCancelled,
    MatchPlayed,
    MatchProposal,
    MatchRejected,
    MatchStatus,
)
from server.app.models.team import Team, TeamManager
from server.app.models.venue_type import VenueType
from server.app.services.weekly_match_proposal_service import (
    generate_weekly_match_proposals,
    next_week_start,
)
from server.app.services.elo_service import apply_elo_for_match_result
from server.extensions import db

match_proposals_bp = Blueprint("match_proposals", __name__, url_prefix="/api/matches")


def proposal_payload(proposal: MatchProposal):
    return {
        "id": proposal.id,
        "proposed_by_user_id": proposal.proposed_by_user_id,
        "sport_type_id": proposal.sport_type_id,
        "ruleset_id": proposal.ruleset_id,
        "team1_id": proposal.team1_id,
        "team2_id": proposal.team2_id,
        "status_id": proposal.status_id,
        "status": proposal.status.name if proposal.status else None,
        "week_start_date": proposal.week_start_date.isoformat() if proposal.week_start_date else None,
        "proposed_start_at": proposal.proposed_start_at.isoformat() + "Z" if proposal.proposed_start_at else None,
        "proposed_end_at": proposal.proposed_end_at.isoformat() + "Z" if proposal.proposed_end_at else None,
        "created_at": proposal.created_at.isoformat() + "Z" if proposal.created_at else None,
        "updated_at": proposal.updated_at.isoformat() + "Z" if proposal.updated_at else None,
        "venue_type_id": proposal.venue_type_id,
        "team1_name": proposal.team1.name if proposal.team1 else None,
        "team2_name": proposal.team2.name if proposal.team2 else None,
        "team1_club_id": proposal.team1.club_id if proposal.team1 else None,
        "team2_club_id": proposal.team2.club_id if proposal.team2 else None,
        "team1_club_city": proposal.team1.club.city if proposal.team1 and proposal.team1.club else None,
        "team2_club_city": proposal.team2.club.city if proposal.team2 and proposal.team2.club else None,
    }


def parse_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        return None


def parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def week_start_for(timestamp):
    return (timestamp - timedelta(days=timestamp.weekday())).date()


def resolve_status(name):
    if not name:
        return None
    return MatchStatus.query.filter(func.lower(MatchStatus.name) == name.lower()).first()


def resolve_managed_team_ids(account):
    resolved = account.resolved_role
    if isinstance(resolved, Administrator):
        return None

    managed_ids = set()
    if isinstance(resolved, ClubOwner):
        if resolved.team_manager:
            for team in resolved.team_manager.teams:
                managed_ids.add(team.id)
        for club in resolved.clubs:
            for team in club.teams:
                managed_ids.add(team.id)
        return managed_ids

    if isinstance(resolved, TeamManager):
        for team in resolved.teams:
            managed_ids.add(team.id)
        return managed_ids

    return set()


def resolve_visible_team_ids(account):
    managed_ids = resolve_managed_team_ids(account)
    if managed_ids is None:
        return None

    visible_ids = set(managed_ids)
    if account.player:
        for team in account.player.teams:
            visible_ids.add(team.id)

    return visible_ids


def can_manage_team(account, team):
    resolved = account.resolved_role
    if isinstance(resolved, Administrator):
        return True

    if isinstance(resolved, ClubOwner):
        manages_team = resolved.team_manager is not None and team in resolved.team_manager.teams
        owns_club = team.club is not None and team.club in resolved.clubs
        return owns_club or manages_team

    if isinstance(resolved, TeamManager):
        return team in resolved.teams

    return False


def is_player_on_team(account, team):
    return account.player is not None and team in account.player.teams


def can_respond_to_proposal(account, team1, team2):
    return (
        (team1 and (can_manage_team(account, team1) or is_player_on_team(account, team1)))
        or (team2 and (can_manage_team(account, team2) or is_player_on_team(account, team2)))
    )


@match_proposals_bp.post("/proposals")
@login_required
def create_match_proposal(account):
    data = request.get_json() or {}

    team1_id = data.get("team1_id")
    team2_id = data.get("team2_id")
    if not team1_id or not team2_id:
        return jsonify({"message": "team1_id and team2_id are required."}), 422

    try:
        team1_id = int(team1_id)
        team2_id = int(team2_id)
    except (TypeError, ValueError):
        return jsonify({"message": "team1_id and team2_id must be integers."}), 422

    if team1_id == team2_id:
        return jsonify({"message": "team1_id and team2_id must be different."}), 422

    team1 = db.session.get(Team, team1_id)
    team2 = db.session.get(Team, team2_id)
    if not team1 or not team2:
        return jsonify({"message": "One or both teams were not found."}), 404

    can_manage_either_team = can_manage_team(account, team1) or can_manage_team(account, team2)
    if not can_manage_either_team:
        return jsonify({"message": "Forbidden: you must manage at least one of the teams."}), 403

    proposed_start_at = parse_timestamp(data.get("proposed_start_at"))
    proposed_end_at = parse_timestamp(data.get("proposed_end_at"))
    if not proposed_start_at or not proposed_end_at:
        return jsonify({"message": "Invalid timestamp format for proposed_start_at/proposed_end_at."}), 422
    if proposed_start_at >= proposed_end_at:
        return jsonify({"message": "proposed_start_at must be before proposed_end_at."}), 422

    week_start_date = parse_date(data.get("week_start_date"))
    if not week_start_date:
        week_start_date = week_start_for(proposed_start_at)

    week_end_date = week_start_date + timedelta(days=6)
    if not (week_start_date <= proposed_start_at.date() <= week_end_date):
        return jsonify({"message": "proposed_start_at must be inside week_start_date week."}), 422

    sport_type_id = data.get("sport_type_id") or team1.sport_type_id
    if not sport_type_id:
        return jsonify({"message": "sport_type_id is required (or must exist on team1)."}), 422

    if team1.sport_type_id and int(sport_type_id) != int(team1.sport_type_id):
        return jsonify({"message": "sport_type_id must match team1 sport type."}), 422
    if team2.sport_type_id and int(sport_type_id) != int(team2.sport_type_id):
        return jsonify({"message": "sport_type_id must match team2 sport type."}), 422

    status_pending = resolve_status("pending")
    if not status_pending:
        return jsonify({"message": "Missing reference data: match status 'pending' was not seeded."}), 500

    ruleset_id = data.get("ruleset_id")
    venue_type_id = data.get("venue_type_id")

    if venue_type_id is not None:
        venue_exists = db.session.get(VenueType, venue_type_id)
        if not venue_exists:
            return jsonify({"message": "venue_type_id not found."}), 404

    # Canonical pair ordering for DB constraint: team1_id < team2_id.
    ordered_team1_id, ordered_team2_id = sorted((team1_id, team2_id))

    proposal = MatchProposal(
        proposed_by_user_id=account.id,
        sport_type_id=sport_type_id,
        ruleset_id=ruleset_id,
        team1_id=ordered_team1_id,
        team2_id=ordered_team2_id,
        status_id=status_pending.id,
        week_start_date=week_start_date,
        proposed_start_at=proposed_start_at,
        proposed_end_at=proposed_end_at,
        location=data.get("location"),
        venue_type_id=venue_type_id,
    )

    db.session.add(proposal)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "A proposal for this team pair and week already exists."}), 409

    return jsonify({"proposal": proposal_payload(proposal)}), 201


@match_proposals_bp.get("/proposals")
@login_required
def list_match_proposals(account):
    query = MatchProposal.query
    visible_team_ids = resolve_visible_team_ids(account)

    if visible_team_ids is not None:
        if not visible_team_ids:
            return jsonify({"proposals": [], "total": 0}), 200
        query = query.filter(
            or_(
                MatchProposal.team1_id.in_(visible_team_ids),
                MatchProposal.team2_id.in_(visible_team_ids),
            )
        )

    team_id = request.args.get("team_id")
    if team_id is not None:
        try:
            team_id = int(team_id)
        except ValueError:
            return jsonify({"message": "team_id must be an integer."}), 422
        query = query.filter(or_(MatchProposal.team1_id == team_id, MatchProposal.team2_id == team_id))

    week_start_date = request.args.get("week_start_date")
    if week_start_date:
        parsed_week = parse_date(week_start_date)
        if not parsed_week:
            return jsonify({"message": "week_start_date must be YYYY-MM-DD."}), 422
        query = query.filter(MatchProposal.week_start_date == parsed_week)

    proposals = (
        query.order_by(
            MatchProposal.week_start_date.asc(),
            MatchProposal.proposed_start_at.asc(),
            MatchProposal.id.asc(),
        ).all()
    )
    return jsonify({"proposals": [proposal_payload(proposal) for proposal in proposals], "total": len(proposals)}), 200


@match_proposals_bp.post("/proposals/generate-weekly")
@login_required
def generate_weekly_proposals(account):
    data = request.get_json() or {}

    week_start_date = parse_date(data.get("week_start_date")) if data.get("week_start_date") else next_week_start()
    if not week_start_date:
        return jsonify({"message": "week_start_date must be YYYY-MM-DD."}), 422

    ladder_id = data.get("ladder_id")
    if ladder_id is not None:
        try:
            ladder_id = int(ladder_id)
        except (TypeError, ValueError):
            return jsonify({"message": "ladder_id must be an integer."}), 422

    duration_minutes = data.get("duration_minutes", 60)
    try:
        duration_minutes = int(duration_minutes)
    except (TypeError, ValueError):
        return jsonify({"message": "duration_minutes must be an integer."}), 422
    if duration_minutes <= 0:
        return jsonify({"message": "duration_minutes must be greater than zero."}), 422

    managed_team_ids = resolve_managed_team_ids(account)
    result = generate_weekly_match_proposals(
        proposed_by_user_id=account.id,
        week_start_date=week_start_date,
        ladder_id=ladder_id,
        managed_team_ids=managed_team_ids,
        duration_minutes=duration_minutes,
        location=data.get("location"),
    )
    return jsonify(result), 201


@match_proposals_bp.patch("/proposals/<int:proposal_id>/status")
@login_required
def update_match_proposal_status(account, proposal_id):
    proposal = MatchProposal.query.filter_by(id=proposal_id).with_for_update().first()
    if not proposal:
        return jsonify({"message": "Match proposal not found."}), 404

    team1 = db.session.get(Team, proposal.team1_id)
    team2 = db.session.get(Team, proposal.team2_id)
    can_respond = can_respond_to_proposal(account, team1, team2)
    is_proposer = proposal.proposed_by_user_id == account.id
    is_admin = isinstance(account.resolved_role, Administrator)

    if not (can_respond or is_proposer or is_admin):
        return jsonify({"message": "Forbidden: cannot update this proposal."}), 403

    data = request.get_json() or {}
    status_name = data.get("status")
    if not status_name:
        return jsonify({"message": "status is required."}), 422

    next_status = resolve_status(status_name)
    if not next_status:
        return jsonify({"message": f"Unknown status '{status_name}'."}), 422

    current_status_name = proposal.status.name.lower() if proposal.status else None

    normalized_status = next_status.name.lower()
    if current_status_name == "played" and normalized_status != "played":
        return jsonify({"message": "Played matches are immutable and cannot change status."}), 409

    if normalized_status == "accepted":
        accepted = db.session.get(MatchAccepted, proposal.id)
        if not accepted:
            accepted = MatchAccepted(id=proposal.id)
            db.session.add(accepted)
        accepted.response_by_user_id = account.id
        accepted.response_text = data.get("response_text")
    elif normalized_status == "rejected":
        rejected = db.session.get(MatchRejected, proposal.id)
        if not rejected:
            rejected = MatchRejected(id=proposal.id)
            db.session.add(rejected)
        rejected.response_by_user_id = account.id
        rejected.response_text = data.get("response_text")
    elif normalized_status == "cancelled":
        cancelled = db.session.get(MatchCancelled, proposal.id)
        if not cancelled:
            cancelled = MatchCancelled(id=proposal.id)
            db.session.add(cancelled)
        cancelled.reason = data.get("reason")
    elif normalized_status == "played":
        if current_status_name == "played":
            existing_played = db.session.get(MatchPlayed, proposal.id)
            if not existing_played:
                return jsonify({"message": "Proposal is already in played status."}), 409

        score_team1 = data.get("score_team1")
        score_team2 = data.get("score_team2")
        if score_team1 is None or score_team2 is None:
            return jsonify({"message": "score_team1 and score_team2 are required for status 'played'."}), 422

        try:
            score_team1 = int(score_team1)
            score_team2 = int(score_team2)
        except ValueError:
            return jsonify({"message": "score_team1 and score_team2 must be integers."}), 422

        if score_team1 < 0 or score_team2 < 0:
            return jsonify({"message": "Scores must be >= 0."}), 422

        parsed_rating = None
        if data.get("rating") is not None:
            try:
                parsed_rating = int(data.get("rating"))
            except ValueError:
                return jsonify({"message": "rating must be an integer."}), 422

        existing_played = db.session.get(MatchPlayed, proposal.id)
        if existing_played:
            same_result = (
                existing_played.score_team1 == score_team1
                and existing_played.score_team2 == score_team2
                and existing_played.rating == parsed_rating
            )
            if same_result:
                proposal.status_id = next_status.id
                proposal.updated_at = datetime.utcnow()
                db.session.commit()
                return (
                    jsonify(
                        {
                            "proposal": proposal_payload(proposal),
                            "message": "Result already recorded; treated as idempotent retry.",
                        }
                    ),
                    200,
                )

            return jsonify({"message": "A different played result already exists for this proposal."}), 409

        played = MatchPlayed(
            id=proposal.id,
            score_team1=score_team1,
            score_team2=score_team2,
            rating=parsed_rating,
        )
        db.session.add(played)

        apply_elo_for_match_result(
            team1_id=proposal.team1_id,
            team2_id=proposal.team2_id,
            score_team1=score_team1,
            score_team2=score_team2,
        )

    proposal.status_id = next_status.id
    proposal.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"proposal": proposal_payload(proposal)}), 200
