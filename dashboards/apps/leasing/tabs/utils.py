import altair as alt
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

LIGHT_GRAY = "#d3d3d3"
GRAY = "#808080" 
LIGHT_TEAL = "#5cc9b8" 
TEAL = "#15b8a6" 
LIGHT_PURPLE = "#d1c4e9" 
PURPLE = "#9575cd" 
DARK_PURPLE = "#512da8" 
LIGHT_RED = "#ffcdd2"
RED = "#f44336"
#5cc9b8 - A medium-light teal (good balance)
#7dd3c0 - Lighter teal
#a3e0d1 - Very light teal
#c7ebe3 - Extra light teal (subtle)



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
                                     options=['All'] + list(filtered_df['fund'].unique()), 
                                     index=0, 
                                     key=f'{tab_name}_fund')
        if selected_fund != 'All':
            filtered_df = filtered_df[filtered_df['fund'] == selected_fund]

    with col_market:
        selected_market = st.selectbox("Select a market",
                                       options=['All'] + list(filtered_df['market'].unique()), 
                                       index=0,
                                       key=f'{tab_name}_market')
        if selected_market != 'All':
            filtered_df = filtered_df[filtered_df['market'] == selected_market]

    if community_filter:
        with col_community:
            selected_community = st.selectbox("Select a community",
                                               options=['All'] + list(filtered_df['community'].unique()), 
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
        dy=-5
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
        point=alt.OverlayMarkDef(color=PURPLE),  # Set point color to purple
        color=PURPLE,
        strokeWidth=2
    ).encode(
        x=alt.X('date:T'),
        y=alt.Y(f"{time_metric_column}:Q",
                title=time_title),
        tooltip=[
            alt.Tooltip('date:T'),
            alt.Tooltip(f"{time_metric}:Q", 
                       format=',.1f', 
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
    legend_line = alt.Chart(legend_data.iloc[2:]).mark_line(
        strokeWidth=3, point=True
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


def create_funnel_chart_old(grouped_df, funnel_stages, chart_type="application"):
    """
    Create a funnel chart showing conversion rates and timing between stages.
    Args:
        grouped_df: DataFrame containing the funnel metrics
        funnel_stages: Dictionary defining the funnel stage configurations
        chart_type: String identifier for the chart (used for unique streamlit keys)
    """
    
    # Add stage selector
    selected_stage = st.selectbox("Select Funnel Stage", 
                                  options=list(funnel_stages.keys()), 
                                  key=f'{chart_type}_funnel_stage')
    stage_config = funnel_stages[selected_stage]
    
    # First bar chart
    first_bars = alt.Chart(grouped_df).mark_bar(size=25).encode(
        x=alt.X('date:T', title='Date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y(f"{stage_config['first_metric']}:Q", 
                title='Count',
                axis=alt.Axis(titleColor=GRAY)),
        color=alt.value(LIGHT_GRAY),
        tooltip=[
            alt.Tooltip('date:T'),
            alt.Tooltip(f"{stage_config['first_metric']}:Q", 
                       title=stage_config['first_label'], 
                       format=',.0f'),
            alt.Tooltip(f"{stage_config['percentage']}:Q", 
                       format='.1%', 
                       title='Conversion Rate')
        ]
    )

    # Second bar chart
    second_bars = alt.Chart(grouped_df).mark_bar(size=25).encode(
        x=alt.X('date:T', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y(f"{stage_config['second_metric']}:Q"),
        color=alt.value(TEAL),
        tooltip=[
            alt.Tooltip('date:T'),
            alt.Tooltip(f"{stage_config['second_metric']}:Q", 
                       title=stage_config['second_label'], 
                       format=',.0f'),
            alt.Tooltip(f"{stage_config['percentage']}:Q", 
                       format='.1%', 
                       title='Conversion Rate')
        ]
    )

    # Conversion rate labels (second bar / first bar)
    text = alt.Chart(grouped_df).mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    ).encode(
        x=alt.X('date:T'),
        y=alt.Y(f"{stage_config['second_metric']}:Q"),  # Change this line
        text=alt.Text(f"{stage_config['percentage']}:Q", format='.0%'),
        opacity=alt.condition(
            f'isValid(datum.{stage_config["percentage"]})',
            alt.value(1),
            alt.value(0)
        )
    )

    # Time metric line (handles both hours and days)
    time_metric = 'avg_hours' if 'avg_hours' in stage_config else 'avg_days'
    time_title = 'Average Time Spent (Hours)' if 'avg_hours' in stage_config else 'Average Time Spent (Days)'
    
    line = alt.Chart(grouped_df).mark_line(
        point=alt.OverlayMarkDef(color=PURPLE),  # Set point color to purple
        color=PURPLE,
        strokeWidth=2
    ).encode(
        x=alt.X('date:T'),
        y=alt.Y(f"{stage_config[time_metric]}:Q",
                title=time_title),
        tooltip=[
            alt.Tooltip('date:T'),
            alt.Tooltip(f"{stage_config[time_metric]}:Q", 
                       format=',.1f', 
                       title=time_title)
        ]
    )

    # Create manual legend
    legend_data = pd.DataFrame({
        'label': [stage_config['first_label'], stage_config['second_label'], time_title],
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
    legend_line = alt.Chart(legend_data.iloc[2:]).mark_line(
        strokeWidth=3, point=True
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