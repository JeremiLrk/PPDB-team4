"""
Tests for the structured match-ruleset system:
  server/app/routes/match_rule/rule_sets.py
"""

import pytest
from flask.testing import FlaskClient

from server.extensions import db
from server.app.models.account import Account, AccountRole
from server.app.models.match_rule import MatchRuleSet
from server.tests._authed_client import _authed_client


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

def _make_account(app, *, email="user@test.com", role_name="team_manager") -> Account:
    role = AccountRole.query.filter_by(name=role_name).first()
    if not role:
        role = AccountRole(name=role_name)
        db.session.add(role)
        db.session.flush()
    acc = Account(
        email=email,
        password_hash="hashed",
        first_name="Test",
        last_name="User",
        account_role_id=role.id,
        is_verified=True,
    )
    db.session.add(acc)
    db.session.flush()
    return acc


def _make_rule_set(creator_id=None, *, name="Set A", public=True, club_id=None) -> MatchRuleSet:
    rs = MatchRuleSet(
        name=name,
        description="desc",
        can_be_used_by_others=public,
        creator_id=creator_id,
        club_id=club_id,
    )
    db.session.add(rs)
    db.session.flush()
    return rs


# ===========================================================================
# GET /api/match-rule-sets/<set_id>
# ===========================================================================

class TestGetRuleSet:
    def test_existing_set_returns_200(self, client, app):
        with app.app_context():
            rs = _make_rule_set(name="Public Set")
            db.session.commit()
            rs_id = rs.id

        resp = client.get(f"/api/match-rule-sets/{rs_id}")
        assert resp.status_code == 200
        assert resp.get_json()["ruleSet"]["id"] == rs_id

    def test_missing_set_returns_404(self, client):
        resp = client.get("/api/match-rule-sets/999999")
        assert resp.status_code == 404

    def test_response_contains_structured_fields(self, client, app):
        with app.app_context():
            rs = _make_rule_set(name="Structured Set")
            db.session.commit()
            rs_id = rs.id

        body = client.get(f"/api/match-rule-sets/{rs_id}").get_json()["ruleSet"]
        for field in ("matchFormat", "thirdSetFormat", "deuceRule", "gameFormat"):
            assert field in body


# ===========================================================================
# GET /api/match-rule-sets
# ===========================================================================

class TestGetRuleSets:
    @pytest.mark.parametrize("from_val,to_val,expected_status", [
        (0,    10,  200),
        (0,    20,  200),
        ("x",  10,  422),
        (0,   "y",  422),
        (-1,   10,  422),
        (10,    5,  422),
    ])
    def test_pagination_validation(self, client, app, from_val, to_val, expected_status):
        with app.app_context():
            db.session.commit()
        resp = client.get(f"/api/match-rule-sets?from={from_val}&to={to_val}")
        assert resp.status_code == expected_status

    def test_only_public_sets_returned(self, client, app):
        with app.app_context():
            acc = _make_account(app, email="sets_pub@t.com")
            _make_rule_set(creator_id=acc.id, name="Set Public",  public=True)
            _make_rule_set(creator_id=acc.id, name="Set Private", public=False)
            db.session.commit()

        resp = client.get("/api/match-rule-sets?from=0&to=50")
        assert resp.status_code == 200
        names = [rs["name"] for rs in resp.get_json()["ruleSets"]]
        assert "Set Public" in names
        assert "Set Private" not in names


# ===========================================================================
# POST /api/match-rule-sets
# ===========================================================================

