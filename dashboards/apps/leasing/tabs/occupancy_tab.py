import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime

from tabs.utils import TEAL, PURPLE


def occupancy_filters(projected_economic_occupancy_df, budget_economic_occupancy_df, rental_df):
    col_fund, col_market = st.columns(2)

    filtered_projected_economic_occupancy_df = projected_economic_occupancy_df.copy()
    filtered_budget_economic_occupancy_df = budget_economic_occupancy_df.copy()
    filtered_rental_df = rental_df.copy()
    with col_fund:
        selected_fund = st.selectbox("Select a fund", ['All'] + sorted(list(projected_economic_occupancy_df['fund'].unique())))
        if selected_fund != 'All':
            filtered_projected_economic_occupancy_df = filtered_projected_economic_occupancy_df[filtered_projected_economic_occupancy_df['fund'] == selected_fund]
            filtered_budget_economic_occupancy_df = filtered_budget_economic_occupancy_df[filtered_budget_economic_occupancy_df['fund'] == selected_fund]
            filtered_rental_df = filtered_rental_df[filtered_rental_df['fund'] == selected_fund]
    with col_market:
        selected_market = st.selectbox("Select a market", ['All'] + sorted(list(filtered_projected_economic_occupancy_df['market'].unique())))
        if selected_market != 'All':
            filtered_projected_economic_occupancy_df = filtered_projected_economic_occupancy_df[filtered_projected_economic_occupancy_df['market'] == selected_market]
            filtered_budget_economic_occupancy_df = filtered_budget_economic_occupancy_df[filtered_budget_economic_occupancy_df['market'] == selected_market]
            filtered_rental_df = filtered_rental_df[filtered_rental_df['market'] == selected_market]
    return filtered_projected_economic_occupancy_df, filtered_budget_economic_occupancy_df, filtered_rental_df


def occupancy_metrics(projected_economic_occupancy_df, budget_economic_occupancy_df):
    economic_occupancy_col, physical_occupancy_col = st.columns(2)
    today_occupancy = projected_economic_occupancy_df[projected_economic_occupancy_df['date'] == datetime.now()]
    with economic_occupancy_col:
        st.metric("Economic Occupancy", 
                  f"{round(today_occupancy['total_gpr_not_vacant'].sum() * 100 / today_occupancy['total_gpr'].sum(), 2)}%", 
                  help="Today's Rent Charged / Today's GPR")
    with physical_occupancy_col:
        st.metric("Physical Occupancy", 
                  f"{round(today_occupancy['num_properties_not_vacant'].sum() * 100 / today_occupancy['num_properties'].sum(), 2)}%", 
                  help="\# Homes Occupied / \# Homes")


def economic_occupancy(projected_economic_occupancy_df, budget_economic_occupancy_df):
    st.subheader("Economic Occupancy")
    # 1. Projected Economic Occupancy
    monthly_projected_economic_occupancy = projected_economic_occupancy_df[projected_economic_occupancy_df['time_granularity'] == 'month'].groupby('date').agg(
        total_gpr_not_vacant=('total_gpr_not_vacant', 'sum'),
        total_gpr=('total_gpr', 'sum')
    ).reset_index()
    monthly_projected_economic_occupancy['economic_occupancy_projected'] = monthly_projected_economic_occupancy['total_gpr_not_vacant'] * 100 / monthly_projected_economic_occupancy['total_gpr']

    # 2. Budget Economic Occupancy
    monthly_budget_economic_occupancy = budget_economic_occupancy_df[budget_economic_occupancy_df['time_granularity'] == 'month'].groupby('period_start').agg(
        total_gpr_not_vacant=('gross_potential_rent_not_vacant', 'sum'),
        total_gpr=('gross_potential_rent', 'sum')
    ).reset_index()
    monthly_budget_economic_occupancy['economic_occupancy_budget'] = monthly_budget_economic_occupancy['total_gpr_not_vacant'] * 100 / monthly_budget_economic_occupancy['total_gpr']
    
    # 3. Combine Projected and Budget Economic Occupancy
    economic_occupancy = pd.merge(monthly_projected_economic_occupancy, monthly_budget_economic_occupancy, left_on='date', right_on='period_start', how='inner').melt(
        id_vars=['date'],
        value_vars=['economic_occupancy_projected', 'economic_occupancy_budget'],
        var_name='type',
        value_name='value'
    )
    economic_occupancy['month_str'] = pd.to_datetime(economic_occupancy['date']).dt.strftime('%Y-%m')
    economic_occupancy['type'] = economic_occupancy['type'].map({'economic_occupancy_projected': 'Projected', 'economic_occupancy_budget': 'Target'})

    all_months = pd.date_range(
        start=(monthly_projected_economic_occupancy['date'].min()),
        end=monthly_projected_economic_occupancy['date'].max(),
        freq='MS'
    )

    min_value = max(economic_occupancy['value'].min() - 10, 0)

    chart = alt.Chart(economic_occupancy).mark_line(point=True).encode(
        x=alt.X('month_str:O', title='Month', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('value:Q', title='Economic Occupancy (%)',
                scale=alt.Scale(domain=[min_value, 100], padding=10)),
        color=alt.Color('type:N', scale=alt.Scale(range=[TEAL, PURPLE])), 
        tooltip=[
            alt.Tooltip("month_str:O", title='Month'), 
            alt.Tooltip('type:N', title='Type'), 
            alt.Tooltip('value:Q', title='Value (%)', format='.2f')
        ]
    )

    st.altair_chart(chart)


def upcoming_moves(rental_df): 
    types = {
        'occupancy_date': 'Move-In Date',
        'move_out_date': 'Move-Out Date'
    }
    for type in types.keys():
        formal_type = types[type].replace(' Date', '')
        st.subheader(f"Upcoming {formal_type}s")

        upcoming_moves = rental_df[rental_df[type] > datetime.now()][['address', 'fund', 'market', type]]
        if upcoming_moves.empty:
            st.badge(f"No upcoming {formal_type}s!", color="violet")
            continue
        upcoming_moves['month'] = pd.to_datetime(upcoming_moves[type]).dt.strftime('%B %Y')
        upcoming_moves.sort_values(by=type, ascending=True, inplace=True)
        upcoming_moves.columns = [col.replace('_', ' ').title() for col in upcoming_moves.columns]
        st.dataframe(upcoming_moves, hide_index=True)


def num_leases_to_target(projected_economic_occupancy_df, budget_economic_occupancy_df):
    st.subheader("Number of Leases to Target")

    st.dataframe(projected_economic_occupancy_df)
    st.dataframe(budget_economic_occupancy_df)


    this_month_projected = projected_economic_occupancy_df[(projected_economic_occupancy_df['time_granularity'] == 'month') & 
                                                           (projected_economic_occupancy_df['date'] == datetime(datetime.now().year, datetime.now().month, 1))]
    st.dataframe(this_month_projected)













