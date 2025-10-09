import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

from tabs.utils import TEAL, DARK_TEAL, LIGHT_GRAY


def competitors_filters(leasing_df, leasing_rent_weekly_rent_changes_df, rent_curve_df):
    col_date_range, col_market, col_competitor = st.columns(3)
    filtered_leasing_period_df = leasing_df.copy()
    filtered_leasing_rent_weekly_rent_changes_df = leasing_rent_weekly_rent_changes_df.copy()
    filtered_rent_curve_df = rent_curve_df.copy()

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
            filtered_leasing_rent_weekly_rent_changes_df = filtered_leasing_rent_weekly_rent_changes_df[(filtered_leasing_rent_weekly_rent_changes_df['week_start'] <= end_date) & 
                                                                                                            (filtered_leasing_rent_weekly_rent_changes_df['week_end'] >= start_date)]
    with col_market:
        selected_market = st.selectbox("Select a market", 
                                options=['All'] + sorted(filtered_leasing_period_df['market_name'].unique()), 
                                index=0,
                                key='competitors_market')
        color_scale = alt.Scale(scheme='tealblues')  
        if selected_market != 'All':
            filtered_leasing_period_df = filtered_leasing_period_df[filtered_leasing_period_df['market_name'] == selected_market]
            filtered_leasing_rent_weekly_rent_changes_df = filtered_leasing_rent_weekly_rent_changes_df[filtered_leasing_rent_weekly_rent_changes_df['market_name'] == selected_market]
            filtered_rent_curve_df = filtered_rent_curve_df[filtered_rent_curve_df['market_name'] == selected_market]
            color_scale = alt.Scale(range=[TEAL]) 
    
    with col_competitor:
        selected_competitor = st.selectbox("Select a competitor", 
                                options=['All'] + list(filtered_leasing_period_df['source'].unique()), 
                                index=0,
                                key='competitors_competitor')
        if selected_competitor != 'All':
            filtered_leasing_period_df = filtered_leasing_period_df[filtered_leasing_period_df['source'] == selected_competitor]
            filtered_leasing_rent_weekly_rent_changes_df = filtered_leasing_rent_weekly_rent_changes_df[filtered_leasing_rent_weekly_rent_changes_df['source'] == selected_competitor]
            filtered_rent_curve_df = filtered_rent_curve_df[filtered_rent_curve_df['source'] == selected_competitor]

    
    
    return filtered_leasing_period_df, filtered_leasing_rent_weekly_rent_changes_df, filtered_rent_curve_df, start_date, end_date, color_scale



def metrics():
    st.subheader("Metrics")
    st.markdown('''
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px;">
        <strong>actual_vacated</strong>: when status changes from 'Notice Unrented' to 'Vacant Unrented Not Ready'<br>
        <strong>actual_available</strong>: when status changes from 'Vacant Unrented Not Ready' to 'Vacant Unrented Ready'<br>
        <strong>latest_lease_signed</strong>: day after the last pull date, if there are 14+ days since home has appeared in pull<br>
        <strong>total_leases_signed</strong> = 1 (if latest_lease_signed exists) + # leases signed that didn't go through (number of gaps ranging 14-30 days)<br>
        <strong>actual_turn_time</strong> = days between actual_vacated and actual_available<br>
        <strong>home_rented_days_on_market</strong> = days between lease_signed and actual_available (estimated available_on if actual_available does not exist)
        </div>
    ''', unsafe_allow_html=True)



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



