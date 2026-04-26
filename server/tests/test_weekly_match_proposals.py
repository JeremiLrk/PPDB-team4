from datetime import datetime, timedelta
import math

from flask import Flask
from flask.testing import FlaskClient

from server.app.models.account import Account
from server.app.models.ladder import Ladder
from server.app.models.ladder_team import LadderTeam
from server.app.models.match import MatchProposal
from server.app.models.team import Team
from server.app.services.weekly_match_proposal_service import (
    auto_generation_not_before,
    generate_weekly_match_proposals,
    next_week_start,
)
import server.app.services.weekly_match_proposal_service as weekly_service
from server.extensions import db


def loginDemoPlayer(client: FlaskClient):
    response = client.post(
        "/api/login",
        json={"email": "jeremilorek@outlook.com", "password": "qwertyuiop"},
    )
    assert response.status_code == 200


def findPlayerDemoProposal(client: FlaskClient):
    list_response = client.get("/api/matches/proposals")
    assert list_response.status_code == 200
    proposals = list_response.get_json()["proposals"]
    return next(
        proposal for proposal in proposals if proposal["team1_name"] == "Player Demo A"
    )


def roundHalfAwayFromZero(value: float) -> int:
    if value >= 0:
        return int(math.floor(value + 0.5))
    return int(math.ceil(value - 0.5))


def expectedScore(player_rating: int, opponent_rating: int) -> float:
    diff = max(-400, min(400, opponent_rating - player_rating))
    return 1 / (1 + 10 ** (diff / 400))


def test_seeded_player_demo_teams_share_one_ladder(seeded_app: Flask):
    with seeded_app.app_context():
        ladder = Ladder.query.filter_by(name="Player Demo Singles").first()
        assert ladder is not None

        rows = (
            LadderTeam.query.filter_by(ladder_id=ladder.id)
            .order_by(LadderTeam.rank.asc())
            .all()
        )
        team_names = [db.session.get(Team, row.team_id).name for row in rows]

        assert team_names == ["Player Demo A", "Player Demo B"]


def test_demo_account_is_player_on_non_managed_ladder_team(seeded_app: Flask):
    with seeded_app.app_context():
        account = Account.query.filter_by(email="jeremilorek@outlook.com").first()
        assert account is not None
        assert account.player is not None
        assert account.team_manager is not None

        managed_team_names = {team.name for team in account.team_manager.teams}
        player_team_names = {team.name for team in account.player.teams}

        assert "Player Demo A" in player_team_names
        assert "Player Demo A" not in managed_team_names


def test_player_can_see_and_accept_weekly_proposal(seeded_client: FlaskClient):
    loginDemoPlayer(seeded_client)

    player_demo_proposal = findPlayerDemoProposal(seeded_client)
    assert player_demo_proposal["team2_name"] == "Player Demo B"
    assert player_demo_proposal["status"] == "pending"

    accept_response = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "accepted"},
    )
    assert accept_response.status_code == 200
    assert accept_response.get_json()["proposal"]["status"] == "accepted"


def test_player_can_set_accepted_proposal_back_to_pending(seeded_client: FlaskClient):
    loginDemoPlayer(seeded_client)
    player_demo_proposal = findPlayerDemoProposal(seeded_client)

    accept_response = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "accepted"},
    )
    assert accept_response.status_code == 200

    pending_response = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "pending"},
    )
    assert pending_response.status_code == 200
    assert pending_response.get_json()["proposal"]["status"] == "pending"


