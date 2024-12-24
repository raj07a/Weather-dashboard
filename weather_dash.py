import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime

# Set page layout to wide
st.set_page_config(layout="wide", page_title="Full-Screen Air Quality Dashboard")

# Inject custom CSS for layout adjustments
st.markdown(
    """
    <style>
    .css-1d391kg {padding: 0rem;}  /* Remove default padding */
    .css-18e3th9 {padding: 0rem;}  /* Remove sidebar padding */
    .css-1cpxqw2 {max-width: 100%;} /* Increase main container width */
    </style>
    """,
    unsafe_allow_html=True,
)

# API URL
API_URL = "https://api.thingspeak.com/channels/1596152/feeds.json?results=1000"

# Function to fetch data from the API
@st.cache_data(ttl=3600)  # Cache for 1 hour
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

        # Resample data to hourly intervals
        df.set_index("created_at", inplace=True)
        df = df.resample("1H").mean().reset_index()
        return df
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()

# Initialize session state for data flow
if "data_flow" not in st.session_state:
    st.session_state.data_flow = True

# Sidebar Controls
st.sidebar.title("Controls")
data_flow = st.sidebar.checkbox("Enable Data Flow", value=st.session_state.data_flow)
st.session_state.data_flow = data_flow

# Fetch data if data flow is enabled
if data_flow:
    data = fetch_api_data()
else:
    st.warning("Data flow is paused. Toggle the switch to fetch data.")
    data = pd.DataFrame()

# Filter by date if data is available
if not data.empty:
    st.sidebar.subheader("Select Date")
    available_dates = data["created_at"].dt.date.unique()
    selected_date = st.sidebar.selectbox("Available Dates", options=available_dates)

    # Filter data for the selected date
    filtered_data = data[data["created_at"].dt.date == selected_date]

    st.title(f"Air Quality Monitoring Dashboard - {selected_date}")
    st.write("### Data is displayed at hourly intervals.")

    # Display latest data
    st.write("## Latest Data Entries")
    st.dataframe(filtered_data, height=200)

    # Row 1: PM2.5 and PM10
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("PM2.5 Levels Over Time")
        fig1 = px.line(filtered_data, x="created_at", y="PM2.5", markers=True, title="PM2.5 Over Time")
        fig1.update_layout(xaxis_title="Time (Hourly)", yaxis_title="PM2.5 Levels")
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.subheader("PM10 Levels Over Time")
        fig2 = px.line(filtered_data, x="created_at", y="PM10", markers=True, title="PM10 Over Time")
        fig2.update_layout(xaxis_title="Time (Hourly)", yaxis_title="PM10 Levels")
        st.plotly_chart(fig2, use_container_width=True)

    # Row 2: Ozone and Temperature vs Humidity
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Ozone Levels Over Time")
        fig3 = px.line(filtered_data, x="created_at", y="Ozone", markers=True, title="Ozone Levels Over Time")
        fig3.update_layout(xaxis_title="Time (Hourly)", yaxis_title="Ozone Levels")
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        st.subheader("Temperature vs Humidity (Bubble Chart)")
        fig4 = px.scatter(
            filtered_data,
            x="Temperature",
            y="Humidity",
            size="PM2.5",
            color="PM10",
            title="Temperature vs Humidity",
        )
        fig4.update_layout(xaxis_title="Temperature (°C)", yaxis_title="Humidity (%)")
        st.plotly_chart(fig4, use_container_width=True)

    # Row 3: Correlation Heatmap and CO Levels
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("Correlation Heatmap")
        correlation_matrix = filtered_data.iloc[:, 1:].corr()
        fig5, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig5)
    with col6:
        st.subheader("CO Levels Over Time")
        fig6 = px.line(filtered_data, x="created_at", y="CO", markers=True, title="CO Levels Over Time")
        fig6.update_layout(xaxis_title="Time (Hourly)", yaxis_title="CO Levels")
        st.plotly_chart(fig6, use_container_width=True)

else:
    st.warning("No data available to display.")
