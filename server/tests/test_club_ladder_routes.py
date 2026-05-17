from server.app.models.account import Account
from server.app.models.club import Club
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.models.sport_type import SportType
from server.app.models.team import Team
from server.extensions import db
from server.tests._authed_client import _authed_client


def _club(name: str = "Club A") -> Club:
    club = Club(name=name)
    db.session.add(club)
    db.session.flush()
    return club


def _team(name: str, club: Club | None = None) -> Team:
    team = Team(name=name, club_id=club.id if club else None)
    db.session.add(team)
    db.session.flush()
    return team


def _ladder(club: Club) -> Ladder:
    ladder = Ladder(club_id=club.id, name="Ladder A")
    db.session.add(ladder)
    db.session.flush()
    return ladder


def _sport_type(name: str) -> SportType:
    sport_type = SportType.query.filter_by(name=name).first()
    assert sport_type is not None
    return sport_type


# Verifies eligible teams include club and free agents.
def test_eligible_teams_include_club_and_free_agents(seeded_app, client, monkeypatch):
    with seeded_app.app_context():
        club = _club()
        club_team = _team("Club Team", club)
        free_agent = _team("Free Agent")
        admin = Account.query.filter_by(email="admin@netrank.test").first()
        assert admin is not None
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


# Verifies admin can add team to ladder and free agent joins club.
def test_admin_can_add_team_to_ladder_and_free_agent_joins_club(seeded_app, client, monkeypatch):
    with seeded_app.app_context():
        club = _club()
        ladder = _ladder(club)
        free_agent = _team("Free Agent")
        admin = Account.query.filter_by(email="admin@netrank.test").first()
        assert admin is not None
        club_id = club.id
        ladder_id = ladder.id
        free_agent_id = free_agent.id
        db.session.commit()

    authed = _authed_client(client, monkeypatch, admin)
    response = authed.post(
        f"/api/clubs/{club_id}/ladders/{ladder_id}/teams/{free_agent_id}",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ladderTeam"]["ladderId"] == ladder_id
    assert payload["ladderTeam"]["teamId"] == free_agent_id

    with seeded_app.app_context():
        team = db.session.get(Team, free_agent_id)
        ladder_team = db.session.get(LadderTeam, (ladder_id, free_agent_id))
        assert team is not None
        assert ladder_team is not None
        assert team.club_id == club_id


# Verifies ladder creation can omit a ruleset for non-racket sports.
def test_admin_can_create_ladder_without_ruleset_for_basketball(seeded_app, client, monkeypatch):
    with seeded_app.app_context():
        club = _club("Basketball Club")
        admin = Account.query.filter_by(email="admin@netrank.test").first()
        assert admin is not None
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

    with seeded_app.app_context():
        ladder = db.session.query(Ladder).filter_by(name="Basketball Ladder", club_id=club_id).first()
        assert ladder is not None
        assert ladder.ruleset_id is None