def weekly_rent_changes(leasing_rent_weekly_rent_changes_df):
    st.subheader("Average Rent Δ per Property")
    average_rent_change_df = (
        leasing_rent_weekly_rent_changes_df
        .groupby(['week_start', 'week_end'])
        .agg(
            num_properties=('num_properties', 'sum'),
            num_properties_with_rent_changes=('num_properties_with_rent_changes', 'sum'), 
            total_rent_change=('total_rent_change', 'sum'))
        .reset_index()
        .assign(
            average_rent_change_all_homes=lambda d: d['total_rent_change'] / d['num_properties'], 
            average_rent_change=lambda d: d['total_rent_change'] / d['num_properties_with_rent_changes']
        )
    )

    average_rent_change_df['week_end_str'] = pd.to_datetime(average_rent_change_df['week_end']).dt.strftime('%Y-%m-%d')

    for avg_rent_change_col in ['average_rent_change_all_homes', 'average_rent_change']:
        homes_included = 'all homes' if avg_rent_change_col == 'average_rent_change_all_homes' else 'only the homes with rent changes'
        average_rent_change_chart = alt.Chart(average_rent_change_df).mark_bar(color=TEAL).encode(
            x=alt.X('week_end_str:O', title='Week End'),
            y=alt.Y(f'{avg_rent_change_col}:Q', title=f'Average Rent Δ per Property'),
            color=alt.condition(
                f"datum.{avg_rent_change_col} > 0",
                alt.value(TEAL),
                alt.value(DARK_TEAL)
            ),
            tooltip=[
                alt.Tooltip('week_end:T', title='Week End'),
                alt.Tooltip('num_properties_with_rent_changes:Q', title='# Properties with Rent Δs'),
                alt.Tooltip('num_properties:Q', title='Number of Properties'), 
                alt.Tooltip(f'{avg_rent_change_col}:Q', title='Average Rent Δ', format='$.2f')
            ]
        ).properties(
            title=alt.Title(
                text='All Homes' if avg_rent_change_col == 'average_rent_change_all_homes' else 'Homes with Rent Changes', 
                subtitle=f'The average rent change in the week across **{homes_included}**'
            ), 
            width=600,
            height=400
        )
        average_rent_change_text = (
            average_rent_change_chart
            .transform_calculate(
                dy_offset=f"datum.{avg_rent_change_col} > 0 ? -7 : 7",
                label_color=f"datum.{avg_rent_change_col} > 0 ? '{TEAL}' : '{DARK_TEAL}'"
            )
            .mark_text(
                align='center',
                baseline='middle',
                dy={"expr": "datum.dy_offset"},
                color={"expr": "datum.label_color"}
            )
            .encode(
                text=alt.Text(f'{avg_rent_change_col}:Q', format="$.2f")
            )
        )

        st.altair_chart(average_rent_change_chart + average_rent_change_text, use_container_width=True)



def rent_curve(leasing_rent_weekly_rent_changes_df):
    st.subheader("Rent Curve")
    col_month, col_leasing_type = st.columns(2)
    with col_month:
        rent_curve_months = sorted(leasing_rent_weekly_rent_changes_df['month'].unique())
        selected_month = st.selectbox("Select a month", options=rent_curve_months, 
                                        key='rent_curve_month', index=len(rent_curve_months) - 1)
    with col_leasing_type:
        selected_leasing_type = st.selectbox("Select a leasing type", options=leasing_rent_weekly_rent_changes_df['leasing_type'].unique(), key='rent_curve_leasing_type')

    graph_rent_curve_df = leasing_rent_weekly_rent_changes_df[
        (leasing_rent_weekly_rent_changes_df['month'] == selected_month) &
        (leasing_rent_weekly_rent_changes_df['leasing_type'] == selected_leasing_type)
    ].groupby('leasing_day').agg(
        total_rent=('total_rent', 'sum'),
        total_rent_ratio_to_day_zero=('total_rent_ratio_to_day_zero', 'sum'), 
        distinct_properties=('distinct_properties', 'sum')
    ).reset_index()

    graph_rent_curve_df['avg_rent'] = graph_rent_curve_df['total_rent'] / graph_rent_curve_df['distinct_properties']
    graph_rent_curve_df['avg_rent_ratio_to_day_zero'] = graph_rent_curve_df['total_rent_ratio_to_day_zero'] / graph_rent_curve_df['distinct_properties']
    vertical_line = alt.Chart(pd.DataFrame({'leasing_day': [-70, -63, -56, -49, -42, -35, -28, -21, -14, -7, 0, 7, 14, 21, 28, 35, 42, 49, 56, 63, 70]})).mark_rule().encode(
        x='leasing_day:O',
        color=alt.condition(
            alt.datum.leasing_day == 0,
            alt.value('gray'), 
            alt.value('lightgray') 
        )
    )

    # Average Rent
    st.subheader("Average Rent")
    rent_curve_chart = alt.Chart(graph_rent_curve_df).mark_line(color=TEAL, point={'color': TEAL}).encode(
        x=alt.X('leasing_day:O', title='Leasing Day'),
        y=alt.Y('avg_rent:Q', title='Average Rent ($)', 
                scale=alt.Scale(domain=(graph_rent_curve_df['avg_rent'].min() - 50, graph_rent_curve_df['avg_rent'].max() + 50)),
                axis=alt.Axis(format='$,.0f'))
    )
    st.altair_chart(vertical_line + rent_curve_chart, use_container_width=True)
    graph_rent_curve_df['avg_rent'] = graph_rent_curve_df['avg_rent'].apply(lambda x: f"${x:,.2f}")
    st.dataframe(graph_rent_curve_df[['leasing_day', 'avg_rent']], hide_index=True, use_container_width=True)


    # Current Rent Ratio to Day Zero    
    st.subheader("Current Rent Ratio to Day Zero")
    rent_curve_chart = alt.Chart(graph_rent_curve_df).mark_line(color=TEAL, point={'color': TEAL}).encode(
        x=alt.X('leasing_day:O', title='Leasing Day'),
        y=alt.Y('avg_rent_ratio_to_day_zero:Q', title='Average Rent Ratio to Day Zero', 
                scale=alt.Scale(domain=(graph_rent_curve_df['avg_rent_ratio_to_day_zero'].min() - .05, graph_rent_curve_df['avg_rent_ratio_to_day_zero'].max() + .05)),
                axis=alt.Axis(format='.0%'))
    )
    st.altair_chart(vertical_line + rent_curve_chart, use_container_width=True)
    graph_rent_curve_df['avg_rent_ratio_to_day_zero'] = graph_rent_curve_df['avg_rent_ratio_to_day_zero'].apply(lambda x: f"{x:.2%}")
    st.dataframe(graph_rent_curve_df[['leasing_day', 'avg_rent_ratio_to_day_zero']], hide_index=True, use_container_width=True)




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



