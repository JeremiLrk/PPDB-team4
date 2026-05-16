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
    - 202 + warning payload when adding would exceed ladder max (no confirmDropLadders)
    - 201 when confirmDropLadders=true bypasses the warning

DELETE /api/teams/<id>/players/<account_id>  (202 warning path)
    - 202 + warning payload when removing would violate ladder min (no confirmDropLadders)
    - 200 when confirmDropLadders=true bypasses the warning

POST   /api/teams/<id>/players  (ladder-drop scenario — max exceeded)
    - team is removed from the affected ladder after confirmation
    - unplayed matches for that ladder are cancelled after confirmation

DELETE /api/teams/<id>/players/<account_id>  (ladder-drop scenario — min violated)
    - team is removed from the affected ladder after confirmation
    - unplayed matches for that ladder are cancelled after confirmation

POST   /api/teams/<id>/players/check-max-exceeded
    - 401 when unauthenticated
    - 403 when caller lacks can_edit_players
    - 200 when no ladder would exceed max
    - 409 listing affected ladders when max would be exceeded

DELETE /api/teams/<id>/players/<account_id>/check-min-violated
    - 401 when unauthenticated
    - 404 when player is not in team
    - 200 when no ladder would violate min
    - 409 listing affected ladders when min would be violated

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
            f"/api/teams/{team_id}/players",
            json={"accountId": target_id, "confirmDropLadders": True},
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
            f"/api/teams/{team_id}/players/{target_id}",
            json={"confirmDropLadders": True},
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


# ===========================================================================
# POST /api/teams/<id>/players — ladder drop scenario (max exceeded)
# ===========================================================================

class TestAddPlayerDropsLadderOnConfirm:
    """When confirmDropLadders=true and adding a player would exceed the max,
    the team must be removed from the affected ladders and all unplayed
    matches in those ladders must be cancelled."""

    def _setup(self, app, suffix):
        """Creates a team at capacity (max=1) enrolled in one ladder with one
        unplayed pending match. Returns a dict of IDs needed by test methods."""
        from server.app.models.match import MatchProposal, MatchStatus
        from server.app.models.team import Team

        st = _make_sport_type(max_players=1, name=f"MaxDropSport{suffix}")
        mgr_acc = _make_account(email=f"maxdrop_mgr{suffix}@t.com")
        target_acc = _make_account(email=f"maxdrop_tgt{suffix}@t.com")
        opponent_acc = _make_account(email=f"maxdrop_opp{suffix}@t.com")

        tm = _make_team_manager(mgr_acc)
        team = _make_team(name=f"MaxDrop Team{suffix}")
        team.sport_type_id = st.id
        _make_assoc(tm, team, can_edit_players=True)

        # Add one existing player so the team is already at the cap
        _add_player_to_team(team, f"maxdrop_filler{suffix}@t.com")

        # Opposing team for the match
        opponent_team = _make_team(name=f"MaxDrop Opponent{suffix}")
        ladder = _make_ladder(name=f"MaxDrop Ladder{suffix}")
        _enroll(team, ladder)
        _enroll(opponent_team, ladder)

        # Create one pending match in this ladder
        proposal = MatchProposal(
            sport_type_id=st.id,
            ladder_id=ladder.id,
            team1_id=team.id,
            team2_id=opponent_team.id,
            status_id=MatchStatus.PENDING,
        )
        db.session.add(proposal)
        db.session.flush()

        return {
            "team_id": team.id,
            "mgr_acc_id": mgr_acc.id,
            "target_acc_id": target_acc.id,
            "ladder_id": ladder.id,
            "proposal_id": proposal.id,
        }

    def test_team_removed_from_ladder_after_confirm(self, client, app, monkeypatch):
        with app.app_context():
            ids = self._setup(app, "_rm_ladder")
            db.session.commit()

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(ids["mgr_acc_id"]))

        resp = client.post(
            f"/api/teams/{ids['team_id']}/players",
            json={"accountId": ids["target_acc_id"], "confirmDropLadders": True},
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert "droppedFromLadders" in body
        dropped_ids = [l["id"] for l in body["droppedFromLadders"]]
        assert ids["ladder_id"] in dropped_ids

        with app.app_context():
            from server.app.models.ladder_team import LadderTeam
            enrollment = LadderTeam.query.filter_by(
                ladder_id=ids["ladder_id"], team_id=ids["team_id"]
            ).first()
            assert enrollment is None

    def test_unplayed_matches_cancelled_after_confirm(self, client, app, monkeypatch):
        with app.app_context():
            ids = self._setup(app, "_cancel_match")
            db.session.commit()

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(ids["mgr_acc_id"]))

        resp = client.post(
            f"/api/teams/{ids['team_id']}/players",
            json={"accountId": ids["target_acc_id"], "confirmDropLadders": True},
        )
        assert resp.status_code == 201

        with app.app_context():
            from server.app.models.match import MatchProposal, MatchStatus
            proposal = db.session.get(MatchProposal, ids["proposal_id"])
            assert proposal is not None
            assert proposal.status_id == MatchStatus.CANCELLED


