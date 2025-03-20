import requests
import json
import datetime

HIST_KEY = "7b29a207a0de"
BASE_URL = f'http://my.meteoblue.com/dataset/query?apikey={HIST_KEY}'

CROP_OPTIMAL_VALUES = {
    "Soybean": {"GDD": (2400, 3000), "P": (450, 700), "pH": (6.0, 6.8), "N": (0, 0.026)},
    "Corn": {"GDD": (2700, 3100), "P": (500, 800), "pH": (6.0, 6.8), "N": (0.077, 0.154)},
    "Cotton": {"GDD": (2200, 2600), "P": (700, 1300), "pH": (6.0, 6.5), "N": (0.051, 0.092)},
    "Rice": {"GDD": (2000, 2500), "P": (1000, 1500), "pH": (5.5, 6.5), "N": (0.051, 0.103)},
    "Wheat": {"GDD": (2000, 2500), "P": (1000, 1500), "pH": (5.5, 6.5), "N": (0.051, 0.103)},
}

WEIGHTS = {"GDD": 0.3, "P": 0.3, "pH": 0.2, "N": 0.2}

def fetch_precipitation(location_coords, location_name, timestamp_range):
    """Fetches total precipitation over the given period."""
    payload = {
        "units": {"temperature": "C", "velocity": "km/h", "length": "metric", "energy": "watts"},
        "geometry": {"type": "MultiPoint", "coordinates": [location_coords], "locationNames": [location_name]},
        "format": "json",
        "timeIntervals": [timestamp_range],
        "queries": [{
            "domain": "ERA5T",
            "gapFillDomain": "NEMSGLOBAL",
            "timeResolution": "daily",
            "codes": [{"code": 61, "level": "sfc", "aggregation": "sum"}]
        }]
    }
    response = requests.post(BASE_URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        return sum(data[0]['codes'][0]['dataPerTimeInterval'][0]['data'][0])
    return None

def fetch_ph(location_coords, location_name, timestamp_range):
    """Fetches soil pH from the dataset."""
    payload = {
        "units": {"temperature": "C", "velocity": "km/h", "length": "metric", "energy": "watts"},
        "geometry": {"type": "MultiPoint", "coordinates": [location_coords], "locationNames": [location_name]},
        "format": "json",
        "timeIntervals": [timestamp_range],
        "queries": [{
            "domain": "SOILGRIDS1000",
            "gapFillDomain": "NEMSGLOBAL",
            "timeResolution": "static",
            "codes": [{"code": 812, "level": "5 cm"}]
        }]
    }
    response = requests.post(BASE_URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data[0]['codes'][0]['dataPerTimeInterval'][0]['data'][0][0]
    return None

def fetch_temperature(location_coords, location_name, timestamp_range):
    """Fetches daily max and min temperature for GDD calculation."""
    payload = {
        "units": {"temperature": "C", "velocity": "km/h", "length": "metric", "energy": "watts"},
        "geometry": {"type": "MultiPoint", "coordinates": [location_coords], "locationNames": [location_name]},
        "format": "json",
        "timeIntervals": [timestamp_range],
        "queries": [{
            "domain": "ERA5T",
            "gapFillDomain": "NEMSGLOBAL",
            "timeResolution": "daily",
            "codes": [
                {"code": 11, "level": "2 m above gnd", "aggregation": "max"},  # Tmax
                {"code": 11, "level": "2 m above gnd", "aggregation": "min"}   # Tmin
            ]
        }]
    }
    response = requests.post(BASE_URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        Tmax_values = data[0]['codes'][0]['dataPerTimeInterval'][0]['data'][0]
        Tmin_values = data[0]['codes'][1]['dataPerTimeInterval'][0]['data'][0]
        return Tmax_values, Tmin_values
    return None, None

def compute_gdd(Tmax_values, Tmin_values, Tbase=10):
    """Computes the total GDD over the period."""
    GDD_total = sum(max(((Tmax + Tmin) / 2) - Tbase, 0) for Tmax, Tmin in zip(Tmax_values, Tmin_values))
    return GDD_total

def compute_yield_risk(GDD, P, pH, N, crop):
    """Computes the yield risk based on the given parameters."""
    optimal_values = CROP_OPTIMAL_VALUES[crop]
    GDD_opt = sum(optimal_values["GDD"]) / 2
    P_opt = sum(optimal_values["P"]) / 2
    pH_opt = sum(optimal_values["pH"]) / 2
    N_opt = sum(optimal_values["N"]) / 2

    yield_risk = (
        WEIGHTS["GDD"] * (GDD - GDD_opt) ** 2 +
        WEIGHTS["P"] * (P - P_opt) ** 2 +
        WEIGHTS["pH"] * (pH - pH_opt) ** 2 +
        WEIGHTS["N"] * (N - N_opt) ** 2
    )

    return yield_risk

if __name__ == "__main__":
    location_coords = [7.57327, 47.558399, 279]  # lon, lat, altitude
    crop_name = "Rice"
    
    start_date_colture = "2025-01-01T+00:00"
    today_date = datetime.datetime.now().strftime("%Y-%m-%dT+00:00")
    timestamp_range = f"{start_date_colture}/{today_date}"

    P = fetch_precipitation(location_coords, crop_name, timestamp_range)
    pH = fetch_ph(location_coords, crop_name, timestamp_range)
    Tmax_values, Tmin_values = fetch_temperature(location_coords, crop_name, timestamp_range)
    
    if None in (P, pH, Tmax_values, Tmin_values):
        print("Error fetching data. Check API response.")
    else:
        GDD = compute_gdd(Tmax_values, Tmin_values)
        N = 0.08  # Example nitrogen value; should be fetched from a proper source
        yield_risk = compute_yield_risk(GDD, P, pH, N, crop_name)

        print(f"Yield Risk for {crop_name}: {yield_risk:.2f}")
