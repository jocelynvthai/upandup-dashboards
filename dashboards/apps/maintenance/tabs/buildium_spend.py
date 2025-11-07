import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import re
from datetime import datetime, timedelta

from data import all_management_expenses_data, owned_homes_data, budget_by_month_data
from tabs.utils import DARK_TEAL, TEAL, LIGHT_TEAL, DARK_PURPLE, PURPLE, PINK, PASTEL_LILAC, PASTEL_LIGHT_BLUE, PASTEL_SOFT_PINK, PASTEL_YELLOW, PASTEL_MINT
PASTEL_PALETTE = [PASTEL_LILAC, PASTEL_LIGHT_BLUE, PASTEL_SOFT_PINK, PASTEL_MINT]

CURRENT_YEAR = datetime.now().year

def all_management_expenses_data_clean(all_management_expenses_df):
    cleaned_all_management_expenses_df = all_management_expenses_df.copy()

    # week & month end dates
    cleaned_all_management_expenses_df['date_time'] = pd.to_datetime(cleaned_all_management_expenses_df['date'])
    cleaned_all_management_expenses_df['week_end'] = (cleaned_all_management_expenses_df['date_time'] + pd.to_timedelta(6 - cleaned_all_management_expenses_df['date_time'].dt.weekday, unit='d')).dt.strftime('%Y-%m-%d')
    cleaned_all_management_expenses_df['month_end'] = (cleaned_all_management_expenses_df['date_time'] + pd.offsets.MonthEnd(0)).dt.strftime('%Y-%m-%d')
    cleaned_all_management_expenses_df['month'] = cleaned_all_management_expenses_df['date_time'].dt.strftime('%B')
    cleaned_all_management_expenses_df['year'] = cleaned_all_management_expenses_df['date_time'].dt.year

    # gl account
    cleaned_all_management_expenses_df['gl_account'] = cleaned_all_management_expenses_df['gl_account_number'] + ' (' + cleaned_all_management_expenses_df['gl_account_name'] + ')'

    # vendor
    cleaned_all_management_expenses_df['vendor_company_name'] = (
        cleaned_all_management_expenses_df['vendor_company_name'] 
        .apply(lambda x: x.strip() if isinstance(x, str) else x)
        .replace([None, '', 'None', 'nan', 'NaN'], np.nan)         
    )
    cleaned_all_management_expenses_df['vendor_contact_name'] = (
        cleaned_all_management_expenses_df['vendor_contact_name']
        .apply(lambda x: x.strip() if isinstance(x, str) else x)
        .replace([None, '', 'None', 'nan', 'NaN'], np.nan)
    )
    cleaned_all_management_expenses_df['vendor'] = np.select(
        [
            cleaned_all_management_expenses_df['vendor_contact_name'].notna() & cleaned_all_management_expenses_df['vendor_company_name'].notna(),
            cleaned_all_management_expenses_df['vendor_contact_name'].notna() & cleaned_all_management_expenses_df['vendor_company_name'].isna(),
            cleaned_all_management_expenses_df['vendor_contact_name'].isna() & cleaned_all_management_expenses_df['vendor_company_name'].notna(),
        ],
        [
            cleaned_all_management_expenses_df['vendor_company_name'] + ' (' + cleaned_all_management_expenses_df['vendor_contact_name'] + ')', 
            '(' + cleaned_all_management_expenses_df['vendor_contact_name'] + ')', 
            cleaned_all_management_expenses_df['vendor_company_name'],
        ],
        default='No vendor'
    )

    # category group & type
    cleaned_all_management_expenses_df[['category_group', 'category_type']] = cleaned_all_management_expenses_df['category'].apply(
        lambda x: pd.Series([
            x.replace('_r_m', '') if 'r_m' in x else 
            x.replace('_capex', '') if 'capex' in x else
            'common_area_maintenance' if x == 'common_area_maintenance' else
            np.nan,
            'R&M' if 'r_m' in x else 
            'Capex' if 'capex' in x else 
            'Common Area Maintenance' if x == 'common_area_maintenance' else 
            np.nan
        ])
    )

    # latchel invoice link
    cleaned_all_management_expenses_df['latchel_invoice_link'] = (
        cleaned_all_management_expenses_df['latchel_invoice_id'].apply(
            lambda x: f'https://app.latchel.com/admin/invoices/{x}' if x is not None else ''
        )
    )

    return cleaned_all_management_expenses_df


