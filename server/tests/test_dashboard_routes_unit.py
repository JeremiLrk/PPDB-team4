from types import SimpleNamespace

from flask import Flask

import server.app.routes.dashboard_routes as dashboard_routes


class _QueryStub:
    def __init__(self, result):
        self._result = result

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return self._result


class _ClubOwnerClubQueryStub:
    def filter_by(self, **kwargs):
        return self

    def all(self):
        return []

    def first(self):
        return None


class _ClubPlayerQueryStub:
    def filter_by(self, **kwargs):
        return self

    def all(self):
        return []

    def first(self):
        return None


class _ClubQueryStub:
    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return []


class _ClubOwnerStub:
    query = _ClubOwnerClubQueryStub()


class _ClubPlayerStub:
    query = _ClubPlayerQueryStub()


class _ClubStub:
    query = _ClubQueryStub()


class _JoinRequestStub:
    query = _ClubPlayerQueryStub()


def test_get_my_dashboard_returns_401_when_cookie_user_missing():
    app = Flask(__name__)
    with app.test_request_context("/api/me/dashboard"):
        response, status = dashboard_routes.get_my_dashboard()

    assert status == 401
    assert response.get_json()["message"] == "Unauthorized"


def test_get_my_dashboard_returns_404_when_account_missing(monkeypatch):
    app = Flask(__name__)
    monkeypatch.setattr(dashboard_routes, "_get_current_user_id_from_cookie", lambda: 101)
    monkeypatch.setattr(
        dashboard_routes,
        "Account",
        SimpleNamespace(query=_QueryStub(None)),
    )

    with app.test_request_context("/api/me/dashboard"):
        response, status = dashboard_routes.get_my_dashboard()

    assert status == 404
    assert response.get_json()["message"] == "Account not found"


def test_get_my_dashboard_returns_payload_when_account_exists(monkeypatch):
    app = Flask(__name__)
    fake_user = SimpleNamespace(id=7, email="demo@netrank.test", role="user")

    monkeypatch.setattr(dashboard_routes, "_get_current_user_id_from_cookie", lambda: 7)
    monkeypatch.setattr(
        dashboard_routes,
        "Account",
        SimpleNamespace(query=_QueryStub(fake_user)),
    )
    monkeypatch.setattr(dashboard_routes, "ClubOwner", _ClubOwnerStub)
    monkeypatch.setattr(dashboard_routes, "ClubOwnerClub", SimpleNamespace(query=_ClubOwnerClubQueryStub()))
    monkeypatch.setattr(dashboard_routes, "ClubPlayer", _ClubPlayerStub)
    monkeypatch.setattr(dashboard_routes, "Club", _ClubStub)
    monkeypatch.setattr(dashboard_routes, "ClubJoinRequest", _JoinRequestStub)

    with app.test_request_context("/api/me/dashboard"):
        response, status = dashboard_routes.get_my_dashboard()

    payload = response.get_json()
    assert status == 200
    assert payload["account"] == {"id": 7, "email": "demo@netrank.test"}
    assert payload["roles"] == ["user"]
    assert payload["clubs"] == []
    assert payload["pending_requests"] == {
        "my_requests": [],
        "my_club_creation_requests": [],
    }
