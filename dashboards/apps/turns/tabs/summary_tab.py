import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import streamlit as st
import altair as alt

from tabs.utils import LIGHT_GRAY, GRAY, DARK_TEAL, TEAL, LIGHT_TEAL

def turn_filters(turns_df):
    st.subheader("Turn Cost Over Time Filters")
    col_fund, col_market, col_level = st.columns(3)

    filtered_turns_df = turns_df.copy()

    with col_fund:
        selected_fund = st.selectbox("Select Fund", ['All'] + sorted(list(turns_df['fund'].unique())))
        if selected_fund != 'All':
            filtered_turns_df = filtered_turns_df[filtered_turns_df['fund'] == selected_fund]
    with col_market:
        selected_market = st.selectbox("Select Market", ['All'] + sorted(list(turns_df['market'].unique())))
        if selected_market != 'All':
            filtered_turns_df = filtered_turns_df[filtered_turns_df['market'] == selected_market]
    with col_level:
        selected_time_granularity = st.selectbox("Select time granularity", ['week', 'month'])
        st.session_state['time_granularity_col'] = f'{selected_time_granularity}_end_date'
    
    # --- Build period columns ---
    if selected_time_granularity == 'week':
        st.session_state['time_granularity_title'] = 'Week End (Project End Date)'
        filtered_turns_df[st.session_state['time_granularity_col']] = pd.to_datetime(filtered_turns_df['project_end_date']).apply(
            lambda d: d + relativedelta(days=6 - d.dayofweek) if pd.notnull(d) else pd.NaT
        )
        st.session_state['cutoff_date'] = datetime.now().date() + relativedelta(
            days=6 - datetime.now().date().weekday()
        ) - timedelta(weeks=12)
    else:
        st.session_state['time_granularity_title'] = 'Month End (Project End Date)'
        filtered_turns_df[st.session_state['time_granularity_col']] = pd.to_datetime(filtered_turns_df['project_end_date']).apply(
            lambda d: (d + relativedelta(day=31)) if pd.notnull(d) else pd.NaT
        )
        st.session_state['cutoff_date'] = datetime.now().date() + relativedelta(day=31) - relativedelta(months=3)

    return filtered_turns_df



