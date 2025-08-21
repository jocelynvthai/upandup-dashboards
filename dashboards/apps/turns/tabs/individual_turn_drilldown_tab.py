import pandas as pd
import streamlit as st
from streamlit_timeline import st_timeline

from tabs.utils import TEAL


DELIMITER = ' -- moved out '
NULL_VALUE = "N/A"


def drilldown_filters(turns_df, construction_scopes_df, line_items_df):
    params = st.query_params
    distinct_turns = turns_df['address'] + DELIMITER + turns_df['move_out_date'].astype(str)
    sorted_turns = sorted(distinct_turns, key=lambda x: x.split(DELIMITER)[1], reverse=True)
    if params:
        default_index = sorted_turns.index(params.get('address', [None]) + DELIMITER + params.get('move_out_date', [None]))
    else:
        default_index = 0

    selected_turn, selected_turn_metrics = st.columns([3, 1])
    with selected_turn: 
        selected_turn = st.selectbox("Select a Turn", sorted_turns, index=default_index).split(DELIMITER)
        
    rental_id = turns_df[(turns_df['address'] == selected_turn[0]) & (turns_df['move_out_date'].astype(str) == selected_turn[1])]['rental_id'].values[0]
    selected_turn_arr = turns_df[(turns_df['rental_id'] == rental_id)].iloc[0]
    filtered_construction_scopes_df = construction_scopes_df[construction_scopes_df['most_recent_rental_id'] == rental_id]
    filtered_line_items_df = line_items_df[(line_items_df['rental_id'] == rental_id)]

    with selected_turn_metrics:
        st.markdown(
            f"""
            <div style='text-align: right; padding: 10px'>
                <h6>Project Type(s)</h6>
                <h6 style='color: {TEAL};'>{selected_turn_arr["project_types"].replace('_', ' ').title()}</h6>
            </div>
            """,
            unsafe_allow_html=True
        )
    return selected_turn_arr, filtered_construction_scopes_df, filtered_line_items_df


def individual_turn_timeline(selected_turn_arr):
    st.subheader("Timeline")

    nat_dates = []  # NaT dates
    items = [] # display only non-NaT dates
    date_fields = [
        ("Move-Out Date", 'move_out_date'),
        ("Scoped Date", 'project_scoped_date'),
        ("Scope Approved Date", 'project_scope_approved_date'),
        ("Finished QC Date", 'project_finished_qc_date'),
        ("Tour Ready Date", 'tour_ready_date'),
        ("Rent Ready Date", 'rent_ready_date'),
        ("Next Occupancy Date", 'next_occupancy_date'),
    ]
    for idx, (content, field) in enumerate(date_fields, start=1):
        date_value = selected_turn_arr[field]
        if pd.isna(date_value):
            nat_dates.append(content)
        else:
            items.append({"id": idx, "content": content, "start": f"{date_value:%m/%d/%y}"})

    st_timeline(items, groups=[], options={}, height="300px")
    if nat_dates:
        st.markdown(f"<div style='text-align: right;'><em><strong>Unconfirmed</strong>: {', '.join(nat_dates)}</em></div>", unsafe_allow_html=True)


def individual_turn_budget_breakdown(selected_turn_arr, filtered_construction_scopes_df, filtered_line_items_df, tickets_df):
    st.subheader("Budget Breakdown")
    # Overall Budget
    project_total_estimated_cost = selected_turn_arr['project_total_estimated_cost'] if not pd.isnull(selected_turn_arr['project_total_estimated_cost']) else 0
    with st.container():
        st.markdown(f"<h5>Total Budget: <span style='color: {TEAL};'>${project_total_estimated_cost:,.2f}</span></h5>", unsafe_allow_html=True)
        st.markdown(f"<h5>Invoiced Cost: <span style='color: {TEAL};'>${filtered_line_items_df['amount'].sum():,.2f}</span></h5>", unsafe_allow_html=True)

    # Budget Breakdown
    # project_estimated_cost = selected_turn_arr['project_estimated_cost'] if not pd.isnull(selected_turn_arr['project_estimated_cost']) else 0
    # occupancy_inspection_estimated_cost = selected_turn_arr['occupancy_inspection_estimated_cost'] if not pd.isnull(selected_turn_arr['occupancy_inspection_estimated_cost']) else 0
    # ticket_approved_budgets = selected_turn_arr['project_ticket_approved_budgets'] if not pd.isnull(selected_turn_arr['project_ticket_approved_budgets']) else 0
    # budget_data = pd.DataFrame({ "Source": ["Main Project(s)"], "Budgeted Amount": [project_estimated_cost] })
    # if "_oi" in selected_turn_arr['project_types'].lower():
    #     budget_data = pd.concat([budget_data, pd.DataFrame([["Occupancy Inspection", occupancy_inspection_estimated_cost]], columns=budget_data.columns)])
    # if (selected_turn_arr['fund'] != 'Homevest Real Estate Partners IV - Limestone, L.P.'):
    #     budget_data = pd.concat([budget_data, pd.DataFrame([["Approved Latchel Tickets", ticket_approved_budgets]], columns=budget_data.columns)])
    # with st.container(horizontal=True, width=600):
    #     st.dataframe(budget_data, hide_index=True, column_config={"Budgeted Amount": st.column_config.NumberColumn(format="accounting")})
    for index, row in filtered_construction_scopes_df.reset_index(drop=True).iterrows():
        with st.container(horizontal=True):
            st.metric(f'Project #{index+1} Type', f"{row['type'].replace('_', ' ').title()}", width=250)
            st.metric('Project Status', f"{row['project_status'].replace('_', ' ').title()}", width=250)
            st.metric('Project Estimated Cost', f"${0 if pd.isna(row['project_estimated_cost']) else row['project_estimated_cost']:,.2f}", width=200)
            if selected_turn_arr['fund'] != 'Homevest Real Estate Partners IV - Limestone, L.P.':
                st.metric('Ticket Approved Budgets', f"${0 if pd.isna(row['ticket_approved_budgets']) else row['ticket_approved_budgets']:,.2f}", width=200)

        project_tickets_df = tickets_df[tickets_df['project_id'] == row['project_id']]
        tickets_columns = ['external_source', 'external_id', 'title', 'category', 'description', 'max_cost', 'status', 'tracking_status']
        if not project_tickets_df.empty:
            st.dataframe(project_tickets_df[tickets_columns], hide_index=True)
        else:
            st.badge("No tickets found for this project!", color="violet")
        if index != len(filtered_construction_scopes_df) - 1:
            st.divider()



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

    output_df['link'] = output_df.apply(
        lambda row: row['memo'] if str(row['memo']).startswith("https://") else None,
        axis=1
    )
    output_df = output_df.sort_values(by='date', ascending=False)
    output_df.columns = [col.replace('_', ' ').title() for col in output_df.columns]
    st.dataframe(
        output_df,
        hide_index=True,
        column_config={
            'Link': st.column_config.LinkColumn(
                display_text='↪',
                pinned=True,
            ),
            'Date': st.column_config.DateColumn(    
                width=1,
                format="M/D/YY"
            ),
            'Amount': st.column_config.NumberColumn(
                width=1,
                format="accounting"
            ),
            # 'Memo': st.column_config.LinkColumn()
        }
    )
