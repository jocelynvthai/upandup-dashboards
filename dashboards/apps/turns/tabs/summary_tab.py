import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import streamlit as st
import altair as alt

from tabs.utils import GRAY, TEAL, PURPLE

def turn_cost_over_time_filters(turns_df):
    st.subheader("Turn Cost Over Time Filters")
    col_fund, col_types, col_address = st.columns(3)
    filtered_turns_df = turns_df.copy()
    with col_fund:
        selected_fund = st.selectbox("Select Fund", ['All'] + list(turns_df['fund'].unique()))
        if selected_fund != 'All':
            filtered_turns_df = filtered_turns_df[filtered_turns_df['fund'] == selected_fund]
    return filtered_turns_df


def turn_cost_over_time(turns_df):
    st.subheader("Turn Cost Over Time")

    # Filter by fund
    selected_fund = st.selectbox("Select Fund", ['All'] + sorted(list(turns_df['fund'].unique())))
    if selected_fund != 'All':
        turns_df = turns_df[turns_df['fund'] == selected_fund]

    # Convert to weekly data
    turns_df['project_week_end_date'] = pd.to_datetime(turns_df['project_end_date']).apply(
        lambda d: d + relativedelta(days=6 - d.dayofweek) if pd.notnull(d) else pd.NaT
    )
    cutoff_date = datetime.now().date() + relativedelta(days=6 - datetime.now().date().weekday()) - timedelta(weeks=12)
    filtered_df = turns_df[turns_df['project_week_end_date'] >= pd.to_datetime(cutoff_date)]
    filtered_df['project_week_end_date_str'] = filtered_df['project_week_end_date'].dt.strftime('%Y-%m-%d')
    grouped_df = filtered_df.groupby('project_week_end_date_str').agg({
        'rental_id': 'count',
        'project_total_estimated_cost': 'mean', 
        'project_invoiced_cost': 'mean',
    }).rename(columns={'rental_id': 'num_turns'}).reset_index()
    grouped_df['project_total_estimated_cost_per_turn'] = grouped_df['project_total_estimated_cost'] / grouped_df['num_turns']
    grouped_df['project_invoiced_cost_per_turn'] = grouped_df['project_invoiced_cost'] / grouped_df['num_turns']

    # add emtpy weeks
    all_weeks = pd.date_range(
        start=cutoff_date, 
        end=turns_df['project_week_end_date'].max(), 
        freq='W-SUN'
    ).strftime('%Y-%m-%d')
    all_weeks_df = pd.DataFrame({'project_week_end_date_str': all_weeks})
    grouped_df = all_weeks_df.merge(grouped_df, on='project_week_end_date_str', how='left').fillna(0)

    for cost_type in ['total', 'per_turn']:
        if cost_type == 'total':
            value_vars = ['project_invoiced_cost', 'project_total_estimated_cost']
        else:
            value_vars = ['project_invoiced_cost_per_turn', 'project_total_estimated_cost_per_turn']

        melted_df = grouped_df.melt(
            id_vars=['project_week_end_date_str'],
            value_vars=value_vars,
            var_name='cost_type',
            value_name='cost'
        )
        
        # Add num_turns column for tooltip
        melted_df = melted_df.merge(
            grouped_df[['project_week_end_date_str', 'num_turns']],
            on='project_week_end_date_str',
            how='left'
        )
        melted_df['cost_type'] = melted_df['cost_type'].map({value_vars[0]: 'Invoiced Cost', value_vars[1]: 'Estimated Cost'})
        cost_chart = alt.Chart(melted_df).mark_bar().encode(
            x=alt.X('project_week_end_date_str:O', title='Week End', axis=alt.Axis(labelAngle=-90)),
            y=alt.Y('cost:Q', title='Cost'),
            color=alt.Color('cost_type:N', scale=alt.Scale(range=[TEAL, PURPLE])), 
            xOffset='cost_type:N', 
            tooltip=[
                alt.Tooltip("project_week_end_date_str:O", title='Week End'), 
                alt.Tooltip('cost_type:N', title='Cost Type'), 
                alt.Tooltip('cost:Q', title='Cost', format='$,.0f'), 
                alt.Tooltip('num_turns:Q', title='Number of Turns')
            ], 
            
        ).properties(
            width=600,
            height=400, 
            title=alt.Title(
                text='Total Cost' if cost_type == 'total' else 'Cost Per Turn', 
            )
        )
        if cost_type == 'total':
            num_turns_chart = alt.Chart(melted_df).mark_line(color=GRAY, point={'color': GRAY}).encode(
                x=alt.X('project_week_end_date_str:O', title='Week End', axis=alt.Axis(labelAngle=-90)),
                y=alt.Y('num_turns:Q', title='Number of Turns'),
            )
            st.altair_chart(alt.layer(cost_chart, num_turns_chart).resolve_scale(y='independent'), use_container_width=True)
        else:
            st.altair_chart(cost_chart, use_container_width=True)





    