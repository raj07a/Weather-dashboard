import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# API URL
API_URL = "https://api.thingspeak.com/channels/1596152/feeds.json?results=1000"

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

        # Resample to 1-hour intervals
        df.set_index("created_at", inplace=True)
        df = df.resample("1H").mean().reset_index()

        return df
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()

# Page Title
st.title("Air Quality Monitoring Dashboard")
st.write("### Data is refreshed every 1 hour.")

# Fetch data
data = fetch_api_data()

if not data.empty:
    # Extract years and months from data
    data["Year"] = data["created_at"].dt.year
    data["Month"] = data["created_at"].dt.month
    data["Hour"] = data["created_at"].dt.hour

    # Dropdowns for year and month
    years = sorted(data["Year"].unique())
    selected_year = st.selectbox("Select Year", years)

    months = sorted(data[data["Year"] == selected_year]["Month"].unique())
    selected_month = st.selectbox("Select Month", months)

    # Filter data based on selected year and month
    filtered_data = data[(data["Year"] == selected_year) & (data["Month"] == selected_month)]

    if not filtered_data.empty:
        st.write(f"### Data for {selected_year}-{selected_month:02d}")

        # Line graphs for hourly trends
        metrics = ["PM2.5", "PM10", "Ozone", "Humidity", "Temperature", "CO"]
        for metric in metrics:
            st.subheader(f"{metric} Levels")
            fig = px.line(
                filtered_data,
                x="created_at",
                y=metric,
                title=f"{metric} Levels Over Time",
                labels={"created_at": "Time", metric: metric},
                markers=True,
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No data available for {selected_year}-{selected_month:02d}.")
else:
    st.warning("No data available to display.")
