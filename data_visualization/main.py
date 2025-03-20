import requests
from collections import defaultdict


def fetch_daily_temperatures(latitude, longitude):
    url = "https://services.cehub.syngenta-ais.com/api/Forecast/ShortRangeForecastDaily"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "supplier": "Meteoblue",
        "measureLabel": "TempAir_DailyMax (C); TempAir_DailyMin (C); TempAir_DailyAvg (C); Rainfall (mm); Evapotranspiration (mm); SoilMoisture (mm)",
        "top": 30,
        "format": "json"
    }
    headers = {
        "accept": "*/*",
        "ApiKey": "d4f087c7-7efc-41b4-9292-0f22b6199215"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"


def compute_diurnal_heat_stress(tmax, crop):
    crop_params = {
        "Soybean": (32, 45),
        "Corn": (33, 44),
        "Cotton": (32, 38),
        "Rice": (32, 38),
        "Wheat": (25, 32)
    }

    TMaxOptimum, TMaxLimit = crop_params[crop]

    if tmax <= TMaxOptimum:
        return 0
    elif TMaxOptimum < tmax < TMaxLimit:
        return 9 * ((tmax - TMaxOptimum) / (TMaxLimit - TMaxOptimum))
    else:
        return 9


def compute_nighttime_heat_stress(tmin, crop):
    crop_params = {
        "Soybean": (22, 28),
        "Corn": (22, 28),
        "Cotton": (20, 25),
        "Rice": (22, 28),
        "Wheat": (15, 20)
    }

    TMinOptimum, TMinLimit = crop_params[crop]

    if tmin < TMinOptimum:
        return 0
    elif TMinOptimum <= tmin < TMinLimit:
        return 9 * ((tmin - TMinOptimum) / (TMinLimit - TMinOptimum))
    else:
        return 9


def compute_frost_stress(tmin, crop):
    crop_params = {
        "Soybean": (4, -3),
        "Corn": (4, -3),
        "Cotton": (4, -3)
    }

    if crop not in crop_params:
        return 0  # Frost stress not applicable for Rice & Wheat

    TMinNoFrost, TMinFrost = crop_params[crop]

    if tmin >= TMinNoFrost:
        return 0
    elif TMinFrost < tmin < TMinNoFrost:
        return 9 * abs(tmin - TMinNoFrost) / abs(TMinFrost - TMinNoFrost)
    else:
        return 9


if __name__ == "__main__":
    daily_data = fetch_daily_temperatures(43.0, 25.0)

    if isinstance(daily_data, list):
        for entry in daily_data:
            tmax = None
            tmin = None
            crop = "Soybean"  # Example crop, modify as needed

            for measure in entry["measureLabel"].split(";"):
                if "Max" in measure:
                    tmax = float(entry["dailyValue"])
                if "Min" in measure:
                    tmin = float(entry["dailyValue"])

            if tmax is not None:
                diurnal_stress = compute_diurnal_heat_stress(tmax, crop)
                print(f"Date: {entry['date']}, Diurnal Heat Stress: {diurnal_stress}")

            if tmin is not None:
                nighttime_stress = compute_nighttime_heat_stress(tmin, crop)
                frost_stress = compute_frost_stress(tmin, crop)
                print(f"Date: {entry['date']}, Nighttime Heat Stress: {nighttime_stress}")
                print(f"Date: {entry['date']}, Frost Stress: {frost_stress}")
