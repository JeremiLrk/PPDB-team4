"""
Parameterized unit tests for:
  server/app/routes/match_rule/rules.py
  server/app/routes/match_rule/rule_sets.py
  server/app/routes/match_rule/_helpers.py

Authentication is replaced by mock via monkeypatch with verify_user.
"""

import pytest
from unittest.mock import MagicMock, patch
from flask.testing import FlaskClient

from server.extensions import db
from server.app.models.account import Account, AccountRole, Administrator
from server.app.models.match_rule import MatchRule, MatchRuleSet, MatchRuleSetRule
from server.app.routes.match_rule._helpers import (
    _is_owner_of_rule,
    _is_owner_of_rule_set,
    _can_use_rule,
    _can_use_rule_set,
)
from server.tests._authed_client import _authed_client


# ---------------------------------------------------------------------------
# Auxiliary factories
# ---------------------------------------------------------------------------

def _make_account(app, *, email="user@test.com", role_name="team_manager") -> Account:
    """Creates an account with the given role and returns it."""
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


def _make_rule(creator_id=None, *, name="Rule A", description = "", public=True, club_id=None) -> MatchRule:
    rule = MatchRule(
        name=name,
        description=description,
        can_be_used_by_others=public,
        creator_id=creator_id,
        club_id=club_id,
    )
    db.session.add(rule)
    db.session.flush()
    return rule


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


def _login(client: FlaskClient, app, account: Account):
    """Sets a cookie access token, replacing verify user."""
    client.set_cookie("access_token", "fake-token")
    return account


# ===========================================================================
# _helpers.py — unit tests without HTTP
# ===========================================================================

class TestIsOwnerOfRule:
    """_is_owner_of_rule(resolved, rule)"""

    @pytest.mark.parametrize("resolved_type,expected", [
        ("admin",   True),
        ("owner",   True),
        ("other",   False),
    ])
    def test_ownership(self, app, resolved_type, expected):
        with app.app_context():
            acc = _make_account(app, email=f"owner_{resolved_type}@t.com")
            rule = _make_rule(creator_id=acc.id, name=f"Rule_{resolved_type}")

            if resolved_type == "admin":
                resolved = MagicMock(spec=Administrator)
                resolved.__class__ = Administrator
                result = _is_owner_of_rule(resolved, rule)
            elif resolved_type == "owner":
                resolved = MagicMock()
                resolved.id = acc.id
                resolved.__class__ = object  # не Administrator
                result = _is_owner_of_rule(resolved, rule)
            else:
                resolved = MagicMock()
                resolved.id = acc.id + 999
                resolved.__class__ = object
                result = _is_owner_of_rule(resolved, rule)

            assert result is expected
            db.session.rollback()

    def test_no_id_returns_false(self, app):
        with app.app_context():
            rule = MatchRule(name="X", can_be_used_by_others=True, creator_id=None)
            resolved = MagicMock()
            resolved.id = None
            resolved.__class__ = object
            assert _is_owner_of_rule(resolved, rule) is False


class TestCanUseRule:
    """_can_use_rule(resolved, rule)"""

    @pytest.mark.parametrize("is_admin,is_public,is_creator,expected", [
        (True,  False, False, True),   # admin can always
        (False, True,  False, True),   # public rule
        (False, False, True,  True),   # private, but creator
        (False, False, False, False),  # private, someone else's
    ])
    def test_can_use(self, app, is_admin, is_public, is_creator, expected):
        with app.app_context():
            owner_id = 42
            rule = MatchRule(name="R", can_be_used_by_others=is_public, creator_id=owner_id)

            if is_admin:
                resolved = MagicMock(spec=Administrator)
                resolved.__class__ = Administrator
            else:
                resolved = MagicMock()
                resolved.__class__ = object
                resolved.id = owner_id if is_creator else owner_id + 1

            assert _can_use_rule(resolved, rule) is expected


# ===========================================================================
# rules.py — HTTP texts (GET /api/match-rules, GET /<id>, POST, PATCH, DELETE)
# ===========================================================================

