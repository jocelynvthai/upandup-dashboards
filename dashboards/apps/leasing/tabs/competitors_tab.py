import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

from tabs.utils import TEAL


def competitors_filters(leasing_df):
    col_date_range, col_market, col_competitor = st.columns(3)
    filtered_leasing_period_df = leasing_df.copy()

    with col_date_range:
        date_range = st.date_input("Pick a period range", 
                                value=(datetime.now() - timedelta(days=30),  datetime.now()), 
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
                                options=['All'] + sorted(leasing_df['market_name'].unique()), 
                                index=0,
                                key='competitors_market')
        color_scale = alt.Scale(scheme='tealblues')  
        if selected_market != 'All':
            filtered_leasing_period_df = filtered_leasing_period_df[filtered_leasing_period_df['market_name'] == selected_market]
            color_scale = alt.Scale(range=[TEAL]) 
    
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

    if len(prelease_df) > 0:
        prelease_clearance_rate = len(prelease_df[(prelease_df['last_lease_signed'] >= start_date) & (prelease_df['last_lease_signed'] <= end_date)]) * 100 / len(prelease_df)
    else:
        prelease_clearance_rate = 0
    if len(rent_ready_df) > 0:
        rent_ready_clearance_rate = len(rent_ready_df[(rent_ready_df['last_lease_signed'] >= start_date) & (rent_ready_df['last_lease_signed'] <= end_date)]) * 100 / len(rent_ready_df)
    else:
        rent_ready_clearance_rate = 0

    col_prelease_clearance_rate, col_rent_ready_clearance_rate = st.columns(2)
    with col_prelease_clearance_rate:
        st.metric("Pre-lease Clearance Rate", f"{prelease_clearance_rate:.2f}%", help="% of pre-lease homes (Notice Unrented, Vacant Unrented Not Ready) rented in period range")
    with col_rent_ready_clearance_rate:
        st.metric("Rent Ready Clearance Rate", f"{rent_ready_clearance_rate:.2f}%", help="% of rent ready homes (Vacant Unrented Ready) rented in period range")



