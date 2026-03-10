from werkzeug.security import generate_password_hash, check_password_hash
from server.app.models.user import User, db
import jwt
import datetime
from server.config import SECRET_KEY

def register_user(email, password):
    if len(password) < 6:
        raise ValueError("Password too short")

    user = User.query.filter_by(email=email).first()
    if user:
        raise ValueError("User already exists")

    new_user = User(email=email, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    return new_user

def login_user(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return None

    payload = {
        "user_id": user.id,
        "role": user.role,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token, user