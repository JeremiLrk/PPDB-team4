from flask import Blueprint, jsonify
from flask import request
from server.app.models import db
from server.app.models.club import Club
from server.app.models.user import User
from server.app.models.club_owner import ClubOwner
from server.app.models.club_owner_club import ClubOwnerClub
from server.app.models.club_player import ClubPlayer
from server.app.models.ladder import Ladder
from server.app.routes.dashboard_routes import _get_current_user_id_from_cookie

clubs_bp = Blueprint("clubs", __name__, url_prefix="/api")

@clubs_bp.get("/clubs")
def list_clubs():
    db_clubs = Club.query.order_by(Club.name.asc()).all()
    clubs = [{"id": club.id, "name": club.name, "description": club.description, "sport": club.sport, "city": club.city} for club in db_clubs]
    return jsonify({"clubs": clubs}), 200


@clubs_bp.get("/clubs/<int:club_id>")
def get_club(club_id: int):
    club = Club.query.filter_by(id=club_id).first()
    if not club:
        return jsonify({"message": "Club not found"}), 404

    return jsonify({"club": {"id": club.id, "name": club.name, "description": club.description, "sport": club.sport, "city": club.city}}), 200

@clubs_bp.put("/clubs/<int:club_id>")
def update_club(club_id: int):
    data = request.get_json() or {}

    user_id = _get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401
    
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404
    
    clubowner = ClubOwner.query.filter_by(id=user_id).first()
    if not clubowner:
        return jsonify({"message": "Unauthorized"}), 401
    
    owner_check = ClubOwnerClub.query.filter_by(club_owner_id=clubowner.id, club_id=club_id).first()
    if not owner_check:
        return jsonify({"message": "Forbidden"}), 403

    club.name = data.get("name", club.name)
    club.description = data.get("description", club.description)
    club.city = data.get("city", club.city)
    club.sport = data.get("sport", club.sport)

    db.session.commit()

    return jsonify({"message": "Club updated successfully"}), 200

@clubs_bp.get("/clubs/<int:club_id>/members")
def get_club_members(club_id: int):
    user_id = _get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404

    # Subquery: get all owner user_ids for this club
    owner_user_ids = (
        db.session.query(ClubOwner.id)
        .join(ClubOwnerClub, ClubOwnerClub.club_owner_id == ClubOwner.id)
        .filter(ClubOwnerClub.club_id == club_id)
        .subquery()
    )

    # Main query: members excluding owners
    members = (
        db.session.query(User)
        .join(ClubPlayer, ClubPlayer.player_id == User.id)
        .filter(ClubPlayer.club_id == club_id)
        .filter(~User.id.in_(owner_user_ids))
        .all()
    )

    result = [
        {
            "id": user.id,
            "email": user.email,
        }
        for user in members
    ]

    return jsonify({"members": result}), 200

@clubs_bp.delete("/clubs/<int:club_id>/members/<int:user_id>")
def remove_member(club_id: int, user_id: int):
    current_user_id = _get_current_user_id_from_cookie()
    if not current_user_id:
        return jsonify({"message": "Unauthorized"}), 401

    # Check club exists
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404

    # Check current user is an owner of this club
    club_owner = ClubOwner.query.filter_by(id=current_user_id).first()
    if not club_owner:
        return jsonify({"message": "Unauthorized"}), 401

    owner_check = ClubOwnerClub.query.filter_by(
        club_owner_id=club_owner.id,
        club_id=club_id
    ).first()

    if not owner_check:
        return jsonify({"message": "Forbidden"}), 403

    is_owner = ClubOwnerClub.query.filter_by(
        club_owner_id=user_id,
        club_id=club_id
    ).first()

    if is_owner:
        return jsonify({"message": "Cannot remove a club owner"}), 403

    # Remove member from ClubPlayer table
    membership = ClubPlayer.query.filter_by(
        club_id=club_id,
        player_id=user_id
    ).first()

    if not membership:
        return jsonify({"message": "Member not found"}), 404

    db.session.delete(membership)
    db.session.commit()

    return jsonify({"message": "Member removed successfully"}), 200

@clubs_bp.post("/clubs/<int:club_id>/ladders")
def create_ladder(club_id: int):
    data = request.get_json() or {}

    user_id = _get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    # Check club exists
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404

    # Check user is owner
    club_owner = ClubOwner.query.filter_by(id=user_id).first()
    if not club_owner:
        return jsonify({"message": "Unauthorized"}), 401

    owner_check = ClubOwnerClub.query.filter_by(
        club_owner_id=club_owner.id,
        club_id=club_id
    ).first()

    if not owner_check:
        return jsonify({"message": "Forbidden"}), 403

    # Create ladder
    ladder = Ladder(
        club_id=club_id,
        name=data.get("name"),
        description=data.get("description"),
        sport_type_id=data.get("sport_type_id", 1),
        ruleset_id=data.get("ruleset_id", 1),
        ladder_rating_function_id=data.get("ladder_rating_function_id", 1)
    )

    db.session.add(ladder)
    db.session.commit()

    test = Ladder.query.filter_by(id=ladder.id).first()
    if not test:
        return jsonify({"message": "Forbidden"}), 903


    return jsonify({
        "ladder": {
            "id": ladder.id,
            "name": ladder.name,
            "description": ladder.description,
            "club_id": ladder.club_id
        }
    }), 201