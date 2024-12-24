import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# API URL for data and control
DATA_API_URL = "https://api.thingspeak.com/channels/1596152/feeds.json?results=1000"
CONTROL_API_URL = "https://api.thingspeak.com/update"

# Function to fetch data from the API
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_api_data():
    response = requests.get(DATA_API_URL)
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

# Function to send ON/OFF signal to the cloud
def send_control_signal(state):
    response = requests.post(CONTROL_API_URL, data={"field1": 1 if state else 0})
    if response.status_code == 200:
        st.success(f"Machine turned {'ON' if state else 'OFF'} successfully!")
    else:
        st.error(f"Failed to send control signal: {response.status_code}")

# Page Title
st.title("Air Quality Monitoring Dashboard")
st.write("### Data refreshes every hour.")

# On/Off Switch for Machine Control
st.sidebar.subheader("Machine Control")
machine_state = st.sidebar.checkbox("Turn Machine ON")
if st.sidebar.button("Send Control Signal"):
    send_control_signal(machine_state)

# Fetch data
data = fetch_api_data()

if not data.empty:
    # Sidebar Dropdown for Year
    st.sidebar.subheader("Filter Data by Year")
    years = sorted(data["created_at"].dt.year.unique())
    selected_year = st.sidebar.selectbox("Select Year", years)

    # Filter data based on selected year
    filtered_data = data[data["created_at"].dt.year == selected_year]

    if not filtered_data.empty:
        st.write(f"### Hourly Data for {selected_year}")

        # Line graphs for hourly trends
        metrics = ["PM2.5", "PM10", "Ozone", "Humidity", "Temperature", "CO"]
        for metric in metrics:
            st.subheader(f"{metric} Levels Over Time")
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
        st.warning(f"No data available for {selected_year}.")
else:
    st.warning("No data available to display.")
