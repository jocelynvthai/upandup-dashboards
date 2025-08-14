import streamlit as st

DELIMITER = ' -- moved out '

def drilldown_filters(turns_df, line_items_df):
    distinct_turns = turns_df['address'] + DELIMITER + turns_df['move_out_date'].astype(str)
    sorted_turns = sorted(distinct_turns, key=lambda x: x.split(DELIMITER)[1], reverse=True)
    selected_turn = st.selectbox("Select Turnover Period", sorted_turns).split(DELIMITER)

    rental_id = turns_df[
        (turns_df['address'] == selected_turn[0]) & 
        (turns_df['move_out_date'].astype(str) == selected_turn[1])
    ]['rental_id'].values[0]

    filtered_line_items_df = line_items_df[(line_items_df['rental_id'] == rental_id)]
    # filtered_turns_df will only be one row
    filtered_turns_df = turns_df[(turns_df['rental_id'] == rental_id)]
    return filtered_line_items_df, filtered_turns_df


def individual_turn_summary(filtered_line_items_df, filtered_turns_df):
    col1, col2, col3, col4 = st.columns(4)
    turn = filtered_turns_df.iloc[0]
    with col1:
        st.metric("Billed Cost", f"${filtered_line_items_df['amount'].sum():,.2f}")
    with col2:
        estimated_cost = turn['project_estimated_cost']
        if turn['fund'] != 'Homevest Real Estate Partners IV - Limestone, L.P.':
            estimated_cost += turn['project_ticket_approved_budgets']
        st.metric("Estimated Cost", f"${estimated_cost:,.2f}")
    with col3:
        st.metric("Move-Out Date", f"{turn['move_out_date']:%m/%d/%Y}")
    with col4:
        st.metric("Scoped Date", f"{turn['project_scoped_at']:%m/%d/%Y}")


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
