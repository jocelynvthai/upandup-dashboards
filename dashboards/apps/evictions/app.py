import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info, evictions_data
from tabs.cohort_analysis import apply_filters, filter_by_statuses, calculate_cohort_stats, format_cohort_table, get_summary_table, get_status_summary_table, format_detail_table

# Configure page layout
st.set_page_config(
    page_title="Evictions",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info())
evictions_df = evictions_data(credentials)

# Application
col1, col2 = st.columns([1, 0.04])
with col1:
    st.title("Evictions Dashboard")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Add spacing to align with title
    st.button("↻", on_click=st.cache_data.clear, help="Refresh All Data")


st.subheader("Cohort Analysis")
# Initialize session state
if 'selected_cohorts' not in st.session_state:
    st.session_state.selected_cohorts = set()
if 'selected_markets' not in st.session_state:
    st.session_state.selected_markets = set()
if 'selected_funds' not in st.session_state:
    st.session_state.selected_funds = set()
if 'selected_statuses' not in st.session_state:
    st.session_state.selected_statuses = set()

# Show active filters and clear button
active_filters = []
if st.session_state.selected_cohorts:
    active_filters.append(f"Cohorts: {', '.join(sorted(st.session_state.selected_cohorts))}")
if st.session_state.selected_markets:
    active_filters.append(f"Markets: {', '.join(sorted(st.session_state.selected_markets))}")
if st.session_state.selected_funds:
    active_filters.append(f"Funds: {', '.join(sorted(st.session_state.selected_funds))}")
if st.session_state.selected_statuses:
    active_filters.append(f"Statuses: {', '.join(sorted(st.session_state.selected_statuses))}")

col1, col2 = st.columns([5, 1])
with col1:
    if active_filters:
        st.success("**Active Filters:** " + " | ".join(active_filters))
with col2:
    if active_filters:
        if st.button("Clear All", type="secondary"):
            st.session_state.selected_cohorts = set()
            st.session_state.selected_markets = set()
            st.session_state.selected_funds = set()
            st.session_state.selected_statuses = set()
            st.rerun()

# Calculate filtered data for each table
cohort_base_df = apply_filters(evictions_df, [], list(st.session_state.selected_markets), list(st.session_state.selected_funds))
cohort_filtered_df = filter_by_statuses(cohort_base_df, st.session_state.selected_statuses)

market_base_df = apply_filters(evictions_df, list(st.session_state.selected_cohorts), [], list(st.session_state.selected_funds))
market_filtered_df = filter_by_statuses(market_base_df, st.session_state.selected_statuses)

fund_base_df = apply_filters(evictions_df, list(st.session_state.selected_cohorts), list(st.session_state.selected_markets), [])
fund_filtered_df = filter_by_statuses(fund_base_df, st.session_state.selected_statuses)

status_filtered_df = apply_filters(evictions_df, list(st.session_state.selected_cohorts), list(st.session_state.selected_markets), list(st.session_state.selected_funds))

detail_df = filter_by_statuses(status_filtered_df, st.session_state.selected_statuses)

# Key metrics
total = len(detail_df)
bal_paid_count = len(detail_df[(detail_df['status'] == 'canceled') & (detail_df['cancelation_reason'] == 'Balance Payed')])
pending_count = len(detail_df[detail_df['status'] == 'pending'])
completed_count = len(detail_df[detail_df['status'] == 'completed'])
buyout_rate = int(bal_paid_count / total * 100) if total > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Evictions", total)
col2.metric("Buyout Rate", f"{buyout_rate}%")
col3.metric("Pending", pending_count)
col4.metric("Completed", completed_count)

st.divider()

# Monthly Cohorts Table
st.subheader("Monthly Cohorts")
if st.session_state.selected_markets or st.session_state.selected_funds:
    st.caption(f"Showing data for: {', '.join(list(st.session_state.selected_markets) + list(st.session_state.selected_funds))}")

