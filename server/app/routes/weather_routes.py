"""
Weather lookup for clubs and match proposals.

The frontend uses this route to preview the weather for a club city on the
date of a proposed match.  The route falls back from OpenWeather's one-call
forecast to the 3-hour forecast when needed.
"""

import os
from datetime import date, datetime, timedelta, timezone

import requests
from flask import Blueprint, jsonify, request
from server.app.models.club import Club
from pathlib import Path
from dotenv import load_dotenv
from server.app.services.city_service import search_cities

base_dir = Path(__file__).resolve().parent.parent.parent 
env_path = base_dir / ".env"

load_dotenv(dotenv_path=env_path, override=True)

weather = Blueprint("weather", __name__, url_prefix="/api")

OPENWEATHER_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"
OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def parse_target_date(value: str | None) -> date | None:
    """Parse the target date query parameter into a date, if possible."""
    cleaned = (value or "").strip()
    if not cleaned:
        return None

    try:
        return date.fromisoformat(cleaned[:10])
    except ValueError:
        return None


def resolve_coordinates(city: str) -> dict | None:
    """Resolve a club city into weather API coordinates and a display label."""
    suggestions = search_cities(city, limit=1)
    if not suggestions:
        return None
    suggestion = suggestions[0]
    lat = suggestion.get("lat")
    lon = suggestion.get("lon")
    if lat is None or lon is None:
        return None
    return {
        "lat": lat,
        "lon": lon,
        "label": suggestion.get("label") or city,
    }


def select_daily_forecast(payload: dict, target_date: date) -> dict | None:
    """Select the one-call daily forecast row for the requested date."""
    daily_rows = payload.get("daily") or []
    timezone_offset = payload.get("timezone_offset") or 0
    for row in daily_rows:
        if not isinstance(row, dict):
            continue
        row_dt = row.get("dt")
        if row_dt is None:
            continue
        row_date = (
            datetime.fromtimestamp(row_dt, tz=timezone.utc)
            + timedelta(seconds=timezone_offset)
        ).date()
        if row_date != target_date:
            continue
        temp = row.get("temp") or {}
        selected = {
            "dt": row_dt,
            "dt_txt": datetime.fromtimestamp(row_dt, tz=timezone.utc).isoformat(),
            "name": "",
            "main": {
                "temp": temp.get("day"),
                "temp_min": temp.get("min"),
                "temp_max": temp.get("max"),
            },
            "weather": row.get("weather") or [],
            "forecastFor": target_date.isoformat(),
            "source": "onecall.daily",
        }
        if row.get("summary"):
            selected["summary"] = row["summary"]
        return selected
    return None


def select_three_hour_forecast(payload: dict, target_date: date) -> dict | None:
    """Select the best 3-hour forecast row for the requested date."""
    forecast_rows = payload.get("list") or []
    timezone_offset = (payload.get("city") or {}).get("timezone") or payload.get("timezone_offset") or 0
    candidates = []

    for row in forecast_rows:
        if not isinstance(row, dict):
            continue
        row_dt = row.get("dt")
        if row_dt is None:
            continue
        local_dt = datetime.fromtimestamp(row_dt, tz=timezone.utc) + timedelta(seconds=timezone_offset)
        if local_dt.date() != target_date:
            continue
        minutes_from_noon = abs((local_dt.hour * 60 + local_dt.minute) - (12 * 60))
        candidates.append((minutes_from_noon, local_dt, row))

    if not candidates:
        return None

    _, chosen_dt, chosen_row = min(candidates, key=lambda item: (item[0], item[1]))
    temp = chosen_row.get("main") or {}
    selected = {
        "dt": chosen_row.get("dt"),
        "dt_txt": chosen_dt.isoformat(),
        "name": "",
        "main": {
            "temp": temp.get("temp"),
            "temp_min": temp.get("temp_min"),
            "temp_max": temp.get("temp_max"),
        },
        "weather": chosen_row.get("weather") or [],
        "forecastFor": target_date.isoformat(),
        "source": "forecast3h",
    }
    return selected


@weather.get("/weather/<int:club_id>")  # Using int: for safety
def get_weather(club_id):
    """Return current weather or forecast data for a club city."""
    club = Club.query.get(club_id)
    
    if not club:
        return jsonify({"error": "Club not found"}), 404
        
    if not club.city:
        return jsonify({"error": "This club has no city assigned"}), 400

    key = os.environ.get("WEATHER_API_KEY")
    if not key:
        return jsonify({"error": "WEATHER_API_KEY is not configured."}), 500

    target_date = _parse_target_date(request.args.get("target_dt"))
    resolved = _resolve_coordinates(club.city)
    if not resolved:
        return jsonify({"error": "Could not resolve weather location."}), 404

    params = {
        "lat": resolved["lat"],
        "lon": resolved["lon"],
        "appid": key,
        "units": "metric"
    }

    try:
        if target_date is None:
            # Current weather uses the simple endpoint and returns immediately.
            response = requests.get(OPENWEATHER_CURRENT_URL, params=params, timeout=10)

            if response.status_code == 401:
                return {
                    "error": "Activation Error",
                    "message": "API Key unauthorized. Check .env loading or activation status."
                }, 401

            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                payload["name"] = resolved["label"]
            return payload

        auth_error = None
        for url, params_override, selector in (
            (
                OPENWEATHER_ONECALL_URL,
                {
                    "lat": resolved["lat"],
                    "lon": resolved["lon"],
                    "exclude": "current,minutely,hourly,alerts",
                    "appid": key,
                    "units": "metric",
                },
                _select_daily_forecast,
            ),
            (
                OPENWEATHER_FORECAST_URL,
                {
                    "lat": resolved["lat"],
                    "lon": resolved["lon"],
                    "appid": key,
                    "units": "metric",
                },
                _select_three_hour_forecast,
            ),
        ):
            response = requests.get(url, params=params_override, timeout=10)

            if response.status_code in {401, 403}:
                # Keep trying the next forecast source if the first one rejects the key.
                auth_error = response
                continue

            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                continue

            forecast = selector(payload, target_date)
            if forecast is not None:
                forecast["name"] = resolved["label"]
                return forecast

        if auth_error is not None:
            # If both forecast sources reject the key, surface the auth error.
            return {
                "error": "Activation Error",
                "message": "API Key unauthorized. Check .env loading or activation status."
            }, auth_error.status_code

        return jsonify({"error": "Weather forecast unavailable for that proposal date."}), 404

    except requests.exceptions.HTTPError as err:
        return {"error": str(err)}, getattr(err.response, "status_code", 502)
    except requests.exceptions.RequestException as err:
        return {"error": str(err)}, 502


# Compatibility aliases for older imports and tests.
_parse_target_date = parse_target_date
_resolve_coordinates = resolve_coordinates
_select_daily_forecast = select_daily_forecast
_select_three_hour_forecast = select_three_hour_forecast
