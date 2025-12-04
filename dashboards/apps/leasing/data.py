import json
import os
import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from dateutil.relativedelta import relativedelta
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


# summary tab data
@st.cache_data(ttl=CACHE_TTL)
def rental_applications_data(_credentials):
    query = """
        SELECT * 
        FROM `homevest-data.dbt_prod.fct_rental_applications`
    """
    return pd.read_gbq(query, credentials=_credentials)


# inquiries tab data
@st.cache_data(ttl=CACHE_TTL)
def raw_inquiries_data(_credentials):
    query = """
        WITH listed_dates AS (
            SELECT
                mls_listing_id,
                date_synced AS date
            FROM `homevest-data.snapshots.internally_listed_mls_listings`
        )
        SELECT
            ld.date,
            ld.mls_listing_id,
            rsi.rental_site_listing_id
        FROM listed_dates AS ld
        LEFT JOIN `homevest-data.dbt_prod.fct_rental_site_inquiries` AS rsi
            ON ld.mls_listing_id = rsi.mls_listing_id
            AND ld.date = DATE(rsi.inquiry_created_at)

    """
    return pd.read_gbq(query, credentials=_credentials)
@st.cache_data(ttl=CACHE_TTL)
def inquiries_data(_credentials):
    query = """
        SELECT * FROM `homevest-data.dbt_prod.agg_rental_site_inquiries`
        ORDER BY
            CASE time_granularity
                WHEN 'week' THEN 1
                WHEN 'month' THEN 2
                WHEN 'quarter' THEN 3
                WHEN 'year' THEN 4
            END,
            address,
            date
    """
    return pd.read_gbq(query, credentials=_credentials)


# tours tab data
@st.cache_data(ttl=CACHE_TTL)
def tours_data(_credentials):
    query = """
        SELECT * FROM `homevest-data.dbt_prod.agg_tours`
        WHERE fund IS NOT NULL
        ORDER BY
            CASE time_granularity
                WHEN 'week' THEN 1
                WHEN 'month' THEN 2
                WHEN 'quarter' THEN 3
                WHEN 'year' THEN 4
            END,
            address,
            date
    """
    return pd.read_gbq(query, credentials=_credentials)


# leasing funnel tab data
@st.cache_data(ttl=CACHE_TTL)
def leasing_funnel_data(_credentials):
    query = """
        SELECT * FROM `homevest-data.dbt_prod.agg_cohortized_leasing_funnel`
        ORDER BY
            CASE time_granularity
                WHEN 'day' THEN 1
                WHEN 'week' THEN 2
                WHEN 'month' THEN 3
                WHEN 'quarter' THEN 4
                WHEN 'year' THEN 5
            END,
            date,
            fund,
            market
    """
    return pd.read_gbq(query, credentials=_credentials)


# occupancy tab data
@st.cache_data(ttl=CACHE_TTL)
def economic_occupancy_data(_credentials):
    query = """
        SELECT *
        FROM `homevest-data.dbt_prod_tin.economic_occupancy_budget_vs_projected`
    """
    return pd.read_gbq(query, credentials=_credentials)
@st.cache_data(ttl=CACHE_TTL)
def rental_data(_credentials):
    query = """
        SELECT 
            r.*, 
            ad.address, 
            ad.fund, 
            ad.market, 
        FROM `homevest-data.dbt_prod.stg_actual_rentals` AS r
        LEFT JOIN `homevest-data.dbt_prod.dim_acquisition_details` AS ad
            ON r.property_id = ad.property_id
    """
    return pd.read_gbq(query, credentials=_credentials)
@st.cache_data(ttl=CACHE_TTL)
def renewal_data(_credentials):
    week_start = datetime.now().date() - relativedelta(days=datetime.now().weekday())
    query = f"""
        SELECT 
            r1.id, 
            ad.address, 
            ad.fund, 
            ad.market, 
            r1._date AS week_start_date, 
            r1.starts_at AS current_lease_start, 
            r1.ends_at AS current_lease_end, 
            r2._date AS current_lease_ended_first_day, 
            r2.starts_at AS new_lease_start, 
            r2.ends_at AS new_lease_end, 
        CASE 
            WHEN (r1.move_out_date IS NULL and r2.ends_at > r1.ends_at) 
                THEN 'yes'
            WHEN (r1.move_out_date IS NOT NULL)
                THEN 'no'
            ELSE 'pending'
        END AS renewed
        FROM `homevest-data.dbt_prod.stg_daily_rentals` as r1
        LEFT JOIN `homevest-data.dbt_prod.stg_daily_rentals` AS r2
            ON r1.id = r2.id
            AND DATE_ADD(r1.ends_at, INTERVAL 1 DAY) = r2._date
        LEFT JOIN `homevest-data.dbt_prod.dim_acquisition_details` AS ad
            ON r1.property_id = ad.property_id
        WHERE r1._date = '{week_start}'
            AND r1.ends_at >= '{week_start}'
    """
    return pd.read_gbq(query, credentials=_credentials)


# vacancy curve tab data
@st.cache_data(ttl=CACHE_TTL)
def vacancy_curve_data(_credentials):
    query = """
        SELECT * FROM `homevest-data.dbt_prod_tin.vacancy_curve`
    """
    return pd.read_gbq(query, credentials=_credentials)
@st.cache_data(ttl=CACHE_TTL)
def distinct_vacancies_data(_credentials):
    query = """
        SELECT DISTINCT
            property_id,
            address,
            vacancy_start_date,
            vacancy_end_date,
            vacancy_rank_asc
        FROM `homevest-data.dbt_prod_tin.vacancy_curve`
        ORDER By vacancy_start_date DESC, address
    """
    return pd.read_gbq(query, credentials=_credentials)


# competitors tab data
@st.cache_data(ttl=CACHE_TTL)
def leasing_scraper_data(_credentials):
    query = """
        SELECT *
        FROM `homevest-data.dbt_prod_tin.leasing_scraper_data`
    """
    return pd.read_gbq(query, credentials=_credentials)
@st.cache_data(ttl=CACHE_TTL)
def leasing_scraper_individual_rent_changes_data(_credentials):
    query = """
        SELECT *
        FROM `homevest-data.dbt_prod_tin.leasing_scraper_individual_rent_changes`
    """
    return pd.read_gbq(query, credentials=_credentials)
@st.cache_data
def leasing_scraper_weekly_rent_changes_data(_credentials):
    query = """
        SELECT *
        FROM `homevest-data.dbt_prod_tin.leasing_scraper_weekly_rent_changes`
    """
    return pd.read_gbq(query, credentials=_credentials)
@st.cache_data(ttl=CACHE_TTL)
def rent_curve_data(_credentials):
    query = """
        SELECT *
        FROM `homevest-data.dbt_prod_tin.rent_curve`
    """
    return pd.read_gbq(query, credentials=_credentials)
