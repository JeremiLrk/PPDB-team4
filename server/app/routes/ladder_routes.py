from flask import Blueprint, jsonify, request

from server.app.decorators.login_required import login_required
from server.app.models.account import Administrator
from server.app.models.club_owner import ClubOwner, ClubOwnerClub
from server.app.models.ladder import Ladder, LadderRatingFunction
from server.app.models.ladder_team import LadderTeam
from server.app.models.match_rule import MatchRuleSet
from server.app.models.team import Team
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

    return jsonify({"teams": [team.to_dict() for team in teams]}), 200


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

    existing = LadderTeam.query.filter_by(ladder_id=ladder_id, team_id=team_id).first()
    if existing:
        return jsonify({"message": "Team is already in this ladder."}), 400

    if team.club_id is not None and team.club_id != club_id:
        return jsonify({"message": "Team belongs to a different club."}), 400

    if team.club_id is None:
        team.club_id = club_id

    next_rank = (
        db.session.query(db.func.coalesce(db.func.max(LadderTeam.rank), 0))
        .filter_by(ladder_id=ladder_id)
        .scalar()
    ) + 1

    ladder_team = LadderTeam(
        ladder_id=ladder_id,
        team_id=team_id,
        rank=next_rank,
        rating=1000,
        matches_played=0,
    )
    db.session.add(ladder_team)
    db.session.commit()

    return jsonify({
        "message": f"Successfully added {team.name} to {ladder.name}.",
        "team": team.to_dict(),
        "ladderTeam": {
            "ladderId": ladder_team.ladder_id,
            "teamId": ladder_team.team_id,
            "rank": ladder_team.rank,
            "rating": ladder_team.rating,
            "matchesPlayed": ladder_team.matches_played,
        },
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
