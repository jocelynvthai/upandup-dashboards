import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import timedelta

from tabs.utils import generate_new_economic_occupancy_df, economic_occupancy_chart, GRAY, TEAL, PURPLE


TODAY = datetime.now().date()

def occupancy_filters(economic_occupancy_df, rental_df):
    col_fund, col_market = st.columns(2)

    filtered_economic_occupancy_df = economic_occupancy_df.copy().sort_values(by='date', ascending=False)
    filtered_rental_df = rental_df.copy()
    with col_fund:
        selected_fund = st.selectbox("Select a fund", ['All'] + sorted(list(economic_occupancy_df['fund'].unique())))
        if selected_fund != 'All':
            filtered_economic_occupancy_df = filtered_economic_occupancy_df[filtered_economic_occupancy_df['fund'] == selected_fund]
            filtered_rental_df = filtered_rental_df[filtered_rental_df['fund'] == selected_fund]
    with col_market:
        selected_market = st.selectbox("Select a market", ['All'] + sorted(list(filtered_economic_occupancy_df['market'].unique())))
        if selected_market != 'All':
            filtered_economic_occupancy_df = filtered_economic_occupancy_df[filtered_economic_occupancy_df['market'] == selected_market]
            filtered_rental_df = filtered_rental_df[filtered_rental_df['market'] == selected_market]
    return filtered_economic_occupancy_df, filtered_rental_df


def occupancy_metrics(economic_occupancy_df):
    st.subheader("Today's Occupancy Metrics")
    economic_occupancy_col, physical_occupancy_col = st.columns(2)
    today_occupancy = economic_occupancy_df[economic_occupancy_df['date'] == datetime.now()]
    with economic_occupancy_col:
        st.metric("Economic Occupancy", 
                  f"{round(today_occupancy['total_gpr_occupied'].sum() * 100 / today_occupancy['total_gpr'].sum(), 2)}%", 
                  help="Today's Rent Charged / Today's GPR")
    with physical_occupancy_col:
        st.metric("Physical Occupancy", 
                  f"{round(today_occupancy['num_properties_occupied'].sum() * 100 / today_occupancy['num_properties'].sum(), 2)}%", 
                  help="\# Homes Occupied / \# Homes")


def economic_occupancy(economic_occupancy_df):
    st.subheader("Projected Economic Occupancy")

    time_granularity_col, date_range_col = st.columns(2)
    with time_granularity_col:
        selected_time_granularity = st.selectbox("Select a time granularity", ['day', 'week', 'month'], index=1)
    with date_range_col:
        last_date = economic_occupancy_df['date'].max()
        if selected_time_granularity == 'day':
            start = TODAY
            selected_days = st.slider("Select # days to view", min_value=1, max_value=(last_date-TODAY).days, value=60)
            end = TODAY + relativedelta(days=selected_days)
        elif selected_time_granularity == 'week':
            start = TODAY - relativedelta(days=datetime.now().weekday())
            last_week_start = last_date - relativedelta(days=last_date.weekday())
            selected_weeks = st.slider("Select # weeks to view", min_value=1, max_value=int((last_week_start-start).days/7), value=8)
            end = start + relativedelta(weeks=selected_weeks)
        else:
            start = TODAY - relativedelta(days=TODAY.day-1)
            last_month_start = last_date - relativedelta(days=last_date.day-1)
            selected_months = st.slider("Select # months to view", min_value=1, max_value=int((last_month_start-start).days/30), value=3)
            end = start + relativedelta(months=selected_months)

    economic_occupancy_selected = economic_occupancy_df[(economic_occupancy_df['time_granularity'] == selected_time_granularity) &
                                                        (economic_occupancy_df['date'] >= start) &
                                                        (economic_occupancy_df['date'] < end)
    ]
    economic_occupancy_selected = economic_occupancy_selected.groupby('date').agg(
        total_gpr=('total_gpr', 'sum'), 
        total_gpr_potentially_occupied=('total_gpr_potentially_occupied', 'sum'),
        total_gpr_occupied=('total_gpr_occupied', 'sum'), 
        total_gpr_occupied_budget=('total_gpr_occupied_budget', 'sum')
    ).reset_index()

    economic_occupancy_selected['economic_occupancy_potentially_occupied'] = economic_occupancy_selected['total_gpr_potentially_occupied'] * 100 / economic_occupancy_selected['total_gpr']
    economic_occupancy_selected['economic_occupancy_occupied'] = economic_occupancy_selected['total_gpr_occupied'] * 100 / economic_occupancy_selected['total_gpr']
    economic_occupancy_selected['economic_occupancy_occupied_budget'] = economic_occupancy_selected['total_gpr_occupied_budget'] * 100 / economic_occupancy_selected['total_gpr']

    economic_occupancy_chart(economic_occupancy_selected, 'economic_occupancy_occupied_budget', ['economic_occupancy_potentially_occupied', 'economic_occupancy_occupied'], selected_time_granularity)
    st.markdown(
        '<div style="text-align: right;"><em>Potentially Occupied assumes that all current leases will be renewed, whereas Occupied assumes that all current leases will move out.</em></div>',
        unsafe_allow_html=True
    )



