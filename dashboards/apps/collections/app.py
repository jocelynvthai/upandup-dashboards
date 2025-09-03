import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info, get_bad_debt_inputs_data, get_collections_curve_data, get_evictions_data, gpr_evictions_data
from tabs.data_tab import data_filters, late_collections_over_ar, ar_over_gpr
from tabs.ontime_collections_tab import ontime_collections_curve_filters, ontime_collections_curve, ontime_collections_drilldown
from tabs.late_collections_tab import late_collections_curve_filters, late_collections_curve, late_collections_drilldown
from tabs.bad_debt_tab import bad_debt_over_time_filters, bad_debt_over_time, bad_debt_month_to_date, bad_debt_projection
from tabs.evictions_tab import evictions_filters, gpr_evictions, evictions_by_status

# Configure page layout
st.set_page_config(
    page_title="Collections Dashboard",
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
bad_debt_inputs_data = get_bad_debt_inputs_data(credentials)
collections_curve_data = get_collections_curve_data(credentials)
evictions_data = get_evictions_data(credentials)
gpr_evictions_data = gpr_evictions_data(credentials)

# Application
st.title("Collections Dashboard")
ontime_collections_tab, late_collections_tab, bad_debt_tab, evictions_tab, data_tab = st.tabs(["On-Time Collections", "Late Collections", "Bad Debt", "Evictions", "Data"])
with ontime_collections_tab:
    ontime_collections_selected_fund = ontime_collections_curve_filters(collections_curve_data)
    ontime_collections_curve(collections_curve_data, ontime_collections_selected_fund)
    ontime_collections_drilldown(bad_debt_inputs_data, ontime_collections_selected_fund)
with late_collections_tab:
    late_collections_selected_fund = late_collections_curve_filters(collections_curve_data)
    late_collections_curve(collections_curve_data, late_collections_selected_fund)
    late_collections_drilldown(bad_debt_inputs_data, late_collections_selected_fund)
with bad_debt_tab:
    filtered_bad_debt_inputs, bad_debt_selected_fund = bad_debt_over_time_filters(bad_debt_inputs_data)
    bad_debt_over_time(filtered_bad_debt_inputs)
    bad_debt_month_to_date(filtered_bad_debt_inputs)
    bad_debt_projection(filtered_bad_debt_inputs)
with evictions_tab:
    filtered_evictions_data, filtered_gpr_evictions_data, evictions_selected_fund = evictions_filters(evictions_data, gpr_evictions_data)
    gpr_evictions(filtered_gpr_evictions_data)
    evictions_by_status(filtered_evictions_data)
with data_tab:
    filtered_bad_debt_inputs, selected_month_year = data_filters(bad_debt_inputs_data)
    late_collections_over_ar(filtered_bad_debt_inputs, selected_month_year)
    ar_over_gpr(filtered_bad_debt_inputs, selected_month_year)


