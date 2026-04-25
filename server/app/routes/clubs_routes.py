from flask import Blueprint, jsonify, request
from server.app.models.club import Club
from server.app.services.auth_service import verify_user
from server.app.models.ladder import Ladder
from server.extensions import db
from server.app.models.account import Account
from server.app.models.club_owner import ClubOwner
from server.app.models.club_owner_club import ClubOwnerClub
from server.app.models.club_player import ClubPlayer
from server.app.models.team import TeamManager
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

@clubs_bp.get("/clubs/<int:club_id>/is_manager")
def check_if_manager(club_id: int):
    # 1. Get the token from the cookie
    token = request.cookies.get("access_token")
    account = verify_user(token)

    # 2. If no valid account is found, they definitely aren't a manager
    if not account:
        return jsonify({"is_manager": False}), 401

    # 3. Find the club in the database
    club = Club.query.filter_by(id=club_id).first()
    if not club:
        return jsonify({"message": "Club not found"}), 404

    clubowner = ClubOwner.query.filter_by(id=account.id).first()
    if not clubowner:
        return jsonify({"message": "Unauthorized"}), 401
    
    owner_check = ClubOwnerClub.query.filter_by(club_owner_id=clubowner.id, club_id=club_id).first()
    if not owner_check:
        return jsonify({"message": "Forbidden"}), 403

    return jsonify({"is_manager": True}), 200

@clubs_bp.post("/clubs")
def create_club():
    # 1. Kijk wie de club probeert aan te maken (net als bij je is_manager route)
    token = request.cookies.get("access_token")
    account = verify_user(token)

    if not account:
        return jsonify({"message": "Je moet ingelogd zijn om een club te maken"}), 401

    # 2. Read payload
    data = request.get_json() or {}
    club_name = (data.get("name") or "").strip()

    if not club_name:
        return jsonify({"message": "Clubnaam is verplicht"}), 400

    city = (data.get("city") or "Unknown").strip() or "Unknown"
    description = (data.get("description") or "Club created by user").strip() or "Club created by user"
    sport_type_id = data.get("sport_type_id")
    sport_name = data.get("sport")

    # Ensure the account can own clubs: team_manager -> club_owner chain.
    team_manager = TeamManager.query.filter_by(id=account.id).first()
    if not team_manager:
        team_manager = TeamManager(id=account.id)
        db.session.add(team_manager)
        db.session.flush()

    club_owner = ClubOwner.query.filter_by(id=account.id).first()
    if not club_owner:
        club_owner = ClubOwner(id=account.id)
        db.session.add(club_owner)
        db.session.flush()

    # 3. Create club (all required fields present)
    new_club = Club(
        name=club_name,
        description=description,
        city=city,
        sport_type_id=sport_type_id,
    )
    if not sport_type_id and sport_name:
        new_club.sport = sport_name

    db.session.add(new_club)
    db.session.flush()

    owner_link = ClubOwnerClub.query.filter_by(club_owner_id=club_owner.id, club_id=new_club.id).first()
    if not owner_link:
        db.session.add(
            ClubOwnerClub(
                club_owner_id=club_owner.id,
                club_id=new_club.id,
                can_rename=True,
                can_change_description=True,
                can_manage_match=True,
                can_add_club_players=True,
                can_add_club_owners=True,
                can_add_club_rule=True,
            )
        )

    # 5. Persist
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
    new_manager = Account.query.filter_by(email=data.get("email")).first()

    if not new_manager:
        return jsonify({"message": "Gebruiker niet gevonden"}), 404

    # 3. Voeg toe aan de relatie
    if new_manager not in club.managers:
        club.managers.append(new_manager)
        db.session.commit()
        return jsonify({"message": "Manager toegevoegd"}), 200
    
    return jsonify({"message": "Gebruiker is al manager"}), 400

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
