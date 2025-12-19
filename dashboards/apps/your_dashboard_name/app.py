import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info, get_data

# Configure page layout
st.set_page_config(
    page_title="Dashboard Name",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info())
data = get_data(credentials)

# Application
col1, col2 = st.columns([1, 0.04])
with col1:
    st.title("_ Dashboard")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Add spacing to align with title
    st.button("↻", on_click=st.cache_data.clear, help="Refresh All Data")
