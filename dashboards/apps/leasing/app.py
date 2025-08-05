import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info, leasing_scraper_data, leasing_funnel_data
from tabs.competitors_tab import metrics, competitors_filters, clearance_rates, rent_changes, turn_times
from tabs.leasing_funnel_tab import leasing_funnel_filters, leasing_funnel_grouped, leasing_funnel_summary_metrics, leasing_funnel_chart
from tabs.application_funnel_tab import application_funnel_filters, application_funnel_chart

# Configure page layout
st.set_page_config(
    page_title="Leasing Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info(local=True))
leasing_df = leasing_scraper_data(credentials)
leasing_funnel_df = leasing_funnel_data(credentials)


# Application
st.title("Leasing Dashboard")

competitors_tab, leasing_funnel_tab, application_funnel_tab = st.tabs(["Competitors", 'Leasing Funnel', 'Application Funnel'])
with competitors_tab:
    leasing_period_df, start_date, end_date, color_scale = competitors_filters(leasing_df)
    metrics()
    clearance_rates(leasing_period_df, start_date, end_date)
    rent_changes(leasing_period_df, color_scale)
    turn_times(leasing_period_df, color_scale)
with leasing_funnel_tab:
    filtered_leasing_funnel_df, selected_time_granularity = leasing_funnel_filters(leasing_funnel_df)
    grouped_leasing_funnel_df = leasing_funnel_grouped(filtered_leasing_funnel_df)
    leasing_funnel_summary_metrics(grouped_leasing_funnel_df, selected_time_granularity)
    leasing_funnel_chart(grouped_leasing_funnel_df)
with application_funnel_tab:
    filtered_application_funnel_df, selected_time_granularity = application_funnel_filters(leasing_funnel_df)
    application_funnel_chart(filtered_application_funnel_df)
    


