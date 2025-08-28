import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import altair as alt

from tabs.utils import GRAY, TEAL, PURPLE

def turn_cost_over_time(turns_df):
    st.subheader("Turn Cost Over Time")

    selected_weeks = st.slider('Select # weeks to view:', min_value=1, max_value=52, value=3)
    turns_df['project_end_date'] = pd.to_datetime(turns_df['project_end_date'])
    filtered_df = turns_df[turns_df['project_end_date'] >= datetime.now() - timedelta(days=selected_weeks*7)]
    filtered_df['project_end_date_str'] = filtered_df['project_end_date'].dt.strftime('%Y-%m-%d')

    grouped_df = filtered_df.groupby('project_end_date_str').agg({
        'rental_id': 'count',
        'project_total_estimated_cost': 'mean', 
        'project_invoiced_cost': 'mean',
    }).rename(columns={'rental_id': 'num_turns'}).reset_index()

    melted_df = grouped_df.melt(
        id_vars=['project_end_date_str'],
        value_vars=['project_invoiced_cost', 'project_total_estimated_cost'],
        var_name='cost_type',
        value_name='cost'
    )
    melted_df['cost_type'] = melted_df['cost_type'].map({'project_invoiced_cost': 'Invoiced Cost', 'project_total_estimated_cost': 'Estimated Cost'})
    cost_chart = alt.Chart(melted_df).mark_bar().encode(
        x=alt.X('project_end_date_str:O', title='Project End Date', axis=alt.Axis(labelAngle=-90)),
        y=alt.Y('cost:Q', title='Cost'),
        color=alt.Color('cost_type:N', scale=alt.Scale(range=[TEAL, PURPLE])), 
        xOffset='cost_type:N', 
        tooltip=[
            alt.Tooltip("project_end_date_str:O", title='Project End Date'), 
            alt.Tooltip('cost_type:N', title='Cost Type'), 
            alt.Tooltip('cost:Q', title='Cost', format='$,.0f')
        ]
    )

    num_turns_chart = alt.Chart(grouped_df).mark_line(color=GRAY, point={'color': GRAY}).encode(
        x=alt.X('project_end_date_str:O', title='Project End Date', axis=alt.Axis(labelAngle=-90)),
        y=alt.Y('num_turns:Q', title='Number of Turns'),
    )

    st.altair_chart(alt.layer(cost_chart, num_turns_chart).resolve_scale(y='independent'), use_container_width=True)





    