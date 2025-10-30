import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

from tabs.utils import TEAL, PURPLE, PINK

def buildium_spend_data_clean(all_management_expenses_df):
    cleaned_all_management_expenses_df = all_management_expenses_df[all_management_expenses_df['transaction_type'] == 'Bill'].copy()

    # week & month end dates
    cleaned_all_management_expenses_df['date_time'] = pd.to_datetime(cleaned_all_management_expenses_df['date'])
    cleaned_all_management_expenses_df['week_end'] = (cleaned_all_management_expenses_df['date_time'] + pd.to_timedelta(6 - cleaned_all_management_expenses_df['date_time'].dt.weekday, unit='d')).dt.strftime('%Y-%m-%d')
    cleaned_all_management_expenses_df['month_end'] = (cleaned_all_management_expenses_df['date_time'] + pd.offsets.MonthEnd(0)).dt.strftime('%Y-%m-%d')

    # gl account
    cleaned_all_management_expenses_df['gl_account'] = cleaned_all_management_expenses_df['gl_account_number'] + ' (' + cleaned_all_management_expenses_df['gl_account_name'] + ')'

    # vendor
    cleaned_all_management_expenses_df['vendor_company_name'] = (
        cleaned_all_management_expenses_df['vendor_company_name'] 
        .apply(lambda x: x.strip() if isinstance(x, str) else x)
        .replace(['', 'None', 'nan', 'NaN'], np.nan)         
    )
    cleaned_all_management_expenses_df['vendor_contact_name'] = (
        cleaned_all_management_expenses_df['vendor_contact_name']
        .apply(lambda x: x.strip() if isinstance(x, str) else x)
        .replace(['', 'None', 'nan', 'NaN'], np.nan)
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
        default=np.nan 
    )

    # category group & type
    cleaned_all_management_expenses_df[['category_group', 'category_type']] = cleaned_all_management_expenses_df['category'].apply(
        lambda x: pd.Series([
            x.replace('_r_m', '') if 'r_m' in x else 
            x.replace('_capex', '') if 'capex' in x else 
            np.nan,
            'R&M' if 'r_m' in x else 
            'Capex' if 'capex' in x else 
            'Common Area Maintenance' if x == 'common_area_maintenance' else 
            np.nan
        ])
    )

    return cleaned_all_management_expenses_df


def buildium_spend_filters(all_management_expenses_df):
    filtered_all_management_expenses_df = all_management_expenses_df.copy()

    # filters
    col_date_range, col_category_type = st.columns(2)
    with col_date_range:
        date_range = st.date_input("Pick a period range", 
                                value=(datetime.now() - timedelta(days=30),  datetime.now()), 
                                format='MM/DD/YYYY',
                                help="The period range to filter the data type selected",
                                key='latchel_spend_date_range')
        if len(date_range) != 2:
            st.stop()
        else:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[(filtered_all_management_expenses_df['date'] >= date_range[0]) & (filtered_all_management_expenses_df['date'] <= date_range[1])]
    with col_category_type:
        category_type = st.multiselect("Select a category type", ['All'] + sorted(list(filtered_all_management_expenses_df['category_type'].unique())), default='All')
        if 'All' not in category_type:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['category_type'].isin(category_type)]
   
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
    with col_market:
        market_options = list(filtered_all_management_expenses_df['market'].unique())
        market_sorted = sorted(market_options, key=lambda x: (pd.isna(x), str(x).lower()))
        selected_markets = st.multiselect("Select a market", ['All'] + sorted(market_options, key=lambda x: (pd.isna(x), str(x).lower())), default='All')
        if 'All' not in selected_markets:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['market'].isin(selected_markets)]


    return filtered_all_management_expenses_df