# ===========================================================================
# DELETE /api/teams/<id>/players/<id> — ladder drop scenario (min violated)
# ===========================================================================

class TestRemovePlayerDropsLadderOnConfirm:
    """When confirmDropLadders=true and removing a player would violate the min,
    the team must be removed from the affected ladders and all unplayed
    matches in those ladders must be cancelled."""

    def _setup(self, app, suffix):
        """Creates a team at the minimum (min=2, 2 players) enrolled in one
        ladder with one unplayed accepted match. Returns a dict of IDs."""
        from server.app.models.match import MatchProposal, MatchStatus

        st = _make_sport_type(min_players=2, name=f"MinDropSport{suffix}")
        mgr_acc = _make_account(email=f"mindrop_mgr{suffix}@t.com")
        target_acc = _make_account(email=f"mindrop_tgt{suffix}@t.com")

        tm = _make_team_manager(mgr_acc)
        team = _make_team(name=f"MinDrop Team{suffix}")
        team.sport_type_id = st.id
        _make_assoc(tm, team, can_edit_players=True)

        # Exactly 2 players — at the minimum
        from server.app.models.player import Player, PlayerTeam
        for acc in [mgr_acc, target_acc]:
            player = Player(id=acc.id)
            db.session.add(player)
            db.session.flush()
            db.session.add(PlayerTeam(player_id=player.id, team_id=team.id))

        opponent_team = _make_team(name=f"MinDrop Opponent{suffix}")
        ladder = _make_ladder(name=f"MinDrop Ladder{suffix}")
        _enroll(team, ladder)
        _enroll(opponent_team, ladder)

        # Create one accepted (unplayed) match in this ladder
        proposal = MatchProposal(
            sport_type_id=st.id,
            ladder_id=ladder.id,
            team1_id=team.id,
            team2_id=opponent_team.id,
            status_id=MatchStatus.ACCEPTED,
        )
        db.session.add(proposal)
        db.session.flush()

        return {
            "team_id": team.id,
            "mgr_acc_id": mgr_acc.id,
            "target_acc_id": target_acc.id,
            "ladder_id": ladder.id,
            "proposal_id": proposal.id,
        }

    def test_team_removed_from_ladder_after_confirm(self, client, app, monkeypatch):
        with app.app_context():
            ids = self._setup(app, "_rm_ladder")
            db.session.commit()

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(ids["mgr_acc_id"]))

        resp = client.delete(
            f"/api/teams/{ids['team_id']}/players/{ids['target_acc_id']}",
            json={"confirmDropLadders": True},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert "droppedFromLadders" in body
        dropped_ids = [l["id"] for l in body["droppedFromLadders"]]
        assert ids["ladder_id"] in dropped_ids

        with app.app_context():
            from server.app.models.ladder_team import LadderTeam
            enrollment = LadderTeam.query.filter_by(
                ladder_id=ids["ladder_id"], team_id=ids["team_id"]
            ).first()
            assert enrollment is None

    def test_unplayed_matches_cancelled_after_confirm(self, client, app, monkeypatch):
        with app.app_context():
            ids = self._setup(app, "_cancel_match")
            db.session.commit()

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(ids["mgr_acc_id"]))

        resp = client.delete(
            f"/api/teams/{ids['team_id']}/players/{ids['target_acc_id']}",
            json={"confirmDropLadders": True},
        )
        assert resp.status_code == 200

        with app.app_context():
            from server.app.models.match import MatchProposal, MatchStatus
            proposal = db.session.get(MatchProposal, ids["proposal_id"])
            assert proposal is not None
            assert proposal.status_id == MatchStatus.CANCELLED


# ===========================================================================
# POST /api/teams/<id>/players/check-max-exceeded
# ===========================================================================

