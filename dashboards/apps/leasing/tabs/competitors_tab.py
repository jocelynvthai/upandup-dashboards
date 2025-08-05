import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import numpy as np



def competitors_filters(leasing_df):
    col_date_range, col_market, col_competitor = st.columns(3)
    filtered_leasing_period_df = leasing_df.copy()

    with col_date_range:
        date_range = st.date_input("Pick a period range", 
                                value=(datetime.now() - timedelta(days=1),  datetime.now()), 
                                format='MM/DD/YYYY',
                                key='competitors_date_range')
        if len(date_range) != 2:
            st.stop()
        else: 
            start_date, end_date = date_range[0], date_range[1]
            filtered_leasing_period_df = filtered_leasing_period_df[(filtered_leasing_period_df['first_pull_date'] <= end_date) & 
                                                        (filtered_leasing_period_df['last_pull_date'] >= (start_date - timedelta(days=1)))]
    with col_market:
        selected_market = st.selectbox("Select a market", 
                                options=['All'] + list(leasing_df['market_name'].unique()), 
                                index=0,
                                key='competitors_market')
        color_scale = alt.Scale(scheme='tealblues')  
        if selected_market != 'All':
            filtered_leasing_period_df = filtered_leasing_period_df[filtered_leasing_period_df['market_name'] == selected_market]
            color_scale = alt.Scale(range=['#15b8a6']) 
    
    with col_competitor:
        selected_competitor = st.selectbox("Select a competitor", 
                                options=['All'] + list(leasing_df['source'].unique()), 
                                index=0,
                                key='competitors_competitor')
        if selected_competitor != 'All':
            filtered_leasing_period_df = filtered_leasing_period_df[filtered_leasing_period_df['source'] == selected_competitor]

    
    
    return filtered_leasing_period_df, start_date, end_date, color_scale


def metrics():
    st.subheader("Metrics")
    st.markdown('''
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px;">
        <strong>actual_vacated</strong>: when status changes from 'Notice Unrented' to 'Vacant Unrented Not Ready'<br>
        <strong>actual_available</strong>: when status changes from 'Vacant Unrented Not Ready' to 'Vacant Unrented Ready'<br>
        <strong>latest_lease_signed</strong>: day after the last pull date, if there is 1+ days since home has appeared in pull<br>
        <strong>total_leases_signed</strong> = 1 (if latest_lease_signed exists) + # leases signed that didn't go through (number of gaps ranging 4-14 days)<br>
        <strong>actual_turn_time</strong> = days between actual_vacated and actual_available<br>
        <strong>home_rented_days_on_market</strong> = days between lease_signed and actual_available (estimated available_on if actual_available does not exist)
        </div>
    ''', unsafe_allow_html=True)



def clearance_rates(filtered_leasing_period_df, start_date, end_date):
    st.subheader("Clearance Rates")
    prelease_df = filtered_leasing_period_df[filtered_leasing_period_df['last_status'].isin(['Notice Unrented', 'Vacant Unrented Not Ready'])]
    rent_ready_df = filtered_leasing_period_df[filtered_leasing_period_df['last_status'].isin(['Vacant Unrented Ready'])]

    clearance_rates = [
        len(prelease_df[(prelease_df['last_lease_signed']>=start_date) & (prelease_df['last_lease_signed']<=end_date)])*100 / len(prelease_df), 
        len(rent_ready_df[(rent_ready_df['last_lease_signed']>=start_date) & (rent_ready_df['last_lease_signed']<=end_date)])*100 / len(rent_ready_df)
    ]
    col_prelease_clearance_rate, col_rent_ready_clearance_rate = st.columns(2)
    with col_prelease_clearance_rate:
        st.metric("Pre-lease Clearance Rate", f"{clearance_rates[0]:.2f}%", help="% of pre-lease homes (Notice Unrented, Vacant Unrented Not Ready) rented in period range")
    with col_rent_ready_clearance_rate:
        st.metric("Rent Ready Clearance Rate", f"{clearance_rates[1]:.2f}%", help="% of pre-lease homes (Vacant Unrented Ready) rented in period range")


