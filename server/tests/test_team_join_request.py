from datetime import datetime, timezone
from server.extensions import db
from server.app.models.account import Account, AccountRole
from server.app.models.team import Team, TeamManager, TeamManagerTeam
from server.app.models.player import Player, PlayerTeam
from server.app.models.team_join_request import TeamJoinRequest
from server.tests._authed_client import _authed_client


def _role(name: str) -> AccountRole:
    role = AccountRole.query.filter_by(name=name).first()
    if not role:
        role = AccountRole(name=name)
        db.session.add(role)
        db.session.flush()
    return role


def _make_account(*, email: str, role_name="team_manager") -> Account:
    r = _role(role_name)
    acc = Account(
        email=email,
        password_hash="hashed",
        first_name="First",
        last_name="Last",
        account_role_id=r.id,
        is_verified=True,
    )
    db.session.add(acc)
    db.session.flush()
    return acc


def _make_team(*, name: str, club_id=None) -> Team:
    t = Team(name=name, club_id=club_id)
    db.session.add(t)
    db.session.flush()
    return t


def _make_team_manager(account: Account) -> TeamManager:
    existing = TeamManager.query.get(account.id)
    if existing:
        return existing
    tm = TeamManager(id=account.id)
    db.session.add(tm)
    db.session.flush()
    return tm


def _make_assoc(tm: TeamManager, team: Team, *,
                can_rename=True, can_delete=True,
                can_edit_players=True, can_edit_managers=True) -> TeamManagerTeam:
    a = TeamManagerTeam(
        team_manager_id=tm.id,
        team_id=team.id,
        can_rename=can_rename,
        can_delete=can_delete,
        can_edit_players=can_edit_players,
        can_edit_managers=can_edit_managers,
    )
    db.session.add(a)
    db.session.flush()
    return a


class TestTeamJoinRequestCreate:
    """Tests for creating team join requests (POST /teams/<id>/players)"""

    def test_create_join_request_success(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)

            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players',
                json={"accountId": player_acc.id}
            )

            assert response.status_code == 201
            data = response.get_json()
            assert data['message'] == "Player join request created successfully."
            assert data['request']['status'] == "pending"
            assert data['request']['user_id'] == player_acc.id
            assert data['request']['team_id'] == team.id

    def test_create_join_request_duplicate_fails(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)

            req = TeamJoinRequest(
                team_id=team.id,
                user_id=player_acc.id,
                date=datetime.now(timezone.utc),
                status="pending"
            )
            db.session.add(req)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players',
                json={"accountId": player_acc.id}
            )

            assert response.status_code == 409
            assert "already exists" in response.get_json()['description']

    def test_create_join_request_player_already_in_team(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)

            player = Player(id=player_acc.id)
            db.session.add(player)
            assoc = PlayerTeam(player_id=player_acc.id, team_id=team.id)
            db.session.add(assoc)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players',
                json={"accountId": player_acc.id}
            )

            assert response.status_code == 409
            assert "already a player" in response.get_json()['description']

    def test_create_join_request_no_permission(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=False)

            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players',
                json={"accountId": player_acc.id}
            )

            assert response.status_code == 403

    def test_create_join_request_missing_team(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                '/api/teams/99999/players',
                json={"accountId": player_acc.id}
            )

            assert response.status_code == 404

    def test_create_join_request_no_json_body(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players',
                data=None,
                content_type='application/json'
            )

            assert response.status_code == 400


