from flask import Blueprint, jsonify, request

from server.app.decorators import login_required
from server.app.models.club import Club
from server.app.services.auth_service import verify_user
from server.app.models.ladder import Ladder
from server.extensions import db
from server.app.models.account import Account, Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.club_owner_club import ClubOwnerClub
from server.app.models.club_player import ClubPlayer
from server.app.models.team import TeamManager
from server.app.routes.dashboard_routes import _get_current_user_id_from_cookie
from sqlalchemy import or_

clubs_bp = Blueprint("clubs", __name__, url_prefix="/api")

@clubs_bp.get("/clubs")
def list_clubs():
    db_clubs = Club.query.order_by(Club.name.asc()).all()
    clubs = [{
        "id": club.id,
        "name": club.name,
        "description": club.description,
        "sport_type_id": club.sport_type_id,
        "sport": club.sport,
        "city": club.city,
    } for club in db_clubs]
    return jsonify({"clubs": clubs}), 200

@clubs_bp.get("/clubs/<int:club_id>")
def get_club(club_id: int):
    club = Club.query.filter_by(id=club_id).first()
    if not club:
        return jsonify({"message": "Club not found"}), 404
    
    return jsonify({"club": {
        "id": club.id,
        "name": club.name,
        "description": club.description,
        "sport_type_id": club.sport_type_id,
        "sport": club.sport,
        "city": club.city,
    }}), 200

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
    admin = Administrator.query.filter_by(id=account.id).first()
    if admin:
        return jsonify({"is_manager": True}), 200
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