def owned_homes_data_clean(owned_homes_df):
    cleaned_owned_homes_df = owned_homes_df.copy()
    cleaned_owned_homes_df['date_time'] = pd.to_datetime(cleaned_owned_homes_df['date'])
    cleaned_owned_homes_df['month'] = cleaned_owned_homes_df['date_time'].dt.strftime('%B')
    cleaned_owned_homes_df['year'] = cleaned_owned_homes_df['date_time'].dt.year
    cleaned_owned_homes_df['date'] = cleaned_owned_homes_df['date_time'].dt.strftime('%Y-%m-%d')
    return cleaned_owned_homes_df


def budget_by_month_data_clean(budget_by_month_df):
    cleaned_budget_by_month_df = budget_by_month_df.copy()
    cleaned_budget_by_month_df['date_time'] = pd.to_datetime(cleaned_budget_by_month_df['date'])
    cleaned_budget_by_month_df['month'] = cleaned_budget_by_month_df['date_time'].dt.strftime('%B')
    cleaned_budget_by_month_df['year'] = cleaned_budget_by_month_df['date_time'].dt.year
    cleaned_budget_by_month_df['date'] = cleaned_budget_by_month_df['date_time'].dt.strftime('%Y-%m-%d')
    return cleaned_budget_by_month_df[cleaned_budget_by_month_df['year'] == CURRENT_YEAR]


def buildium_spend_filters(credentials):
    # filters
    col_date_range, col_category_group = st.columns(2)
    with col_date_range:
        date_range = st.date_input("Pick a period range", 
                                value=(datetime(2023, 1, 1),  datetime.now()), 
                                format='MM/DD/YYYY',
                                help="The period range to filter the data type selected",
                                key='buildium_spend_date_range')
        if len(date_range) != 2:
            st.stop()
        else:
            filtered_all_management_expenses_df = all_management_expenses_data_clean(all_management_expenses_data(credentials, date_range[0], date_range[1]))
            filtered_owned_homes_df = owned_homes_data_clean(owned_homes_data(credentials, date_range[0]))
            filtered_budget_by_month_df = budget_by_month_data_clean(budget_by_month_data(credentials, date_range[0]))
    with col_category_group:
        category_group = st.multiselect("Select a category group", ['All'] + sorted(list(filtered_all_management_expenses_df['category_group'].unique())), default='run_rate', key='buildium_spend_category_group')
        if 'All' not in category_group:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['category_group'].isin(category_group)]
            if (len(category_group) == 1) and (category_group[0] in ['run_rate', 'common_area_maintenance', 'turn']):
                filtered_budget_by_month_df = filtered_budget_by_month_df[filtered_budget_by_month_df['management_category'] == category_group[0]]
                
    col_gl_account, col_vendor = st.columns(2)
    with col_gl_account:
        selected_gl_accounts = st.multiselect("Select a GL account", ['All'] + sorted(list(filtered_all_management_expenses_df['gl_account'].unique())), default='All')
        if 'All' not in selected_gl_accounts:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['gl_account'].isin(selected_gl_accounts)]
    with col_vendor:
        selected_vendors = st.multiselect("Select a vendor", ['All'] + sorted(list(filtered_all_management_expenses_df['vendor'].unique())), default='All', help="vendor format is 'Company Name (Contact Name)' or 'Contact Name'")
        if 'All' not in selected_vendors:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['vendor'].isin(selected_vendors)]

    col_fund, col_market = st.columns(2)
    with col_fund:
        selected_funds = st.multiselect("Select a fund", ['All'] + sorted(list(filtered_all_management_expenses_df['fund'].unique())), default='All')
        if 'All' not in selected_funds:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['fund'].isin(selected_funds)]
            filtered_owned_homes_df = filtered_owned_homes_df[filtered_owned_homes_df['fund'].isin(selected_funds)]
            filtered_budget_by_month_df = filtered_budget_by_month_df[filtered_budget_by_month_df['fund'].isin(selected_funds)]
    with col_market:
        market_options = list(filtered_all_management_expenses_df['market'].unique())
        market_sorted = sorted(market_options, key=lambda x: (pd.isna(x), str(x).lower()))
        selected_markets = st.multiselect("Select a market", ['All'] + sorted(market_options, key=lambda x: (pd.isna(x), str(x).lower())), default='All', key='buildium_spend_market')
        if 'All' not in selected_markets:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['market'].isin(selected_markets)]
            filtered_owned_homes_df = filtered_owned_homes_df[filtered_owned_homes_df['market'].isin(selected_markets)]

    return filtered_all_management_expenses_df, filtered_owned_homes_df, filtered_budget_by_month_df


