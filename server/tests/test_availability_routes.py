from datetime import timedelta

from flask.testing import FlaskClient

from server.app.models.account import Account
from server.app.models.ladder import Ladder
from server.app.services.availability_service import list_blocks_for_user
from server.app.services.weekly_match_proposal_service import (
    generate_weekly_match_proposals,
    next_week_start,
)


def login_demo_player(client: FlaskClient):
    response = client.post(
        "/api/login",
        json={"email": "jeremilorek@outlook.com", "password": "qwertyuiop"},
    )
    assert response.status_code == 200


def test_weekly_availability_round_trip(seeded_client: FlaskClient):
    login_demo_player(seeded_client)

    response = seeded_client.post(
        "/api/me/availability",
        json={"weekday": 2, "start_time": "18:00", "end_time": "19:00"},
    )

    assert response.status_code == 201
    block = response.get_json()["block"]
    assert block["weekday"] == 2
    assert block["weekday_label"] == "Wednesday"
    assert block["start_time"] == "18:00"
    assert block["end_time"] == "19:00"

    list_response = seeded_client.get("/api/me/availability")
    assert list_response.status_code == 200
    availability = list_response.get_json()["availability"]
    assert any(item["weekday"] == 2 and item["start_time"] == "18:00" for item in availability)


def test_seeded_demo_availability_uses_weekly_recurrence(seeded_app):
    with seeded_app.app_context():
        account = Account.query.filter_by(email="jeremilorek@outlook.com").first()
        assert account is not None

        blocks = list_blocks_for_user(account.id)
        assert blocks
        assert any(
            block["weekday"] is not None
            and block["start_time"] is not None
            and block["end_time"] is not None
            for block in blocks
        )


def test_weekly_availability_still_drives_match_generation(seeded_app):
    with seeded_app.app_context():
        account = Account.query.filter_by(email="jeremilorek@outlook.com").first()
        ladder = Ladder.query.filter_by(name="Player Demo Singles").first()
        assert account is not None
        assert ladder is not None

        future_week = next_week_start() + timedelta(days=35)
        result = generate_weekly_match_proposals(
            proposed_by_user_id=account.id,
            week_start_date=future_week,
            ladder_id=ladder.id,
            managed_team_ids=None,
            duration_minutes=60,
            location="Player Demo Court 1",
        )

        assert result["created_count"] == 1
        assert result["skipped_count"] >= 0