class TestCheckMaxExceeded:
    """POST /api/teams/<id>/players/check-max-exceeded"""

    def test_unauthenticated_returns_401(self, client, app):
        with app.app_context():
            team = _make_team(name="CheckMax Auth Team")
            db.session.commit()
            team_id = team.id
        resp = client.post(f"/api/teams/{team_id}/players/check-max-exceeded", json={})
        assert resp.status_code == 401

    def test_no_permission_returns_403(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(email="checkmax_403@t.com")
            tm = _make_team_manager(acc)
            team = _make_team(name="CheckMax 403 Team")
            _make_assoc(tm, team, can_edit_players=False)
            db.session.commit()
            team_id, acc_id = team.id, acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.post(f"/api/teams/{team_id}/players/check-max-exceeded", json={})
        assert resp.status_code == 403

    def test_returns_200_when_no_ladder_would_exceed_max(self, client, app, monkeypatch):
        with app.app_context():
            st = _make_sport_type(max_players=10, name="CheckMaxOKSport")
            acc = _make_account(email="checkmax_ok@t.com")
            tm = _make_team_manager(acc)
            team = _make_team(name="CheckMax OK Team")
            team.sport_type_id = st.id
            _make_assoc(tm, team, can_edit_players=True)
            ladder = _make_ladder(name="CheckMax OK Ladder")
            _enroll(team, ladder)
            db.session.commit()
            team_id, acc_id = team.id, acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.post(f"/api/teams/{team_id}/players/check-max-exceeded", json={})
        assert resp.status_code == 200

    def test_returns_409_with_ladder_names_when_max_would_be_exceeded(
        self, client, app, monkeypatch
    ):
        with app.app_context():
            # max=1, team already has 1 player — adding another would exceed
            st = _make_sport_type(max_players=1, name="CheckMax409Sport")
            acc = _make_account(email="checkmax_409@t.com")
            tm = _make_team_manager(acc)
            team = _make_team(name="CheckMax 409 Team")
            team.sport_type_id = st.id
            _make_assoc(tm, team, can_edit_players=True)
            _add_player_to_team(team, "checkmax_409_filler@t.com")
            ladder = _make_ladder(name="CheckMax 409 Ladder")
            _enroll(team, ladder)
            db.session.commit()
            team_id, acc_id = team.id, acc.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.post(f"/api/teams/{team_id}/players/check-max-exceeded", json={})
        assert resp.status_code == 409
        body = resp.get_json()
        assert "ladders" in body
        assert "CheckMax 409 Ladder" in body["ladders"]


# ===========================================================================
# DELETE /api/teams/<id>/players/<id>/check-min-violated
# ===========================================================================

class TestCheckMinViolated:
    """DELETE /api/teams/<id>/players/<account_id>/check-min-violated"""

    def test_unauthenticated_returns_401(self, client, app):
        with app.app_context():
            acc = _make_account(email="checkmin_auth_acc@t.com")
            team = _make_team(name="CheckMin Auth Team")
            db.session.commit()
            team_id, acc_id = team.id, acc.id
        resp = client.delete(
            f"/api/teams/{team_id}/players/{acc_id}/check-min-violated"
        )
        assert resp.status_code == 401

    def test_player_not_in_team_returns_404(self, client, app, monkeypatch):
        with app.app_context():
            acc = _make_account(email="checkmin_404_mgr@t.com")
            target = _make_account(email="checkmin_404_tgt@t.com")
            tm = _make_team_manager(acc)
            team = _make_team(name="CheckMin 404 Team")
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()
            team_id, acc_id, target_id = team.id, acc.id, target.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.delete(
            f"/api/teams/{team_id}/players/{target_id}/check-min-violated"
        )
        assert resp.status_code == 404

    def test_returns_200_when_no_ladder_would_violate_min(self, client, app, monkeypatch):
        with app.app_context():
            # min=1, team has 2 players — removing one still leaves min satisfied
            st = _make_sport_type(min_players=1, name="CheckMinOKSport")
            acc = _make_account(email="checkmin_ok_mgr@t.com")
            target = _make_account(email="checkmin_ok_tgt@t.com")
            tm = _make_team_manager(acc)
            team = _make_team(name="CheckMin OK Team")
            team.sport_type_id = st.id
            _make_assoc(tm, team, can_edit_players=True)
            from server.app.models.player import Player, PlayerTeam
            for a in [acc, target]:
                p = Player(id=a.id)
                db.session.add(p)
                db.session.flush()
                db.session.add(PlayerTeam(player_id=p.id, team_id=team.id))
            ladder = _make_ladder(name="CheckMin OK Ladder")
            _enroll(team, ladder)
            db.session.commit()
            team_id, acc_id, target_id = team.id, acc.id, target.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.delete(
            f"/api/teams/{team_id}/players/{target_id}/check-min-violated"
        )
        assert resp.status_code == 200

    def test_returns_409_with_ladder_names_when_min_would_be_violated(
        self, client, app, monkeypatch
    ):
        with app.app_context():
            # min=2, team exactly has 2 players — removing one violates min
            st = _make_sport_type(min_players=2, name="CheckMin409Sport")
            acc = _make_account(email="checkmin_409_mgr@t.com")
            target = _make_account(email="checkmin_409_tgt@t.com")
            tm = _make_team_manager(acc)
            team = _make_team(name="CheckMin 409 Team")
            team.sport_type_id = st.id
            _make_assoc(tm, team, can_edit_players=True)
            from server.app.models.player import Player, PlayerTeam
            for a in [acc, target]:
                p = Player(id=a.id)
                db.session.add(p)
                db.session.flush()
                db.session.add(PlayerTeam(player_id=p.id, team_id=team.id))
            ladder = _make_ladder(name="CheckMin 409 Ladder")
            _enroll(team, ladder)
            db.session.commit()
            team_id, acc_id, target_id = team.id, acc.id, target.id

        with app.app_context():
            _authed_client(client, monkeypatch, Account.query.get(acc_id))

        resp = client.delete(
            f"/api/teams/{team_id}/players/{target_id}/check-min-violated"
        )
        assert resp.status_code == 409
        body = resp.get_json()
        assert "ladders" in body
        assert "CheckMin 409 Ladder" in body["ladders"]
