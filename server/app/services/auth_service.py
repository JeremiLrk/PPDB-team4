import os
import jwt
import datetime
from dotenv import load_dotenv
from server.config import SECRET_KEY
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from server.app.models.account import Account
from server.extensions import db

load_dotenv()

PW_RESET_SALT = os.environ["PW_RESET_SALT"]

def register_user(email, password, first_name, last_name, date_of_birth):
    if len(password) < 6:
        raise ValueError("Password is too short.")

    user = Account.query.filter_by(email=email).first()
    if user:
        raise ValueError("User already exists.")

    new_user = Account(email=email, password_hash=generate_password_hash(password), first_name=first_name, last_name=last_name, date_of_birth=date_of_birth)
    db.session.add(new_user)
    db.session.commit()
    return new_user

def login_user(email, password):
    user = Account.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return None

    payload = {
        "user_id": user.id,
        "role": user.role,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token, user

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

def verify_reset_token(token, expiration=900):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt=PW_RESET_SALT, max_age=expiration)
        return email
    except:
        return None
    
def update_password(email, password):
    if len(password) < 6:
        raise ValueError("Password is too short.")
    
    user = Account.query.filter_by(email=email).first()

    if not user:
        raise ValueError("User not found.")
    
    user.password_hash = generate_password_hash(password)
    db.session.commit()
    return user