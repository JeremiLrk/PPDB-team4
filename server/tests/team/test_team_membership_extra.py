"""
Tests for team membership routes not covered by existing test files.

Routes under test
-----------------
GET    /api/teams/<id>/members
    - 404 when team is missing
    - 200 with firstName/lastName only (no personal info)

GET    /api/teams/<id>/managers/search?q=
    - 401 when unauthenticated
    - 400 when q is missing
    - 403 when caller lacks can_edit_managers
    - 200 with results list

POST   /api/teams/<id>/players  (202 warning path)
    - 202 + warning payload when adding would exceed ladder max (no confirmExceed)
    - 201 when confirmExceed=true bypasses the warning

DELETE /api/teams/<id>/players/<account_id>  (202 warning path)
    - 202 + warning payload when removing would violate ladder min (no confirmViolate)
    - 200 when confirmViolate=true bypasses the warning

GET    /api/teams/my-join-requests
    - 401 when unauthenticated
    - 200 with pending requests for current user
    - 200 with empty list when user has no pending requests

GET    /api/teams/my  (Administrator path)
    - Administrator sees all teams

GET    /api/teams/my-all  (Administrator path)
    - Administrator sees all teams

GET    /api/teams/<id>/ladder-peers?ladder_id=
    - 400 when ladder_id is missing
    - 400 when ladder_id is not an integer
    - 404 when team is missing
    - 404 when ladder is missing
    - 404 when team is not enrolled in the ladder
    - 200 with peers list excluding the focal team
    - 200 with empty peers list when team is the only member
"""

import pytest
from datetime import datetime, timezone

from server.extensions import db
from server.app.models.account import Account, Administrator
from server.app.models.team import Team
from server.app.models.player import Player, PlayerTeam
from server.app.models.team_join_request import TeamJoinRequest

from server.tests._authed_client import _authed_client


# ---------------------------------------------------------------------------
# Shared factories
# ---------------------------------------------------------------------------

from server.tests.team.factories import (
    _make_account,
    _make_team,
    _make_team_manager,
    _make_assoc,
    _make_sport_type,
    _make_ladder,
    _enroll,
    _add_player_to_team,
    _make_admin,
)


# ===========================================================================
# GET /api/teams/<id>/members
# ===========================================================================

class TestGetTeamMembers:
    """Public endpoint — returns first/last name only."""

    def test_missing_team_returns_404(self, client):
        resp = client.get("/api/teams/999999/members")
        assert resp.status_code == 404

    def test_returns_200_with_member_name_fields(self, client, app):
        with app.app_context():
            team = _make_team(name="Members Team")
            _add_player_to_team(team, "member1@t.com")
            db.session.commit()
            team_id = team.id

        resp = client.get(f"/api/teams/{team_id}/members")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["teamId"] == team_id
        assert "members" in body
        assert body["total"] == 1
        member = body["members"][0]
        assert "firstName" in member
        assert "lastName" in member

    def test_response_does_not_expose_email(self, client, app):
        with app.app_context():
            team = _make_team(name="Members No Email Team")
            _add_player_to_team(team, "noemail_member@t.com")
            db.session.commit()
            team_id = team.id

        resp = client.get(f"/api/teams/{team_id}/members")
        assert resp.status_code == 200
        for member in resp.get_json()["members"]:
            assert "email" not in member

    def test_empty_team_returns_empty_list(self, client, app):
        with app.app_context():
            team = _make_team(name="Members Empty Team")
            db.session.commit()
            team_id = team.id

        resp = client.get(f"/api/teams/{team_id}/members")
        assert resp.status_code == 200
        assert resp.get_json()["members"] == []


# ===========================================================================
# GET /api/teams/<id>/managers/search?q=
# ===========================================================================

