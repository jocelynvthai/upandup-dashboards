import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta, MO
from datetime import timedelta

from tabs.utils import (
    LIGHT_TEAL, 
    TEAL, 
    DARK_TEAL, 
    LIGHT_PURPLE, 
    PURPLE, 
    DARK_PURPLE, 
    economic_occupancy_chart, 
    target_leases_per_week_chart, 
    target_leases_per_week_text
)

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


    # Determine period_end based on time_granularity
    filtered_economic_occupancy_df['period_end'] = filtered_economic_occupancy_df.apply(
        lambda row: (
            row['date'] if row['time_granularity'].lower() == "day"
            else (pd.to_datetime(row['date']) + pd.Timedelta(days=6)).date() if row['time_granularity'].lower() == "week"
            else (pd.to_datetime(row['date']) + pd.offsets.MonthEnd(0)).date() if row['time_granularity'].lower() == "month"
            else pd.NaT
        ),
        axis=1
    )
    return filtered_economic_occupancy_df, filtered_rental_df



def occupancy_metrics(economic_occupancy_df):
    st.subheader("Today's Occupancy Metrics")
    col_economic_occupancy, col_physical_occupancy = st.columns(2)
    today_occupancy = economic_occupancy_df[economic_occupancy_df['date'] == datetime.now()]
    with col_economic_occupancy:
        st.metric("Economic Occupancy", 
                f"{round(today_occupancy['total_gpr_occupied'].sum() * 100 / today_occupancy['total_gpr'].sum(), 2)}%", 
                help="Today's Rent Charged / Today's GPR")
    with col_physical_occupancy:
        st.metric("Physical Occupancy", 
                f"{round(today_occupancy['num_properties_occupied'].sum() * 100 / today_occupancy['num_properties'].sum(), 2)}%", 
                help="\# Homes Occupied / \# Homes")



def economic_occupancy(economic_occupancy_df):
    st.subheader(
        "Projected Economic Occupancy (Current)",
        help = "Best case assumes that all current leases will be renewed.  Worst case assumes that all current leases will move out."
    )

    col_time_granularity, col_date_range = st.columns(2)
    with col_time_granularity:
        selected_time_granularity = st.selectbox("Select a time granularity", ['week', 'month'], index=0)
    with col_date_range:
        last_date = economic_occupancy_df['period_end'].max()
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
                                                        (economic_occupancy_df['period_end'] >= start) &
                                                        (economic_occupancy_df['period_end'] < end)
    ]
    economic_occupancy_selected = economic_occupancy_selected.groupby('period_end').agg(
        total_gpr=('total_gpr', 'sum'), 
        total_gpr_potentially_occupied=('total_gpr_potentially_occupied', 'sum'),
        total_gpr_occupied=('total_gpr_occupied', 'sum'), 
        total_gpr_occupied_budget=('total_gpr_occupied_budget', 'sum')
    ).reset_index()

    economic_occupancy_selected['economic_occupancy_best_case'] = economic_occupancy_selected['total_gpr_potentially_occupied'] * 100 / economic_occupancy_selected['total_gpr']
    economic_occupancy_selected['economic_occupancy_worst_case'] = economic_occupancy_selected['total_gpr_occupied'] * 100 / economic_occupancy_selected['total_gpr']
    economic_occupancy_selected['economic_occupancy_forecast'] = economic_occupancy_selected['total_gpr_occupied_budget'] * 100 / economic_occupancy_selected['total_gpr']

    # View week ends in dashboard
    projected_eo_chart = economic_occupancy_chart(economic_occupancy_selected, 'economic_occupancy_forecast', ['economic_occupancy_best_case', 'economic_occupancy_worst_case'], selected_time_granularity)
    st.altair_chart(projected_eo_chart)