class TestCreateRuleSet:
    def test_unauthenticated_returns_401(self, client):
        resp = client.post("/api/match-rule-sets", json={"name": "New Set"})
        assert resp.status_code == 401

    @pytest.mark.parametrize("payload,expected_status", [
        ({"name": ""},          422),
        ({"name": "Valid Set"}, 201),
    ])
    def test_create_validation(self, client, app, monkeypatch, payload, expected_status):
        with app.app_context():
            acc = _make_account(app, email=f"crs_{expected_status}@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post("/api/match-rule-sets", json=payload)
        assert resp.status_code == expected_status

    def test_create_persists_structured_fields(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(app, email="crs_persist@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        payload = {
            "name":           "Padel Competitie",
            "matchFormat":    "best_of_3",
            "thirdSetFormat": "super_tiebreak",
            "deuceRule":      "golden_point",
            "gameFormat":     "doubles",
            "canBeUsedByOthers": False,
        }
        resp = client.post("/api/match-rule-sets", json=payload)
        assert resp.status_code == 201
        body = resp.get_json()["ruleSet"]
        assert body["name"]           == "Padel Competitie"
        assert body["deuceRule"]      == "golden_point"
        assert body["gameFormat"]     == "doubles"
        assert body["canBeUsedByOthers"] is False

    def test_timed_format_requires_duration(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(app, email="timed_422@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post("/api/match-rule-sets", json={"name": "Timed No Duration", "matchFormat": "timed"})
        assert resp.status_code == 422

    def test_timed_format_with_duration_succeeds(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(app, email="timed_201@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        payload = {"name": "60 Min Tennis", "matchFormat": "timed", "timedDurationMinutes": 60}
        resp = client.post("/api/match-rule-sets", json=payload)
        assert resp.status_code == 201
        assert resp.get_json()["ruleSet"]["timedDurationMinutes"] == 60

    @pytest.mark.parametrize("invalid_format", ["best_of_5", "shootout", ""])
    def test_invalid_match_format_returns_422(self, client, app, monkeypatch, invalid_format):
        with app.app_context():
            acc = _make_account(app, email=f"inv_fmt_{invalid_format[:3]}@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post("/api/match-rule-sets", json={"name": "X", "matchFormat": invalid_format})
        assert resp.status_code == 422


# ===========================================================================
# PUT /api/match-rule-sets/<set_id>
# ===========================================================================

class TestUpdateRuleSet:
    def test_owner_can_update(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(app, email="upd_ok@t.com")
            rs  = _make_rule_set(creator_id=acc.id, name="Old Name")
            db.session.commit()
            rs_id  = rs.id
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        payload = {
            "name":        "New Name",
            "deuceRule":   "golden_point",
            "gameFormat":  "singles",
        }
        resp = client.put(f"/api/match-rule-sets/{rs_id}", json=payload)
        assert resp.status_code == 200
        body = resp.get_json()["ruleSet"]
        assert body["name"]      == "New Name"
        assert body["deuceRule"] == "golden_point"

    def test_non_owner_cannot_update(self, client, app, monkeypatch):
        with app.app_context():
            owner = _make_account(app, email="upd_own@t.com")
            other = _make_account(app, email="upd_oth@t.com")
            rs    = _make_rule_set(creator_id=owner.id, name="Protected")
            db.session.commit()
            rs_id    = rs.id
            other_id = other.id

        with app.app_context():
            other = Account.query.get(other_id)
            _authed_client(client, monkeypatch, other)

        resp = client.put(f"/api/match-rule-sets/{rs_id}", json={"name": "Hacked"})
        assert resp.status_code == 403


# ===========================================================================
# DELETE /api/match-rule-sets/<set_id>
# ===========================================================================

class TestDeleteRuleSet:
    @pytest.mark.parametrize("is_owner,expected_status", [
        (True,  200),
        (False, 403),
    ])
    def test_delete_permissions(self, client, app, monkeypatch, is_owner, expected_status):
        with app.app_context():
            owner  = _make_account(app, email=f"rs_del_own_{is_owner}@t.com")
            other  = _make_account(app, email=f"rs_del_oth_{is_owner}@t.com")
            rs     = _make_rule_set(creator_id=owner.id, name=f"Del Set {is_owner}")
            db.session.commit()
            rs_id    = rs.id
            actor_id = owner.id if is_owner else other.id

        with app.app_context():
            actor = Account.query.get(actor_id)
            _authed_client(client, monkeypatch, actor)

        resp = client.delete(f"/api/match-rule-sets/{rs_id}")
        assert resp.status_code == expected_status

    def test_delete_missing_set_returns_404(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(app, email="rs_del_404@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.delete("/api/match-rule-sets/999777")
        assert resp.status_code == 404
