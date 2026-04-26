import pytest
import sys

from server.app import create_app, seed_db
from server.extensions import db
import subprocess

# Tables that tests write to — truncated after every test to ensure isolation.
# Seed tables (account_role, page_text, match_rule_set, ladder_rating_function,
# sport_type, venue_type, match_status) are intentionally excluded.
_TEST_TABLES = (
    "team_manager_team, player_team, club_owner_club, club_join_request, "
    "club_player, availability_block, "
    "match_rule_set_rule, match_rule, "
    "ladder_team, ladder, "
    "match_proposal, match_accepted, match_rejected, match_played, match_cancelled, "
    "team, club, player, club_owner, team_manager, administrator, account"
)


@pytest.fixture(scope="session", autouse=True)
def reset_database_once():
    subprocess.run(
        [sys.executable, "-m", "server.app.utils.reset_db", "--no-schema"],
        check=True
    )


@pytest.fixture(scope="session")
def app():
    flask_app = create_app()
    flask_app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test_secret_key",
        }
    )
    yield flask_app


@pytest.fixture(autouse=True)
def clean_database(app):
    with app.app_context():
        try:
            db.session.execute(
                db.text(f"TRUNCATE TABLE {_TEST_TABLES} RESTART IDENTITY CASCADE")
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        finally:
            db.session.remove()
    yield


@pytest.fixture
def seeded_app(app):
    seed_db(app, verbose=False)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_client(seeded_app):
    return seeded_app.test_client()
