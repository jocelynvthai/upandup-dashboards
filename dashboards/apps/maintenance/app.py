import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info, bills_tickets_invoices_data
from tabs.latchel_spend import latchel_spend_filters, latchel_spend

# Configure page layout
st.set_page_config(
    page_title="Dashboard Name",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info())
bills_tickets_invoices_df = bills_tickets_invoices_data(credentials)

# Application
st.title("Maintenance Dashboard")
latchel_spend_tab, non_latchel_spend_tab = st.tabs(["Latchel Spend", "Non-Latchel Spend"])
with latchel_spend_tab:
    filtered_bills_tickets_invoices_df = latchel_spend_filters(bills_tickets_invoices_df)
    latchel_spend(filtered_bills_tickets_invoices_df)
# with non_latchel_spend:
    # non_latchel_spend(bills_tickets_invoices_df)