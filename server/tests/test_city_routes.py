from types import SimpleNamespace

from server.app.models.account import Account, AccountRole
from server.app.models.club import Club
from server.app.models.club_owner import ClubOwner
from server.app.models.club_owner_club import ClubOwnerClub
from server.app.models.team import TeamManager
from server.extensions import db


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def _make_account(app, email: str = "city@test.com") -> int:
    with app.app_context():
        role = AccountRole.query.filter_by(name="team_manager").first()
        if role is None:
            role = AccountRole(name="team_manager")
            db.session.add(role)
            db.session.flush()
        account = Account(
            email=email,
            password_hash="hashed",
            first_name="City",
            last_name="Tester",
            account_role_id=role.id,
            is_verified=True,
        )
        db.session.add(account)
        db.session.commit()
        return account.id


def test_city_search_returns_canonical_labels(client, monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return FakeResponse([
            {
                "name": "Antwerpen",
                "country": "BE",
                "lat": 51.2194,
                "lon": 4.4025,
            },
            {
                "name": "Antwerp",
                "country": "CA",
                "state": "Ontario",
                "lat": 44.2,
                "lon": -76.0,
            },
        ])

    monkeypatch.setattr("server.app.services.city_service.requests.get", fake_get)

    response = client.get("/api/cities/search?q=ant")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["cities"][0]["label"] == "Antwerpen, Belgium"
    assert payload["cities"][1]["label"] == "Antwerp, Canada"


def test_create_club_rejects_non_city_input(client, app, monkeypatch):
    account_id = _make_account(app)
    monkeypatch.setattr("server.app.routes.clubs_routes.verify_user", lambda token: SimpleNamespace(id=account_id))
    monkeypatch.setattr("server.app.routes.clubs_routes.resolve_city_label", lambda value: None)

    response = client.post(
        "/api/clubs",
        json={"name": "No City Club", "city": "Ant"},
    )

    assert response.status_code == 400
    assert "real city" in response.get_json()["message"].lower()


def test_create_club_normalizes_city(client, app, monkeypatch):
    account_id = _make_account(app, "city-create@test.com")
    monkeypatch.setattr("server.app.routes.clubs_routes.verify_user", lambda token: SimpleNamespace(id=account_id))
    monkeypatch.setattr(
        "server.app.routes.clubs_routes.resolve_city_label",
        lambda value: "Antwerpen, Belgium" if value else None,
    )

    response = client.post(
        "/api/clubs",
        json={"name": "City Club", "city": "Antwerp"},
    )

    assert response.status_code == 201

    with app.app_context():
        club = Club.query.filter_by(name="City Club").first()
        assert club is not None
        assert club.city == "Antwerpen, Belgium"


def test_update_club_requires_real_city(client, app, monkeypatch):
    account_id = _make_account(app, "city-update@test.com")
    monkeypatch.setattr("server.app.routes.clubs_routes.get_current_user_id_from_cookie", lambda: account_id)

    with app.app_context():
        club = Club(name="Editable Club", description="test", city="Antwerp", sport_type_id=None)
        db.session.add(club)
        db.session.commit()
        club_id = club.id
        db.session.add(TeamManager(id=account_id))
        db.session.add(ClubOwner(id=account_id))
        db.session.add(ClubOwnerClub(club_owner_id=account_id, club_id=club_id))
        db.session.commit()

    monkeypatch.setattr("server.app.routes.clubs_routes.resolve_city_label", lambda value: None)

    response = client.put(
        f"/api/clubs/{club_id}",
        json={"city": "NotACity"},
    )

    assert response.status_code == 400
    assert "real city" in response.get_json()["message"].lower()
