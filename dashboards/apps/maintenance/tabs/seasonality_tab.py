import streamlit as st
import pandas as pd
from datetime import datetime

from data import all_management_expenses_data, owned_homes_data, budget_by_month_data
from tabs.utils import (
    all_management_expenses_data_clean,
    owned_homes_data_clean,
    budget_by_month_data_clean, 
    projected_df,
    seasonality_chart,
    CURRENT_YEAR, 
    MONTH_ORDER,
    CURRENT_YEAR_PROJECTED
)

def seasonality_filters(credentials):
    # filters
    date_range = st.date_input("Pick a period range", 
                            value=(datetime(2023, 1, 1),  datetime.now()), 
                            format='MM/DD/YYYY',
                            help="The period range to filter the data type selected",
                            key='seasonality_date_range')
    if len(date_range) != 2:
        st.stop()
    else:
        filtered_all_management_expenses_df = all_management_expenses_data_clean(all_management_expenses_data(credentials, date_range[0], date_range[1]))
        filtered_owned_homes_df = owned_homes_data_clean(owned_homes_data(credentials, date_range[0]))
        filtered_budget_by_month_df = budget_by_month_data_clean(budget_by_month_data(credentials, date_range[0]))
                
    col_category_group, col_vendor = st.columns(2)
    with col_category_group:
        category_group_options = [c for c in filtered_all_management_expenses_df['category_group'].unique() if pd.notna(c)]
        category_group = st.multiselect("Select a category group", ['All'] + sorted(category_group_options), default='run_rate', key='seasonality_category_group')
        if 'All' not in category_group:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['category_group'].isin(category_group)]
            filtered_budget_by_month_df = filtered_budget_by_month_df[filtered_budget_by_month_df['management_category'].isin(category_group)]
    with col_vendor:
        vendor_options = [v for v in filtered_all_management_expenses_df['vendor'].unique() if pd.notna(v)]
        selected_vendors = st.multiselect("Select a vendor", ['All'] + sorted(vendor_options), default='All', key='seasonality_vendor', help="vendor format is 'Company Name (Contact Name)' or 'Contact Name'")
        if 'All' not in selected_vendors:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['vendor'].isin(selected_vendors)]

    col_fund, col_market = st.columns(2)
    with col_fund:
        fund_options = [f for f in filtered_all_management_expenses_df['fund'].unique() if pd.notna(f)]
        selected_funds = st.multiselect("Select a fund", ['All'] + sorted(fund_options), default='All', key='seasonality_fund')
        if 'All' not in selected_funds:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['fund'].isin(selected_funds)]
            filtered_owned_homes_df = filtered_owned_homes_df[filtered_owned_homes_df['fund'].isin(selected_funds)]
            filtered_budget_by_month_df = filtered_budget_by_month_df[filtered_budget_by_month_df['fund'].isin(selected_funds)]
    with col_market:
        market_options = [m for m in filtered_all_management_expenses_df['market'].unique() if pd.notna(m)]
        selected_markets = st.multiselect("Select a market", ['All'] + sorted(market_options, key=lambda x: str(x).lower()), default='All', key='seasonality_market')
        if 'All' not in selected_markets:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['market'].isin(selected_markets)]
            filtered_owned_homes_df = filtered_owned_homes_df[filtered_owned_homes_df['market'].isin(selected_markets)]

    return filtered_all_management_expenses_df, filtered_owned_homes_df, filtered_budget_by_month_df