def num_leases_to_target(economic_occupancy_df):
    st.subheader(
        'Leases to Target This Week',
        help=(
            "To maintain the economic occupancy budget:\n"
            "- Each target week's number of leases to sign is based on its corresponding occupancy week's economic occupancy gap, which is 2 weeks from the target week.\n"
            "- Each week's target assumes the target was hit for all prior weeks. e.g. Week 4's target assumes Weeks 1–3's targets were hit."
        )
    )

    week_economic_occupancy = economic_occupancy_df[
        (economic_occupancy_df['time_granularity'] == 'week') &
        (economic_occupancy_df['date'] >= TODAY - relativedelta(days=TODAY.weekday()))
    ].groupby(['date', 'fund']).agg(
        num_properties=('num_properties', 'sum'),
        num_properties_potentially_occupied=('num_properties_potentially_occupied', 'sum'),
        num_properties_occupied=('num_properties_occupied', 'sum'),
        total_gpr=('total_gpr', 'sum'),
        total_gpr_potentially_occupied=('total_gpr_potentially_occupied', 'sum'),
        total_gpr_occupied=('total_gpr_occupied', 'sum'),
        total_gpr_occupied_budget=('total_gpr_occupied_budget', 'sum')
    ).reset_index()
    week_economic_occupancy['economic_occupancy_best_case'] = week_economic_occupancy['total_gpr_potentially_occupied'] / week_economic_occupancy['total_gpr']
    week_economic_occupancy['economic_occupancy_worst_case'] = week_economic_occupancy['total_gpr_occupied'] / week_economic_occupancy['total_gpr']
    week_economic_occupancy['economic_occupancy_budget'] = week_economic_occupancy['total_gpr_occupied_budget'] / week_economic_occupancy['total_gpr']

    # 1. Data Preparation
    # Target Week is current week
    selected_target_week = st.selectbox("Select a target week", ['Current Week', 'Next Week'], index=0)
    if selected_target_week == 'Current Week':
        st.session_state['target_week_start'] = TODAY + relativedelta(weekday=MO(-1))
        st.session_state['target_week_end'] = st.session_state['target_week_start'] + relativedelta(days=6)
    else:
        st.session_state['target_week_start'] = TODAY + relativedelta(weekday=MO(-1)) + relativedelta(days=7)
        st.session_state['target_week_end'] = st.session_state['target_week_start'] + relativedelta(days=6)
    # Occupancy Week is 2 weeks from target week
    occupancy_week_start = st.session_state['target_week_start'] + relativedelta(days=14)
    occupancy_week_end = occupancy_week_start + relativedelta(days=6)
    # Compute the rent gained per new lease during the occupancy week
    occupancy_df = week_economic_occupancy[week_economic_occupancy['date'] == occupancy_week_start]
    occupancy_df['weekly_gpr_per_new_lease'] = (occupancy_df['total_gpr']-occupancy_df['total_gpr_occupied']) / (occupancy_df['num_properties']-occupancy_df['num_properties_occupied'])
    occupancy_df['gpr_needed_to_hit_budget_worst_case'] = (occupancy_df['total_gpr_occupied_budget'] - occupancy_df['total_gpr_occupied']).clip(lower=0)
    occupancy_df['gpr_needed_to_hit_budget_best_case'] = (occupancy_df['total_gpr_occupied_budget'] - occupancy_df['total_gpr_potentially_occupied']).clip(lower=0)
    occupancy_df['num_new_leases_needed_worst_case']= occupancy_df['gpr_needed_to_hit_budget_worst_case'] / occupancy_df['weekly_gpr_per_new_lease']
    occupancy_df['num_new_leases_needed_best_case']= occupancy_df['gpr_needed_to_hit_budget_best_case'] / occupancy_df['weekly_gpr_per_new_lease']
    st.session_state['num_new_leases_needed_worst_case'] = occupancy_df['num_new_leases_needed_worst_case'].sum()
    st.session_state['num_new_leases_needed_best_case'] = occupancy_df['num_new_leases_needed_best_case'].sum()


    # 2. Target week metrics
    col_target_week, col_occupancy_week, col_num_leases_to_sign_worst_case, col_num_leases_to_sign_best_case, col_weeks_ahead = st.columns(5)
    with col_target_week:
        st.metric(f"Target Week", f"{st.session_state['target_week_start'].strftime('%m/%d')} - {st.session_state['target_week_end'].strftime('%m/%d')}", 
                  help="The week we need to sign leases by. Move in/rent recovery occurs 14 days after lease signing, \
                        so the target number of leases to sign this week is based on the economic occupancy gap 2 weeks from now (Occupancy Week).")
    with col_occupancy_week:
        st.metric(f"Occupancy Week", f"{occupancy_week_start.strftime('%m/%d')} - {occupancy_week_end.strftime('%m/%d')}", 
                  help="The week the signed leases will move in/rent recovery begins.")
    with col_num_leases_to_sign_worst_case:
        st.metric(f"\# Leases to Sign (Worst Case)", f"{st.session_state['num_new_leases_needed_worst_case']:.2f}")
    with col_num_leases_to_sign_best_case:
        st.metric(f"\# Leases to Sign (Best Case)", f"{st.session_state['num_new_leases_needed_best_case']:.2f}")
    with col_weeks_ahead:
        max_weeks_ahead = int((max(week_economic_occupancy['date']) - occupancy_week_start).days / 7) - 1
        selected_weeks_ahead = st.slider("Select # weeks to view", min_value=8, max_value=max_weeks_ahead, value=12)
    
    occupancy_display_df = occupancy_df[['fund', 
                                         'economic_occupancy_budget', 
                                         'economic_occupancy_worst_case', 
                                         'economic_occupancy_best_case', 
                                         'weekly_gpr_per_new_lease', 
                                         'gpr_needed_to_hit_budget_worst_case', 
                                         'gpr_needed_to_hit_budget_best_case', 
                                         'num_new_leases_needed_worst_case', 
                                         'num_new_leases_needed_best_case']]
    # Create MultiIndex columns
    occupancy_display_df.columns = pd.MultiIndex.from_tuples([
        ('Fund', ''),  # single-level
        ('Economic Occupancy', 'Budgeted'),
        ('Economic Occupancy', 'Worst Case'),
        ('Economic Occupancy', 'Best Case'),
        ('Weekly Rent Gained', 'Per Signed Lease'),
        ('Weekly Rent Needed', 'Worst Case'),
        ('Weekly Rent Needed', 'Best Case'),
        ('Leases to Sign', 'Worst Case'),
        ('Leases to Sign', 'Best Case')
    ])

    with st.expander("View target week's metrics"):
        st.dataframe(
            occupancy_display_df.style.format({
                ('Economic Occupancy', 'Budgeted'): "{:.2%}",
                ('Economic Occupancy', 'Best Case'): "{:.2%}",
                ('Economic Occupancy', 'Worst Case'): "{:.2%}",
                ('Weekly Rent Gained', 'Per Signed Lease'): "${:,.2f}",
                ('Weekly Rent Needed', 'Worst Case'): "${:,.2f}",
                ('Weekly Rent Needed', 'Best Case'): "${:,.2f}",
                ('Leases to Sign', 'Worst Case'): "{:.2f}",
                ('Leases to Sign', 'Best Case'): "{:.2f}"
            }), 
            hide_index=True
        )

    # 3. Following weeks' target Economic Occupancy
    target_leases = {}
    funds = week_economic_occupancy['fund'].unique()
    for fund in funds:
        weekly_gpr_per_new_lease = occupancy_df[occupancy_df['fund'] == fund]['weekly_gpr_per_new_lease'].iloc[0]
        fund_target_leases = week_economic_occupancy[(week_economic_occupancy['fund'] == fund) & (week_economic_occupancy['date'] >= occupancy_week_start)]
        for case in ['worst_case', 'best_case']:
            recovery_leases_signed_arr = [0]
            leases_needed_week_arr = []
            recovery_gpr_arr = []
            for index, row in fund_target_leases.iterrows():
                recovery_leases = recovery_leases_signed_arr[-1]
                if case == 'worst_case':
                    recovery_gpr = row['total_gpr_occupied'] + (recovery_leases * weekly_gpr_per_new_lease)
                else:
                    recovery_gpr = row['total_gpr_potentially_occupied'] + (recovery_leases * weekly_gpr_per_new_lease)
                new_gpr_needed_to_hit_budget = max(row['total_gpr_occupied_budget'] - recovery_gpr, 0)
                new_num_leases_needed = new_gpr_needed_to_hit_budget / weekly_gpr_per_new_lease
                recovery_gpr_arr.append(recovery_gpr)
                leases_needed_week_arr.append(round(new_num_leases_needed, 2))
                recovery_leases_signed_arr.append(recovery_leases_signed_arr[-1] + new_num_leases_needed)
            fund_target_leases[f'recovery_leases_signed_{case}'] = recovery_leases_signed_arr[:-1]
            fund_target_leases[f'recovery_gpr_{case}'] = recovery_gpr_arr
            fund_target_leases[f'signed_leases_needed_{case}'] = leases_needed_week_arr
        fund_target_leases['is_target_week'] = fund_target_leases['date'] == occupancy_week_start
        target_leases[fund] = fund_target_leases
    # Concatenate all the target leases
    target_leases_df = pd.concat(target_leases.values())
    # week end is the end of the occupancy week (2 weeks from target week)
    target_leases_df['week_end'] = target_leases_df['date'].apply(lambda x: (pd.to_datetime(x)+relativedelta(days=6)-relativedelta(days=14)).strftime('%Y-%m-%d'))
    target_leases_df['worst_case'] = 'Worst (current leases all move out)'
    target_leases_df['best_case'] = 'Best (current leases all renewed)'

    filtered_target_leases_df = target_leases_df[target_leases_df['date'] <= occupancy_week_start + relativedelta(weeks=selected_weeks_ahead-1)]
    selection = alt.selection_single(fields=['fund'], bind='legend')
    if len(funds) == 1:
        best_case_chart = target_leases_per_week_chart(filtered_target_leases_df, selection, 'best_case', funds)
        worst_case_chart = target_leases_per_week_chart(filtered_target_leases_df, selection, 'worst_case', funds)
        worst_case_text = target_leases_per_week_text(filtered_target_leases_df, worst_case_chart, 'worst_case', funds)
        best_case_text = target_leases_per_week_text(filtered_target_leases_df, best_case_chart, 'best_case', funds)
        target_leases_chart = alt.layer(worst_case_chart, worst_case_text, 
                          best_case_chart, best_case_text)
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; gap: 16px; font-size: 12px; align-items: center; margin-top: 4px;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 10px; height: 10px; border-radius: 50%; background-color: {LIGHT_TEAL}; margin-right: 4px;"></div>
                    <span>Best Case</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 10px; height: 10px; border-radius: 50%; background-color: {DARK_TEAL}; margin-right: 4px;"></div>
                    <span>Worst Case</span>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.altair_chart(target_leases_chart, use_container_width=True)
    else:
        chart = target_leases_per_week_chart(filtered_target_leases_df, selection, 'worst_case', funds)
        text = target_leases_per_week_text(filtered_target_leases_df, chart, 'worst_case', funds)
        target_leases_chart = alt.layer(chart, text)
        st.altair_chart(target_leases_chart, use_container_width=True)
        


