from flask import Blueprint, jsonify, request
import jwt

from server.app.models.user import User
from server.config import SECRET_KEY

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

    # TODO(team): replace this temporary shape with real queries from membership/request tables.
    # This keeps the frontend dashboard route working while auth/database flows are being finalized.
    return jsonify(
        {
            "user": {"id": user.id, "email": user.email},
            "roles": [getattr(user, "role", "user")],
            "clubs": [],
            "pending_requests": {
                "my_requests": [],
                "join_requests_to_review": [],
                "club_creation_to_review": [],
            },
        }
    ), 200
