import altair as alt
import streamlit as st
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
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


def subheader_with_help(text: str, help_text: str):
        st.markdown(
            f"""
            <style>
            .subheader-with-help {{
                display: flex;
                align-items: center;
                gap: 0px; 
            }}
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
                left: 50%;
                transform: translateX(-50%);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 9999;
                white-space: normal;
                word-wrap: break-word;
            }}
            .st-help-icon:hover .st-help-text {{
                visibility: visible;
                opacity: 1;
            }}
            </style>

            <div class="subheader-with-help">
            <h3>{text}</h3>
            <span class="st-help-icon">ℹ
                <span class="st-help-text">{help_text}</span>
            </span>
            </div>
            """,
            unsafe_allow_html=True,
        )



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



def filters(df, tab_name, community_filter=False, time_granularity_help_text=None):
    if community_filter:
        col_preselected_dates, col_date_range, col_time_granularity, col_fund, col_market, col_community = st.columns(6)
    else:
        col_preselected_dates, col_date_range, col_time_granularity, col_fund, col_market = st.columns(5)
    filtered_df = df.copy()


    today = datetime.now().date()
    this_monday = today - relativedelta(days=today.weekday())  # current week's Monday
    last_sunday = this_monday - relativedelta(days=1)          # last week's Sunday

    options_dict = {
        'Select...': (
            datetime.now() - timedelta(days=30), 
            datetime.now()
        ),
        # Weeks
        'This week': (
            this_monday,  # Monday of this week
            today         # Today
        ),
        'Last week': (
            this_monday - relativedelta(weeks=1),   # Monday of last week
            last_sunday                             # Sunday of last week
        ),
        'Last 2 weeks': (
            this_monday - relativedelta(weeks=2),   # Monday 2 weeks ago
            last_sunday                             # Sunday of last week
        ),
        'Last 3 weeks': (
            this_monday - relativedelta(weeks=3),   # Monday 3 weeks ago
            last_sunday                             # Sunday of last week
        ),

        # Months
        'This month': (
            today.replace(day=1),  # 1st of this month
            today                  # Today
        ),
        'Last month': (
            (today.replace(day=1) - relativedelta(months=1)),    # 1st of last month
            today.replace(day=1) - relativedelta(days=1)         # last day of last month
        ),
        'Last 2 months': (
            (today.replace(day=1) - relativedelta(months=2)),    # 1st of 2 months ago
            today.replace(day=1) - relativedelta(days=1)         # last day of last month
        ),
        'Last 3 months': (
            (today.replace(day=1) - relativedelta(months=3)),    # 1st of 3 months ago
            today.replace(day=1) - relativedelta(days=1)         # last day of last month
        ),

        # Year
        'This year': (
            datetime(today.year, 1, 1),  # Jan 1 of this year
            today                    # today
        )
    }
    with col_preselected_dates:
        preselected_dates = st.selectbox("Quick select period range", 
                                          options_dict.keys(), 
                                          key=f'{tab_name}_preselected_dates', 
                                          help="Will override the period range selection filter to the right")

    with col_date_range:
        preselected_start_date, preselected_end_date = options_dict[preselected_dates]
        date_range = st.date_input("Pick a period range",
                                   value=(preselected_start_date, preselected_end_date),
                                   format='MM/DD/YYYY',
                                   key=f'{tab_name}_date_range', 
                                   help=time_granularity_help_text)
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
        dy=-2, 
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
        id_vars=['period_end'],
        value_vars=[budget_col] + series_cols,
        var_name='type',
        value_name='value'
    )

    type_mappings = {}
    for type in economic_occupancy_chart['type'].unique():
        type_mappings[type] = type.replace('economic_occupancy_', '').replace('_', ' ').title()
    economic_occupancy_chart['time_str'] = pd.to_datetime(economic_occupancy_chart['period_end']).dt.strftime('%Y-%m-%d')
    economic_occupancy_chart['type'] = economic_occupancy_chart['type'].map(type_mappings) 
    
    # set lower bound of y-axis
    min_economic_occupancy = max(economic_occupancy_chart['value'].min() - 5, 0)

    # Define a selection that will be used to interact with the legend
    selection = alt.selection_single(fields=['type'], bind='legend')
    chart = alt.Chart(economic_occupancy_chart).mark_line(point=True).encode(
        x=alt.X('time_str:O', title=f'{selected_time_granularity.title()} End', axis=alt.Axis(labelAngle=0)),
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
            alt.Tooltip('value:Q', title='Value (%)', format='.2f'), 
        ],
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    ).add_selection(
        selection
    ).properties(
        width=600,
        height=400
    )
    return chart

    

def target_leases_per_week_chart(target_leases_df, selection, case, funds):
    return alt.Chart(target_leases_df).mark_bar(color=TEAL, point={'color': TEAL}).encode(
        x=alt.X('week_end', title='Week End', axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f'signed_leases_needed_{case}', title='# Leases to Sign'), 
        color=alt.value(LIGHT_TEAL if case == 'best_case' else DARK_TEAL
        ) if len(funds) == 1 else alt.Color(
            'fund:N', 
            scale=alt.Scale(range=[TEAL, LIGHT_TEAL, DARK_TEAL, PURPLE, LIGHT_PURPLE, DARK_PURPLE]), 
            title='Fund'
        ), 
        tooltip=[
            alt.Tooltip(f'{case}', title='Case'), 
            alt.Tooltip('fund', title='Fund'),
            alt.Tooltip('week_end', title='Week End'),
            alt.Tooltip(f'signed_leases_needed_{case}', title='# Leases to Sign')
        ], 
        opacity=alt.condition(selection, alt.value(1), alt.value(0.1))
    ).add_selection(
        selection
    ).properties(
        width=600,
        height=400
    )


def target_leases_per_week_text(target_leases_df, chart, case, funds):
    if len(funds) != 1:
        total_leases = (
            target_leases_df
            .groupby('week_end')
            .agg(total_signed_leases_needed=(f'signed_leases_needed_{case}', 'sum'))
            .reset_index()
        )
        return alt.Chart(total_leases).mark_text(
            align='center',
            baseline='bottom',
            dy=-2,
            color=DARK_TEAL
        ).encode(
            x='week_end',
            y=f'total_signed_leases_needed',
            text=f'total_signed_leases_needed'
        ) 
    else: 
        return chart.mark_text(
            align='center',
            baseline='bottom',
            dy=-2
        ).encode(
            text=f'signed_leases_needed_{case}:Q'
        )




    
