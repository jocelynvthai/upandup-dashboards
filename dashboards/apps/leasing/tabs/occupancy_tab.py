import streamlit as st
import pandas as pd
from datetime import datetime


def occupancy_filters(projected_economic_occupancy_df, budget_economic_occupancy_df):
    selected_fund = st.selectbox("Select a fund", ['All'] + list(projected_economic_occupancy_df['fund'].unique()))
    if selected_fund != 'All':
        filtered_projected_economic_occupancy_df = projected_economic_occupancy_df[projected_economic_occupancy_df['fund'] == selected_fund]
        filtered_budget_economic_occupancy_df = budget_economic_occupancy_df[budget_economic_occupancy_df['fund'] == selected_fund]
    else:
        filtered_projected_economic_occupancy_df = projected_economic_occupancy_df
        filtered_budget_economic_occupancy_df = budget_economic_occupancy_df
    
    return filtered_projected_economic_occupancy_df, filtered_budget_economic_occupancy_df, selected_fund


def occupancy_metrics(projected_economic_occupancy_df, budget_economic_occupancy_df):
    economic_occupancy_col, physical_occupancy_col = st.columns(2)
    today_occupancy = projected_economic_occupancy_df[projected_economic_occupancy_df['date'] == datetime.now()]
    with economic_occupancy_col:
        st.metric("Economic Occupancy", 
                  f"{round(today_occupancy['total_gpr_not_vacant'].sum() * 100 / today_occupancy['total_gpr'].sum(), 2)}%", 
                  help="Today's Rent Charged / Today's GPR")
    with physical_occupancy_col:
        st.metric("Physical Occupancy", 
                  f"{round(today_occupancy['num_properties_not_vacant'].sum() * 100 / today_occupancy['num_properties'].sum(), 2)}%", 
                  help="\# Homes Occupied / \# Homes")


def occupancy_targets():
    st.subheader("Occupancy Targets")
