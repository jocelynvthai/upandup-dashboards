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
def all_management_expenses_data(_credentials, start_date, end_date):
    query = f"""
        SELECT
            ame.property_id,
            ame.address,
            acq.market,
            ame.fund,
            ame.date,
            ame.gl_account_number,
            ame.gl_account_name,
            ame.category,
            ame.subcategory,
            ame.amount,
            ame.description,
            ame.vendor_company_name,
            ame.vendor_contact_name,
            REGEXP_EXTRACT(ame.memo, r'app\.latchel\.com/admin/invoices/([0-9]+)') AS latchel_invoice_id
        FROM `homevest-data.dbt_prod.stg_all_management_expenses__no_capex_winddowns` AS ame
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
        AND subcategory NOT LIKE '%chargeback%'
        AND date >= '{start_date}'
        AND date <= '{end_date}'
    """
    data = pd.read_gbq(query, credentials=_credentials)
    return data


@st.cache_data(ttl=CACHE_TTL)
def owned_homes_data(_credentials, start_date):
    query = f"""
        SELECT *
        FROM `homevest-data.dbt_prod.stg_owned_homes`
        WHERE date >= '{start_date}'
    """
    data = pd.read_gbq(query, credentials=_credentials)
    return data


@st.cache_data(ttl=CACHE_TTL)
def budget_by_month_data(_credentials, start_date):
    query = f"""
        SELECT 
        month AS date,
        fund, 
        CASE 
            WHEN management_category = 'run_rate_r_m' THEN 'run_rate'
            WHEN management_category = 'turn_r_m' THEN 'turn'
            WHEN management_category = 'common_area_maintenance' THEN 'common_area_maintenance'
        END AS management_category,
        SUM(amount) AS amount
        FROM `homevest-data.operating_forecasts.monthly_budget_ledger_2025_09`
        WHERE management_category IN ('run_rate_r_m', 'turn_r_m', 'common_area_maintenance')
        AND month >= '{start_date}'
        GROUP BY 1, 2, 3
    """
    data = pd.read_gbq(query, credentials=_credentials)
    return data


@st.cache_data(ttl=CACHE_TTL)
def bills_tickets_invoices_data(_credentials, start_date, end_date):
    query = f"""
        SELECT *
        FROM `homevest-data.dbt_prod_tin.bills_tickets_invoices`
        WHERE date >= '{start_date}'
        AND date <= '{end_date}'
    """
    data = pd.read_gbq(query, credentials=_credentials)
    data['ticket_date'] = np.where(data['ticket_actual_start_date'].notna(), 
                              data['ticket_actual_start_date'], 
                              data['ticket_planned_start_date'])
    return data