def leased_homes_stats(leasing_rent_changes_df, filtered_leasing_period_df, start_date, end_date, color_scale):
    st.subheader("Leased Homes Stats")
    homes_rented_df = filtered_leasing_period_df[(filtered_leasing_period_df['last_lease_signed'] >= start_date) & (filtered_leasing_period_df['last_lease_signed'] <= end_date)]
    homes_rented_df['rent_change_overall'] = homes_rented_df['last_rent'] - homes_rented_df['first_rent']


    selected_lease_type = st.selectbox("Select a lease type", options=['All', 'Pre-lease', 'Rent Ready'], key='rent_changes_lease_type')
    if selected_lease_type == 'All':
        homes_rented_type_df = homes_rented_df
    elif selected_lease_type == 'Pre-lease':
        homes_rented_type_df = homes_rented_df[homes_rented_df['last_status'].isin(['Notice Unrented', 'Vacant Unrented Not Ready'])]
    elif selected_lease_type == 'Rent Ready':
        homes_rented_type_df = homes_rented_df[homes_rented_df['last_status'].isin(['Vacant Unrented Ready'])]
    

    # Leased Homes by Day of Week
    homes_rented_type_df['lease_signed_day_of_week'] = pd.to_datetime(homes_rented_type_df['last_lease_signed']).dt.day_name()
    lease_signed_dow_perc = round(homes_rented_type_df['lease_signed_day_of_week'].value_counts(normalize=True) * 100, 2).reset_index()
    lease_signed_dow_perc.columns = ['Day of Week', 'Percentage']
    lease_signed_dow_perc_chart = alt.Chart(lease_signed_dow_perc).mark_bar(color=TEAL).encode(
        x=alt.X('Day of Week', sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
        y=alt.Y('Percentage', title='% of Signed Leases')
    ).properties(
        title="% of Signed Leases by Day of Week",
        width=600,
        height=400
    )
    lease_signed_dow_perc_text = lease_signed_dow_perc_chart.mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    ).encode(
        text='Percentage:Q'
    )
    st.altair_chart(lease_signed_dow_perc_chart + lease_signed_dow_perc_text, use_container_width=True)


    # Rent Change Chart
    rent_change_chart = alt.Chart(homes_rented_type_df).mark_point().encode(
        x=alt.X('rent_change_overall:Q', title='Rent Δ ($)'),
        y=alt.Y('market_name:N', title=None),
        color=alt.Color('market_name:N', scale=color_scale, title='Market'),
        tooltip=[
            alt.Tooltip('address', title='Address'),
            alt.Tooltip('market_name', title='Market'),
            alt.Tooltip('first_rent', title='Initial Rent ($)'),
            alt.Tooltip('last_rent', title='Current Rent ($)'),
            alt.Tooltip('rent_change_overall', title='Rent Δ ($)'),
            alt.Tooltip('home_rented_days_on_market', title='Days on Market'), 
            alt.Tooltip('last_lease_signed', title='Lease Signed')
        ]
    ).properties(
        title=alt.Title(
            text='Rent Δ', 
            subtitle='Leased Rent - Initial Rent'
        )
    )
    zero_line = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(
        color='gray'
    ).encode(x='x:Q')
    st.altair_chart((rent_change_chart + zero_line), use_container_width=True)



    # Individual Rent Changes Chart
    filtered_leasing_rent_changes_df = leasing_rent_changes_df.merge(
        homes_rented_type_df, on='property_id', how='inner'
    )
    filtered_leasing_rent_changes_df = filtered_leasing_rent_changes_df[
        (filtered_leasing_rent_changes_df['date_of_rent_change'] >= filtered_leasing_rent_changes_df['first_pull_date']) &
        (filtered_leasing_rent_changes_df['date_of_rent_change'] <= filtered_leasing_rent_changes_df['last_pull_date'])
    ]
    filtered_leasing_rent_changes_df['days_listed'] = (filtered_leasing_rent_changes_df['date_of_rent_change'] - filtered_leasing_rent_changes_df['first_pull_date']).dt.days
    individual_rent_changes_chart = alt.Chart(filtered_leasing_rent_changes_df).mark_point(color=TEAL).encode(
        x=alt.X('days_listed:Q', title='Days Listed'),
        y=alt.Y('rent_change:Q', title='Rent Change ($)'), 
        tooltip=[
            alt.Tooltip('address', title='Address'),
            alt.Tooltip('new_rent', title='New Rent', format='$.2f'),
            alt.Tooltip('prior_rent', title='Prior Rent', format='$.2f'),
            alt.Tooltip('rent_change', title='Rent Δ', format='$.2f'),
        ]
    ).properties(
        title=alt.Title(
            text='Individual Rent Δ', 
            subtitle='Change in rent vs # days the home has been listed'
        ),
        height=800
    )
    st.altair_chart(individual_rent_changes_chart, use_container_width=True)



    # Days on Market Chart
    dom_chart = alt.Chart(homes_rented_type_df).mark_point().encode(
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
    st.markdown("<h6><b>Summary Statistics</b></h6>", unsafe_allow_html=True)
    stats_df = homes_rented_df.groupby('market_name').agg({
        'last_status': [
            ('num_homes_leased', 'count'),
            ('num_homes_leased_prelease', lambda x: x.isin(['Notice Unrented', 'Vacant Unrented Not Ready']).sum()),
            ('num_homes_leased_rent_ready', lambda x: x.isin(['Vacant Unrented Ready']).sum())
        ],
        'rent_change_overall': [
            ('average_rent_change', 'mean'),
            ('average_rent_change_prelease', lambda x: x[homes_rented_df['last_status'].isin(['Notice Unrented', 'Vacant Unrented Not Ready'])].mean()), 
            ('average_rent_change_rent_ready', lambda x: x[homes_rented_df['last_status'].isin(['Vacant Unrented Ready'])].mean()), 
            ('median_rent_change', 'median'),
            ('median_rent_change_prelease', lambda x: x[homes_rented_df['last_status'].isin(['Notice Unrented', 'Vacant Unrented Not Ready'])].median()), 
            ('median_rent_change_rent_ready', lambda x: x[homes_rented_df['last_status'].isin(['Vacant Unrented Ready'])].median())
        ],
        'home_rented_days_on_market': [
            ('average_days_on_market', 'mean'),
            ('average_days_on_market_prelease', lambda x: x[homes_rented_df['last_status'].isin(['Notice Unrented', 'Vacant Unrented Not Ready'])].mean()), 
            ('average_days_on_market_rent_ready', lambda x: x[homes_rented_df['last_status'].isin(['Vacant Unrented Ready'])].mean()), 
            ('median_days_on_market', 'median'), 
            ('median_days_on_market_prelease', lambda x: x[homes_rented_df['last_status'].isin(['Notice Unrented', 'Vacant Unrented Not Ready'])].median()), 
            ('median_days_on_market_rent_ready', lambda x: x[homes_rented_df['last_status'].isin(['Vacant Unrented Ready'])].median())
        ],
    }).round(2)
    stats_df.columns = pd.MultiIndex.from_tuples([
        ('# Homes Leased', ''),
        ('# Homes Leased', 'Pre-lease'),
        ('# Homes Leased', 'Rent Ready'),
        ('Average Rent Δ ($)', ''),
        ('Average Rent Δ ($)', 'Pre-lease'),
        ('Average Rent Δ ($)', 'Rent Ready'),
        ('Median Rent Δ ($)', ''),
        ('Median Rent Δ ($)', 'Pre-lease'),
        ('Median Rent Δ ($)', 'Rent Ready'),
        ('Average Days on Market', ''),
        ('Average Days on Market', 'Pre-lease'),
        ('Average Days on Market', 'Rent Ready'), 
        ('Median Days on Market', ''), 
        ('Median Days on Market', 'Pre-lease'),
        ('Median Days on Market', 'Rent Ready')
    ])
    st.dataframe(stats_df, use_container_width=True)



def turn_times(filtered_leasing_period_df, color_scale):
    st.subheader("Turn Times")
    turn_times_df = filtered_leasing_period_df[filtered_leasing_period_df['actual_turn_time'].notna()]

    # Histogram
    turn_times_histogram = alt.Chart(turn_times_df).mark_bar(color=TEAL).encode(
        x=alt.X('actual_turn_time:Q', bin=alt.Bin(maxbins=30), title='Turn Time (days)', axis=alt.Axis(format='d')),
        y=alt.Y('count()', title='# Homes'),
        tooltip=[
            alt.Tooltip('count()', title='# Homes'),
            alt.Tooltip('actual_turn_time:Q', title='Turn Time (days)')
        ]
    )
    st.altair_chart(turn_times_histogram, use_container_width=True)

    # Summary Statistics
    st.markdown("<h6><b>Summary Statistics</b></h6>", unsafe_allow_html=True)
    stats_df = turn_times_df.groupby('market_name').agg(
        **{
            '# Homes Turned': ('actual_turn_time', 'count'),
            'Average Turn Time (days)': ('actual_turn_time', 'mean'),
            'Median Turn Time (days)': ('actual_turn_time', 'median'), 
        }
    ).round(2)
    st.dataframe(stats_df, use_container_width=True)





    






















