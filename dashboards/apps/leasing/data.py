import streamlit as st
import pandas as pd


@st.cache_data
def leasing_scraper_data(_credentials):
    query = """
        SELECT *
        FROM `homevest-data.dbt_prod_tin.leasing_scraper_data`
    """
    return pd.read_gbq(query, credentials=_credentials)


@st.cache_data
def leasing_scraper_rent_changes_data(_credentials):
    query = """
        SELECT *
        FROM `homevest-data.dbt_prod_tin.leasing_scraper_rent_changes`
    """
    return pd.read_gbq(query, credentials=_credentials)


@st.cache_data
def rental_applications_data(_credentials):
    query = """
        SELECT * 
        FROM `homevest-data.dbt_prod.fct_rental_applications`
    """
    return pd.read_gbq(query, credentials=_credentials)


@st.cache_data
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


@st.cache_data
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


@st.cache_data
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


@st.cache_data
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

@st.cache_data
def vacancy_curve_data(_credentials):
    query = """
        SELECT * FROM `homevest-data.dbt_prod_tin.vacancy_curve`
    """
    return pd.read_gbq(query, credentials=_credentials)


@st.cache_data
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


@st.cache_data
def economic_occupancy_data(_credentials):
    query = """
        SELECT *
        FROM `homevest-data.dbt_prod_tin.economic_occupancy_budget_vs_projected`
    """
    return pd.read_gbq(query, credentials=_credentials)


@st.cache_data
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





