from server.app.models.account import Account, AccountRole
from server.app.models.club import Club
from server.app.models.club_player import ClubPlayer
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.models.player import Player, PlayerTeam
from server.app.models.sport_type import SportType
from server.app.models.team import Team, TeamManager, TeamManagerTeam
from server.app.models.team_club_join_request import TeamClubJoinRequest
from server.extensions import db
from server.tests._authed_client import _authed_client


def _club(name: str = "Club A") -> Club:
    club = Club(name=name)
    db.session.add(club)
    db.session.flush()
    return club


def _account(email: str, role_name: str = "team_manager") -> Account:
    role = AccountRole.query.filter_by(name=role_name).first()
    assert role is not None
    account = Account(
        email=email,
        password_hash="hashed",
        first_name=email.split("@")[0],
        last_name="User",
        account_role_id=role.id,
        is_verified=True,
    )
    db.session.add(account)
    db.session.flush()
    return account


def _admin(email: str = "ladder-admin@test.com") -> Account:
    from server.app.models.account import Administrator

    account = _account(email, role_name="administrator")
    db.session.add(Administrator(id=account.id, access_level=0))
    db.session.flush()
    return account


def _team(name: str, club: Club | None = None) -> Team:
    team = Team(name=name, club_id=club.id if club else None)
    db.session.add(team)
    db.session.flush()
    return team


def _managed_team(name: str, manager: Account, club: Club | None = None) -> Team:
    team = _team(name, club)
    manager_profile = TeamManager.query.get(manager.id)
    if manager_profile is None:
        manager_profile = TeamManager(id=manager.id)
        db.session.add(manager_profile)
        db.session.flush()
    db.session.add(TeamManagerTeam(
        team_manager_id=manager.id,
        team_id=team.id,
        can_rename=True,
        can_delete=True,
        can_edit_players=True,
        can_edit_managers=True,
    ))
    db.session.flush()
    return team


def _add_player(team: Team, account: Account) -> None:
    if Player.query.get(account.id) is None:
        db.session.add(Player(id=account.id))
        db.session.flush()
    db.session.add(PlayerTeam(player_id=account.id, team_id=team.id))
    db.session.flush()


def _ladder(club: Club) -> Ladder:
    ladder = Ladder(club_id=club.id, name="Ladder A")
    db.session.add(ladder)
    db.session.flush()
    return ladder


def _sport_type(name: str) -> SportType:
    sport_type = SportType.query.filter_by(name=name).first()
    assert sport_type is not None
    return sport_type


# Verifies eligible teams include club teams and independent teams with action metadata.
def test_eligible_teams_include_club_and_independent_metadata(app, client, monkeypatch):
    with app.app_context():
        club = _club()
        club_team = _team("Club Team", club)
        free_agent = _team("Free Agent")
        admin = _admin("eligible-ladder-admin@test.com")
        club_id = club.id
        club_team_id = club_team.id
        free_agent_id = free_agent.id
        db.session.commit()

    authed = _authed_client(client, monkeypatch, admin)
    response = authed.get(f"/api/clubs/{club_id}/eligible-teams")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["teams"]
    team_ids = {team["id"] for team in payload["teams"]}
    assert club_team_id in team_ids
    assert free_agent_id in team_ids
    rows = {team["id"]: team for team in payload["teams"]}
    assert rows[club_team_id]["canAddDirectly"] is True
    assert rows[free_agent_id]["requiresInvite"] is True


