import pandas as pd


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