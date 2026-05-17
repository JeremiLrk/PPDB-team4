import uuid
from flask import Flask
from flask.testing import FlaskClient

from server.app.models.account import Account
from server.app.models.club import Club
from server.app.models.account import TeamManager
from server.app.models.club_owner import ClubOwner
from server.app.models.club_owner_club import ClubOwnerClub
from server.app.services.auth_service import generate_verification_token
from server.extensions import db


def _unique_email() -> str:
    return f"test-{uuid.uuid4()}@example.com"


def _signup_body(email: str, **overrides):
    body = {
        "email": email,
        "password": "password123",
        "firstName": "Test",
        "lastName": "Account",
        "dateOfBirth": "2000-01-01",
        "gender": "male",
        "phoneNumber": "+32 470 99 00 01",
    }
    body.update(overrides)
    return body


# Verifies signup success.
def test_signup_success(client: FlaskClient, app: Flask):
    email = _unique_email()
    payload = _signup_body(
        email,
        gender="female",
        phoneNumber="+32 470 12 34 56",
    )
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 201
    assert response.get_json()["message"] == "Registered successfully. Check your email to verify your account."

    with app.app_context():
        account = Account.query.filter_by(email=email).first()

        assert account is not None
        assert account.email == email
        assert account.password_hash != "password123"
        assert account.first_name == "Test"
        assert account.last_name == "Account"
        assert str(account.date_of_birth) == "2000-01-01"
        assert account.is_verified is True
        assert account.gender == "female"
        assert account.phone == "+32 470 12 34 56"


