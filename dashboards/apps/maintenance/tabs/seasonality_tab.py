import streamlit as st
import pandas as pd
from datetime import datetime

from data import all_management_expenses_data
from tabs.utils import all_management_expenses_data_clean, seasonality_chart, MONTH_ORDER

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
                
    col_category_group, col_vendor = st.columns(2)
    with col_category_group:
        category_group = st.multiselect("Select a category group", ['All'] + sorted(list(filtered_all_management_expenses_df['category_group'].unique())), default='run_rate', key='seasonality_category_group')
        if 'All' not in category_group:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['category_group'].isin(category_group)]
    with col_vendor:
        selected_vendors = st.multiselect("Select a vendor", ['All'] + sorted(list(filtered_all_management_expenses_df['vendor'].unique())), default='All', key='seasonality_vendor', help="vendor format is 'Company Name (Contact Name)' or 'Contact Name'")
        if 'All' not in selected_vendors:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['vendor'].isin(selected_vendors)]

    col_fund, col_market = st.columns(2)
    with col_fund:
        selected_funds = st.multiselect("Select a fund", ['All'] + sorted(list(filtered_all_management_expenses_df['fund'].unique())), default='All', key='seasonality_fund')
        if 'All' not in selected_funds:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['fund'].isin(selected_funds)]
    with col_market:
        market_options = list(filtered_all_management_expenses_df['market'].unique())
        market_sorted = sorted(market_options, key=lambda x: (pd.isna(x), str(x).lower()))
        selected_markets = st.multiselect("Select a market", ['All'] + sorted(market_options, key=lambda x: (pd.isna(x), str(x).lower())), default='All', key='seasonality_market')
        if 'All' not in selected_markets:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['market'].isin(selected_markets)]

    return filtered_all_management_expenses_df


def seasonality_by_category(all_management_expenses_df):
    st.subheader("Seasonality by Category")

    # only include categories if column has values
    category_options = ['gl_account']
    for category in ['maintenance_category', 'maintenance_subcategory']:
        unique_values = all_management_expenses_df[category].dropna().unique()
        unique_values = [v for v in unique_values if str(v).lower() != 'none']
        if len(unique_values) > 0:
            category_options.append(category)
    selected_group_by = st.selectbox("Select a category", category_options, key='seasonality_group_by')
    for group in sorted(all_management_expenses_df[selected_group_by].unique()):
        group_expenses_df = all_management_expenses_df[all_management_expenses_df[selected_group_by] == group]

        # group by year and month
        seasonality_df = (
            group_expenses_df
            .groupby(['year', 'month'], as_index=False)
            .agg(total_spend=('amount', 'sum'))
        )
        seasonality_df['month'] = pd.Categorical(seasonality_df['month'], categories=MONTH_ORDER, ordered=True)
        seasonality_df = seasonality_df.sort_values(['year', 'month'])
        
        # ensure all months are present for each year in the selected date range
        years = sorted(all_management_expenses_df['year'].unique())
        all_combos = pd.MultiIndex.from_product([years, MONTH_ORDER], names=['year', 'month']).to_frame(index=False)
        seasonality_df = (
            all_combos
            .merge(seasonality_df, on=['year', 'month'], how='left')
            .fillna({'total_spend': 0})
        )

        # display chart
        st.markdown(f"<h5>{group.replace('_', ' ').title()}</h5>", unsafe_allow_html=True)
        seasonality_chart(seasonality_df, 'total_spend', 'Buildium Spend ($)')