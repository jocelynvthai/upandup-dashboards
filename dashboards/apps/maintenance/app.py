import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info
from tabs.seasonality_tab import seasonality_filters, seasonality_by_category
from tabs.buildium_spend_tab import buildium_spend_filters, buildium_spend_bar_chart, buildium_spend_over_time, buildium_spend_seasonality, buildium_spend_line_items
from tabs.latchel_spend_tab import latchel_spend_filters, latchel_spend, latchel_spend_bills
from tabs.non_latchel_spend_tab import non_latchel_spend_filters, non_latchel_spend, non_latchel_spend_bills

# Configure page layout
st.set_page_config(
    page_title="Maintenance Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info())

# Application
st.title("Maintenance Dashboard")
buildium_spend_tab, latchel_tab, non_latchel_tab = st.tabs(["Buildium Spend", "Latchel Spend (Budget vs Actual)", "Non-Latchel Spend"])
with buildium_spend_tab:
    selected_tab = st.pills('TABS', options=["Overall", "Seasonality by Category"], 
                        default='Overall',
                        selection_mode = "single", 
                        label_visibility="collapsed"
    )
    if selected_tab == 'Overall':
        filtered_all_management_expenses_df, filtered_owned_homes_df, filtered_budget_by_month_df, filtered_imputed_daily_budget_df = buildium_spend_filters(credentials)
        buildium_spend_bar_chart(filtered_all_management_expenses_df, filtered_owned_homes_df, filtered_imputed_daily_budget_df)
        buildium_spend_over_time(filtered_all_management_expenses_df, filtered_owned_homes_df)
        # buildium_spend_seasonality(filtered_all_management_expenses_df, filtered_owned_homes_df, filtered_budget_by_month_df)
        buildium_spend_line_items(filtered_all_management_expenses_df)
    if selected_tab == 'Seasonality by Category':
        filtered_all_management_expenses_df, filtered_owned_homes_df = seasonality_filters(credentials)
        seasonality_by_category(filtered_all_management_expenses_df, filtered_owned_homes_df)
with latchel_tab:
    filtered_bills_tickets_invoices_df = latchel_spend_filters(credentials)
    latchel_spend(filtered_bills_tickets_invoices_df)
    latchel_spend_bills(filtered_bills_tickets_invoices_df)
with non_latchel_tab:
    filtered_bills_tickets_invoices_df = non_latchel_spend_filters(credentials)
    non_latchel_spend(filtered_bills_tickets_invoices_df)
    non_latchel_spend_bills(filtered_bills_tickets_invoices_df)