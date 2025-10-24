import streamlit as st
# import pandas as pd
# import altair as alt
from datetime import datetime, timedelta

def latchel_spend_filters(bills_tickets_invoices_df):
    filtered_bills_tickets_invoices_df = bills_tickets_invoices_df.copy()

    col_date_type, col_date_range, col_spend_category, col_gl_account_name = st.columns(4)

    with col_date_type:
        date_type = st.selectbox("Select a date type", ['Buildium bill date', 'Latchel work order date'])
    with col_date_range:
        date_range = st.date_input("Pick a period range", 
                                value=(datetime.now() - timedelta(days=30),  datetime.now()), 
                                format='MM/DD/YYYY',
                                key='latchel_spend_date_range')
        if len(date_range) != 2:
            st.stop()
        else:
            start_date, end_date = date_range[0], date_range[1]
            if date_type == 'Buildium bill date':
                filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[(filtered_bills_tickets_invoices_df['date'] >= start_date) & (filtered_bills_tickets_invoices_df['date'] <= end_date)]
            elif date_type == 'Latchel work order date':
                filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[(filtered_bills_tickets_invoices_df['ticket_date'] >= start_date) & (filtered_bills_tickets_invoices_df['ticket_date'] <= end_date)]
    with col_spend_category:
        spend_category = st.selectbox("Select a spend category", ['All'] + sorted(filtered_bills_tickets_invoices_df['spend_categories'].str.split(', ').explode().unique()))
        if spend_category != 'All':
            filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[filtered_bills_tickets_invoices_df['spend_categories'].str.contains(spend_category)]
    with col_gl_account_name:
        gl_account_name = st.selectbox("Select a GL account name", ['All'] + sorted(filtered_bills_tickets_invoices_df['gl_account_names'].str.split(', ').explode().unique()))
        if gl_account_name != 'All':
            filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[filtered_bills_tickets_invoices_df['gl_account_names'].str.contains(gl_account_name)]
    
    col_fund, col_vendor_company, col_vendor_name = st.columns(3)
    with col_fund:
        fund = st.selectbox("Select a fund", ['All'] + sorted([f for f in filtered_bills_tickets_invoices_df['fund'].unique() if f is not None]))
        if fund != 'All':
            filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[filtered_bills_tickets_invoices_df['fund'] == fund]
    with col_vendor_company:
        vendor_company = st.selectbox("Select a vendor company", ['All'] + sorted([f for f in filtered_bills_tickets_invoices_df['vendor_company'].unique() if f is not None]))
        if vendor_company != 'All':
            filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[filtered_bills_tickets_invoices_df['vendor_company'] == vendor_company]
    with col_vendor_name:
        vendor_name = st.selectbox("Select a vendor name", ['All'] + sorted([f for f in filtered_bills_tickets_invoices_df['vendor_name'].unique() if f is not None]))
        if vendor_name != 'All':
            filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[filtered_bills_tickets_invoices_df['vendor_name'] == vendor_name]
    
    return filtered_bills_tickets_invoices_df

def latchel_spend(bills_tickets_invoices_df):
    st.subheader("Latchel Spend")
    st.dataframe(bills_tickets_invoices_df)

    