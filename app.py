import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
from collections import Counter, defaultdict

st.set_page_config(
    page_title="Agriculture Yield Analysis",
    page_icon="🌾",
    layout="wide"
)

st.title("🌾 Agriculture Yield Analysis & Seasonal Trend")
st.markdown("Real-time weather + Historical crop yield data for Tamil Nadu")

@st.cache_data
def load_data():
    df = pd.read_csv('All-India District-wise Crop and Climate Dataset (19842017).csv')
    df.columns = df.columns.str.strip()
    df['YIELD (Kg per ha)']      = pd.to_numeric(df['YIELD (Kg per ha)'],      errors='coerce')
    df['PRODUCTION (1000 tons)'] = pd.to_numeric(df['PRODUCTION (1000 tons)'], errors='coerce')
    df['AREA (1000 ha)']         = pd.to_numeric(df['AREA (1000 ha)'],          errors='coerce')
    df.dropna(subset=['YIELD (Kg per ha)'], inplace=True)
    df = df[df['YIELD (Kg per ha)'] > 0]
    return df

df = load_data()

st.sidebar.header("Filters")
states    = sorted(df['State Name'].str.title().unique())
sel_state = st.sidebar.selectbox("Select State", states, index=states.index("Tamil Nadu"))
df_state  = df[df['State Name'].str.lower() == sel_state.lower()]

crops     = sorted(df_state['Crops'].unique())
sel_crop  = st.sidebar.selectbox("Select Crop", ["All"] + crops)
if sel_crop != "All":
    df_state = df_state[df_state['Crops'] == sel_crop]

seasons    = sorted(df_state['Season'].unique())
sel_season = st.sidebar.selectbox("Select Season", ["All"] + seasons)
if sel_season != "All":
    df_state = df_state[df_state['Season'] == sel_season]

st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Records",     f"{len(df):,}")
col2.metric("State Records",     f"{len(df_state):,}")
col3.metric("Avg Yield (Kg/ha)", f"{df_state['YIELD (Kg per ha)'].mean():.0f}")
col4.metric("Years Covered",     f"{int(df_state['Year'].min())} - {int(df_state['Year'].max())}")

st.markdown("---")
st.subheader("Seasonal Average Yield")
seasonal = df_state.groupby(['Crops','Season'])['YIELD (Kg per ha)'].mean().round(2).reset_index()
fig1 = px.bar(
    seasonal, x='Crops', y='YIELD (Kg per ha)',
    color='Season', barmode='group',
    title=f"Seasonal Yield — {sel_state}",
    labels={'YIELD (Kg per ha)': 'Yield (Kg/ha)'}
)
st.plotly_chart(fig1, use_container_width=True)

st.subheader("Year-over-Year Yield Trend")
yearly = df_state.groupby(['Year','Crops'])['YIELD (Kg per ha)'].mean().round(2).reset_index()
fig2 = px.line(
    yearly, x='Year', y='YIELD (Kg per ha)',
    color='Crops',
    title=f"Yearly Trend — {sel_state}",
    labels={'YIELD (Kg per ha)': 'Yield (Kg/ha)'}
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Crop Summary")
summary = df_state.groupby('Crops')['YIELD (Kg per ha)'].agg(['mean','max','min']).round(2)
summary.columns = ['Avg Yield','Max Yield','Min Yield']
st.dataframe(summary, use_container_width=True)

st.markdown("---")
st.subheader("District-wise Yield Analysis")
district_data = df_state.groupby('Dist Name')['YIELD (Kg per ha)'].mean().round(2).reset_index()
district_data.columns = ['District', 'Avg Yield (Kg/ha)']
district_data = district_data.sort_values('Avg Yield (Kg/ha)', ascending=False)
fig5 = px.bar(
    district_data,
    x='District',
    y='Avg Yield (Kg/ha)',
    title=f"District-wise Avg Yield — {sel_state} — {sel_crop}",
    color='Avg Yield (Kg/ha)',
    color_continuous_scale='Greens'
)
fig5.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig5, use_container_width=True)
st.dataframe(district_data, use_container_width=True)

st.markdown("---")
st.subheader("Real-Time Weather — Tamil Nadu Districts")

DISTRICTS = {
    "Coimbatore":  (11.0168, 76.9558),
    "Chennai":     (13.0827, 80.2707),
    "Madurai":     (9.9252,  78.1198),
    "Salem":       (11.6643, 78.1460),
    "Trichy":      (10.7905, 78.7047),
    "Erode":       (11.3410, 77.7172),
    "Tirunelveli": (8.7139,  77.7567),
}

@st.cache_data(ttl=3600)
def fetch_all_weather():
    all_data = []
    for name, (lat, lon) in DISTRICTS.items():
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": ["temperature_2m_max","temperature_2m_min",
                          "precipitation_sum","relative_humidity_2m_mean"],
                "timezone": "Asia/Kolkata",
                "forecast_days": 7
            }
            r = requests.get(url, params=params, timeout=10)
            d = r.json()['daily']
            temp_df = pd.DataFrame({
                'Date':        d['time'],
                'Temp Max':    d['temperature_2m_max'],
                'Temp Min':    d['temperature_2m_min'],
                'Rainfall mm': d['precipitation_sum'],
                'Humidity %':  d['relative_humidity_2m_mean'],
                'District':    name
            })
            all_data.append(temp_df)
        except Exception as e:
            st.warning(f"Could not fetch {name}: {e}")
    return pd.concat(all_data, ignore_index=True) if all_data else None

weather_df = fetch_all_weather()

if weather_df is not None:
    weather_summary = weather_df.groupby('District')[['Temp Max','Rainfall mm','Humidity %']].mean().round(2)

    col1, col2 = st.columns(2)
    with col1:
        fig3 = px.bar(
            weather_summary.reset_index(),
            x='District', y='Rainfall mm',
            title='7-Day Avg Rainfall by District',
            color='Rainfall mm',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        fig4 = px.bar(
            weather_summary.reset_index(),
            x='District', y='Temp Max',
            title='7-Day Avg Max Temperature by District',
            color='Temp Max',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.dataframe(weather_summary, use_container_width=True)

st.markdown("---")
st.caption("Data: Kaggle (1984-2017) + Open-Meteo Live API")