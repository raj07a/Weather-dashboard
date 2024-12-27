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
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")  # Convert timestamps
        if df["created_at"].isnull().any():
            st.error("Some timestamps could not be parsed. Check data format.")
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

    # Machine Control Toggle
    if st.sidebar.button("Turn ON Machine"):
        # Placeholder for sending an ON signal to the cloud
        st.sidebar.success("Machine Turned ON")
    if st.sidebar.button("Turn OFF Machine"):
        # Placeholder for sending an OFF signal to the cloud
        st.sidebar.warning("Machine Turned OFF")

    # Filter data based on selection
    filtered_data = data[(data["Year"] == selected_year) & (data["Month"] == selected_month)]

    if not filtered_data.empty:
        st.write(f"## Data for {selected_month} {selected_year}")

        # Resample data to 1-hour intervals
        filtered_data = filtered_data.dropna()
        filtered_data = filtered_data.set_index("created_at").resample("1H").mean().reset_index()

        # Time-Series Line Charts
        st.subheader("Hourly Trends")

        for field in ["PM2.5", "PM10", "Ozone", "Humidity", "Temperature", "CO"]:
            fig = px.line(filtered_data, x="created_at", y=field, markers=True,
                          title=f"{field} Over Time (1-Hour Intervals)")
            fig.update_layout(xaxis_title="Time", yaxis_title=f"{field}")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.warning(f"No data available for {selected_month} {selected_year}.")
else:
    st.warning("No data available to display.")
