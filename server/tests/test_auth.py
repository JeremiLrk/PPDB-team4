import uuid
from flask import Flask
from flask.testing import FlaskClient
<<<<<<< HEAD

from server.app.models.user import User
from server.extensions import db
=======
from server.app import User, Administrator, db

>>>>>>> e275562 (beetje vanalles)

def _unique_email() -> str:
    return f"test-{uuid.uuid4()}@example.com"

def test_signup_success(client: FlaskClient, app: Flask):
    email = _unique_email()
    payload = {"email": email, "password": "password123", "firstName": "Test", "lastName": "User", "dateOfBirth": "2000-01-01"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 201
    assert response.get_json()["message"] == "Registered successfully."

    with app.app_context():
        user = User.query.filter_by(email=email).first()

        assert user is not None
        assert user.email == email
        assert user.password_hash != "password123"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert str(user.date_of_birth) == "2000-01-01"


def test_signup_missing_credentials(client: FlaskClient):
    email = _unique_email()
    payload = {"email": email}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Missing credentials."


def test_signup_short_password(client: FlaskClient):
    email = _unique_email()
    payload = {"email": email, "password": "pass", "firstName": "Test", "lastName": "User", "dateOfBirth": "2000-01-01"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Password is too short."


def test_signup_existing_user(client: FlaskClient, app: Flask):
    email = _unique_email()

    with app.app_context():
        existing_user = User(email=email, password_hash="hashedpassword")
        db.session.add(existing_user)
        db.session.commit()

    payload = {"email": email, "password": "password123", "firstName": "Test", "lastName": "User", "dateOfBirth": "2000-01-01"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "User already exists."


def test_login_success(client: FlaskClient):
    email = _unique_email()
    signup_payload = {"email": email, "password": "password123", "firstName": "Test", "lastName": "User", "dateOfBirth": "2000-01-01"}
    client.post("/api/signup", json=signup_payload)

    response = client.post("/api/login", json={"email": email, "password": "password123"})

    assert response.status_code == 200
    assert response.get_json()["message"] == "Login successful."


def test_login_invalid_credentials(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json={"email": email, "password": "password123", "firstName": "Test", "lastName": "User", "dateOfBirth": "2000-01-01"})

    payload = {"email": email, "password": "wrongpassword"}
    response = client.post("/api/login", json=payload)

    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid credentials."


def test_login_missing_credentials(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json={"email": email, "password": "password123", "firstName": "Test", "lastName": "User", "dateOfBirth": "2000-01-01"})

    payload = {"email": email}
    response = client.post("/api/login", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Email and password are required."


def test_login_jwt_cookie(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json={"email": email, "password": "password123", "firstName": "Test", "lastName": "User", "dateOfBirth": "2000-01-01"})

    client.post("/api/login", json={"email": email, "password": "password123"})

    cookie = client.get_cookie("access_token")

    assert cookie is not None
    assert cookie.key == "access_token"
    assert cookie.http_only is True
    assert cookie.secure is True
    assert cookie.same_site == "Lax"
<<<<<<< HEAD

def test_logout_jwt_cookie(client: FlaskClient):
    email = _unique_email()

    client.post("/api/signup", json={"email": email, "password": "password123", "firstName": "Test", "lastName": "User", "dateOfBirth": "2000-01-01"})
    client.post("/api/login", json={"email": email, "password": "password123"})
    cookie = client.get_cookie("access_token")
    assert cookie is not None

    response = client.post("/api/logout")
    assert response.status_code == 200
    assert response.get_json()["message"] == "Successfully logged out."

    cookie = client.get_cookie("access_token")
    assert cookie is None or cookie.value == ""


def test_me_success(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup",json={"email": email,"password": "password123","firstName": "Test","lastName": "User","dateOfBirth": "2000-01-01"})

    response = client.get("/api/me")

    assert response.status_code == 200
    data = response.get_json()
    assert data["user"]["email"] == email
    assert data["user"]["firstName"] == "Test"
    assert data["user"]["lastName"] == "User"


def test_me_unauthorized(client: FlaskClient):
    response = client.get("/api/me")

    assert response.status_code == 401
    assert response.get_json()["message"] == "Unauthorized."
=======
"""def test_isAdmin_False(client: FlaskClient, app: Flask):
    email = _unique_email()
    payload = {"email": email, "password": "password123"}
    client.post("/api/signup", json=payload)

    with app.app_context():
        user = User.query.filter_by(email=email).first()
        assert user is not None
        assert user.is_admin() is False
def test_isAdmin_True(client: FlaskClient, app: Flask):
    email = _unique_email()
    payload = {"email": email, "password": "password123"}
    client.post("/api/signup", json=payload)

    with app.app_context():
        user = User.query.filter_by(email=email).first()
        assert user is not None

        # Create an administrator profile for this user
        admin_profile = Administrator(access_level=10)
        user.admin_profile = admin_profile
        db.session.commit()

        assert user.is_admin() is True"""
    
>>>>>>> e275562 (beetje vanalles)