def new_projected_economic_occupancy(economic_occupancy_df):
    st.subheader(
        "Projected Economic Occupancy (Based on Target)",
        help = "Based on a specified target day for x number of leases to be signed, what is the projected economic occupancy?"
    )

    week_economic_occupancy = economic_occupancy_df[
        (economic_occupancy_df['time_granularity'] == 'week') &
        (economic_occupancy_df['period_end'] >= TODAY)
    ].groupby('period_end').agg(
        num_properties=('num_properties', 'sum'),
        num_properties_potentially_occupied=('num_properties_potentially_occupied', 'sum'),
        num_properties_occupied=('num_properties_occupied', 'sum'),
        num_properties_pending_renewal=('num_properties_pending_renewal', 'sum'),
        total_gpr=('total_gpr', 'sum'),
        total_gpr_potentially_occupied=('total_gpr_potentially_occupied', 'sum'),
        total_gpr_occupied=('total_gpr_occupied', 'sum'),
        total_gpr_occupied_budget=('total_gpr_occupied_budget', 'sum')
    ).reset_index()

    # Select a target week and a number of leases
    col_target_week, col_num_leases = st.columns([1, 4])
    with col_target_week:
        st.metric(f"Target Week", f"{st.session_state['target_week_start'].strftime('%m/%d')} - {st.session_state['target_week_end'].strftime('%m/%d')}")
        occupancy_week_end = (st.session_state['target_week_end'] + relativedelta(days=14)).strftime('%Y-%m-%d')
        target_row = week_economic_occupancy[week_economic_occupancy['period_end'] == st.session_state['target_week_end']]
        num_vacant_homes = target_row['num_properties'].iloc[0] - target_row['num_properties_occupied'].iloc[0]
    with col_num_leases:
        selected_num_leases = st.slider("Select # of leases to sign", min_value=1, max_value=num_vacant_homes, value=round(st.session_state['num_new_leases_needed_worst_case']), help="The number of leases that need to be signed")

    signed_leases = week_economic_occupancy.copy()
    signed_leases['new_leases'] = signed_leases['period_end'].apply(lambda x: 
        selected_num_leases 
        if x >= st.session_state['target_week_end'] + relativedelta(days=14) 
        else 0
    )

    signed_leases['total_gpr_per_new_lease'] = (signed_leases['total_gpr']-signed_leases['total_gpr_occupied']) / (signed_leases['num_properties']-signed_leases['num_properties_occupied'])
    signed_leases['recovery_gpr'] = signed_leases['total_gpr_per_new_lease'] * signed_leases['new_leases']
    signed_leases['economic_occupancy_forecast'] = signed_leases['total_gpr_occupied_budget'] * 100 / signed_leases['total_gpr']
    signed_leases['economic_occupancy_prior_projected'] = (signed_leases['total_gpr_occupied']) * 100 / signed_leases['total_gpr']
    signed_leases['economic_occupancy_new_projected'] = (signed_leases['total_gpr_occupied'] + signed_leases['recovery_gpr']) * 100 / signed_leases['total_gpr']

    st.write(f"**Assumption 1:** All leases are signed by the target week end ({st.session_state['target_week_end'].strftime('%Y-%m-%d')}).")
    st.write(f"**Assumption 2:** Move in, aka GPR recovery, occurs 14 days after the lease signed date ({occupancy_week_end}).")
    
    # 1. Projected Economic Occupancy Chart
    chart_signed_leases = signed_leases[signed_leases['period_end'] <= st.session_state['target_week_end'] + relativedelta(weeks=8)]
    new_projected_eo_chart = economic_occupancy_chart(
        chart_signed_leases, 
        'economic_occupancy_forecast', 
        ['economic_occupancy_new_projected', 'economic_occupancy_prior_projected'], 
        'week'
    )
    # 2. Move in Line
    move_in_line = alt.Chart(pd.DataFrame({'date_str': [occupancy_week_end]})
    ).mark_rule(
        color='red'
    ).encode(
        x='date_str:O', 
        tooltip=alt.Tooltip(value=f'Move in/rent recovery begins: {occupancy_week_end}')
    )

    # 3. Pending Renewals
    pivoted_chart_signed_leases = chart_signed_leases.set_index('period_end')[['num_properties_pending_renewal']].T
    with st.expander("View pending renewals (# active leases ending within 30 days with no move out date set)"):
        st.dataframe(pivoted_chart_signed_leases, hide_index=True)

    st.altair_chart(alt.layer(new_projected_eo_chart + move_in_line).resolve_scale(x='independent'), use_container_width=True)



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



