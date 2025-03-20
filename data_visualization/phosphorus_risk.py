import requests
import datetime
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

HIST_KEY = os.getenv("HIST_KEY")
BASE_URL = f'http://my.meteoblue.com/dataset/query?apikey={HIST_KEY}'

class PhosphorusStress:
    def __init__(self, crop_name, yield_tonnes_per_ha, phosphorus_applied_kg_per_ha, actual_rainfall, actual_soil_moisture, actual_pH):
        self.crop_name = crop_name
        self.yield_tonnes_per_ha = yield_tonnes_per_ha
        self.phosphorus_applied_kg_per_ha = phosphorus_applied_kg_per_ha
        self.actual_rainfall = actual_rainfall
        self.actual_soil_moisture = actual_soil_moisture
        self.actual_pH = actual_pH
        
        self.optimal_conditions = {
            "Soyabean": {"soil_moisture": (50, 70), "precipitation": (450, 700), "pH": (6.0, 7.0)},
            "Corn": {"soil_moisture": (50, 70), "precipitation": (500, 800), "pH": (6.0, 7.0)},
            "Cotton": {"soil_moisture": (50, 70), "precipitation": (700, 1300), "pH": (6.0, 6.5)},
            "Rice": {"soil_moisture": (80, 80), "precipitation": (1000, 1500), "pH": (5.5, 6.5)},
            "Wheat": {"soil_moisture": (80, 80), "precipitation": (1000, 1500), "pH": (6.0, 7.0)},
        }

    def calculate_factors(self):
        optimal = self.optimal_conditions[self.crop_name]
        
        # pH factor
        optimal_pH = sum(optimal["pH"]) / 2
        pH_factor = optimal_pH / self.actual_pH if self.actual_pH > 0 else 0
        
        # Rainfall factor
        optimal_rainfall = sum(optimal["precipitation"]) / 2
        rainfall_factor = self.actual_rainfall / optimal_rainfall if optimal_rainfall > 0 else 0
        
        # Soil moisture factor
        optimal_soil_moisture = sum(optimal["soil_moisture"]) / 2
        soil_moisture_factor = self.actual_soil_moisture / optimal_soil_moisture if optimal_soil_moisture > 0 else 0
        
        # Soil factor (SF)
        soil_factor = (pH_factor + soil_moisture_factor + rainfall_factor) / 4
        
        return soil_factor

    def calculate_PUE(self):
        if self.phosphorus_applied_kg_per_ha <= 0:
            return 0  # Avoid division by zero
        
        soil_factor = self.calculate_factors()
        PUE = (self.yield_tonnes_per_ha / self.phosphorus_applied_kg_per_ha) * soil_factor
        return PUE

    def recommend_biosimulants(self):
        PUE = self.calculate_PUE()
        
        base_recommendation = """
    🔬 Recommended Biosimulant Solution:
    A innovative product based on 3 endophytic bacteria strains:
    • Sphingobium salicis
    • Pseudomonas siliginis
    • Curtobacterium salicis
    
    ✨ Benefits:
    """
        
        if PUE < 0.05:
            return f"{base_recommendation}\n🔴 Low PUE - Strongly Recommend Biosimulants\n" + """
        • Enhanced N2 fixation from air
        • Improved NO3 and NH4 uptake
        • Maximum P-solubilization
        • Enhanced nutrient transport
        • Full spectrum micronutrient solubilization
        """
        elif PUE < 0.10:
            return f"{base_recommendation}\n🟡 Moderate PUE - Recommend Biosimulants\n" + """
        • Moderate N2 fixation support
        • Enhanced P-solubilization
        • Improved nutrient transport
        • Selective micronutrient solubilization
        """
        elif PUE < 0.15:
            return f"{base_recommendation}\n🟢 Good PUE - Optional Biosimulants\n" + """
        • Maintenance of nutrient uptake
        • Supportive P-solubilization
        • Basic micronutrient support
        """
        else:
            return "🌟 Excellent PUE - No biosimulants needed at this time"

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


def phosphorus():
    # Get user input
    print("\n📝 Please enter the following information:")
    
    # Crop selection
    available_crops = ["Soyabean", "Corn", "Cotton", "Rice", "Wheat"]
    print("\nAvailable crops:", ", ".join(available_crops))
    while True:
        crop_name = input("Enter crop name: ").capitalize()
        if crop_name in available_crops:
            break
        print("❌ Invalid crop. Please choose from the available options.")

    # Get other inputs
    yield_tonnes_per_ha = float(input("Enter yield (tonnes/ha): "))
    phosphorus_applied_kg_per_ha = float(input("Enter phosphorus applied (kg/ha): "))
    
    # Location input
    print("\n📍 Enter location coordinates:")
    lon = float(input("Longitude: "))
    lat = float(input("Latitude: "))
    alt = float(input("Altitude: "))
    location_coords = [lon, lat, alt]

    # Date input
    start_date = input("Enter start date (YYYY-MM-DD): ")
    start_date_colture = f"{start_date}T+00:00"
    today_date = datetime.datetime.now().strftime("%Y-%m-%dT+00:00")
    timestamp_range = f"{start_date_colture}/{today_date}"

    print("\n⏳ Fetching environmental data...")
    actual_rainfall = PhosphorusStress.fetch_precipitation(location_coords, crop_name, timestamp_range)
    actual_soil_moisture = PhosphorusStress.fetch_soil_moisture(location_coords, crop_name, timestamp_range)
    actual_pH = PhosphorusStress.fetch_ph(location_coords, crop_name, timestamp_range)

    print("\n📊 Environmental Conditions:")
    print(f"Rainfall: {actual_rainfall:.2f} mm")
    print(f"Soil Moisture: {actual_soil_moisture:.2f}%")
    print(f"Soil pH: {actual_pH:.2f}")

    # Create instance and calculate
    crop = PhosphorusStress(crop_name, yield_tonnes_per_ha, phosphorus_applied_kg_per_ha, 
                           actual_rainfall, actual_soil_moisture, actual_pH)

    print("\n🔍 Results:")
    print(f"Phosphorus Use Efficiency: {crop.calculate_PUE():.3f}")
    print("\n💡 Recommendation:")
    print(crop.recommend_biosimulants())