def total_turn_cost_over_time(turns_df):
    st.subheader("Turn Cost Over Time (Waterfall)")

    time_granularity_str_col = f'{st.session_state["time_granularity_col"]}_str'
    turns_df = turns_df[turns_df[st.session_state['time_granularity_col']] >= pd.to_datetime(st.session_state['cutoff_date'])].copy()

    # --- Group data ---
    turns_df[time_granularity_str_col] = turns_df[st.session_state['time_granularity_col']].dt.strftime('%Y-%m-%d')
    grouped_df = turns_df.groupby(time_granularity_str_col, as_index=False).agg({
        'rental_id': 'count',
        'project_total_estimated_cost': 'sum',
        'project_invoiced_cost': 'sum',
        'clawback_amount': 'sum',
    }).rename(columns={'rental_id': 'num_turns'})

    # --- Add costs per turn ---
    grouped_df['project_total_estimated_cost_per_turn'] = grouped_df['project_total_estimated_cost'] / grouped_df['num_turns']
    grouped_df['project_invoiced_cost_per_turn'] = grouped_df['project_invoiced_cost'] / grouped_df['num_turns']
    grouped_df['turn_clawbacks_per_turn'] = grouped_df['clawback_amount'] / grouped_df['num_turns']

    for cost_type in ['total', 'per_turn']:

        # --- Build waterfall rows per period ---
        rows = []
        for _, r in grouped_df.iterrows():
            period = r[time_granularity_str_col]
            num_turns = float(r['num_turns'])
            if cost_type == 'total':
                est = float(r['project_total_estimated_cost'])
                inv = float(r['project_invoiced_cost'])
                cb  = float(r['clawback_amount'])
            else:
                est = float(r['project_total_estimated_cost_per_turn'])
                inv = float(r['project_invoiced_cost_per_turn'])
                cb  = float(r['turn_clawbacks_per_turn'])
            final_total = inv - cb

            # Order for display:
            # 1) Estimated Cost (standalone)
            # 2) Invoiced (absolute — starts ladder at 0)
            # 3) Chargebacks (relative, negative)
            # 4) Final Total (absolute total to land at inv - cb)
            rows.append({'period': period, 'step': 'Estimated', 'amount': est, 'role': 'base', 'num_turns': num_turns})
            rows.append({'period': period, 'step': 'Invoiced', 'amount': inv, 'role': 'absolute', 'num_turns': num_turns})
            rows.append({'period': period, 'step': 'Clawbacks', 'amount': -cb, 'role': 'change', 'num_turns': num_turns})
            rows.append({'period': period, 'step': 'Final Total', 'amount': final_total, 'role': 'total', 'num_turns': num_turns})

        wf = pd.DataFrame(rows)

        # keep steps ordered per period
        wf['step'] = pd.Categorical(wf['step'], categories=['Estimated', 'Invoiced', 'Clawbacks', 'Final Total'], ordered=True)
        wf = wf.sort_values(['period', 'step']).reset_index(drop=True)

        # --- Compute previous / cumulative per period, treating 'base' as standalone and NOT part of ladder ---
        wf['previous'] = 0.0
        wf['cumulative'] = 0.0

        for period, grp in wf.groupby('period', sort=False):
            # running ladder only uses absolute/change/total rows (ignores base)
            running = 0.0
            # iterate in display order
            for idx in grp.index.tolist():
                role = wf.at[idx, 'role']
                amt = float(wf.at[idx, 'amount'])
                if role == 'base':
                    # standalone: bottom = 0, top = amt ; does NOT change running
                    wf.at[idx, 'previous'] = 0.0
                    wf.at[idx, 'cumulative'] = amt
                elif role == 'absolute':
                    # absolute start of ladder: bottom = 0, top = amt ; set running to amt
                    wf.at[idx, 'previous'] = 0.0
                    wf.at[idx, 'cumulative'] = amt
                    running = amt
                elif role == 'change':
                    # relative change: bottom = running, top = running + amt ; update running
                    wf.at[idx, 'previous'] = running
                    running = running + amt
                    wf.at[idx, 'cumulative'] = running
                elif role == 'total':
                    # draw as total anchored to final_total (absolute). previous = running
                    wf.at[idx, 'previous'] = 0.0
                    wf.at[idx, 'cumulative'] = amt
                    running = amt

        # compute bottom/top for Altair
        wf['bottom'] = wf[['previous', 'cumulative']].min(axis=1)
        wf['top'] = wf[['previous', 'cumulative']].max(axis=1)

        # st.dataframe(wf[['period','step','role','amount','previous','cumulative','bottom','top']].head(50), use_container_width=True)

        # --- Prepare num_turns data for line chart ---
        num_turns_df = grouped_df[[time_granularity_str_col, 'num_turns']].rename(
            columns={time_granularity_str_col: 'period'}
        )

        # --- Waterfall Chart ---
        color_scale = alt.Scale(
            domain=['Estimated', 'Invoiced', 'Clawbacks', 'Final Total'],
            range=[LIGHT_GRAY, LIGHT_TEAL, TEAL, DARK_TEAL]
        )
        waterfall_chart = alt.Chart(wf).mark_bar().encode(
            x=alt.X('period:N', title= st.session_state['time_granularity_title'], axis=alt.Axis(labelAngle=-90)),
            xOffset='step:N',
            y=alt.Y('bottom:Q', title='Cost'),
            y2='top:Q',
            color=alt.Color(
                'step:N',
                scale=color_scale,
                legend=alt.Legend(
                    title="Waterfall Components",
                    orient="right"
                )
            ),
            tooltip=[
                alt.Tooltip('period:N', title= st.session_state['time_granularity_title']),
                alt.Tooltip('step:N', title='Step'),
                alt.Tooltip('amount:Q', title='Amount', format='$,.0f'),
                alt.Tooltip('num_turns:Q', title='# Turns'),
            ]
        ).properties(
            width=700,
            height=420,
            title="Total Turn Cost" if cost_type == 'total' else "Cost Per Turn"
        )

        # --- Number of Turns Line Chart ---
        num_turns_line = alt.Chart(num_turns_df).mark_line(color=GRAY, point={'color': GRAY}).encode(
            x=alt.X('period:N', title= st.session_state['time_granularity_title'], axis=alt.Axis(labelAngle=-90)),
            y=alt.Y('num_turns:Q', title='# Turns', axis=alt.Axis(titleColor='gray')),
            tooltip=[
                alt.Tooltip('period:N', title=st.session_state['time_granularity_title']),
                alt.Tooltip('num_turns:Q', title='# Turns'),
            ]
        )

        # --- Combine Charts ---
        # chart = alt.layer(waterfall_chart, num_turns_line).resolve_scale(y='independent')
        chart = alt.layer(waterfall_chart, num_turns_line).resolve_scale(y='independent')
        st.altair_chart(chart, use_container_width=True)




