import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import numpy as np

def conversion_rates_filters(conversion_rates_df):
    col_date_range, col_time_granularity, col_market, col_fund = st.columns(4)
    conversion_rates_df = conversion_rates_df.copy()

    with col_date_range:
        date_range = st.date_input(
            "Pick a period range",
            value=(datetime.now() - timedelta(days=1),  datetime.now()),
            format='MM/DD/YYYY',
            key='conversion_rates_date_range'
        )
        if len(date_range) != 2:
            st.stop()
        else:
            start_date, end_date = date_range[0], date_range[1]
            conversion_rates_df = conversion_rates_df[
                (conversion_rates_df['date'] <= end_date) &
                (conversion_rates_df['date'] >= start_date)
            ]

    with col_time_granularity:
        time_granularity = st.selectbox(
            "Select a time granularity",
            options=list(conversion_rates_df['time_granularity'].unique()), index=0)
        if time_granularity is None:
            st.stop()

    with col_market:
        selected_market = st.selectbox(
            "Select a market",
            options=['All'] + list(conversion_rates_df['market'].unique()), index=0)
        if selected_market != 'All':
            conversion_rates_df = conversion_rates_df[
                conversion_rates_df['market'] == selected_market
            ]

    with col_fund:
        selected_fund = st.selectbox(
            "Select a fund",
            options=['All'] + list(conversion_rates_df['fund'].unique()), index=0)
        if selected_fund != 'All':
            conversion_rates_df = conversion_rates_df[
                conversion_rates_df['fund'] == selected_fund
            ]

    return conversion_rates_df

def leasing_funnel_defs():
    st.subheader("Leasing Funnel Stages")
    st.markdown('''
        All metrics are based on cohorts of when the user entered Hudson.
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px;">
        <strong>Lead</strong>: User created in Hudson<br>
        <strong>Paid Applicant</strong>: User created an application & paid application fee<br>
        <strong>Approved Applicant</strong>: Up&Up reviewed, underwrote, and approved application<br>
        <strong>Initial Payment</strong>: User signed lease & made $500 initial payment<br>
        <strong>Deal</strong>: Up&Up countersigned lease<br>
        </div>
    ''', unsafe_allow_html=True)

def conversion_rates_summary(conversion_rates_df):
    st.subheader("Conversion Rates Summary")
    # KEVIN TO DO

def conversion_rates(conversion_rates_df):
    st.subheader("Conversion Rates")
    st.write(conversion_rates_df)