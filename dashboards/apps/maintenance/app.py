import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info, all_management_expenses_data, construction_bills_source_data, bills_tickets_invoices_data
# from tabs.latchel_spend import latchel_spend_filters, latchel_spend
from tabs.buildium_spend import buildium_spend_data_clean, buildium_spend_filters, buildium_spend_over_time, buildium_spend_line_items

# Configure page layout
st.set_page_config(
    page_title="Dashboard Name",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info())
all_management_expenses_df = all_management_expenses_data(credentials)
construction_bills_source_df = construction_bills_source_data(credentials)
bills_tickets_invoices_df = bills_tickets_invoices_data(credentials)

# Application
st.title("Maintenance Dashboard")
buildium_spend_tab, budget_vs_actual_tab = st.tabs(["Buildium Spend", "Budget vs Actual"])
with buildium_spend_tab:
    cleaned_all_management_expenses_df = buildium_spend_data_clean(all_management_expenses_df)
    filtered_all_management_expenses_df = buildium_spend_filters(cleaned_all_management_expenses_df)
    buildium_spend_over_time(filtered_all_management_expenses_df)
    buildium_spend_line_items(filtered_all_management_expenses_df)
# with budget_vs_actual_tab:
#     budget_vs_actual(bills_tickets_invoices_df)