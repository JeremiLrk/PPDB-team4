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

_ALLOWED_GENDERS = frozenset({"male", "female", "other"})


def parse_date_of_birth(date_of_birth, *, allow_none: bool = False):
    """Parse an ISO date string into a date object for account records."""
    if date_of_birth in (None, ""):
        if allow_none:
            return None
        raise ValueError("dateOfBirth is required.")

    if isinstance(date_of_birth, datetime.datetime):
        return date_of_birth.date()
    if isinstance(date_of_birth, datetime.date):
        return date_of_birth

    try:
        return datetime.date.fromisoformat(str(date_of_birth))
    except (TypeError, ValueError):
        raise ValueError("dateOfBirth must be a valid ISO date (YYYY-MM-DD).")


def register_user(email, password, first_name, last_name, date_of_birth, gender=None, phone=None):
    """
    Registers a new user with the provided details.

    Args:
        email (str): The user's email address.
        password (str): The user's password.
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        date_of_birth (datetime.date): The user's date of birth.
        gender (str, optional): The user's gender.
        phone (str, optional): The user's phone number.

    Returns:
        Account: The newly created user account.

    Postconditions:
        - A new user account is created in the database.
    """
    if len(password) < 6:
        raise ValueError("Password is too short.")

    if not gender or not phone:
        raise ValueError("Gender and phone number are required.")

    if gender not in _ALLOWED_GENDERS:
        raise ValueError("gender must be male, female, or other.")

    account = Account.query.filter_by(email=email).first()
    if account:
        raise ValueError("Account already exists.")

    parsed_date_of_birth = parse_date_of_birth(date_of_birth)

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
        date_of_birth=parsed_date_of_birth,
        gender=gender,
        phone=phone,
        account_role_id=user_role.id,
        is_verified=False,
    )

    db.session.add(new_user)
    db.session.commit()
    return new_user

def login_user(email, password):
    """
    Logs in a user with the provided email and password.

    Args:
        email (str): The user's email address.
        password (str): The user's password.

    Returns:
        tuple: A tuple containing the authentication token and the user account, or None if login fails.
    """
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
    """
    Verifies a user with the provided token.

    Args:
        token (str): The authentication token.

    Returns:
        Account: The verified user account, or None if verification fails.
    """
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
    """Generates a password reset token for the given email address."""
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt=PW_RESET_SALT)


def generate_verification_token(email):
    """Generates an email verification token for the given email address."""
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt=EMAIL_VERIFICATION_SALT)

def verify_reset_token(token, expiration=900):
    """Verifies a password reset token, returning the associated email if valid or None if invalid or expired."""
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt=PW_RESET_SALT, max_age=expiration)
        return email
    except:
        return None


def verify_email_token(token, expiration=86400):
    """Verifies an email verification token, returning the associated email if valid or None if invalid or expired."""
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt=EMAIL_VERIFICATION_SALT, max_age=expiration)
        return email
    except:
        return None


def mark_user_as_verified(email):
    """Marks the user with the given email address as verified, returning the updated account or raising an error if the account is not found."""
    account = Account.query.filter_by(email=email).first()
    if not account:
        raise ValueError("User not found.")

    account.is_verified = True
    db.session.commit()
    return account
    
def update_password(email, password):
    """Updates the password for the user with the given email address, returning the updated account or raising an error if the account is not found or the password is invalid."""
    if len(password) < 6:
        raise ValueError("Password is too short.")

    account = Account.query.filter_by(email=email).first()

    if not account:
        raise ValueError("Account not found.")

    account.password_hash = generate_password_hash(password)
    db.session.commit()
    return account


def change_password(account, current_password, new_password, repeat_password=None):
    """Changes the password for the given user account, verifying the current password and ensuring the new password meets requirements."""
    if not current_password or not new_password:
        raise ValueError("Current password and new password are required.")

    if repeat_password is not None and new_password != repeat_password:
        raise ValueError("Passwords do not match.")

    if not check_password_hash(account.password_hash, current_password):
        raise ValueError("Current password is incorrect.")

    return update_password(account.email, new_password)
