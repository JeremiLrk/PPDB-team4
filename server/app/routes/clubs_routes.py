from flask import Blueprint, jsonify

from server.app.models.club import Club

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

from flask import Blueprint, jsonify, request
from server.app.models.club import Club
from server.app.services.auth_service import verify_user # <-- Import your auth function

clubs_bp = Blueprint("clubs", __name__, url_prefix="/api")

# ... (keep your existing list_clubs and get_club routes here) ...

@clubs_bp.get("/clubs/<int:club_id>/is_manager")
def check_if_manager(club_id: int):
    # 1. Get the token from the cookie (just like you did in auth_routes.py)
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

    # 5. Send the result back to React!
    return jsonify({"is_manager": is_manager}), 200