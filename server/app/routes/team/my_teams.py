"""
Personal team views and join-request actions.

These routes back the "my teams", "my all teams", and join-request tabs in
the frontend dashboard and team management screens.
"""

from flask import Blueprint, request, jsonify, abort
from server.app.models.account import Account, Administrator
from server.app.models.club_player import ClubPlayer
from server.app.models.club_owner import ClubOwner
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.models.player import Player
from server.app.models.team import Team, TeamManager
from server.app.decorators.login_required import login_required
from server.extensions import db
from ._helpers import parse_pagination, resolve_target, get_team_or_404
from ._permissions import can_edit_managers_or_403, can_manage_join_request_or_403
from ...models.player import PlayerTeam
from ...models.team_club_join_request import TeamClubJoinRequest
from ...models.team_join_request import TeamJoinRequest
from ...utils.promote import promote_to_player

my_teams_bp = Blueprint("team_my", __name__)


def _next_ladder_rank(ladder_id: int) -> int:
    return (
        db.session.query(db.func.coalesce(db.func.max(LadderTeam.rank), 0))
        .filter_by(ladder_id=ladder_id)
        .scalar()
    ) + 1


def _ensure_club_member(account: Account, club_id: int) -> None:
    if account.player is None and Player.query.get(account.id) is None:
        db.session.add(Player(id=account.id))
        db.session.flush()

    if ClubPlayer.query.filter_by(club_id=club_id, player_id=account.id).first() is None:
        db.session.add(ClubPlayer(club_id=club_id, player_id=account.id))


def _attach_team_people_to_club(team: Team, club_id: int) -> None:
    accounts_by_id: dict[int, Account] = {}
    for manager in team.managers:
        if manager.account is not None:
            accounts_by_id[manager.account.id] = manager.account
    for player in team.players:
        if player.account is not None:
            accounts_by_id[player.account.id] = player.account

    for account in accounts_by_id.values():
        _ensure_club_member(account, club_id)


def _add_team_to_ladder_if_needed(team: Team, ladder: Ladder | None) -> LadderTeam | None:
    if ladder is None:
        return None

    existing = LadderTeam.query.filter_by(ladder_id=ladder.id, team_id=team.id).first()
    if existing:
        return existing

    ladder_team = LadderTeam(
        ladder_id=ladder.id,
        team_id=team.id,
        rank=_next_ladder_rank(ladder.id),
        rating=1000,
        matches_played=0,
    )
    db.session.add(ladder_team)
    return ladder_team


@my_teams_bp.route("/my", methods=["GET"])
@login_required
def get_my_teams(account: Account):
    """
    Return the teams managed by the current account.

    Preconditions:
        - `account` must exist and be active in the database.

    Args:
        account (Account): The account for which to retrieve the managed teams.

    Returns:
        a JSON response containing a paginated list of teams managed by the current account, 
        along with the total count and pagination metadata.
    """
    offset, limit, sort_col = parse_pagination(request.args)

    resolved = account.resolved_role

    if isinstance(resolved, Administrator):
        base_query = Team.query

    elif isinstance(resolved, ClubOwner):
        club_ids    = [c.id for c in resolved.clubs]
        managed_ids = [t.id for t in resolved.team_manager.teams]
        base_query  = Team.query.filter(
            db.or_(Team.club_id.in_(club_ids), Team.id.in_(managed_ids))
        )

    elif isinstance(resolved, TeamManager):
        managed_ids = [t.id for t in resolved.teams]
        base_query  = Team.query.filter(Team.id.in_(managed_ids))

    else:
        return jsonify({
            "total": 0,
            "from": offset,
            "to": offset,
            "teams": []
        }), 200

    total = base_query.count()
    teams = base_query.order_by(sort_col).offset(offset).limit(limit).all()

    return jsonify({
        "total": total,
        "from": offset,
        "to": offset + len(teams),
        "teams": [t.to_dict() for t in teams]
    }), 200


