import json
import os
import streamlit as st
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
def get_bad_debt_inputs_data(_credentials):
    bad_debt_inputs_query = """
        SELECT * 
        FROM `homevest-data.dbt_prod_tin.bad_debt_inputs` 
        WHERE month >= DATE_SUB(LAST_DAY(CURRENT_DATE(), MONTH), INTERVAL 11 MONTH) 
        AND month <= LAST_DAY(CURRENT_DATE(), MONTH)
    """
    bad_debt_inputs = pd.read_gbq(bad_debt_inputs_query, credentials=_credentials)
    # Convert month to first of the month for charting purposes
    bad_debt_inputs['month'] = pd.to_datetime(bad_debt_inputs['month']).dt.to_period('M').dt.to_timestamp()
    bad_debt_inputs['display_month'] = bad_debt_inputs['month'].dt.strftime('%B %Y')
    return bad_debt_inputs


@st.cache_data(ttl=CACHE_TTL)
def get_collections_curve_data(_credentials):
    collections_curve_query = """
        SELECT * 
        FROM `homevest-data.dbt_prod_tin.rent_collections_curve`
    """
    return pd.read_gbq(collections_curve_query, credentials=_credentials)


@st.cache_data(ttl=CACHE_TTL)
def get_evictions_data(_credentials):
    evictions_query = """
        WITH 
        evictions AS (
            SELECT 
                e.*,
                ad.address,
                ad.address_line_2,
                ad.fund,
                canceled_admin.full_name AS canceled_by_admin_name,
                completed_admin.full_name AS completed_by_admin_name,
                file_sent_to_attorney_admin.full_name AS file_sent_to_attorney_by_admin_name,
                filed_admin.full_name AS filed_by_admin_name
            FROM `homevest-data.dbt_prod.fct_evictions` AS e
            LEFT JOIN `homevest-data.dbt_prod.fct_rentals` AS r
                ON e.rental_id = r.id
            LEFT JOIN `homevest-data.dbt_prod.dim_acquisition_details` AS ad
                ON r.property_id = ad.property_id
            LEFT JOIN `homevest-data.dbt_prod.dim_admins` AS canceled_admin
                ON e.canceled_by_admin_id = canceled_admin.id
            LEFT JOIN `homevest-data.dbt_prod.dim_admins` AS completed_admin
                ON e.completed_by_admin_id = completed_admin.id
            LEFT JOIN `homevest-data.dbt_prod.dim_admins` AS file_sent_to_attorney_admin
                ON e.file_sent_to_attorney_by_admin_id = file_sent_to_attorney_admin.id
            LEFT JOIN `homevest-data.dbt_prod.dim_admins` AS filed_admin
                ON e.filed_by_admin_id = filed_admin.id
        ),

        notes_joined AS (
            SELECT 
                e.id AS eviction_id,
                FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', n.created_at) || ' (' || a.full_name || '): ' || n.note AS note_line, 
                n.created_at
            FROM `homevest-data.dbt_prod.fct_evictions` AS e
            JOIN `homevest-data.dbt_prod.dim_notes` AS n
                ON n.resource_id = e.id OR n.resource_id = e.rental_id
            LEFT JOIN `homevest-data.dbt_prod.dim_admins` AS a
                ON n.created_by_admin_id = a.id
        ),

        aggregated_notes AS (
            SELECT 
                eviction_id,
                STRING_AGG(note_line, '\\n\\n' ORDER BY created_at DESC) AS notes
            FROM notes_joined
            GROUP BY eviction_id
        )

        SELECT 
            ev.*,
            an.notes
        FROM evictions ev
        LEFT JOIN aggregated_notes an
            ON ev.id = an.eviction_id
        WHERE address IS NOT NULL
    """
    return pd.read_gbq(evictions_query, credentials=_credentials)


@st.cache_data(ttl=CACHE_TTL)
def gpr_evictions_data(_credentials):
    gpr_evictions_query = """
        WITH months AS (
            (
                SELECT last_day
                FROM `homevest-data.dbt_prod.dim_min_max_months`
                WHERE last_day < LAST_DAY(CURRENT_DATE)
            )
            UNION ALL
            (
                SELECT CURRENT_DATE AS last_day
            )
        ), 

        noiy_breakdown_adjusted AS (
            SELECT *,
                CASE
                    WHEN date = LAST_DAY(CURRENT_DATE()) THEN CURRENT_DATE()
                    ELSE date
                END AS adjusted_date
            FROM `homevest-data.dbt_prod_tin.noiy_breakdown__property`
            WHERE gross_potential_rent_L1M > 0
        )

        SELECT 
            dpt._date AS month, 
            dpt.property_id,
            dpt.fund, 
            dpt.pg_occupancy_status, 
            CAST(noiy.gross_potential_rent_L1M AS FLOAT64) AS gpr, 
            dr.id AS rental_id,
            dr.lease_end_reason,
            dr.move_out_date,
            dr.status AS rental_status, 
            dr.eviction_status,
            dr.in_evictions
        FROM `homevest-data.dbt_prod.fct_daily_properties_table` AS dpt
        INNER JOIN months
            ON  dpt._date = months.last_day
        LEFT JOIN noiy_breakdown_adjusted AS noiy
            ON dpt.property_id = noiy.property_id
            AND dpt._date = noiy.adjusted_date
        LEFT JOIN `homevest-data.dbt_prod.stg_daily_rentals` AS dr
            ON dpt.property_id = dr.property_id
            AND dpt._date = dr._date
            AND (dr.move_out_date IS NULL or dpt._date <= dr.move_out_date)
        WHERE dpt.pg_occupancy_status IS NOT NULL
    """
    return pd.read_gbq(gpr_evictions_query, credentials=_credentials)
