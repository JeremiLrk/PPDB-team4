from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from server.app.decorators.login_required import login_required
from server.app.models.account import Account, Administrator
from server.app.models.club_owner import ClubOwner, ClubOwnerClub
from server.app.models.ladder import Ladder, LadderRatingFunction
from server.app.models.ladder_team import LadderTeam
from server.app.models.match import cancel_unplayed_matches_for_team
from server.app.models.match_rule import MatchRuleSet
from server.app.models.team import Team
from server.app.models.team_club_join_request import TeamClubJoinRequest
from server.app.models.sport_type import SportType
from server.app.services.ladder_service import (
    get_all_players_ladder,
    get_ladder_player_achievement_stats,
)
from server.extensions import db

ladder_bp = Blueprint("ladder", __name__, url_prefix="/api")


def _can_manage_club(account, club_id: int) -> bool:
    """Helper function to check if the given account has management permissions for the specified club."""
    with db.session.no_autoflush:
        if Administrator.query.filter_by(id=account.id).first() is not None:
            return True
        if ClubOwner.query.filter_by(id=account.id).first() is not None:
            return ClubOwnerClub.query.filter_by(
                club_owner_id=account.id,
                club_id=club_id,
            ).first() is not None
    return False


def _next_ladder_rank(ladder_id: int) -> int:
    return (
        db.session.query(db.func.coalesce(db.func.max(LadderTeam.rank), 0))
        .filter_by(ladder_id=ladder_id)
        .scalar()
    ) + 1


def _recompute_ladder_ranks(ladder_id: int) -> None:
    rows = (
        LadderTeam.query
        .filter_by(ladder_id=ladder_id)
        .order_by(LadderTeam.rank.asc().nullslast(), LadderTeam.rating.desc(), LadderTeam.team_id.asc())
        .all()
    )
    for rank, row in enumerate(rows, start=1):
        row.rank = rank


def _serialize_account_name(account: Account | None) -> dict | None:
    if account is None:
        return None
    name = " ".join(part for part in [account.first_name, account.last_name] if part).strip()
    return {
        "id": account.id,
        "name": name or account.email,
    }


def _pending_team_club_invitation(club_id: int, team_id: int) -> TeamClubJoinRequest | None:
    return TeamClubJoinRequest.query.filter_by(
        club_id=club_id,
        team_id=team_id,
        status="pending",
    ).first()


def _serialize_ladder_candidate(team: Team, club_id: int) -> dict:
    payload = team.to_dict()
    ladder_rows = LadderTeam.query.filter_by(team_id=team.id).all()
    pending_invitation = _pending_team_club_invitation(club_id, team.id)

    managers = [
        item
        for item in (_serialize_account_name(manager.account) for manager in team.managers)
        if item is not None
    ]
    players = [
        item
        for item in (_serialize_account_name(player.account) for player in team.players)
        if item is not None
    ]

    payload.update({
        "membershipStatus": "club" if team.club_id == club_id else "independent",
        "ladderIds": [row.ladder_id for row in ladder_rows],
        "pendingClubInvitation": pending_invitation.serialize() if pending_invitation else None,
        "managers": managers,
        "players": players,
        "managerCount": len(managers),
        "playerCount": len(players),
        "canAddDirectly": team.club_id == club_id,
        "requiresInvite": team.club_id is None,
    })
    return payload


def _create_or_refresh_team_club_invitation(
    *,
    account: Account,
    club_id: int,
    team: Team,
    ladder: Ladder,
) -> TeamClubJoinRequest:
    if not team.managers:
        return None

    invitation = _pending_team_club_invitation(club_id, team.id)
    if invitation is None:
        invitation = TeamClubJoinRequest(
            club_id=club_id,
            team_id=team.id,
            ladder_id=ladder.id,
            requested_by=account.id,
            date=datetime.now(timezone.utc),
            status="pending",
        )
        db.session.add(invitation)
    else:
        invitation.ladder_id = ladder.id
        invitation.requested_by = account.id
        invitation.date = datetime.now(timezone.utc)

    return invitation


def _ladder_max_players(ladder: Ladder) -> int | None:
    """Return the maximum roster size the ladder expects, if known."""
    if ladder.rule_set and ladder.rule_set.game_format == "singles":
        return 1
    if ladder.rule_set and ladder.rule_set.game_format == "doubles":
        return 2

    if ladder.sport_type_id is None:
        return None

    sport_type = db.session.get(SportType, ladder.sport_type_id)
    if sport_type is None:
        return None
    return sport_type.maximum_number_of_players_per_team


