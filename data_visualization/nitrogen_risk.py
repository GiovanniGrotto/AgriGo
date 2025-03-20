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
        
        rainfall_factor = actual_rainfall / (sum(optimal_precipitation) / 2)
        soil_moisture_factor = actual_soil_moisture / (sum(optimal_soil_moisture) / 2)
        
        nue = (crop_yield / nitrogen_applied) * rainfall_factor * soil_moisture_factor
        
        if nue > 40:
            nue_category = "✅ High NUE - No biosimulants needed\n" \
                          "Your crop is performing well in terms of nitrogen use efficiency!"
        elif 20 <= nue <= 40:
            nue_category = "⚠️ Moderate NUE - Biosimulants recommended\n" \
                          "Consider applying our innovative bacterial consortium:\n" \
                          "• 🦠 Enhanced N fixation from air and soil\n" \
                          "• 🌱 Improved P mobilization and uptake\n" \
                          "• 🔄 Better nutrient cycling and availability"
        else:
            nue_category = "❗ Low NUE - Biosimulants strongly recommended\n" \
                          "Immediate application of our bacterial solution is advised:\n" \
                          "• 🦠 Triple-strain bacterial formula (Sphingobium, Pseudomonas, Curtobacterium)\n" \
                          "• 🌿 Enhanced nitrogen fixation and phosphate mobilization\n" \
                          "• 🔋 Improved macro and micronutrient availability\n" \
                          "• 💪 Better stress tolerance and nutrient use efficiency"
        
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
        """Fetches average soil moisture over the given period."""
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
                    {"code": 144, "level": "0-7 cm down", "aggregation": "mean"},
                ]
            }]
        }
        response = requests.post(BASE_URL, json=payload)
        if response.status_code == 200:
            data = response.json()
            data = data[0]['codes'][0]['dataPerTimeInterval'][0]['data'][0]
            return sum(data)/len(data)
        return None

def print_crop_list():
    print("Available crops:")
    for crop in NitrogenStressRisk.CROP_OPTIMAL_VALUES.keys():
        print(f"• {crop}")
    print()

if __name__ == "__main__":
    print_crop_list()
    
    try:
        # Get user input
        crop_name = input("🌱 Enter crop name: ")
        while crop_name not in NitrogenStressRisk.CROP_OPTIMAL_VALUES:
            print("❌ Invalid crop name. Please choose from the available crops.")
            crop_name = input("🌱 Enter crop name: ")
        
        crop_yield = float(input("📊 Enter crop yield (kg/ha): "))
        nitrogen_applied = float(input("💉 Enter nitrogen applied (kg/ha): "))
        
        print("\n📍 Location coordinates")
        lon = float(input("Enter longitude: "))
        lat = float(input("Enter latitude: "))
        alt = float(input("Enter altitude (meters): "))
        location_coords = [lon, lat, alt]
        
        print("\n📅 Date range")
        start_date = input("Enter start date (YYYY-MM-DD): ")
        start_date_colture = f"{start_date}T+00:00"
        today_date = datetime.datetime.now().strftime("%Y-%m-%dT+00:00")
        timestamp_range = f"{start_date_colture}/{today_date}"

        print("\n🔄 Fetching weather data...")
        actual_rainfall = NitrogenStressRisk.fetch_precipitation(location_coords, crop_name, timestamp_range)
        actual_soil_moisture = NitrogenStressRisk.fetch_soil_moisture(location_coords, crop_name, timestamp_range)

        if actual_rainfall is None or actual_soil_moisture is None:
            print("❌ Error fetching weather data. Please check your inputs and try again.")
        else:
            print("\n📊 Results:")
            result = NitrogenStressRisk.compute_nue(crop_name, crop_yield, nitrogen_applied, actual_rainfall, actual_soil_moisture)
            print(f"NUE Score: {result['NUE']:.2f}")
            print(f"Rainfall Factor: {result['Rainfall Factor']:.2f}")
            print(f"Soil Moisture Factor: {result['Soil Moisture Factor']:.2f}")
            print("\n🔍 Recommendation:")
            print(result['Recommendation'])

    except ValueError as e:
        print(f"❌ Error: Invalid input - {str(e)}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {str(e)}")
    finally:
        print("\n🌾 Thank you for using the Nitrogen Stress Risk Calculator! 🌾")