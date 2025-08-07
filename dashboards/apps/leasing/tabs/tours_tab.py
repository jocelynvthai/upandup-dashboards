import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from tabs.utils import LIGHT_GRAY, GRAY, TEAL, PURPLE


def tours_grouped(filtered_tours_df):
    # Overall aggregation
    grouped_tours_df = filtered_tours_df.groupby('date').agg(
        num_homes_listed=('tour_type', lambda x: x.isna().sum()),
        num_tours=('num_tours', 'sum'),
        num_tours_safe_mode=('num_tours', lambda x, df=filtered_tours_df: x[df['tour_type'] == 'safe_mode'].sum()),
        num_tours_doorman=('num_tours', lambda x, df=filtered_tours_df: x[df['tour_type'] != 'safe_mode'].sum()),
        num_id_verified=('num_identity_verified', 'sum'),
        num_prequalified=('num_prequalified', 'sum'),
        num_created_application=('num_applicants', 'sum'),
        num_paid_application_fee=('num_paid_applicants', 'sum'),
    )
    grouped_tours_df['avg_tours_per_home'] = grouped_tours_df['num_tours'] / grouped_tours_df['num_homes_listed']

    property_tours = filtered_tours_df.groupby(['date', 'address']).agg(
        total_tours_per_property=('num_tours', 'sum'), 
    ).reset_index()
    median_tours = property_tours.groupby('date').agg(
        median_tours_per_home=('total_tours_per_property', 'median')
    )
    zero_tours = property_tours.groupby('date').agg(
        num_homes_with_zero_tours=('total_tours_per_property', lambda x: (x == 0).sum())
    )

    grouped_tours_df = grouped_tours_df.merge(median_tours, left_on='date', right_index=True).merge(zero_tours, left_on='date', right_index=True)
    grouped_tours_df['perc_homes_with_zero_tours'] = grouped_tours_df['num_homes_with_zero_tours'] / grouped_tours_df['num_homes_listed']
    return grouped_tours_df


def tour_metrics(grouped_tours_df):
    st.dataframe(grouped_tours_df)

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1:
        st.metric("# Tours", f"{grouped_tours_df['num_tours'].sum()}")
    with col2:
        st.metric("# Tours (Doorman)", f"{grouped_tours_df['num_tours_doorman'].sum()}")
    with col3:
        st.metric("# Tours (Rently)", f"{grouped_tours_df['num_tours_safe_mode'].sum()}")
    with col4:
        st.metric("# ID Verified", f"{grouped_tours_df['num_id_verified'].sum()}")
        st.markdown(f"<small style='margin-top: -25px; display: block;'>{grouped_tours_df['num_id_verified'].sum() / grouped_tours_df['num_tours'].sum() * 100:.2f}% of tours</small>", unsafe_allow_html=True)
    with col5:
        st.metric("# Prequalified", f"{grouped_tours_df['num_prequalified'].sum()}")
        st.markdown(f"<small style='margin-top: -25px; display: block;'>{grouped_tours_df['num_prequalified'].sum() / grouped_tours_df['num_tours'].sum() * 100:.2f}% of tours</small>", unsafe_allow_html=True)
    with col6:
        st.metric("# Created Application", f"{grouped_tours_df['num_created_application'].sum()}")
        st.markdown(f"<small style='margin-top: -25px; display: block;'>{grouped_tours_df['num_created_application'].sum() / grouped_tours_df['num_tours'].sum() * 100:.2f}% of tours</small>", unsafe_allow_html=True)
    with col7:
        st.metric("# Paid Application Fee", f"{grouped_tours_df['num_paid_application_fee'].sum()}")
        st.markdown(f"<small style='margin-top: -25px; display: block;'>{grouped_tours_df['num_paid_application_fee'].sum() / grouped_tours_df['num_tours'].sum() * 100:.2f}% of tours</small>", unsafe_allow_html=True)

