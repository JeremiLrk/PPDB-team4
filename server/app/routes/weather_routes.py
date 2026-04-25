import os
import requests
from flask import Blueprint, jsonify, request
from pathlib import Path
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent.parent.parent 
env_path = base_dir / ".env"

load_dotenv(dotenv_path=env_path, override=True)

weather = Blueprint("weather", __name__, url_prefix="/api")

@weather.get("/weather/<city>")
def get_weather(city):
    key = os.environ.get("WEATHER_API_KEY")
    
    api_url = "https://api.openweathermap.org/data/2.5/weather"
    
    params = {
        "q": city,
        "appid": key,
        "units": "metric"
    }

    try:
        response = requests.get(api_url, params=params)
        
        if response.status_code == 401:
            return {
                "error": "Activation Error",
                "message": "OpenWeather key is valid but not yet active. Wait ~2 hours."
            }, 401

        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as err:
        return {"error": str(err)}, response.status_code