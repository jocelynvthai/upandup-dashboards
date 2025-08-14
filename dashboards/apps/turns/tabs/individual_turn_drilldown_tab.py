import pandas as pd
import streamlit as st

DELIMITER = ' -- moved out '
NULL_VALUE = "N/A"
LIMESTONE_FUND = 'Homevest Real Estate Partners IV - Limestone, L.P.'


def drilldown_filters(turns_df, line_items_df):
    params = st.query_params
    distinct_turns = turns_df['address'] + DELIMITER + turns_df['move_out_date'].astype(str)
    sorted_turns = sorted(distinct_turns, key=lambda x: x.split(DELIMITER)[1], reverse=True)
    if params:
        default_index = sorted_turns.index(params.get('address', [None]) + DELIMITER + params.get('move_out_date', [None]))
    else:
        default_index = 0

    with st.container():
        turn_dropdown = st.selectbox("Select a Rental", sorted_turns, width=600, index=default_index)
        selected_value = turn_dropdown.split(DELIMITER)
        rental_id = turns_df[
            (turns_df['address'] == selected_value[0]) & 
            (turns_df['move_out_date'].astype(str) == selected_value[1])
        ]['rental_id'].values[0]
        filtered_line_items_df = line_items_df[(line_items_df['rental_id'] == rental_id)]

        # note that filtered_turns_df will only ever be one row
        filtered_turns_df = turns_df[(turns_df['rental_id'] == rental_id)]
        selected_turn = filtered_turns_df.iloc[0]
        st.markdown(f'**Project Type(s)**: {selected_turn["project_types"]}')
        return filtered_line_items_df, selected_turn


def cost_container(
    total_estimated_cost,
    total_invoiced_cost,
    project_estimated_cost,
    oi_estimated_cost,
    ticket_approved_budgets,
    fund,
    project_types
):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Budget", f"${total_estimated_cost:,.2f}")
    with col2:
        st.metric("Billed Cost", f"${total_invoiced_cost:,.2f}")
    with st.container(width=600):
        st.markdown("##### Budget Breakdown")
        budget_data = pd.DataFrame({ "Source": ["Main Project(s)"], "Budgeted Amount": [project_estimated_cost] })
        if "_oi" in project_types.lower():
            budget_data = pd.concat([
                budget_data,
                pd.DataFrame([["Occupancy Inspection", oi_estimated_cost]], columns=budget_data.columns)
            ])
        if ticket_approved_budgets > 0 and fund != LIMESTONE_FUND:
            budget_data = pd.concat([
                budget_data,
                pd.DataFrame([["Approved Latchel Tickets", ticket_approved_budgets]], columns=budget_data.columns)
            ])
        st.dataframe(budget_data, hide_index=True, column_config={
            "Budgeted Amount": st.column_config.NumberColumn(format="accounting")
        })


def timeline_container(selected_turn):
    st.markdown("##### Timeline")
    col3, col4, col5, col6 = st.columns(4)
    with col3:
        st.metric("Move-Out Date", f"{selected_turn['move_out_date']:%m/%d/%y}")
    with col4:
        col4_title = "Scoped Date"
        project_scoped_date = selected_turn['project_scoped_date']
        if not pd.isnull(project_scoped_date):
            st.metric(col4_title, f"{project_scoped_date:%m/%d/%y}")
        else:
            st.metric(col4_title, NULL_VALUE)
    with col5:
        col5_title = "Scope Approved Date"
        project_scope_approved_date = selected_turn['project_scope_approved_date']
        if not pd.isnull(project_scoped_date):
            st.metric(col5_title, f"{project_scope_approved_date:%m/%d/%y}")
        else:
            st.metric(col5_title, NULL_VALUE)

    col7, col8, col9 = st.columns(spec=3, width=1090)
    with col6:
        col6_title = "Finished QC Date"
        project_finished_qc_date = selected_turn['project_finished_qc_date']
        if not pd.isnull(project_finished_qc_date):
            st.metric(col6_title, f"{project_finished_qc_date:%m/%d/%y}")
        else:
            st.metric(col6_title, NULL_VALUE)
    with col7:
        col7_title = "Tour Ready Date"
        tour_ready_date = selected_turn['tour_ready_date']
        if not pd.isnull(tour_ready_date):
            st.metric(col7_title, f"{tour_ready_date:%m/%d/%y}")
        else:
            st.metric(col7_title, NULL_VALUE)
    with col8:
        col8_title = "Rent Ready Date"
        rent_ready_date = selected_turn['rent_ready_date']
        if not pd.isnull(rent_ready_date):
            st.metric(col8_title, f"{rent_ready_date:%m/%d/%y}")
        else:
            st.metric(col8_title, NULL_VALUE)
    with col9:
        col9_title = "Move-In Date"
        move_in_date = selected_turn['next_occupancy_date']
        if not pd.isnull(move_in_date):
            st.metric(col9_title, f"{move_in_date:%m/%d/%y}")
        else:
            st.metric(col9_title, NULL_VALUE)


def individual_turn_summary(filtered_line_items_df, selected_turn):
    # Extract & format some values from the selected turn
    fund = selected_turn['fund']
    project_types = selected_turn['project_types']
    project_estimated_cost = selected_turn['project_estimated_cost'] if not pd.isnull(selected_turn['project_estimated_cost']) else 0
    oi_estimated_cost = selected_turn['occupancy_inspection_estimated_cost'] if not pd.isnull(selected_turn['occupancy_inspection_estimated_cost']) else 0
    ticket_approved_budgets = selected_turn['project_ticket_approved_budgets'] if not pd.isnull(selected_turn['project_ticket_approved_budgets']) else 0
    total_estimated_cost = project_estimated_cost + oi_estimated_cost
    if fund != LIMESTONE_FUND:
        total_estimated_cost += ticket_approved_budgets
    total_invoiced_cost = filtered_line_items_df['amount'].sum()

    with st.container(horizontal=True):
        with st.container(border=True, width=600):
            cost_container(
                total_estimated_cost,
                total_invoiced_cost,
                project_estimated_cost,
                oi_estimated_cost,
                ticket_approved_budgets,
                fund,
                project_types
            )
        with st.container(border=True):
            timeline_container(selected_turn)


def individual_turn_drilldown(filtered_line_items_df):
    st.subheader("Line Items")
    output_df = filtered_line_items_df[[
        'date',
        'amount',
        'gl_account_name',
        'memo',
        'description',
        'vendor_contact_name',
        'vendor_company_name'
    ]].copy()
    output_df = output_df.sort_values(by='date', ascending=False)
    output_df.columns = [col.replace('_', ' ').title() for col in output_df.columns]
    st.dataframe(
        output_df,
        hide_index=True,
        column_config={
            'Date': st.column_config.DateColumn(
                width=1,
                format="M/D/YY"
            ),
            'Amount': st.column_config.NumberColumn(
                width=1,
                format="accounting"
            ),
            'Memo': st.column_config.LinkColumn()
        }
    )
