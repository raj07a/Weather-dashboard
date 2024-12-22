import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# API URL
API_URL = "https://api.thingspeak.com/channels/1596152/feeds.json?results=10"

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
st.write("### Data is refreshed every 1 hour.")
st.write("Toggle the switch below to control the data flow.")

# Initialize session state for data flow
if "data_flow" not in st.session_state:
    st.session_state.data_flow = True

# Toggle switch for data flow
data_flow = st.checkbox("Enable Data Flow", value=st.session_state.data_flow)
st.session_state.data_flow = data_flow

if data_flow:
    data = fetch_api_data()
else:
    st.warning("Data flow is paused. Toggle the switch to fetch data.")
    data = pd.DataFrame()

# Dashboard visuals
if not data.empty:
    st.write("## Latest 10 Data Entries")
    st.dataframe(data, height=200)

    # Layout for 6 visuals in a 3x2 grid
    st.write("## Dashboard Overview")

    # Row 1: First three visuals
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("PM2.5 Levels Over Time")
        fig1 = px.line(data, x="created_at", y="PM2.5", markers=True, title="PM2.5 Over Time")
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.subheader("PM10 Levels Over Time")
        fig2 = px.line(data, x="created_at", y="PM10", markers=True, title="PM10 Over Time")
        st.plotly_chart(fig2, use_container_width=True)
    with col3:
        st.subheader("Ozone Levels Over Time")
        fig3 = px.bar(data, x="created_at", y="Ozone", color="Ozone", title="Ozone Levels")
        st.plotly_chart(fig3, use_container_width=True)

    # Row 2: Next three visuals
    col4, col5, col6 = st.columns(3)
    with col4:
        st.subheader("Temperature vs Humidity")
        fig4 = px.scatter(
            data,
            x="Temperature",
            y="Humidity",
            size="PM2.5",
            color="PM10",
            title="Humidity vs Temperature",
        )
        st.plotly_chart(fig4, use_container_width=True)
    with col5:
        st.subheader("Correlation Heatmap")
        correlation_matrix = data.iloc[:, 1:].corr()
        fig5, ax = plt.subplots(figsize=(5, 4))
        sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig5)
    with col6:
        st.subheader("CO Levels Over Time")
        fig6 = px.line(data, x="created_at", y="CO", markers=True, title="CO Levels")
        st.plotly_chart(fig6, use_container_width=True)
else:
    st.warning("No data available to display.")