def buildium_spend_over_time(all_management_expenses_df, owned_homes_df):
    st.subheader("Buildium Spend Over Time")

    # customize view specifications
    col_time_granularity, col_dimension, col_spend_per_home = st.columns([1, 1, 0.25])
    with col_time_granularity:
        selected_time_granularity = st.selectbox("Select a time granularity", ['week', 'month'], key='buildium_spend_time_granularity')
        st.session_state["time_granularity"] = f'{selected_time_granularity}_end'
        configured_owned_homes_df = owned_homes_df[owned_homes_df['time_granularity'] == selected_time_granularity]
    with col_dimension:
        category_dict = {
            'GL Account': 'gl_account',
            'Vendor': 'vendor',
            'Fund': 'fund',
            'Market': 'market'
        }
        selected_dimension = st.selectbox("Select a dimension", category_dict.keys())
        st.session_state["category"] = category_dict[selected_dimension]
    with col_spend_per_home:
        st.markdown(
            """
            <style>
                .right-align-toggle {
                    display: flex;
                    margin-top: 2rem;
                }
            </style>
            <div class="right-align-toggle">
            """,
            unsafe_allow_html=True
        )
        spend_per_home = st.toggle("$/Home", value=False, key='buildium_spend_over_time_per_home')

    # group, pivot & format data
    grouped_management_expenses_df = (
        all_management_expenses_df
        .groupby([st.session_state["time_granularity"], st.session_state["category"]], dropna=False)
        .agg(total_spend=('amount', 'sum'))
        .reset_index()
    )
    # add spend per home
    if spend_per_home:
        if st.session_state["category"] in configured_owned_homes_df.columns:
            # fund or market dimension
            groupby_cols = ['date', st.session_state["category"]]
            merge_left_on = [st.session_state["time_granularity"], st.session_state["category"]]
            merge_right_on = ['date', st.session_state["category"]]
        else:
            # gl account or vendor dimension
            groupby_cols = ['date']
            merge_left_on = [st.session_state["time_granularity"]]
            merge_right_on = ['date']

        grouped_owned_homes_df = configured_owned_homes_df.groupby(groupby_cols).agg(total_homes_owned=('homes_owned', 'sum')).reset_index()
        grouped_management_expenses_df = grouped_management_expenses_df.merge(grouped_owned_homes_df, 
                                            left_on=merge_left_on, 
                                            right_on=merge_right_on, 
                                            how='left')
        grouped_management_expenses_df['total_spend_per_home'] = grouped_management_expenses_df['total_spend'] / grouped_management_expenses_df['total_homes_owned']

    pivot_df = grouped_management_expenses_df.pivot(
        index=st.session_state["category"],
        columns=st.session_state["time_granularity"],
        values='total_spend_per_home' if spend_per_home else 'total_spend'
    ).fillna(0).reset_index()
    
    value_columns = [col for col in pivot_df.columns if col != st.session_state["category"]]
    styled_pivot_df = pivot_df.style.map(
        lambda v: "color: rgba(0, 0, 0, 0.25)" if v == 0 else "",
        subset=value_columns,
    )
    event = st.dataframe(
        styled_pivot_df,
        on_select="rerun",
        selection_mode=["single-cell"],
        hide_index=True,
        column_config={
            **{
                col: st.column_config.NumberColumn(format="dollar")
                for col in pivot_df.columns
                if col != st.session_state["category"]
            },
            st.session_state["category"]: st.column_config.TextColumn(pinned=True),
        },
    )
    st.caption("<p style='text-align: right;'><i>Select a cell to view the line items</i></p>", unsafe_allow_html=True)

    selected_info = event['selection']
    if len(selected_info['cells']):
        st.session_state["category_filter"] = pivot_df.loc[selected_info['cells'][0][0], st.session_state["category"]]
        st.session_state["time_granularity_filter"] = selected_info['cells'][0][1]
    else:
        st.session_state["category_filter"] = None
        st.session_state["time_granularity_filter"] = None
        