def num_leases_to_target(economic_occupancy_df):
    st.subheader("Number of Leases to Target (Option 1)")
    deadline_col, deadline_date_col = st.columns([6, 1])
    with deadline_col:
        deadline_options = {
            'This week': TODAY + relativedelta(weeks=0, weekday=6),
            'Next week': TODAY + relativedelta(weeks=1, weekday=6), 
            'Next next week': TODAY + relativedelta(weeks=2, weekday=6), 
            'This month': TODAY.replace(day=1) + relativedelta(months=1) - relativedelta(days=1), 
            'Next month': TODAY.replace(day=1) + relativedelta(months=2) - relativedelta(days=1)
        }
        # deadline_options_display = [f"{key} ({value})" for key, value in deadline_options.items()]
        selected_deadline = st.selectbox("Select a deadline", list(deadline_options.keys()), 
                                        index=0, 
                                        help="Deadline date is end of the selected time period",
                                        key="num_leases_to_target_deadline")
    with deadline_date_col:
        deadline_date = deadline_options[selected_deadline]
        st.markdown(
            f"""
            <div style='text-align: right; padding: 10px'>
                <h6>Deadline Date</h6>
                <h6 style='color: {TEAL};'>{deadline_date.strftime('%Y-%m-%d')}</h6>
            </div>
            """,
            unsafe_allow_html=True
        )

    day_economic_occupancy = economic_occupancy_df[(economic_occupancy_df['time_granularity'] == 'day') &
                                                    (economic_occupancy_df['date'] >= TODAY) &
                                                    (economic_occupancy_df['date'] <= deadline_date)
    ].groupby('date').agg(
        num_properties=('num_properties', 'sum'),
        num_properties_potentially_occupied=('num_properties_potentially_occupied', 'sum'),
        num_properties_occupied=('num_properties_occupied', 'sum'),
        total_gpr=('total_gpr', 'sum'),
        total_gpr_potentially_occupied=('total_gpr_potentially_occupied', 'sum'),
        total_gpr_occupied=('total_gpr_occupied', 'sum'),
        total_gpr_occupied_budget=('total_gpr_occupied_budget', 'sum')
    ).reset_index()

    day_economic_occupancy['hole'] = day_economic_occupancy['total_gpr_occupied_budget'] - day_economic_occupancy['total_gpr_occupied']
    deadline_row = day_economic_occupancy[day_economic_occupancy['date'] == deadline_date]
    hole_col, vacant_homes_col, recoverable_gpr_col, leases_needed_col = st.columns(4)
    with hole_col:
        hole = deadline_row['hole'].iloc[0]
        st.metric("Hole", f"${hole:,.2f}")
    with vacant_homes_col:
        vacant_homes = deadline_row['num_properties'].iloc[0] - deadline_row['num_properties_occupied'].iloc[0]
        st.metric("Vacant Homes", f"{vacant_homes:,.0f}")
    with recoverable_gpr_col:
        recoverable_gpr_per_home_per_day = (deadline_row['total_gpr'].iloc[0] - deadline_row['total_gpr_occupied'].iloc[0]) / (deadline_row['num_properties'].iloc[0] - deadline_row['num_properties_occupied'].iloc[0])
        st.metric("Recoverable GPR per Home per Day", f"${recoverable_gpr_per_home_per_day:,.2f}")
    with leases_needed_col:
        leases_needed = hole / recoverable_gpr_per_home_per_day
        st.metric("Leases Needed", f"{leases_needed:,.0f}")

    st.write('**Recovery Days Table:**')
    st.dataframe(day_economic_occupancy)