@clubs_bp.get("/clubs/<int:club_id>/ladders")
def get_club_ladders(club_id: int):
    # Haal alle ladders op die bij deze specifieke club horen
    ladders = Ladder.query.filter_by(club_id=club_id).all()
    
    # Zet ze om naar een lijst die React begrijpt
    return jsonify([
        {"id": l.id, "name": l.name, "description": l.description,"ruleset_id": l.ruleset_id}
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
    admin = Administrator.query.filter_by(id=user_id).first()
    if not clubowner and not admin:
        return jsonify({"message": "Unauthorized"}), 401
    
    owner_check = ClubOwnerClub.query.filter_by(club_owner_id=clubowner.id, club_id=club_id).first()
    if not owner_check and not admin:
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
    admin = Administrator.query.filter_by(id=current_user_id).first()
    if not club_owner and not admin:
        return jsonify({"message": "Unauthorized"}), 401

    owner_check = ClubOwnerClub.query.filter_by(
        club_owner_id=club_owner.id,
        club_id=club_id
    ).first()

    if not owner_check and not admin:
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
    admin = Administrator.query.filter_by(id=user_id).first()
    if not club_owner and not admin:
        return jsonify({"message": "Unauthorized"}), 401

    owner_check = ClubOwnerClub.query.filter_by(
        club_owner_id=club_owner.id,
        club_id=club_id
    ).first()

    if not owner_check and not admin:
        return jsonify({"message": "Forbidden"}), 403

    # Create ladder
    ladder = Ladder(
        club_id=club_id,
        name=data.get("name"),
        description=data.get("description"),
        sport_type_id=data.get("sport_type_id", 1),
        ruleset_id=data.get("ruleset_id"),
        ladder_rating_function_id=data.get("ladder_rating_function_id", 1),
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

from sqlalchemy import or_

@clubs_bp.get("/clubs/<int:club_id>/owners")
def get_club_owners(club_id: int):
    """List all owners/managers of a club AND global administrators."""
    current_user_id = _get_current_user_id_from_cookie()
    if not current_user_id:
        return jsonify({"message": "Unauthorized"}), 401

    # Query accounts that are EITHER:
    # 1. Linked to this specific club via ClubOwner/ClubOwnerClub
    # 2. Registered in the Administrator table
    owners = (
        db.session.query(Account)
        .outerjoin(ClubOwner, ClubOwner.id == Account.id)
        .outerjoin(ClubOwnerClub, ClubOwnerClub.club_owner_id == ClubOwner.id)
        .outerjoin(Administrator, Administrator.id == Account.id)
        .filter(
            or_(
                ClubOwnerClub.club_id == club_id,
                Administrator.id.isnot(None)
            )
        )
        .distinct() # Ensure an Admin who is also a ClubOwner isn't listed twice
        .all()
    )

    return jsonify({
        "owners": [
            {
                "id": owner.id, 
                "email": owner.email, 
                "name": f"{owner.first_name} {owner.last_name}",
                # Optional: helpful for the frontend to know WHY they are in this list
                "role": "admin" if owner.administrator else "owner" 
            } 
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

    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404

    requester_owner = ClubOwnerClub.query.filter_by(
        club_owner_id=current_user_id, club_id=club_id
    ).first()
    admin = Administrator.query.filter_by(id=current_user_id).first()
    if not requester_owner and not admin:
        return jsonify({"message": "Forbidden"}), 403

    target_account = Account.query.get(target_owner_id)
    if not target_account:
        return jsonify({"message": "User not found"}), 404

    target_manager = TeamManager.query.get(target_owner_id)
    if not target_manager:
        target_manager = TeamManager(id=target_owner_id)
        db.session.add(target_manager)
        db.session.flush()

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

    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404

    requester_owner = ClubOwnerClub.query.filter_by(
        club_owner_id=current_user_id, club_id=club_id
    ).first()
    admin = Administrator.query.filter_by(id=current_user_id).first()
    if not requester_owner and not admin:
        return jsonify({"message": "Forbidden"}), 403

    target_link = ClubOwnerClub.query.filter_by(
        club_owner_id=owner_id, club_id=club_id
    ).first()

    if not target_link:
        return jsonify({"message": "Owner not found in this club"}), 404

    db.session.delete(target_link)
    db.session.commit()

    return jsonify({"message": "Owner removed successfully"}), 200
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

@clubs_bp.get("/clubs/my")
@login_required
def list_my_clubs(account: Account):
    """Return all clubs the current user can manage (is an owner of)."""

    admin = Administrator.query.filter_by(id=account.id).first()
    if admin:
        db_clubs = Club.query.order_by(Club.name.asc()).all()
        clubs = [{"id": club.id, "name": club.name} for club in db_clubs]
        return jsonify({"clubs": clubs}), 200
    club_owner = ClubOwner.query.filter_by(id=account.id).first()
    if not club_owner:
        return jsonify({"clubs": []}), 200

    links = ClubOwnerClub.query.filter_by(club_owner_id=club_owner.id).all()
    club_ids = [link.club_id for link in links]

    if not club_ids:
        return jsonify({"clubs": []}), 200

    db_clubs = Club.query.filter(Club.id.in_(club_ids)).order_by(Club.name.asc()).all()
    clubs = [{"id": club.id, "name": club.name} for club in db_clubs]
    return jsonify({"clubs": clubs}), 200

@clubs_bp.delete("/clubs/<int:club_id>")
def delete_club(club_id: int):
    """
    Deletes the club and cleans up owner associations.
    Note: Depending on your business logic, you might want to 
    unaffiliate teams instead of deleting them.
    """
    current_user_id = _get_current_user_id_from_cookie()
    if not current_user_id:
        return jsonify({"message": "Unauthorized"}), 401

    # 1. Fetch the club
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"message": "Club not found"}), 404

    # 2. Authorization Check: Is the requester an owner of THIS club?
    requester_owner = ClubOwnerClub.query.filter_by(
        club_owner_id=current_user_id, club_id=club_id
    ).first()
    admin = Administrator.query.filter_by(id=current_user_id).first()
    if not requester_owner and not admin:
        return jsonify({"message": "Forbidden"}), 403

    try:
        db.session.delete(club)
        db.session.commit()

        return jsonify({
            "message": f"Club '{club.name}' and all associated data have been deleted."
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Failed to delete club: {str(e)}"}), 500