# Verifies admin can add an existing club team to a ladder immediately.
def test_admin_can_add_club_team_to_ladder(app, client, monkeypatch):
    with app.app_context():
        club = _club()
        ladder = _ladder(club)
        club_team = _team("Club Team", club)
        admin = _admin("direct-ladder-admin@test.com")
        club_id = club.id
        ladder_id = ladder.id
        club_team_id = club_team.id
        db.session.commit()

    authed = _authed_client(client, monkeypatch, admin)
    response = authed.post(
        f"/api/clubs/{club_id}/ladders/{ladder_id}/teams/{club_team_id}",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ladderTeam"]["ladderId"] == ladder_id
    assert payload["ladderTeam"]["teamId"] == club_team_id

    with app.app_context():
        team = db.session.get(Team, club_team_id)
        ladder_team = db.session.get(LadderTeam, (ladder_id, club_team_id))
        assert team is not None
        assert ladder_team is not None
        assert team.club_id == club_id


# Verifies independent teams receive an invitation instead of being claimed.
def test_admin_invites_independent_team_instead_of_assigning_club(app, client, monkeypatch):
    with app.app_context():
        club = _club()
        ladder = _ladder(club)
        manager = _account("ladder-invite-manager@test.com")
        free_team = _managed_team("Independent Team", manager)
        admin = _admin("invite-ladder-admin@test.com")
        club_id = club.id
        ladder_id = ladder.id
        team_id = free_team.id
        db.session.commit()

    authed = _authed_client(client, monkeypatch, admin)
    response = authed.post(
        f"/api/clubs/{club_id}/ladders/{ladder_id}/teams/{team_id}",
    )

    assert response.status_code == 202
    payload = response.get_json()
    assert payload["action"] == "invitation_sent"

    with app.app_context():
        team = db.session.get(Team, team_id)
        invitation = TeamClubJoinRequest.query.filter_by(club_id=club_id, team_id=team_id).first()
        ladder_team = db.session.get(LadderTeam, (ladder_id, team_id))
        assert team.club_id is None
        assert invitation is not None
        assert invitation.status == "pending"
        assert invitation.ladder_id == ladder_id
        assert ladder_team is None


def test_team_manager_accepts_club_invite_and_team_people_join_club(app, client, monkeypatch):
    with app.app_context():
        club = _club()
        ladder = _ladder(club)
        manager = _account("ladder-accept-manager@test.com")
        player = _account("ladder-accept-player@test.com", role_name="user")
        admin = _admin("accept-ladder-admin@test.com")
        assert manager is not None
        assert player is not None
        assert admin is not None
        team = _managed_team("Invited Independent Team", manager)
        _add_player(team, player)
        invitation = TeamClubJoinRequest(
            club_id=club.id,
            team_id=team.id,
            ladder_id=ladder.id,
            requested_by=admin.id,
            date=db.func.now(),
            status="pending",
        )
        db.session.add(invitation)
        db.session.flush()
        club_id = club.id
        ladder_id = ladder.id
        team_id = team.id
        manager_id = manager.id
        player_id = player.id
        invitation_id = invitation.id
        db.session.commit()

    authed = _authed_client(client, monkeypatch, manager)
    response = authed.post(
        f"/api/teams/{team_id}/club-invitations/{invitation_id}/accept",
    )

    assert response.status_code == 200

    with app.app_context():
        team = db.session.get(Team, team_id)
        invitation = db.session.get(TeamClubJoinRequest, invitation_id)
        ladder_team = db.session.get(LadderTeam, (ladder_id, team_id))
        assert team.club_id == club_id
        assert invitation.status == "accepted"
        assert ladder_team is not None
        assert ClubPlayer.query.filter_by(club_id=club_id, player_id=manager_id).first() is not None
        assert ClubPlayer.query.filter_by(club_id=club_id, player_id=player_id).first() is not None


def test_admin_can_remove_team_from_ladder(app, client, monkeypatch):
    with app.app_context():
        club = _club()
        ladder = _ladder(club)
        team = _team("Removable Club Team", club)
        db.session.add(LadderTeam(ladder_id=ladder.id, team_id=team.id, rank=1, rating=1000, matches_played=0))
        admin = _admin("remove-ladder-team-admin@test.com")
        club_id = club.id
        ladder_id = ladder.id
        team_id = team.id
        db.session.commit()

    authed = _authed_client(client, monkeypatch, admin)
    response = authed.delete(f"/api/clubs/{club_id}/ladders/{ladder_id}/teams/{team_id}")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["teamId"] == team_id
    assert payload["ladderId"] == ladder_id

    with app.app_context():
        assert db.session.get(LadderTeam, (ladder_id, team_id)) is None


def test_admin_can_delete_ladder(app, client, monkeypatch):
    with app.app_context():
        club = _club()
        ladder = _ladder(club)
        team = _team("Team In Deleted Ladder", club)
        db.session.add(LadderTeam(ladder_id=ladder.id, team_id=team.id, rank=1, rating=1000, matches_played=0))
        admin = _admin("delete-ladder-admin@test.com")
        club_id = club.id
        ladder_id = ladder.id
        team_id = team.id
        db.session.commit()

    authed = _authed_client(client, monkeypatch, admin)
    response = authed.delete(f"/api/clubs/{club_id}/ladders/{ladder_id}")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ladderId"] == ladder_id
    assert payload["removedTeams"] == 1

    with app.app_context():
        assert db.session.get(Ladder, ladder_id) is None
        assert db.session.get(LadderTeam, (ladder_id, team_id)) is None


# Verifies ladder creation can omit a ruleset for non-racket sports.
def test_admin_can_create_ladder_without_ruleset_for_basketball(app, client, monkeypatch):
    with app.app_context():
        club = _club("Basketball Club")
        admin = _admin("basketball-ladder-admin@test.com")
        club_id = club.id
        basketball_id = _sport_type("Basketball").id
        admin_id = admin.id
        db.session.commit()

    monkeypatch.setattr("server.app.routes.clubs_routes.get_current_user_id_from_cookie", lambda: admin_id)
    authed = _authed_client(client, monkeypatch, admin)
    response = authed.post(
        f"/api/clubs/{club_id}/ladders",
        json={
            "name": "Basketball Ladder",
            "description": "No ruleset needed here",
            "sport_type_id": basketball_id,
            "ladder_rating_function_id": 1,
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["ladder"]["name"] == "Basketball Ladder"

    with app.app_context():
        ladder = db.session.query(Ladder).filter_by(name="Basketball Ladder", club_id=club_id).first()
        assert ladder is not None
        assert ladder.ruleset_id is None