def test_played_result_updates_elo_rating_matches_played_and_rank(seeded_client: FlaskClient, seeded_app: Flask):
    loginDemoPlayer(seeded_client)
    player_demo_proposal = findPlayerDemoProposal(seeded_client)

    with seeded_app.app_context():
        ladder = Ladder.query.filter_by(name="Player Demo Singles").first()
        team_a = Team.query.filter_by(name="Player Demo A").first()
        team_b = Team.query.filter_by(name="Player Demo B").first()
        assert ladder is not None
        assert team_a is not None
        assert team_b is not None

        before_a = db.session.get(LadderTeam, (ladder.id, team_a.id))
        before_b = db.session.get(LadderTeam, (ladder.id, team_b.id))
        assert before_a is not None
        assert before_b is not None
        rating_a_before = before_a.rating
        rating_b_before = before_b.rating
        played_a_before = before_a.matches_played
        played_b_before = before_b.matches_played

    accept_response = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "accepted"},
    )
    assert accept_response.status_code == 200

    played_response = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "played", "score_team1": 3, "score_team2": 1},
    )
    assert played_response.status_code == 200
    assert played_response.get_json()["proposal"]["status"] == "played"

    expected_a = expectedScore(rating_a_before, rating_b_before)
    expected_b = expectedScore(rating_b_before, rating_a_before)
    expected_delta_a = roundHalfAwayFromZero(40 * (1.0 - expected_a))
    expected_delta_b = roundHalfAwayFromZero(40 * (0.0 - expected_b))

    with seeded_app.app_context():
        db.session.expire_all()
        after_a = db.session.get(LadderTeam, (ladder.id, team_a.id))
        after_b = db.session.get(LadderTeam, (ladder.id, team_b.id))
        assert after_a is not None
        assert after_b is not None

        assert after_a.rating == rating_a_before + expected_delta_a
        assert after_b.rating == rating_b_before + expected_delta_b
        assert after_a.matches_played == played_a_before + 1
        assert after_b.matches_played == played_b_before + 1
        assert after_a.rank == 1
        assert after_b.rank == 2


def test_played_result_cannot_be_recorded_twice(seeded_client: FlaskClient):
    loginDemoPlayer(seeded_client)
    player_demo_proposal = findPlayerDemoProposal(seeded_client)

    accept_response = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "accepted"},
    )
    assert accept_response.status_code == 200

    first_played = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "played", "score_team1": 2, "score_team2": 0},
    )
    assert first_played.status_code == 200

    second_played = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "played", "score_team1": 1, "score_team2": 0},
    )
    assert second_played.status_code == 409
    assert "already exists" in second_played.get_json()["message"].lower()


def test_played_result_same_payload_is_idempotent_retry(seeded_client: FlaskClient):
    loginDemoPlayer(seeded_client)
    player_demo_proposal = findPlayerDemoProposal(seeded_client)

    accept_response = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "accepted"},
    )
    assert accept_response.status_code == 200

    first_played = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "played", "score_team1": 2, "score_team2": 0},
    )
    assert first_played.status_code == 200

    second_played = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "played", "score_team1": 2, "score_team2": 0},
    )
    assert second_played.status_code == 200
    assert "idempotent" in (second_played.get_json().get("message") or "").lower()


def test_played_result_cannot_be_reset_to_pending(seeded_client: FlaskClient):
    loginDemoPlayer(seeded_client)
    player_demo_proposal = findPlayerDemoProposal(seeded_client)

    accept_response = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "accepted"},
    )
    assert accept_response.status_code == 200

    played_response = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "played", "score_team1": 2, "score_team2": 1},
    )
    assert played_response.status_code == 200

    pending_response = seeded_client.patch(
        f"/api/matches/proposals/{player_demo_proposal['id']}/status",
        json={"status": "pending"},
    )
    assert pending_response.status_code == 409
    assert "immutable" in pending_response.get_json()["message"].lower()


def test_weekly_generation_is_idempotent_for_existing_week(seeded_app: Flask):
    with seeded_app.app_context():
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
    assert auto_generation_not_before(generated_at) == datetime(2026, 5, 3, 8, 0, 0)


def test_weekly_generation_skips_pair_when_rematch_cooldown_active(seeded_app: Flask, monkeypatch):
    with seeded_app.app_context():
        account = Account.query.filter_by(email="jeremilorek@outlook.com").first()
        ladder = Ladder.query.filter_by(name="Player Demo Singles").first()
        assert account is not None
        assert ladder is not None

        future_week = next_week_start() + timedelta(days=35)
        monkeypatch.setattr(weekly_service, "meets_rematch_cooldown", lambda *_args, **_kwargs: False)

        result = generate_weekly_match_proposals(
            proposed_by_user_id=account.id,
            week_start_date=future_week,
            ladder_id=ladder.id,
            managed_team_ids=None,
            duration_minutes=60,
            location="Player Demo Court 1",
        )

        assert result["created_count"] == 0
        assert any(row["reason"] == "rematch_cooldown" for row in result["skipped"])
