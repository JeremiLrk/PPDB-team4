import os
import resend
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, make_response

from server.app.decorators.login_required import login_required
from server.app.models.account import Account
from server.app.services.auth_service import register_user, login_user, generate_reset_token, verify_reset_token, update_password

load_dotenv()

resend.api_key = os.environ["RESEND_API_KEY"]
FRONTEND_URL = os.environ["FRONTEND_URL"].rstrip("/")
MAIL_FROM = os.environ["MAIL_FROM"]

auth_bp = Blueprint("auth", __name__, url_prefix="/api")

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    first_name = data.get("firstName")
    last_name = data.get("lastName")
    date_of_birth = data.get("dateOfBirth")

    if not email or not password or not first_name or not last_name or not date_of_birth:
        return jsonify({"message": "Missing credentials."}), 400

    try:
        register_user(email, password, first_name, last_name, date_of_birth)

        token, user = login_user(email, password)
        response = make_response(
            jsonify(
                {
                    "message": "Registered successfully.",
                    "user": user.to_dict(),
                }
            ),
            201,
        )
        response.set_cookie(
            "access_token",
            token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        return response
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Email and password are required."}), 400

    result = login_user(email, password)
    if not result:
        return jsonify({"message": "Invalid credentials."}), 401

    token, user = result
    response = make_response(
        jsonify(
            {
                "message": "Login successful.",
                "user": user.to_dict()
            }
        ),
        200,
    )
    response.set_cookie("access_token", token, httponly=True, secure=True, samesite="Lax")
    return response

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout(user: Account):
    response = make_response(jsonify({"message": "Successfully logged out."}), 200)
    response.set_cookie(
        "access_token",
        "",
        expires=0,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    return response

@auth_bp.route("/me", methods=["GET"])
@login_required
def me(user: Account):
    return jsonify({"user": user.to_dict()}), 200

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"message": "Email is required."}), 400

    user = Account.query.filter_by(email=email).first()

    if user:
        token = generate_reset_token(email)

        params: resend.Emails.SendParams = {
            "from": MAIL_FROM,
            "to": [email],
            "subject": "Password reset request",
            "html": f'<a href="{FRONTEND_URL}/reset-password/{token}">Reset Password</a>',
        }

        resend.Emails.send(params)
    
    response = make_response(jsonify({"message": "Check your inbox for the password reset link."}), 200)
    
    return response

@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):
    email = verify_reset_token(token)
    
    data = request.get_json() or {}
    password = data.get("password") or ""

    if not email:
        return jsonify({"message": "Token is invalid or expired."}), 400

    if not password:
        return jsonify({"message": "Password is required."}), 400
    
    try:
        update_password(email, password)
        return jsonify({"message": "Password updated successfully."}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
