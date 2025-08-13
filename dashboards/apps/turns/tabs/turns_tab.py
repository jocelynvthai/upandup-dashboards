import streamlit as st


def turns(turns_df):
    turns_df_display = turns_df[[
        'address', 
        'state', 
        'fund', 
        'occupancy_date',
        'move_out_date', 
        'lease_end_reason',
        'project_types', 
        'project_start_date', 
        'project_end_date', 
        'project_estimated_cost',
        'project_invoiced_cost',
        'chargeback_amount',
        'clawback_amount',
        'cashout_status',
        'tour_ready_date',
        'rent_ready_date',
        'next_occupancy_date', 
        'occupancy_inspection_start_date', 
        'occupancy_inspection_end_date', 
        'occupancy_inspection_estimated_cost', 
        'occupancy_inspection_count', 
        'occupancy_inspection_status', 
        'occupancy_inspection_result', 
        'occupancy_inspection_at', 
        'buyers_inspection_start_date', 
        'buyers_inspection_end_date', 
        'buyers_inspection_estimated_cost', 
        'total_invoiced_cost_before_move_out', 
        'total_invoiced_cost_during_vacancy', 
        'total_invoiced_cost_after_move_in'
    ]].copy()
    turns_df_display.columns = [col.replace('_', ' ').title() for col in turns_df_display.columns]
    st.dataframe(turns_df_display)