# Verifies signup invalid gender.
def test_signup_invalid_gender(client: FlaskClient):
    email = _unique_email()
    response = client.post(
        "/api/signup",
        json=_signup_body(email, gender="invalid"),
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "gender must be male, female, or other."


# Verifies signup missing credentials.
def test_signup_missing_credentials(client: FlaskClient):
    email = _unique_email()
    payload = {"email": email}
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Missing credentials."


# Verifies signup short password.
def test_signup_short_password(client: FlaskClient):
    email = _unique_email()
    payload = _signup_body(email, password="pass")
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Password is too short."


# Verifies signup existing user.
def test_signup_existing_user(client: FlaskClient, app: Flask):
    email = _unique_email()

    with app.app_context():
        # Create baseline user through the same API flow to keep required fields consistent.
        response = client.post(
            "/api/signup",
            json=_signup_body(
                email,
                firstName="Existing",
                lastName="User",
            ),
        )
        assert response.status_code == 201

    payload = _signup_body(email)
    response = client.post("/api/signup", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Account already exists."


# Verifies login success.
def test_login_success(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json=_signup_body(email))

    response = client.post("/api/login", json={"email": email, "password": "password123"})

    assert response.status_code == 200
    assert response.get_json()["message"] == "Login successful."


# Verifies login unverified user.
def test_login_unverified_user(client: FlaskClient):
    # New signup flow auto-verifies users, so login should succeed directly.
    email = _unique_email()
    client.post("/api/signup", json=_signup_body(email, lastName="User"))
    response = client.post("/api/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200


# Verifies login invalid credentials.
def test_login_invalid_credentials(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json=_signup_body(email))

    payload = {"email": email, "password": "wrongpassword"}
    response = client.post("/api/login", json=payload)

    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid credentials."


# Verifies login missing credentials.
def test_login_missing_credentials(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json=_signup_body(email))

    payload = {"email": email}
    response = client.post("/api/login", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Email and password are required."


# Verifies login jwt cookie.
def test_login_jwt_cookie(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json=_signup_body(email))

    client.post("/api/login", json={"email": email, "password": "password123"})

    cookie = client.get_cookie("access_token")

    assert cookie is not None
    assert cookie.key == "access_token"
    assert cookie.http_only is True
    assert cookie.secure is True
    assert cookie.same_site == "Lax"

# Verifies logout jwt cookie.
def test_logout_jwt_cookie(client: FlaskClient):
    email = _unique_email()

    client.post("/api/signup", json=_signup_body(email))

    client.post("/api/login", json={"email": email, "password": "password123"})
    cookie = client.get_cookie("access_token")
    assert cookie is not None

    response = client.post("/api/logout")
    assert response.status_code == 200
    assert response.get_json()["message"] == "Successfully logged out."

    cookie = client.get_cookie("access_token")
    assert cookie is None or cookie.value == ""


# Verifies me success.
def test_me_success(client: FlaskClient):
    email = _unique_email()
    client.post("/api/signup", json=_signup_body(email))

    login_response = client.post("/api/login", json={"email": email, "password": "password123"})
    assert login_response.status_code == 200

    response = client.get("/api/me")

    assert response.status_code == 200
    data = response.get_json()
    assert data["account"]["email"] == email
    assert data["account"]["firstName"] == "Test"
    assert data["account"]["lastName"] == "Account"
    assert data["account"]["dateOfBirth"] == "2000-01-01"
    assert data["account"]["gender"] == "male"
    assert data["account"]["phoneNumber"] == "+32 470 99 00 01"
    assert data["account"]["playerTeamIds"] == []


# Verifies patch me profile fields.
def test_patch_me_profile_fields(client: FlaskClient):
    email = _unique_email()
    client.post(
        "/api/signup",
        json=_signup_body(
            email,
            phoneNumber="+32 471 00 11 22",
        ),
    )
    client.post("/api/login", json={"email": email, "password": "password123"})

    response = client.patch(
        "/api/me",
        json={
            "firstName": "Updated",
            "lastName": "Name",
            "dateOfBirth": "1999-05-05",
            "gender": "other",
            "phoneNumber": "+32 2 123 45 67",
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["account"]["firstName"] == "Updated"
    assert body["account"]["lastName"] == "Name"
    assert body["account"]["dateOfBirth"] == "1999-05-05"
    assert body["account"]["gender"] == "other"
    assert body["account"]["phoneNumber"] == "+32 2 123 45 67"

    me = client.get("/api/me")
    assert me.status_code == 200
    acc = me.get_json()["account"]
    assert acc["gender"] == "other"
    assert acc["phoneNumber"] == "+32 2 123 45 67"


# Verifies me unauthorized.
def test_me_unauthorized(client: FlaskClient):
    response = client.get("/api/me")

    assert response.status_code == 401
    assert response.get_json()["message"] == "Unauthorized."
# --- Add these to the bottom of your test file ---

def test_is_manager_true(client: FlaskClient, app: Flask):
    # 1. Create and log in an account (cookie is stored in the test client)
    email = _unique_email()
    client.post(
        "/api/signup",
        json=_signup_body(email, firstName="Manager"),
    )
    login_response = client.post("/api/login", json={"email": email, "password": "password123"})
    assert login_response.status_code == 200

    # 2. Create a club and link this account as club owner in the database.
    with app.app_context():
        account = Account.query.filter_by(email=email).first()
        club = Club(name="The Cool Club", description="Test club", sport="Padel", city="Antwerp")
        db.session.add(club)
        db.session.flush()
        db.session.add(TeamManager(id=account.id))
        db.session.add(ClubOwner(id=account.id))
        db.session.flush()
        db.session.add(ClubOwnerClub(club_owner_id=account.id, club_id=club.id))
        db.session.commit()
        club_id = club.id

    # 3. Ask the API if the logged-in account is a manager
    response = client.get(f"/api/clubs/{club_id}/is_manager")

    # 4. Assert they get a 200 OK and is_manager is true
    assert response.status_code == 200
    assert response.get_json()["is_manager"] is True


# Verifies is manager false.
def test_is_manager_false(client: FlaskClient, app: Flask):
    # 1. Create and log in a account
    email = _unique_email()
    client.post(
        "/api/signup",
        json=_signup_body(email, firstName="Regular"),
    )
    login_response = client.post("/api/login", json={"email": email, "password": "password123"})
    assert login_response.status_code == 200

    # 2. Create a club, but DO NOT assign the account as a manager
    with app.app_context():
        club = Club(name="Another Club", description="Test club", sport="Padel", city="Antwerp")
        db.session.add(club)
        db.session.commit()
        club_id = club.id

    # 3. Ask the API if the logged-in account is a manager
    response = client.get(f"/api/clubs/{club_id}/is_manager")

    # 4. Current API returns 401 when account is not a ClubOwner.
    assert response.status_code == 401


# Verifies is manager unauthorized.
def test_is_manager_unauthorized(client: FlaskClient, app: Flask):
    # 1. Create a club (no account logged in)
    with app.app_context():
        club = Club(name="No Login Club", description="Test club", sport="Padel", city="Antwerp")
        db.session.add(club)
        db.session.commit()
        club_id = club.id

    # 2. Try to hit the endpoint without a cookie
    response = client.get(f"/api/clubs/{club_id}/is_manager")

    # 3. Assert they get a 401 Unauthorized and is_manager is false
    assert response.status_code == 401
    assert response.get_json()["is_manager"] is False


# Verifies verify email invalid token.
def test_verify_email_invalid_token(client: FlaskClient):
    response = client.get("/api/verify-email/invalid-token")

    assert response.status_code == 400
    assert response.get_json()["message"] == "Token is invalid or expired."
