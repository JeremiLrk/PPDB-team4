from flask import Flask
from flask.testing import FlaskClient
from app import User, db

def test_signup_success(client: FlaskClient, app: Flask):
    payload = {"email": "test@example.com", "password": "password123"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 201
    assert response.get_json()["message"] == "Registered successfully."

    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()

        assert user is not None
        assert user.email == "test@example.com"
        assert user.password_hash != "password123"

def test_signup_missing_credentials(client: FlaskClient):
    payload = {"email": "test@example.com"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Email and password are required."

def test_signup_short_password(client: FlaskClient):
    payload = {"email": "test@example.com", "password": "pass"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Password is too short."

def test_signup_existing_user(client: FlaskClient, app: Flask):
    email="test@example.com"

    with app.app_context():
        existing_user = User(email=email, password_hash="hashedpassword")
        db.session.add(existing_user)
        db.session.commit()

    payload = {"email": email, "password": "password123"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "User already exists."

def test_login_success(client: FlaskClient):
    payload = {"email": "test@example.com", "password": "password123"}
    client.post("/api/signup", json=payload)

    response = client.post("/api/login", json=payload)

    assert response.status_code == 200
    assert response.get_json()["message"] == "Login successful."

def test_login_invalid_credentials(client: FlaskClient):
    client.post("/api/signup", json={"email": "test@example.com", "password": "password123"})

    payload = {"email": "test@example.com", "password": "wrongpassword"}
    response = client.post("/api/login", json=payload)

    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid credentials."

def test_login_missing_credentials(client: FlaskClient):
    client.post("/api/signup", json={"email": "test@example.com", "password": "password123"})

    payload = {"email": "test@example.com"}
    response = client.post("/api/login", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Email and password are required."

def test_login_jwt_cookie(client: FlaskClient):
    payload = {"email": "test@example.com", "password": "password123"}
    client.post("/api/signup", json=payload)

    client.post("/api/login", json=payload)

    cookie = client.get_cookie("access_token")
    
    assert cookie is not None
    assert cookie.key == "access_token"
    assert cookie.http_only is True
    assert cookie.secure is True
    assert cookie.same_site == "Lax"