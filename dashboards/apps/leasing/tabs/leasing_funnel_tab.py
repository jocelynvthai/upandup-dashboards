import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

def leasing_funnel_filters(leasing_funnel_df):
    col_date_range, col_time_granularity, col_fund, col_market = st.columns(4)
    filtered_leasing_funnel_df = leasing_funnel_df.copy()

    with col_date_range:
        date_range = st.date_input("Pick a period range",
                                   value=(datetime.now() - timedelta(days=1),  datetime.now()),
                                   format='MM/DD/YYYY',
                                   key='leasing_funnel_date_range')
        if len(date_range) != 2:
            st.stop()
        else:
            start_date, end_date = date_range[0], date_range[1]
            filtered_leasing_funnel_df = filtered_leasing_funnel_df[(filtered_leasing_funnel_df['date'] <= end_date) &
                                                                        (filtered_leasing_funnel_df['date'] >= start_date)]

    with col_time_granularity:
        available_granularities = filtered_leasing_funnel_df['time_granularity'].unique()
        selected_time_granularity = st.selectbox("Select a time granularity",
                                      options=[g for g in ['day', 'week', 'month', 'quarter', 'year'] if g in available_granularities], 
                                      index=0, 
                                      key='leasing_funnel_time_granularity')
        filtered_leasing_funnel_df = filtered_leasing_funnel_df[filtered_leasing_funnel_df['time_granularity'] == selected_time_granularity]

    with col_fund:
        selected_fund = st.selectbox("Select a fund",
                                     options=['All'] + list(filtered_leasing_funnel_df['fund'].unique()), 
                                     index=0,
                                     key='leasing_funnel_fund')
        if selected_fund != 'All':
            filtered_leasing_funnel_df = filtered_leasing_funnel_df[filtered_leasing_funnel_df['fund'] == selected_fund]

    with col_market:
        selected_market = st.selectbox("Select a market",
                                       options=['All'] + list(filtered_leasing_funnel_df['market'].unique()), 
                                       index=0,
                                       key='leasing_funnel_market')
        if selected_market != 'All':
            filtered_leasing_funnel_df = filtered_leasing_funnel_df[filtered_leasing_funnel_df['market'] == selected_market]

    return filtered_leasing_funnel_df, selected_time_granularity



