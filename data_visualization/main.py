import requests
from collections import defaultdict

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
            print(f"Found {measure_label} with value: {entry['dailyValue']}")
            return float(entry['dailyValue'])
    return None

def print_daily_risks(daily_data, crop):
    """Print the risk levels for each day based on the data."""
    # Group the data by date
    data_by_date = defaultdict(list)
    for entry in daily_data:
        data_by_date[entry['date']].append(entry)

    print("Data by date:")
    for date in data_by_date:
        print(date)

    for date, data in data_by_date.items():
        tmax = get_value_for_measure(data, 'TempAir_DailyMax (C)')
        tmin = get_value_for_measure(data, 'TempAir_DailyMin (C)')
        avg_temp = get_value_for_measure(data, 'TempAir_DailyAvg (C)')
        rainfall = get_value_for_measure(data, 'Precip_DailySum (mm)')
        evapotranspiration = get_value_for_measure(data, 'Referenceevapotranspiration_DailySum (mm)')
        soil_moisture = get_value_for_measure(data, 'Soilmoisture_0to10cm_DailyAvg (vol%)')

        if tmax is None or tmin is None or avg_temp is None or rainfall is None or evapotranspiration is None or soil_moisture is None:
            print(f"Missing data for {date}")
            print(f"tmax: {tmax}, tmin: {tmin}, avg_temp: {avg_temp}, rainfall: {rainfall}, evapotranspiration: {evapotranspiration}, soil_moisture: {soil_moisture}")
            continue

        # Compute the different stress factors
        diurnal_heat_stress = compute_diurnal_heat_stress(tmax, crop)
        nighttime_heat_stress = compute_nighttime_heat_stress(tmin, crop)
        frost_stress = compute_frost_stress(tmin, crop)
        drought_risk = compute_drought_risk(rainfall, evapotranspiration, soil_moisture, avg_temp)

        # Print the results
        print(f"Date: {date}")
        print(f"  Diurnal Heat Stress: {diurnal_heat_stress}")
        print(f"  Nighttime Heat Stress: {nighttime_heat_stress}")
        print(f"  Frost Stress: {frost_stress}")
        print(f"  Drought Risk: {drought_risk}")
        print()

if __name__ == "__main__":
    daily_data = fetch_daily_temperatures(47.5, 7.5)
    
    # Choose a crop for analysis (e.g., Soybean)
    crop = "Soybean"
    
    print_daily_risks(daily_data, crop)
