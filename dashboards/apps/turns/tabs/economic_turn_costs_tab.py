import streamlit as st


def economic_turn_costs(turns_df):
    st.subheader("Economic Turn Costs")
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
        'project_estimated_cost',
        'project_ticket_approved_budgets', 
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
    economic_turn_costs_df.columns = [col.replace('_', ' ').title() for col in economic_turn_costs_df.columns]
    st.dataframe(economic_turn_costs_df, hide_index=True)

