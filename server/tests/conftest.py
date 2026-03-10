import pytest
from app import app as flask_app, db

@pytest.fixture
def app():
    flask_app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test_secret_key",
        }
    )

    with flask_app.app_context():
        yield flask_app
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()