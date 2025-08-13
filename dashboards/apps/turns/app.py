import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info, turns_data
from tabs.economic_turn_costs_tab import economic_turn_costs

# Configure page layout
st.set_page_config(
    page_title="Dashboard Name",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info())
turns_df = turns_data(credentials)

# Application
st.title("Turns Dashboard")

economic_turn_costs_tab, = st.tabs(["Economic Turn Costs"])
with economic_turn_costs_tab:
    economic_turn_costs(turns_df)

