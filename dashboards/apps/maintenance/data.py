import json
import os
import streamlit as st
import numpy as np
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

# Cache TTL for 1 hour
CACHE_TTL = 3600

def get_service_account_info():
    if os.getenv('ENV') == 'local':
        service_account_info = st.secrets["gcp_service_account"]
    else: 
        with open('/gcp_service_account/GCLOUD_SERVICE_ACCOUNT', 'r') as f:
            service_account_info = json.load(f)
    return service_account_info


@st.cache_data(ttl=CACHE_TTL)
def bills_tickets_invoices_data(_credentials):
    query = """
        SELECT *
        FROM `homevest-data.dbt_prod_tin.bills_tickets_invoices`
    """
    data = pd.read_gbq(query, credentials=_credentials)
    data['ticket_date'] = np.where(data['ticket_actual_start_date'].notna(), 
                              data['ticket_actual_start_date'], 
                              data['ticket_planned_start_date'])
    return data
