import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# Page config - must be first
st.set_page_config(
    page_title="Eviction Cohort Analysis (BigQuery)",
    page_icon="📊",
    layout="wide"
)

# BigQuery connection
@st.cache_resource
def get_bq_client():
    credentials = service_account.Credentials.from_service_account_file(
        '/Users/michaelwong/Documents/Development/Homevest/ops-api/assets/homevest-data-admin-cert.json',
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    return bigquery.Client(credentials=credentials, project='homevest-data')

@st.cache_data(ttl=300)
def get_eviction_data():
    """Fetch all eviction data from BigQuery replicas"""
    client = get_bq_client()

    # BigQuery SQL using homevest-data datasets
    query = """
    WITH latest_balance AS (
        SELECT
            rental_id,
            aggregate_balance_after,
            aggregate_successful_balance_after,
            ROW_NUMBER() OVER (PARTITION BY rental_id ORDER BY date DESC, available_on DESC) as rn
        FROM `homevest-data.dbt_prod.fct_current_balances`
    )
    SELECT
        e.id,
        e.rental_id,
        e.created_at,
        e.status,
        e.cancelation_reason,
        e.filed_at,
        e.court_date,
        e.completed_at,
        e.canceled_at,
        m.display_name AS market_name,
        COALESCE(f.name, 'No Fund') AS fund_name,
        FORMAT_TIMESTAMP('%Y-%m', e.created_at) AS cohort,
        a.display_line_1 AS address,
        a.city,
        a.state,
        CONCAT(u.first_name, ' ', u.last_name) AS tenant_name,
        u.email AS tenant_email,
        u.phone AS tenant_phone,
        COALESCE(lb.aggregate_balance_after, 0) AS current_balance,
        COALESCE(lb.aggregate_balance_after, 0) - COALESCE(lb.aggregate_successful_balance_after, 0) AS processing
    FROM `homevest-data.google_cloud_postgresql_public.evictions` e
    JOIN `homevest-data.google_cloud_postgresql_public.rentals` r ON r.id = e.rental_id
    JOIN `homevest-data.google_cloud_postgresql_public.properties` p ON p.id = r.property_id
    JOIN `homevest-data.google_cloud_postgresql_public.portfolio_homes` ph ON ph.real_estate_acquisition_id = p.real_estate_acquisition_id
    JOIN `homevest-data.google_cloud_postgresql_public.homes` h ON h.id = ph.home_id
    JOIN `homevest-data.google_cloud_postgresql_public.addresses` a ON a.id = h.address_id
    JOIN `homevest-data.google_cloud_postgresql_public.markets` m ON m.id = h.market_id
    LEFT JOIN `homevest-data.google_cloud_postgresql_public.llc_properties` lp ON lp.property_id = p.id AND lp.end_date IS NULL
    LEFT JOIN `homevest-data.google_cloud_postgresql_public.llcs` l ON l.id = lp.llc_id
    LEFT JOIN `homevest-data.google_cloud_postgresql_public.fund_llcs` fl ON fl.llc_id = l.id
    LEFT JOIN `homevest-data.google_cloud_postgresql_public.funds` f ON f.id = fl.fund_id
    LEFT JOIN `homevest-data.google_cloud_postgresql_public.rental_users` ru ON ru.rental_id = r.id AND ru.deactivated_at IS NULL
    LEFT JOIN `homevest-data.google_cloud_postgresql_fast_public.users` u ON u.id = ru.user_id
    LEFT JOIN latest_balance lb ON lb.rental_id = CAST(r.id AS STRING) AND lb.rn = 1
    WHERE e.created_at >= TIMESTAMP(DATE_SUB(DATE_TRUNC(CURRENT_DATE(), MONTH), INTERVAL 12 MONTH))
    """

    df = client.query(query).to_dataframe()
    df = df.drop_duplicates(subset=['id'])
    # Exclude Homevest, Inc. fund
    df = df[df['fund_name'] != 'Homevest, Inc.']
    return df

def calculate_cohort_stats(df):
    """Calculate cohort statistics from raw data"""
    if len(df) == 0:
        return pd.DataFrame(columns=['cohort', 'created', 'bal_paid', 'not_bought_out', 'vacated', 'other', 'completed', 'pending'])

    stats = df.groupby('cohort').agg(
        created=('id', 'count'),
        bal_paid=('id', lambda x: ((df.loc[x.index, 'status'] == 'canceled') &
                                    (df.loc[x.index, 'cancelation_reason'] == 'Balance Payed')).sum()),
        vacated=('id', lambda x: ((df.loc[x.index, 'status'] == 'canceled') &
                                   (df.loc[x.index, 'cancelation_reason'] == 'Tenant Vacated Prior to Judgement')).sum()),
        other=('id', lambda x: ((df.loc[x.index, 'status'] == 'canceled') &
                                 (df.loc[x.index, 'cancelation_reason'] == 'Other')).sum()),
        completed=('id', lambda x: (df.loc[x.index, 'status'] == 'completed').sum()),
        pending=('id', lambda x: (df.loc[x.index, 'status'] == 'pending').sum())
    ).reset_index()
    stats['not_bought_out'] = stats['created'] - stats['bal_paid']
    stats = stats.sort_values('cohort', ascending=False)
    return stats

def format_with_pct(value, total):
    """Format a value with percentage of total"""
    if total == 0:
        return f"{value} (0%)"
    pct = round(value / total * 100)
    return f"{value} ({pct}%)"

def format_cohort_table(stats, selected_cohorts):
    """Format stats into display table with Select column"""
    display_df = pd.DataFrame({
        'Select': [c in selected_cohorts for c in stats['cohort']],
        'Cohort': stats['cohort'],
        'Created': stats['created'],
        'Bal Paid': [format_with_pct(v, c) for v, c in zip(stats['bal_paid'], stats['created'])],
        'Not Bought Out': [format_with_pct(v, c) for v, c in zip(stats['not_bought_out'], stats['created'])],
        'Vacated': [format_with_pct(v, c) for v, c in zip(stats['vacated'], stats['created'])],
        'Other': [format_with_pct(v, c) for v, c in zip(stats['other'], stats['created'])],
        'Completed': [format_with_pct(v, c) for v, c in zip(stats['completed'], stats['created'])],
        'Pending': [format_with_pct(v, c) for v, c in zip(stats['pending'], stats['created'])]
    })
    return display_df

def get_summary_table(df, group_col, group_name, selected_items):
    """Get summary by market or fund with Select column"""
    if len(df) == 0:
        return pd.DataFrame(columns=['Select', group_name, 'Total', 'Bal Paid', 'Not Bought Out', 'Vacated', 'Other', 'Completed', 'Pending'])

    summary = df.groupby(group_col).agg(
        total=('id', 'count'),
        bal_paid=('id', lambda x: ((df.loc[x.index, 'status'] == 'canceled') &
                                    (df.loc[x.index, 'cancelation_reason'] == 'Balance Payed')).sum()),
        vacated=('id', lambda x: ((df.loc[x.index, 'status'] == 'canceled') &
                                   (df.loc[x.index, 'cancelation_reason'] == 'Tenant Vacated Prior to Judgement')).sum()),
        other=('id', lambda x: ((df.loc[x.index, 'status'] == 'canceled') &
                                 (df.loc[x.index, 'cancelation_reason'] == 'Other')).sum()),
        completed=('id', lambda x: (df.loc[x.index, 'status'] == 'completed').sum()),
        pending=('id', lambda x: (df.loc[x.index, 'status'] == 'pending').sum())
    ).reset_index()
    summary['not_bought_out'] = summary['total'] - summary['bal_paid']
    summary = summary.sort_values('total', ascending=False)

    return pd.DataFrame({
        'Select': [item in selected_items for item in summary[group_col]],
        group_name: summary[group_col],
        'Total': summary['total'],
        'Bal Paid': summary['bal_paid'],
        'Not Bought Out': summary['not_bought_out'],
        'Vacated': summary['vacated'],
        'Other': summary['other'],
        'Completed': summary['completed'],
        'Pending': summary['pending']
    })

def filter_by_statuses(df, selected_statuses):
    """Filter dataframe by selected status categories"""
    if not selected_statuses:
        return df

    masks = []
    for status in selected_statuses:
        if status == 'Completed':
            masks.append(df['status'] == 'completed')
        elif status == 'Canceled - Balance Payed':
            masks.append((df['status'] == 'canceled') & (df['cancelation_reason'] == 'Balance Payed'))
        elif status == 'Canceled - Vacated':
            masks.append((df['status'] == 'canceled') & (df['cancelation_reason'] == 'Tenant Vacated Prior to Judgement'))
        elif status == 'Canceled - Other':
            masks.append((df['status'] == 'canceled') & (df['cancelation_reason'] == 'Other'))
        elif status == 'Pending':
            masks.append(df['status'] == 'pending')

    if masks:
        combined_mask = masks[0]
        for mask in masks[1:]:
            combined_mask = combined_mask | mask
        return df[combined_mask]
    return df

def get_status_summary_table(df, selected_statuses):
    """Get summary by status with Select column"""
    if len(df) == 0:
        return pd.DataFrame(columns=['Select', 'Status', 'Count'])

    status_data = []

    completed_count = len(df[df['status'] == 'completed'])
    if completed_count > 0:
        status_data.append({'Status': 'Completed', 'Count': completed_count})

    bal_paid_count = len(df[(df['status'] == 'canceled') & (df['cancelation_reason'] == 'Balance Payed')])
    if bal_paid_count > 0:
        status_data.append({'Status': 'Canceled - Balance Payed', 'Count': bal_paid_count})

    vacated_count = len(df[(df['status'] == 'canceled') & (df['cancelation_reason'] == 'Tenant Vacated Prior to Judgement')])
    if vacated_count > 0:
        status_data.append({'Status': 'Canceled - Vacated', 'Count': vacated_count})

    other_count = len(df[(df['status'] == 'canceled') & (df['cancelation_reason'] == 'Other')])
    if other_count > 0:
        status_data.append({'Status': 'Canceled - Other', 'Count': other_count})

    pending_count = len(df[df['status'] == 'pending'])
    if pending_count > 0:
        status_data.append({'Status': 'Pending', 'Count': pending_count})

    if not status_data:
        return pd.DataFrame(columns=['Select', 'Status', 'Count'])

    summary = pd.DataFrame(status_data)
    summary['Select'] = [s in selected_statuses for s in summary['Status']]

    return summary[['Select', 'Status', 'Count']]

def format_detail_table(df):
    """Format eviction details for display"""
    if len(df) == 0:
        return pd.DataFrame()

    detail_df = df[['address', 'city', 'state', 'tenant_name',
                    'market_name', 'fund_name', 'status', 'cancelation_reason',
                    'current_balance', 'processing',
                    'created_at', 'filed_at', 'court_date', 'completed_at', 'canceled_at']].copy()

    def format_status(row):
        if row['status'] == 'completed':
            return 'Completed'
        elif row['status'] == 'canceled':
            reason = row['cancelation_reason'] or 'Unknown'
            return f'Canceled - {reason}'
        elif row['status'] == 'pending':
            return 'Pending'
        return row['status']

    detail_df['display_status'] = detail_df.apply(format_status, axis=1)

    def status_sort_order(row):
        if row['status'] == 'completed':
            return 1
        elif row['status'] == 'canceled':
            return 2
        elif row['status'] == 'pending':
            return 3
        return 4

    detail_df['sort_order'] = detail_df.apply(status_sort_order, axis=1)
    detail_df = detail_df.sort_values(['sort_order', 'cancelation_reason', 'created_at'])

    result_df = detail_df[['address', 'city', 'state', 'tenant_name',
                           'market_name', 'fund_name', 'display_status',
                           'current_balance', 'processing',
                           'created_at', 'filed_at', 'court_date', 'completed_at', 'canceled_at']].copy()
    result_df.columns = ['Address', 'City', 'State', 'Tenant',
                         'Market', 'Fund', 'Status',
                         'Current Balance', 'Processing',
                         'Created', 'Filed', 'Court Date', 'Completed', 'Canceled']

    # Format currency columns
    result_df['Current Balance'] = result_df['Current Balance'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
    result_df['Processing'] = result_df['Processing'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")

    for col in ['Created', 'Filed', 'Court Date', 'Completed', 'Canceled']:
        result_df[col] = pd.to_datetime(result_df[col]).dt.strftime('%Y-%m-%d')
        result_df[col] = result_df[col].replace('NaT', '')

    return result_df

def apply_filters(df, selected_cohorts, selected_markets, selected_funds):
    """Apply all selected filters to dataframe"""
    filtered = df.copy()
    if selected_cohorts:
        filtered = filtered[filtered['cohort'].isin(selected_cohorts)]
    if selected_markets:
        filtered = filtered[filtered['market_name'].isin(selected_markets)]
    if selected_funds:
        filtered = filtered[filtered['fund_name'].isin(selected_funds)]
    return filtered

# Initialize session state
if 'selected_cohorts' not in st.session_state:
    st.session_state.selected_cohorts = set()
if 'selected_markets' not in st.session_state:
    st.session_state.selected_markets = set()
if 'selected_funds' not in st.session_state:
    st.session_state.selected_funds = set()
if 'selected_statuses' not in st.session_state:
    st.session_state.selected_statuses = set()

st.title("Eviction Cohort Analysis")
st.caption("Last 12 months - Data from BigQuery (homevest-data)")

try:
    df = get_eviction_data()

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
    cohort_base_df = apply_filters(df, [], list(st.session_state.selected_markets), list(st.session_state.selected_funds))
    cohort_filtered_df = filter_by_statuses(cohort_base_df, st.session_state.selected_statuses)

    market_base_df = apply_filters(df, list(st.session_state.selected_cohorts), [], list(st.session_state.selected_funds))
    market_filtered_df = filter_by_statuses(market_base_df, st.session_state.selected_statuses)

    fund_base_df = apply_filters(df, list(st.session_state.selected_cohorts), list(st.session_state.selected_markets), [])
    fund_filtered_df = filter_by_statuses(fund_base_df, st.session_state.selected_statuses)

    status_filtered_df = apply_filters(df, list(st.session_state.selected_cohorts), list(st.session_state.selected_markets), list(st.session_state.selected_funds))

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

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Check that the BigQuery credentials file exists at /Users/michaelwong/Documents/Development/Homevest/ops-api/assets/homevest-data-admin-cert.json")
    import traceback
    st.code(traceback.format_exc())