def leased_homes_stats(filtered_leasing_period_df, leasing_rent_individual_rent_changes_df, start_date, end_date, color_scale):
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
    st.subheader("% of Signed Leases by Day of Week")
    homes_rented_type_df['lease_signed_day_of_week'] = pd.to_datetime(homes_rented_type_df['last_lease_signed']).dt.day_name()
    lease_signed_dow_perc = round(homes_rented_type_df['lease_signed_day_of_week'].value_counts(normalize=True) * 100, 2).reset_index()
    lease_signed_dow_perc.columns = ['Day of Week', 'Percentage']
    lease_signed_dow_perc_chart = alt.Chart(lease_signed_dow_perc).mark_bar(color=TEAL).encode(
        x=alt.X('Day of Week', sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                axis=alt.Axis(labelAngle=0)), 
        y=alt.Y('Percentage', title='% of Signed Leases')
    ).properties(
        width=600,
        height=400
    )
    lease_signed_dow_perc_text = lease_signed_dow_perc_chart.mark_text(
        align='center',
        baseline='bottom',
        dy=-2, 
        color=DARK_TEAL
    ).encode(
        text=alt.Text('Percentage:Q', format=".2f")
    ).transform_calculate(
        label=alt.datum.Percentage + '%' 
    ).encode(
        text='label:N'
    )
    st.altair_chart(lease_signed_dow_perc_chart + lease_signed_dow_perc_text, use_container_width=True)



    # Leased Homes Summary Statistics
    st.subheader("Summary Statistics (Rent Δ & Days on Market )")
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


    # Rent Change Chart
    st.subheader("Rent Δ")
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
            text='Leased Rent - Initial Rent Δ', 
            subtitle='Each point represents the rent on the first day it was listed minus the day it was leased'
        )
    )
    zero_line = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(
        color='gray'
    ).encode(x='x:Q')
    st.altair_chart((rent_change_chart + zero_line), use_container_width=True)



    # Individual Rent Changes Chart
    filtered_leasing_rent_changes_df = leasing_rent_individual_rent_changes_df.merge(
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
            text='Individual Rent Δs', 
            subtitle='Each point represents a single change in rent for a home leased in the period range vs how many days the home has been listed on that rent change day'
        ),
        height=800
    )
    st.altair_chart(individual_rent_changes_chart, use_container_width=True)



    # Days on Market Chart
    st.subheader("Days on Market")
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
        title=alt.Title(
            text='Days on Market', 
            subtitle='Each point represents how many days a home had been on market when it got leased'
        )
    )
    st.altair_chart(dom_chart + zero_line, use_container_width=True)
























