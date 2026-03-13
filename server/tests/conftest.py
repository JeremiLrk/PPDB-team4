import pytest
from server.app import create_app
from server.extensions import db

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test_secret_key",
    })

    with app.app_context():
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()