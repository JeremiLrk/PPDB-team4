from datetime import datetime

from flask import Flask
from flask.testing import FlaskClient

from server.app.models.account import Account
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.models.match import MatchProposal
from server.app.models.team import Team
from server.app.services.weekly_match_proposal_service import (
    _auto_generation_not_before,
    generate_weekly_match_proposals,
    next_week_start,
)
from server.extensions import db


def _login_demo_player(client: FlaskClient):
    response = client.post(
        "/api/login",
        json={"email": "jeremilorek@outlook.com", "password": "qwertyuiop"},
    )
    assert response.status_code == 200


def test_seeded_player_demo_teams_share_one_ladder(app: Flask):
    with app.app_context():
        ladder = Ladder.query.filter_by(name="Player Demo Singles").first()
        assert ladder is not None

        rows = (
            LadderTeam.query.filter_by(ladder_id=ladder.id)
            .order_by(LadderTeam.rank.asc())
            .all()
        )
        team_names = [db.session.get(Team, row.team_id).name for row in rows]

        assert team_names == ["Player Demo A", "Player Demo B"]


def test_demo_account_is_player_on_non_managed_ladder_team(app: Flask):
    with app.app_context():
        account = Account.query.filter_by(email="jeremilorek@outlook.com").first()
        assert account is not None
        assert account.player is not None
        assert account.team_manager is not None

        managed_team_names = {team.name for team in account.team_manager.teams}
        player_team_names = {team.name for team in account.player.teams}

        assert "Player Demo A" in player_team_names
        assert "Player Demo A" not in managed_team_names


def test_player_can_see_and_accept_weekly_proposal(client: FlaskClient):
    _login_demo_player(client)

    list_response = client.get("/api/matches/proposals")
    assert list_response.status_code == 200

    proposals = list_response.get_json()["proposals"]
    player_demo_proposal = next(
        proposal for proposal in proposals if proposal["team1_name"] == "Player Demo A"
    )
    assert player_demo_proposal["team2_name"] == "Player Demo B"
    assert player_demo_proposal["status"] == "pending"

    accept_response = client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "accepted"},
    )
    assert accept_response.status_code == 200
    assert accept_response.get_json()["proposal"]["status"] == "accepted"


def test_player_can_set_accepted_proposal_back_to_pending(client: FlaskClient):
    _login_demo_player(client)

    list_response = client.get("/api/matches/proposals")
    assert list_response.status_code == 200

    proposals = list_response.get_json()["proposals"]
    player_demo_proposal = next(
        proposal for proposal in proposals if proposal["team1_name"] == "Player Demo A"
    )

    accept_response = client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "accepted"},
    )
    assert accept_response.status_code == 200

    pending_response = client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "pending"},
    )
    assert pending_response.status_code == 200
    assert pending_response.get_json()["proposal"]["status"] == "pending"


def test_weekly_generation_is_idempotent_for_existing_week(app: Flask):
    with app.app_context():
        account = Account.query.filter_by(email="jeremilorek@outlook.com").first()
        ladder = Ladder.query.filter_by(name="Player Demo Singles").first()

        before_count = MatchProposal.query.filter_by(
            week_start_date=next_week_start(),
        ).count()

        result = generate_weekly_match_proposals(
            proposed_by_user_id=account.id,
            week_start_date=next_week_start(),
            ladder_id=ladder.id,
            managed_team_ids=None,
            duration_minutes=60,
            location="Player Demo Court 1",
        )

        after_count = MatchProposal.query.filter_by(
            week_start_date=next_week_start(),
        ).count()

        assert result["created_count"] == 0
        assert result["skipped_count"] >= 1
        assert any(row["reason"] == "already_exists" for row in result["skipped"])
        assert after_count == before_count


def test_auto_generation_has_one_week_precaution_floor():
    generated_at = datetime(2026, 4, 26, 3, 0, 0)  # Sunday 03:00
    assert _auto_generation_not_before(generated_at) == datetime(2026, 5, 3, 8, 0, 0)
