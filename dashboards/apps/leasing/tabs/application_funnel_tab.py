import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from .utils import create_funnel_chart

def application_funnel_filters(application_funnel_df):
    col_date_range, col_time_granularity, col_fund, col_market = st.columns(4)
    filtered_application_funnel_df = application_funnel_df.copy()

    with col_date_range:
        date_range = st.date_input("Pick a period range",
                                   value=(datetime.now() - timedelta(days=1),  datetime.now()),
                                   format='MM/DD/YYYY',
                                   key='application_funnel_date_range')
        if len(date_range) != 2:
            st.stop()
        else:
            start_date, end_date = date_range[0], date_range[1]
            filtered_application_funnel_df = filtered_application_funnel_df[(filtered_application_funnel_df['date'] <= end_date) &
                                                                        (filtered_application_funnel_df['date'] >= start_date)]

    with col_time_granularity:
        available_granularities = filtered_application_funnel_df['time_granularity'].unique()
        selected_time_granularity = st.selectbox("Select a time granularity",
                                      options=[g for g in ['day', 'week', 'month', 'quarter', 'year'] if g in available_granularities], 
                                      index=0, 
                                      key='application_funnel_time_granularity')
        filtered_application_funnel_df = filtered_application_funnel_df[filtered_application_funnel_df['time_granularity'] == selected_time_granularity]

    with col_fund:
        selected_fund = st.selectbox("Select a fund", 
                                     options=['All'] + list(filtered_application_funnel_df['fund'].unique()), 
                                     index=0, 
                                     key='application_funnel_fund')
        if selected_fund != 'All':
            filtered_application_funnel_df = filtered_application_funnel_df[filtered_application_funnel_df['fund'] == selected_fund]

    with col_market:
        selected_market = st.selectbox("Select a market",
                                       options=['All'] + list(filtered_application_funnel_df['market'].unique()), 
                                       index=0,
                                       key='application_funnel_market')
        if selected_market != 'All':
            filtered_application_funnel_df = filtered_application_funnel_df[filtered_application_funnel_df['market'] == selected_market]

    return filtered_application_funnel_df, selected_time_granularity


def application_funnel_grouped(filtered_application_funnel_df):
    grouped_application_funnel_df = filtered_application_funnel_df.groupby('date').agg(
        total_num_applications=('total_num_created_applications', 'sum'),
        total_num_submitted_applications=('total_num_submitted_applications', 'sum'),
        total_num_application_fees=('total_num_paid_applications', 'sum'),
        total_num_reviewed_applications=('total_num_reviewed_applications', 'sum'),
        total_num_approved_applications=('total_num_underwritten_applications', 'sum'),
        total_num_lease_created=('total_num_lease_created_applications', 'sum'),
        total_num_initial_payments=('total_num_initial_payment_applications', 'sum'),
        total_num_completed_applications=('total_num_completed_applications', 'sum'),
        total_hours_created_to_submitted=pd.NamedAgg(column='total_seconds_submitting_application', aggfunc=lambda x: x.sum() / 3600), 
        total_hours_submitted_to_paid_fee=pd.NamedAgg(column='total_seconds_paying_application_fee', aggfunc=lambda x: x.sum() / 3600), 
        total_hours_paid_fee_to_reviewed=pd.NamedAgg(column='total_seconds_reviewing_application', aggfunc=lambda x: x.sum() / 3600), 
        total_hours_reviewed_to_approved=pd.NamedAgg(column='total_seconds_underwriting_application', aggfunc=lambda x: x.sum() / 3600), 
        total_hours_approved_to_lease_creation=pd.NamedAgg(column='total_seconds_lease_creation', aggfunc=lambda x: x.sum() / 3600), 
        total_hours_lease_creation_to_initial_payment=pd.NamedAgg(column='total_seconds_applicant_signing', aggfunc=lambda x: x.sum() / 3600), 
        total_hours_initial_payment_to_completed=pd.NamedAgg(column='total_seconds_upandup_signing', aggfunc=lambda x: x.sum() / 3600), 
        ).reset_index()
     
    grouped_application_funnel_df['perc_created_to_submitted'] = grouped_application_funnel_df['total_num_submitted_applications'] / grouped_application_funnel_df['total_num_applications']
    grouped_application_funnel_df['perc_submitted_to_paid_fee'] = grouped_application_funnel_df['total_num_application_fees'] / grouped_application_funnel_df['total_num_submitted_applications']
    grouped_application_funnel_df['perc_paid_fee_to_reviewed'] = grouped_application_funnel_df['total_num_reviewed_applications'] / grouped_application_funnel_df['total_num_application_fees']
    grouped_application_funnel_df['perc_reviewed_to_approved'] = grouped_application_funnel_df['total_num_approved_applications'] / grouped_application_funnel_df['total_num_reviewed_applications']
    grouped_application_funnel_df['perc_approved_to_lease_creation'] = grouped_application_funnel_df['total_num_lease_created'] / grouped_application_funnel_df['total_num_approved_applications']
    grouped_application_funnel_df['perc_lease_creation_to_initial_payment'] = grouped_application_funnel_df['total_num_initial_payments'] / grouped_application_funnel_df['total_num_lease_created']
    grouped_application_funnel_df['perc_initial_payment_to_completed'] = grouped_application_funnel_df['total_num_completed_applications'] / grouped_application_funnel_df['total_num_initial_payments']
    
    grouped_application_funnel_df['avg_hours_created_to_submitted'] = grouped_application_funnel_df['total_hours_created_to_submitted'] / grouped_application_funnel_df['total_num_submitted_applications']
    grouped_application_funnel_df['avg_hours_submitted_to_paid_fee'] = grouped_application_funnel_df['total_hours_submitted_to_paid_fee'] / grouped_application_funnel_df['total_num_application_fees']
    grouped_application_funnel_df['avg_hours_paid_fee_to_reviewed'] = grouped_application_funnel_df['total_hours_paid_fee_to_reviewed'] / grouped_application_funnel_df['total_num_reviewed_applications']
    grouped_application_funnel_df['avg_hours_reviewed_to_approved'] = grouped_application_funnel_df['total_hours_reviewed_to_approved'] / grouped_application_funnel_df['total_num_approved_applications']
    grouped_application_funnel_df['avg_hours_approved_to_lease_creation'] = grouped_application_funnel_df['total_hours_approved_to_lease_creation'] / grouped_application_funnel_df['total_num_lease_created']
    grouped_application_funnel_df['avg_hours_lease_creation_to_initial_payment'] = grouped_application_funnel_df['total_hours_lease_creation_to_initial_payment'] / grouped_application_funnel_df['total_num_initial_payments']
    grouped_application_funnel_df['avg_hours_initial_payment_to_completed'] = grouped_application_funnel_df['total_hours_initial_payment_to_completed'] / grouped_application_funnel_df['total_num_completed_applications']
    return grouped_application_funnel_df


