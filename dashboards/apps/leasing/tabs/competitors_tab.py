import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import numpy as np


def competitors_filters(leasing_df):
    col_date_range, col_market, col_competitor = st.columns(3)

    leasing_period_df = leasing_df.copy()
    with col_date_range:
        date_range = st.date_input("Pick a period range", 
                                value=(datetime.now() - timedelta(days=1),  datetime.now()), 
                                format='MM/DD/YYYY')
        if len(date_range) != 2:
            st.stop()
        else: 
            start_date, end_date = date_range[0], date_range[1]
            leasing_period_df = leasing_period_df[(leasing_period_df['first_pull_date'] <= end_date) & 
                                                        (leasing_period_df['last_pull_date'] >= (start_date - timedelta(days=1)))]
    with col_market:
        selected_market = st.selectbox("Select a market", 
                                options=['All'] + list(leasing_df['market_name'].unique()), index=0)
        if selected_market != 'All':
            leasing_period_df = leasing_period_df[leasing_period_df['market_name'] == selected_market]
    
    with col_competitor:
        selected_competitor = st.selectbox("Select a competitor", 
                                options=['All'] + list(leasing_df['source'].unique()), index=0)
        if selected_competitor != 'All':
            leasing_period_df = leasing_period_df[leasing_period_df['source'] == selected_competitor]
    
    return leasing_period_df, start_date, end_date



def clearance_rates(leasing_period_df, start_date, end_date):
    st.subheader("Clearance Rates")

    prelease_df = leasing_period_df[leasing_period_df['last_status'].isin(['Notice Unrented', 'Vacant Unrented Not Ready'])]
    rent_ready_df = leasing_period_df[leasing_period_df['last_status'].isin(['Vacant Unrented Ready'])]

    clearance_rates = [
        len(prelease_df[(prelease_df['last_lease_signed']>=start_date) & (prelease_df['last_lease_signed']<=end_date)])*100 / len(prelease_df), 
        len(rent_ready_df[(rent_ready_df['last_lease_signed']>=start_date) & (rent_ready_df['last_lease_signed']<=end_date)])*100 / len(rent_ready_df)
    ]
    col_prelease_clearance_rate, col_rent_ready_clearance_rate = st.columns(2)
    with col_prelease_clearance_rate:
        st.metric("Pre-lease Clearance Rate", f"{clearance_rates[0]:.2f}%", help="% of pre-lease homes (Notice Unrented, Vacant Unrented Not Ready) rented in period range")
    with col_rent_ready_clearance_rate:
        st.metric("Rent Ready Clearance Rate", f"{clearance_rates[1]:.2f}%", help="% of pre-lease homes (Vacant Unrented Ready) rented in period range")


def homes_rented_stats(leasing_period_df, start_date, end_date):
    st.subheader("Homes Rented Stats")

    homes_rented_df = leasing_period_df[leasing_period_df['last_lease_signed'].notna()]

    homes_rented_df['rent_change'] = homes_rented_df['last_rent'] - homes_rented_df['first_rent']
    # Rent Change Chart
    if len(homes_rented_df['market_name'].unique()) == 1:
        color_scale = alt.Scale(range=['#15b8a6']) 
    else:
        color_scale = alt.Scale(scheme='tealblues')  
    rent_change_chart = alt.Chart(homes_rented_df).mark_point().encode(
        x=alt.X('rent_change:Q', title='Rent Change ($)'),
        y=alt.Y('market_name:N', title=None),
        color=alt.Color('market_name:N', scale=color_scale, title='Market'),
        tooltip=['market_name', 'first_rent', 'last_rent', 'rent_change', 'address']
    ).properties(
        title='Rent Changes by Market'
    )
    zero_line = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(
        color='gray',
        strokeDash=[4, 4]
    ).encode(x='x:Q')
    st.altair_chart((rent_change_chart + zero_line), use_container_width=True)

    # Rent Change Summary Statistics
    st.markdown("<h6><b>Rent Change Summary Statistics</b></h6>", unsafe_allow_html=True)
    stats_df = homes_rented_df.groupby('market_name')['rent_change'].agg([
        ('Mean', 'mean'),
        ('Median', 'median'),
        ('Min', 'min'),
        ('Max', 'max'),
        ('Count', 'count'),
        ('Std Dev', 'std')
    ]).round(2)
    st.dataframe(stats_df, use_container_width=True)

    # Days on Market strip plot
    dom_strip = alt.Chart(homes_rented_df).mark_point().encode(
        x=alt.X('days_on_market:Q', title='# Days'),
        y=alt.Y('market_name:N', title=None),
        color=alt.Color('market_name:N', scale=color_scale, title='Market', legend=None),
        tooltip=['market_name', 'days_on_market', 'address']
    ).properties(
        title='Days on Market'
    )

    st.altair_chart(dom_strip, use_container_width=True)

    
    # # Rent scatter plot
    # if len(homes_rented_df['market_name'].unique()) == 1:
    #     color_scale = alt.Scale(range=['#15b8a6']) 
    # else:
    #     color_scale = alt.Scale(scheme='tealblues')  
    # scatter_chart = alt.Chart(homes_rented_df).mark_point().encode(
    #     x=alt.X('first_rent:Q', title='first Rent'),
    #     y=alt.Y('last_rent:Q', title='last Rent'),
    #     color=alt.Color('market_name:N', scale=color_scale, title='Market'),
    #     tooltip=['market_name', 'first_rent', 'last_rent']
    # )
    # diagonal_line = alt.Chart(pd.DataFrame({
    #     'x': [0, homes_rented_df['first_rent'].max()],
    #     'y': [0, homes_rented_df['first_rent'].max()]
    # })).mark_line(color='#00000010').encode(x='x:Q', y='y:Q')
    # st.altair_chart((diagonal_line + scatter_chart).properties(title='Market Cycle Rent Comparison'), use_container_width=True)

    # # Days on Market strip plot
    # dom_strip = alt.Chart(homes_rented_df).mark_point().encode(
    #     x=alt.X('days_on_market:Q', title='# Days'),
    #     y=alt.Y('market_name:N', title=None),
    #     color=alt.Color('market_name:N', scale=color_scale, title='Market', legend=None),
    #     tooltip=['market_name', 'days_on_market', 'address']
    # ).properties(
    #     title='Days on Market'
    # )

    # st.altair_chart(dom_strip, use_container_width=True)
    






















