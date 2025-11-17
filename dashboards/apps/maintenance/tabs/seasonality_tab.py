import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

from data import all_management_expenses_data, owned_homes_data
from tabs.utils import (
    all_management_expenses_data_clean,
    owned_homes_data_clean,
    projected_current_month_df,
    seasonality_chart,
    MONTH_ORDER,
    CURRENT_MONTH_PROJECTED
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
            filtered_owned_homes_df = filtered_owned_homes_df[filtered_owned_homes_df['fund'].isin(selected_funds)]
    with col_market:
        market_options = list(filtered_all_management_expenses_df['market'].unique())
        market_sorted = sorted(market_options, key=lambda x: (pd.isna(x), str(x).lower()))
        selected_markets = st.multiselect("Select a market", ['All'] + sorted(market_options, key=lambda x: (pd.isna(x), str(x).lower())), default='All', key='seasonality_market')
        if 'All' not in selected_markets:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['market'].isin(selected_markets)]
            filtered_owned_homes_df = filtered_owned_homes_df[filtered_owned_homes_df['market'].isin(selected_markets)]

    return filtered_all_management_expenses_df, filtered_owned_homes_df


def seasonality_by_category(all_management_expenses_df, owned_homes_df):
    st.subheader("Seasonality by Category")

    # only include categories if column has values
    category_options = []
    for category in ['maintenance_category', 'maintenance_subcategory']:
        unique_values = all_management_expenses_df[category].dropna().unique()
        unique_values = [v for v in unique_values if str(v).lower() != 'none']
        if len(unique_values) > 0:
            category_options.append(category)

    category_options.append('gl_account')

    col_category, col_spend_per_home = st.columns([2, 0.25])
    with col_category:
        selected_category = st.selectbox("Select a category", category_options, key='seasonality_category')
    with col_spend_per_home:
        spend_per_home = st.toggle("$/Home", value=False, key='seasonality_by_category_per_home')
    for category in sorted(all_management_expenses_df[selected_category].unique()):
        category_expenses_df = all_management_expenses_df[all_management_expenses_df[selected_category] == category]

        # group by year and month
        seasonality_df = (
            category_expenses_df
            .groupby(['year', 'month'], as_index=False)
            .agg(total_spend=('amount', 'sum'))
        )

        # add data point for current month with projected spend by end of month
        seasonality_df = pd.concat([
            seasonality_df,
            projected_current_month_df(category_expenses_df)
        ], ignore_index=True)

        seasonality_df['month'] = pd.Categorical(seasonality_df['month'], categories=MONTH_ORDER, ordered=True)
        seasonality_df = seasonality_df.sort_values(['year', 'month'])

        # ensure all months are present for each year in the selected date range
        years = sorted(all_management_expenses_df['year'].unique())
        all_combos = pd.MultiIndex.from_product(
            [years, MONTH_ORDER],
            names=['year', 'month']
        ).to_frame(index=False)
        # however, exclude any future months
        num_future_rows = 12 - datetime.now().month
        all_combos = all_combos.iloc[:-num_future_rows] if num_future_rows > 0 else all_combos

        current_month = datetime.now().strftime('%B')
        last_month = (datetime.now() - relativedelta(months=1)).strftime('%B')
        all_combos = pd.concat([
            all_combos,
            pd.DataFrame([
                { 'year': CURRENT_MONTH_PROJECTED, 'month': current_month },
                { 'year': CURRENT_MONTH_PROJECTED, 'month': last_month }
            ]) 
        ], ignore_index=True)
        seasonality_df = (
            all_combos
            .merge(seasonality_df, on=['year', 'month'], how='left')
            .fillna({'total_spend': 0})
        )

        if spend_per_home:
            month_owned_homes_df = owned_homes_df[owned_homes_df['time_granularity'] == 'month']
            grouped_month_owned_homes_df = month_owned_homes_df.groupby(['year', 'month'], as_index=False).agg(total_homes_owned=('homes_owned', 'sum'))
            seasonality_df = seasonality_df.merge(grouped_month_owned_homes_df, on=['year', 'month'], how='left')

            # fill values for CURRENT_MONTH_PROJECTED
            current_month_homes_owned = seasonality_df.loc[(
                (seasonality_df['year'] == datetime.now().year)
                & (seasonality_df['month'] == current_month)
            ), 'total_homes_owned'].iloc[0]
            seasonality_df.loc[
                (seasonality_df['year'] == CURRENT_MONTH_PROJECTED)
                & (seasonality_df['month'] == current_month),
                'total_homes_owned'
            ] = current_month_homes_owned

            last_month_homes_owned = seasonality_df.loc[(
                (seasonality_df['year'] == datetime.now().year)
                & (seasonality_df['month'] == last_month)
            ), 'total_homes_owned'].iloc[0]
            seasonality_df.loc[
                (seasonality_df['year'] == CURRENT_MONTH_PROJECTED)
                & (seasonality_df['month'] == last_month),
                'total_homes_owned'
            ] = last_month_homes_owned

            seasonality_df['total_spend_per_home'] = round(seasonality_df['total_spend'] / seasonality_df['total_homes_owned'], 2)

        # display chart
        st.markdown(f"<h5>{category.replace('_', ' ').title()}</h5>", unsafe_allow_html=True)
        seasonality_chart(seasonality_df, 
            spend_col='total_spend_per_home' if spend_per_home else 'total_spend', 
            spend_title='Buildium Spend ($/Home)' if spend_per_home else 'Buildium Spend ($)', 
        )
