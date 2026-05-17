import os
from typing import Any

import requests
from babel import Locale

OPENWEATHER_GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"


def _country_name(country_code: str | None) -> str | None:
    """Convert a country code to its full country name using Babel."""
    if not country_code:
        return None

    try:
        locale = Locale.parse("en")
        return locale.territories.get(country_code.upper())
    except Exception:
        return None


def _format_city_label(city: str | None, country_code: str | None) -> str | None:
    """Format a city label as 'City, Country' if possible."""
    if not city:
        return None

    country_name = _country_name(country_code)
    if country_name:
        return f"{city}, {country_name}"
    if country_code:
        return f"{city}, {country_code.upper()}"
    return city


def _normalize_suggestion(item: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize a single city suggestion from the OpenWeather Geocoding API response."""
    city = item.get("name")
    label = _format_city_label(city, item.get("country"))
    if not city or not label:
        return None

    return {
        "label": label,
        "city": city,
        "country": _country_name(item.get("country")) or item.get("country"),
        "country_code": item.get("country"),
        "state": item.get("state"),
        "lat": item.get("lat"),
        "lon": item.get("lon"),
    }


def search_cities(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Search for cities based on a query string.

    Args:
        query (str): The search query for cities.
        limit (int): The maximum number of results to return.

    Returns:
        list[dict[str, Any]]: A list of normalized city suggestions.
    """
    cleaned_query = (query or "").strip()
    if len(cleaned_query) < 2:
        return []

    api_key = os.environ.get("WEATHER_API_KEY")
    if not api_key:
        raise RuntimeError("WEATHER_API_KEY is not configured.")

    response = requests.get(
        OPENWEATHER_GEOCODING_URL,
        params={
            "q": cleaned_query,
            "limit": limit,
            "appid": api_key,
        },
        timeout=10,
    )
    response.raise_for_status()

    payload = response.json()
    if not isinstance(payload, list):
        return []

    suggestions = []
    seen_labels: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        suggestion = _normalize_suggestion(item)
        if not suggestion:
            continue

        label_key = suggestion["label"].casefold()
        if label_key in seen_labels:
            continue

        seen_labels.add(label_key)
        suggestions.append(suggestion)

    return suggestions


def resolve_city_label(city_input: str) -> str | None:
    """Resolve a city input string to a standardized city label using the OpenWeather Geocoding API."""
    cleaned_input = (city_input or "").strip()
    if not cleaned_input:
        return None

    try:
        suggestions = search_cities(cleaned_input, limit=10)
    except Exception:
        return None

    normalized_input = cleaned_input.casefold()
    exact_label_match = next(
        (
            suggestion
            for suggestion in suggestions
            if suggestion["label"].casefold() == normalized_input
        ),
        None,
    )
    if exact_label_match:
        return exact_label_match["label"]

    exact_city_match = next(
        (
            suggestion
            for suggestion in suggestions
            if suggestion["city"].casefold() == normalized_input
        ),
        None,
    )
    if exact_city_match:
        return exact_city_match["label"]

    return None