@ladder_bp.get("/clubs/<int:club_id>/eligible-teams")
@login_required
def get_eligible_teams(account, club_id: int):
    """Endpoint to retrieve teams that are eligible to be added to a ladder within the specified club."""
    if not _can_manage_club(account, club_id):
        return jsonify({"message": "Forbidden."}), 403

    teams = (
        Team.query.filter(
            (Team.club_id == club_id) | (Team.club_id.is_(None))
        )
        .order_by(Team.name.asc())
        .all()
    )

    return jsonify({
        "teams": [_serialize_ladder_candidate(team, club_id) for team in teams],
    }), 200


@ladder_bp.get("/clubs/<int:club_id>/ladders/<int:ladder_id>/players")
def get_players(club_id, ladder_id):
    """
    Retrieves the list of players in a specific ladder.

    Args:
        club_id (int): The ID of the club to which the ladder belongs.
        ladder_id (int): The ID of the ladder for which to retrieve players.

    Returns:
        list: A list of dictionaries containing player information.
    """
    rows = get_all_players_ladder(ladder_id)
    achievement_stats = get_ladder_player_achievement_stats(ladder_id)
    return [
        {
            "id": team.id,
            "name": team.name,
            "rating": ladder_team.rating,
            "wins": achievement_stats.get(team.id, {}).get("wins", 0),
            "win_streak": achievement_stats.get(team.id, {}).get("win_streak", 0),
            "best_win_streak": achievement_stats.get(team.id, {}).get("best_win_streak", 0),
            "win_rate": (
                achievement_stats.get(team.id, {}).get("wins", 0)
                / achievement_stats.get(team.id, {}).get("matches_played", 0)
                if achievement_stats.get(team.id, {}).get("matches_played", 0)
                else 0.0
            ),
        }
        for team, ladder_team in rows
    ]


@ladder_bp.post("/clubs/<int:club_id>/ladders/<int:ladder_id>/teams/<int:team_id>")
@login_required
def add_team_to_ladder(account, club_id: int, ladder_id: int, team_id: int):
    """
    Adds a team to a specific ladder.

    Preconditions:
        - The user must have management permissions for the specified club.

    Args:
        account (Account): The account of the currently authenticated user.
        club_id (int): The unique identifier of the club to which the ladder belongs.
        ladder_id (int): The unique identifier of the ladder to which the team will be added.
        team_id (int): The unique identifier of the team to be added to the ladder.

    Returns:
        dict: A dictionary containing a success message, the added team's information, and the ladder team details.

    Postconditions:
        - The specified team is added to the ladder with an initial rating and rank.
    """
    if not _can_manage_club(account, club_id):
        return jsonify({"message": "Forbidden."}), 403

    ladder = db.session.get(Ladder, ladder_id)
    if not ladder or ladder.club_id != club_id:
        return jsonify({"message": "Ladder not found."}), 404

    team = db.session.get(Team, team_id)
    if not team:
        return jsonify({"message": "Team not found."}), 404

    if team.club_id is not None and team.club_id != club_id:
        return jsonify({"message": "Team belongs to a different club."}), 400

    data = request.get_json(silent=True) or {}

    max_players = _ladder_max_players(ladder)
    team_player_count = len(team.players)
    ladder_sport_name = None
    if ladder.sport_type_id:
        ladder_sport = db.session.get(SportType, ladder.sport_type_id)
        ladder_sport_name = ladder_sport.name if ladder_sport else None

    team_sport_name = team.sport_type.name if team.sport_type else None
    sport_mismatch = bool(
        ladder.sport_type_id
        and team.sport_type_id
        and ladder.sport_type_id != team.sport_type_id
    )
    if sport_mismatch and data.get("confirmSportMismatch") is not True:
        return jsonify({
            "message": (
                f"{team.name} is {team_sport_name or 'unknown'}, but {ladder.name} expects {ladder_sport_name or 'another'}."
                f" Accepting will change the team's sport type to {ladder_sport_name or 'the ladder sport'}."
            ),
            "warning": "sport_mismatch",
            "requireConfirm": True,
            "teamSportName": team_sport_name,
            "ladderSportName": ladder_sport_name,
            "team": team.to_dict(),
            "ladder": {
                "id": ladder.id,
                "name": ladder.name,
            },
        }), 202

    if (
        max_players is not None
        and team_player_count > max_players
        and data.get("confirmOversizedTeam") is not True
    ):
        return jsonify({
            "message": f"{team.name} has {team_player_count} players, but {ladder.name} expects teams of at most {max_players}.",
            "warning": "oversized_team",
            "requireConfirm": True,
            "maxPlayers": max_players,
            "teamPlayerCount": team_player_count,
            "team": team.to_dict(),
            "ladder": {
                "id": ladder.id,
                "name": ladder.name,
            },
        }), 202

    if team.club_id is None:
        invitation = _create_or_refresh_team_club_invitation(
            account=account,
            club_id=club_id,
            team=team,
            ladder=ladder,
        )
        if invitation is None:
            return jsonify({
                "message": "Independent teams need a team manager before they can be invited to a club ladder.",
            }), 400
        db.session.commit()
        return jsonify({
            "message": f"Invitation sent to {team.name}. A team manager must accept before the team joins {ladder.name}.",
            "action": "invitation_sent",
            "team": _serialize_ladder_candidate(team, club_id),
            "invitation": invitation.serialize(),
        }), 202

    existing = LadderTeam.query.filter_by(ladder_id=ladder_id, team_id=team_id).first()
    if existing:
        return jsonify({"message": "Team is already in this ladder."}), 400

    if ladder.sport_type_id and team.sport_type_id != ladder.sport_type_id:
        team.sport_type_id = ladder.sport_type_id

    ladder_team = LadderTeam(
        ladder_id=ladder_id,
        team_id=team_id,
        rank=_next_ladder_rank(ladder_id),
        rating=1000,
        matches_played=0,
    )
    db.session.add(ladder_team)
    db.session.commit()

    return jsonify({
        "message": f"Successfully added {team.name} to {ladder.name}.",
        "action": "added",
        "team": team.to_dict(),
        "ladderTeam": {
            "ladderId": ladder_team.ladder_id,
            "teamId": ladder_team.team_id,
            "rank": ladder_team.rank,
            "rating": ladder_team.rating,
            "matchesPlayed": ladder_team.matches_played,
        },
    }), 200


