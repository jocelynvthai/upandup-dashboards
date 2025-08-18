import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info, leasing_scraper_data, rental_applications_data, raw_inquiries_data, leasing_funnel_data, inquiries_data, tours_data, vacancy_data, distinct_vacancy_data
from tabs.utils import filters
from tabs.competitors_tab import metrics, competitors_filters, clearance_rates, rent_changes, turn_times
from tabs.summary_tab import summary_filters, summary_metrics
from tabs.leasing_funnel_tab import leasing_funnel_grouped, leasing_funnel_summary_metrics, leasing_funnel_chart
from tabs.application_funnel_tab import application_funnel_grouped, application_funnel_summary_metrics, application_funnel_chart
from tabs.inquiries_tab import inquiries_grouped, num_inquiries, inquiries_filled_out_prequalification_form, inquiries_prequalified, homes_with_zero_inquiries
from tabs.tours_tab import tours_grouped, tour_metrics, num_tours_by_source, num_tours_by_farthest_funnel_stage, homes_with_zero_tours
from tabs.vacancy_tab import vacancy_filters, vacancy_curve

# Configure page layout
st.set_page_config(
    page_title="Leasing Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info())
leasing_df = leasing_scraper_data(credentials)
rental_applications_df = rental_applications_data(credentials)
raw_inquiries_df = raw_inquiries_data(credentials)
leasing_funnel_df = leasing_funnel_data(credentials)
inquiries_df = inquiries_data(credentials)
tours_df = tours_data(credentials)
vacancy_df = vacancy_data(credentials)
distinct_vacancy_df = distinct_vacancy_data(credentials)

# Application
st.title("Leasing Dashboard")

competitors_tab, summary_tab, leasing_funnel_tab, application_funnel_tab, inquiries_tab, tours_tab, vacancy_tab = st.tabs(["Competitors", 'Summary', 'Leasing Funnel', 'Application Funnel', 'Inquiries', 'Tours', 'Vacancy'])
with competitors_tab:
    leasing_period_df, start_date, end_date, color_scale = competitors_filters(leasing_df)
    metrics()
    clearance_rates(leasing_period_df, start_date, end_date)
    rent_changes(leasing_period_df, color_scale)
    turn_times(leasing_period_df, color_scale)
with summary_tab:
    summary_start_date, summary_end_date = summary_filters(rental_applications_df)
    summary_metrics(rental_applications_df, summary_start_date, summary_end_date, raw_inquiries_df)
with leasing_funnel_tab:
    filtered_leasing_funnel_df, filtered_selected_time_granularity = filters(leasing_funnel_df, 'leasing_funnel')
    grouped_leasing_funnel_df = leasing_funnel_grouped(filtered_leasing_funnel_df)
    leasing_funnel_summary_metrics(grouped_leasing_funnel_df, filtered_selected_time_granularity)
    leasing_funnel_chart(grouped_leasing_funnel_df)
with application_funnel_tab:
    filtered_application_funnel_df, filtered_selected_time_granularity = filters(leasing_funnel_df, 'application_funnel')
    grouped_application_funnel_df = application_funnel_grouped(filtered_application_funnel_df)
    application_funnel_summary_metrics(grouped_application_funnel_df, filtered_selected_time_granularity)
    application_funnel_chart(grouped_application_funnel_df)
with inquiries_tab:
    filtered_inquiries_df, filtered_selected_time_granularity = filters(inquiries_df, 'inquiries')
    grouped_inquiries_df = inquiries_grouped(filtered_inquiries_df)
    num_inquiries(grouped_inquiries_df, filtered_selected_time_granularity)
    inquiries_filled_out_prequalification_form(grouped_inquiries_df)
    inquiries_prequalified(grouped_inquiries_df)
    homes_with_zero_inquiries(grouped_inquiries_df)
with tours_tab: 
    filtered_tours_df, filtered_selected_time_granularity = filters(tours_df, 'tours')
    grouped_tours_df = tours_grouped(filtered_tours_df)
    tour_metrics(grouped_tours_df)
    num_tours_by_source(grouped_tours_df)
    num_tours_by_farthest_funnel_stage(grouped_tours_df)
    homes_with_zero_tours(grouped_tours_df)
with vacancy_tab:
    filtered_vacancy_df, selected_vacancy = vacancy_filters(distinct_vacancy_df, vacancy_df)
    vacancy_curve(filtered_vacancy_df)
    

    