class TestTeamJoinRequestAccept:
    """Tests for accepting join requests"""

    def test_accept_request_success(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)

            req = TeamJoinRequest(
                team_id=team.id,
                user_id=player_acc.id,
                date=datetime.now(timezone.utc),
                status="pending"
            )
            db.session.add(req)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players/join-requests/{req.id}/accept'
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == "Player join request accepted successfully."
            assert data['request']['status'] == "accepted"

            db.session.refresh(req)
            assert req.status == "accepted"

            player_in_team = db.session.query(PlayerTeam).filter(
                PlayerTeam.team_id == team.id,
                PlayerTeam.player_id == player_acc.id
            ).first()
            assert player_in_team is not None

    def test_accept_nonexistent_request(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players/join-requests/99999/accept'
            )

            assert response.status_code == 404
            assert "not found" in response.get_json()['description']

    def test_accept_non_pending_request(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)

            req = TeamJoinRequest(
                team_id=team.id,
                user_id=player_acc.id,
                date=datetime.now(timezone.utc),
                status="rejected"
            )
            db.session.add(req)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players/join-requests/{req.id}/accept'
            )

            assert response.status_code == 409
            assert "not in pending status" in response.get_json()['description']

    def test_accept_no_permission(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=False)

            req = TeamJoinRequest(
                team_id=team.id,
                user_id=player_acc.id,
                date=datetime.now(timezone.utc),
                status="pending"
            )
            db.session.add(req)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players/join-requests/{req.id}/accept'
            )

            assert response.status_code == 403


class TestTeamJoinRequestReject:
    """Tests for rejecting join requests"""

    def test_reject_request_success(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)

            req = TeamJoinRequest(
                team_id=team.id,
                user_id=player_acc.id,
                date=datetime.now(timezone.utc),
                status="pending"
            )
            db.session.add(req)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players/join-requests/{req.id}/reject'
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == "Player join request rejected successfully."
            assert data['request']['status'] == "rejected"

            db.session.refresh(req)
            assert req.status == "rejected"

            player_in_team = db.session.query(PlayerTeam).filter(
                PlayerTeam.team_id == team.id,
                PlayerTeam.player_id == player_acc.id
            ).first()
            assert player_in_team is None

    def test_reject_nonexistent_request(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players/join-requests/99999/reject'
            )

            assert response.status_code == 404

    def test_reject_non_pending_request(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)

            req = TeamJoinRequest(
                team_id=team.id,
                user_id=player_acc.id,
                date=datetime.now(timezone.utc),
                status="accepted"
            )
            db.session.add(req)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players/join-requests/{req.id}/reject'
            )

            assert response.status_code == 409

    def test_reject_no_permission(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=False)

            req = TeamJoinRequest(
                team_id=team.id,
                user_id=player_acc.id,
                date=datetime.now(timezone.utc),
                status="pending"
            )
            db.session.add(req)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.post(
                f'/api/teams/{team.id}/players/join-requests/{req.id}/reject'
            )

            assert response.status_code == 403