def num_leases_to_target_2(economic_occupancy_df):
    st.subheader("Number of Leases to Target (Option 2)")

    day_economic_occupancy = economic_occupancy_df[(economic_occupancy_df['time_granularity'] == 'day') &
                                                    (economic_occupancy_df['date'] >= pd.to_datetime('2025-08-01'))
    ].groupby('date').agg(
        num_properties=('num_properties', 'sum'),
        num_properties_potentially_occupied=('num_properties_potentially_occupied', 'sum'),
        num_properties_occupied=('num_properties_occupied', 'sum'),
        total_gpr=('total_gpr', 'sum'),
        total_gpr_potentially_occupied=('total_gpr_potentially_occupied', 'sum'),
        total_gpr_occupied=('total_gpr_occupied', 'sum'),
        total_gpr_occupied_budget=('total_gpr_occupied_budget', 'sum')
    ).reset_index()
    day_economic_occupancy['total_gpr_per_property'] = day_economic_occupancy['total_gpr'] / day_economic_occupancy['num_properties']

    # Select a deadline and a number of leases
    deadline_col, num_leases_col, optimal_num_leases_col = st.columns([2, 2, 1])
    with deadline_col:
        selected_deadline = st.date_input("Select a deadline", 
                                        value=TODAY + relativedelta(weeks=1, weekday=6), 
                                        min_value=TODAY + relativedelta(days=1),
                                        max_value=max(economic_occupancy_df['date']),
                                        help="The date all leases need to be signed by",
                                        key="num_leases_to_target_2_deadline")
        deadline_row = day_economic_occupancy[day_economic_occupancy['date'] == selected_deadline]
        num_vacant_homes = deadline_row['num_properties'].iloc[0] - deadline_row['num_properties_occupied'].iloc[0]
    with num_leases_col:
        selected_num_leases = st.slider("Select # of leases", min_value=1, max_value=num_vacant_homes, value=1, help="The number of leases that need to be signed")

    signed_leases, lease_distribution = generate_new_economic_occupancy_df(day_economic_occupancy, selected_deadline, selected_num_leases)
    optimal_num_leases = 0
    optimal_diff = float('inf')
    for i in range(1, num_vacant_homes):
        signed_leases_i, lease_distribution_i = generate_new_economic_occupancy_df(day_economic_occupancy, selected_deadline, i)
        diff = (signed_leases_i['economic_occupancy_budget'] - signed_leases_i['economic_occupancy_new_projected']).sum()
        if diff < optimal_diff:
            optimal_diff = diff
            optimal_num_leases = i
    # with optimal_num_leases_col:
    #     st.metric("Optimal # of Leases", f"{optimal_num_leases:,.0f}")

    st.write(f'**Assumption 1: Each lease signed (up to the number of leases selected) is evenly distributed from today to the selected deadline ({selected_deadline.strftime('%Y-%m-%d')}). See below.**')
    st.dataframe(lease_distribution, hide_index=True)
    st.write('**Assumption 2: Each lease signed has a length of 365 days.**')
    st.write('**Assumption 3: Move in, aka GPR recovery, occurs 8 days after the lease signed date.**')
    economic_occupancy_chart(signed_leases[signed_leases['date'] <= TODAY + relativedelta(weeks=3)], 'economic_occupancy_budget', ['economic_occupancy_new_projected', 'economic_occupancy_prior_projected'], 'day')



def upcoming_moves(rental_df): 
    types = {
        'occupancy_date': 'Move-In Date',
        'move_out_date': 'Move-Out Date'
    }
    for type in types.keys():
        formal_type = types[type].replace(' Date', '')
        st.subheader(f"Upcoming {formal_type}s")

        upcoming_moves = rental_df[rental_df[type] > datetime.now()][['address', 'fund', 'market', type]].sort_values(by=type, ascending=True)
        if upcoming_moves.empty:
            st.badge(f"No upcoming {formal_type}s!", color="violet")
            continue
        upcoming_moves['month'] = pd.to_datetime(upcoming_moves[type]).dt.strftime('%B %Y')
        upcoming_moves.sort_values(by=type, ascending=True, inplace=True)

        grouped_moves = upcoming_moves.groupby('month')
        html_rows = []
        sorted_months = sorted(grouped_moves.groups.keys(), key=lambda x: pd.to_datetime(x, format='%B %Y'))
        for month in sorted_months:
            group = grouped_moves.get_group(month)
            month_count = group.shape[0]
            for i, row in group.iterrows():
                if i == group.index[0]:
                    html_rows.append(f'''<tr>
                                            <td rowspan="{month_count}">{month}</td>
                                            <td>{row['address']}</td>
                                            <td>{row['fund']}</td>
                                            <td>{row['market']}</td>
                                            <td>{row[type]}</td>
                                        </tr>''')
                else:
                    html_rows.append(f'''<tr>
                                            <td>{row['address']}</td>
                                            <td>{row['fund']}</td>
                                            <td>{row['market']}</td>
                                            <td>{row[type]}</td>
                                        </tr>''')

        # Convert the rows to a complete HTML table
        html_table = f'''<table class="dataframe" style="width: 100%;">
                            <thead>
                                <tr>
                                    <th>Month</th>
                                    <th>Address</th>
                                    <th>Fund</th>
                                    <th>Market</th>
                                    <th>{types[type]}</th>
                                </tr>
                            </thead>
                            <tbody>{"".join(html_rows)}</tbody>
                        </table>'''
        st.markdown(html_table, unsafe_allow_html=True)


