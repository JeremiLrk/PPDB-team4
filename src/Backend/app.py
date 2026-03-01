from flask import Flask, jsonify, request, make_response
from config import config_data as config
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
import jwt
import datetime
import psycopg

DEBUG = True
HOST = "127.0.0.1" if DEBUG else "0.0.0.0"

# Initialize the Flask app
app = Flask(__name__)

# Configure global application data 
app_data = {}
app_data['app_name'] = config['app_name']
app_data['interface'] = config['interface']

# Configure the database
db_username = config['db_username']
db_password = config['db_password']
db_host = config['db_host']
db_port = config['db_port']
db_name = config['db_name']
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "test_secret_key"

# Initialize the database
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(255), nullable=True) 
    last_name = db.Column(db.String(255), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)

    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")

def load_sql():
    try:
        sql_file_path = '../../sql/schema.sql'
        with open(sql_file_path, 'r') as file:
            sql_script = file.read()
        with psycopg.connect(
            dbname=db_name,
            user=db_username,
            password=db_password,
            host=db_host,
            port=db_port
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_script)
                conn.commit()
        print("SQL script executed successfully.")
    except Exception as e:
        print(f"Error executing SQL script: {e}")


with app.app_context():
 #   db.drop_all()
    load_sql()
    db.create_all()

############
# REST API #
############

@app.route("/api/signup", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Email and password are required."}), 400
    
    if len(password) < 6:
        return jsonify({"message": "Password is too short."}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"message": "User already exists."}), 400

    new_user = User(email=email, password_hash=generate_password_hash(password))

    db.session.add(new_user)
    db.session.commit()

    response = make_response(jsonify({"message": "Registered successfully."}), 201)

    return response

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Email and password are required."}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials."}), 401
    
    payload = {
        "user_id": user.id,
        "role": user.role,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }

    token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

    response = make_response(jsonify({"message": "Login successful."}), 200)

    response.set_cookie("access_token", token, httponly=True, secure=True, samesite="Lax")

    return response

########
# VIEW #
########

# Home route (renders index page)
@app.route("/")
def index():
    return jsonify({"ok": True, "msg": "Backend running."})

@app.get("/api/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return {"ok": True, "db_connected": True}
    except Exception:
        return {
            "ok": False,
            "db_connected": False,
            "msg": "Database not reachable",
        }, 503


##################
# RUN DEV SERVER #
##################
if __name__ == "__main__":
    app.run(HOST, debug=DEBUG)
