import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env
LONG_KEY = os.getenv("LONG_KEY")


def fetch_daily_weather(latitude, longitude):
    url = "https://services.cehub.syngenta-ais.com/api/Forecast/ShortRangeForecastDaily"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "supplier": "Meteoblue",
        "measureLabel": "ThunderstormProbability_DailyMax (pct); Cloudcover_DailyAvg (pct); PrecipProbability_Daily (pct); SnowFraction_Daily (pct)",
        "top": 30,
        "format": "json"
    }
    headers = {
        "accept": "*/*",
        "ApiKey": LONG_KEY
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"


def decide_weather(weather_data):
    # Extract values from the input dictionary
    cloudcover = int(weather_data.get('Cloudcover_DailyAvg (pct)', 0))
    precip_prob = int(weather_data.get('PrecipProbability_Daily (pct)', 0))
    snow_fraction = int(weather_data.get('SnowFraction_Daily (pct)', 0))
    thunderstorm_prob = int(weather_data.get('ThunderstormProbability_DailyMax (pct)', 0))

    if precip_prob > 50:
        return "Rainy weather 🌧️"
    elif cloudcover > 50:
        return "Cloudy weather ☁️"
    elif snow_fraction > 50:
        return "Snowy weather ❄️"
    elif thunderstorm_prob > 50:
        return "Thunderstorm expected ⛈️"
    else:
        return "Sunny weather ☀️"


def parse_weather_response(response):
    result = {}

    for entry in response:
        date = entry['date']
        measureLabel = entry['measureLabel']
        dailyValue = entry['dailyValue']

        # If date is not in the result dict, add it
        if date not in result:
            result[date] = {}

        # Add the measureLabel and corresponding value for that date
        result[date][measureLabel] = dailyValue

    for key, value in result.items():
        weather = decide_weather(value)
        print(key.split(" ")[0], ": ", weather)
    return


def predict_weather(lat, long):
    response = fetch_daily_weather(lat, long)
    return parse_weather_response(response)
