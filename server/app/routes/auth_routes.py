from flask import Blueprint, request, jsonify, make_response
from server.app.services.auth_service import register_user, login_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api")

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400

    try:
        user = register_user(email, password)
        return jsonify({"message": "Registered successfully"}), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400

    result = login_user(email, password)
    if not result:
        return jsonify({"message": "Invalid credentials"}), 401

    token, user = result
    response = make_response(
        jsonify(
            {
                "message": "Login successful",
                "user": {"id": user.id, "email": user.email}
            }
                ), 200)
    response.set_cookie("access_token", token, httponly=True, secure=True, samesite="Lax")
    return response