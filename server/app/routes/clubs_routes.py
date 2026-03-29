from flask import Blueprint, jsonify, request
from server.app.models.club import Club
from server.app.services.auth_service import verify_user
from server.app.models.user import db
from server.app.models.ladder import Ladder
# Define the Blueprint EXACTLY ONCE
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
    return jsonify({"club": {"id": club.id, "name": club.name}}), 200

@clubs_bp.get("/clubs/<int:club_id>/is_manager")
def check_if_manager(club_id: int):
    # 1. Get the token from the cookie
    token = request.cookies.get("access_token")
    user = verify_user(token)

    # 2. If no valid user is found, they definitely aren't a manager
    if not user:
        return jsonify({"is_manager": False}), 401

    # 3. Find the club in the database
    club = Club.query.filter_by(id=club_id).first()
    if not club:
        return jsonify({"message": "Club not found"}), 404

    # 4. Check if the logged-in user is in the club's list of managers
    is_manager = any(manager.id == user.id for manager in club.managers)

    # 5. Send the result back to React
    return jsonify({"is_manager": is_manager}), 200

@clubs_bp.post("/clubs")
def create_club():
    # 1. Kijk wie de club probeert aan te maken (net als bij je is_manager route)
    token = request.cookies.get("access_token")
    user = verify_user(token)

    if not user:
        return jsonify({"message": "Je moet ingelogd zijn om een club te maken"}), 401

    # 2. Haal de naam van de club uit de request van de frontend
    data = request.get_json()
    club_name = data.get("name")

    if not club_name:
        return jsonify({"message": "Clubnaam is verplicht"}), 400

    # 3. Maak de nieuwe club aan
    new_club = Club(name=club_name)

    # 4. De Magie: Voeg de maker direct toe als manager! 
    # SQLAlchemy snapt dit dankzij onze club_owner_club tabel fix.
    new_club.managers.append(user)

    # 5. Opslaan in de database
    db.session.add(new_club)
    db.session.commit()

    return jsonify({
        "message": "Club succesvol aangemaakt!", 
        "club": {"id": new_club.id, "name": new_club.name}
    }), 201
@clubs_bp.post("/clubs/<int:club_id>/managers")
def add_club_manager(club_id: int):
    # 1. Check of de huidige gebruiker zelf manager is (beveiliging!)
    token = request.cookies.get("access_token")
    current_user = verify_user(token)
    club = Club.query.get_or_404(club_id)
    
    if not current_user or current_user not in club.managers:
        return jsonify({"message": "Niet geautoriseerd"}), 403

    # 2. Zoek de nieuwe manager op via email
    data = request.get_json()
    new_manager = User.query.filter_by(email=data.get("email")).first()

    if not new_manager:
        return jsonify({"message": "Gebruiker niet gevonden"}), 404

    # 3. Voeg toe aan de relatie
    if new_manager not in club.managers:
        club.managers.append(new_manager)
        db.session.commit()
        return jsonify({"message": "Manager toegevoegd"}), 200
    
    return jsonify({"message": "Gebruiker is al manager"}), 400

@clubs_bp.post("/clubs/<int:club_id>/ladders")
def create_ladder(club_id: int):
    token = request.cookies.get("access_token")
    user = verify_user(token)
    club = Club.query.get_or_404(club_id)

    if not user or user not in club.managers:
        return jsonify({"message": "Niet geautoriseerd"}), 403

    data = request.get_json()
    
    new_ladder = Ladder(
        club_id=club_id,
        name=data.get("name"),
        description=data.get("description"),
        sport_type_id=data.get("sport_type_id"), # Pak de sport uit de frontend
        ladder_rating_function_id=1 
    )

    db.session.add(new_ladder)
    db.session.commit()

    return jsonify({"message": "Ladder succesvol gestart!", "id": new_ladder.id}), 201
@clubs_bp.get("/clubs/<int:club_id>/ladders")
def get_club_ladders(club_id: int):
    # Haal alle ladders op die bij deze specifieke club horen
    ladders = Ladder.query.filter_by(club_id=club_id).all()
    
    # Zet ze om naar een lijst die React begrijpt
    return jsonify([
        {"id": l.id, "name": l.name, "description": l.description} 
        for l in ladders
    ]), 200

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