def rent_changes(filtered_leasing_period_df, color_scale):
    st.subheader("Leased Homes Stats")
    homes_rented_df = filtered_leasing_period_df[filtered_leasing_period_df['last_lease_signed'].notna()]

    # Rent Change Chart
    homes_rented_df['rent_change'] = homes_rented_df['last_rent'] - homes_rented_df['first_rent']
    rent_change_chart = alt.Chart(homes_rented_df).mark_point().encode(
        x=alt.X('rent_change:Q', title='Rent Δ ($)'),
        y=alt.Y('market_name:N', title=None),
        color=alt.Color('market_name:N', scale=color_scale, title='Market'),
        tooltip=[
            alt.Tooltip('address', title='Address'),
            alt.Tooltip('market_name', title='Market'),
            alt.Tooltip('first_rent', title='Initial Rent ($)'),
            alt.Tooltip('last_rent', title='Current Rent ($)'),
            alt.Tooltip('rent_change', title='Rent Δ ($)'),
            alt.Tooltip('home_rented_days_on_market', title='Days on Market'), 
            alt.Tooltip('last_lease_signed', title='Lease Signed')
        ]
    ).properties(
        title='Rent Δ'
    )
    zero_line = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(
        color='gray'
    ).encode(x='x:Q')
    st.altair_chart((rent_change_chart + zero_line), use_container_width=True)

    # Days on Market Chart
    dom_chart = alt.Chart(homes_rented_df).mark_point().encode(
        x=alt.X('home_rented_days_on_market:Q', title='# Days'),
        y=alt.Y('market_name:N', title=None),
        color=alt.Color('market_name:N', scale=color_scale, title='Market', legend=None),
        tooltip=[
            alt.Tooltip('address', title='Address'),
            alt.Tooltip('market_name', title='Market'),
            alt.Tooltip('home_rented_days_on_market', title='Days on Market'), 
            alt.Tooltip('last_lease_signed', title='Lease Signed')
        ]
    ).properties(
        title='Days on Market'
    )
    st.altair_chart(dom_chart + zero_line, use_container_width=True)

    # Leased Homes Summary Statistics
    st.markdown("<h6><b>Leased Homes Summary Statistics</b></h6>", unsafe_allow_html=True)
    stats_df = homes_rented_df.groupby('market_name').agg({
        'rent_change': [
            ('Count', 'count'),
            ('Average', 'mean'),
            ('Median', 'median')
        ],
        'home_rented_days_on_market': [
            ('Average', 'mean'),
            ('Median', 'median')
        ]
    }).round(2)
    stats_df.columns = pd.MultiIndex.from_tuples([
        ('', '# Homes Leased'),
        ('Rent Δ ($)', 'Average'),
        ('Rent Δ ($)', 'Median'),
        ('Days on Market', 'Average'),
        ('Days on Market', 'Median')
    ])
    st.dataframe(stats_df, use_container_width=True)


def turn_times(filtered_leasing_period_df, color_scale):
    st.subheader("Turn Times")
    turn_times_df = filtered_leasing_period_df[filtered_leasing_period_df['actual_turn_time'].notna()]

    # Chart
    turn_times_chart = alt.Chart(turn_times_df).mark_point().encode(
        x=alt.X('actual_turn_time:Q', title='Turn Time (days)', axis=alt.Axis(format='d')),
        y=alt.Y('market_name:N', title=None),
        color=alt.Color('market_name:N', scale=color_scale, title='Market'),
        tooltip=[
            alt.Tooltip('address', title='Address'),
            alt.Tooltip('market_name', title='Market'),
            alt.Tooltip('actual_vacated', title='Vacated On'),
            alt.Tooltip('actual_available', title='Available On'),
            alt.Tooltip('actual_turn_time', title='Turn Time (days)')
        ]
    )
    st.altair_chart(turn_times_chart,  use_container_width=True)

    # Summary Statistics
    st.markdown("<h6><b>Turn Times Summary Statistics</b></h6>", unsafe_allow_html=True)
    stats_df = turn_times_df.groupby('market_name').agg(
        **{
            '# Homes Turned': ('actual_turn_time', 'count'),
            'Average Turn Time (days)': ('actual_turn_time', 'mean'),
            'Median Turn Time (days)': ('actual_turn_time', 'median')
        }
    ).round(2)
    st.dataframe(stats_df, use_container_width=True)





    






















