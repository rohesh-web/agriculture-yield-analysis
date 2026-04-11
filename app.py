import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from collections import Counter, defaultdict

st.set_page_config(
    page_title="Agriculture Yield Analysis",
    page_icon="🌾",
    layout="wide"
)

st.title("🌾 Agriculture Yield Analysis & Seasonal Trend")
st.markdown("Real-time weather + Historical crop yield data — India")

# ── Load Dataset ───────────────────────────────────────
@st.cache_data
def load_data():
    url = 'https://drive.google.com/uc?export=download&id=1tvZEcFor8V2-3f_UAjoX2oNy5p082Lf8'
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    df['YIELD (Kg per ha)']      = pd.to_numeric(df['YIELD (Kg per ha)'],      errors='coerce')
    df['PRODUCTION (1000 tons)'] = pd.to_numeric(df['PRODUCTION (1000 tons)'], errors='coerce')
    df['AREA (1000 ha)']         = pd.to_numeric(df['AREA (1000 ha)'],          errors='coerce')
    df.dropna(subset=['YIELD (Kg per ha)'], inplace=True)
    df = df[df['YIELD (Kg per ha)'] > 0]
    return df

df = load_data()

# ── Sidebar Filters ────────────────────────────────────
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

# Year range filter
min_year = int(df_state['Year'].min())
max_year = int(df_state['Year'].max())
year_range = st.sidebar.slider(
    "Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)
df_state = df_state[(df_state['Year'] >= year_range[0]) & (df_state['Year'] <= year_range[1])]

# ── Today's Date Info ──────────────────────────────────
st.markdown("---")
today = datetime.now()
st.info(f"Today: {today.strftime('%d %B %Y')}  |  Dataset covers: {min_year} to {max_year}  |  Current season data fetched via live weather API")

# ── Top Metrics ────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Records",     f"{len(df):,}")
col2.metric("State Records",     f"{len(df_state):,}")
col3.metric("Avg Yield (Kg/ha)", f"{df_state['YIELD (Kg per ha)'].mean():.0f}")
col4.metric("Years Covered",     f"{year_range[0]} - {year_range[1]}")

# ── Seasonal Analysis ──────────────────────────────────
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

# ── Yearly Trend ───────────────────────────────────────
st.subheader("Year-over-Year Yield Trend")
yearly = df_state.groupby(['Year','Crops'])['YIELD (Kg per ha)'].mean().round(2).reset_index()
fig2 = px.line(
    yearly, x='Year', y='YIELD (Kg per ha)',
    color='Crops',
    title=f"Yearly Trend — {sel_state}",
    labels={'YIELD (Kg per ha)': 'Yield (Kg/ha)'}
)
st.plotly_chart(fig2, use_container_width=True)

# ── Crop Summary ───────────────────────────────────────
st.subheader("Crop Summary")
summary = df_state.groupby('Crops')['YIELD (Kg per ha)'].agg(['mean','max','min']).round(2)
summary.columns = ['Avg Yield','Max Yield','Min Yield']
st.dataframe(summary, use_container_width=True)

# ── District-wise Analysis ─────────────────────────────
st.markdown("---")
st.subheader("District-wise Yield Analysis")
district_data = df_state.groupby('Dist Name')['YIELD (Kg per ha)'].mean().round(2).reset_index()
district_data.columns = ['District', 'Avg Yield (Kg/ha)']
district_data = district_data.sort_values('Avg Yield (Kg/ha)', ascending=False)
fig5 = px.bar(
    district_data,
    x='District', y='Avg Yield (Kg/ha)',
    title=f"District-wise Avg Yield — {sel_state} — {sel_crop}",
    color='Avg Yield (Kg/ha)',
    color_continuous_scale='Greens'
)
fig5.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig5, use_container_width=True)
st.dataframe(district_data, use_container_width=True)

# ── DISASTER YEAR DETECTION ────────────────────────────
st.markdown("---")
st.subheader("Disaster Year Detection — Yield Loss Analysis")
st.markdown("Years where yield dropped significantly compared to previous year")

yearly_avg = df_state.groupby('Year')['YIELD (Kg per ha)'].mean().reset_index()
yearly_avg.columns = ['Year', 'Avg Yield']
yearly_avg = yearly_avg.sort_values('Year')
yearly_avg['Prev Yield']   = yearly_avg['Avg Yield'].shift(1)
yearly_avg['Yield Change'] = yearly_avg['Avg Yield'] - yearly_avg['Prev Yield']
yearly_avg['Change %']     = ((yearly_avg['Yield Change'] / yearly_avg['Prev Yield']) * 100).round(2)
yearly_avg['Status']       = yearly_avg['Change %'].apply(
    lambda x: '🔴 Disaster' if x < -20
    else ('🟡 Warning' if x < -10
    else '🟢 Normal')
)

disaster_years = yearly_avg[yearly_avg['Change %'] < -10].sort_values('Change %')

col1, col2 = st.columns(2)
with col1:
    fig_dis = px.bar(
        yearly_avg.dropna(),
        x='Year', y='Change %',
        color='Status',
        color_discrete_map={
            '🔴 Disaster': '#E24B4A',
            '🟡 Warning':  '#EF9F27',
            '🟢 Normal':   '#1D9E75'
        },
        title='Year-over-Year Yield Change %'
    )
    fig_dis.add_hline(y=-10, line_dash='dash', line_color='orange', annotation_text='Warning threshold')
    fig_dis.add_hline(y=-20, line_dash='dash', line_color='red',    annotation_text='Disaster threshold')
    st.plotly_chart(fig_dis, use_container_width=True)

