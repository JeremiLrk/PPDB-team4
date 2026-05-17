"""
Parameterized unit tests for:
  server/app/routes/team/core.py
  server/app/routes/team/membership.py
  server/app/routes/team/my_teams.py
  server/app/routes/team/_helpers.py
  server/app/routes/team/_permissions.py

Approach: Flask test client (PostgreSQL via conftest) + monkeypatch verify_user.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from flask.testing import FlaskClient

from server.extensions import db
from server.app.models.account import Account, AccountRole, Administrator
from server.app.models.team import Team, TeamManager, TeamManagerTeam
from server.app.models.player import Player, PlayerTeam
from server.app.models.team_join_request import TeamJoinRequest
from server.app.models.club_owner import ClubOwner

from server.app.routes.team._permissions import (
    can_rename,
    can_delete,
    can_edit_players,
    can_edit_managers,
    is_admin,
    is_owner_of_team_club,
    get_permissions,
)
from server.app.routes.team._helpers import parse_pagination, search_accounts
from server.tests._authed_client import _authed_client
from server.tests.team.factories import _make_team, _make_account, _make_team_manager, _make_assoc


# ===========================================================================
# _permissions.py — unit tests without HTTP
# ===========================================================================

class TestIsAdmin:
    """is_admin(resolved)"""

    # Verifies the administrator check returns true.
    def test_administrator_returns_true(self, app):
        with app.app_context():
            admin = MagicMock(spec=Administrator)
            admin.__class__ = Administrator
            assert is_admin(admin) is True

    # Verifies the non-admin check returns false.
    def test_non_admin_returns_false(self, app):
        with app.app_context():
            owner = MagicMock(spec=ClubOwner)
            owner.__class__ = ClubOwner
            assert is_admin(owner) is False

            tm = MagicMock(spec=TeamManager)
            tm.__class__ = TeamManager
            assert is_admin(tm) is False


class TestIsOwnerOfTeamClub:
    """is_owner_of_team_club(resolved, team)"""

    # Verifies club owner with matching club is true.
    def test_club_owner_with_matching_club_is_true(self, app):
        with app.app_context():
            from server.app.models.club import Club
            club = Club(name="Test Club Perm", description="test", city="Test city")
            db.session.add(club)
            db.session.flush()
            team = _make_team(name="Club Perm Team", club_id=club.id)
            team.club = club

            owner = MagicMock(spec=ClubOwner)
            owner.__class__ = ClubOwner
            owner.clubs = [club]
            assert is_owner_of_team_club(owner, team) is True
            db.session.rollback()

    # Verifies club owner of different club is false.
    def test_club_owner_of_different_club_is_false(self, app):
        with app.app_context():
            from server.app.models.club import Club
            club1 = Club(name="Club Owner Has", description="test", city="Test city")
            club2 = Club(name="Club Team Has",  description="test", city="Test city")
            db.session.add_all([club1, club2])
            db.session.flush()
            team = _make_team(name="Not My Club Team", club_id=club2.id)
            team.club = club2

            owner = MagicMock(spec=ClubOwner)
            owner.__class__ = ClubOwner
            owner.clubs = [club1]
            assert is_owner_of_team_club(owner, team) is False
            db.session.rollback()

    # Verifies team without club is false.
    def test_team_without_club_is_false(self, app):
        with app.app_context():
            team = _make_team(name="No Club Team")
            team.club = None

            owner = MagicMock(spec=ClubOwner)
            owner.__class__ = ClubOwner
            owner.clubs = []
            assert is_owner_of_team_club(owner, team) is False
            db.session.rollback()

    # Verifies administrator is false.
    def test_administrator_is_false(self, app):
        """is_owner_of_team_club is strictly about ClubOwner — admins are handled separately."""
        with app.app_context():
            team = _make_team(name="Admin Club Check")
            admin = MagicMock(spec=Administrator)
            admin.__class__ = Administrator
            assert is_owner_of_team_club(admin, team) is False
            db.session.rollback()

    # Verifies club owner of other club falls through to manager perms.
    def test_club_owner_of_other_club_falls_through_to_manager_perms(self, app):
        """
        ClubOwner who does NOT own this team's club should fall through
        to their TeamManager association rights — not be hard-blocked.

        ClubOwner is NOT a Python subclass of TeamManager (shared-PK joined table),
        so _permissions.py delegates via resolved.team_manager back-reference.
        We use real DB objects to avoid MRO issues with MagicMock.
        """
        with app.app_context():
            from server.app.models.club import Club
            from server.app.models.club_owner import ClubOwner as RealClubOwner
            from server.app.models.club_owner_club import ClubOwnerClub

            club1 = Club(name="Owner Club CO", description="test", city="Test city")
            club2 = Club(name="Team Club CO",  description="test", city="Test city")
            db.session.add_all([club1, club2])
            db.session.flush()

            # Account -> TeamManager -> ClubOwner (real DB chain)
            acc = _make_account(email="co_fallthrough@t.com")
            tm  = _make_team_manager(acc)
            co  = RealClubOwner(id=tm.id)
            db.session.add(co)
            db.session.flush()

            # ClubOwner owns club1, NOT club2
            co_club = ClubOwnerClub(club_owner_id=co.id, club_id=club1.id)
            db.session.add(co_club)
            db.session.flush()

            # Team belongs to club2
            team = _make_team(name="CO Fallthrough Team", club_id=club2.id)
            db.session.flush()
            # Attach the real Club object so team.club is not None
            team.club = club2

            # Give the underlying TeamManager granular rights on this team
            _make_assoc(tm, team, can_rename=True, can_delete=False,
                        can_edit_players=True, can_edit_managers=False)

            # Expire all cached state so relationships load fresh from DB
            db.session.expire_all()
            co   = db.session.get(RealClubOwner, tm.id)
            team = db.session.get(Team, team.id)

            # Sanity: co is a ClubOwner that owns club1 but NOT club2
            assert is_owner_of_team_club(co, team) is False

            # Falls through to TeamManager association rights
            assert can_rename(co, team)        is True
            assert can_delete(co, team)        is False
            assert can_edit_players(co, team)  is True
            assert can_edit_managers(co, team) is False
            db.session.rollback()


class TestCanPermissions:
    """can_rename / can_delete / can_edit_players / can_edit_managers"""

    @pytest.mark.parametrize("perm_fn,assoc_kwarg,other_kw", [
        (can_rename,        "can_rename",        {"can_delete": False, "can_edit_players": False, "can_edit_managers": False}),
        (can_delete,        "can_delete",        {"can_rename": False, "can_edit_players": False, "can_edit_managers": False}),
        (can_edit_players,  "can_edit_players",  {"can_rename": False, "can_delete": False, "can_edit_managers": False}),
        (can_edit_managers, "can_edit_managers", {"can_rename": False, "can_delete": False, "can_edit_players": False}),
    ])
    # Verifies team manager flag respected.
    def test_team_manager_flag_respected(self, app, perm_fn, assoc_kwarg, other_kw):
        with app.app_context():
            acc  = _make_account(email=f"perm_{assoc_kwarg}@t.com")
            tm   = _make_team_manager(acc)
            team = _make_team(name=f"Perm Team {assoc_kwarg}")
            _make_assoc(tm, team, **{assoc_kwarg: True}, **other_kw)
            db.session.refresh(tm)

            assert perm_fn(tm, team) is True

            assoc = next(a for a in tm.team_associations if a.team_id == team.id)
            setattr(assoc, assoc_kwarg, False)
            db.session.flush()
            db.session.refresh(tm)

            assert perm_fn(tm, team) is False
            db.session.rollback()

    # Verifies admin always can.
    def test_admin_always_can(self, app):
        with app.app_context():
            team = _make_team(name="Admin Perm Team")
            admin = MagicMock(spec=Administrator)
            admin.__class__ = Administrator
            assert can_rename(admin, team) is True
            assert can_delete(admin, team) is True
            assert can_edit_players(admin, team) is True
            assert can_edit_managers(admin, team) is True
            db.session.rollback()

    # Verifies unknown role cannot.
    def test_unknown_role_cannot(self, app):
        with app.app_context():
            team = _make_team(name="Unknown Role Team")
            unknown = MagicMock()
            unknown.__class__ = object
            assert can_rename(unknown, team) is False
            assert can_delete(unknown, team) is False
            db.session.rollback()


class TestGetPermissions:
    """get_permissions(resolved, team) -> dict"""

    # Verifies admin gets all true.
    def test_admin_gets_all_true(self, app):
        with app.app_context():
            team  = _make_team(name="Perms Dict Team")
            admin = MagicMock(spec=Administrator)
            admin.__class__ = Administrator
            perms = get_permissions(admin, team)
            assert all(perms.values())
            db.session.rollback()

    # Verifies no assoc gets all false.
    def test_no_assoc_gets_all_false(self, app):
        with app.app_context():
            acc  = _make_account(email="noassoc@t.com")
            tm   = _make_team_manager(acc)
            team = _make_team(name="No Assoc Team")
            db.session.refresh(tm)
            perms = get_permissions(tm, team)
            assert not any(perms.values())
            db.session.rollback()

    # Verifies partial permissions.
    def test_partial_permissions(self, app):
        with app.app_context():
            acc  = _make_account(email="partial_perm@t.com")
            tm   = _make_team_manager(acc)
            team = _make_team(name="Partial Perm Team")
            _make_assoc(tm, team,
                        can_rename=True, can_delete=False,
                        can_edit_players=True, can_edit_managers=False)
            db.session.refresh(tm)
            perms = get_permissions(tm, team)
            assert perms["canRename"] is True
            assert perms["canDelete"] is False
            assert perms["canEditPlayers"] is True
            assert perms["canEditManagers"] is False
            db.session.rollback()


# ===========================================================================
# _helpers.py unit tests
# ===========================================================================

class TestParseHelpers:
    """parse_pagination — direct validation without HTTP."""

    @pytest.mark.parametrize("from_v,to_v,sort_v,ok", [
        ("0",  "20", "id",   True),
        ("5",  "15", "name", True),
        ("abc","10", "id",   False),
        ("0",  "abc","id",   False),
        ("-1", "10", "id",   False),
        ("10", "5",  "id",   False),
        ("0",  "10", "rating", False),
    ])
    # Verifies pagination via get.
    def test_pagination_via_get(self, client, app, from_v, to_v, sort_v, ok):
        resp = client.get(f"/api/teams?from={from_v}&to={to_v}&sort={sort_v}")
        if ok:
            assert resp.status_code == 200
        else:
            assert resp.status_code == 422


# ===========================================================================
# core.py — HTTP tests
# ===========================================================================

class TestGetTeam:
    """GET /api/teams/<team_id>"""

    # Verifies the endpoint returns 200 for an existing team.
    def test_existing_team_returns_200(self, client, app):
        with app.app_context():
            team = _make_team(name="Visible Team")
            db.session.commit()
            team_id = team.id

        resp = client.get(f"/api/teams/{team_id}")
        assert resp.status_code == 200
        assert resp.get_json()["team"]["id"] == team_id

    # Verifies the endpoint returns 404 when the team is missing.
    def test_missing_team_returns_404(self, client):
        resp = client.get("/api/teams/999999")
        assert resp.status_code == 404


class TestGetTeams:
    """GET /api/teams?from=&to=&sort="""

    @pytest.mark.parametrize("params,expected_status", [
        ("from=0&to=20",          200),
        ("from=0&to=20&sort=name",200),
        ("from=abc&to=10",        422),
        ("from=0&to=xyz",         422),
        ("from=-1&to=10",         422),
        ("from=10&to=5",          422),
        ("from=0&to=10&sort=bad", 422),
    ])
    # Verifies pagination and sort.
    def test_pagination_and_sort(self, client, app, params, expected_status):
        with app.app_context():
            db.session.commit()
        resp = client.get(f"/api/teams?{params}")
        assert resp.status_code == expected_status

    # Verifies response shape.
    def test_response_shape(self, client, app):
        with app.app_context():
            db.session.commit()
        resp = client.get("/api/teams?from=0&to=5")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "total" in body and "teams" in body


class TestGetTeamsByClub:
    """GET /api/teams/by-club/<club_id>"""

    # Verifies the endpoint returns 404 when the club is missing.
    def test_missing_club_returns_404(self, client):
        resp = client.get("/api/teams/by-club/999999")
        assert resp.status_code == 404

    # Verifies the endpoint returns 200 for an existing club.
    def test_existing_club_returns_200(self, client, app):
        with app.app_context():
            from server.app.models.club import Club
            club = Club(
                name="Test Club By",
                description="test",
                city="Test city"
            )
            db.session.add(club)
            db.session.commit()
            club_id = club.id

        resp = client.get(f"/api/teams/by-club/{club_id}")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["clubId"] == club_id


class TestCreateTeam:
    """POST /api/teams"""

    # Verifies the endpoint returns 401 when the caller is not authenticated.
    def test_unauthenticated_returns_401(self, client):
        resp = client.post("/api/teams", json={"name": "Team X"})
        assert resp.status_code == 401

    @pytest.mark.parametrize("payload,expected_status", [
        ({},              400),
        ({"name": ""},    422),
        ({"name": "  "}, 422),
        ({"name": "OK"},  201),
    ])
    # Verifies create validation.
    def test_create_validation(self, client, app, monkeypatch, payload, expected_status):
        with app.app_context():
            acc = _make_account(email=f"ct_{expected_status}_{str(payload)[:5]}@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        if not payload:
            resp = client.post("/api/teams", content_type="application/json", data="")
        else:
            resp = client.post("/api/teams", json=payload)
        assert resp.status_code == expected_status

    # Verifies the created team persists the name.
    def test_create_persists_name(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(email="ct_persist@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post("/api/teams", json={"name": "Persisted Team"})
        assert resp.status_code == 201
        assert resp.get_json()["team"]["name"] == "Persisted Team"


class TestDeleteTeam:
    """DELETE /api/teams/<team_id>"""

    # Verifies the endpoint returns 401 when the caller is not authenticated.
    def test_unauthenticated_returns_401(self, client, app):
        with app.app_context():
            team = _make_team(name="Del Team Auth")
            db.session.commit()
            team_id = team.id
        resp = client.delete(f"/api/teams/{team_id}")
        assert resp.status_code == 401

    # Verifies the endpoint returns 403 without permission.
    def test_no_permission_returns_403(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(email="del_403@t.com")
            tm   = _make_team_manager(acc)
            team = _make_team(name="Del No Perm Team")
            _make_assoc(tm, team, can_delete=False)
            db.session.commit()
            team_id = team.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.delete(f"/api/teams/{team_id}")
        assert resp.status_code == 403

    # Verifies the owner can delete the team.
    def test_owner_can_delete(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(email="del_200@t.com")
            tm   = _make_team_manager(acc)
            team = _make_team(name="Del OK Team")
            _make_assoc(tm, team, can_delete=True)
            db.session.commit()
            team_id = team.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.delete(f"/api/teams/{team_id}")
        assert resp.status_code == 200

    # Verifies the endpoint returns 404 when the team is missing.
    def test_missing_team_returns_404(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(email="del_404_team@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.delete("/api/teams/9988776")
        assert resp.status_code == 404


class TestRenameTeam:
    """PATCH /api/teams/<team_id>"""

    @pytest.mark.parametrize("new_name,expected_status", [
        ("",             422),
        ("Old Name",     422),
        ("New Name",     200),
    ])
    # Verifies rename validation.
    def test_rename_validation(self, client, app, monkeypatch, new_name, expected_status):
        with app.app_context():
            acc  = _make_account(email=f"rnt_{expected_status}_{new_name[:3]}@t.com")
            tm   = _make_team_manager(acc)
            team = _make_team(name="Old Name")
            _make_assoc(tm, team, can_rename=True)
            db.session.commit()
            team_id = team.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.patch(f"/api/teams/{team_id}", json={"name": new_name})
        assert resp.status_code == expected_status

    # Verifies the endpoint returns 403 without rename permission.
    def test_no_rename_permission_returns_403(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(email="rnt_403@t.com")
            tm   = _make_team_manager(acc)
            team = _make_team(name="Locked Name")
            _make_assoc(tm, team, can_rename=False)
            db.session.commit()
            team_id = team.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.patch(f"/api/teams/{team_id}", json={"name": "New Name"})
        assert resp.status_code == 403


# ===========================================================================
# membership.py — HTTP tests
# ===========================================================================

class TestGetTeamPlayers:
    """GET /api/teams/<team_id>/players"""

    # Verifies the endpoint returns 404 when the team is missing.
    def test_missing_team_returns_404(self, client):
        resp = client.get("/api/teams/999999/players")
        assert resp.status_code == 404

    # Verifies the endpoint returns the players list.
    def test_returns_players_list(self, client, app):
        with app.app_context():
            team = _make_team(name="Players Team")
            db.session.commit()
            team_id = team.id

        resp = client.get(f"/api/teams/{team_id}/players")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "players" in body
        assert body["teamId"] == team_id


class TestAddPlayerToTeam:
    """POST /api/teams/<team_id>/players"""

    # Verifies the endpoint returns 401 when the caller is not authenticated.
    def test_unauthenticated_returns_401(self, client, app):
        with app.app_context():
            team = _make_team(name="Add Player Auth")
            db.session.commit()
            team_id = team.id
        resp = client.post(f"/api/teams/{team_id}/players", json={"accountId": 1})
        assert resp.status_code == 401

    # Verifies the endpoint returns 403 without permission.
    def test_no_permission_returns_403(self, client, app, monkeypatch):
        with app.app_context():
            acc    = _make_account(email="add_pl_403@t.com")
            target = _make_account(email="add_pl_target_403@t.com")
            tm     = _make_team_manager(acc)
            team   = _make_team(name="Add Player 403")
            _make_assoc(tm, team, can_edit_players=False)
            db.session.commit()
            team_id   = team.id
            acc_id    = acc.id
            target_id = target.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post(f"/api/teams/{team_id}/players", json={"accountId": target_id})
        assert resp.status_code == 403

    # Verifies the endpoint returns 422 when account id is missing.
    def test_missing_account_id_returns_422(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(email="add_pl_422@t.com")
            tm   = _make_team_manager(acc)
            team = _make_team(name="Add Player 422")
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()
            team_id = team.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post(f"/api/teams/{team_id}/players", json={})
        assert resp.status_code == 422


    # Verifies adding a player succeeds.
    def test_add_player_success(self, client, app, monkeypatch):
        # POST /players creates a pending join request, not a direct membership.
        with app.app_context():
            acc    = _make_account(email="add_pl_201@t.com")
            target = _make_account(email="add_pl_target_201@t.com")
            tm     = _make_team_manager(acc)
            team   = _make_team(name="Add Player 201")
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()
            team_id   = team.id
            acc_id    = acc.id
            target_id = target.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post(f"/api/teams/{team_id}/players", json={"accountId": target_id})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["request"]["status"] == "pending"
        assert data["request"]["user_id"] == target_id
        assert data["request"]["team_id"] == team_id

        with app.app_context():
            req = TeamJoinRequest.query.filter_by(
                team_id=team_id, user_id=target_id
            ).first()
            assert req is not None
            assert req.status == "pending"

    # Verifies a rejected add-player request can be resubmitted.
    def test_add_player_rejected_request_can_be_resubmitted(self, client, app, monkeypatch):
        # A previously rejected join request must not block a new one.
        # The search route shows rejected players as available, so adding must also work.
        with app.app_context():
            acc    = _make_account(email="add_pl_resubmit@t.com")
            target = _make_account(email="add_pl_target_resubmit@t.com")
            tm     = _make_team_manager(acc)
            team   = _make_team(name="Resubmit Team")
            _make_assoc(tm, team, can_edit_players=True)

            rejected_req = TeamJoinRequest(
                team_id=team.id,
                user_id=target.id,
                date=datetime.utcnow(),
                status="rejected",
            )
            db.session.add(rejected_req)
            db.session.commit()
            team_id   = team.id
            acc_id    = acc.id
            target_id = target.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post(f"/api/teams/{team_id}/players", json={"accountId": target_id})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["request"]["status"] == "pending"

    # Verifies adding a duplicate player returns 409.
    def test_add_duplicate_player_returns_409(self, client, app, monkeypatch):
        with app.app_context():
            acc    = _make_account(email="add_pl_409@t.com")
            target = _make_account(email="add_pl_target_409@t.com")
            tm     = _make_team_manager(acc)
            team   = _make_team(name="Add Player 409")
            _make_assoc(tm, team, can_edit_players=True)
            player = Player(id=target.id)
            db.session.add(player)
            db.session.flush()
            pt = PlayerTeam(player_id=player.id, team_id=team.id)
            db.session.add(pt)
            db.session.commit()
            team_id   = team.id
            acc_id    = acc.id
            target_id = target.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post(f"/api/teams/{team_id}/players", json={"accountId": target_id})
        assert resp.status_code == 409


class TestRemovePlayerFromTeam:
    """DELETE /api/teams/<team_id>/players/<account_id>"""

    # Verifies the endpoint returns 404 when the player is not in the team.
    def test_player_not_in_team_returns_404(self, client, app, monkeypatch):
        with app.app_context():
            acc    = _make_account(email="rm_pl_404@t.com")
            target = _make_account(email="rm_pl_target_404@t.com")
            tm     = _make_team_manager(acc)
            team   = _make_team(name="Remove Player 404")
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()
            team_id   = team.id
            acc_id    = acc.id
            target_id = target.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.delete(f"/api/teams/{team_id}/players/{target_id}")
        assert resp.status_code == 404

    # Verifies removing a player succeeds.
    def test_remove_player_success(self, client, app, monkeypatch):
        with app.app_context():
            acc    = _make_account(email="rm_pl_ok@t.com")
            target = _make_account(email="rm_pl_target_ok@t.com")
            tm     = _make_team_manager(acc)
            team   = _make_team(name="Remove Player OK")
            _make_assoc(tm, team, can_edit_players=True)
            player = Player(id=target.id)
            db.session.add(player)
            db.session.flush()
            pt = PlayerTeam(player_id=player.id, team_id=team.id)
            db.session.add(pt)
            db.session.commit()
            team_id   = team.id
            acc_id    = acc.id
            target_id = target.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.delete(f"/api/teams/{team_id}/players/{target_id}")
        assert resp.status_code == 200


class TestGetTeamManagers:
    """GET /api/teams/<team_id>/managers"""

    # Verifies the endpoint returns 404 when the team is missing.
    def test_missing_team_returns_404(self, client):
        resp = client.get("/api/teams/999999/managers")
        assert resp.status_code == 404

    # Verifies the endpoint returns the managers list.
    def test_returns_managers_list(self, client, app):
        with app.app_context():
            team = _make_team(name="Managers List Team")
            db.session.commit()
            team_id = team.id

        resp = client.get(f"/api/teams/{team_id}/managers")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "managers" in body
        assert body["teamId"] == team_id


class TestAddManagerToTeam:
    """POST /api/teams/<team_id>/managers"""

    # Verifies the endpoint returns 401 when the caller is not authenticated.
    def test_unauthenticated_returns_401(self, client, app):
        with app.app_context():
            team = _make_team(name="Add Mgr Auth")
            db.session.commit()
            team_id = team.id
        resp = client.post(f"/api/teams/{team_id}/managers", json={"accountId": 1})
        assert resp.status_code == 401

    # Verifies the endpoint returns 403 without permission.
    def test_no_permission_returns_403(self, client, app, monkeypatch):
        with app.app_context():
            acc    = _make_account(email="add_mgr_403@t.com")
            target = _make_account(email="add_mgr_target_403@t.com")
            tm     = _make_team_manager(acc)
            team   = _make_team(name="Add Mgr 403")
            _make_assoc(tm, team, can_edit_managers=False)
            db.session.commit()
            team_id   = team.id
            acc_id    = acc.id
            target_id = target.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post(f"/api/teams/{team_id}/managers", json={"accountId": target_id})
        assert resp.status_code == 403

    # Verifies adding a manager succeeds.
    def test_add_manager_success(self, client, app, monkeypatch):
        with app.app_context():
            acc    = _make_account(email="add_mgr_ok@t.com")
            target = _make_account(email="add_mgr_target_ok@t.com")
            tm     = _make_team_manager(acc)
            team   = _make_team(name="Add Mgr OK")
            _make_assoc(tm, team, can_edit_managers=True)
            db.session.commit()
            team_id   = team.id
            acc_id    = acc.id
            target_id = target.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post(f"/api/teams/{team_id}/managers", json={"accountId": target_id})
        assert resp.status_code == 201

    # Verifies adding a duplicate manager returns 409.
    def test_duplicate_manager_returns_409(self, client, app, monkeypatch):
        with app.app_context():
            acc    = _make_account(email="add_mgr_409@t.com")
            target = _make_account(email="add_mgr_target_409@t.com")
            tm     = _make_team_manager(acc)
            tm2    = _make_team_manager(target)
            team   = _make_team(name="Add Mgr 409")
            _make_assoc(tm, team, can_edit_managers=True)
            _make_assoc(tm2, team)
            db.session.commit()
            team_id   = team.id
            acc_id    = acc.id
            target_id = target.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.post(f"/api/teams/{team_id}/managers", json={"accountId": target_id})
        assert resp.status_code == 409


class TestRemoveManagerFromTeam:
    """DELETE /api/teams/<team_id>/managers/<account_id>"""

    @pytest.mark.parametrize("is_manager,expected_status", [
        (False, 404),
        (True,  200),
    ])
    # Verifies removing a manager succeeds.
    def test_remove_manager(self, client, app, monkeypatch, is_manager, expected_status):
        with app.app_context():
            acc    = _make_account(email=f"rm_mgr_{is_manager}@t.com")
            target = _make_account(email=f"rm_mgr_tgt_{is_manager}@t.com")
            tm     = _make_team_manager(acc)
            team   = _make_team(name=f"Remove Mgr {is_manager}")
            _make_assoc(tm, team, can_edit_managers=True)
            if is_manager:
                tm2 = _make_team_manager(target)
                _make_assoc(tm2, team)
            db.session.commit()
            team_id   = team.id
            acc_id    = acc.id
            target_id = target.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.delete(f"/api/teams/{team_id}/managers/{target_id}")
        assert resp.status_code == expected_status


class TestSearchPlayersNotInTeam:
    """GET /api/teams/<team_id>/players/search?q="""

    # Verifies the endpoint returns 400 when q is missing.
    def test_missing_q_returns_400(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(email="srch_pl_400@t.com")
            tm   = _make_team_manager(acc)
            team = _make_team(name="Search Player 400")
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()
            team_id = team.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.get(f"/api/teams/{team_id}/players/search")
        assert resp.status_code == 400

    # Verifies the search endpoint returns results.
    def test_search_returns_results(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(email="srch_pl_ok@t.com")
            tm   = _make_team_manager(acc)
            team = _make_team(name="Search Player OK")
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()
            team_id = team.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.get(f"/api/teams/{team_id}/players/search?q=test")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "results" in body


class TestGetMyPermissions:
    """GET /api/teams/<team_id>/my-permissions"""

    # Verifies the endpoint returns 401 when the caller is not authenticated.
    def test_unauthenticated_returns_401(self, client, app):
        with app.app_context():
            team = _make_team(name="Perms Unauth")
            db.session.commit()
            team_id = team.id
        resp = client.get(f"/api/teams/{team_id}/my-permissions")
        assert resp.status_code == 401

    # Verifies the endpoint returns the permissions dictionary.
    def test_returns_permissions_dict(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(email="my_perms_ok@t.com")
            tm   = _make_team_manager(acc)
            team = _make_team(name="My Perms OK Team")
            _make_assoc(tm, team,
                        can_rename=True, can_delete=False,
                        can_edit_players=True, can_edit_managers=False)
            db.session.commit()
            team_id = team.id
            acc_id  = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.get(f"/api/teams/{team_id}/my-permissions")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "permissions" in body
        assert body["permissions"]["canRename"] is True
        assert body["permissions"]["canDelete"] is False


# ===========================================================================
# my_teams.py — HTTP tests
# ===========================================================================

class TestGetMyTeams:
    """GET /api/teams/my"""

    # Verifies the endpoint returns 401 when the caller is not authenticated.
    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/teams/my")
        assert resp.status_code == 401

    # Verifies a team manager sees their own teams.
    def test_team_manager_sees_own_teams(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(email="my_teams_tm@t.com")
            tm   = _make_team_manager(acc)
            team = _make_team(name="My TM Team")
            _make_assoc(tm, team)
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.get("/api/teams/my")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["total"] >= 1
        names = [t["name"] for t in body["teams"]]
        assert "My TM Team" in names

    @pytest.mark.parametrize("params,expected_status", [
        ("from=0&to=10",         200),
        ("from=abc&to=10",       422),
        ("from=0&to=xyz",        422),
        ("from=-1&to=10",        422),
        ("from=10&to=5",         422),
        ("from=0&to=10&sort=bad",422),
    ])
    # Verifies pagination validation.
    def test_pagination_validation(self, client, app, monkeypatch, params, expected_status):
        with app.app_context():
            acc = _make_account(email=f"my_teams_pag_{params[:5]}@t.com")
            _make_team_manager(acc)
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.get(f"/api/teams/my?{params}")
        assert resp.status_code == expected_status


class TestGetMyAllTeams:
    """GET /api/teams/my-all"""

    # Verifies the endpoint returns 401 when the caller is not authenticated.
    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/teams/my-all")
        assert resp.status_code == 401

    # Verifies a player sees their own teams.
    def test_player_sees_own_teams(self, client, app, monkeypatch):
        with app.app_context():
            acc  = _make_account(email="my_all_player@t.com")
            team = _make_team(name="Player All Team")
            player = Player(id=acc.id)
            db.session.add(player)
            db.session.flush()
            pt = PlayerTeam(player_id=player.id, team_id=team.id)
            db.session.add(pt)
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.get("/api/teams/my-all")
        assert resp.status_code == 200
        body = resp.get_json()
        names = [t["name"] for t in body["teams"]]
        assert "Player All Team" in names

    # Verifies a plain user gets an empty list.
    def test_plain_user_gets_empty(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(email="my_all_plain@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            acc = Account.query.get(acc_id)
            _authed_client(client, monkeypatch, acc)

        resp = client.get("/api/teams/my-all")
        assert resp.status_code == 200
