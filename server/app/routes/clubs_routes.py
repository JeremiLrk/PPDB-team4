from flask import Blueprint, jsonify, request
from server.app.models.club import Club
from server.app.services.auth_service import verify_user
from server.app.models.user import db
from server.app.models.ladder import Ladder
# Define the Blueprint EXACTLY ONCE
clubs_bp = Blueprint("clubs", __name__, url_prefix="/api")

@clubs_bp.get("/clubs")
def list_clubs():
    db_clubs = Club.query.order_by(Club.name.asc()).all()
    clubs = [{"id": club.id, "name": club.name} for club in db_clubs]
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