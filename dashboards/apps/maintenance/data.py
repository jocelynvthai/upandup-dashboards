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
def all_management_expenses_data(_credentials):
    query = """
        SELECT ame.*, acq.market
        FROM `homevest-data.property_financials.all_management_expenses` AS ame
        LEFT JOIN `homevest-data.dbt_prod.dim_acquisition_details` AS acq
            ON ame.property_id = acq.property_id
        WHERE category IN (
			'make_ready_r_m',
			'run_rate_r_m',
			'turn_r_m',
			'disposition_r_m',
			'make_ready_capex',
			'run_rate_capex',
			'turn_capex',
			'disposition_capex',
			'common_area_maintenance'
		)
    """
    data = pd.read_gbq(query, credentials=_credentials)
    return data
    

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