@my_teams_bp.route("/my-all", methods=["GET"])
@login_required
def get_my_all_teams(account: Account):
    """
    Return every team where the account is involved.

    Preconditions:
        - `account` must exist and be active in the database.

    Args:
        account (Account): The account for which to retrieve the involved teams.

    Returns:
        a JSON response containing a paginated list of teams where the account is involved, 
        along with the total count and pagination metadata.
    """
    offset, limit, sort_col = parse_pagination(request.args)

    resolved = account.resolved_role

    if isinstance(resolved, Administrator):
        total = Team.query.count()
        teams = Team.query.order_by(sort_col).offset(offset).limit(limit).all()
        return jsonify({
            "total": total,
            "from": offset,
            "to": offset + len(teams),
            "teams": [t.to_dict() for t in teams]
        }), 200

    team_ids: set[int] = set()

    if isinstance(resolved, ClubOwner):
        for club in resolved.clubs:
            for t in club.teams:
                team_ids.add(t.id)
        if resolved.team_manager:
            for t in resolved.team_manager.teams:
                team_ids.add(t.id)
    elif isinstance(resolved, TeamManager):
        for t in resolved.teams:
            team_ids.add(t.id)

    if account.player is not None:
        for t in account.player.teams:
            team_ids.add(t.id)

    if not team_ids:
        return jsonify({
            "total": 0,
            "from": offset,
            "to": offset,
            "teams": []
        }), 200

    base_query = Team.query.filter(Team.id.in_(team_ids))
    total = base_query.count()
    teams = base_query.order_by(sort_col).offset(offset).limit(limit).all()

    return jsonify({
        "total": total,
        "from": offset,
        "to": offset + len(teams),
        "teams": [t.to_dict() for t in teams]
    }), 200

@my_teams_bp.route("/<int:team_id>/players/join-requests/<int:request_id>/accept", methods=["POST"])
@login_required
def accept_player_join_request(account: Account, team_id: int, request_id: int):
    """
    Accept a player join request.

    Preconditions:
        - `account` must exist and be active in the database.
        - `team_id` must exist and be active in the database.
        - `request_id` must exist, be active in the database, and be associated with the specified team.

    Args:
        account (Account): The account accepting the join request.
        team_id (int): The ID of the team for which to accept the join request.
        request_id (int): The ID of the join request to accept.

    Returns:
        a JSON response containing a success message and the accepted join request, along with a 200 status code.

    Postconditions:
        - The join request status is updated to "accepted" in the database.
        - The user associated with the join request is promoted to a player role if not already a player.
        - An association between the player and the team is created in the database.
    """
    team = get_team_or_404(team_id)
    resolved = account.resolved_role

    join_request = db.session.query(TeamJoinRequest).filter(
        TeamJoinRequest.id == request_id,
        TeamJoinRequest.team_id == team_id,
        ).first()

    if not join_request:
        abort(404, description="Join request not found.")

    can_manage_join_request_or_403(resolved, join_request, team)

    if join_request.status != "pending":
        abort(409, description="Join request is not in pending status.")

    join_request.status = "accepted"
    db.session.flush()

    target = resolve_target(join_request.user_id)
    promote_to_player(target)

    assoc = PlayerTeam(player_id=target.player.id, team_id=team.id)
    db.session.add(assoc)
    db.session.commit()

    return jsonify({
        "message": "Player join request accepted successfully.",
        "request": join_request.serialize()
    }), 200


@my_teams_bp.route("/<int:team_id>/players/join-requests/<int:request_id>/reject", methods=["POST"])
@login_required
def reject_player_join_request(account: Account, team_id: int, request_id: int):
    """
    Reject a player join request.

    Preconditions:
        - `account` must exist and be active in the database.
        - `team_id` must exist and be active in the database.
        - `request_id` must exist, be active in the database, and be associated with the specified team.

    Args:
        account (Account): The account rejecting the join request.
        team_id (int): The ID of the team for which to reject the join request.
        request_id (int): The ID of the join request to reject.

    Returns:
        a JSON response containing a success message and the rejected join request, along with a 200 status code.

    Postconditions:
        - The join request status is updated to "rejected" in the database.
        - The user associated with the join request is not promoted to a player role.
        - No association between the player and the team is created in the database.
    """
    team = get_team_or_404(team_id)
    resolved = account.resolved_role

    join_request = db.session.query(TeamJoinRequest).filter(
        TeamJoinRequest.id == request_id,
        TeamJoinRequest.team_id == team_id,
        ).first()

    if not join_request:
        abort(404, description="Join request not found.")

    can_manage_join_request_or_403(resolved, join_request, team)

    if join_request.status != "pending":
        abort(409, description="Join request is not in pending status.")

    join_request.status = "rejected"
    db.session.commit()

    return jsonify({
        "message": "Player join request rejected successfully.",
        "request": join_request.serialize()
    }), 200

@my_teams_bp.route("/my-join-requests", methods=["GET"])
@login_required
def get_my_join_requests(account: Account):
    """
    Return the pending join requests made by the current account.

    Preconditions:
        - `account` must exist and be active in the database.

    Args:
        account (Account): The account for which to retrieve the pending join requests.

    Returns:
        a JSON response containing a list of pending join requests made by the current account, 
        along with the total count.
    """
    requests = (
        db.session.query(TeamJoinRequest)
        .filter(
            TeamJoinRequest.user_id == account.id,
            TeamJoinRequest.status == "pending",
            )
        .order_by(TeamJoinRequest.date.desc())
        .all()
    )

    return jsonify({
        "total": len(requests),
        "joinRequests": [r.serialize() for r in requests],
    }), 200