class TestSearchManagersNotInTeam:

    def test_unauthenticated_returns_401(self, client, app):
        with app.app_context():
            team = _make_team(name="MgrSrch Auth")
            db.session.commit()
            team_id = team.id
        resp = client.get(f"/api/teams/{team_id}/managers/search?q=test")
        assert resp.status_code == 401

    def test_missing_q_returns_400(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(email="mgr_srch_400@t.com")
            tm = _make_team_manager(acc)
            team = _make_team(name="MgrSrch 400")
            _make_assoc(tm, team, can_edit_managers=True)
            db.session.commit()
            team_id, acc_id = team.id, acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        assert client.get(f"/api/teams/{team_id}/managers/search").status_code == 400

    def test_no_permission_returns_403(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(email="mgr_srch_403@t.com")
            tm = _make_team_manager(acc)
            team = _make_team(name="MgrSrch 403")
            _make_assoc(tm, team, can_edit_managers=False)
            db.session.commit()
            team_id, acc_id = team.id, acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.get(f"/api/teams/{team_id}/managers/search?q=test")
        assert resp.status_code == 403

    def test_returns_200_with_results(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(email="mgr_srch_ok@t.com")
            tm = _make_team_manager(acc)
            team = _make_team(name="MgrSrch OK")
            _make_assoc(tm, team, can_edit_managers=True)
            db.session.commit()
            team_id, acc_id = team.id, acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.get(f"/api/teams/{team_id}/managers/search?q=test")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "results" in body
        assert body["teamId"] == team_id

    def test_existing_managers_are_excluded_from_results(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(email="mgr_srch_excl@t.com")
            tm = _make_team_manager(acc)
            team = _make_team(name="MgrSrch Excl")
            _make_assoc(tm, team, can_edit_managers=True)
            db.session.commit()
            team_id, acc_id = team.id, acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        # Search by the manager's own email — should not appear in results
        resp = client.get(
            f"/api/teams/{team_id}/managers/search?q=mgr_srch_excl%40t.com"
        )
        assert resp.status_code == 200
        result_ids = [r["id"] for r in resp.get_json()["results"]]
        assert acc_id not in result_ids


# ===========================================================================
# POST /api/teams/<id>/players — 202 warning path
# ===========================================================================

class TestAddPlayerWarning:
    """POST /players returns 202 when adding would exceed ladder max."""

    def _setup_at_cap(self, app, *, mgr_email, target_email, team_name, sport_name):
        """Creates a team at max capacity in one ladder. Returns (team_id, acc_id, target_id, ladder_id)."""
        st = _make_sport_type(max_players=1, name=sport_name)
        acc = _make_account(email=mgr_email)
        target = _make_account(email=target_email)
        tm = _make_team_manager(acc)
        team = _make_team(name=team_name)
        team.sport_type_id = st.id
        _make_assoc(tm, team, can_edit_players=True)
        _add_player_to_team(team, mgr_email.replace("@", "_filler@"))
        ladder = _make_ladder(name=f"{team_name} Ladder")
        _enroll(team, ladder)
        db.session.flush()
        return team.id, acc.id, target.id, ladder.id

    def test_returns_202_with_warning_payload(self, client, app, monkeypatch):
        with app.app_context():
            team_id, acc_id, target_id, ladder_id = self._setup_at_cap(
                app,
                mgr_email="warnmax_mgr@t.com",
                target_email="warnmax_tgt@t.com",
                team_name="WarnMax Team",
                sport_name="WarnMaxSport",
            )
            db.session.commit()

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.post(
            f"/api/teams/{team_id}/players",
            json={"accountId": target_id},
        )
        assert resp.status_code == 202
        body = resp.get_json()
        assert body["warning"] == "exceeds_max_players"
        assert body["requireConfirm"] is True
        assert isinstance(body["ladders"], list)
        assert len(body["ladders"]) >= 1

    def test_confirm_exceed_true_bypasses_warning(self, client, app, monkeypatch):
        with app.app_context():
            team_id, acc_id, target_id, _ = self._setup_at_cap(
                app,
                mgr_email="warnconf_mgr@t.com",
                target_email="warnconf_tgt@t.com",
                team_name="WarnConfirm Team",
                sport_name="WarnConfirmSport",
            )
            db.session.commit()

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.post(
            f"/api/teams/{team_id}/players?confirmExceed=true",
            json={"accountId": target_id},
        )
        assert resp.status_code == 201


# ===========================================================================
# DELETE /api/teams/<id>/players/<account_id> — 202 warning path
# ===========================================================================

class TestRemovePlayerWarning:
    """DELETE /players/<id> returns 202 when removing would violate ladder min."""

    def _setup_at_min(self, app, *, mgr_email, target_email, team_name, sport_name):
        """Creates a team at min size (2 players) in one ladder.
        Returns (team_id, acc_id, target_id).
        """
        st = _make_sport_type(min_players=2, name=sport_name)
        acc = _make_account(email=mgr_email)
        target = _make_account(email=target_email)
        tm = _make_team_manager(acc)
        team = _make_team(name=team_name)
        team.sport_type_id = st.id
        _make_assoc(tm, team, can_edit_players=True)
        for a in [acc, target]:
            player = Player(id=a.id)
            db.session.add(player)
            db.session.flush()
            db.session.add(PlayerTeam(player_id=player.id, team_id=team.id))
        ladder = _make_ladder(name=f"{team_name} Ladder")
        _enroll(team, ladder)
        db.session.flush()
        return team.id, acc.id, target.id

    def test_returns_202_with_warning_payload(self, client, app, monkeypatch):
        with app.app_context():
            team_id, acc_id, target_id = self._setup_at_min(
                app,
                mgr_email="warnmin_mgr@t.com",
                target_email="warnmin_tgt@t.com",
                team_name="WarnMin Team",
                sport_name="WarnMinSport",
            )
            db.session.commit()

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.delete(f"/api/teams/{team_id}/players/{target_id}")
        assert resp.status_code == 202
        body = resp.get_json()
        assert body["warning"] == "violates_min_players"
        assert body["requireConfirm"] is True

    def test_confirm_violate_true_bypasses_warning(self, client, app, monkeypatch):
        with app.app_context():
            team_id, acc_id, target_id = self._setup_at_min(
                app,
                mgr_email="warnminconf_mgr@t.com",
                target_email="warnminconf_tgt@t.com",
                team_name="WarnMinConfirm Team",
                sport_name="WarnMinConfirmSport",
            )
            db.session.commit()

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.delete(
            f"/api/teams/{team_id}/players/{target_id}?confirmViolate=true"
        )
        assert resp.status_code == 200


# ===========================================================================
# GET /api/teams/my-join-requests
# ===========================================================================

class TestGetMyJoinRequests:

    def test_unauthenticated_returns_401(self, client):
        assert client.get("/api/teams/my-join-requests").status_code == 401

    def test_returns_pending_requests_for_current_user(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(email="myjr_ok@t.com")
            team = _make_team(name="MyJR Team")
            db.session.add(TeamJoinRequest(
                team_id=team.id,
                user_id=acc.id,
                date=datetime.now(timezone.utc),
                status="pending",
            ))
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.get("/api/teams/my-join-requests")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "joinRequests" in body
        assert body["total"] >= 1
        assert all(r["status"] == "pending" for r in body["joinRequests"])

    def test_rejected_requests_are_not_returned(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(email="myjr_rej@t.com")
            team = _make_team(name="MyJR Rejected Team")
            db.session.add(TeamJoinRequest(
                team_id=team.id,
                user_id=acc.id,
                date=datetime.now(timezone.utc),
                status="rejected",
            ))
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.get("/api/teams/my-join-requests")
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 0

    def test_user_with_no_requests_gets_empty_list(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(email="myjr_empty@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.get("/api/teams/my-join-requests")
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 0


# ===========================================================================
# GET /api/teams/my  — Administrator path
# ===========================================================================

class TestGetMyTeamsAsAdmin:

    def test_admin_sees_all_teams(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_admin("admin_my_teams@t.com")
            _make_team(name="Admin Visible Team")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.get("/api/teams/my")
        assert resp.status_code == 200
        assert resp.get_json()["total"] >= 1

    def test_admin_response_shape(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_admin("admin_my_shape@t.com")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.get("/api/teams/my")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "teams" in body and "total" in body


# ===========================================================================
# GET /api/teams/my-all  — Administrator path
# ===========================================================================

class TestGetMyAllTeamsAsAdmin:

    def test_admin_sees_all_teams(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_admin("admin_myall@t.com")
            _make_team(name="AdminAll Visible Team")
            db.session.commit()
            acc_id = acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.get("/api/teams/my-all")
        assert resp.status_code == 200
        assert resp.get_json()["total"] >= 1


# ===========================================================================
# GET /api/teams/<id>/ladder-peers?ladder_id=
# ===========================================================================

class TestGetLadderPeers:

    def test_missing_ladder_id_param_returns_400(self, client, app):
        with app.app_context():
            team = _make_team(name="Peers No Param")
            db.session.commit()
            team_id = team.id
        assert client.get(f"/api/teams/{team_id}/ladder-peers").status_code == 400

    def test_non_integer_ladder_id_returns_400(self, client, app):
        with app.app_context():
            team = _make_team(name="Peers Bad Param")
            db.session.commit()
            team_id = team.id
        resp = client.get(f"/api/teams/{team_id}/ladder-peers?ladder_id=abc")
        assert resp.status_code == 400

    def test_missing_team_returns_404(self, client):
        resp = client.get("/api/teams/9999999/ladder-peers?ladder_id=1")
        assert resp.status_code == 404

    def test_missing_ladder_returns_404(self, client, app):
        with app.app_context():
            team = _make_team(name="Peers No Ladder")
            db.session.commit()
            team_id = team.id
        resp = client.get(f"/api/teams/{team_id}/ladder-peers?ladder_id=9999999")
        assert resp.status_code == 404

    def test_team_not_enrolled_in_ladder_returns_404(self, client, app):
        with app.app_context():
            team = _make_team(name="Peers Not Enrolled")
            ladder = _make_ladder(name="Peers Ladder Not Enrolled")
            db.session.commit()
            team_id, ladder_id = team.id, ladder.id
        resp = client.get(
            f"/api/teams/{team_id}/ladder-peers?ladder_id={ladder_id}"
        )
        assert resp.status_code == 404

    def test_returns_peers_excluding_focal_team(self, client, app):
        with app.app_context():
            team1 = _make_team(name="Peers Self Team")
            team2 = _make_team(name="Peers Other Team")
            ladder = _make_ladder(name="Peers Shared Ladder")
            _enroll(team1, ladder)
            _enroll(team2, ladder)
            db.session.commit()
            team1_id, team2_id, ladder_id = team1.id, team2.id, ladder.id

        resp = client.get(
            f"/api/teams/{team1_id}/ladder-peers?ladder_id={ladder_id}"
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["teamId"] == team1_id
        assert body["ladderId"] == ladder_id
        peer_ids = [p["id"] for p in body["peers"]]
        assert team2_id in peer_ids
        assert team1_id not in peer_ids

    def test_single_team_in_ladder_returns_empty_peers(self, client, app):
        with app.app_context():
            team = _make_team(name="Peers Alone Team")
            ladder = _make_ladder(name="Peers Solo Ladder")
            _enroll(team, ladder)
            db.session.commit()
            team_id, ladder_id = team.id, ladder.id

        resp = client.get(
            f"/api/teams/{team_id}/ladder-peers?ladder_id={ladder_id}"
        )
        assert resp.status_code == 200
        assert resp.get_json()["peers"] == []

    def test_response_contains_expected_peer_fields(self, client, app):
        with app.app_context():
            team1 = _make_team(name="Peers Fields Team1")
            team2 = _make_team(name="Peers Fields Team2")
            ladder = _make_ladder(name="Peers Fields Ladder")
            _enroll(team1, ladder)
            _enroll(team2, ladder)
            db.session.commit()
            team1_id, ladder_id = team1.id, ladder.id

        resp = client.get(
            f"/api/teams/{team1_id}/ladder-peers?ladder_id={ladder_id}"
        )
        assert resp.status_code == 200
        peer = resp.get_json()["peers"][0]
        for field in ("id", "name", "clubId", "rank", "rating", "matchesPlayed"):
            assert field in peer
