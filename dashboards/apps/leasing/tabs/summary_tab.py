import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from tabs.utils import LIGHT_RED


def summary_filters(rental_applications_df):
    col_date_range = st.columns(1)

    today = datetime.now()
    start_of_current_week = today - timedelta(days=today.weekday())
    date_range = st.date_input("Pick a period range", 
                            value=(start_of_current_week - timedelta(days=7), start_of_current_week - timedelta(days=1)), 
                            format='MM/DD/YYYY',
                            key='summary_date_range')
    if len(date_range) != 2:
        st.stop()
    else: 
        return date_range[0], date_range[1]


def summary_metrics(rental_applications_df, start_date, end_date, raw_inquiries_df):
    st.subheader("Snapshot Summary Metrics", help="""This is a snapshot of the metrics for the selected period.""")

    num_inquiries = raw_inquiries_df[
        (raw_inquiries_df['date'] >= pd.to_datetime(start_date).tz_localize('UTC')) & 
        (raw_inquiries_df['date'] <= pd.to_datetime(end_date).tz_localize('UTC'))
    ]['rental_site_listing_id'].count()
    num_apps = len(rental_applications_df[
        (rental_applications_df['created_at'] >= pd.to_datetime(start_date).tz_localize('UTC')) & 
        (rental_applications_df['created_at'] <= pd.to_datetime(end_date).tz_localize('UTC'))
    ])
    num_approved = len(rental_applications_df[
        (rental_applications_df['is_underwriting_approved'] == True) &
        (rental_applications_df['underwritten_at'] >= pd.to_datetime(start_date).tz_localize('UTC')) & 
        (rental_applications_df['underwritten_at'] <= pd.to_datetime(end_date).tz_localize('UTC'))
    ])
    canceled_df = rental_applications_df[  
        (rental_applications_df['canceled_at'] >= pd.to_datetime(start_date).tz_localize('UTC')) & 
        (rental_applications_df['canceled_at'] <= pd.to_datetime(end_date).tz_localize('UTC'))
    ]
    num_cancelled = len(canceled_df)
    num_completed = len(rental_applications_df[
        (rental_applications_df['completed_at'] >= pd.to_datetime(start_date).tz_localize('UTC')) & 
        (rental_applications_df['completed_at'] <= pd.to_datetime(end_date).tz_localize('UTC'))
    ])

    num_inquiries_col, num_apps_col, num_approved_col, num_cancelled_col, num_completed_col = st.columns(5)
    with num_inquiries_col:
        st.metric("&#35; Inquiries", num_inquiries)
    with num_apps_col:
        st.metric("&#35; Apps", num_apps)
    with num_approved_col:
        st.metric("&#35; Approved", num_approved)
    with num_cancelled_col:
        st.metric("&#35; Cancelled", num_cancelled)
    with num_completed_col:
        st.metric("&#35; Completed", num_completed)


    st.subheader("Cancelled Applications")
    canceled_grouped_df = canceled_df.groupby(['cancelation_reason', 'cancelation_subreason']).size().reset_index(name='num_apps').sort_values(by='cancelation_reason')

    # Define the custom order for reasons and subreasons
    custom_order = {
        'credit_report': [
            'insufficient', 'debt_to_income_ratio', 'infile_date', 'no_credit',
            'adverse_rental_history', 'recent_bankruptcy'
        ],
        'income': ['insufficient'],
        'background_check': ['criminal_history', 'eviction_history'],
        'documents_rejected': [
            'offer_letter', 'tax_return', 'paystub', 'bank_statements', 'id'
        ],
        'home_rented': ['rematched', 'no_rematch'],
        'tenant_reason': [
            'found_another_home', 'cannot_afford_move_in_cost', 'move_in_timeline',
            'lease_term', 'not_interested_in_program_terms', 'did_not_pay_app_fee',
            'unresponsive'
        ],
        'engineering': ['duplicate_application', 'test']
    }
    canceled_grouped_df['reason_order'] = canceled_grouped_df['cancelation_reason'].map(lambda x: list(custom_order.keys()).index(x))
    canceled_grouped_df['subreason_order'] = canceled_grouped_df.apply(lambda row: custom_order[row['cancelation_reason']].index(row['cancelation_subreason']), axis=1)
    canceled_grouped_df = canceled_grouped_df.sort_values(by=['reason_order', 'subreason_order']).drop(columns=['reason_order', 'subreason_order'])

    declined_reasons = ['credit_report', 'income', 'background_check', 'documents_rejected']
    canceled_grouped_df['status'] = canceled_grouped_df['cancelation_reason'].apply(lambda x: 'Declined' if x in declined_reasons else 'Canceled')

    display_df = canceled_grouped_df.copy()
    last_reason = None
    html_rows = []
    for index, row in display_df.iterrows():
        status_color = LIGHT_RED if row["status"] == "Declined" else None
        if row['cancelation_reason'] != last_reason:
            # Count how many times the current reason appears
            reason_count = display_df[display_df['cancelation_reason'] == row['cancelation_reason']].shape[0]
            html_rows.append(f'''<tr>
                                    <td rowspan="{reason_count}">{row["cancelation_reason"]}</td>
                                    <td>{row["cancelation_subreason"]}</td>
                                    <td>{row["num_apps"]}</td>
                                    <td style="color: {status_color};">{row["status"]}</td>
                                </tr>''')
            last_reason = row['cancelation_reason']
        else:
            html_rows.append(f'''<tr>
                                    <td>{row["cancelation_subreason"]}</td>
                                    <td>{row["num_apps"]}</td>
                                    <td style="color: {status_color};">{row["status"]}</td>
                                </tr>''')
    # Convert the rows to a complete HTML table
    html_table = f'''<table class="dataframe" style="width: 100%;">
                        <thead>
                            <tr>
                                <th>Cancelation Reason</th>
                                <th>Cancelation Subreason</th>
                                <th>Number of Apps</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>{"".join(html_rows)}</tbody>
                    </table>'''
    st.markdown(html_table, unsafe_allow_html=True)



    

    







    

    
    

    
    