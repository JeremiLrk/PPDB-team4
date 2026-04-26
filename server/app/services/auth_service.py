import os
import jwt
import datetime
from pathlib import Path
from dotenv import load_dotenv
from server.config import SECRET_KEY
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from server.app.models.account import Account
from server.app.models.account_role import AccountRole
from server.extensions import db

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

PW_RESET_SALT = os.environ["PW_RESET_SALT"]
EMAIL_VERIFICATION_SALT = os.environ.get("EMAIL_VERIFICATION_SALT", "email-verify-salt")

def register_user(email, password, first_name, last_name, date_of_birth):
    if len(password) < 6:
        raise ValueError("Password is too short.")

    account = Account.query.filter_by(email=email).first()
    if account:
        raise ValueError("Account already exists.")

    user_role = AccountRole.query.filter_by(name="user").first()

    if not user_role:
        user_role = AccountRole(name="account")
        db.session.add(user_role)
        db.session.flush()

    new_user = Account(
        email=email,
        password_hash=generate_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        account_role_id=user_role.id,
        is_verified=True,
    )

    db.session.add(new_user)
    db.session.commit()
    return new_user

def login_user(email, password):
    account = Account.query.filter_by(email=email).first()
    if not account or not check_password_hash(account.password_hash, password):
        return None
    if not account.is_verified:
        raise PermissionError("Please verify your email before logging in.")


    resolved = account.resolved_role
    role_name = type(resolved).__name__.lower()

    payload = {
        "user_id": account.id,
        "role": role_name,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token, account

def verify_user(token):
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    return Account.query.filter_by(id=user_id).first()

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt=PW_RESET_SALT)


def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt=EMAIL_VERIFICATION_SALT)

def verify_reset_token(token, expiration=900):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt=PW_RESET_SALT, max_age=expiration)
        return email
    except:
        return None


def verify_email_token(token, expiration=86400):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt=EMAIL_VERIFICATION_SALT, max_age=expiration)
        return email
    except:
        return None


def mark_user_as_verified(email):
    account = Account.query.filter_by(email=email).first()
    if not account:
        raise ValueError("User not found.")

    account.is_verified = True
    db.session.commit()
    return account
    
def update_password(email, password):
    if len(password) < 6:
        raise ValueError("Password is too short.")

    account = Account.query.filter_by(email=email).first()

    if not account:
        raise ValueError("Account not found.")

    account.password_hash = generate_password_hash(password)
    db.session.commit()
    return account


def change_password(account, current_password, new_password, repeat_password=None):
    if not current_password or not new_password:
        raise ValueError("Current password and new password are required.")

    if repeat_password is not None and new_password != repeat_password:
        raise ValueError("Passwords do not match.")

    if not check_password_hash(account.password_hash, current_password):
        raise ValueError("Current password is incorrect.")

    return update_password(account.email, new_password)
