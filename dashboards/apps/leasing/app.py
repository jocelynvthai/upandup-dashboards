import streamlit as st
from google.oauth2 import service_account

from data import (
    get_service_account_info,
    leasing_scraper_data,
    leasing_scraper_individual_rent_changes_data,
    leasing_scraper_weekly_rent_changes_data,
    rental_applications_data,
    raw_inquiries_data,
    leasing_funnel_data,
    inquiries_data,
    tours_data,
    vacancy_curve_data,
    distinct_vacancies_data,
    economic_occupancy_data,
    rental_data
)
from tabs.utils import filters
from tabs.summary_tab import summary_filters, summary_metrics
from tabs.inquiries_tab import inquiries_grouped, num_inquiries, inquiries_filled_out_prequalification_form, inquiries_prequalified, homes_with_zero_inquiries
from tabs.tours_tab import tours_grouped, tour_metrics, num_tours_by_source, num_tours_by_farthest_funnel_stage, homes_with_zero_tours
from tabs.leasing_funnel_tab import leasing_funnel_grouped, leasing_funnel_summary_metrics, leasing_funnel_chart
from tabs.application_funnel_tab import application_funnel_grouped, application_funnel_summary_metrics, application_funnel_chart
from tabs.occupancy_tab import occupancy_filters, occupancy_metrics, economic_occupancy, num_leases_to_target, new_projected_economic_occupancy, upcoming_moves
from tabs.vacancy_curve_tab import vacancy_curve_filters, vacancy_curve
from tabs.competitors_tab import competitors_filters, metrics, turn_times, weekly_rent_changes, rent_curve, clearance_rates, leased_homes_stats

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
leasing_rent_individual_rent_changes_df = leasing_scraper_individual_rent_changes_data(credentials)
leasing_rent_weekly_rent_changes_df = leasing_scraper_weekly_rent_changes_data(credentials)
rental_applications_df = rental_applications_data(credentials)
raw_inquiries_df = raw_inquiries_data(credentials)
leasing_funnel_df = leasing_funnel_data(credentials)
inquiries_df = inquiries_data(credentials)
tours_df = tours_data(credentials)
vacancy_curve_df = vacancy_curve_data(credentials)
distinct_vacancies_df = distinct_vacancies_data(credentials)
economic_occupancy_df = economic_occupancy_data(credentials)
rental_df = rental_data(credentials)

# Application
st.title("Leasing Dashboard")

summary_tab, inquiries_tab, tours_tab, leasing_funnel_tab, application_funnel_tab, occupancy_tab, vacancy_curve_tab, competitors_tab= st.tabs(["Summary", 'Inquiries', 'Tours', 'Leasing Funnel', 'Application Funnel', 'Occupancy', 'Vacancy Curve', 'Competitors'])
with summary_tab:
    summary_start_date, summary_end_date = summary_filters(rental_applications_df)
    summary_metrics(rental_applications_df, summary_start_date, summary_end_date, raw_inquiries_df)
with inquiries_tab:
    filtered_inquiries_df, inquiries_selected_time_granularity = filters(inquiries_df, 'inquiries', community_filter=True)
    grouped_inquiries_df = inquiries_grouped(filtered_inquiries_df)
    num_inquiries(grouped_inquiries_df, inquiries_selected_time_granularity)
    inquiries_filled_out_prequalification_form(grouped_inquiries_df)
    inquiries_prequalified(grouped_inquiries_df)
    homes_with_zero_inquiries(grouped_inquiries_df)
with tours_tab: 
    filtered_tours_df, tours_selected_time_granularity = filters(tours_df, 'tours', community_filter=True)
    grouped_tours_df = tours_grouped(filtered_tours_df)
    tour_metrics(grouped_tours_df)
    num_tours_by_source(grouped_tours_df)
    num_tours_by_farthest_funnel_stage(grouped_tours_df)
    homes_with_zero_tours(grouped_tours_df)
with leasing_funnel_tab:
    filtered_leasing_funnel_df, leasing_selected_time_granularity = filters(leasing_funnel_df, 'leasing_funnel')
    grouped_leasing_funnel_df = leasing_funnel_grouped(filtered_leasing_funnel_df)
    leasing_funnel_summary_metrics(grouped_leasing_funnel_df, leasing_selected_time_granularity)
    leasing_funnel_chart(grouped_leasing_funnel_df)
with application_funnel_tab:
    filtered_application_funnel_df, application_selected_time_granularity = filters(leasing_funnel_df, 'application_funnel')
    grouped_application_funnel_df = application_funnel_grouped(filtered_application_funnel_df)
    application_funnel_summary_metrics(grouped_application_funnel_df, application_selected_time_granularity)
    application_funnel_chart(grouped_application_funnel_df)
with occupancy_tab:
    filtered_economic_occupancy_df, filtered_rental_df = occupancy_filters(economic_occupancy_df, rental_df)
    occupancy_metrics(filtered_economic_occupancy_df)
    st.divider()
    economic_occupancy(filtered_economic_occupancy_df)
    st.divider()
    num_leases_to_target(filtered_economic_occupancy_df)
    st.divider()
    new_projected_economic_occupancy(filtered_economic_occupancy_df)
    st.divider()
    upcoming_moves(filtered_rental_df)
with vacancy_curve_tab:
    filtered_vacancy_curve_df, selected_vacancy = vacancy_curve_filters(distinct_vacancies_df, vacancy_curve_df)
    vacancy_curve(filtered_vacancy_curve_df)
with competitors_tab:
    leasing_period_df, filtered_leasing_rent_weekly_rent_changes_df, start_date, end_date, color_scale = competitors_filters(leasing_df, leasing_rent_weekly_rent_changes_df) 
    metrics()
    selected_tab = st.pills('TABS', options=["Turn Times", "Weekly Rent Changes", "Leased Homes"], 
                        default='Weekly Rent Changes',
                        selection_mode = "single", 
                        label_visibility="hidden"
    )

    if selected_tab == "Turn Times":
        turn_times(leasing_period_df, color_scale)
    if selected_tab == "Weekly Rent Changes":
        weekly_rent_changes(filtered_leasing_rent_weekly_rent_changes_df)
        st.divider()
        rent_curve(filtered_leasing_rent_weekly_rent_changes_df)
    elif selected_tab == "Leased Homes":
        clearance_rates(leasing_period_df, start_date, end_date)
        st.divider()
        leased_homes_stats(leasing_period_df, leasing_rent_individual_rent_changes_df, start_date, end_date, color_scale)

    