def application_funnel_summary_metrics(grouped_application_funnel_df, selected_time_granularity):
    st.subheader("Summary Metrics")
    summary_data = {
        'Funnel Stage': ['Created', 'Submitted', 'Paid Fee', 'Reviewed', 'Approved', 'Lease Created', 'Initial Payment', 'Completed'],
        'Definition': ['User clicks "Get Started" and creates an application',
                       'User submits all initial application data ',
                       'User pays $20 application fee',
                       'Up&Up (Issa) did initial review of application',
                       'Up&Up (Serra) underwrote and approved application',
                       'Up&Up (Thomas) created lease',
                       'User signed lease & made $500 initial payment',
                       'Up&Up countersigned lease'], 
        'Total Count': [grouped_application_funnel_df['total_num_applications'].sum(),
                        grouped_application_funnel_df['total_num_submitted_applications'].sum(),
                        grouped_application_funnel_df['total_num_application_fees'].sum(),
                        grouped_application_funnel_df['total_num_reviewed_applications'].sum(),
                        grouped_application_funnel_df['total_num_approved_applications'].sum(), 
                        grouped_application_funnel_df['total_num_lease_created'].sum(), 
                        grouped_application_funnel_df['total_num_initial_payments'].sum(), 
                        grouped_application_funnel_df['total_num_completed_applications'].sum()], 
        f'Average Count (per {selected_time_granularity})': [grouped_application_funnel_df['total_num_applications'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_submitted_applications'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_application_fees'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_reviewed_applications'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_approved_applications'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_lease_created'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_initial_payments'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_completed_applications'].mean().round(2)],
        'Conversion Rate from Previous Step': [None,
                                               f"{(grouped_application_funnel_df['total_num_submitted_applications'].sum() / grouped_application_funnel_df['total_num_applications'].sum() * 100).round(2)}%",
                                               f"{(grouped_application_funnel_df['total_num_application_fees'].sum() / grouped_application_funnel_df['total_num_submitted_applications'].sum() * 100).round(2)}%",
                                               f"{(grouped_application_funnel_df['total_num_reviewed_applications'].sum() / grouped_application_funnel_df['total_num_application_fees'].sum() * 100).round(2)}%",
                                               f"{(grouped_application_funnel_df['total_num_approved_applications'].sum() / grouped_application_funnel_df['total_num_reviewed_applications'].sum() * 100).round(2)}%",
                                               f"{(grouped_application_funnel_df['total_num_lease_created'].sum() / grouped_application_funnel_df['total_num_approved_applications'].sum() * 100).round(2)}%",
                                               f"{(grouped_application_funnel_df['total_num_initial_payments'].sum() / grouped_application_funnel_df['total_num_lease_created'].sum() * 100).round(2)}%",
                                               f"{(grouped_application_funnel_df['total_num_completed_applications'].sum() / grouped_application_funnel_df['total_num_initial_payments'].sum() * 100).round(2)}%"],
        'Average Time Spent (hours)': [(grouped_application_funnel_df['total_hours_created_to_submitted'].sum() / grouped_application_funnel_df['total_num_submitted_applications'].sum()).round(2),
                                       (grouped_application_funnel_df['total_hours_submitted_to_paid_fee'].sum() / grouped_application_funnel_df['total_num_application_fees'].sum()).round(2),
                                       (grouped_application_funnel_df['total_hours_paid_fee_to_reviewed'].sum() / grouped_application_funnel_df['total_num_reviewed_applications'].sum()).round(2),
                                       (grouped_application_funnel_df['total_hours_reviewed_to_approved'].sum() / grouped_application_funnel_df['total_num_approved_applications'].sum()).round(2),
                                       (grouped_application_funnel_df['total_hours_approved_to_lease_creation'].sum() / grouped_application_funnel_df['total_num_lease_created'].sum()).round(2),
                                       (grouped_application_funnel_df['total_hours_lease_creation_to_initial_payment'].sum() / grouped_application_funnel_df['total_num_initial_payments'].sum()).round(2),
                                       (grouped_application_funnel_df['total_hours_initial_payment_to_completed'].sum() / grouped_application_funnel_df['total_num_completed_applications'].sum()).round(2), 
                                       None],
        'Survivorship Rate': [f"{(grouped_application_funnel_df['total_num_applications'].sum() / grouped_application_funnel_df['total_num_applications'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_submitted_applications'].sum() / grouped_application_funnel_df['total_num_applications'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_application_fees'].sum() / grouped_application_funnel_df['total_num_applications'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_reviewed_applications'].sum() / grouped_application_funnel_df['total_num_applications'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_approved_applications'].sum() / grouped_application_funnel_df['total_num_applications'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_lease_created'].sum() / grouped_application_funnel_df['total_num_applications'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_initial_payments'].sum() / grouped_application_funnel_df['total_num_applications'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_completed_applications'].sum() / grouped_application_funnel_df['total_num_applications'].sum() * 100).round(2)}%"],
    }
    summary_metrics_df = pd.DataFrame(summary_data)
    st.dataframe(summary_metrics_df)    



def application_funnel_chart(grouped_application_funnel_df):
    st.subheader("Application Funnel")
    funnel_stages = {
        "Created to Submitted": {
            "first_metric": "total_num_applications",
            "second_metric": "total_num_submitted_applications",
            "percentage": "perc_created_to_submitted",
            "avg_hours": "avg_hours_created_to_submitted",
            "first_label": "Created Applications",
            "second_label": "Submitted Applications"
        },
        "Submitted to Paid Fee": {
            "first_metric": "total_num_submitted_applications",
            "second_metric": "total_num_application_fees",
            "percentage": "perc_submitted_to_paid_fee",
            "avg_hours": "avg_hours_submitted_to_paid_fee",
            "first_label": "Submitted Applications",
            "second_label": "Paid Applications"
        },
        "Paid Fee to Reviewed": {
            "first_metric": "total_num_application_fees",
            "second_metric": "total_num_reviewed_applications",
            "percentage": "perc_paid_fee_to_reviewed",
            "avg_hours": "avg_hours_paid_fee_to_reviewed",
            "first_label": "Paid Applications",
            "second_label": "Reviewed Applications"
        },
        "Reviewed to Approved": {
            "first_metric": "total_num_reviewed_applications",
            "second_metric": "total_num_approved_applications",
            "percentage": "perc_reviewed_to_approved",
            "avg_hours": "avg_hours_reviewed_to_approved",
            "first_label": "Reviewed Applications",
            "second_label": "Approved Applications"
        },
        "Approved to Lease Created": {
            "first_metric": "total_num_approved_applications",
            "second_metric": "total_num_lease_created",
            "percentage": "perc_approved_to_lease_creation",
            "avg_hours": "avg_hours_approved_to_lease_creation",
            "first_label": "Approved Applications",
            "second_label": "Lease Created"
        },
        "Lease Created to Initial Payment": {
            "first_metric": "total_num_lease_created",
            "second_metric": "total_num_initial_payments",
            "percentage": "perc_lease_creation_to_initial_payment",
            "avg_hours": "avg_hours_lease_creation_to_initial_payment",
            "first_label": "Lease Created",
            "second_label": "Initial Payment Made"
        },
        "Initial Payment to Completed": {
            "first_metric": "total_num_initial_payments",
            "second_metric": "total_num_completed_applications",
            "percentage": "perc_initial_payment_to_completed",
            "avg_hours": "avg_hours_initial_payment_to_completed",
            "first_label": "Initial Payment Made",
            "second_label": "Completed Applications"
        }
    }
    create_funnel_chart(grouped_application_funnel_df, funnel_stages, "application")