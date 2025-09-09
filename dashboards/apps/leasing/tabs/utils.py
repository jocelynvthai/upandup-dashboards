import altair as alt
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

LIGHT_GRAY = "#d3d3d3"
GRAY = "#808080" 
LIGHT_TEAL = "#5cc9b8" 
TEAL = "#15b8a6" 
DARK_TEAL = "#0E8074"
LIGHT_PURPLE = "#d1c4e9" 
PURPLE = "#9575cd" 
DARK_PURPLE = "#512da8" 
LIGHT_RED = "#ffcdd2"
RED = "#f44336"
ORANGE = "#ffa500"


def help_icon(help_text: str, align: str = "center"):
    # align: "center" | "left" | "right"
    align_class = {
        "center": "align-center",
        "left": "align-left",
        "right": "align-right"
    }.get(align, "align-center")

    st.markdown(
        f"""
        <style>
        .st-help-icon {{
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 18px;
          height: 18px;
          background-color: rgb(239, 240, 241);
          color: rgb(68,68,68);
          border-radius: 50%;
          font-size: 12px;
          cursor: help;
          position: relative;
        }}
        .st-help-text {{
          visibility: hidden;
          opacity: 0;
          min-width: max-content;
          max-width: 60vw;
          background: white;
          color: #111;
          border: 1px solid #e6e6e6;
          border-radius: 4px;
          padding: 6px 8px;
          font-size: 13px;
          line-height: 1.3;
          position: absolute;
          top: 24px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          z-index: 9999;
          white-space: normal;
          word-wrap: break-word;
        }}

        /* Default: center */
        .st-help-icon.align-center .st-help-text {{
          left: 50%;
          transform: translateX(-50%);
        }}

        /* Left aligned: tooltip left edge aligns with icon left */
        .st-help-icon.align-left .st-help-text {{
          left: 0;
          transform: none;
        }}

        /* Right aligned: tooltip right edge aligns with icon right */
        .st-help-icon.align-right .st-help-text {{
          right: 0;
          left: auto;
          transform: none;
        }}

        /* show on hover */
        .st-help-icon:hover .st-help-text {{
          visibility: visible;
          opacity: 1;
        }}
        </style>

        <span class="st-help-icon {align_class}">ℹ
          <span class="st-help-text">{help_text}</span>
        </span>
        """,
        unsafe_allow_html=True,
    )


def filters(df, tab_name, community_filter=False):
    if community_filter:
        col_date_range, col_time_granularity, col_fund, col_market, col_community = st.columns(5)
    else:
        col_date_range, col_time_granularity, col_fund, col_market = st.columns(4)
    filtered_df = df.copy()

    with col_date_range:
        date_range = st.date_input("Pick a period range",
                                   value=(datetime.now() - timedelta(days=30),  datetime.now()),
                                   format='MM/DD/YYYY',
                                   key=f'{tab_name}_date_range')
        if len(date_range) != 2:
            st.stop()
        else:
            start_date, end_date = date_range[0], date_range[1]
            filtered_df = filtered_df[(filtered_df['date'] <= end_date) &
                                                                        (filtered_df['date'] >= start_date)]

    with col_time_granularity:
        available_granularities = filtered_df['time_granularity'].unique()
        selected_time_granularity = st.selectbox("Select a time granularity",
                                      options=[g for g in ['day', 'week', 'month', 'quarter', 'year'] if g in available_granularities], 
                                      index=int(np.where(available_granularities == "week")[0][0]) if 'week' in available_granularities else 0,  
                                      key=f'{tab_name}_time_granularity')
        filtered_df = filtered_df[filtered_df['time_granularity'] == selected_time_granularity]

    with col_fund:
        selected_fund = st.selectbox("Select a fund", 
                                     options=['All'] + sorted(filtered_df['fund'].unique()), 
                                     index=0, 
                                     key=f'{tab_name}_fund')
        if selected_fund != 'All':
            filtered_df = filtered_df[filtered_df['fund'] == selected_fund]

    with col_market:
        selected_market = st.selectbox("Select a market",
                                       options=['All'] + sorted(filtered_df['market'].unique()), 
                                       index=0,
                                       key=f'{tab_name}_market')
        if selected_market != 'All':
            filtered_df = filtered_df[filtered_df['market'] == selected_market]

    if community_filter:
        with col_community:
            selected_community = st.selectbox("Select a community",
                                               options=['All'] + sorted(filtered_df['community'].dropna().unique()), 
                                               index=0, 
                                               key=f'{tab_name}_community')
            if selected_community != 'All':
                filtered_df = filtered_df[filtered_df['community'] == selected_community]

    return filtered_df, selected_time_granularity


