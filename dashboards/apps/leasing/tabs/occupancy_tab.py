import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta, MO
from datetime import timedelta

from tabs.utils import GRAY, TEAL, DARK_TEAL, PURPLE, economic_occupancy_chart, generate_new_economic_occupancy_df


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
        "Projected Economic Occupancy",
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

    economic_occupancy_chart(economic_occupancy_selected, 'economic_occupancy_budget', ['economic_occupancy_best_case', 'economic_occupancy_worst_case'], selected_time_granularity)


def num_leases_to_target(economic_occupancy_df):
    st.subheader(
        'Leases to Target',
        help=(
            "To maintain 95% Economic Occupancy, each week's target assumes the target was hit for prior weeks.\n"
            "e.g. Week 4's target assumes Weeks 1–3's targets were hit."
        )
    )

    week_economic_occupancy = economic_occupancy_df[
        (economic_occupancy_df['time_granularity'] == 'week') &
        (economic_occupancy_df['date'] >= TODAY - relativedelta(days=TODAY.weekday()))
    ]
    week_economic_occupancy = week_economic_occupancy.groupby('date').agg(
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
    
    # 1. Chosen deadline week's target Economic Occupancy
    # Define the "deadline week", which will default to the week after next (can make this user-configurable later)
    SUNDAY = TODAY - relativedelta(days=1)
    selected_deadline_week = st.selectbox("Select a deadline week", ['This week', 'Next week', 'Next next week'], index=1)
    if selected_deadline_week == 'This week':
        deadline_week_start = TODAY + relativedelta(weekday=MO(-1))
    elif selected_deadline_week == 'Next week':
        deadline_week_start = TODAY + relativedelta(weeks=1, weekday=MO(-1))
    elif selected_deadline_week == 'Next next week':
        deadline_week_start = TODAY + relativedelta(weeks=2, weekday=MO(-1))
    deadline_week_end = deadline_week_start + relativedelta(days=6)
    deadline_week_formatted = f"{deadline_week_start.strftime('%b %d')} - {deadline_week_end.strftime('%b %d')}"
    deadline_row = week_economic_occupancy[week_economic_occupancy['date'] == deadline_week_start].iloc[0]
    # Compute the rent gained during the deadline week for one new lease
    total_gpr_vacant_homes = deadline_row['total_gpr'] - deadline_row['total_gpr_occupied']
    num_vacant_homes = deadline_row['num_properties'] - deadline_row['num_properties_occupied']
    gpr_per_new_lease = total_gpr_vacant_homes / num_vacant_homes
    # Use this to determine the number of new leases needed to hit budget
    gpr_needed_to_hit_budget = max(deadline_row['total_gpr_occupied_budget'] - deadline_row['total_gpr_occupied'], 0)
    num_new_leases_needed = gpr_needed_to_hit_budget / gpr_per_new_lease
    # Display the results
    deadline_week_col, budgeted_eo_col, best_case_eo_col, worst_case_eo_col = st.columns([0.75, 1, 1, 1])
    with deadline_week_col:
        st.metric(f"Deadline Week", f"{deadline_week_start.strftime('%m/%d')} - {deadline_week_end.strftime('%m/%d')}")
    with budgeted_eo_col:
        st.metric(f"Budgeted Economic Occupancy", f"{deadline_row['economic_occupancy_budget']:.2%}")
    with best_case_eo_col:
        st.metric(f"Best-Case Economic Occupancy", f"{deadline_row['economic_occupancy_best_case']:.2%}")
    with worst_case_eo_col:
        st.metric(f"Worst-Case Economic Occupancy", f"{deadline_row['economic_occupancy_worst_case']:.2%}")
    _, additional_rent_needed_col, rent_per_new_lease_col, num_new_leases_needed_col = st.columns([0.75, 1, 1, 1])
    with additional_rent_needed_col:
        st.metric(f"+$_ to hit Budgeted Economic Occupancy", f"${gpr_needed_to_hit_budget:.2f}")
    with rent_per_new_lease_col:
        st.metric(f"Avg Rent Gained per Signed Lease", f"${gpr_per_new_lease:.2f}")
    with num_new_leases_needed_col:
        st.metric(f"\# Signed Leases to hit Budgeted Economic Occupancy", f"{num_new_leases_needed:.2f}")

    # 2. Following weeks' target Economic Occupancy
    target_leases = week_economic_occupancy[week_economic_occupancy['date'] >= deadline_week_start]
    catch_up_leases_signed_arr = [0]
    leases_needed_week_arr = []
    catch_up_gpr_arr = []
    for index, row in target_leases.iterrows():
        catch_up_leases = catch_up_leases_signed_arr[-1]
        catch_up_gpr = row['total_gpr_occupied'] + (catch_up_leases * gpr_per_new_lease)
        new_gpr_needed_to_hit_budget = max(row['total_gpr_occupied_budget'] - catch_up_gpr, 0)
        new_num_leases_needed = new_gpr_needed_to_hit_budget / gpr_per_new_lease

        catch_up_gpr_arr.append(catch_up_gpr)
        leases_needed_week_arr.append(round(new_num_leases_needed, 1))
        catch_up_leases_signed_arr.append(catch_up_leases_signed_arr[-1] + new_num_leases_needed)

    target_leases['catch_up_leases_signed'] = catch_up_leases_signed_arr[:-1]
    target_leases['catch_up_gpr'] = catch_up_gpr_arr
    target_leases['signed_leases_needed'] = leases_needed_week_arr
    target_leases['is_deadline_week'] = target_leases['date'] == deadline_week_start

    target_leases_per_week_chart = alt.Chart(target_leases).mark_bar(color=TEAL, point={'color': TEAL}).encode(
        x=alt.X('date', title='Week'),
        y=alt.Y('signed_leases_needed', title='# Signed Leases'), 
        color=alt.condition(
            alt.datum.is_deadline_week,
            alt.value(TEAL), 
            alt.value(DARK_TEAL)  
        ),
        tooltip=[
            alt.Tooltip('date', title='Week Start'),
            alt.Tooltip('signed_leases_needed', title='# Signed Leases Needed')
        ]
    ).properties(
        width=600,
        height=400
    )
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
        "Projected Economic Occupancy Based on Target",
        help = "Based on a specified deadline for x number of leases to be signed, what is the projected economic occupancy?"
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

    # Select a deadline and a number of leases
    deadline_col, num_leases_col = st.columns([2, 2])
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

    st.write(f'**Assumption 1:** each lease signed (up to the number of leases selected) is evenly distributed from today to the selected deadline ({selected_deadline.strftime("%Y-%m-%d")}).')
    st.write('**Assumption 2:** each lease signed has a length of 365 days.')
    st.write('**Assumption 3:** move in, aka GPR recovery, occurs 8 days after the lease signed date.')
    economic_occupancy_chart(signed_leases[signed_leases['date'] <= selected_deadline + relativedelta(weeks=3)], 'economic_occupancy_budget', ['economic_occupancy_new_projected', 'economic_occupancy_prior_projected'], 'day')



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



    
# def num_leases_to_target_extra(economic_occupancy_df):
#     st.subheader("Number of Leases to Target (Option 1)")

#     with st.container(border=True):
#         deadline_col, deadline_date_col = st.columns([6, 1])
#         with deadline_col:
#             deadline_options = {
#                 'This week': TODAY + relativedelta(weeks=0, weekday=6),
#                 'Next week': TODAY + relativedelta(weeks=1, weekday=6), 
#                 'Next next week': TODAY + relativedelta(weeks=2, weekday=6), 
#                 'This month': TODAY.replace(day=1) + relativedelta(months=1) - relativedelta(days=1), 
#                 'Next month': TODAY.replace(day=1) + relativedelta(months=2) - relativedelta(days=1)
#             }
#             # deadline_options_display = [f"{key} ({value})" for key, value in deadline_options.items()]
#             selected_deadline = st.selectbox("Select a deadline", list(deadline_options.keys()), 
#                                             index=0, 
#                                             help="Deadline date is end of the selected time period",
#                                             key="num_leases_to_target_deadline")
#         with deadline_date_col:
#             deadline_date = deadline_options[selected_deadline]
#             st.markdown(
#                 f"""
#                 <div style='text-align: right; padding: 10px'>
#                     <h6>Deadline Date</h6>
#                     <h6 style='color: {TEAL};'>{deadline_date.strftime('%Y-%m-%d')}</h6>
#                 </div>
#                 """,
#                 unsafe_allow_html=True
#             )

#         day_economic_occupancy = economic_occupancy_df[(economic_occupancy_df['time_granularity'] == 'day') &
#                                                         (economic_occupancy_df['date'] >= TODAY) &
        #                                                 (economic_occupancy_df['date'] <= deadline_date)
        # ].groupby('date').agg(
        #     num_properties=('num_properties', 'sum'),
        #     num_properties_potentially_occupied=('num_properties_potentially_occupied', 'sum'),
        #     num_properties_occupied=('num_properties_occupied', 'sum'),
        #     total_gpr=('total_gpr', 'sum'),
        #     total_gpr_potentially_occupied=('total_gpr_potentially_occupied', 'sum'),
        #     total_gpr_occupied=('total_gpr_occupied', 'sum'),
        #     total_gpr_occupied_budget=('total_gpr_occupied_budget', 'sum')
        # ).reset_index()

        # day_economic_occupancy['hole'] = day_economic_occupancy['total_gpr_occupied_budget'] - day_economic_occupancy['total_gpr_occupied']
        # deadline_row = day_economic_occupancy[day_economic_occupancy['date'] == deadline_date]
        # hole_col, vacant_homes_col, recoverable_gpr_col, leases_needed_col = st.columns(4)
        # with hole_col:
        #     hole = deadline_row['hole'].iloc[0]
        #     st.metric("Hole", f"${hole:,.2f}")
        # with vacant_homes_col:
        #     vacant_homes = deadline_row['num_properties'].iloc[0] - deadline_row['num_properties_occupied'].iloc[0]
        #     st.metric("Vacant Homes", f"{vacant_homes:,.0f}")
        # with recoverable_gpr_col:
        #     recoverable_gpr_per_home_per_day = (deadline_row['total_gpr'].iloc[0] - deadline_row['total_gpr_occupied'].iloc[0]) / (deadline_row['num_properties'].iloc[0] - deadline_row['num_properties_occupied'].iloc[0])
        #     st.metric("Recoverable GPR per Home per Day", f"${recoverable_gpr_per_home_per_day:,.2f}")
        # with leases_needed_col:
        #     leases_needed = hole / recoverable_gpr_per_home_per_day
        #     st.metric("Leases Needed", f"{leases_needed:,.0f}")

        # st.write('**Recovery Days Table:**')
        # st.dataframe(day_economic_occupancy)


