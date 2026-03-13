import uuid
import pytest
<<<<<<< HEAD
from server.app import create_app
from server.extensions import db
=======
from flask import Flask
from flask.testing import FlaskClient
from server.app import User, Administrator, db
>>>>>>> e275562 (beetje vanalles)

@pytest.fixture
def app():
    flask_app = create_app()
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