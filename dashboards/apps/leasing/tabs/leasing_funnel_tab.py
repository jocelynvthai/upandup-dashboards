import streamlit as st
import pandas as pd
from tabs.utils import create_funnel_chart
import altair as alt


def leasing_funnel_prelease(leasing_funnel_df):
    prelease = st.toggle("Pre-lease")
    if prelease:
        filtered_leasing_funnel_df = leasing_funnel_df[leasing_funnel_df['is_pre_lease'] == 'Yes']
    else:
        filtered_leasing_funnel_df = leasing_funnel_df[leasing_funnel_df['is_pre_lease'] == 'No']
    return filtered_leasing_funnel_df

def leasing_funnel_grouped(filtered_leasing_funnel_df):
    grouped_leasing_funnel_df = filtered_leasing_funnel_df.groupby('date').agg(
        homes_listed=('num_homes_listed', 'sum'),
        days_listed=('num_days_listed', 'sum'),
        total_num_leads=('total_num_leads', 'sum'),
        total_num_paid_applicants=('total_num_paid_applicants', 'sum'),
        total_num_approved_applicants=('total_num_approved_applicants', 'sum'),
        total_num_initial_payments=('total_num_initial_payments', 'sum'),
        total_num_deals=('total_num_deals', 'sum'), 
        total_days_leads_to_paid_applicants=pd.NamedAgg(column='total_seconds_converting_to_application', aggfunc=lambda x: x.sum() / 86400),
        total_days_paid_applicants_to_approved_applicants=pd.NamedAgg(column='total_seconds_reviewing_underwriting_application', aggfunc=lambda x: x.sum() / 86400),
        total_days_approved_applicants_to_initial_payments=pd.NamedAgg(column='total_seconds_lease_creation_and_applicant_signing', aggfunc=lambda x: x.sum() / 86400),
        total_days_initial_payments_to_deals=pd.NamedAgg(column='total_seconds_upandup_signing', aggfunc=lambda x: x.sum() / 86400),
        ).reset_index()

    return grouped_leasing_funnel_df


def leasing_funnel_summary_metrics(grouped_leasing_funnel_df, selected_time_granularity):
    st.subheader("Summary Metrics")
    summary_data = {
        'Funnel Stage': ['Lead', 'Paid Applicant', 'Approved Applicant', 'Initial Payment', 'Deal'],
        'Definition': ['User created in Hudson',
                       'User created an application & paid application fee',
                       'Up&Up reviewed, underwrote, and approved application',
                       'User signed lease & made $500 initial payment',
                       'Up&Up countersigned lease'],
        'Total Count': [grouped_leasing_funnel_df['total_num_leads'].sum(),
                        grouped_leasing_funnel_df['total_num_paid_applicants'].sum(),
                        grouped_leasing_funnel_df['total_num_approved_applicants'].sum(),
                        grouped_leasing_funnel_df['total_num_initial_payments'].sum(),
                        grouped_leasing_funnel_df['total_num_deals'].sum()], 
        f'Average Count (per {selected_time_granularity})': [grouped_leasing_funnel_df['total_num_leads'].mean().round(2),
                                                             grouped_leasing_funnel_df['total_num_paid_applicants'].mean().round(2),
                                                             grouped_leasing_funnel_df['total_num_approved_applicants'].mean().round(2),
                                                             grouped_leasing_funnel_df['total_num_initial_payments'].mean().round(2),
                                                             grouped_leasing_funnel_df['total_num_deals'].mean().round(2)],
        'Conversion Rate from Previous Step': [None,
                                               f"{(grouped_leasing_funnel_df['total_num_paid_applicants'].sum() / grouped_leasing_funnel_df['total_num_leads'].sum() * 100).round(2)}%",
                                               f"{(grouped_leasing_funnel_df['total_num_approved_applicants'].sum() / grouped_leasing_funnel_df['total_num_paid_applicants'].sum() * 100).round(2)}%",
                                               f"{(grouped_leasing_funnel_df['total_num_initial_payments'].sum() / grouped_leasing_funnel_df['total_num_approved_applicants'].sum() * 100).round(2)}%",
                                               f"{(grouped_leasing_funnel_df['total_num_deals'].sum() / grouped_leasing_funnel_df['total_num_initial_payments'].sum() * 100).round(2)}%"], 
        'Average Time Spent (days)': [(grouped_leasing_funnel_df['total_days_leads_to_paid_applicants'].sum() / grouped_leasing_funnel_df['total_num_paid_applicants'].sum()).round(2),
                                      (grouped_leasing_funnel_df['total_days_paid_applicants_to_approved_applicants'].sum() / grouped_leasing_funnel_df['total_num_approved_applicants'].sum()).round(2),
                                      (grouped_leasing_funnel_df['total_days_approved_applicants_to_initial_payments'].sum() / grouped_leasing_funnel_df['total_num_initial_payments'].sum()).round(2),
                                      (grouped_leasing_funnel_df['total_days_initial_payments_to_deals'].sum() / grouped_leasing_funnel_df['total_num_deals'].sum()).round(2), 
                                      None], 
        'Survivorship Rate': [f"{(grouped_leasing_funnel_df['total_num_leads'].sum() / grouped_leasing_funnel_df['total_num_leads'].sum() * 100).round(2)}%",
                             f"{(grouped_leasing_funnel_df['total_num_paid_applicants'].sum() / grouped_leasing_funnel_df['total_num_leads'].sum() * 100).round(2)}%",
                             f"{(grouped_leasing_funnel_df['total_num_approved_applicants'].sum() / grouped_leasing_funnel_df['total_num_leads'].sum() * 100).round(2)}%",
                             f"{(grouped_leasing_funnel_df['total_num_initial_payments'].sum() / grouped_leasing_funnel_df['total_num_leads'].sum() * 100).round(2)}%",
                             f"{(grouped_leasing_funnel_df['total_num_deals'].sum() / grouped_leasing_funnel_df['total_num_leads'].sum() * 100).round(2)}%"]
    }
    summary_metrics_df = pd.DataFrame(summary_data)
    st.dataframe(summary_metrics_df)
    


def leasing_funnel_chart(grouped_leasing_funnel_df):
    st.subheader("Leasing Funnel")
    
    # Define funnel stages
    funnel_stages = ['Leads', 'Paid Applicants', 'Approved Applicants', 'Initial Payments', 'Deals']
    
    col_first_stage, col_second_stage = st.columns(2)
    with col_first_stage:
        first_stage = st.selectbox("Select First Funnel Stage", options=funnel_stages[:-1], key='leasing_first_funnel_stage')
        first_stage_index = funnel_stages.index(first_stage)
    with col_second_stage:
        second_stage = st.selectbox("Select Second Funnel Stage", options=funnel_stages[first_stage_index + 1:], key='leasing_second_funnel_stage', index=0)

    create_funnel_chart(grouped_leasing_funnel_df.copy(), funnel_stages, first_stage, second_stage, "days")



    