def buildium_spend_seasonality(all_management_expenses_df, owned_homes_df, budget_by_month_df):
    st.subheader("Buildium Spend Seasonality")

    seasonality_df = (
        all_management_expenses_df
        .groupby(['year', 'month'], as_index=False)
        .agg(total_spend=('amount', 'sum'))
    )
    month_order = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    seasonality_df['month'] = pd.Categorical(seasonality_df['month'], categories=month_order, ordered=True)
    seasonality_df = seasonality_df.sort_values(['year', 'month'])

    # prepare budget data
    grouped_budget_by_month_df = budget_by_month_df.groupby(['year', 'month'], as_index=False).agg(total_spend=('amount', 'sum'))
    # add spend per home
    _, col_spend_per_home = st.columns([2, 0.25])
    with col_spend_per_home:
        spend_per_home = st.toggle("$/Home", value=False, key='buildium_spend_seasonality_per_home')
    if spend_per_home:
        month_owned_homes_df = owned_homes_df[owned_homes_df['time_granularity'] == 'month']
        grouped_month_owned_homes_df = month_owned_homes_df.groupby(['year', 'month'], as_index=False).agg(total_homes_owned=('homes_owned', 'sum'))
        seasonality_df = seasonality_df.merge(grouped_month_owned_homes_df, on=['year', 'month'], how='left')
        # add budget data
        budget_seasonality_df = grouped_budget_by_month_df.merge(grouped_month_owned_homes_df, on=['year', 'month'], how='left')
        budget_seasonality_df.loc[budget_seasonality_df['year'] == CURRENT_YEAR, 'year'] = 'Budget'
        seasonality_df = pd.concat([seasonality_df, budget_seasonality_df])
        seasonality_df['total_spend_per_home'] = seasonality_df['total_spend'] / seasonality_df['total_homes_owned']
    else:
        # add budget data
        grouped_budget_by_month_df.loc[grouped_budget_by_month_df['year'] == CURRENT_YEAR, 'year'] = 'Budget'
        seasonality_df = pd.concat([seasonality_df, grouped_budget_by_month_df])


    years = [str(y) for y in seasonality_df['year'].unique() if y not in ['Budget', CURRENT_YEAR]]
    color_scale = alt.Scale(
        domain=years+[str(CURRENT_YEAR), 'Budget'],
        range=PASTEL_PALETTE[:len(years)]+[TEAL, PASTEL_YELLOW]
    )
    seasonality_chart = (
        alt.Chart(seasonality_df)
        .mark_line(point=True)
        .encode(
            x=alt.X('month', sort=month_order, title='Month'),
            y=alt.Y(
                'total_spend_per_home' if spend_per_home else 'total_spend',
                title='Buildium Spend ($/Home)' if spend_per_home else 'Buildium Spend ($)'
            ),
            color=alt.Color('year:N', title='Year', scale=color_scale),
            strokeWidth=alt.condition(
                f"datum.year == {CURRENT_YEAR}", alt.value(3), alt.value(1.5)
            ),
            tooltip=['year', 'month', 'total_spend_per_home' if spend_per_home else 'total_spend']
        )
        .properties(width=700, height=400)
        .interactive()
    )
    st.altair_chart(seasonality_chart, use_container_width=True)



def buildium_spend_line_items(all_management_expenses_df):
    if ("time_granularity_filter" in st.session_state and st.session_state["time_granularity_filter"] is not None) and ("category_filter" in st.session_state and st.session_state["category_filter"] is not None):
        st.subheader("Buildium Spend Line Items")    
        
        line_items_df = all_management_expenses_df.copy()
        line_items_df = line_items_df[line_items_df[st.session_state["time_granularity"]] == st.session_state["time_granularity_filter"]]
        line_items_df = line_items_df[line_items_df[st.session_state["category"]] == st.session_state["category_filter"]]

        line_items_cols = [
            'latchel_invoice_link',
            'category_group',
            'category_type',
            'gl_account',
            'address',
            'fund',
            'market',
            'date',
            'amount',
            'description',
            'vendor'
        ]
        def color_category(val):
            if val == 'R&M':
                return f'color: {TEAL}' 
            elif val == 'Capex':
                return f'color: {PURPLE}' 
            elif val == 'Common Area Maintenance':
                return f'color: {PINK}'

        styled_df = (
            line_items_df.assign(
                category_type=pd.Categorical(
                    line_items_df['category_type'], 
                    categories=['R&M', 'Capex', 'Common Area Maintenance'], 
                    ordered=True
                ),
                category_group=pd.Categorical(
                    line_items_df['category_group'], 
                    categories=['make_ready', 'run_rate', 'turn', 'disposition'], 
                    ordered=True
                )
            )
            .sort_values(['category_type', 'category_group'])
            [line_items_cols]
            .style.applymap(color_category, subset=['category_type'])
        )
        st.dataframe(
            styled_df, 
            hide_index=True,
            column_config={
                'latchel_invoice_link': st.column_config.LinkColumn(
                    label="latchel",
                    display_text=":material/link:",
                    width="small",
                    pinned=True,
                ),
                'gl_account': st.column_config.TextColumn(pinned=True),
                'category_group': st.column_config.TextColumn(pinned=True,),
                'category_type': st.column_config.TextColumn(pinned=True),
                'amount': st.column_config.NumberColumn(format="dollar"),
            }
        )


