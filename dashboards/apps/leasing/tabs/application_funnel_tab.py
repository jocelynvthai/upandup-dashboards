import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

def application_funnel_filters(application_funnel_df):
    col_date_range, col_time_granularity, col_fund, col_market = st.columns(4)
    filtered_application_funnel_df = application_funnel_df.copy()

    with col_date_range:
        date_range = st.date_input("Pick a period range",
                                   value=(datetime.now() - timedelta(days=1),  datetime.now()),
                                   format='MM/DD/YYYY',
                                   key='application_funnel_date_range')
        if len(date_range) != 2:
            st.stop()
        else:
            start_date, end_date = date_range[0], date_range[1]
            filtered_application_funnel_df = filtered_application_funnel_df[(filtered_application_funnel_df['date'] <= end_date) &
                                                                        (filtered_application_funnel_df['date'] >= start_date)]

    with col_time_granularity:
        available_granularities = filtered_application_funnel_df['time_granularity'].unique()
        selected_time_granularity = st.selectbox("Select a time granularity",
                                      options=[g for g in ['day', 'week', 'month', 'quarter', 'year'] if g in available_granularities], 
                                      index=0, 
                                      key='application_funnel_time_granularity')
        filtered_application_funnel_df = filtered_application_funnel_df[filtered_application_funnel_df['time_granularity'] == selected_time_granularity]

    with col_fund:
        selected_fund = st.selectbox("Select a fund", 
                                     options=['All'] + list(filtered_application_funnel_df['fund'].unique()), 
                                     index=0, 
                                     key='application_funnel_fund')
        if selected_fund != 'All':
            filtered_application_funnel_df = filtered_application_funnel_df[filtered_application_funnel_df['fund'] == selected_fund]

    with col_market:
        selected_market = st.selectbox("Select a market",
                                       options=['All'] + list(filtered_application_funnel_df['market'].unique()), 
                                       index=0,
                                       key='application_funnel_market')
        if selected_market != 'All':
            filtered_application_funnel_df = filtered_application_funnel_df[filtered_application_funnel_df['market'] == selected_market]

    return filtered_application_funnel_df, selected_time_granularity


def application_funnel_chart(filtered_application_funnel_df):
    st.subheader("Application Funnel")