class TestGetRule:
    """GET /api/match-rules/<rule_id>"""

    def test_existing_rule_returns_200(self, client, app):
        with app.app_context():
            rule = _make_rule(name="Visible Rule", public=True)
            db.session.commit()
            rule_id = rule.id

        resp = client.get(f"/api/match-rules/{rule_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["rule"]["id"] == rule_id
        assert data["rule"]["name"] == "Visible Rule"

    def test_missing_rule_returns_404(self, client):
        resp = client.get("/api/match-rules/999999")
        assert resp.status_code == 404


class TestGetRules:
    """GET /api/match-rules?from=&to="""

    @pytest.mark.parametrize("from_val,to_val,expected_status", [
        (0,   5,   200),
        (0,   20,  200),
        ("abc", 10, 422),
        (0,   "xyz", 422),
        (-1,  10, 422),
        (10,  5,  422),
    ])
    def test_pagination_validation(self, client, app, from_val, to_val, expected_status):
        with app.app_context():
            db.session.commit()
        resp = client.get(f"/api/match-rules?from={from_val}&to={to_val}")
        assert resp.status_code == expected_status

    def test_returns_only_public_rules(self, client, app):
        with app.app_context():
            acc = _make_account(app, email="pub_owner@t.com")
            _make_rule(creator_id=acc.id, name="Public One", public=True)
            _make_rule(creator_id=acc.id, name="Private One", public=False)
            db.session.commit()

        resp = client.get("/api/match-rules?from=0&to=50")
        assert resp.status_code == 200
        names = [r["name"] for r in resp.get_json()["rules"]]
        assert "Public One" in names
        assert "Private One" not in names

    def test_pagination_fields_present(self, client, app):
        with app.app_context():
            db.session.commit()
        resp = client.get("/api/match-rules?from=0&to=10")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "total" in body and "from" in body and "to" in body and "rules" in body


class TestCreateRule:
    """POST /api/match-rules"""

    def test_unauthenticated_returns_401(self, client):
        resp = client.post("/api/match-rules", json={"name": "New Rule"})
        assert resp.status_code == 401

    def test_no_body_returns_400(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(app, email="cr_400@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post("/api/match-rules", content_type="application/json", data="")
        assert resp.status_code in (400, 401)

    @pytest.mark.parametrize("payload,expected_status", [
        ({"name": ""},           422),
        ({"name": "   "},        422),
        ({"name": "Valid Name"}, 201),
    ])
    def test_create_validation(self, client, app, monkeypatch, payload, expected_status):
        with app.app_context():
            acc = _make_account(app, email=f"cr_{expected_status}_{payload['name'][:3]}@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post("/api/match-rules", json=payload)
        assert resp.status_code == expected_status

    def test_create_rule_persists_fields(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(app, email="cr_persist@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        payload = {"name": "My Rule", "description": "Detail", "canBeUsedByOthers": False}
        resp = client.post("/api/match-rules", json=payload)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["rule"]["name"] == "My Rule"
        assert body["rule"]["canBeUsedByOthers"] is False


class TestDeleteRule:
    """DELETE /api/match-rules/<rule_id>"""

    def test_unauthenticated_returns_401(self, client, app):
        with app.app_context():
            rule = _make_rule(name="Del Unauth")
            db.session.commit()
            rule_id = rule.id

        resp = client.delete(f"/api/match-rules/{rule_id}")
        assert resp.status_code == 401

    def test_not_owner_returns_403(self, client, app, monkeypatch):
        with app.app_context():
            owner = _make_account(app, email="owner_del@t.com")
            other = _make_account(app, email="other_del@t.com")
            rule  = _make_rule(creator_id=owner.id, name="Rule To Del")
            db.session.commit()
            rule_id  = rule.id
            other_id = other.id

        with app.app_context():
            other = Account.query.get(other_id)
            _authed_client(client, monkeypatch, other)

        resp = client.delete(f"/api/match-rules/{rule_id}")
        assert resp.status_code == 403

    def test_owner_can_delete(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(app, email="owner_del_ok@t.com")
            rule = _make_rule(creator_id=acc.id, name="Rule Owner Del")
            db.session.commit()
            rule_id = rule.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.delete(f"/api/match-rules/{rule_id}")
        assert resp.status_code == 200

    def test_nonexistent_rule_returns_404(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(app, email="del_404@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.delete("/api/match-rules/999888")
        assert resp.status_code == 404


class TestRenameRule:
    """PATCH /api/match-rules/<rule_id>/name"""

    @pytest.mark.parametrize("payload,expected_status", [
        ({},                         400),   # empty body
        ({"name": ""},               422),   # empty name
        ({"name": "Same Name"},      422),   # the same name (check separately below)
        ({"name": "Brand New Name"}, 201),
    ])
    def test_rename_validation(self, client, app, monkeypatch, payload, expected_status):
        with app.app_context():
            acc  = _make_account(app, email=f"rn_{expected_status}@t.com")
            rule = _make_rule(creator_id=acc.id, name="Same Name")
            db.session.commit()
            rule_id = rule.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        if not payload:
            resp = client.patch(
                f"/api/match-rules/{rule_id}/name",
                content_type="application/json",
                data="",
            )
        else:
            resp = client.patch(f"/api/match-rules/{rule_id}/name", json=payload)
        assert resp.status_code == expected_status

    def test_non_owner_cannot_rename(self, client, app, monkeypatch):
        with app.app_context():
            owner = _make_account(app, email="rn_owner@t.com")
            other = _make_account(app, email="rn_other@t.com")
            rule  = _make_rule(creator_id=owner.id, name="Protected Rule")
            db.session.commit()
            rule_id  = rule.id
            other_id = other.id

        with app.app_context():
            other = Account.query.get(other_id)
            _authed_client(client, monkeypatch, other)

        resp = client.patch(f"/api/match-rules/{rule_id}/name", json={"name": "Hacked"})
        assert resp.status_code == 403


class TestUpdateRuleDescription:
    """PATCH /api/match-rules/<rule_id>/description"""

    def test_same_description_returns_422(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(app, email="desc_same@t.com")
            rule = _make_rule(creator_id=acc.id, name="Desc Rule", description="old desc")
            db.session.commit()
            rule_id = rule.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.patch(
            f"/api/match-rules/{rule_id}/description",
            json={"description": "old desc"},
        )
        assert resp.status_code == 422

    def test_new_description_returns_200(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(app, email="desc_ok@t.com")
            rule = _make_rule(creator_id=acc.id, name="Desc Rule OK", description = "old")
            db.session.commit()
            rule_id = rule.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.patch(
            f"/api/match-rules/{rule_id}/description",
            json={"description": "new desc"},
        )
        assert resp.status_code == 201
        assert resp.get_json()["rule"]["description"] == "new desc"


# ===========================================================================
# rule_sets.py — HTTP tests
# ===========================================================================

class TestGetRuleSet:
    """GET /api/match-rule-sets/<set_id>"""

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


class TestGetRuleSets:
    """GET /api/match-rule-sets?from=&to="""

    @pytest.mark.parametrize("from_val,to_val,expected_status", [
        (0,  10,   200),
        (0,  20,   200),
        ("x", 10,  422),
        (0,  "y",  422),
        (-1, 10,   422),
        (10, 5,    422),
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


class TestCreateRuleSet:
    """POST /api/match-rule-sets"""

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

    def test_create_persists_fields(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(app, email="crs_persist@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        payload = {"name": "My Set", "description": "A set", "canBeUsedByOthers": False}
        resp = client.post("/api/match-rule-sets", json=payload)
        assert resp.status_code == 201
        body = resp.get_json()["ruleSet"]
        assert body["name"] == "My Set"
        assert body["canBeUsedByOthers"] is False


class TestDeleteRuleSet:
    """DELETE /api/match-rule-sets/<set_id>"""

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


class TestRenameRuleSet:
    """PATCH /api/match-rule-sets/<set_id>/name"""

    @pytest.mark.parametrize("new_name,expected_status", [
        ("",           422),
        ("Same Name",  422),   # that same name — 422
        ("New Name",   200),
    ])
    def test_rename_validation(self, client, app, monkeypatch, new_name, expected_status):
        with app.app_context():
            acc = _make_account(app, email=f"rns_{expected_status}_{new_name[:3]}@t.com")
            rs  = _make_rule_set(creator_id=acc.id, name="Same Name")
            db.session.commit()
            rs_id  = rs.id
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.patch(f"/api/match-rule-sets/{rs_id}/name", json={"name": new_name})
        assert resp.status_code == expected_status


class TestUpdateRuleSetDescription:
    """PATCH /api/match-rule-sets/<set_id>/description"""

    @pytest.mark.parametrize("old_desc,new_desc,expected_status", [
        ("same", "same",    422),
        ("old",  "updated", 200),
        ("old",  "",        200),   # None — different from "old"
    ])
    def test_update_description(self, client, app, monkeypatch,
                                 old_desc, new_desc, expected_status):
        with app.app_context():
            acc = _make_account(app, email=f"rsd_{expected_status}_{old_desc[:2]}@t.com")
            rs  = _make_rule_set(creator_id=acc.id, name=f"Set Desc {old_desc}")
            rs.description = old_desc
            db.session.commit()
            rs_id  = rs.id
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.patch(
            f"/api/match-rule-sets/{rs_id}/description",
            json={"description": new_desc},
        )
        assert resp.status_code == expected_status


class TestAddRuleToSet:
    """POST /api/match-rule-sets/<set_id>/rules"""

    def test_unauthenticated_returns_401(self, client, app):
        with app.app_context():
            rs = _make_rule_set(name="Set Auth")
            db.session.commit()
            rs_id = rs.id
        resp = client.post(f"/api/match-rule-sets/{rs_id}/rules", json={"ruleId": 1})
        assert resp.status_code == 401

    def test_missing_rule_id_returns_422(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(app, email="add_422@t.com")
            rs  = _make_rule_set(creator_id=acc.id, name="Set No RuleId")
            db.session.commit()
            rs_id  = rs.id
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post(f"/api/match-rule-sets/{rs_id}/rules", json={})
        assert resp.status_code == 422

    def test_add_private_rule_of_other_user_returns_403(self, client, app, monkeypatch):
        with app.app_context():
            acc   = _make_account(app, email="add_403@t.com")
            other = _make_account(app, email="add_403_other@t.com")
            rule  = _make_rule(creator_id=other.id, name="Private Rule Other", public=False)
            rs    = _make_rule_set(creator_id=acc.id, name="Set 403")
            db.session.commit()
            rs_id   = rs.id
            rule_id = rule.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post(f"/api/match-rule-sets/{rs_id}/rules", json={"ruleId": rule_id})
        assert resp.status_code == 403

    def test_add_public_rule_returns_201(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(app, email="add_201@t.com")
            rule = _make_rule(creator_id=acc.id, name="Public Add Rule", public=True)
            rs   = _make_rule_set(creator_id=acc.id, name="Set Add 201")
            db.session.commit()
            rs_id   = rs.id
            rule_id = rule.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post(f"/api/match-rule-sets/{rs_id}/rules", json={"ruleId": rule_id})
        assert resp.status_code == 201

    def test_add_duplicate_rule_returns_409(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(app, email="add_409@t.com")
            rule = _make_rule(creator_id=acc.id, name="Dup Rule", public=True)
            rs   = _make_rule_set(creator_id=acc.id, name="Set Dup")
            assoc = MatchRuleSetRule(match_rule_set_id=rs.id, match_rule_id=rule.id)
            db.session.add(assoc)
            db.session.commit()
            rs_id   = rs.id
            rule_id = rule.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post(f"/api/match-rule-sets/{rs_id}/rules", json={"ruleId": rule_id})
        assert resp.status_code == 409


class TestRemoveRuleFromSet:
    """DELETE /api/match-rule-sets/<set_id>/rules/<rule_id>"""

    def test_remove_existing_rule_returns_200(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(app, email="rm_200@t.com")
            rule = _make_rule(creator_id=acc.id, name="Rm Rule")
            rs   = _make_rule_set(creator_id=acc.id, name="Set Rm")
            assoc = MatchRuleSetRule(match_rule_set_id=rs.id, match_rule_id=rule.id)
            db.session.add(assoc)
            db.session.commit()
            rs_id   = rs.id
            rule_id = rule.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.delete(f"/api/match-rule-sets/{rs_id}/rules/{rule_id}")
        assert resp.status_code == 200

    def test_remove_nonexistent_association_returns_404(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(app, email="rm_404@t.com")
            rule = _make_rule(creator_id=acc.id, name="Rm No Assoc Rule")
            rs   = _make_rule_set(creator_id=acc.id, name="Set Rm 404")
            db.session.commit()
            rs_id   = rs.id
            rule_id = rule.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.delete(f"/api/match-rule-sets/{rs_id}/rules/{rule_id}")
        assert resp.status_code == 404

    def test_non_owner_cannot_remove(self, client, app, monkeypatch):
        with app.app_context():
            owner  = _make_account(app, email="rm_403_own@t.com")
            other  = _make_account(app, email="rm_403_oth@t.com")
            rule   = _make_rule(creator_id=owner.id, name="Rm 403 Rule")
            rs     = _make_rule_set(creator_id=owner.id, name="Set Rm 403")
            assoc  = MatchRuleSetRule(match_rule_set_id=rs.id, match_rule_id=rule.id)
            db.session.add(assoc)
            db.session.commit()
            rs_id    = rs.id
            rule_id  = rule.id
            other_id = other.id

        with app.app_context():
            other = Account.query.get(other_id)
            _authed_client(client, monkeypatch, other)

        resp = client.delete(f"/api/match-rule-sets/{rs_id}/rules/{rule_id}")
        assert resp.status_code == 403
