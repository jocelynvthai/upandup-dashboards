import streamlit as st
# import pandas as pd
# import altair as alt
from datetime import datetime, timedelta

def latchel_spend_filters(bills_tickets_invoices_df):
    filtered_bills_tickets_invoices_df = bills_tickets_invoices_df.copy()

    col_date_type, col_date_range = st.columns(2)
    with col_date_type:
        date_type = st.selectbox("Select a date type", ['Buildium bill date', 'Latchel work order date'],
                                help="""**Buildium bill date** – the date the bill was issued  
                                **Latchel work order date** – the actual start date (planned start date if actual start date is not available) of the work order""")
    with col_date_range:
        date_range = st.date_input("Pick a period range", 
                                value=(datetime.now() - timedelta(days=30),  datetime.now()), 
                                format='MM/DD/YYYY',
                                help="The period range to filter the data type selected",
                                key='latchel_spend_date_range')
        if len(date_range) != 2:
            st.stop()
        else:
            start_date, end_date = date_range[0], date_range[1]
            if date_type == 'Buildium bill date':
                filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[(filtered_bills_tickets_invoices_df['date'] >= start_date) & (filtered_bills_tickets_invoices_df['date'] <= end_date)]
            elif date_type == 'Latchel work order date':
                filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[(filtered_bills_tickets_invoices_df['ticket_date'] >= start_date) & (filtered_bills_tickets_invoices_df['ticket_date'] <= end_date)]
    

    fund = st.multiselect("Select a fund", ['All'] + sorted([f for f in filtered_bills_tickets_invoices_df['fund'].unique() if f is not None]), default=['All'])
    if 'All' not in fund:
        pattern = '|'.join(fund)
        filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[filtered_bills_tickets_invoices_df['fund'].str.contains(pattern,  na=False)]

    col_gl_account_name, col_spend_category = st.columns(2)
    with col_gl_account_name:
        gl_account_name = st.multiselect("Select a GL account name", ['All'] + sorted(filtered_bills_tickets_invoices_df['gl_account_names'].str.split(', ').explode().unique()), default=['All'])
        if 'All' not in gl_account_name:
            pattern = '|'.join(gl_account_name)
            filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[filtered_bills_tickets_invoices_df['gl_account_names'].str.contains(pattern,  na=False)]
    with col_spend_category:
        spend_category = st.multiselect("Select a spend category", ['All'] + sorted(filtered_bills_tickets_invoices_df['spend_categories'].str.split(', ').explode().unique()), default=['All'])
        if 'All' not in spend_category:
            pattern = '|'.join(spend_category)
            filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[filtered_bills_tickets_invoices_df['spend_categories'].str.contains(pattern,  na=False)]

    col_vendor_company, col_vendor_name = st.columns(2)
    with col_vendor_company:
        vendor_company = st.multiselect("Select a vendor company", ['All'] + sorted([f for f in filtered_bills_tickets_invoices_df['vendor_company'].unique() if f is not None]), default=['All'])
        if 'All' not in vendor_company:
            pattern = '|'.join(vendor_company)
            filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[filtered_bills_tickets_invoices_df['vendor_company'].str.contains(pattern,  na=False)]
    with col_vendor_name:   
        vendor_name = st.multiselect("Select a vendor name", ['All'] + sorted([f for f in filtered_bills_tickets_invoices_df['vendor_name'].unique() if f is not None]), default=['All'])
        if 'All' not in vendor_name:
            pattern = '|'.join(vendor_name)
            filtered_bills_tickets_invoices_df = filtered_bills_tickets_invoices_df[filtered_bills_tickets_invoices_df['vendor_name'].str.contains(pattern,  na=False)]
    
    return filtered_bills_tickets_invoices_df

def latchel_spend(bills_tickets_invoices_df):
    st.subheader("Latchel Spend")
    st.dataframe(bills_tickets_invoices_df)

    