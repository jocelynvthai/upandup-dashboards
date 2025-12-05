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
            np.nan_to_num(row['buyers_inspection_estimated_cost'])
        ),
        axis=1
    )
    return data


@st.cache_data(ttl=CACHE_TTL)
def construction_scopes_data(_credentials):
    query = """
        SELECT
            project_id,
            most_recent_rental_id,
            type,
            project_status,
            project_estimated_cost
        FROM `homevest-data.dbt_prod.dim_construction_scopes`
    """
    return pd.read_gbq(query, credentials=_credentials)


@st.cache_data(ttl=CACHE_TTL)
def tickets_data(_credentials):
    query = """
        SELECT 
            t.*,
            t.max_cost AS approved_budgets,
            l.slug, 
            v.name AS vendor_name
        FROM `homevest-data.dbt_prod.stg_tickets` AS t
        LEFT JOIN `homevest-data.dbt_prod.stg_tickets_latchel_data` AS l
            ON t.external_id = CAST(l.job_id AS STRING)
        LEFT JOIN `homevest-data.dbt_prod.stg_ticket_vendor_assignments` AS tva
            ON t.id = tva.ticket_id
        LEFT JOIN `homevest-data.dbt_prod.dim_vendors` AS v
            ON tva.vendor_id = v.id
    """
    return pd.read_gbq(query, credentials=_credentials)


@st.cache_data(ttl=CACHE_TTL)
def line_items_data(_credentials):
    query = """
        SELECT * 
        FROM `homevest-data.dbt_prod.stg_bdm_turn_line_items`
    """
    return pd.read_gbq(query, credentials=_credentials)