with col2:
    st.markdown("**Disaster / Warning Years:**")
    if not disaster_years.empty:
        for _, row in disaster_years.iterrows():
            st.error(f"{row['Status']}  Year: {int(row['Year'])}  |  Drop: {row['Change %']}%  |  Yield: {row['Avg Yield']:.0f} Kg/ha")
    else:
        st.success("No major disaster years found for selected filters!")

# ── YIELD LOSS CALCULATOR ──────────────────────────────
st.markdown("---")
st.subheader("Yield Loss Calculator")
st.markdown("Calculate total yield loss and financial impact for a disaster year")

col1, col2, col3 = st.columns(3)
with col1:
    selected_year = st.selectbox(
        "Select Year to Analyze",
        sorted(df_state['Year'].unique(), reverse=True)
    )
with col2:
    price_per_kg = st.number_input(
        "Market Price (₹ per Kg)",
        min_value=1, max_value=10000,
        value=25
    )
with col3:
    area_input = st.number_input(
        "Area (in 1000 ha)",
        min_value=1, max_value=10000,
        value=100
    )

year_data  = df_state[df_state['Year'] == selected_year]
prev_data  = df_state[df_state['Year'] == selected_year - 1]

if not year_data.empty and not prev_data.empty:
    curr_yield = year_data['YIELD (Kg per ha)'].mean()
    prev_yield = prev_data['YIELD (Kg per ha)'].mean()
    loss_kg    = max(0, prev_yield - curr_yield)
    loss_pct   = (loss_kg / prev_yield * 100) if prev_yield > 0 else 0
    total_loss_kg    = loss_kg * area_input * 1000
    financial_loss   = total_loss_kg * price_per_kg

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Year Yield",  f"{curr_yield:.0f} Kg/ha")
    col2.metric("Previous Year Yield", f"{prev_yield:.0f} Kg/ha")
    col3.metric("Yield Loss",          f"{loss_kg:.0f} Kg/ha", f"-{loss_pct:.1f}%")
    col4.metric("Financial Loss",      f"₹{financial_loss:,.0f}")

    if loss_pct > 20:
        st.error(f"🔴 DISASTER YEAR — {selected_year} had a {loss_pct:.1f}% yield drop!")
    elif loss_pct > 10:
        st.warning(f"🟡 WARNING — {selected_year} had a {loss_pct:.1f}% yield drop.")
    else:
        st.success(f"🟢 NORMAL — {selected_year} yield is stable.")

# ── COST CALCULATOR ────────────────────────────────────
st.markdown("---")
st.subheader("Crop Cost & Profit Calculator")
st.markdown("Estimate farming cost and profit based on yield")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Input Costs (₹ per hectare)**")
    seed_cost      = st.number_input("Seed Cost",        value=2000,  step=100)
    fertilizer     = st.number_input("Fertilizer Cost",  value=4000,  step=100)
    labor          = st.number_input("Labor Cost",       value=6000,  step=100)
    irrigation     = st.number_input("Irrigation Cost",  value=3000,  step=100)
    other          = st.number_input("Other Costs",      value=2000,  step=100)
    total_cost     = seed_cost + fertilizer + labor + irrigation + other

with col2:
    st.markdown("**Revenue Calculation**")
    calc_crop = st.selectbox("Select Crop", crops if crops else ["All"])
    calc_year = st.selectbox("Select Year", sorted(df_state['Year'].unique(), reverse=True), key="calc_year")

    crop_df   = df_state[df_state['Crops'] == calc_crop] if calc_crop != "All" else df_state
    year_df   = crop_df[crop_df['Year'] == calc_year]
    avg_yield = year_df['YIELD (Kg per ha)'].mean() if not year_df.empty else 0

    sell_price  = st.number_input("Selling Price (₹/Kg)", value=25, step=1)
    calc_area   = st.number_input("Your Farm Area (hectares)", value=1, step=1)

    revenue     = avg_yield * sell_price * calc_area
    total_cost_farm = total_cost * calc_area
    profit      = revenue - total_cost_farm
    roi         = (profit / total_cost_farm * 100) if total_cost_farm > 0 else 0

    st.markdown("---")
    st.metric("Expected Yield",   f"{avg_yield:.0f} Kg/ha")
    st.metric("Total Revenue",    f"₹{revenue:,.0f}")
    st.metric("Total Cost",       f"₹{total_cost_farm:,.0f}")
    st.metric("Net Profit/Loss",  f"₹{profit:,.0f}", f"ROI: {roi:.1f}%")

    if profit > 0:
        st.success(f"✅ Profitable! You earn ₹{profit:,.0f}")
    else:
        st.error(f"❌ Loss! You lose ₹{abs(profit):,.0f}")

# ── Real-Time Weather ──────────────────────────────────
st.markdown("---")
st.subheader("Real-Time Weather — Tamil Nadu Districts")
st.markdown(f"Live 7-day forecast as of {today.strftime('%d %B %Y')}")

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
                "latitude": lat, "longitude": lon,
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
            color='Rainfall mm', color_continuous_scale='Blues'
        )
        st.plotly_chart(fig3, use_container_width=True)
    with col2:
        fig4 = px.bar(
            weather_summary.reset_index(),
            x='District', y='Temp Max',
            title='7-Day Avg Max Temperature by District',
            color='Temp Max', color_continuous_scale='Reds'
        )
        st.plotly_chart(fig4, use_container_width=True)
    st.dataframe(weather_summary, use_container_width=True)

st.markdown("---")
st.caption(f"Data: Kaggle (1984-2017) + Open-Meteo Live API | Last updated: {today.strftime('%d %B %Y')}")
