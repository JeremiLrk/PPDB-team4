from flask import Blueprint, jsonify, request
from server.app.models.club import Club
from server.app.services.auth_service import verify_user
from server.app.models.ladder import Ladder
from server.extensions import db
from server.app.models.account import Account
from server.app.models.club_owner import ClubOwner
from server.app.models.club_owner_club import ClubOwnerClub
from server.app.models.club_player import ClubPlayer
from server.app.routes.dashboard_routes import _get_current_user_id_from_cookie

clubs_bp = Blueprint("clubs", __name__, url_prefix="/api")

@clubs_bp.get("/clubs")
def list_clubs():
    db_clubs = Club.query.order_by(Club.name.asc()).all()
    clubs = [{"id": club.id, "name": club.name, "description": club.description, "sport_type_id": club.sport_type_id, "city": club.city} for club in db_clubs]
    return jsonify({"clubs": clubs}), 200

@clubs_bp.get("/clubs/<int:club_id>")
def get_club(club_id: int):
    club = Club.query.filter_by(id=club_id).first()
    if not club:
        return jsonify({"message": "Club not found"}), 404
    
    return jsonify({"club": {"id": club.id, "name": club.name, "description": club.description, "sport_type_id": club.sport_type_id, "city": club.city}}), 200


@clubs_bp.get("/clubs/<int:club_id>/ladders")
def get_club_ladders(club_id: int):
    # Haal alle ladders op die bij deze specifieke club horen
    ladders = Ladder.query.filter_by(club_id=club_id).all()
    
    # Zet ze om naar een lijst die React begrijpt
    return jsonify([
        {"id": l.id, "name": l.name, "description": l.description} 
        for l in ladders
    ]), 200

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
    club.sport_type_id = data.get("sport_type_id", club.sport_type_id)

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
        db.session.query(Account)
        .join(ClubPlayer, ClubPlayer.player_id == Account.id)
        .filter(ClubPlayer.club_id == club_id)
        .filter(~Account.id.in_(owner_user_ids))
        .all()
    )

    result = [
        {
            "id": account.id,
            "email": account.email,
        }
        for account in members
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

    # Check current account is an owner of this club
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

    # Check account is owner
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

@clubs_bp.get("/clubs/<int:club_id>/owners")
def get_club_owners(club_id: int):
    """List all owners/managers of a club."""
    current_user_id = _get_current_user_id_from_cookie()
    if not current_user_id:
        return jsonify({"message": "Unauthorized"}), 401

    owners = (
        db.session.query(Account)
        .join(ClubOwner, ClubOwner.id == Account.id)
        .join(ClubOwnerClub, ClubOwnerClub.club_owner_id == ClubOwner.id)
        .filter(ClubOwnerClub.club_id == club_id)
        .all()
    )

    return jsonify({
        "owners": [
            {"id": owner.id, "email": owner.email, "name": owner.first_name + " " + owner.last_name} 
            for owner in owners
        ]
    }), 200

@clubs_bp.post("/clubs/<int:club_id>/owners")
def add_club_owner(club_id: int):
    """Add a new owner to the club by their Account ID."""
    current_user_id = _get_current_user_id_from_cookie()
    data = request.get_json() or {}
    target_owner_id = data.get("owner_id")

    if not current_user_id:
        return jsonify({"message": "Unauthorized"}), 401
    
    if not target_owner_id:
        return jsonify({"message": "Owner ID is required"}), 400

    requester_owner = ClubOwnerClub.query.filter_by(
        club_owner_id=current_user_id, club_id=club_id
    ).first()
    if not requester_owner:
        return jsonify({"message": "Forbidden"}), 403

    target_account = Account.query.get(target_owner_id)
    if not target_account:
        return jsonify({"message": "User not found"}), 404

    owner_profile = ClubOwner.query.get(target_owner_id)
    if not owner_profile:
        owner_profile = ClubOwner(id=target_owner_id)
        db.session.add(owner_profile)
        db.session.flush()

    existing_link = ClubOwnerClub.query.filter_by(
        club_owner_id=target_owner_id, club_id=club_id
    ).first()
    if existing_link:
        return jsonify({"message": "User is already an owner"}), 400

    new_link = ClubOwnerClub(club_owner_id=target_owner_id, club_id=club_id)
    db.session.add(new_link)
    db.session.commit()

    return jsonify({
        "message": "Owner added successfully",
        "owner": {"id": target_account.id, "email": target_account.email}
    }), 201

@clubs_bp.delete("/clubs/<int:club_id>/owners/<int:owner_id>")
def remove_club_owner(club_id: int, owner_id: int):
    """Remove an owner from the club."""
    current_user_id = _get_current_user_id_from_cookie()
    if not current_user_id:
        return jsonify({"message": "Unauthorized"}), 401

    if current_user_id == owner_id:
        return jsonify({"message": "You cannot remove yourself"}), 400

    requester_owner = ClubOwnerClub.query.filter_by(
        club_owner_id=current_user_id, club_id=club_id
    ).first()
    if not requester_owner:
        return jsonify({"message": "Forbidden"}), 403

    target_link = ClubOwnerClub.query.filter_by(
        club_owner_id=owner_id, club_id=club_id
    ).first()

    if not target_link:
        return jsonify({"message": "Owner not found in this club"}), 404

    db.session.delete(target_link)
    db.session.commit()

    return jsonify({"message": "Owner removed successfully"}), 200

from sqlalchemy import or_

@clubs_bp.get("/accounts/search")
def search_accounts():
    query = request.args.get("q", "").strip()
    
    if len(query) < 3:
        return jsonify({"accounts": []}), 200

    search_pattern = f"%{query}%"

    accounts = Account.query.filter(
        or_(
            Account.email.ilike(search_pattern),
            Account.first_name.ilike(search_pattern),
            Account.last_name.ilike(search_pattern)
        )
    ).limit(10).all()

    return jsonify({
        "accounts": [
            {
                "id": a.id,
                "email": a.email,
                "name": f"{a.first_name} {a.last_name}".strip() or "Unknown User"
            } 
            for a in accounts
        ]
    }), 200