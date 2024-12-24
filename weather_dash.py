import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import timedelta

# API URL
API_URL = "https://api.thingspeak.com/channels/1596152/feeds.json?results=800"

# Function to fetch data from the API
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_api_data():
    response = requests.get(API_URL)
    if response.status_code == 200:
        data = response.json()
        feeds = data["feeds"]

        # Convert feeds into a DataFrame
        df = pd.DataFrame(feeds)
        df["created_at"] = pd.to_datetime(df["created_at"])  # Convert timestamps
        df = df.rename(
            columns={
                "field1": "PM2.5",
                "field2": "PM10",
                "field3": "Ozone",
                "field4": "Humidity",
                "field5": "Temperature",
                "field6": "CO",
            }
        )
        # Convert numeric fields
        for field in ["PM2.5", "PM10", "Ozone", "Humidity", "Temperature", "CO"]:
            df[field] = pd.to_numeric(df[field], errors="coerce")
        return df
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()

# Page Title
st.title("Air Quality Monitoring Dashboard")
st.write("### Data refreshes automatically every 1 hour.")

# Fetch data
data = fetch_api_data()

if not data.empty:
    # Extract year and month for dropdown
    data["Year"] = data["created_at"].dt.year
    data["Month"] = data["created_at"].dt.month_name()

    # Sidebar Filters
    st.sidebar.header("Filters")
    selected_year = st.sidebar.selectbox("Select Year", options=sorted(data["Year"].unique()), index=0)
    selected_month = st.sidebar.selectbox("Select Month", options=data["Month"].unique(), index=0)
    selected_field = st.sidebar.selectbox("Select Metric", ["Temperature", "Humidity", "PM2.5", "PM10", "CO", "Ozone"], index=0)

    # Filter data based on selection
    filtered_data = data[(data["Year"] == selected_year) & (data["Month"] == selected_month)]

    if not filtered_data.empty:
        st.write(f"## Data for {selected_month} {selected_year}")

        # Ensure created_at is set as index for resampling
        filtered_data.set_index("created_at", inplace=True)
        filtered_data = filtered_data.resample('2H').mean().reset_index()

        # Time-Series Line Charts
        st.subheader("Hourly Trends")

        col1, col2 = st.columns(2, gap="large")
        with col1:
            fig1 = px.line(filtered_data, x="created_at", y="Temperature", markers=True,
                           title="Temperature Over Time (2-Hour Intervals)")
            fig1.update_layout(xaxis_title="Time", yaxis_title="Temperature (°C)")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            fig2 = px.line(filtered_data, x="created_at", y="Humidity", markers=True,
                           title="Humidity Over Time (2-Hour Intervals)")
            fig2.update_layout(xaxis_title="Time", yaxis_title="Humidity (%)")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col3, col4 = st.columns(2, gap="large")
        with col3:
            fig3 = px.line(filtered_data, x="created_at", y="PM2.5", markers=True,
                           title="PM2.5 Levels Over Time (2-Hour Intervals)")
            fig3.update_layout(xaxis_title="Time", yaxis_title="PM2.5 (µg/m³)")
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            fig4 = px.line(filtered_data, x="created_at", y="PM10", markers=True,
                           title="PM10 Levels Over Time (2-Hour Intervals)")
            fig4.update_layout(xaxis_title="Time", yaxis_title="PM10 (µg/m³)")
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("Other Visuals")

        col5, col6 = st.columns(2, gap="large")
        with col5:
            fig5 = px.line(filtered_data, x="created_at", y="CO", markers=True,
                           title="CO Levels Over Time (2-Hour Intervals)")
            fig5.update_layout(xaxis_title="Time", yaxis_title="CO (ppm)")
            st.plotly_chart(fig5, use_container_width=True)

        with col6:
            fig6 = px.line(filtered_data, x="created_at", y="Ozone", markers=True,
                           title="Ozone Levels Over Time (2-Hour Intervals)")
            fig6.update_layout(xaxis_title="Time", yaxis_title="Ozone (ppb)")
            st.plotly_chart(fig6, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.warning(f"No data available for {selected_month} {selected_year}.")
else:
    st.warning("No data available to display.")