def buildium_spend_over_time(all_management_expenses_df):
    st.subheader("Buildium Spend Over Time")

    # customize view specifications
    col_time_granularity, col_dimension = st.columns(2)
    with col_time_granularity:
        time_granularity_dict = {
            'Week': 'week_end',
            'Month': 'month_end'
        }
        selected_time_granularity = st.selectbox("Select a time granularity", time_granularity_dict.keys(), key='buildium_spend_time_granularity')
        st.session_state["time_granularity"] = time_granularity_dict[selected_time_granularity]
    with col_dimension:
        category_dict = {
            'GL Account': 'gl_account',
            'Vendor': 'vendor',
            'Fund': 'fund',
            'Market': 'market'
        }
        selected_dimension = st.selectbox("Select a dimension", category_dict.keys())
        st.session_state["category"] = category_dict[selected_dimension]

    # group, pivot & format data
    grouped_management_expenses_df = (
        all_management_expenses_df
        .groupby([st.session_state["time_granularity"], st.session_state["category"]], dropna=False)
        .agg(total_amount=('amount', 'sum'))
        .reset_index()
    )
    pivot_df = grouped_management_expenses_df.pivot(
        index=st.session_state["category"],
        columns=st.session_state["time_granularity"],
        values='total_amount'
    ).fillna(0).reset_index()
    pivot_df['Total'] = pivot_df.select_dtypes(include=[np.number]).sum(axis=1)
    pivot_df = pivot_df.sort_values(by='Total', ascending=False).reset_index(drop=True)
    
    # display dataframe with selection
    event = st.dataframe(
        pivot_df, 
        on_select='rerun', 
        selection_mode=['multi-row', 'multi-column'], 
        hide_index=True,
        column_config={
            **{col: st.column_config.NumberColumn(format="dollar") 
               for col in pivot_df.columns 
               if col != st.session_state["category"]}
        }
    )
    st.caption(
        "<p style='text-align: right;'>Select multiple rows (checkboxes) and/or columns (cmd⌘ - click) to filter the line items table below</p>",
        unsafe_allow_html=True
    )
    selected_info = event['selection']
    if len(selected_info['rows']):
        st.session_state["category_filter"] = pivot_df.loc[selected_info['rows'], st.session_state["category"]]
        
    else:
        st.session_state["category_filter"] = None
    if len(selected_info['columns']):
        st.session_state["time_granularity_filter"] = selected_info['columns']
    else:
        st.session_state["time_granularity_filter"] = None


def buildium_spend_line_items(all_management_expenses_df):
    st.subheader("Line Items", help="Filter by selecting rows and/or columns in the Buildium Spend Over Time table above")
    line_items_df = all_management_expenses_df.copy()

    if ("time_granularity_filter" in st.session_state) and (st.session_state["time_granularity_filter"] is not None):
        line_items_df = line_items_df[line_items_df[st.session_state["time_granularity"]].isin(st.session_state["time_granularity_filter"])]
    if ("category_filter" in st.session_state) and (st.session_state["category_filter"] is not None):
        line_items_df = line_items_df[line_items_df[st.session_state["category"]].isin(st.session_state["category_filter"])]

    line_items_cols = [
        'date',
        'gl_account',
        'category_group',
        'category_type',
        'address',
        'fund',
        'market',
        'vendor',
        'description',
        'amount'
        # 'accounting_property_name',
        # 'state',
        # 'entity',
        # 'gl_account_id',
        # 'gl_account_number',
        # 'gl_account_name',
        # 'transaction_id',
        # 'transaction_type',
        # 'payment_type',
        # 'memo',
        # 'category',
        # 'supercategory',
        # 'subcategory',
        # 'cashflow_type',
        # 'vendor_id',
        # 'vendor_contact_name',
        # 'vendor_company_name',
        # 'vendor_primary_phone',
        # 'vendor_primary_email',
        # 'is_uuid',
        # 'source',
        # 'date_time',
        # 'week_end',
        # 'month_end'
    ]
    def color_category(val):
        if val == 'R&M':
            return f'color: {TEAL}'  # teal
        elif val == 'Capex':
            return f'color: {PURPLE}'  # purple
        elif val == 'Common Area Maintenance':
            return f'color: {PINK}'  # pink

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
            'date': st.column_config.DateColumn(pinned=True),
            'gl_account': st.column_config.TextColumn(pinned=True),
            'category_group': st.column_config.TextColumn(pinned=True,),
            'category_type': st.column_config.TextColumn(pinned=True),
            'amount': st.column_config.NumberColumn(format="dollar"), 
        }
    )


