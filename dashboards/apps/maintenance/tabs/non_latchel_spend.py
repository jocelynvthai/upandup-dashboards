import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

from data import bills_tickets_invoices_data

def non_latchel_spend_data_clean(bills_tickets_invoices_df):
    cleaned_bills_tickets_invoices_df = bills_tickets_invoices_df[bills_tickets_invoices_df['latchel_invoice_id'].isna()].copy()

    # week & month end dates
    cleaned_bills_tickets_invoices_df['date_time'] = pd.to_datetime(cleaned_bills_tickets_invoices_df['date'])
    cleaned_bills_tickets_invoices_df['week_end'] = (cleaned_bills_tickets_invoices_df['date_time'] + pd.to_timedelta(6 - cleaned_bills_tickets_invoices_df['date_time'].dt.weekday, unit='d')).dt.strftime('%Y-%m-%d')
    cleaned_bills_tickets_invoices_df['month_end'] = (cleaned_bills_tickets_invoices_df['date_time'] + pd.offsets.MonthEnd(0)).dt.strftime('%Y-%m-%d')

    # vendor
    cleaned_bills_tickets_invoices_df['vendor_company'] = (
        cleaned_bills_tickets_invoices_df['vendor_company'] 
        .apply(lambda x: x.strip() if isinstance(x, str) else x)
        .replace([None, '', 'None', 'nan', 'NaN'], np.nan)         
    )
    cleaned_bills_tickets_invoices_df['vendor_name'] = (
        cleaned_bills_tickets_invoices_df['vendor_name']
        .apply(lambda x: x.strip() if isinstance(x, str) else x)
        .replace([None, '', 'None', 'nan', 'NaN'], np.nan)
    )
    cleaned_bills_tickets_invoices_df['vendor'] = np.select(
        [
            cleaned_bills_tickets_invoices_df['vendor_name'].notna() & cleaned_bills_tickets_invoices_df['vendor_company'].notna(),
            cleaned_bills_tickets_invoices_df['vendor_name'].notna() & cleaned_bills_tickets_invoices_df['vendor_company'].isna(),
            cleaned_bills_tickets_invoices_df['vendor_name'].isna() & cleaned_bills_tickets_invoices_df['vendor_company'].notna(),
        ],
        [
            cleaned_bills_tickets_invoices_df['vendor_company'] + ' (' + cleaned_bills_tickets_invoices_df['vendor_name'] + ')', 
            '(' + cleaned_bills_tickets_invoices_df['vendor_name'] + ')', 
            cleaned_bills_tickets_invoices_df['vendor_company'],
        ],
        default=' (No vendor)'
    )
    return cleaned_bills_tickets_invoices_df



def non_latchel_spend_filters(credentials):
    # filters
    col_date_range, col_vendor = st.columns(2)
    with col_date_range:
        date_range = st.date_input("Pick a period range", 
                            value=(datetime.now() - timedelta(days=30),  datetime.now()), 
                            format='MM/DD/YYYY',
                            help="The period range to filter the data type selected",
                            key='non_latchel_spend_date_range')
        if len(date_range) != 2:
            st.stop()
        else:
            bills_tickets_invoices_df = bills_tickets_invoices_data(credentials, date_range[0], date_range[1])
            filtered_bills_tickets_invoices_df = non_latchel_spend_data_clean(bills_tickets_invoices_df)
    with col_vendor:
        vendor_options = list(filtered_bills_tickets_invoices_df['vendor'].unique())
        vendor_sorted = sorted(vendor_options, key=lambda x: (pd.isna(x), str(x).lower()))
        selected_vendors = st.multiselect("Select a vendor", ['All'] + vendor_sorted, default='All')
        if 'All' not in selected_vendors:
            filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[filtered_bills_tickets_invoices_df['vendor'].isin(selected_vendors)]

    # fund filter
    all_funds = filtered_bills_tickets_invoices_df['funds'].apply(
        lambda x: re.split(r', (?!(?:L\.P\.|LLC))', x)
    ).explode().unique()
    selected_funds = st.multiselect("Select a fund", ['All'] + sorted(list(all_funds)), default='All', key='non_latchel_spend_fund')
    if 'All' not in selected_funds:
        # Keep rows where any selected fund is in the 'funds' string
        filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[
            filtered_bills_tickets_invoices_df['funds'].apply(
                lambda x: any(fund in x for fund in selected_funds)
            )
        ]

    return filtered_bills_tickets_invoices_df


