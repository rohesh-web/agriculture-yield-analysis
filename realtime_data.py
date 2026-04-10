import requests
import pandas as pd
import numpy as np
from collections import Counter

DISTRICTS = {
    "Coimbatore":  (11.0168, 76.9558),
    "Chennai":     (13.0827, 80.2707),
    "Madurai":     (9.9252,  78.1198),
    "Salem":       (11.6643, 78.1460),
    "Trichy":      (10.7905, 78.7047),
    "Erode":       (11.3410, 77.7172),
    "Tirunelveli": (8.7139,  77.7567),
}

def fetch_weather_for_district(name, lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "relative_humidity_2m_mean"
        ],
        "timezone": "Asia/Kolkata",
        "forecast_days": 7
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()['daily']
        df = pd.DataFrame({
            'date':        data['time'],
            'temp_max':    data['temperature_2m_max'],
            'temp_min':    data['temperature_2m_min'],
            'rainfall_mm': data['precipitation_sum'],
            'humidity':    data['relative_humidity_2m_mean']
        })
        df['district'] = name
        return df
    except Exception as e:
        print(f"[ERROR] Could not fetch data for {name}: {e}")
        return None

def run_realtime_analysis():
    print("\n=== Real-Time Weather Analysis - Tamil Nadu Districts ===")
    all_data = []

    for name, (lat, lon) in DISTRICTS.items():
        print(f"  Fetching {name}...")
        df = fetch_weather_for_district(name, lat, lon)
        if df is not None:
            all_data.append(df)

    if not all_data:
        print("No data fetched.")
        return

    combined = pd.concat(all_data, ignore_index=True)

    print("\n--- District-wise Average (7 Days) ---")
    summary = combined.groupby('district')[['temp_max','rainfall_mm','humidity']].mean().round(2)
    print(summary)

    best_rain = summary['rainfall_mm'].idxmax()
    hottest   = summary['temp_max'].idxmax()
    print(f"\n  Best Rainfall District : {best_rain}")
    print(f"  Hottest District       : {hottest}")

    combined.to_csv('realtime_weather.csv', index=False)
    print("\n  Data saved to realtime_weather.csv")