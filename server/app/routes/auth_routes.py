import os
import resend
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, make_response

from server.app.decorators.login_required import login_required
from server.app.models.account import Account
from server.app.services.auth_service import register_user, login_user, generate_reset_token, verify_reset_token, update_password, generate_verification_token, verify_email_token, mark_user_as_verified, change_password
from server.extensions import db

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

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

        token = generate_verification_token(email)
        params: resend.Emails.SendParams = {
            "from": MAIL_FROM,
            "to": [email],
            "subject": "Verify your account",
            "html": f'<a href="{FRONTEND_URL}/verify-email/{token}">Verify your account</a>',
        }
        resend.Emails.send(params)

        return jsonify({"message": "Registered successfully. Check your email to verify your account."}), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception:
        return jsonify({"message": "Could not send verification email. Please try again later."}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Email and password are required."}), 400

    try:
        result = login_user(email, password)
    except PermissionError as e:
        return jsonify({"message": str(e)}), 403

    if not result:
        return jsonify({"message": "Invalid credentials."}), 401

    token, account = result
    response = make_response(
        jsonify(
            {
                "message": "Login successful.",
                "account": account.to_dict()
            }
        ),
        200,
    )
    response.set_cookie("access_token", token, httponly=True, secure=True, samesite="Lax")
    return response

@auth_bp.route("/logout", methods=["POST"])
def logout():
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
def me(account: Account):
    base = account.to_dict()

    managed_team_ids = []
    if account.team_manager:
        managed_team_ids = [t.id for t in account.team_manager.teams]

    base["managedTeamIds"] = managed_team_ids

    club_ids = []
    if account.team_manager and account.team_manager.club_owner:
        club_ids = [c.id for c in account.team_manager.club_owner.clubs]
    base["clubIds"] =club_ids

    return jsonify({
        "account": base
         }), 200


@auth_bp.route("/me", methods=["PATCH"])
@login_required
def update_me(account: Account):
    data = request.get_json() or {}

    first_name = (data.get("firstName") or "").strip()
    last_name = (data.get("lastName") or "").strip()
    date_of_birth_raw = data.get("dateOfBirth")

    if not first_name or not last_name:
        return jsonify({"message": "First name and last name are required."}), 400

    parsed_date_of_birth = account.date_of_birth
    if date_of_birth_raw in (None, ""):
        parsed_date_of_birth = None
    else:
        try:
            parsed_date_of_birth = date.fromisoformat(str(date_of_birth_raw))
        except ValueError:
            return jsonify({"message": "dateOfBirth must be a valid ISO date (YYYY-MM-DD)."}), 400

    account.first_name = first_name
    account.last_name = last_name
    account.date_of_birth = parsed_date_of_birth

    db.session.add(account)
    db.session.commit()

    return jsonify({"account": account.to_dict()}), 200


@auth_bp.route("/me/password", methods=["PATCH"])
@login_required
def update_my_password(account: Account):
    data = request.get_json() or {}
    current_password = data.get("currentPassword") or ""
    new_password = data.get("password") or ""
    repeat_password = data.get("repeatPassword")

    try:
        change_password(account, current_password, new_password, repeat_password)
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"message": "Password updated successfully."}), 200


@auth_bp.route("/me/details", methods=["GET"])
@login_required
def me_details(account: Account):
    base = account.to_dict(include=["team_manager", "club_owner", "player", "administrator"])

    return jsonify({
        "account": base
    }), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"message": "Email is required."}), 400

    account = Account.query.filter_by(email=email).first()

    if account:
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


@auth_bp.route("/verify-email/<token>", methods=["GET"])
def verify_email(token):
    email = verify_email_token(token)

    if not email:
        return jsonify({"message": "Token is invalid or expired."}), 400

    try:
        mark_user_as_verified(email)
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"message": "Email verified successfully."}), 200

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
    