def buildium_spend_seasonality(all_management_expenses_df, owned_homes_df, budget_by_month_df):
    st.subheader("Buildium Spend Seasonality")
    
    # spend per year/month
    seasonality_df = all_management_expenses_df.groupby(['year', 'month'], as_index=False).agg(total_spend=('amount', 'sum'))
    seasonality_df['month'] = pd.Categorical(seasonality_df['month'], categories=MONTH_ORDER, ordered=True)
    seasonality_df = seasonality_df.sort_values(['year', 'month'])
    # add projected data
    seasonality_df = pd.concat([seasonality_df, projected_df(all_management_expenses_df)], ignore_index=True)
    # add budget data
    grouped_budget_base_by_month_df = budget_by_month_df.groupby(['year', 'month'], as_index=False).agg(total_spend=('amount_base', 'sum'))
    grouped_budget_base_by_month_df.loc[grouped_budget_base_by_month_df['year'] == CURRENT_YEAR, 'year'] = 'Budget (Base)'
    grouped_budget_stretch_by_month_df = budget_by_month_df.groupby(['year', 'month'], as_index=False).agg(total_spend=('amount_stretch', 'sum'))
    grouped_budget_stretch_by_month_df.loc[grouped_budget_stretch_by_month_df['year'] == CURRENT_YEAR, 'year'] = 'Budget (Stretch)'
    seasonality_df = pd.concat([seasonality_df, grouped_budget_base_by_month_df, grouped_budget_stretch_by_month_df], ignore_index=True)

    # add spend per home
    _, col_spend_per_home = st.columns([2, 0.25])
    with col_spend_per_home:
        spend_per_home = st.toggle("$/Home", value=False, key='buildium_spend_seasonality_per_home')
    if spend_per_home:
        month_owned_homes_df = owned_homes_df[owned_homes_df['time_granularity'] == 'month']
        grouped_month_owned_homes_df = month_owned_homes_df.groupby(['year', 'month'], as_index=False).agg(total_homes_owned=('homes_owned', 'sum'))
        seasonality_df = seasonality_df.merge(grouped_month_owned_homes_df, on=['year', 'month'], how='left')

        # impute total homes owned for budget and projected rows
        budget_and_projected_rows = seasonality_df[
            (seasonality_df['year'] == 'Budget (Base)')
            | (seasonality_df['year'] == 'Budget (Stretch)')
            | (seasonality_df['year'] == CURRENT_YEAR_PROJECTED)
        ]
        for index, row in budget_and_projected_rows.iterrows():
            homes_owned_for_month = grouped_month_owned_homes_df.loc[((grouped_month_owned_homes_df['year'] == CURRENT_YEAR) & (grouped_month_owned_homes_df['month'] == row['month']))]['total_homes_owned'].iloc[0]
            seasonality_df.loc[index, 'total_homes_owned'] = homes_owned_for_month
        
        # compute spend per home
        seasonality_df['total_spend_per_home'] = round(seasonality_df['total_spend'] / seasonality_df['total_homes_owned'], 2)

    # display chart
    seasonality_chart(seasonality_df, 
        spend_col='total_spend_per_home' if spend_per_home else 'total_spend', 
        spend_title='Buildium Spend ($/Home)' if spend_per_home else 'Buildium Spend ($)', 
        budget_year=True, 
    )



def seasonality_by_category(all_management_expenses_df, owned_homes_df):
    st.subheader("Seasonality by Category")

    col_category, col_spend_per_home = st.columns([2, 0.25])
    with col_category:
        selected_category = st.selectbox("Select a category", ['maintenance_category', 'maintenance_subcategory', 'gl_account'], format_func=lambda x: x.replace('_', ' ').title(), key='seasonality_category')
    with col_spend_per_home:
        spend_per_home = st.toggle("$/Home", value=False, key='seasonality_by_category_per_home')
    for category in sorted(all_management_expenses_df[selected_category].dropna().unique()):
        category_expenses_df = all_management_expenses_df[all_management_expenses_df[selected_category] == category]

        # spend per year/month data
        seasonality_df = category_expenses_df.groupby(['year', 'month'], as_index=False).agg(total_spend=('amount', 'sum'))
        seasonality_df['month'] = pd.Categorical(seasonality_df['month'], categories=MONTH_ORDER, ordered=True)
        seasonality_df = seasonality_df.sort_values(['year', 'month'])
        # ensure all months are present for each year up until the current month
        years = sorted(all_management_expenses_df['year'].unique())
        all_combos = pd.MultiIndex.from_product([years, MONTH_ORDER],names=['year', 'month']).to_frame(index=False)
        num_future_rows = 12 - datetime.now().month
        all_combos = all_combos.iloc[:-num_future_rows] if num_future_rows > 0 else all_combos
        seasonality_df = all_combos.merge(seasonality_df, on=['year', 'month'], how='left').fillna({'total_spend': 0})
        # add projected data
        seasonality_df = pd.concat([seasonality_df, projected_df(category_expenses_df)], ignore_index=True)

        if spend_per_home:
            month_owned_homes_df = owned_homes_df[owned_homes_df['time_granularity'] == 'month']
            grouped_month_owned_homes_df = month_owned_homes_df.groupby(['year', 'month'], as_index=False).agg(total_homes_owned=('homes_owned', 'sum'))
            seasonality_df = seasonality_df.merge(grouped_month_owned_homes_df, on=['year', 'month'], how='left')

            projected_rows = seasonality_df[seasonality_df['year'] == CURRENT_YEAR_PROJECTED]
            for index, row in projected_rows.iterrows():
                homes_owned_for_month = grouped_month_owned_homes_df.loc[((grouped_month_owned_homes_df['year'] == CURRENT_YEAR) & (grouped_month_owned_homes_df['month'] == row['month']))]['total_homes_owned'].iloc[0]
                seasonality_df.loc[index, 'total_homes_owned'] = homes_owned_for_month
                
            # compute spend per home
            seasonality_df['total_spend_per_home'] = round(seasonality_df['total_spend'] / seasonality_df['total_homes_owned'], 2)
        
        # display chart
        st.markdown(f"<h5>{category.replace('_', ' ').title()}</h5>", unsafe_allow_html=True)
        seasonality_chart(seasonality_df, 
            spend_col='total_spend_per_home' if spend_per_home else 'total_spend', 
            spend_title='Buildium Spend ($/Home)' if spend_per_home else 'Buildium Spend ($)', 
        )
