import json
import os
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

def get_service_account_info(local=None):
    if local is None:
        local = os.getenv('ENV') == 'local'

    if local:
        service_account_info = st.secrets["gcp_service_account"]
    else: 
        with open('/gcp_service_account/GCLOUD_SERVICE_ACCOUNT', 'r') as f:
            service_account_info = json.load(f)
    return service_account_info
