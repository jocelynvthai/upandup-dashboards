import streamlit as st
import pandas as pd
from google.oauth2 import service_account

from data import get_service_account_info, leasing_scraper_data, conversion_rates_data
from tabs.competitors_tab import competitors_filters, clearance_rates, homes_rented_stats
from tabs.conversion_rates_tab import conversion_rates

# Configure page layout
st.set_page_config(
    page_title="Leasing Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info())
leasing_df = leasing_scraper_data(credentials)
conversion_rates_df = conversion_rates_data(credentials)


# Application
st.title("Leasing Dashboard")

competitors_tab, conversion_rates_tab = st.tabs(["Competitors", 'Conversion Rates'])
with competitors_tab:
    leasing_period_df, start_date, end_date = competitors_filters(leasing_df)
    clearance_rates(leasing_period_df, start_date, end_date)
    homes_rented_stats(leasing_period_df, start_date, end_date)
with conversion_rates_tab:
    # KEVIN TO DO
    conversion_rates(conversion_rates_df)



