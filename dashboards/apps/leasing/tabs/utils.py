import altair as alt
import streamlit as st

def create_funnel_chart(grouped_df, funnel_stages, chart_type="application"):
    """
    Create a funnel chart showing conversion rates and timing between stages.
    Args:
        grouped_df: DataFrame containing the funnel metrics
        funnel_stages: Dictionary defining the funnel stage configurations
        chart_type: String identifier for the chart (used for unique streamlit keys)
    """

    FIRST_BAR_COLOR = "#808080"  # gray
    SECOND_BAR_COLOR = "#15b8a6"  # teal
    LINE_COLOR = "#9575cd"  # purple
    
    # Add stage selector
    selected_stage = st.selectbox("Select Funnel Stage", 
                                  options=list(funnel_stages.keys()), 
                                  key=f'{chart_type}_funnel_stage')
    stage_config = funnel_stages[selected_stage]
    
    # First bar chart
    first_bars = alt.Chart(grouped_df).mark_bar().encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y(f"{stage_config['first_metric']}:Q", 
                title='Count',
                axis=alt.Axis(titleColor=FIRST_BAR_COLOR)),
        color=alt.value(FIRST_BAR_COLOR),
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
    second_bars = alt.Chart(grouped_df).mark_bar().encode(
        x=alt.X('date:T'),
        y=alt.Y(f"{stage_config['second_metric']}:Q"),
        color=alt.value(SECOND_BAR_COLOR),
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
        y=alt.Y(f"{stage_config['first_metric']}:Q"),
        text=alt.Text(f"{stage_config['percentage']}:Q", format='.0%'),
        opacity=alt.condition(
            f'isValid(datum.{stage_config["percentage"]})',
            alt.value(1),
            alt.value(0)
        )
    )

    # Time metric line (handles both hours and days)
    time_metric = 'avg_hours' if 'avg_hours' in stage_config else 'avg_days'
    time_title = 'Average Hours' if 'avg_hours' in stage_config else 'Average Days'
    
    line = alt.Chart(grouped_df).mark_line(
        color=LINE_COLOR,
        strokeWidth=2
    ).encode(
        x=alt.X('date:T'),
        y=alt.Y(f"{stage_config[time_metric]}:Q",
                title=time_title,
                axis=alt.Axis(titleColor=LINE_COLOR)),
        tooltip=[
            alt.Tooltip('date:T'),
            alt.Tooltip(f"{stage_config[time_metric]}:Q", 
                       format=',.1f', 
                       title=time_title)
        ]
    )

    # Layer and plot the charts
    bars_layer = alt.layer(first_bars, second_bars, text).properties(
        width=800,
        height=400,
        title=selected_stage
    )
    chart = alt.layer(bars_layer, line).resolve_scale(y='independent')
    st.altair_chart(chart, use_container_width=True) 