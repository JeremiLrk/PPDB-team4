import uuid
import pytest
from flask import Flask
from flask.testing import FlaskClient

from server.app.models.user import User
from server.extensions import db

def _unique_email() -> str:
    return f"test-{uuid.uuid4()}@example.com"

def test_signup_success(client: FlaskClient, app: Flask):
    email = _unique_email()
    payload = {"email": email, "password": "password123"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 201
    assert response.get_json()["message"] == "Registered successfully."

    with app.app_context():
        user = User.query.filter_by(email=email).first()

        assert user is not None
        assert user.email == email
        assert user.password_hash != "password123"


def test_signup_missing_credentials(client: FlaskClient):
    email = _unique_email()
    payload = {"email": email}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Email and password are required."


def test_signup_short_password(client: FlaskClient):
    email = _unique_email()
    payload = {"email": email, "password": "pass"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Password is too short."


def test_signup_existing_user(client: FlaskClient, app: Flask):
    email = _unique_email()

    with app.app_context():
        existing_user = User(email=email, password_hash="hashedpassword")
        db.session.add(existing_user)
        db.session.commit()

    payload = {"email": email, "password": "password123"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "User already exists."


def test_login_success(client: FlaskClient):
    email = _unique_email()
    payload = {"email": email, "password": "password123"}
    client.post("/api/signup", json=payload)

    response = client.post("/api/login", json=payload)

    assert response.status_code == 200
    assert response.get_json()["message"] == "Login successful."


def test_login_invalid_credentials(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json={"email": email, "password": "password123"})

    payload = {"email": email, "password": "wrongpassword"}
    response = client.post("/api/login", json=payload)

    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid credentials."


def test_login_missing_credentials(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json={"email": email, "password": "password123"})

    payload = {"email": email}
    response = client.post("/api/login", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Email and password are required."


def test_login_jwt_cookie(client: FlaskClient):
    email = _unique_email()
    payload = {"email": email, "password": "password123"}
    client.post("/api/signup", json=payload)

    client.post("/api/login", json=payload)

    cookie = client.get_cookie("access_token")

    assert cookie is not None
    assert cookie.key == "access_token"
    assert cookie.http_only is True
    assert cookie.secure is True
    assert cookie.same_site == "Lax"