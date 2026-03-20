from flask import Blueprint, jsonify, request
import jwt

from server.app.models.user import User
from server.app.models.club_join_request import ClubJoinRequest
from server.app.models.club import Club
from server.app.models.club_owner import ClubOwner
from server.app.models.club_owner_club import ClubOwnerClub
from server.app.models import db
from server.config import SECRET_KEY
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")


def _get_current_user_id_from_cookie():
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.PyJWTError:
        return None


@dashboard_bp.get("/me/dashboard")
def get_my_dashboard():
    user_id = _get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    club_owner = ClubOwner.query.filter_by(id=user_id).first()

    clubs = []
    if club_owner:
        owned_links = ClubOwnerClub.query.filter_by(club_owner_id=club_owner.id).all()
        club_ids = [link.club_id for link in owned_links]

        if club_ids:
            clubs = Club.query.filter(Club.id.in_(club_ids)).all()

    join_requests = ClubJoinRequest.query.filter_by(user_id=user_id).all()
    return jsonify(
        {
            "user": {"id": user.id, "email": user.email},
            "roles": [getattr(user, "role", "user")],
            "clubs": [club.serialize() for club in clubs],
            "pending_requests": {
                "my_requests": [request.serialize() for request in join_requests],
                "my_club_creation_requests": [],
            },
        }
    ), 200

@dashboard_bp.post("/club/join-request")
def set_join():
    user_id = _get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    club_id = request.get_json()["club_id"]
    if not club_id:
        return jsonify({"message": "Club not found"}), 404
    
    if ClubJoinRequest.query.filter_by(club_id=club_id, user_id=user_id).first():
        return jsonify({"status": True}), 200

    join_request = ClubJoinRequest(
        club_id=club_id,
        user_id=user_id,
        date=datetime.now()
    )

    db.session.add(join_request)
    db.session.commit()
    
    return jsonify({"status": True}), 200


@dashboard_bp.post("/club/add-club")
def add_club():
    user_id = _get_current_user_id_from_cookie()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()

    required_fields = ["name", "description", "sport", "city"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"message": f"Missing fields: {missing}"}), 400

    try:
            club = Club(
                name=data["name"],
                description=data["description"],
                sport=data["sport"],
                city=data["city"]
            )

            db.session.add(club)
            db.session.flush()

            club_owner = ClubOwner.query.filter_by(id=user_id).first()

            if not club_owner:
                club_owner = ClubOwner(id=user_id)
                db.session.add(club_owner)
                db.session.flush()

            club_owner_club = ClubOwnerClub(
                club_owner_id=club_owner.id,
                club_id=club.id
            )
            db.session.add(club_owner_club)

            db.session.commit()

            return jsonify({"status": True,}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500