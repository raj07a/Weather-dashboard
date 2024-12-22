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

# Layout for visuals
if not data.empty:
    st.write("## Latest 10 Data Entries")
    st.dataframe(data, height=200)

    # Dashboard visuals with spacing and better layout
    st.write("## Dashboard Overview")

    # Row 1: Metrics
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric("PM2.5", f"{data['PM2.5'].iloc[-1]:.2f} µg/m³")
    with col2:
        st.metric("PM10", f"{data['PM10'].iloc[-1]:.2f} µg/m³")
    with col3:
        st.metric("Ozone", f"{data['Ozone'].iloc[-1]:.2f} ppb")

    st.markdown("---")  # Divider for clarity

    # Row 2: PM Levels and Ozone Levels
    col4, col5 = st.columns([2, 1])  # Wider column for line chart
    with col4:
        st.subheader("PM2.5 and PM10 Levels Over Time")
        fig1 = px.line(data, x="created_at", y=["PM2.5", "PM10"], markers=True, 
                       title="PM Levels Over Time")
        st.plotly_chart(fig1, use_container_width=True)
    with col5:
        st.subheader("Ozone Levels Over Time")
        fig2 = px.bar(data, x="created_at", y="Ozone", color="Ozone", title="Ozone Levels")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")  # Divider for clarity

    # Row 3: Scatter Plot and Correlation Heatmap
    col6, col7 = st.columns([1, 1])  # Equal width for scatter plot and heatmap
    with col6:
        st.subheader("Temperature vs Humidity")
        fig3 = px.scatter(
            data,
            x="Temperature",
            y="Humidity",
            size="PM2.5",
            color="PM10",
            title="Humidity vs Temperature",
        )
        st.plotly_chart(fig3, use_container_width=True)
    with col7:
        st.subheader("Correlation Heatmap")
        correlation_matrix = data.iloc[:, 1:].corr()
        fig4, ax = plt.subplots(figsize=(6, 5))
        sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig4)
else:
    st.warning("No data available to display.")
