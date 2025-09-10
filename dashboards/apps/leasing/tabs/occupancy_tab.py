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
    generate_new_economic_occupancy_df
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
    st.subheader(
        "Projected Economic Occupancy (Current)",
        help = "Best case assumes that all current leases will be renewed.  Worst case assumes that all current leases will move out."
    )

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

    economic_occupancy_selected['economic_occupancy_best_case'] = economic_occupancy_selected['total_gpr_potentially_occupied'] * 100 / economic_occupancy_selected['total_gpr']
    economic_occupancy_selected['economic_occupancy_worst_case'] = economic_occupancy_selected['total_gpr_occupied'] * 100 / economic_occupancy_selected['total_gpr']
    economic_occupancy_selected['economic_occupancy_budget'] = economic_occupancy_selected['total_gpr_occupied_budget'] * 100 / economic_occupancy_selected['total_gpr']

    projected_eo_chart = economic_occupancy_chart(economic_occupancy_selected, 'economic_occupancy_budget', ['economic_occupancy_best_case', 'economic_occupancy_worst_case'], selected_time_granularity)
    st.altair_chart(projected_eo_chart)



def num_leases_to_target(economic_occupancy_df):
    st.subheader(
        'Leases to Target',
        help=(
            "To maintain the economic occupancy budget, each week's target assumes the target was hit for all prior weeks.\n"
            "e.g. Week 4's target assumes Weeks 1–3's targets were hit."
        )
    )

    week_economic_occupancy = economic_occupancy_df[
        (economic_occupancy_df['time_granularity'] == 'week') &
        (economic_occupancy_df['date'] >= TODAY - relativedelta(days=TODAY.weekday()))
    ]
    week_economic_occupancy = week_economic_occupancy.groupby(['date', 'fund']).agg(
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
    
    # 1. Chosen target week's Economic Occupancy
    SUNDAY = TODAY - relativedelta(days=1)
    target_week_col, target_col, num_leases_to_sign_col, weeks_ahead_col = st.columns([1, 2, .5, 2.5])
    with target_col:
        selected_target_week = st.selectbox("Select a target week", ['This week', 'Next week', 'Next next week'], index=1)
        # get start and end date of the target week
        if selected_target_week == 'This week':
            target_week_start = TODAY + relativedelta(weekday=MO(-1))
        elif selected_target_week == 'Next week':
            target_week_start = TODAY + relativedelta(weeks=1, weekday=MO(-1))
        elif selected_target_week == 'Next next week':
            target_week_start = TODAY + relativedelta(weeks=2, weekday=MO(-1))
        target_week_end = target_week_start + relativedelta(days=6)
        target_week_formatted = f"{target_week_start.strftime('%b %d')} - {target_week_end.strftime('%b %d')}"
        targets_df = week_economic_occupancy[week_economic_occupancy['date'] == target_week_start]
    with target_week_col:
        st.metric(f"Target Week", f"{target_week_start.strftime('%m/%d')} - {target_week_end.strftime('%m/%d')}")
    with weeks_ahead_col:
        max_weeks_ahead = int((max(week_economic_occupancy['date']) - target_week_start).days / 7)
        selected_weeks_ahead = st.slider("Select # weeks to view", min_value=8, max_value=max_weeks_ahead, value=12)

    # Compute the rent gained during the target week for one new lease
    targets_df['total_gpr_vacant_homes'] = targets_df['total_gpr'] - targets_df['total_gpr_occupied']
    targets_df['num_vacant_homes'] = targets_df['num_properties'] - targets_df['num_properties_occupied']
    targets_df['weekly_gpr_per_new_lease'] = targets_df['total_gpr_vacant_homes'] / targets_df['num_vacant_homes']
    # Determine the number of new leases needed to hit budget
    targets_df['gpr_needed_to_hit_budget'] = (targets_df['total_gpr_occupied_budget'] - targets_df['total_gpr_occupied']).clip(lower=0)
    targets_df['num_new_leases_needed']= targets_df['gpr_needed_to_hit_budget'] / targets_df['weekly_gpr_per_new_lease']
    with num_leases_to_sign_col:
        st.metric(f"\# Leases to Sign", f"{targets_df['num_new_leases_needed'].sum():.2f}")

    # 1. Target week metrics
    targets_display_df = targets_df[['fund', 'economic_occupancy_budget', 'economic_occupancy_best_case', 'economic_occupancy_worst_case', 'gpr_needed_to_hit_budget', 'weekly_gpr_per_new_lease', 'num_new_leases_needed']]

    with st.expander("View fund metrics"):
        targets_display_df = targets_display_df
        st.data_editor(
            targets_display_df, 
            column_config={
                'num_new_leases_needed': st.column_config.NumberColumn(
                    label='Leases to Sign',
                    format='%.2f', 
                    help='Number of Leases to Sign'
                ), 
                'economic_occupancy_budget': st.column_config.NumberColumn(
                    label='Budgeted EO',
                    format='percent', 

                    help='Budgeted Economic Occupancy'
                ), 
                'economic_occupancy_best_case': st.column_config.NumberColumn(
                    label='Best Case EO',
                    format='percent', 
                    help='Best Case Economic Occupancy'
                ), 
                'economic_occupancy_worst_case': st.column_config.NumberColumn(
                    label='Worst Case EO',
                    format='percent', 
                    help='Worst Case Economic Occupancy'
                ), 
                'gpr_needed_to_hit_budget': st.column_config.NumberColumn(
                    label='Weekly Rent Needed',
                    format='dollar', 
                    help='Weekly Rent Needed to Hit Budget'
                ), 
                'weekly_gpr_per_new_lease': st.column_config.NumberColumn(
                    label='Avg Weekly Rent Gained per Signed Lease',
                    format='dollar', 
                    help='Average Weekly Rent Gained per Signed Lease'
                )
            },
            hide_index=True
        )


    # 2. Following weeks' target Economic Occupancy
    target_leases = {}
    funds = week_economic_occupancy['fund'].unique()
    for fund in funds:
        weekly_gpr_per_new_lease = targets_df[targets_df['fund'] == fund]['weekly_gpr_per_new_lease'].iloc[0]
        fund_target_leases = week_economic_occupancy[(week_economic_occupancy['fund'] == fund) & (week_economic_occupancy['date'] >= target_week_start)]
        catch_up_leases_signed_arr = [0]
        leases_needed_week_arr = []
        catch_up_gpr_arr = []
        for index, row in fund_target_leases.iterrows():
            catch_up_leases = catch_up_leases_signed_arr[-1]
            catch_up_gpr = row['total_gpr_occupied'] + (catch_up_leases * weekly_gpr_per_new_lease)
            new_gpr_needed_to_hit_budget = max(row['total_gpr_occupied_budget'] - catch_up_gpr, 0)
            new_num_leases_needed = new_gpr_needed_to_hit_budget / weekly_gpr_per_new_lease
            catch_up_gpr_arr.append(catch_up_gpr)
            leases_needed_week_arr.append(round(new_num_leases_needed, 2))
            catch_up_leases_signed_arr.append(catch_up_leases_signed_arr[-1] + new_num_leases_needed)
        fund_target_leases['catch_up_leases_signed'] = catch_up_leases_signed_arr[:-1]
        fund_target_leases['catch_up_gpr'] = catch_up_gpr_arr
        fund_target_leases['signed_leases_needed'] = leases_needed_week_arr
        fund_target_leases['is_target_week'] = fund_target_leases['date'] == target_week_start
        target_leases[fund] = fund_target_leases
    # Concatenate all the target leases
    target_leases_df = pd.concat(target_leases.values())
    target_leases_df['week_start'] = pd.to_datetime(target_leases_df['date']).dt.strftime('%Y-%m-%d')
    target_leases_df['week_end'] = target_leases_df['date'].apply(lambda x: (pd.to_datetime(x) + relativedelta(days=6)).strftime('%Y-%m-%d'))
    target_leases_df = target_leases_df[target_leases_df['signed_leases_needed'] > 0]
    
    selection = alt.selection_single(fields=['fund'], bind='legend')
    target_leases_per_week_chart = alt.Chart(target_leases_df[target_leases_df['date'] <= target_week_start + relativedelta(weeks=selected_weeks_ahead)]).mark_bar(color=TEAL, point={'color': TEAL}).encode(
        x=alt.X('week_start', title='Week Start', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('signed_leases_needed', title='# Leases to Sign'), 
        color=alt.condition(
            alt.datum.is_target_week, 
            alt.value(TEAL), 
            alt.value(DARK_TEAL)
        ) if len(funds) == 1 else alt.Color(
            'fund:N', 
            scale=alt.Scale(range=[TEAL, LIGHT_TEAL, DARK_TEAL, PURPLE, LIGHT_PURPLE, DARK_PURPLE]), 
            title='Fund'
        ), 
        tooltip=[
            alt.Tooltip('fund', title='Fund'),
            alt.Tooltip('week_start', title='Week Start'),
            alt.Tooltip('week_end', title='Week End'),
            alt.Tooltip('signed_leases_needed', title='# Leases to Sign')
        ], 
        opacity=alt.condition(selection, alt.value(1), alt.value(0.1))
    ).add_selection(
        selection
    ).properties(
        width=600,
        height=400
    )

    if len(funds) > 1:
        st.altair_chart(target_leases_per_week_chart, use_container_width=True)
    else:
        target_leases_per_week_text = target_leases_per_week_chart.mark_text(
            align='center',
            baseline='bottom',
            dy=-5
        ).encode(
            text='signed_leases_needed:Q'
        )
        st.altair_chart(target_leases_per_week_chart + target_leases_per_week_text, use_container_width=True)
    


def new_projected_economic_occupancy(economic_occupancy_df):
    st.subheader(
        "Projected Economic Occupancy (Based on Target)",
        help = "Based on a specified target day for x number of leases to be signed, what is the projected economic occupancy?"
    )

    day_economic_occupancy = economic_occupancy_df[(economic_occupancy_df['time_granularity'] == 'day') &
                                                    (economic_occupancy_df['date'] >= TODAY)
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

    # Select a target week and a number of leases
    target_col, num_leases_col = st.columns([2, 2])
    with target_col:
        selected_target_day = st.date_input("Select a target day", 
                                        value=TODAY + relativedelta(weeks=1, weekday=6), 
                                        min_value=TODAY + relativedelta(days=1),
                                        max_value=max(economic_occupancy_df['date']),
                                        help="The date all leases need to be signed by",
                                        key="num_leases_to_target")
        target_row = day_economic_occupancy[day_economic_occupancy['date'] == selected_target_day]
        num_vacant_homes = target_row['num_properties'].iloc[0] - target_row['num_properties_occupied'].iloc[0]
    with num_leases_col:
        selected_num_leases = st.slider("Select # of leases to sign", min_value=1, max_value=num_vacant_homes, value=1, help="The number of leases that need to be signed")

    signed_leases, lease_distribution = generate_new_economic_occupancy_df(day_economic_occupancy, selected_target_day, selected_num_leases)
    optimal_num_leases = 0
    optimal_diff = float('inf')
    for i in range(1, num_vacant_homes):
        signed_leases_i, lease_distribution_i = generate_new_economic_occupancy_df(day_economic_occupancy, selected_target_day, i)
        diff = (signed_leases_i['economic_occupancy_budget'] - signed_leases_i['economic_occupancy_new_projected']).sum()
        if diff < optimal_diff:
            optimal_diff = diff
            optimal_num_leases = i

    st.write(f'**Assumption 1:** each lease signed (up to the number of leases selected) is evenly distributed from today to the target day ({selected_target_day.strftime("%Y-%m-%d")}).')
    with st.expander("View the signed leases distribution"):
        st.data_editor(
            lease_distribution,
            column_config={
                'date': st.column_config.DateColumn(label='Date'),
                'num_leases_signed': st.column_config.NumberColumn(label='# Leases Signed')
            }, 
            hide_index=True
        )
    st.write('**Assumption 2:** each lease signed has a length of 365 days.')
    st.write('**Assumption 3:** move in, aka GPR recovery, occurs 8 days after the lease signed date.')
    

    eight_days_from_today = (TODAY + timedelta(days=8)).strftime('%Y-%m-%d')
    move_in_line = alt.Chart(pd.DataFrame({'date_str': [eight_days_from_today]})).mark_rule(color='red').encode(
        x='date_str:O',
        tooltip=alt.Tooltip(value=f'({eight_days_from_today}): Earliest move in/rent recovery begins 8 days from today (first lease signed). ')
    )
    new_projected_eo_chart = economic_occupancy_chart(signed_leases[signed_leases['date'] <= selected_target_day + relativedelta(weeks=3)], 'economic_occupancy_budget', ['economic_occupancy_new_projected', 'economic_occupancy_prior_projected'], 'day')
    st.altair_chart(alt.layer(new_projected_eo_chart + move_in_line), use_container_width=True)



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



    



# def num_leases_to_target_old(economic_occupancy_df):
    
#     st.subheader(
#         'Leases to Target',
#         help=(
#             "To maintain 95% Economic Occupancy, each week's target assumes the target was hit for prior weeks.\n"
#             "e.g. Week 4's target assumes Weeks 1–3's targets were hit."
#         )
#     )
    # selected_fund = st.selectbox("Select a fund", ['All'] + sorted(list(economic_occupancy_df['fund'].unique())), key="num_leases_to_target_old_fund")
    # if selected_fund != 'All':
    #     economic_occupancy_df = economic_occupancy_df[economic_occupancy_df['fund'] == selected_fund]

    # week_economic_occupancy = economic_occupancy_df[
    #     (economic_occupancy_df['time_granularity'] == 'week') &
    #     (economic_occupancy_df['date'] >= TODAY - relativedelta(days=TODAY.weekday()))
    # ]
    # week_economic_occupancy = week_economic_occupancy.groupby('date').agg(
    #     num_properties=('num_properties', 'sum'),
    #     num_properties_potentially_occupied=('num_properties_potentially_occupied', 'sum'),
    #     num_properties_occupied=('num_properties_occupied', 'sum'),
    #     total_gpr=('total_gpr', 'sum'),
    #     total_gpr_potentially_occupied=('total_gpr_potentially_occupied', 'sum'),
    #     total_gpr_occupied=('total_gpr_occupied', 'sum'),
    #     total_gpr_occupied_budget=('total_gpr_occupied_budget', 'sum')
    # ).reset_index()
    # week_economic_occupancy['economic_occupancy_best_case'] = week_economic_occupancy['total_gpr_potentially_occupied'] / week_economic_occupancy['total_gpr']
    # week_economic_occupancy['economic_occupancy_worst_case'] = week_economic_occupancy['total_gpr_occupied'] / week_economic_occupancy['total_gpr']
    # week_economic_occupancy['economic_occupancy_budget'] = week_economic_occupancy['total_gpr_occupied_budget'] / week_economic_occupancy['total_gpr']
    
    # # 1. Chosen deadline week's target Economic Occupancy
    # # Define the "deadline week", which will default to the week after next (can make this user-configurable later)
    # SUNDAY = TODAY - relativedelta(days=1)
    # deadline_col, weeks_ahead_col = st.columns(2)
    # with deadline_col:
    #     selected_deadline_week = st.selectbox("Select a deadline week", ['This week', 'Next week', 'Next next week'], index=1)
    #     # get start and end date of the deadline week
    #     if selected_deadline_week == 'This week':
    #         deadline_week_start = TODAY + relativedelta(weekday=MO(-1))
    #     elif selected_deadline_week == 'Next week':
    #         deadline_week_start = TODAY + relativedelta(weeks=1, weekday=MO(-1))
    #     elif selected_deadline_week == 'Next next week':
    #         deadline_week_start = TODAY + relativedelta(weeks=2, weekday=MO(-1))
    #     deadline_week_end = deadline_week_start + relativedelta(days=6)
    #     deadline_week_formatted = f"{deadline_week_start.strftime('%b %d')} - {deadline_week_end.strftime('%b %d')}"
    #     deadline_row = week_economic_occupancy[week_economic_occupancy['date'] == deadline_week_start].iloc[0]
    # with weeks_ahead_col:
    #     max_weeks_ahead = int((max(week_economic_occupancy['date']) - deadline_week_start).days / 7)
    #     selected_weeks_ahead = st.slider("Select # weeks to view", min_value=8, max_value=max_weeks_ahead, value=12, key="num_leases_to_target_old")

    # # Compute the rent gained during the deadline week for one new lease
    # total_gpr_vacant_homes = deadline_row['total_gpr'] - deadline_row['total_gpr_occupied']
    # num_vacant_homes = deadline_row['num_properties'] - deadline_row['num_properties_occupied']
    # gpr_per_new_lease = total_gpr_vacant_homes / num_vacant_homes
    # # Determine the number of new leases needed to hit budget
    # gpr_needed_to_hit_budget = max(deadline_row['total_gpr_occupied_budget'] - deadline_row['total_gpr_occupied'], 0)
    # num_new_leases_needed = gpr_needed_to_hit_budget / gpr_per_new_lease

    # # Deadline week metrics
    # deadline_week_col, budgeted_eo_col, best_case_eo_col, worst_case_eo_col = st.columns([0.75, 1, 1, 1])
    # with deadline_week_col:
    #     st.metric(f"Deadline Week", f"{deadline_week_start.strftime('%m/%d')} - {deadline_week_end.strftime('%m/%d')}")
    # with budgeted_eo_col:
    #     st.metric(f"Budgeted Economic Occupancy", f"{deadline_row['economic_occupancy_budget']:.2%}")
    # with best_case_eo_col:
    #     st.metric(f"Best Case Economic Occupancy", f"{deadline_row['economic_occupancy_best_case']:.2%}")
    # with worst_case_eo_col:
    #     st.metric(f"Worst Case Economic Occupancy", f"{deadline_row['economic_occupancy_worst_case']:.2%}")
    # _, additional_rent_needed_col, rent_per_new_lease_col, num_new_leases_needed_col = st.columns([0.75, 1, 1, 1])
    # with additional_rent_needed_col:
    #     st.metric(f"+$_ to hit Budgeted Economic Occupancy", f"${gpr_needed_to_hit_budget:.2f}")
    # with rent_per_new_lease_col:
    #     st.metric(f"Avg Rent Gained per Signed Lease", f"${gpr_per_new_lease:.2f}")
    # with num_new_leases_needed_col:
    #     st.metric(f"\# Leases to Sign to hit Budgeted Economic Occupancy", f"{num_new_leases_needed:.2f}")

    # # 2. Following weeks' target Economic Occupancy
    # target_leases = week_economic_occupancy[week_economic_occupancy['date'] >= deadline_week_start]
    # catch_up_leases_signed_arr = [0]
    # leases_needed_week_arr = []
    # catch_up_gpr_arr = []
    # for index, row in target_leases.iterrows():
    #     catch_up_leases = catch_up_leases_signed_arr[-1]
    #     catch_up_gpr = row['total_gpr_occupied'] + (catch_up_leases * gpr_per_new_lease)
    #     new_gpr_needed_to_hit_budget = max(row['total_gpr_occupied_budget'] - catch_up_gpr, 0)
    #     new_num_leases_needed = new_gpr_needed_to_hit_budget / gpr_per_new_lease

    #     catch_up_gpr_arr.append(catch_up_gpr)
    #     leases_needed_week_arr.append(round(new_num_leases_needed, 2))
    #     catch_up_leases_signed_arr.append(catch_up_leases_signed_arr[-1] + new_num_leases_needed)

    # target_leases['catch_up_leases_signed'] = catch_up_leases_signed_arr[:-1]
    # target_leases['catch_up_gpr'] = catch_up_gpr_arr
    # target_leases['signed_leases_needed'] = leases_needed_week_arr
    # target_leases['is_deadline_week'] = target_leases['date'] == deadline_week_start

    # target_leases['date_str'] = pd.to_datetime(target_leases['date']).dt.strftime('%Y-%m-%d')
    # target_leases_per_week_chart = alt.Chart(target_leases[target_leases['date'] <= deadline_week_start + relativedelta(weeks=selected_weeks_ahead)]).mark_bar(color=TEAL, point={'color': TEAL}).encode(
    #     x=alt.X('date_str', title='Week', axis=alt.Axis(labelAngle=0)),
    #     y=alt.Y('signed_leases_needed', title='# Leases to Sign'), 
    #     color=alt.condition(
    #         alt.datum.is_deadline_week,
    #         alt.value(TEAL), 
    #         alt.value(DARK_TEAL)  
    #     ),
    #     tooltip=[
    #         alt.Tooltip('date_str', title='Week Start'),
    #         alt.Tooltip('signed_leases_needed', title='# Leases to Sign')
    #     ]
    # ).properties(
    #     width=600,
    #     height=400
    # )
    # target_leases_per_week_text = target_leases_per_week_chart.mark_text(
    #     align='center',
    #     baseline='bottom',
    #     dy=-5
    # ).encode(
    #     text='signed_leases_needed:Q'
    # )
    # st.altair_chart(target_leases_per_week_chart + target_leases_per_week_text, use_container_width=True)



