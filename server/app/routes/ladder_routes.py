from flask import Blueprint, jsonify, request
from server.app.services.auth_service import verify_user
from server.app.models.ladder import Ladder, LadderRatingFunction
from server.app.models.match_rule import MatchRuleSet
from server.app.models.sport_type import SportType
from server.app.services.ladder_service import get_all_players_ladder
from server.extensions import db
from sqlalchemy import or_
from server.app.models.team import Team
from server.app.models.club_owner import ClubOwner, ClubOwnerClub
from server.app.models.club import Club
from server.app.models.ladder_team import LadderTeam 

ladder_bp = Blueprint("ladder", __name__, url_prefix="/api")


@ladder_bp.get("/clubs/<int:club_id>/ladders/<int:ladder_id>/players")
def get_players(club_id, ladder_id):
    rows = get_all_players_ladder(ladder_id)
    return [
        {
            "id": team.id,
            "name": team.name,
            "rating": ladder_team.rating,
        }
        for team, ladder_team in rows
    ]

@ladder_bp.post("/clubs/<int:club_id>/ladders/<int:ladder_id>/teams/<int:team_id>")
def add_team_to_ladder(club_id, ladder_id, team_id):
    token = request.cookies.get("access_token")
    account = verify_user(token)
    if not account:
        return jsonify({"message": "Unauthorized"}), 401

    # 2. PERMISSION CHECK
    clubowner = ClubOwner.query.filter_by(id=account.id).first()
    if not clubowner:
        return jsonify({"message": "Unauthorized"}), 401
    
    owner_check = ClubOwnerClub.query.filter_by(
        club_owner_id=clubowner.id, 
        club_id=club_id
    ).first()
    
    if not owner_check:
        return jsonify({"message": "Forbidden: You do not own this club"}), 403

    # 3. DATA VALIDATION
    team = Team.query.get(team_id)
    ladder = Ladder.query.get(ladder_id)
    
    if not team:
        return jsonify({"message": "Team not found"}), 404
    if not ladder:
        return jsonify({"message": "Ladder not found"}), 404

    # 4. LOGIC: Check if team belongs to another club
    # If team.club_id exists and isn't this club, block it
    if team.club_id is not None and team.club_id != club_id:
        return jsonify({"message": "Team belongs to a different club"}), 400

    # 5. LOGIC: Check if team is already in this specific ladder
    existing_entry = LadderTeam.query.filter_by(
        ladder_id=ladder_id, 
        team_id=team_id
    ).first()
    
    if existing_entry:
        return jsonify({"message": "Team is already in this ladder"}), 400

    try:
        # 6. ACTION: Affiliate team with club if they were "Free Agents"
        if team.club_id is None:
            team.club_id = club_id

        # 7. ACTION: Add to junction table
        # We calculate the next rank by counting current teams in ladder + 1
        current_count = LadderTeam.query.filter_by(ladder_id=ladder_id).count()
        
        new_entry = LadderTeam(
            ladder_id=ladder_id,
            team_id=team_id,
            rank=current_count + 1,
            rating=1000, # Default from your model
            matches_played=0
        )
        
        db.session.add(new_entry)
        db.session.commit()

        return jsonify({
            "message": f"Successfully added {team.name} to {ladder.name}",
            "team": team.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Server error: {str(e)}"}), 500

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