def turns_breakdown(turns_df):
    st.subheader("Turns Breakdown")

    selected_time_granularity_date = st.date_input(f"Pick a {st.session_state['time_granularity_title']}", 
                                format='MM/DD/YYYY',
                                value=turns_df[st.session_state['time_granularity_col']].max(),
                                min_value=st.session_state['cutoff_date'],
                                key=f'{st.session_state["time_granularity_col"]}_date_input')
    if selected_time_granularity_date is not None:
        selected_turns_df = turns_df[turns_df[st.session_state['time_granularity_col']] == pd.to_datetime(selected_time_granularity_date)]
        selected_turns_df['hudson_link'] = "https://hudson.upandup.co/rent-roll/" + selected_turns_df['rental_id'].astype(str)
        st.dataframe(
            selected_turns_df[[
                'hudson_link', 'address', 'fund', 'market', 'project_end_date', 'project_total_estimated_cost', 'project_invoiced_cost', 'clawback_amount'
            ]].rename(columns={
                'address': 'Address',
                'fund': 'Fund',
                'market': 'Market',
                'project_end_date': 'Project End Date',
                'project_total_estimated_cost': 'Estimated Cost',
                'project_invoiced_cost': 'Invoiced Cost',
                'clawback_amount': 'Clawback Amount'
            }).sort_values(by='Project End Date').reset_index(drop=True),
            column_config={
                "hudson_link": st.column_config.LinkColumn(
                    "Hudson",
                    display_text=":material/link:",
                    width="small"
                )
            }
        )



def turns_without_ends_dates(turns_df):
    st.subheader("Turns Missing Project End Date")

    # Filter missing end dates
    missing_end_dates_df = turns_df[turns_df['project_end_date'].isna()].copy()
    missing_end_dates_df['hudson_link'] = (
        "https://hudson.upandup.co/rent-roll/" + 
        missing_end_dates_df['rental_id'].astype(str)
    )

    # Only show those starting 2025+
    missing_end_dates_df = missing_end_dates_df[
        missing_end_dates_df['project_start_date'] >= pd.to_datetime('2025-01-01')
    ].copy()

    # Add display column
    missing_end_dates_df['project_end_date_display'] = missing_end_dates_df['project_end_date'].apply(
        lambda x: "MISSING" if pd.isna(x) else x.strftime('%Y-%m-%d')
    )

    # Reorder / rename
    df_display = missing_end_dates_df[
        ['hudson_link', 'address', 'fund', 'market', 'project_start_date', 'project_end_date_display']
    ].rename(columns={
        'address': 'Address',
        'fund': 'Fund',
        'market': 'Market',
        'project_start_date': 'Project Start Date',
        'project_end_date_display': 'Project End Date'
    }).sort_values(by='Project Start Date').reset_index(drop=True)

    # Style MISSING red
    def highlight_missing(val):
        if val == "MISSING":
            return "color: red;"
        return ""

    styled = df_display.style.applymap(highlight_missing, subset=['Project End Date'])
    st.dataframe(
        styled,
        column_config={
            "hudson_link": st.column_config.LinkColumn(
                "Hudson",
                display_text=":material/link:",
                width="small"
            ),
        }
    )









    