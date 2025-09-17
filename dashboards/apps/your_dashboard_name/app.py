import sys
from pathlib import Path
import streamlit as st
from google.oauth2 import service_account

# Add the dashboards directory to Python path so we can import utils.credentials
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.credentials import get_service_account_info

from data import get_data

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
st.title("Dashboard Name")
