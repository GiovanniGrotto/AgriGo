import os
import datetime
import requests

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

HIST_KEY = os.getenv("HIST_KEY")
BASE_URL = f'http://my.meteoblue.com/dataset/query?apikey={HIST_KEY}'

class NitrogenStressRisk:
    CROP_OPTIMAL_VALUES = {
        "Soyabean": {"soil_moisture": (50, 70), "precipitation": (450, 700)},
        "Corn": {"soil_moisture": (50, 70), "precipitation": (500, 800)},
        "Cotton": {"soil_moisture": (50, 70), "precipitation": (700, 1300)},
        "Rice": {"soil_moisture": (80, 80), "precipitation": (1000, 1500)},
        "Wheat": {"soil_moisture": (80, 80), "precipitation": (1000, 1500)},
    }

    @staticmethod
    def compute_nue(crop_name, crop_yield, nitrogen_applied, actual_rainfall, actual_soil_moisture):
        if crop_name not in NitrogenStressRisk.CROP_OPTIMAL_VALUES:
            raise ValueError(f"Unknown crop: {crop_name}")
        
        optimal_precipitation = NitrogenStressRisk.CROP_OPTIMAL_VALUES[crop_name]["precipitation"]
        optimal_soil_moisture = NitrogenStressRisk.CROP_OPTIMAL_VALUES[crop_name]["soil_moisture"]
        
        # Compute Rainfall Factor (RF)
        optimal_rainfall_avg = sum(optimal_precipitation) / 2  # Take the midpoint of optimal range
        rainfall_factor = actual_rainfall / optimal_rainfall_avg
        
        # Compute Soil Moisture Factor (SMF)
        optimal_soil_moisture_avg = sum(optimal_soil_moisture) / 2
        soil_moisture_factor = actual_soil_moisture / optimal_soil_moisture_avg
        
        # Compute NUE
        nue = (crop_yield / nitrogen_applied) * rainfall_factor * soil_moisture_factor
        
        # Categorize NUE Level
        if nue > 40:
            nue_category = "High NUE - No biosimulants needed"
        elif 20 <= nue <= 40:
            nue_category = "Moderate NUE - Biosimulants recommended"
        else:
            nue_category = "Low NUE - Biosimulants strongly recommended"
        
        return {
            "NUE": nue,
            "Rainfall Factor": rainfall_factor,
            "Soil Moisture Factor": soil_moisture_factor,
            "Recommendation": nue_category
        }
    
    @staticmethod
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

    @staticmethod
    def fetch_soil_moisture(location_coords, location_name, timestamp_range):
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
                    {"code": 144, "level": "0-7 cm down", "aggregation": "mean"},  # Soil moisture
                ]
            }]
        }
        response = requests.post(BASE_URL, json=payload)
        if response.status_code == 200:
            data = response.json()
            data = data[0]['codes'][0]['dataPerTimeInterval'][0]['data'][0]
            return sum(data)/len(data)
        return None


# Example usage
if __name__ == "__main__":
    location_coords = [7.57327, 47.558399, 279]  # lon, lat, altitude
    crop_name = "Rice"
    crop_yield = 8000  # kg/ha
    nitrogen_applied = 200  # kg/ha
    start_date_colture = "2025-01-01T+00:00"
    today_date = datetime.datetime.now().strftime("%Y-%m-%dT+00:00")
    timestamp_range = f"{start_date_colture}/{today_date}"
    actual_rainfall = NitrogenStressRisk.fetch_precipitation(location_coords, crop_name, timestamp_range)
    actual_soil_moisture = NitrogenStressRisk.fetch_soil_moisture(location_coords, crop_name, timestamp_range)
    result = NitrogenStressRisk.compute_nue(crop_name, crop_yield, nitrogen_applied, actual_rainfall, actual_soil_moisture)
    print(result)