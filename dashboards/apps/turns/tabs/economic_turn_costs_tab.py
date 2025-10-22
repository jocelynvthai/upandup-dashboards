import streamlit as st
import pandas as pd

from tabs.utils import TEAL

def economic_turn_costs_filters(turns_df):
    col_fund, col_types, col_address = st.columns(3)

    filtered_turns_df = turns_df.copy()
    with col_fund:
        selected_fund = st.selectbox("Select Fund", ['All'] + list(turns_df['fund'].unique()))
        if selected_fund != 'All':
            filtered_turns_df = filtered_turns_df[filtered_turns_df['fund'] == selected_fund]
    with col_types:
        selected_types = st.selectbox("Select Types", ['All'] + list(filtered_turns_df['project_types'].str.split(', ').explode().unique()))
        if selected_types != 'All':
            filtered_turns_df = filtered_turns_df[filtered_turns_df['project_types'].str.contains(selected_types)]
    with col_address:
        selected_address = st.selectbox("Select Address", ['All'] + list(filtered_turns_df['address'].unique()))
        if selected_address != 'All':
            filtered_turns_df = filtered_turns_df[filtered_turns_df['address'] == selected_address]

    return filtered_turns_df


def economic_turn_costs(turns_df):
    st.subheader("Economic Turn Costs")

    turns_df['project_budget'] = turns_df['project_estimated_cost']

    turns_df['project_end_date'] = pd.to_datetime(turns_df['project_end_date']).dt.strftime('%Y-%m-%d')
    turns_df['last_change_order_date'] = pd.to_datetime(turns_df['last_change_order_date']).dt.strftime('%Y-%m-%d')

    economic_turn_costs_df = turns_df[[
        'address', 
        'state', 
        'fund', 
        'occupancy_date',
        'move_out_date', 
        'lease_end_reason',
        'project_types', 
        'project_start_date', 
        'project_end_date', 
        'project_scoped_date', 
        'project_scope_approved_date', 
        'project_finished_qc_date',
        'project_total_estimated_cost', 
        'project_estimated_cost',
        'project_invoiced_cost',
        'last_invoice_date',
        'last_change_order_date', 
        'chargeback_amount',
        'clawback_amount',
        'cashout_status',
        'tour_ready_date',
        'rent_ready_date',
        'next_occupancy_date', 
        'occupancy_inspection_project_start_date', 
        'occupancy_inspection_project_end_date', 
        'occupancy_inspection_estimated_cost', 
        'occupancy_inspection_count', 
        'most_recent_occupancy_inspection_at', 
        'most_recent_occupancy_inspection_status', 
        'most_recent_occupancy_inspection_result', 
        'buyers_inspection_start_date', 
        'buyers_inspection_end_date', 
        'buyers_inspection_estimated_cost', 
        'total_invoiced_cost_before_move_out', 
        'total_invoiced_cost_during_vacancy', 
        'total_invoiced_cost_after_move_in'
    ]].copy()

    economic_turn_costs_df.columns = [
        col.replace('project_', '').replace('_', ' ').title() if col.startswith('project_') 
        else col.replace('_', ' ').title() 
        for col in economic_turn_costs_df.columns
    ]

    # Add a column for the button/link
    economic_turn_costs_df['Drilldown'] = economic_turn_costs_df.apply(
        lambda row: f"individual_turn_drilldown?address={row['Address']}&move_out_date={row['Move Out Date']}", axis=1
    ).astype(str)

    st.data_editor(
        economic_turn_costs_df,
        column_config={
            "Address": st.column_config.TextColumn(
                pinned=True,
            ),
            "Drilldown": st.column_config.LinkColumn(
                display_text=":material/link:",
                pinned=True
            )
        }
    )





