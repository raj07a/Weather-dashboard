import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime

# Debugging: Add logging
st.write("App Loaded")

# API URL
API_URL = "https://api.thingspeak.com/channels/1596152/feeds.json?results=1000"

@st.cache_data(ttl=3600)
def fetch_api_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            feeds = data["feeds"]
            df = pd.DataFrame(feeds)
            st.write("Raw DataFrame:", df.head())  # Debugging: Show raw data

            # Convert created_at to datetime
            df["created_at"] = pd.to_datetime(df["created_at"])
            st.write("Timestamps Converted:", df["created_at"].head())  # Debugging

            # Resample to hourly
            df.set_index("created_at", inplace=True)
            df = df.resample("1H").mean().reset_index()
            st.write("Resampled Data:", df.head())  # Debugging

            return df
        else:
            st.error(f"Failed to fetch data: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Fetch data
data = fetch_api_data()

if not data.empty:
    st.write("Processed Data Available:", data.head())  # Debugging
else:
    st.warning("No data available to display.")
