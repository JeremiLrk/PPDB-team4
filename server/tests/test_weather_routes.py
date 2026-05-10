from datetime import datetime, time, timedelta, timezone

from server.app.models.club import Club
from server.extensions import db


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_weather_route_uses_proposal_day_forecast(client, app, monkeypatch):
    with app.app_context():
        club = Club(name="Weather Club", city="Antwerpen, Belgium")
        db.session.add(club)
        db.session.commit()
        club_id = club.id

    target_dt = datetime.now(timezone.utc) + timedelta(days=2)
    target_day = target_dt.date()
    target_iso = target_dt.isoformat().replace("+00:00", "Z")
    forecast_dt = datetime.combine(target_day, time(hour=12), tzinfo=timezone.utc)

    monkeypatch.setattr(
        "server.app.routes.weather_routes.search_cities",
        lambda city, limit=1: [{"lat": 51.2194, "lon": 4.4025, "label": "Antwerpen, Belgium"}],
    )

    def fake_get(url, params=None, timeout=None):
        assert "onecall" in url
        return FakeResponse(
            {
                "daily": [
                    {
                        "dt": int(forecast_dt.timestamp()),
                        "temp": {"day": 19.4, "min": 16.2, "max": 21.1},
                        "weather": [{"description": "light rain"}],
                    },
                    {
                        "dt": int((forecast_dt + timedelta(days=1)).timestamp()),
                        "temp": {"day": 22.0, "min": 18.0, "max": 25.0},
                        "weather": [{"description": "clear sky"}],
                    },
                ]
            }
        )

    monkeypatch.setattr("server.app.routes.weather_routes.requests.get", fake_get)

    response = client.get(f"/api/weather/{club_id}?target_dt={target_iso}")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["name"] == "Antwerpen, Belgium"
    assert payload["main"]["temp"] == 19.4
    assert payload["weather"][0]["description"] == "light rain"
    assert payload["source"] == "onecall.daily"
    assert payload["forecastFor"].startswith(target_dt.date().isoformat())


def test_weather_route_returns_404_for_out_of_range_forecast(client, app, monkeypatch):
    with app.app_context():
        club = Club(name="Weather Club 2", city="Antwerpen, Belgium")
        db.session.add(club)
        db.session.commit()
        club_id = club.id

    target_dt = datetime.now(timezone.utc) + timedelta(days=10)
    target_iso = target_dt.isoformat().replace("+00:00", "Z")

    monkeypatch.setattr(
        "server.app.routes.weather_routes.search_cities",
        lambda city, limit=1: [{"lat": 51.2194, "lon": 4.4025, "label": "Antwerpen, Belgium"}],
    )

    def fake_get(url, params=None, timeout=None):
        if "onecall" in url:
            return FakeResponse(
                {
                    "daily": [
                        {
                            "dt": int((datetime.now(timezone.utc) + timedelta(days=3)).timestamp()),
                            "temp": {"day": 19.4, "min": 16.2, "max": 21.1},
                            "weather": [{"description": "light rain"}],
                        }
                    ]
                }
            )
        assert "forecast" in url
        return FakeResponse(
            {
                "city": {"timezone": 7200},
                "list": [
                    {
                        "dt": int((datetime.now(timezone.utc) + timedelta(days=3)).timestamp()),
                        "main": {"temp": 20.0, "temp_min": 18.0, "temp_max": 22.0},
                        "weather": [{"description": "light rain"}],
                    }
                ],
            }
        )

    monkeypatch.setattr("server.app.routes.weather_routes.requests.get", fake_get)

    response = client.get(f"/api/weather/{club_id}?target_dt={target_iso}")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Weather forecast unavailable for that proposal date."


def test_weather_route_uses_timezone_adjusted_forecast_day(client, app, monkeypatch):
    with app.app_context():
        club = Club(name="Weather Club 3", city="Antwerpen, Belgium")
        db.session.add(club)
        db.session.commit()
        club_id = club.id

    target_day = (datetime.now(timezone.utc) + timedelta(days=2)).date()
    target_iso = datetime.combine(target_day, time(hour=18), tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    monkeypatch.setattr(
        "server.app.routes.weather_routes.search_cities",
        lambda city, limit=1: [{"lat": 51.2194, "lon": 4.4025, "label": "Antwerpen, Belgium"}],
    )

    def fake_get(url, params=None, timeout=None):
        assert "onecall" in url
        return FakeResponse(
            {
                "timezone_offset": 7200,
                "daily": [
                    {
                        "dt": int(datetime.combine(target_day - timedelta(days=1), time(hour=22), tzinfo=timezone.utc).timestamp()),
                        "temp": {"day": 17.0, "min": 14.0, "max": 20.0},
                        "weather": [{"description": "scattered clouds"}],
                    }
                ],
            }
        )

    monkeypatch.setattr("server.app.routes.weather_routes.requests.get", fake_get)

    response = client.get(f"/api/weather/{club_id}?target_dt={target_iso}")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["main"]["temp"] == 17.0
    assert payload["weather"][0]["description"] == "scattered clouds"


def test_weather_route_falls_back_to_five_day_forecast_when_onecall_is_unauthorized(client, app, monkeypatch):
    with app.app_context():
        club = Club(name="Weather Club 4", city="Antwerpen, Belgium")
        db.session.add(club)
        db.session.commit()
        club_id = club.id

    target_day = (datetime.now(timezone.utc) + timedelta(days=2)).date()
    target_iso = datetime.combine(target_day, time(hour=18), tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    monkeypatch.setattr(
        "server.app.routes.weather_routes.search_cities",
        lambda city, limit=1: [{"lat": 51.2194, "lon": 4.4025, "label": "Antwerpen, Belgium"}],
    )

    def fake_get(url, params=None, timeout=None):
        if "onecall" in url:
            return FakeResponse({"message": "unauthorized"}, status_code=401)
        assert "forecast" in url
        return FakeResponse(
            {
                "city": {"timezone": 7200},
                "list": [
                    {
                        "dt": int(datetime.combine(target_day, time(hour=11), tzinfo=timezone.utc).timestamp()),
                        "main": {"temp": 18.5, "temp_min": 17.0, "temp_max": 20.0},
                        "weather": [{"description": "few clouds"}],
                    }
                ],
            }
        )

    monkeypatch.setattr("server.app.routes.weather_routes.requests.get", fake_get)

    response = client.get(f"/api/weather/{club_id}?target_dt={target_iso}")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["source"] == "forecast3h"
    assert payload["main"]["temp"] == 18.5
    assert payload["weather"][0]["description"] == "few clouds"
