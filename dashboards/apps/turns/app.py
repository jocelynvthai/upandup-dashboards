import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info, turns_data, line_items_data
from tabs.individual_turn_drilldown_tab import individual_turn_drilldown, individual_turn_summary, drilldown_filters
from tabs.economic_turn_costs_tab import economic_turn_costs_filters, economic_turn_costs

# Configure page layout
st.set_page_config(
    page_title="Turns Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info())
turns_df = turns_data(credentials)
line_items_df = line_items_data(credentials)

# Application
st.title("Turns Dashboard")
individual_turn_drilldown_tab, economic_turn_costs_tab = st.tabs(["Individual Turn Drilldown", "Economic Turn Costs",])
with individual_turn_drilldown_tab:
    filtered_line_items_df, filtered_turns_df = drilldown_filters(turns_df, line_items_df)
    individual_turn_summary(filtered_line_items_df, filtered_turns_df)
    individual_turn_drilldown(filtered_line_items_df)
with economic_turn_costs_tab:
    filtered_turns_df = economic_turn_costs_filters(turns_df)
    economic_turn_costs(filtered_turns_df)