@ladder_bp.delete("/clubs/<int:club_id>/ladders/<int:ladder_id>/teams/<int:team_id>")
@login_required
def remove_team_from_ladder(account, club_id: int, ladder_id: int, team_id: int):
    """Remove one team from a club ladder and cancel its unplayed ladder matches."""
    if not _can_manage_club(account, club_id):
        return jsonify({"message": "Forbidden."}), 403

    ladder = db.session.get(Ladder, ladder_id)
    if not ladder or ladder.club_id != club_id:
        return jsonify({"message": "Ladder not found."}), 404

    ladder_team = LadderTeam.query.filter_by(ladder_id=ladder_id, team_id=team_id).first()
    if not ladder_team:
        return jsonify({"message": "Team is not in this ladder."}), 404

    cancelled = cancel_unplayed_matches_for_team(
        team_id=team_id,
        ladder_ids=[ladder_id],
        reason="Team was removed from ladder.",
    )
    db.session.delete(ladder_team)
    db.session.flush()
    _recompute_ladder_ranks(ladder_id)
    db.session.commit()

    return jsonify({
        "message": "Team removed from ladder.",
        "teamId": team_id,
        "ladderId": ladder_id,
        "cancelledMatches": len(cancelled),
    }), 200


@ladder_bp.delete("/clubs/<int:club_id>/ladders/<int:ladder_id>")
@login_required
def delete_ladder(account, club_id: int, ladder_id: int):
    """Delete a club ladder."""
    if not _can_manage_club(account, club_id):
        return jsonify({"message": "Forbidden."}), 403

    ladder = db.session.get(Ladder, ladder_id)
    if not ladder or ladder.club_id != club_id:
        return jsonify({"message": "Ladder not found."}), 404

    team_count = LadderTeam.query.filter_by(ladder_id=ladder_id).count()
    db.session.delete(ladder)
    db.session.commit()

    return jsonify({
        "message": "Ladder deleted.",
        "ladderId": ladder_id,
        "removedTeams": team_count,
    }), 200


@ladder_bp.get("/clubs/<int:club_id>/ladders/<int:ladder_id>")
def get_ladder_rows(club_id, ladder_id):
    # Backward-compatible contract: this endpoint returns ladder rows.
    rows = get_all_players_ladder(ladder_id)
    return [
        {
            "id": team.id,
            "name": team.name,
            "rating": ladder_team.rating,
        }
        for team, ladder_team in rows
    ]


@ladder_bp.get("/clubs/<int:club_id>/ladders/<int:ladder_id>/details")
def get_ladder_details(club_id, ladder_id):
    """Retrieves detailed information about a specific ladder, including its associated sport type, ruleset, and rating function."""
    result = (
        db.session.query(Ladder, SportType.name, MatchRuleSet, LadderRatingFunction.name)
        .outerjoin(SportType, Ladder.sport_type_id == SportType.id)
        .outerjoin(MatchRuleSet, Ladder.ruleset_id == MatchRuleSet.id)
        .outerjoin(LadderRatingFunction, Ladder.ladder_rating_function_id == LadderRatingFunction.id)
        .filter(Ladder.id == ladder_id, Ladder.club_id == club_id)
        .first()
    )

    if not result:
        return jsonify({"message": "Ladder not found"}), 404

    ladder, sport_name, rule_set, rating_func_name = result

    return jsonify(
        {
            "id": ladder.id,
            "name": ladder.name,
            "description": ladder.description,
            "sport_type": sport_name,
            "ruleset": rule_set.to_dict() if rule_set else None,
            "rating_function": rating_func_name,
        }
    )
