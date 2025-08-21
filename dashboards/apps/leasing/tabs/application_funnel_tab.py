import streamlit as st
import pandas as pd
from tabs.utils import create_funnel_chart


def application_funnel_grouped(filtered_application_funnel_df):
    grouped_application_funnel_df = filtered_application_funnel_df.groupby('date').agg(
        total_num_created=('total_num_created_applications', 'sum'),
        total_num_submitted=('total_num_submitted_applications', 'sum'),
        total_num_paid_fees=('total_num_paid_applications', 'sum'),
        total_num_reviewed=('total_num_reviewed_applications', 'sum'),
        total_num_approved=('total_num_underwritten_applications', 'sum'),
        total_num_lease_creation=('total_num_lease_created_applications', 'sum'),
        total_num_initial_payments=('total_num_initial_payment_applications', 'sum'),
        total_num_completed=('total_num_completed_applications', 'sum'),
        total_hours_created_to_submitted=pd.NamedAgg(column='total_seconds_submitting_application', aggfunc=lambda x: x.sum() / 3600), 
        total_hours_submitted_to_paid_fees=pd.NamedAgg(column='total_seconds_paying_application_fee', aggfunc=lambda x: x.sum() / 3600), 
        total_hours_paid_fees_to_reviewed=pd.NamedAgg(column='total_seconds_reviewing_application', aggfunc=lambda x: x.sum() / 3600), 
        total_hours_reviewed_to_approved=pd.NamedAgg(column='total_seconds_underwriting_application', aggfunc=lambda x: x.sum() / 3600), 
        total_hours_approved_to_lease_creation=pd.NamedAgg(column='total_seconds_lease_creation', aggfunc=lambda x: x.sum() / 3600), 
        total_hours_lease_creation_to_initial_payments=pd.NamedAgg(column='total_seconds_applicant_signing', aggfunc=lambda x: x.sum() / 3600), 
        total_hours_initial_payments_to_completed=pd.NamedAgg(column='total_seconds_upandup_signing', aggfunc=lambda x: x.sum() / 3600), 
        ).reset_index()
     
    grouped_application_funnel_df['perc_created_to_submitted'] = grouped_application_funnel_df['total_num_submitted'] / grouped_application_funnel_df['total_num_created']
    grouped_application_funnel_df['perc_submitted_to_paid_fee'] = grouped_application_funnel_df['total_num_paid_fees'] / grouped_application_funnel_df['total_num_submitted']
    grouped_application_funnel_df['perc_paid_fee_to_reviewed'] = grouped_application_funnel_df['total_num_reviewed'] / grouped_application_funnel_df['total_num_paid_fees']
    grouped_application_funnel_df['perc_reviewed_to_approved'] = grouped_application_funnel_df['total_num_approved'] / grouped_application_funnel_df['total_num_reviewed']
    grouped_application_funnel_df['perc_approved_to_lease_creation'] = grouped_application_funnel_df['total_num_lease_creation'] / grouped_application_funnel_df['total_num_approved']
    grouped_application_funnel_df['perc_lease_creation_to_initial_payment'] = grouped_application_funnel_df['total_num_initial_payments'] / grouped_application_funnel_df['total_num_lease_creation']
    grouped_application_funnel_df['perc_initial_payment_to_completed'] = grouped_application_funnel_df['total_num_completed'] / grouped_application_funnel_df['total_num_initial_payments']
    
    grouped_application_funnel_df['avg_hours_created_to_submitted'] = grouped_application_funnel_df['total_hours_created_to_submitted'] / grouped_application_funnel_df['total_num_submitted']
    grouped_application_funnel_df['avg_hours_submitted_to_paid_fees'] = grouped_application_funnel_df['total_hours_submitted_to_paid_fees'] / grouped_application_funnel_df['total_num_paid_fees']
    grouped_application_funnel_df['avg_hours_paid_fees_to_reviewed'] = grouped_application_funnel_df['total_hours_paid_fees_to_reviewed'] / grouped_application_funnel_df['total_num_reviewed']
    grouped_application_funnel_df['avg_hours_reviewed_to_approved'] = grouped_application_funnel_df['total_hours_reviewed_to_approved'] / grouped_application_funnel_df['total_num_approved']
    grouped_application_funnel_df['avg_hours_approved_to_lease_creation'] = grouped_application_funnel_df['total_hours_approved_to_lease_creation'] / grouped_application_funnel_df['total_num_lease_creation']
    grouped_application_funnel_df['avg_hours_lease_creation_to_initial_payments'] = grouped_application_funnel_df['total_hours_lease_creation_to_initial_payments'] / grouped_application_funnel_df['total_num_initial_payments']
    grouped_application_funnel_df['avg_hours_initial_payments_to_completed'] = grouped_application_funnel_df['total_hours_initial_payments_to_completed'] / grouped_application_funnel_df['total_num_completed']
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
        'Total Count': [grouped_application_funnel_df['total_num_created'].sum(),
                        grouped_application_funnel_df['total_num_submitted'].sum(),
                        grouped_application_funnel_df['total_num_paid_fees'].sum(),
                        grouped_application_funnel_df['total_num_reviewed'].sum(),
                        grouped_application_funnel_df['total_num_approved'].sum(), 
                        grouped_application_funnel_df['total_num_lease_creation'].sum(), 
                        grouped_application_funnel_df['total_num_initial_payments'].sum(), 
                        grouped_application_funnel_df['total_num_completed'].sum()], 
        f'Average Count (per {selected_time_granularity})': [grouped_application_funnel_df['total_num_created'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_submitted'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_paid_fees'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_reviewed'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_approved'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_lease_creation'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_initial_payments'].mean().round(2),
                                                             grouped_application_funnel_df['total_num_completed'].mean().round(2)],
        'Conversion Rate from Previous Step': [None,
                                               f"{(grouped_application_funnel_df['total_num_submitted'].sum() / grouped_application_funnel_df['total_num_created'].sum() * 100).round(2)}%",
                                               f"{(grouped_application_funnel_df['total_num_paid_fees'].sum() / grouped_application_funnel_df['total_num_submitted'].sum() * 100).round(2)}%",
                                               f"{(grouped_application_funnel_df['total_num_reviewed'].sum() / grouped_application_funnel_df['total_num_paid_fees'].sum() * 100).round(2)}%",
                                               f"{(grouped_application_funnel_df['total_num_approved'].sum() / grouped_application_funnel_df['total_num_reviewed'].sum() * 100).round(2)}%",
                                               f"{(grouped_application_funnel_df['total_num_lease_creation'].sum() / grouped_application_funnel_df['total_num_approved'].sum() * 100).round(2)}%",
                                               f"{(grouped_application_funnel_df['total_num_initial_payments'].sum() / grouped_application_funnel_df['total_num_lease_creation'].sum() * 100).round(2)}%",
                                               f"{(grouped_application_funnel_df['total_num_completed'].sum() / grouped_application_funnel_df['total_num_initial_payments'].sum() * 100).round(2)}%"],
        'Average Time Spent (hours)': [(grouped_application_funnel_df['total_hours_created_to_submitted'].sum() / grouped_application_funnel_df['total_num_submitted'].sum()).round(2),
                                       (grouped_application_funnel_df['total_hours_submitted_to_paid_fees'].sum() / grouped_application_funnel_df['total_num_paid_fees'].sum()).round(2),
                                       (grouped_application_funnel_df['total_hours_paid_fees_to_reviewed'].sum() / grouped_application_funnel_df['total_num_reviewed'].sum()).round(2),
                                       (grouped_application_funnel_df['total_hours_reviewed_to_approved'].sum() / grouped_application_funnel_df['total_num_approved'].sum()).round(2),
                                       (grouped_application_funnel_df['total_hours_approved_to_lease_creation'].sum() / grouped_application_funnel_df['total_num_lease_creation'].sum()).round(2),
                                       (grouped_application_funnel_df['total_hours_lease_creation_to_initial_payments'].sum() / grouped_application_funnel_df['total_num_initial_payments'].sum()).round(2),
                                       (grouped_application_funnel_df['total_hours_initial_payments_to_completed'].sum() / grouped_application_funnel_df['total_num_completed'].sum()).round(2), 
                                       None],
        'Survivorship Rate': [f"{(grouped_application_funnel_df['total_num_created'].sum() / grouped_application_funnel_df['total_num_created'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_submitted'].sum() / grouped_application_funnel_df['total_num_created'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_paid_fees'].sum() / grouped_application_funnel_df['total_num_created'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_reviewed'].sum() / grouped_application_funnel_df['total_num_created'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_approved'].sum() / grouped_application_funnel_df['total_num_created'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_lease_creation'].sum() / grouped_application_funnel_df['total_num_created'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_initial_payments'].sum() / grouped_application_funnel_df['total_num_created'].sum() * 100).round(2)}%",
                              f"{(grouped_application_funnel_df['total_num_completed'].sum() / grouped_application_funnel_df['total_num_created'].sum() * 100).round(2)}%"],
    }
    summary_metrics_df = pd.DataFrame(summary_data)
    st.dataframe(summary_metrics_df)    



def application_funnel_chart(grouped_application_funnel_df):
    st.subheader("Application Funnel")
    
    # Define funnel stages
    funnel_stages = ['Created', 'Submitted', 'Paid Fees', 'Reviewed', 'Approved', 'Lease Created', 'Initial Payments', 'Completed']
    
    first_stage_col, second_stage_col = st.columns(2)
    with first_stage_col:
        first_stage = st.selectbox("Select First Funnel Stage", options=funnel_stages[:-1], key='application_first_funnel_stage')
        first_stage_index = funnel_stages.index(first_stage)
    with second_stage_col:
        second_stage = st.selectbox("Select Second Funnel Stage", options=funnel_stages[first_stage_index + 1:], key='application_second_funnel_stage', index=0)

    create_funnel_chart(grouped_application_funnel_df.copy(), funnel_stages, first_stage, second_stage, "hours")

