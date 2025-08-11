import streamlit as st
import pandas as pd
import altair as alt
from tabs.utils import LIGHT_GRAY, LIGHT_TEAL, LIGHT_PURPLE, DARK_PURPLE

def vacancy_filters(distinct_vacancy_df, vacancy_df):
    distinct_vacancies = distinct_vacancy_df['address'] + ' -- ' + distinct_vacancy_df['vacancy_start_date'].astype(str)
    selected_vacancy = st.selectbox("Select Vacancy", distinct_vacancies.unique()).split(' -- ')

    filtered_vacancy_df = vacancy_df[
        (vacancy_df['address'] == selected_vacancy[0]) & 
        (vacancy_df['vacancy_start_date'].astype(str) == selected_vacancy[1])
    ]
    return filtered_vacancy_df, selected_vacancy



def vacancy_curve(filtered_vacancy_df):
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total # Inquiries", filtered_vacancy_df['cumulative_num_inquiries'].max())
    with col2:
        st.metric("Total # Tours", filtered_vacancy_df['cumulative_num_tours'].max())
    with col3:
        st.metric("Total # Applications", filtered_vacancy_df['cumulative_num_applications'].max())
    with col4:
        st.metric("# Days Vacant", filtered_vacancy_df['days_since_vacancy_start'].max())
    with col5:
        st.metric("# Days Listed", filtered_vacancy_df['is_internally_listed'].sum())

    # Melt the data for easier plotting with Altair
    chart_data_melted = pd.melt(
        filtered_vacancy_df, 
        id_vars=['days_since_vacancy_start'],
        value_vars=['cumulative_num_inquiries', 'cumulative_num_tours', 'cumulative_num_applications'],
        var_name='metric',
        value_name='count'
    )
    
    # Rename metrics for better display
    metric_names = {
        'cumulative_num_inquiries': 'Inquiries',
        'cumulative_num_tours': 'Tours',
        'cumulative_num_applications': 'Applications'
    }
    chart_data_melted['metric'] = chart_data_melted['metric'].map(metric_names)
    
    # Define colors for each metric
    color_scale = alt.Scale(domain=['Inquiries', 'Tours', 'Applications'], 
                           range=[LIGHT_TEAL, LIGHT_PURPLE, DARK_PURPLE])
    
    # Create background layer for internally listed days
    background = alt.Chart(filtered_vacancy_df).mark_bar(
        opacity=0.3,
        width=10,
        color=LIGHT_GRAY
    ).encode(
        x=alt.X('days_since_vacancy_start:Q'),
        y=alt.value(0),
        y2=alt.value('height')
    ).transform_filter(
        alt.datum.is_internally_listed == True
    )

    # Prepare dummy background data for legend
    background_data = filtered_vacancy_df[filtered_vacancy_df['is_internally_listed']][['days_since_vacancy_start']]
    background_data['metric'] = 'Listing Window'
    background_data['count'] = 0  # Won't be visible as lines since all values are 0

    # Combine chart data with background data
    combined_data = pd.concat([chart_data_melted, background_data], ignore_index=True)

    # Update color scale to include the background
    color_scale = alt.Scale(
        domain=['Inquiries', 'Tours', 'Applications', 'Listing Window'], 
        range=[LIGHT_TEAL, LIGHT_PURPLE, DARK_PURPLE, LIGHT_GRAY]
    )

    # Create Altair line chart with updated data
    chart = alt.Chart(combined_data).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X('days_since_vacancy_start:Q', title='Days Since Vacancy Start'),
        y=alt.Y('count:Q', title='Cumulative Count'),
        color=alt.Color('metric:N', scale=color_scale, title='Metric'),
        tooltip=[
            alt.Tooltip('days_since_vacancy_start:Q', title='Days Since Start'),
            alt.Tooltip('metric:N', title='Metric'),
            alt.Tooltip('count:Q', title='Count')
        ]
    )
    
    st.subheader("Cumulative Metrics Over Vacancy")
    st.altair_chart(background + chart, use_container_width=True)

    
    