def non_latchel_spend(bills_tickets_invoices_df):
    st.subheader("Non-Latchel Spend Over Time")

    # customize view specifications
    time_granularity_dict = {
        'Week': 'week_end',
        'Month': 'month_end'
    }
    selected_time_granularity = st.selectbox("Select a time granularity", time_granularity_dict.keys(), key='non_latchel_spend_time_granularity')
    st.session_state["time_granularity"] = time_granularity_dict[selected_time_granularity]

    # group, pivot & format data
    grouped_bills_tickets_invoices_df = (
        bills_tickets_invoices_df
        .groupby([st.session_state["time_granularity"]], dropna=False)
        .agg(buildium_bill_spend=('total_bill_amount', 'sum'))
        .reset_index()
    )
    
    # display dataframe with selection
    event = st.dataframe(
        grouped_bills_tickets_invoices_df, 
        on_select='rerun', 
        selection_mode=['single-row'], 
        hide_index=True,
        column_config={
            **{col: st.column_config.NumberColumn(format="dollar") 
               for col in grouped_bills_tickets_invoices_df.columns 
               if col != st.session_state["time_granularity"]}
        }
    )
    selected_info = event['selection']
    if len(selected_info['rows']):
        st.session_state["time_granularity_filter"] = grouped_bills_tickets_invoices_df.loc[selected_info['rows'][0], st.session_state["time_granularity"]]
    else:
        st.session_state["time_granularity_filter"] = None



def non_latchel_spend_bills(bills_tickets_invoices_df):
    st.subheader("Non-Latchel Spend Line Items")
    bills_df = bills_tickets_invoices_df.copy()

    if ("time_granularity_filter" in st.session_state) and (st.session_state["time_granularity_filter"] is not None):
        bills_df = bills_df[bills_df[st.session_state["time_granularity"]] == st.session_state["time_granularity_filter"]]

    columns = [
        'date', 
        'due_date', 
        'paid_date', 
        'addresses', 
        'vendor', 
        'description', 
        'total_bill_amount', 
         # 'id', 
        # 'vendor_id', 
        # 'vendor_name', 
        # 'vendor_company', 
        # 'spend_categories', 
        # 'gl_account_names', 
        # 'funds', 
        # 'properties', 
        # 'bill_source', 
        # 'latchel_invoice_id', 
        # 'address', 
        # 'market', 
        # 'fund', 
        # 'entity', 
        # 'invoice_date', 
        # 'invoice_description', 
        # 'invoice_total_amount', 
        # 'latchel_vendor_name', 
        # 'ticket_title', 
        # 'ticket_description', 
        # 'ticket_actual_start_date', 
        # 'ticket_planned_start_date', 
        # 'ticket_estimated_cost', 
        # 'ticket_actual_cost', 
        # 'ticket_max_cost', 
        # 'ticket_date', 
        # 'date_time', 
        # 'week_end', 
        # 'month_end', 
    ]

    st.dataframe(
        bills_df[columns].sort_values(by='date'), 
        hide_index=True,
        column_config={
            'date': st.column_config.DateColumn(pinned=True),
            'due_date': st.column_config.DateColumn(pinned=True),
            'paid_date': st.column_config.DateColumn(pinned=True),
            'addresses': st.column_config.TextColumn(pinned=True),
            'total_bill_amount': st.column_config.NumberColumn(format="dollar"),
        }
    )

    