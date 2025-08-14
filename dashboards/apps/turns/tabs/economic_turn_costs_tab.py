import streamlit as st

def economic_turn_costs_filters(turns_df):
    col_address, col_fund, col_types = st.columns(3)


    filtered_turns_df = turns_df.copy()
    with col_address:
        selected_address = st.selectbox("Select Address", ['All'] + list(turns_df['address'].unique()))
        if selected_address != 'All':
            filtered_turns_df = turns_df[turns_df['address'] == selected_address]
    with col_fund:
        selected_fund = st.selectbox("Select Fund", ['All'] + list(turns_df['fund'].unique()))
        if selected_fund != 'All':
            filtered_turns_df = filtered_turns_df[filtered_turns_df['fund'] == selected_fund]
    with col_types:
        selected_types = st.selectbox("Select Types", ['All'] + ['rehab', 'turn', 'turn_oi', 'disposition', 'disposition_inspection', 'disposition_oi'])
        if selected_types != 'All':
            filtered_turns_df = filtered_turns_df[filtered_turns_df['project_types'].str.contains(selected_types)]

    return filtered_turns_df


def economic_turn_costs(turns_df):
    st.subheader("Economic Turn Costs")

    turns_df['project_budget'] = turns_df.apply(
        lambda row: row['project_estimated_cost'] if row['fund'] == 'Homevest Real Estate Partners IV - Limestone, L.P.' 
        else row['project_estimated_cost'] + row['project_ticket_approved_budgets'], 
        axis=1
    )
    
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
        # 'project_estimated_cost',
        # 'project_ticket_approved_budgets', 
        'project_budget', 
        'project_invoiced_cost',
        'last_invoice_date',
        'last_change_order_date', 
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

    economic_turn_costs_df.columns = [
        col.replace('project_', '').replace('_', ' ').title() if col.startswith('project_') 
        else col.replace('_', ' ').title() 
        for col in economic_turn_costs_df.columns
    ]

    # Add a column for the button/link
    economic_turn_costs_df['Drilldown'] = economic_turn_costs_df.apply(
        lambda row: f"individual_turn_drilldown?address={row['Address']}&move_out_date={row['Move Out Date']}", axis=1
    )


    st.data_editor(
        economic_turn_costs_df,
        column_config={
            "Address": st.column_config.TextColumn(
                pinned=True,
            ),
            "Drilldown": st.column_config.LinkColumn(
                display_text='↪',
                pinned=True,
            )
        },
        # hide_index=True,
    )



