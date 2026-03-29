import uuid
from flask import Flask
from flask.testing import FlaskClient

from server.app.models.account import Account
from server.extensions import db


def _unique_email() -> str:
    return f"test-{uuid.uuid4()}@example.com"

def test_signup_success(client: FlaskClient, app: Flask):
    email = _unique_email()
    payload = {"email": email, "password": "password123", "firstName": "Test", "lastName": "Account", "dateOfBirth": "2000-01-01"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 201
    assert response.get_json()["message"] == "Registered successfully."

    with app.app_context():
        account = Account.query.filter_by(email=email).first()

        assert account is not None
        assert account.email == email
        assert account.password_hash != "password123"
        assert account.first_name == "Test"
        assert account.last_name == "Account"
        assert str(account.date_of_birth) == "2000-01-01"


def test_signup_missing_credentials(client: FlaskClient):
    email = _unique_email()
    payload = {"email": email}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Missing credentials."


def test_signup_short_password(client: FlaskClient):
    email = _unique_email()
    payload = {"email": email, "password": "pass", "firstName": "Test", "lastName": "Account", "dateOfBirth": "2000-01-01"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Password is too short."


def test_signup_existing_user(client: FlaskClient, app: Flask):
    email = _unique_email()

    with app.app_context():
        existing_user = Account(email=email, password_hash="hashedpassword")
        db.session.add(existing_user)
        db.session.commit()

    payload = {"email": email, "password": "password123", "firstName": "Test", "lastName": "Account", "dateOfBirth": "2000-01-01"}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Account already exists."


def test_login_success(client: FlaskClient):
    email = _unique_email()
    signup_payload = {"email": email, "password": "password123", "firstName": "Test", "lastName": "Account", "dateOfBirth": "2000-01-01"}
    client.post("/api/signup", json=signup_payload)

    response = client.post("/api/login", json={"email": email, "password": "password123"})

    assert response.status_code == 200
    assert response.get_json()["message"] == "Login successful."


def test_login_invalid_credentials(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json={"email": email, "password": "password123", "firstName": "Test", "lastName": "Account", "dateOfBirth": "2000-01-01"})

    payload = {"email": email, "password": "wrongpassword"}
    response = client.post("/api/login", json=payload)

    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid credentials."


def test_login_missing_credentials(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json={"email": email, "password": "password123", "firstName": "Test", "lastName": "Account", "dateOfBirth": "2000-01-01"})

    payload = {"email": email}
    response = client.post("/api/login", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Email and password are required."


def test_login_jwt_cookie(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json={"email": email, "password": "password123", "firstName": "Test", "lastName": "Account", "dateOfBirth": "2000-01-01"})

    client.post("/api/login", json={"email": email, "password": "password123"})

    cookie = client.get_cookie("access_token")

    assert cookie is not None
    assert cookie.key == "access_token"
    assert cookie.http_only is True
    assert cookie.secure is True
    assert cookie.same_site == "Lax"

def test_logout_jwt_cookie(client: FlaskClient):
    email = _unique_email()

    client.post("/api/signup", json={"email": email, "password": "password123", "firstName": "Test", "lastName": "Account", "dateOfBirth": "2000-01-01"})
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
    client.post("/api/signup",json={"email": email,"password": "password123","firstName": "Test","lastName": "Account","dateOfBirth": "2000-01-01"})

    response = client.get("/api/me")

    assert response.status_code == 200
    data = response.get_json()
    assert data["account"]["email"] == email
    assert data["account"]["firstName"] == "Test"
    assert data["account"]["lastName"] == "Account"


def test_me_unauthorized(client: FlaskClient):
    response = client.get("/api/me")

    assert response.status_code == 401
    assert response.get_json()["message"] == "Unauthorized."
# --- Add these to the bottom of your test file ---

def test_is_manager_true(client: FlaskClient, app: Flask):
    # 1. Create and log in a account (the cookie will be saved in the client)
    email = _unique_email()
    client.post("/api/signup", json={
        "email": email, "password": "password123", 
        "firstName": "Manager", "lastName": "Account", "dateOfBirth": "2000-01-01"
    })

    # 2. Create a club and assign this account as a manager in the database
    with app.app_context():
        account = Account.query.filter_by(email=email).first()
        club = Club(name="The Cool Club")
        club.managers.append(account) # Links the account to the club via our many-to-many relationship
        db.session.add(club)
        db.session.commit()
        club_id = club.id

    # 3. Ask the API if the logged-in account is a manager
    response = client.get(f"/api/clubs/{club_id}/is_manager")

    # 4. Assert they get a 200 OK and is_manager is true
    assert response.status_code == 200
    assert response.get_json()["is_manager"] is True


def test_is_manager_false(client: FlaskClient, app: Flask):
    # 1. Create and log in a account
    email = _unique_email()
    client.post("/api/signup", json={
        "email": email, "password": "password123", 
        "firstName": "Regular", "lastName": "Account", "dateOfBirth": "2000-01-01"
    })

    # 2. Create a club, but DO NOT assign the account as a manager
    with app.app_context():
        club = Club(name="Another Club")
        db.session.add(club)
        db.session.commit()
        club_id = club.id

    # 3. Ask the API if the logged-in account is a manager
    response = client.get(f"/api/clubs/{club_id}/is_manager")

    # 4. Assert they get a 200 OK and is_manager is false
    assert response.status_code == 200
    assert response.get_json()["is_manager"] is False


def test_is_manager_unauthorized(client: FlaskClient, app: Flask):
    # 1. Create a club (no account logged in)
    with app.app_context():
        club = Club(name="No Login Club")
        db.session.add(club)
        db.session.commit()
        club_id = club.id

    # 2. Try to hit the endpoint without a cookie
    response = client.get(f"/api/clubs/{club_id}/is_manager")

    # 3. Assert they get a 401 Unauthorized and is_manager is false
    assert response.status_code == 401
    assert response.get_json()["is_manager"] is False