def leasing_funnel_grouped(filtered_leasing_funnel_df):
    grouped_leasing_funnel_df = filtered_leasing_funnel_df.groupby('date').agg(
        homes_listed=('num_homes_listed', 'sum'),
        days_listed=('num_days_listed', 'sum'),
        total_num_leads=('total_num_leads', 'sum'),
        total_num_paid_applicants=('total_num_paid_applicants', 'sum'),
        total_num_approved_applicants=('total_num_approved_applicants', 'sum'),
        total_num_initial_payments=('total_num_initial_payments', 'sum'),
        total_num_deals=('total_num_deals', 'sum'), 
        total_num_days_lead_to_paid_applicant=pd.NamedAgg(column='total_seconds_converting_to_application', aggfunc=lambda x: x.sum() / 86400),
        total_num_days_paid_applicant_to_approved_applicant=pd.NamedAgg(column='total_seconds_reviewing_underwriting_application', aggfunc=lambda x: x.sum() / 86400),
        total_num_days_approved_applicant_to_initial_payment=pd.NamedAgg(column='total_seconds_lease_creation_and_applicant_signing', aggfunc=lambda x: x.sum() / 86400),
        total_num_days_initial_payment_to_deal=pd.NamedAgg(column='total_seconds_upandup_signing', aggfunc=lambda x: x.sum() / 86400),
        ).reset_index()
    grouped_leasing_funnel_df['perc_leads_to_paid_applicants'] = grouped_leasing_funnel_df['total_num_paid_applicants'] / grouped_leasing_funnel_df['total_num_leads']
    grouped_leasing_funnel_df['perc_paid_applicants_to_approved_applicants'] = grouped_leasing_funnel_df['total_num_approved_applicants'] / grouped_leasing_funnel_df['total_num_paid_applicants']
    grouped_leasing_funnel_df['perc_approved_applicants_to_initial_payment'] = grouped_leasing_funnel_df['total_num_initial_payments'] / grouped_leasing_funnel_df['total_num_approved_applicants']
    grouped_leasing_funnel_df['perc_initial_payment_to_deal'] = grouped_leasing_funnel_df['total_num_deals'] / grouped_leasing_funnel_df['total_num_initial_payments']
    grouped_leasing_funnel_df['perc_lead_to_deal'] = grouped_leasing_funnel_df['total_num_deals'] / grouped_leasing_funnel_df['total_num_leads']
    grouped_leasing_funnel_df['avg_days_leads_to_paid_applicants'] = grouped_leasing_funnel_df['total_num_days_lead_to_paid_applicant'] / grouped_leasing_funnel_df['total_num_paid_applicants']
    grouped_leasing_funnel_df['avg_days_paid_applicants_to_approved_applicants'] = grouped_leasing_funnel_df['total_num_days_paid_applicant_to_approved_applicant'] / grouped_leasing_funnel_df['total_num_approved_applicants']
    grouped_leasing_funnel_df['avg_days_approved_applicants_to_initial_payment'] = grouped_leasing_funnel_df['total_num_days_approved_applicant_to_initial_payment'] / grouped_leasing_funnel_df['total_num_initial_payments']
    grouped_leasing_funnel_df['avg_days_initial_payment_to_deal'] = grouped_leasing_funnel_df['total_num_days_initial_payment_to_deal'] / grouped_leasing_funnel_df['total_num_deals']
    grouped_leasing_funnel_df['avg_days_lead_to_deal'] = (grouped_leasing_funnel_df['total_num_days_lead_to_paid_applicant'] + 
                                                          grouped_leasing_funnel_df['total_num_days_paid_applicant_to_approved_applicant'] +
                                                          grouped_leasing_funnel_df['total_num_days_approved_applicant_to_initial_payment'] +
                                                          grouped_leasing_funnel_df['total_num_days_initial_payment_to_deal']) / grouped_leasing_funnel_df['total_num_deals']
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
        'Average Time Spent (days)': [(grouped_leasing_funnel_df['total_num_days_lead_to_paid_applicant'].sum() / grouped_leasing_funnel_df['total_num_paid_applicants'].sum()).round(2),
                                      (grouped_leasing_funnel_df['total_num_days_paid_applicant_to_approved_applicant'].sum() / grouped_leasing_funnel_df['total_num_approved_applicants'].sum()).round(2),
                                      (grouped_leasing_funnel_df['total_num_days_approved_applicant_to_initial_payment'].sum() / grouped_leasing_funnel_df['total_num_initial_payments'].sum()).round(2),
                                      (grouped_leasing_funnel_df['total_num_days_initial_payment_to_deal'].sum() / grouped_leasing_funnel_df['total_num_deals'].sum()).round(2), 
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
    
    # Define consistent colors
    FIRST_BAR_COLOR = "#808080"  # gray
    SECOND_BAR_COLOR = "#15b8a6"  # teal
    LINE_COLOR = "#9575cd"  # purple
    
    # Define the funnel stages configuration
    funnel_stages = {
        "Leads to Paid Applicants": {
            "first_metric": "total_num_leads",
            "second_metric": "total_num_paid_applicants",
            "percentage": "perc_leads_to_paid_applicants",
            "avg_days": "avg_days_leads_to_paid_applicants",
            "first_label": "Total Leads",
            "second_label": "Paid Applicants"
        },
        "Paid Applicants to Approved Applicants": {
            "first_metric": "total_num_paid_applicants",
            "second_metric": "total_num_approved_applicants",
            "percentage": "perc_paid_applicants_to_approved_applicants",
            "avg_days": "avg_days_paid_applicants_to_approved_applicants",
            "first_label": "Paid Applicants",
            "second_label": "Approved Applicants"
        },
        "Approved Applicants to Initial Payment": {
            "first_metric": "total_num_approved_applicants",
            "second_metric": "total_num_initial_payments",
            "percentage": "perc_approved_applicants_to_initial_payment",
            "avg_days": "avg_days_approved_applicants_to_initial_payment",
            "first_label": "Approved Applicants",
            "second_label": "Initial Payments"
        },
        "Initial Payment to Deal": {
            "first_metric": "total_num_initial_payments",
            "second_metric": "total_num_deals",
            "percentage": "perc_initial_payment_to_deal",
            "avg_days": "avg_days_initial_payment_to_deal",
            "first_label": "Initial Payments",
            "second_label": "Deals"
        },
        "Lead to Deal": {
            "first_metric": "total_num_leads",
            "second_metric": "total_num_deals",
            "percentage": "perc_lead_to_deal",
            "avg_days": "avg_days_lead_to_deal",
            "first_label": "Total Leads",
            "second_label": "Deals"
        }
    }

    # Add stage selector
    selected_stage = st.selectbox("Select Funnel Stage", options=list(funnel_stages.keys()), key='leasing_funnel_stage')
    stage_config = funnel_stages[selected_stage]
    
    # First bar chart
    first_bars = alt.Chart(grouped_leasing_funnel_df).mark_bar().encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y(f"{stage_config['first_metric']}:Q", 
                title='Count',
                axis=alt.Axis(titleColor=FIRST_BAR_COLOR)),
        color=alt.value(FIRST_BAR_COLOR),
        tooltip=[
            alt.Tooltip('date:T'),
            alt.Tooltip(f"{stage_config['first_metric']}:Q", 
                       title=stage_config['first_label'], 
                       format=',.0f'),
            alt.Tooltip(f"{stage_config['percentage']}:Q", 
                       format='.1%', 
                       title='Conversion Rate')
        ]
    )

    # Second bar chart
    second_bars = alt.Chart(grouped_leasing_funnel_df).mark_bar().encode(
        x=alt.X('date:T'),
        y=alt.Y(f"{stage_config['second_metric']}:Q"),
        color=alt.value(SECOND_BAR_COLOR),
        tooltip=[
            alt.Tooltip('date:T'),
            alt.Tooltip(f"{stage_config['second_metric']}:Q", 
                       title=stage_config['second_label'], 
                       format=',.0f'),
            alt.Tooltip(f"{stage_config['percentage']}:Q", 
                       format='.1%', 
                       title='Conversion Rate')
        ]
    )

    # Conversion rate text
    text = alt.Chart(grouped_leasing_funnel_df).mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    ).encode(
        x=alt.X('date:T'),
        y=alt.Y(f"{stage_config['first_metric']}:Q"),
        text=alt.Text(f"{stage_config['percentage']}:Q", format='.0%'),
        opacity=alt.condition(
            f'isValid(datum.{stage_config["percentage"]})',
            alt.value(1),
            alt.value(0)
        )
    )

    # Average days line
    line = alt.Chart(grouped_leasing_funnel_df).mark_line(
        color=LINE_COLOR,
        strokeWidth=2
    ).encode(
        x=alt.X('date:T'),
        y=alt.Y(f"{stage_config['avg_days']}:Q",
                title=f"Average Days",
                axis=alt.Axis(titleColor=LINE_COLOR)),
        tooltip=[
            alt.Tooltip('date:T'),
            alt.Tooltip(f"{stage_config['avg_days']}:Q", 
                       format=',.1f', 
                       title='Avg Days')
        ]
    )

    # Layer the charts
    bars_layer = alt.layer(first_bars, second_bars, text).properties(
        width=800,
        height=400,
        title=selected_stage
    )
    
    chart = alt.layer(bars_layer, line).resolve_scale(
        y='independent'
    )

    st.altair_chart(chart, use_container_width=True)
    st.dataframe(grouped_leasing_funnel_df)
    