def create_funnel_chart(grouped_df, funnel_stages, first_stage, second_stage, time_metric):
    first_stage_column = f"total_num_{first_stage.lower().replace(' ', '_')}"
    second_stage_column = f"total_num_{second_stage.lower().replace(' ', '_')}"
    time_metric_column = f"avg_{time_metric}_between_stages"
    time_title = f"Average Time Spent ({time_metric.upper()})"

    grouped_df['conversion_rate'] = grouped_df[second_stage_column] / grouped_df[first_stage_column]
    columns_to_sum = []
    for i in range(funnel_stages.index(first_stage), funnel_stages.index(second_stage)):
        columns_to_sum.append(f"total_{time_metric}_{funnel_stages[i].lower().replace(' ', '_')}_to_{funnel_stages[i+1].lower().replace(' ', '_')}")
    grouped_df[time_metric_column] = grouped_df[columns_to_sum].sum(axis=1) / grouped_df[second_stage_column]

    # First bar chart
    first_bars = alt.Chart(grouped_df).mark_bar(size=25).encode(
        x=alt.X('date:T', title='Date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y(f"{first_stage_column}:Q", 
                title='Count',
                axis=alt.Axis(titleColor=GRAY)),
        color=alt.value(LIGHT_GRAY),
        tooltip=[
            alt.Tooltip('date:T', title='Date'),
            alt.Tooltip(f"{first_stage_column}:Q", 
                       title=first_stage),
            alt.Tooltip("conversion_rate:Q", 
                       format='.1%', 
                       title='Conversion Rate')
        ]
    )

    # Second bar chart
    second_bars = alt.Chart(grouped_df).mark_bar(size=25).encode(
        x=alt.X('date:T', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y(f"{second_stage_column}:Q"),
        color=alt.value(TEAL),
        tooltip=[
            alt.Tooltip('date:T', title='Date'),
            alt.Tooltip(f"{second_stage_column}:Q", 
                       title=second_stage, 
                       format=',.0f'),
            alt.Tooltip("conversion_rate:Q", 
                       format='.1%', 
                       title='Conversion Rate')
        ]
    )

    # Conversion rate labels (second bar / first bar)
    text = alt.Chart(grouped_df).mark_text(
        align='center',
        baseline='bottom',
        dy=-5, 
        color=DARK_TEAL
    ).encode(
        x=alt.X('date:T'),
        y=alt.Y(f"{second_stage_column}:Q"),
        text=alt.Text("conversion_rate:Q", format='.0%'),
        opacity=alt.condition(
            'isValid(datum.conversion_rate)',
            alt.value(1),
            alt.value(0)
        )
    )
    
    line = alt.Chart(grouped_df).mark_line(
        point={'color': PURPLE},
        color=PURPLE
    ).encode(
        x=alt.X('date:T'),
        y=alt.Y(f"{time_metric_column}:Q",
                title=time_title),
        tooltip=[
            alt.Tooltip('date:T'),
            alt.Tooltip(f"{time_metric_column}:Q", 
                       format=',.2f', 
                       title=time_title)
        ]
    )

    # Create manual legend
    legend_data = pd.DataFrame({
        'label': [first_stage, second_stage, time_title],
        'color': [LIGHT_GRAY, TEAL, PURPLE], 
        'x': [1, 1, 1],
        'y': [1, 2, 3]
    })
    legend_rect = alt.Chart(legend_data.iloc[:2]).mark_rect(
        width=15, height=15
    ).encode(
        x=alt.X('x:O', axis=None, scale=alt.Scale(domain=[1])),
        y=alt.Y('y:O', axis=None),
        color=alt.Color('color:N', scale=None, legend=None)
    )
    legend_line = alt.Chart(legend_data.iloc[2:]).mark_line(point=True
    ).encode(
        x=alt.X('x:O', axis=None, scale=alt.Scale(domain=[1])),
        y=alt.Y('y:O', axis=None),
        color=alt.Color('color:N', scale=None, legend=None)
    )
    legend_text = alt.Chart(legend_data).mark_text(
        align='left', dx=25, fontSize=11
    ).encode(
        x=alt.X('x:O', axis=None, scale=alt.Scale(domain=[1])),
        y=alt.Y('y:O', axis=None),
        text='label:N'
    )
    legend = alt.layer(legend_rect, legend_line, legend_text).properties(
        width=50,  
        height=80
    )

    # Layer and plot the charts
    bars_layer = alt.layer(first_bars, second_bars, text).properties(
        width=1000,
        height=400  # Adjust the height as needed
    )
    main_chart = alt.layer(bars_layer, line).resolve_scale(y='independent')
    
    # Combine main chart with legend - main chart will expand, legend stays fixed
    chart = alt.hconcat(main_chart, legend, spacing=10)
    st.altair_chart(chart, use_container_width=True) 


def economic_occupancy_chart(economic_occupancy_df, budget_col, series_cols, selected_time_granularity):
    economic_occupancy_chart = economic_occupancy_df.melt(
        id_vars=['date'],
        value_vars=[budget_col] + series_cols,
        var_name='type',
        value_name='value'
    )

    type_mappings = {}
    for type in economic_occupancy_chart['type'].unique():
        type_mappings[type] = type.replace('economic_occupancy_', '').replace('_', ' ').title()
    economic_occupancy_chart['time_str'] = pd.to_datetime(economic_occupancy_chart['date']).dt.strftime('%Y-%m-%d')
    economic_occupancy_chart['type'] = economic_occupancy_chart['type'].map(type_mappings) 
    
    # set lower bound of y-axis
    min_economic_occupancy = max(economic_occupancy_chart['value'].min() - 10, 0)

    # Define a selection that will be used to interact with the legend
    selection = alt.selection_single(fields=['type'], bind='legend')
    chart = alt.Chart(economic_occupancy_chart).mark_line(point=True).encode(
        x=alt.X('time_str:O', title=f'{selected_time_granularity.title()}', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('value:Q', title='Economic Occupancy (%)',
                scale=alt.Scale(domain=[min_economic_occupancy, 100], padding=10)),
        color=alt.Color(
            'type:N',
            scale=alt.Scale(
                domain=type_mappings.values(),
                range=[GRAY, TEAL] if len(series_cols) == 1 else [GRAY, TEAL, PURPLE]
            ),
            legend=alt.Legend(title="Type", symbolType='circle')
        ),
        tooltip=[
            alt.Tooltip("time_str:O", title=selected_time_granularity.title()),
            alt.Tooltip('type:N', title='Type'),
            alt.Tooltip('value:Q', title='Value (%)', format='.2f')
        ],
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    ).add_selection(
        selection
    )
    st.altair_chart(chart)


def generate_new_economic_occupancy_df(day_economic_occupancy, selected_deadline, selected_num_leases):
    today = datetime.now().date()
    # Generate a uniform lease signed distribution between TODAY and selected_deadline
    num_days = (selected_deadline - today).days + 1
    interval = num_days / selected_num_leases
    lease_signed_dates = [today + timedelta(days=round(i*interval)) for i in range(selected_num_leases)]

    lease_distribution = pd.DataFrame({
        'date': lease_signed_dates,
        'leases': [1] * (selected_num_leases),
    }).groupby('date').agg(
        num_leases_signed=('leases', 'sum')
    ).reset_index()

    # Set the recovery start to be 3 days after the lease signed date
    signed_leases = day_economic_occupancy.merge(lease_distribution, left_on='date', right_on='date', how='left').fillna(0)
    signed_leases['recovery_leases_start'] = signed_leases['num_leases_signed'].shift(8, fill_value=0)


    signed_leases['recovery_leases'] = 0
    for idx, row in signed_leases.iterrows():
        if row['recovery_leases_start'] > 0:
            start_idx = idx
            end_idx = min(idx + 365, len(signed_leases))  # cap at dataframe length
            signed_leases.loc[start_idx:end_idx-1, 'recovery_leases'] += row['recovery_leases_start']

    signed_leases['recovery_gpr'] = signed_leases['total_gpr_per_property'] * signed_leases['recovery_leases']
    signed_leases['economic_occupancy_budget'] = signed_leases['total_gpr_occupied_budget'] * 100 / signed_leases['total_gpr']
    signed_leases['economic_occupancy_prior_projected'] = (signed_leases['total_gpr_occupied']) * 100 / signed_leases['total_gpr']
    signed_leases['economic_occupancy_new_projected'] = (signed_leases['total_gpr_occupied'] + signed_leases['recovery_gpr']) * 100 / signed_leases['total_gpr']

    return signed_leases, lease_distribution
    
