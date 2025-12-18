import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info, turns_data, construction_scopes_data, tickets_data, line_items_data
from tabs.summary_tab import turn_filters, total_turn_cost_over_time, turns_breakdown, turns_without_ends_dates
from tabs.individual_turn_drilldown_tab import drilldown_filters, individual_turn_timeline, individual_turn_budget_breakdown, individual_turn_drilldown, invoices_by_vendor
from tabs.economic_turn_costs_tab import economic_turn_costs_filters, economic_turn_costs

# Configure page layout
st.set_page_config(
    page_title="Turns Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown("""
    <style>
    [data-testid="stMetricLabel"] div {
        font-size: .7rem !important;
    }
    [data-testid="stMetricValue"] div {
        font-size: 1.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info())
turns_df = turns_data(credentials)
construction_scopes_df = construction_scopes_data(credentials)
tickets_df = tickets_data(credentials)
line_items_df = line_items_data(credentials)

# Application
st.title("Turns Dashboard")
st.button("Refresh All Data", on_click=st.cache_data.clear)

params = st.query_params
selected_tab = st.pills('TABS', options=["Summary", "Individual Turn Drilldown", "Economic Turn Costs"], 
                        default='Individual Turn Drilldown' if params.get('address') and params.get('move_out_date') else 'Summary',
                        selection_mode = "single", 
                        label_visibility="hidden"
)
if selected_tab == "Summary":
    filtered_turns_df = turn_filters(turns_df)
    total_turn_cost_over_time(filtered_turns_df)
    turns_breakdown(filtered_turns_df)
    turns_without_ends_dates(filtered_turns_df)
if selected_tab == "Individual Turn Drilldown":
    selected_turn_arr, filtered_construction_scopes_df, filtered_line_items_df = drilldown_filters(turns_df, construction_scopes_df, line_items_df)
    individual_turn_timeline(selected_turn_arr)
    individual_turn_budget_breakdown(selected_turn_arr, filtered_construction_scopes_df, filtered_line_items_df, tickets_df)
    individual_turn_drilldown(filtered_line_items_df)
    invoices_by_vendor(filtered_line_items_df)
if selected_tab == "Economic Turn Costs":
    filtered_turns_df = economic_turn_costs_filters(turns_df)
    economic_turn_costs(filtered_turns_df)

