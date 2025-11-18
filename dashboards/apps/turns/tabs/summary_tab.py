import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import streamlit as st
import altair as alt

from tabs.utils import GRAY, TEAL, PURPLE

def turn_filters(turns_df):
    st.subheader("Turn Cost Over Time Filters")
    col_fund, col_market, col_level = st.columns(3)

    filtered_turns_df = turns_df.copy()

    with col_fund:
        selected_fund = st.selectbox("Select Fund", ['All'] + sorted(list(turns_df['fund'].unique())))
        if selected_fund != 'All':
            filtered_turns_df = filtered_turns_df[filtered_turns_df['fund'] == selected_fund]
    with col_market:
        selected_market = st.selectbox("Select Market", ['All'] + sorted(list(turns_df['market'].unique())))
        if selected_market != 'All':
            filtered_turns_df = filtered_turns_df[filtered_turns_df['market'] == selected_market]
    with col_level:
        selected_time_granularity = st.selectbox("Select time granularity", ['weekly', 'monthly'])

    return filtered_turns_df, selected_time_granularity


def total_turn_cost_over_time(turns_df, selected_time_granularity):
    st.subheader("Turn Cost Over Time")

    time_granularity_col = f'project_{selected_time_granularity}_end_date'
    if selected_time_granularity == 'weekly':
        title = 'Week End'
            
        # Week end date
        turns_df[time_granularity_col] = pd.to_datetime(turns_df['project_end_date']).apply(
            lambda d: d + relativedelta(days=6 - d.dayofweek) if pd.notnull(d) else pd.NaT
        )
        this_week = datetime.now().date() + relativedelta(days=6 - datetime.now().date().weekday())
        cutoff_date = this_week - timedelta(weeks=12)
        # add empty weeks
        all_dates = pd.date_range(
            start=cutoff_date,
            end=this_week,
            freq='W-SUN'
        ).strftime('%Y-%m-%d')
        all_dates_df = pd.DataFrame({f'{time_granularity_col}_str': all_dates})

    elif selected_time_granularity == 'monthly':
        title = 'Month End'
        # Month end date
        turns_df[time_granularity_col] = pd.to_datetime(turns_df['project_end_date']).apply(
            lambda d: (d + relativedelta(day=31)) if pd.notnull(d) else pd.NaT
        )
        this_month = datetime.now().date() + relativedelta(day=31)
        cutoff_date = this_month - relativedelta(months=3)
        # add empty months
        all_dates = pd.date_range(
            start=cutoff_date, 
            end=turns_df[time_granularity_col].max(), 
            freq='M'
        ).strftime('%Y-%m-%d')
        all_dates_df = pd.DataFrame({f'{time_granularity_col}_str': all_dates})


    filtered_df = turns_df[turns_df[time_granularity_col] >= pd.to_datetime(cutoff_date)]
    filtered_df[f'{time_granularity_col}_str'] = filtered_df[time_granularity_col].dt.strftime('%Y-%m-%d')
    grouped_df = filtered_df.groupby(f'{time_granularity_col}_str').agg({
        'rental_id': 'count',
        'project_total_estimated_cost': 'mean', 
        'project_invoiced_cost': 'mean',
    }).rename(columns={'rental_id': 'num_turns'}).reset_index()
    grouped_df['project_total_estimated_cost_per_turn'] = grouped_df['project_total_estimated_cost'] / grouped_df['num_turns']
    grouped_df['project_invoiced_cost_per_turn'] = grouped_df['project_invoiced_cost'] / grouped_df['num_turns']
    grouped_df['# Turns'] = 0
    grouped_df = all_dates_df.merge(grouped_df, on=f'{time_granularity_col}_str', how='left').fillna(0)


    for cost_type in ['total', 'per_turn']:
        if cost_type == 'total':
            value_vars = ['project_invoiced_cost', 'project_total_estimated_cost', '# Turns']
        else:
            value_vars = ['project_invoiced_cost_per_turn', 'project_total_estimated_cost_per_turn', '# Turns']

        melted_df = grouped_df.melt(
            id_vars=[f'{time_granularity_col}_str'],
            value_vars=value_vars,
            var_name='cost_type',
            value_name='cost'
        )
        
        # Add num_turns column for tooltip
        melted_df = melted_df.merge(
            grouped_df[[f'{time_granularity_col}_str', 'num_turns']],
            on=f'{time_granularity_col}_str',
            how='left'
        )
        melted_df['cost_type'] = melted_df['cost_type'].map({value_vars[0]: 'Invoiced Cost', value_vars[1]: 'Estimated Cost', value_vars[2]: '# Turns'})
        cost_chart = alt.Chart(melted_df).mark_bar().encode(
            x=alt.X(f'{time_granularity_col}_str:O', title=title, axis=alt.Axis(labelAngle=-90)),
            y=alt.Y('cost:Q', title='Cost'),
            color=alt.Color('cost_type:N', scale=alt.Scale(range=[GRAY, TEAL, PURPLE])), 
            xOffset='cost_type:N',
            tooltip=[
                alt.Tooltip(f'{time_granularity_col}_str:O', title=title), 
                alt.Tooltip('cost_type:N', title='Type'), 
                alt.Tooltip('cost:Q', title='Cost', format='$,.0f'), 
                alt.Tooltip('num_turns:Q', title='# Turns')
            ], 
        ).properties(
            width=600,
            height=400, 
            title=alt.Title(
                text='Total Cost' if cost_type == 'total' else 'Cost Per Turn', 
                subtitle=f'Total Cost / # Turns' if cost_type == 'per_turn' else ''
            )
        )

        num_turns_chart = alt.Chart(melted_df).mark_line(color=GRAY, point={'color': GRAY}).encode(
            x=alt.X(f'{time_granularity_col}_str:O', title=title, axis=alt.Axis(labelAngle=-90)),
            y=alt.Y('num_turns:Q', title='Number of Turns')
        )
        st.altair_chart(alt.layer(cost_chart, num_turns_chart).resolve_scale(y='independent'), use_container_width=True)









    