stats = calculate_cohort_stats(cohort_filtered_df)
cohort_table = format_cohort_table(stats, st.session_state.selected_cohorts)

edited_cohort = st.data_editor(
    cohort_table,
    use_container_width=True,
    hide_index=True,
    disabled=['Cohort', 'Created', 'Bal Paid', 'Not Bought Out', 'Vacated', 'Other', 'Completed', 'Pending'],
    column_config={
        "Select": st.column_config.CheckboxColumn(width="small"),
        "Cohort": st.column_config.TextColumn(width="small"),
    },
    key="cohort_editor"
)

new_cohort_selections = set(edited_cohort[edited_cohort['Select']]['Cohort'].tolist())
if new_cohort_selections != st.session_state.selected_cohorts:
    st.session_state.selected_cohorts = new_cohort_selections
    st.rerun()

st.divider()

# By Market table
st.subheader("By Market")
if st.session_state.selected_cohorts or st.session_state.selected_funds:
    st.caption(f"Showing data for: {', '.join(list(st.session_state.selected_cohorts) + list(st.session_state.selected_funds))}")

market_table = get_summary_table(market_filtered_df, 'market_name', 'Market', st.session_state.selected_markets)

edited_market = st.data_editor(
    market_table,
    use_container_width=True,
    hide_index=True,
    disabled=['Market', 'Total', 'Bal Paid', 'Not Bought Out', 'Vacated', 'Other', 'Completed', 'Pending'],
    column_config={
        "Select": st.column_config.CheckboxColumn(width="small"),
    },
    key="market_editor"
)

new_market_selections = set(edited_market[edited_market['Select']]['Market'].tolist())
if new_market_selections != st.session_state.selected_markets:
    st.session_state.selected_markets = new_market_selections
    st.rerun()

st.divider()

# By Fund table
st.subheader("By Fund")
if st.session_state.selected_cohorts or st.session_state.selected_markets:
    st.caption(f"Showing data for: {', '.join(list(st.session_state.selected_cohorts) + list(st.session_state.selected_markets))}")

fund_table = get_summary_table(fund_filtered_df, 'fund_name', 'Fund', st.session_state.selected_funds)

edited_fund = st.data_editor(
    fund_table,
    use_container_width=True,
    hide_index=True,
    disabled=['Fund', 'Total', 'Bal Paid', 'Not Bought Out', 'Vacated', 'Other', 'Completed', 'Pending'],
    column_config={
        "Select": st.column_config.CheckboxColumn(width="small"),
    },
    key="fund_editor"
)

new_fund_selections = set(edited_fund[edited_fund['Select']]['Fund'].tolist())
if new_fund_selections != st.session_state.selected_funds:
    st.session_state.selected_funds = new_fund_selections
    st.rerun()

# Status table
st.subheader("By Status")
if st.session_state.selected_cohorts or st.session_state.selected_markets or st.session_state.selected_funds:
    st.caption(f"Showing data for: {', '.join(list(st.session_state.selected_cohorts) + list(st.session_state.selected_markets) + list(st.session_state.selected_funds))}")

status_table = get_status_summary_table(status_filtered_df, st.session_state.selected_statuses)

if len(status_table) > 0:
    edited_status = st.data_editor(
        status_table,
        use_container_width=True,
        hide_index=True,
        disabled=['Status', 'Count'],
        column_config={
            "Select": st.column_config.CheckboxColumn(width="small"),
        },
        key="status_editor"
    )

    new_status_selections = set(edited_status[edited_status['Select']]['Status'].tolist())
    if new_status_selections != st.session_state.selected_statuses:
        st.session_state.selected_statuses = new_status_selections
        st.rerun()

st.divider()

# Detail table
st.subheader("Eviction Details")
st.write(f"**{len(detail_df)} evictions**")

if len(detail_df) > 0:
    st.dataframe(format_detail_table(detail_df), use_container_width=True, hide_index=True)
else:
    st.info("No evictions match the selected filters")

    
