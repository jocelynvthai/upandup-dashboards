import json
import streamlit as st
import pandas as pd
import numpy as np


def get_service_account_info(local=False):
    if local:
        service_account_info = st.secrets["gcp_service_account"]
    else: 
        with open('/gcp_service_account/GCLOUD_SERVICE_ACCOUNT', 'r') as f:
            service_account_info = json.load(f)
    return service_account_info


@st.cache_data
def turns_data(_credentials):
    query = """
        SELECT * 
        FROM `homevest-data.dbt_prod.fct_turns`
    """
    data = pd.read_gbq(query, credentials=_credentials)
    data['project_total_estimated_cost'] = data.apply(
        lambda row: (
            np.nan_to_num(row['project_estimated_cost']) + 
            np.nan_to_num(row['occupancy_inspection_estimated_cost']) + 
            (np.nan_to_num(row['project_ticket_approved_budgets']) if row['fund'] != 'Homevest Real Estate Partners IV - Limestone, L.P.' else 0)
        ),
        axis=1
    )
    return data


@st.cache_data
def line_items_data(_credentials):
    query = """
        SELECT * 
        FROM `homevest-data.dbt_prod.stg_bdm_turn_line_items`
    """
    data = pd.read_gbq(query, credentials=_credentials)
    return data

