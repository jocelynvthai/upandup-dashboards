import streamlit as st
import pandas as pd
import altair as alt
from tabs.utils import LIGHT_GRAY, TEAL, LIGHT_PURPLE, PURPLE, DARK_PURPLE

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

    
    # 1. is_internally_listed background
    background = alt.Chart(filtered_vacancy_df).mark_bar(
        opacity=0.3,
        width=10,
        color=LIGHT_GRAY
    ).encode(
        x=alt.X('days_since_vacancy_start:Q'),
        y=alt.value(0),
        y2=alt.value('height'), 
        tooltip=[
            alt.Tooltip('days_since_vacancy_start:Q', title='Days Since Vacancy Start'),
            alt.Tooltip('is_internally_listed:N', title='Is Internally Listed')
        ]
    ).transform_filter(
        alt.datum.is_internally_listed == True
    )

    # prepare data for metrics over vacancy line charts
    chart_data_melted = pd.melt(
        filtered_vacancy_df, 
        id_vars=['days_since_vacancy_start'],
        value_vars=['cumulative_num_inquiries', 'cumulative_num_tours', 'cumulative_num_applications'],
        var_name='metric',
        value_name='count'
    )
    metric_names = {
        'cumulative_num_inquiries': 'Inquiries',
        'cumulative_num_tours': 'Tours',
        'cumulative_num_applications': 'Applications'
    }
    chart_data_melted['metric'] = chart_data_melted['metric'].map(metric_names)

    # is_internally_listed dummy data for legend
    background_data = filtered_vacancy_df[filtered_vacancy_df['is_internally_listed']][['days_since_vacancy_start']]
    background_data['metric'] = 'Listing Window'
    background_data['count'] = None 
    listed_rent_data = filtered_vacancy_df[['days_since_vacancy_start']]
    listed_rent_data['metric'] = 'Listed Rent'
    listed_rent_data['count'] = None
    combined_data = pd.concat([chart_data_melted, background_data, listed_rent_data], ignore_index=True)

    # 2. metrics over vacancy line charts
    color_scale = alt.Scale(domain=['Inquiries', 'Tours', 'Applications', 'Listed Rent', 'Listing Window'], 
                            range=[LIGHT_PURPLE, PURPLE, DARK_PURPLE, TEAL, LIGHT_GRAY])
    metrics_chart = alt.Chart(combined_data).mark_line(point=True).encode(
        x=alt.X('days_since_vacancy_start:Q', title='Days Since Vacancy Start'),
        y=alt.Y('count:Q', title='Cumulative Count'),
        color=alt.Color('metric:N', scale=color_scale, title='Metric'),
        tooltip=[
            alt.Tooltip('days_since_vacancy_start:Q', title='Days Since Vacancy Start'),
            alt.Tooltip('metric:N', title='Metric'),
            alt.Tooltip('count:Q', title='Count')
        ]
    )

     # 3. most_recent_listed_rent line chart
    rent_chart = alt.Chart(filtered_vacancy_df).mark_line(point={'color': TEAL}, color=TEAL).encode(
        x=alt.X('days_since_vacancy_start:Q', title='Days Since Vacancy Start'),
        y=alt.Y('most_recent_listed_rent:Q', title='Most Recent Listed Rent'),
        tooltip=[
            alt.Tooltip('days_since_vacancy_start:Q', title='Days Since Start'),
            alt.Tooltip('most_recent_listed_rent:Q', title='Listed Rent')
        ]
    )
    
    st.subheader("Cumulative Metrics Over Vacancy")
    metrics_layer = alt.layer(background, metrics_chart)
    st.altair_chart(alt.layer(metrics_layer, rent_chart).resolve_scale(y='independent'), use_container_width=True)

