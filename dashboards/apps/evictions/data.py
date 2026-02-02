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
def evictions_data(_credentials):
    query = """
        WITH latest_balance AS (
            SELECT
                rental_id,
                aggregate_balance_after,
                aggregate_successful_balance_after,
                ROW_NUMBER() OVER (PARTITION BY rental_id ORDER BY date DESC, available_on DESC) as rn
            FROM `homevest-data.dbt_prod.fct_current_balances`
        )
        SELECT
            e.id,
            e.rental_id,
            e.created_at,
            e.status,
            e.cancelation_reason,
            e.filed_at,
            e.court_date,
            e.completed_at,
            e.canceled_at,
            m.display_name AS market_name,
            COALESCE(f.name, 'No Fund') AS fund_name,
            FORMAT_TIMESTAMP('%Y-%m', e.created_at) AS cohort,
            a.display_line_1 AS address,
            a.city,
            a.state,
            CONCAT(u.first_name, ' ', u.last_name) AS tenant_name,
            u.email AS tenant_email,
            u.phone AS tenant_phone,
            COALESCE(lb.aggregate_balance_after, 0) AS current_balance,
            COALESCE(lb.aggregate_balance_after, 0) - COALESCE(lb.aggregate_successful_balance_after, 0) AS processing
        FROM `homevest-data.google_cloud_postgresql_public.evictions` e
        JOIN `homevest-data.google_cloud_postgresql_public.rentals` r ON r.id = e.rental_id
        JOIN `homevest-data.google_cloud_postgresql_public.properties` p ON p.id = r.property_id
        JOIN `homevest-data.google_cloud_postgresql_public.portfolio_homes` ph ON ph.real_estate_acquisition_id = p.real_estate_acquisition_id
        JOIN `homevest-data.google_cloud_postgresql_public.homes` h ON h.id = ph.home_id
        JOIN `homevest-data.google_cloud_postgresql_public.addresses` a ON a.id = h.address_id
        JOIN `homevest-data.google_cloud_postgresql_public.markets` m ON m.id = h.market_id
        LEFT JOIN `homevest-data.google_cloud_postgresql_public.llc_properties` lp ON lp.property_id = p.id AND lp.end_date IS NULL
        LEFT JOIN `homevest-data.google_cloud_postgresql_public.llcs` l ON l.id = lp.llc_id
        LEFT JOIN `homevest-data.google_cloud_postgresql_public.fund_llcs` fl ON fl.llc_id = l.id
        LEFT JOIN `homevest-data.google_cloud_postgresql_public.funds` f ON f.id = fl.fund_id
        LEFT JOIN `homevest-data.google_cloud_postgresql_public.rental_users` ru ON ru.rental_id = r.id AND ru.deactivated_at IS NULL
        LEFT JOIN `homevest-data.google_cloud_postgresql_fast_public.users` u ON u.id = ru.user_id
        LEFT JOIN latest_balance lb ON lb.rental_id = CAST(r.id AS STRING) AND lb.rn = 1
        WHERE e.created_at >= TIMESTAMP(DATE_SUB(DATE_TRUNC(CURRENT_DATE(), MONTH), INTERVAL 12 MONTH))
    """
    data = pd.read_gbq(query, credentials=_credentials)
    data = data.drop_duplicates(subset=['id'])
    # Exclude Homevest, Inc. fund
    data = data[data['fund_name'] != 'Homevest, Inc.']

    return data