class TestTeamPlayersSearch:
    """Tests for updated search endpoint (excludes pending requests)"""

    def test_search_excludes_pending_requests(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player1_acc = _make_account(email="player1@test.com", role_name="player")
            player2_acc = _make_account(email="player2@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)

            req = TeamJoinRequest(
                team_id=team.id,
                user_id=player1_acc.id,
                date=datetime.now(timezone.utc),
                status="pending"
            )
            db.session.add(req)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.get(
                f'/api/teams/{team.id}/players/search?q=player'
            )

            assert response.status_code == 200
            data = response.get_json()
            emails = [r['email'] for r in data['results']]

            assert player1_acc.email not in emails
            assert player2_acc.email in emails

    def test_search_excludes_existing_players(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player1_acc = _make_account(email="player1@test.com", role_name="player")
            player2_acc = _make_account(email="player2@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)

            player1 = Player(id=player1_acc.id)
            db.session.add(player1)
            assoc = PlayerTeam(player_id=player1_acc.id, team_id=team.id)
            db.session.add(assoc)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.get(
                f'/api/teams/{team.id}/players/search?q=player'
            )

            assert response.status_code == 200
            data = response.get_json()
            emails = [r['email'] for r in data['results']]

            assert player1_acc.email not in emails
            assert player2_acc.email in emails

    def test_search_excludes_both_pending_and_existing(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player1_acc = _make_account(email="player1@test.com", role_name="player")
            player2_acc = _make_account(email="player2@test.com", role_name="player")
            player3_acc = _make_account(email="player3@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)

            player1 = Player(id=player1_acc.id)
            db.session.add(player1)
            assoc1 = PlayerTeam(player_id=player1_acc.id, team_id=team.id)
            db.session.add(assoc1)

            req = TeamJoinRequest(
                team_id=team.id,
                user_id=player2_acc.id,
                date=datetime.now(timezone.utc),
                status="pending"
            )
            db.session.add(req)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.get(
                f'/api/teams/{team.id}/players/search?q=player'
            )

            assert response.status_code == 200
            data = response.get_json()
            emails = [r['email'] for r in data['results']]

            assert player1_acc.email not in emails
            assert player2_acc.email not in emails
            assert player3_acc.email in emails

    def test_search_does_not_exclude_rejected_requests(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)

            req = TeamJoinRequest(
                team_id=team.id,
                user_id=player_acc.id,
                date=datetime.now(timezone.utc),
                status="rejected"
            )
            db.session.add(req)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.get(
                f'/api/teams/{team.id}/players/search?q=player'
            )

            assert response.status_code == 200
            data = response.get_json()
            emails = [r['email'] for r in data['results']]

            assert player_acc.email in emails

    def test_search_missing_query(self, client, app, monkeypatch):
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            response = client.get(
                f'/api/teams/{team.id}/players/search'
            )

            assert response.status_code == 400


class TestTeamJoinRequestWorkflow:
    """End-to-end workflow tests"""

    def test_complete_accept_workflow(self, client, app, monkeypatch):
        """Test: create request -> accept -> verify player in team"""
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            create_resp = client.post(
                f'/api/teams/{team.id}/players',
                json={"accountId": player_acc.id}
            )
            assert create_resp.status_code == 201
            assert create_resp.get_json()['request']['status'] == 'pending'
            request_id = create_resp.get_json()['request']['id']

            accept_resp = client.post(
                f'/api/teams/{team.id}/players/join-requests/{request_id}/accept'
            )
            assert accept_resp.status_code == 200
            assert accept_resp.get_json()['request']['status'] == 'accepted'

            search_resp = client.get(
                f'/api/teams/{team.id}/players/search?q=player'
            )
            assert search_resp.status_code == 200
            results = search_resp.get_json()['results']
            assert not any(r['id'] == player_acc.id for r in results)

    def test_complete_reject_workflow(self, client, app, monkeypatch):
        """Test: create request -> reject -> verify player not in team"""
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            create_resp = client.post(
                f'/api/teams/{team.id}/players',
                json={"accountId": player_acc.id}
            )
            assert create_resp.status_code == 201

            request_id = create_resp.get_json()['request']['id']
            reject_resp = client.post(
                f'/api/teams/{team.id}/players/join-requests/{request_id}/reject'
            )
            assert reject_resp.status_code == 200
            assert reject_resp.get_json()['request']['status'] == 'rejected'

            search_resp = client.get(
                f'/api/teams/{team.id}/players/search?q=player'
            )
            assert search_resp.status_code == 200
            results = search_resp.get_json()['results']
            assert any(r['id'] == player_acc.id for r in results)

    def test_cannot_accept_twice(self, client, app, monkeypatch):
        """Test: cannot accept already accepted request"""
        with app.app_context():
            manager_acc = _make_account(email="manager@test.com")
            player_acc = _make_account(email="player@test.com", role_name="player")
            team = _make_team(name="Test Team")
            tm = _make_team_manager(manager_acc)
            _make_assoc(tm, team, can_edit_players=True)
            db.session.commit()

            _authed_client(client, monkeypatch, manager_acc)
            create_resp = client.post(
                f'/api/teams/{team.id}/players',
                json={"accountId": player_acc.id}
            )
            request_id = create_resp.get_json()['request']['id']
            first_accept = client.post(
                f'/api/teams/{team.id}/players/join-requests/{request_id}/accept'
            )
            assert first_accept.status_code == 200

            second_accept = client.post(
                f'/api/teams/{team.id}/players/join-requests/{request_id}/accept'
            )
            assert second_accept.status_code == 409