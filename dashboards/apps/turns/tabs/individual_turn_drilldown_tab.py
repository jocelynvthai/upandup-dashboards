import pandas as pd
import streamlit as st

DELIMITER = ' -- moved out '
NULL_VALUE = "N/A"
  

def drilldown_filters(turns_df, line_items_df):
    params = st.query_params 

    distinct_turns = turns_df['address'] + DELIMITER + turns_df['move_out_date'].astype(str)
    sorted_turns = sorted(distinct_turns, key=lambda x: x.split(DELIMITER)[1], reverse=True)
    if params:
        default_index = sorted_turns.index(params.get('address', [None]) + DELIMITER + params.get('move_out_date', [None]))
    else:
        default_index = 0
    selected_turn = st.selectbox("Select Turnover Period", sorted_turns, index=default_index).split(DELIMITER)

    rental_id = turns_df[
        (turns_df['address'] == selected_turn[0]) & 
        (turns_df['move_out_date'].astype(str) == selected_turn[1])
    ]['rental_id'].values[0]

    filtered_line_items_df = line_items_df[(line_items_df['rental_id'] == rental_id)]
    # filtered_turns_df will only be one row
    filtered_turns_df = turns_df[(turns_df['rental_id'] == rental_id)]
    return filtered_line_items_df, filtered_turns_df



def individual_turn_summary(filtered_line_items_df, filtered_turns_df):
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
    turn = filtered_turns_df.iloc[0]
    with col1:
        st.metric("Billed Cost", f"${filtered_line_items_df['amount'].sum():,.2f}")
    with col2:
        project_estimated_cost = turn['project_estimated_cost'] if not pd.isnull(turn['project_estimated_cost']) else 0
        ticket_approved_budgets = turn['project_ticket_approved_budgets'] if not pd.isnull(turn['project_ticket_approved_budgets']) else 0
        estimated_cost = project_estimated_cost
        if turn['fund'] != 'Homevest Real Estate Partners IV - Limestone, L.P.':
            estimated_cost += ticket_approved_budgets
        st.metric("Estimated Cost", f"${estimated_cost:,.2f}")
    with col3:
        st.metric("Move-Out Date", f"{turn['move_out_date']:%m/%d/%y}")
    with col4:
        col4_title = "Scoped Date"
        project_scoped_date = turn['project_scoped_date']
        if not pd.isnull(project_scoped_date):
          st.metric(col4_title, f"{project_scoped_date:%m/%d/%y}")
        else:
          st.metric(col4_title, NULL_VALUE)
    with col5:
        col5_title = "Scope Approved Date"
        project_scope_approved_date = turn['project_scope_approved_date']
        if not pd.isnull(project_scoped_date):
          st.metric(col5_title, f"{project_scope_approved_date:%m/%d/%y}")
        else:
          st.metric(col5_title, NULL_VALUE)
    with col6:
        col6_title = "Finished QC Date"
        project_finished_qc_date = turn['project_finished_qc_date']
        if not pd.isnull(project_finished_qc_date):
          st.metric(col6_title, f"{project_finished_qc_date:%m/%d/%y}")
        else:
          st.metric(col6_title, NULL_VALUE)
    with col7:
        col7_title = "Tour Ready Date"
        tour_ready_date = turn['tour_ready_date']
        if not pd.isnull(tour_ready_date):
          st.metric(col7_title, f"{tour_ready_date:%m/%d/%y}")
        else:
          st.metric(col7_title, NULL_VALUE)
    with col8:
        col8_title = "Rent Ready Date"
        rent_ready_date = turn['rent_ready_date']
        if not pd.isnull(rent_ready_date):
          st.metric(col8_title, f"{rent_ready_date:%m/%d/%y}")
        else:
          st.metric(col8_title, NULL_VALUE)
    with col9:
        col9_title = "Move-In Date"
        move_in_date = turn['next_occupancy_date']
        if not pd.isnull(move_in_date):
          st.metric(col9_title, f"{move_in_date:%m/%d/%y}")
        else:
          st.metric(col9_title, NULL_VALUE)


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
                format="M/DD/YYYY"
            ),
            'Amount': st.column_config.NumberColumn(
                width=1,
                format="accounting"
            ),
            'Memo': st.column_config.LinkColumn()
        }
    )
