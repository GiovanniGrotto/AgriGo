import requests
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env


def fetch_daily_temperatures(latitude, longitude):
    url = "https://services.cehub.syngenta-ais.com/api/Forecast/ShortRangeForecastDaily"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "supplier": "Meteoblue",
        "measureLabel": "TempAir_DailyMax (C); TempAir_DailyMin (C); TempAir_DailyAvg (C); Precip_DailySum (mm); Referenceevapotranspiration_DailySum (mm); Soilmoisture_0to10cm_DailyAvg (vol%)",
        "top": 30,
        "format": "json"
    }
    headers = {
        "accept": "*/*",
        "ApiKey": os.getenv('LONG_KEY')
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


def compute_drought_risk(rainfall, evapotranspiration, soil_moisture, avg_temp):
    # Calculate the Drought Index (DI)
    DI = (rainfall - evapotranspiration + soil_moisture) / avg_temp
    
    # Interpret the Drought Index (DI)
    if DI > 1:
        return "No risk"
    elif DI == 1:
        return "Medium risk"
    else:
        return "High risk"


def get_value_for_measure(daily_data, measure_label):
    """Extract the value for a specific measure (e.g., TempAir_DailyMax) from the daily data."""
    for entry in daily_data:
        # Debugging print to see the exact measure labels
        # print(f"Checking: {entry['measureLabel']} against {measure_label}")
        if entry['measureLabel'].strip() == measure_label.strip():
            return float(entry['dailyValue'])
    return None

def get_stress_recommendations(diurnal_heat_stress, nighttime_heat_stress, frost_stress, drought_risk):
    recommendations = []
    
    # High temperature stress recommendations
    if diurnal_heat_stress > 6:
        recommendations.append(
            "High temperature stress detected! Recommendations:\n"
            "- Apply biostimulant containing vegetal extracts to enhance heat tolerance\n"
            "- Consider additional irrigation during peak heat hours\n"
            "- Use of foliar applications to reduce plant stress"
        )
    
    # Night temperature stress recommendations
    if nighttime_heat_stress > 6:
        recommendations.append(
            "Night temperature stress detected! Recommendations:\n"
            "- Apply biostimulant to help plant recovery during night hours\n"
            "- Monitor plant health closely\n"
            "- Consider adjusting irrigation timing"
        )
    
    # Frost stress recommendations
    if frost_stress > 6:
        recommendations.append(
            "Frost stress risk detected! Recommendations:\n"
            "- Apply protective biostimulant before forecasted frost events\n"
            "- Consider frost protection methods\n"
            "- Monitor soil moisture levels"
        )
    
    # Drought stress recommendations
    if drought_risk == "High risk":
        recommendations.append(
            "High drought risk detected! Recommendations:\n"
            "- Apply biostimulant to enhance drought tolerance\n"
            "- Optimize irrigation scheduling\n"
            "- Consider soil moisture conservation techniques"
        )
    
    return recommendations


def print_daily_risks(daily_data, crop):
    """Print the risk levels and recommendations for each day with emojis."""
    data_by_date = defaultdict(list)
    for entry in daily_data:
        data_by_date[entry['date']].append(entry)

    for date, data in data_by_date.items():
        tmax = get_value_for_measure(data, 'TempAir_DailyMax (C)')
        tmin = get_value_for_measure(data, 'TempAir_DailyMin (C)')
        avg_temp = get_value_for_measure(data, 'TempAir_DailyAvg (C)')
        rainfall = get_value_for_measure(data, 'Precip_DailySum (mm)')
        evapotranspiration = get_value_for_measure(data, 'Referenceevapotranspiration_DailySum (mm)')
        soil_moisture = get_value_for_measure(data, 'Soilmoisture_0to10cm_DailyAvg (vol%)')

        if any(x is None for x in [tmax, tmin, avg_temp, rainfall, evapotranspiration, soil_moisture]):
            print(f"⚠️ Missing data for {date}")
            continue

        # Compute the different stress factors
        diurnal_heat_stress = compute_diurnal_heat_stress(tmax, crop)
        nighttime_heat_stress = compute_nighttime_heat_stress(tmin, crop)
        frost_stress = compute_frost_stress(tmin, crop)
        drought_risk = compute_drought_risk(rainfall, evapotranspiration, soil_moisture, avg_temp)

        # Print the results
        print(f"\n📅 Date: {date[:10]}")
        print(f"  🌡️ Diurnal Heat Stress: {diurnal_heat_stress:.2f}")
        print(f"  🌙 Nighttime Heat Stress: {nighttime_heat_stress:.2f}")
        print(f"  ❄️ Frost Stress: {frost_stress:.2f}")
        print(f"  💧 Drought Risk: {drought_risk}")

        # Get and print recommendations if needed
        recommendations = get_stress_recommendations(
            diurnal_heat_stress, 
            nighttime_heat_stress, 
            frost_stress, 
            drought_risk
        )
        
        if recommendations:
            print("\n⚠️ RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"🔸 {rec}")
            print("\n📝 Note: Our biostimulant products contain selected vegetal extracts that help plants:")
            print("🌱 - Tolerate and quickly overcome stress conditions")
            print("🌾 - Preserve yield during stress periods")
            print("🌿 - Optimize plant growth when applied regularly")


def stress():
    print("🌍 Weather Risk Assessment Tool")
    latitude = float((input("📍 Enter latitude: ")))
    longitude = float((input("📍 Enter longitude: ")))
    crop = input("🌱 Enter crop (e.g. Rice, Soybean, Cotton, etc.): ")
    print("\n⏳ Fetching data...")
    daily_data = fetch_daily_temperatures(latitude, longitude)
    print("\n📊 Analysis Results:")
    print_daily_risks(daily_data, crop)