@my_teams_bp.route("/my-club-invitations", methods=["GET"])
@login_required
def get_my_team_club_invitations(account: Account):
    """
    Return pending invitations where a club wants one of the user's managed
    teams to join the club and optionally enter a ladder.
    """
    if isinstance(account.resolved_role, Administrator):
        invitations = (
            TeamClubJoinRequest.query
            .filter_by(status="pending")
            .order_by(TeamClubJoinRequest.date.desc())
            .all()
        )
    elif account.team_manager is not None:
        managed_team_ids = [team.id for team in account.team_manager.teams]
        if not managed_team_ids:
            invitations = []
        else:
            invitations = (
                TeamClubJoinRequest.query
                .filter(
                    TeamClubJoinRequest.status == "pending",
                    TeamClubJoinRequest.team_id.in_(managed_team_ids),
                )
                .order_by(TeamClubJoinRequest.date.desc())
                .all()
            )
    else:
        invitations = []

    return jsonify({
        "total": len(invitations),
        "clubInvitations": [invitation.serialize() for invitation in invitations],
    }), 200


@my_teams_bp.route("/<int:team_id>/club-invitations/<int:invitation_id>/accept", methods=["POST"])
@login_required
def accept_team_club_invitation(account: Account, team_id: int, invitation_id: int):
    """
    Accept a club invitation for an independent team.

    The team joins the club, all current managers and players become club
    members, and the team is added to the requested ladder when one was part
    of the invitation.
    """
    team = get_team_or_404(team_id)
    can_edit_managers_or_403(account.resolved_role, team)

    invitation = TeamClubJoinRequest.query.filter_by(
        id=invitation_id,
        team_id=team_id,
    ).first()
    if invitation is None:
        abort(404, description="Team club invitation not found.")

    ladder = db.session.get(Ladder, invitation.ladder_id) if invitation.ladder_id else None

    if invitation.status != "pending":
        if team.club_id == invitation.club_id:
            if ladder is not None and ladder.sport_type_id and team.sport_type_id != ladder.sport_type_id:
                team.sport_type_id = ladder.sport_type_id
            ladder_team = _add_team_to_ladder_if_needed(team, ladder)
            db.session.commit()
            return jsonify({
                "message": "Team joined the club successfully.",
                "invitation": invitation.serialize(),
                "team": team.to_dict(),
                "ladderTeam": {
                    "ladderId": ladder_team.ladder_id,
                    "teamId": ladder_team.team_id,
                    "rank": ladder_team.rank,
                    "rating": ladder_team.rating,
                    "matchesPlayed": ladder_team.matches_played,
                } if ladder_team is not None else None,
            }), 200
        abort(409, description="Team club invitation is not pending.")

    if team.club_id is not None and team.club_id != invitation.club_id:
        abort(409, description="Team already belongs to a different club.")

    if ladder is not None and ladder.club_id != invitation.club_id:
        abort(409, description="Invitation ladder does not belong to the invited club.")

    if ladder is not None:
        if ladder.sport_type_id and team.sport_type_id != ladder.sport_type_id:
            team.sport_type_id = ladder.sport_type_id

    team.club_id = invitation.club_id
    _attach_team_people_to_club(team, invitation.club_id)
    ladder_team = _add_team_to_ladder_if_needed(team, ladder)

    invitation.status = "accepted"
    db.session.commit()

    return jsonify({
        "message": "Team joined the club successfully.",
        "invitation": invitation.serialize(),
        "team": team.to_dict(),
        "ladderTeam": {
            "ladderId": ladder_team.ladder_id,
            "teamId": ladder_team.team_id,
            "rank": ladder_team.rank,
            "rating": ladder_team.rating,
            "matchesPlayed": ladder_team.matches_played,
        } if ladder_team is not None else None,
    }), 200


@my_teams_bp.route("/<int:team_id>/club-invitations/<int:invitation_id>/reject", methods=["POST"])
@login_required
def reject_team_club_invitation(account: Account, team_id: int, invitation_id: int):
    """Reject a pending club invitation for a managed team."""
    team = get_team_or_404(team_id)
    can_edit_managers_or_403(account.resolved_role, team)

    invitation = TeamClubJoinRequest.query.filter_by(
        id=invitation_id,
        team_id=team_id,
    ).first()
    if invitation is None:
        abort(404, description="Team club invitation not found.")
    if invitation.status != "pending":
        abort(409, description="Team club invitation is not pending.")

    invitation.status = "rejected"
    db.session.commit()

    return jsonify({
        "message": "Team club invitation rejected successfully.",
        "invitation": invitation.serialize(),
    }), 200
