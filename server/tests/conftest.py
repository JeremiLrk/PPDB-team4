import pytest

from server.app import create_app, seed_db
from server.extensions import db
from server.config import config_data
import resend
import psycopg

# Tables that tests write to — truncated after every test to ensure isolation.
# Seed tables (account_role, page_text, match_rule_set, ladder_rating_function,
# sport_type, venue_type, match_status) are intentionally excluded.
_TEST_TABLES = (
    "team_manager_team, player_team, club_owner_club, club_join_request, team_club_join_request, "
    "club_player, availability_block, "
    "ladder_team, ladder, "
    "match_score_submission, "
    "match_proposal, match_accepted, match_rejected, match_played, match_cancelled, "
    "team, club, player, club_owner, team_manager, administrator, account"
)


def _reset_database():
    with psycopg.connect(
        dbname=config_data["db_name"],
        user=config_data["db_username"],
        password=config_data["db_password"],
        host=config_data["db_host"],
        port=config_data["db_port"],
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = current_database()
                  AND pid <> pg_backend_pid()
                """
            )
            cur.execute("DROP SCHEMA IF EXISTS public CASCADE")
            cur.execute("CREATE SCHEMA public")
            cur.execute("GRANT ALL ON SCHEMA public TO public")


@pytest.fixture(scope="session", autouse=True)
def reset_database_once():
    _reset_database()


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


@pytest.fixture(autouse=True)
def disable_resend_for_tests(monkeypatch):
    # Keep the test suite from consuming the free-tier email quota.
    monkeypatch.setattr(resend.Emails, "send", lambda *args, **kwargs: None, raising=False)


@pytest.fixture
def seeded_app(app, clean_database):
    from server.app.models.match import MatchProposal

    def _seed_safe_to_dict(self):
        return {}

    original_to_dict = MatchProposal.to_dict
    MatchProposal.to_dict = _seed_safe_to_dict
    with app.app_context():
        try:
            seed_db(app, verbose=False)
        finally:
            MatchProposal.to_dict = original_to_dict
            db.session.remove()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_client(seeded_app):
    return seeded_app.test_client()
