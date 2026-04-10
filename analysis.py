import numpy as np
import pandas as pd
from collections import Counter, defaultdict

def load_real_data(filepath):
    try:
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip()
        df['YIELD (Kg per ha)']      = pd.to_numeric(df['YIELD (Kg per ha)'],      errors='coerce')
        df['PRODUCTION (1000 tons)'] = pd.to_numeric(df['PRODUCTION (1000 tons)'], errors='coerce')
        df['AREA (1000 ha)']         = pd.to_numeric(df['AREA (1000 ha)'],          errors='coerce')
        df.dropna(subset=['YIELD (Kg per ha)'], inplace=True)
        df = df[df['YIELD (Kg per ha)'] > 0]
        return df
    except FileNotFoundError:
        print("[ERROR] Dataset file not found.")
        return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def filter_state(df, state="tamil nadu"):
    filtered = df[df['State Name'].str.lower() == state.lower()]
    if filtered.empty:
        print(f"[WARNING] No data found for {state}")
    return filtered

def seasonal_analysis(df):
    print("\n===== Seasonal Average Yield (Kg/ha) =====")
    avg = df.groupby(['Crops', 'Season'])['YIELD (Kg per ha)'].mean().round(2)
    print(avg)

def yearly_trend(df):
    print("\n===== Year-over-Year Yield Trend =====")
    trend = df.groupby(['Crops', 'Year'])['YIELD (Kg per ha)'].mean().round(2).unstack(fill_value=0)
    print(trend)

def detect_outliers(df):
    print("\n===== Low Yield Alerts =====")
    values = df['YIELD (Kg per ha)'].dropna().values
    mean = np.mean(values)
    std  = np.std(values)
    print(f"  Mean Yield : {mean:.2f} Kg/ha")
    print(f"  Std Dev    : {std:.2f} Kg/ha")
    outliers = df[df['YIELD (Kg per ha)'] < mean - std]
    print(outliers[['Year','Dist Name','Crops','Season','YIELD (Kg per ha)']].head(10))

def top_seasons(df):
    print("\n===== Most Common High-Yield Seasons =====")
    mean = np.mean(df['YIELD (Kg per ha)'].values)
    high = df[df['YIELD (Kg per ha)'] > mean]
    freq = Counter(high['Season'])
    for season, count in freq.most_common():
        print(f"  {season}: {count} high-yield records")

def crop_summary(df):
    print("\n===== Per-Crop Summary =====")
    crop_data = defaultdict(list)
    for _, row in df.iterrows():
        crop_data[row['Crops']].append(row['YIELD (Kg per ha)'])
    for crop, yields in crop_data.items():
        arr = np.array(yields)
        print(f"  {crop:20s} | Avg: {np.mean(arr):8.1f} | Max: {np.max(arr):8.1f} | Min: {np.min(arr):.1f}")

def weather_vs_yield(df):
    print("\n===== Weather Impact on Yield =====")
    corr_rain = df['PRECTOTCORR'].corr(df['YIELD (Kg per ha)'])
    corr_temp = df['T2M_MAX'].corr(df['YIELD (Kg per ha)'])
    print(f"  Rainfall vs Yield    : {corr_rain:.3f}")
    print(f"  Temperature vs Yield : {corr_temp:.3f}")