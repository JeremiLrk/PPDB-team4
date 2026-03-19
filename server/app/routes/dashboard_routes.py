from flask import Blueprint, jsonify, request
import jwt

from server.app.models.user import User
from server.app.models.club_join_request import ClubJoinRequest
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

    join_requests = ClubJoinRequest.query.filter_by(user_id=user_id).all()
    return jsonify(
        {
            "user": {"id": user.id, "email": user.email},
            "roles": [getattr(user, "role", "user")],
            "clubs": [],
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