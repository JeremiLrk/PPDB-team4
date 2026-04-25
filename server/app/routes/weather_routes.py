import os
import requests
from flask import Blueprint, jsonify, request
from server.app.models.club import Club
from server.extensions import db
from pathlib import Path
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent.parent.parent 
env_path = base_dir / ".env"

load_dotenv(dotenv_path=env_path, override=True)

weather = Blueprint("weather", __name__, url_prefix="/api")

@weather.get("/weather/<int:club_id>") # Using int: for safety
def get_weather(club_id):
    club = Club.query.get(club_id)
    
    if not club:
        return jsonify({"error": "Club not found"}), 404
        
    if not club.city:
        return jsonify({"error": "This club has no city assigned"}), 400

    key = os.environ.get("WEATHER_API_KEY")
    api_url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": club.city,
        "appid": key,
        "units": "metric"
    }

    try:
        response = requests.get(api_url, params=params)
        
        if response.status_code == 401:
            return {
                "error": "Activation Error",
                "message": "API Key unauthorized. Check .env loading or activation status."
            }, 401

        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as err:
        return {"error": str(err)}, response.status_code