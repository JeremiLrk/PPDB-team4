from flask.testing import FlaskClient

from server.app.models.account import Account


def _authed_client(client: FlaskClient, monkeypatch, account: Account) -> FlaskClient:
    monkeypatch.setattr(
        "server.app.services.auth_service.verify_user",
        lambda token: account,
    )
    client.set_cookie("access_token", "fake-token")
    return client