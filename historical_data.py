import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

HIST_KEY = os.getenv("HIST_KEY")
BASE_URL = f'http://my.meteoblue.com/dataset/query?apikey={HIST_KEY}'


def fetch_meteo_data(location_coords, location_name, timestamp_range):
    """
    Fetches meteo data based on the specified code, location, and time range.

    Args:
        location_coords (list): [longitude, latitude, altitude]
        location_name (str): Human-readable location name
        timestamp_range (str): Time interval in format "YYYY-MM-DDT+00:00/YYYY-MM-DDT+00:00"

    Returns:
        dict: Dict of data entries or error message
    """
    payload = {
        "units": {
            "temperature": "C",
            "velocity": "km/h",
            "length": "metric",
            "energy": "watts"
        },
        "geometry": {
            "type": "MultiPoint",
            "coordinates": [location_coords],
            "locationNames": [location_name]
        },
        "format": "json",
        "timeIntervals": [
            timestamp_range
        ],
        "queries": [{
            "domain": "ERA5T",
            "gapFillDomain": "NEMSGLOBAL",
            "timeResolution": "daily",
            "codes": [
                {
                    "code": 11,  # Max Temperature
                    "level": "2 m above gnd",
                    "aggregation": "max"
                },
                {
                    "code": 11,  # Min Temperature
                    "level": "2 m above gnd",
                    "aggregation": "min"
                },
                {
                    "code": 11,  # Mean Temperature
                    "level": "2 m above gnd",
                    "aggregation": "mean"
                },
                {
                    "code": 180,  # Cumulative Precipitation
                    "level": "sfc",
                    "aggregation": "sum"
                },
                {
                    "code": 261,  # Cumulative Evaporation
                    "level": "sfc",
                    "aggregation": "sum"
                },
                {
                    "code": 144,  # Mean Soil Moisture
                    "level": "0-7 cm down",
                    "aggregation": "mean"
                },
            ]
        }]
    }

    response = requests.post(BASE_URL, json=payload)

    if response.status_code == 200:
        data = response.json()
        print("Data fetched successfully!")
        data = data[0]['codes']
        keys = ['max_temp', 'min_temp', 'mean_temp', 'precipitation', 'evaporation', 'moisture']
        final_data = {}
        for res, key in zip(data, keys):
            final_data[key] = res['dataPerTimeInterval'][0]['data'][0]

        return final_data
    else:
        error_msg = f"Failed to fetch data: {response.status_code} - {response.text}"
        print(error_msg)
        return {"error": error_msg}


# Example Usage:
if __name__ == "__main__":
    code = 11  # Example: 11 = Temperature 2m
    location_coords = [7.57327, 47.558399, 279]  # lon, lat, altitude
    location_name = "Basel"
    timestamp_range = "2023-06-01T+00:00/2023-06-03T+00:00"

    result = fetch_meteo_data(location_coords, location_name, timestamp_range)
    print(json.dumps(result, indent=2))
