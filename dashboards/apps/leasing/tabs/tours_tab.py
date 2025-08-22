import streamlit as st
import altair as alt
from tabs.utils import LIGHT_GRAY, GRAY, LIGHT_TEAL, TEAL, LIGHT_PURPLE, PURPLE, DARK_PURPLE


def tours_grouped(filtered_tours_df):
    # Overall aggregation
    grouped_tours_df = filtered_tours_df.groupby('date').agg(
        num_homes_listed=('tour_type', lambda x: x.isna().sum()),
        num_tours=('num_tours', 'sum'),
        num_tours_safe_mode=('num_tours', lambda x, df=filtered_tours_df: x[df['tour_type'] == 'safe_mode'].sum()),
        num_tours_doorman=('num_tours', lambda x, df=filtered_tours_df: x[df['tour_type'] != 'safe_mode'].sum()),
        num_id_verified=('num_identity_verified', 'sum'),
        num_prequalified=('num_prequalified', 'sum'),
        num_created_application=('num_applicants', 'sum'),
        num_paid_application_fee=('num_paid_applicants', 'sum'),
        num_deals=('num_completed_applicants', 'sum'),
    ).reset_index()
    grouped_tours_df['avg_num_tours_per_home'] = grouped_tours_df['num_tours'] / grouped_tours_df['num_homes_listed']

    property_tours = filtered_tours_df.groupby(['date', 'address']).agg(
        total_tours_per_property=('num_tours', 'sum'), 
    ).reset_index()
    median_tours = property_tours.groupby('date').agg(
        median_tours_per_home=('total_tours_per_property', 'median')
    )
    zero_tours = property_tours.groupby('date').agg(
        num_homes_with_zero_tours=('total_tours_per_property', lambda x: (x == 0).sum())
    )

    grouped_tours_df = grouped_tours_df.merge(median_tours, left_on='date', right_index=True).merge(zero_tours, left_on='date', right_index=True)
    grouped_tours_df['perc_homes_with_zero_tours'] = grouped_tours_df['num_homes_with_zero_tours'] / grouped_tours_df['num_homes_listed']
    return grouped_tours_df


def tour_metrics(grouped_tours_df):
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("&#35; Tours", f"{grouped_tours_df['num_tours'].sum()}")
    with col2:
        st.metric("&#35; Tours (Doorman)", f"{grouped_tours_df['num_tours_doorman'].sum()}")
    with col3:
        st.metric("&#35; Tours (Safe Mode)", f"{grouped_tours_df['num_tours_safe_mode'].sum()}")
    with col4:
        st.metric('Avg per home per week', f"{grouped_tours_df['num_tours'].sum() / grouped_tours_df['num_homes_listed'].sum():.2f}")
    with col5: 
        st.metric('Median per home', f"{ grouped_tours_df['median_tours_per_home'].median():.2f}")

    funnel_col1, funnel_col2, funnel_col3, funnel_col4, funnel_col5 = st.columns(5)
    with funnel_col1:
        st.metric("# ID Verified", f"{grouped_tours_df['num_id_verified'].sum()}")
        st.markdown(f"<small style='margin-top: -25px; display: block;'>{grouped_tours_df['num_id_verified'].sum() / grouped_tours_df['num_tours'].sum() * 100:.2f}% of tours</small>", unsafe_allow_html=True)
    with funnel_col2:
        st.metric("# Prequalified", f"{grouped_tours_df['num_prequalified'].sum()}")
        st.markdown(f"<small style='margin-top: -25px; display: block;'>{grouped_tours_df['num_prequalified'].sum() / grouped_tours_df['num_tours'].sum() * 100:.2f}% of tours</small>", unsafe_allow_html=True)
    with funnel_col3:
        st.metric("# Created Application", f"{grouped_tours_df['num_created_application'].sum()}")
        st.markdown(f"<small style='margin-top: -25px; display: block;'>{grouped_tours_df['num_created_application'].sum() / grouped_tours_df['num_tours'].sum() * 100:.2f}% of tours</small>", unsafe_allow_html=True)
    with funnel_col4:
        st.metric("# Paid Application Fee", f"{grouped_tours_df['num_paid_application_fee'].sum()}")
        st.markdown(f"<small style='margin-top: -25px; display: block;'>{grouped_tours_df['num_paid_application_fee'].sum() / grouped_tours_df['num_tours'].sum() * 100:.2f}% of tours</small>", unsafe_allow_html=True)
    with funnel_col5:
        st.metric("# Deals", f"{grouped_tours_df['num_deals'].sum()}")
        st.markdown(f"<small style='margin-top: -25px; display: block;'>{grouped_tours_df['num_deals'].sum() / grouped_tours_df['num_tours'].sum() * 100:.2f}% of tours</small>", unsafe_allow_html=True)
    



def num_tours_by_source(grouped_tours_df):
    st.subheader('# Tours by Source')

    # Prepare data for stacked bar chart
    chart_data = grouped_tours_df.reset_index()[['date', 'num_tours_safe_mode', 'num_tours_doorman']].melt(
        id_vars=['date'], 
        value_vars=['num_tours_safe_mode', 'num_tours_doorman'],
        var_name='tour_type', 
        value_name='count'
    )
    chart_data['tour_type_display'] = chart_data['tour_type'].map({
        'num_tours_safe_mode': 'Safe Mode',
        'num_tours_doorman': 'Doorman'
    })
    line_data = grouped_tours_df.reset_index()[['date', 'avg_num_tours_per_home']]
    bars = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('yearmonthdate(date):O', title='Tour Creation Date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y('count:Q', title='Number of Tours'),
        color=alt.Color(
            'tour_type_display:N',
            title='Tour Type',
            scale=alt.Scale(
                domain=['Safe Mode', 'Doorman'],
                range=[TEAL, PURPLE]
            ),
            legend=alt.Legend(
                labelExpr="datum.value" 
            )
        ),
        tooltip=[
            'date:T', 
            alt.Tooltip('tour_type_display:N', title='Tour Type'),
            alt.Tooltip('count:Q', title='# Tours')
        ]
    )
    
    # Create line chart for avg tours per home
    line = alt.Chart(line_data).mark_line(
        point=alt.OverlayMarkDef(color=LIGHT_GRAY),
        color=LIGHT_GRAY,
        strokeWidth=3
    ).encode(
        x=alt.X('yearmonthdate(date):O'),
        y=alt.Y('avg_num_tours_per_home:Q', title='Avg # Tours per Home'),
        tooltip=['date:T', alt.Tooltip('avg_num_tours_per_home:Q', title='Avg # Tours per Home', format='.2f')]
    )
    
    # Combine charts with dual y-axes
    combined_chart = (bars + line).resolve_scale(
        y='independent',
        color='independent'
    ).properties(
        width=600,
        height=400
    )
    st.altair_chart(combined_chart, use_container_width=True)



def num_tours_by_farthest_funnel_stage(grouped_tours_df):
    st.subheader('# Tours by Farthest Funnel Stage')
    
    # Prepare data for grouped bar chart
    chart_data = grouped_tours_df.reset_index()[['date', 'num_tours', 'num_id_verified', 'num_prequalified', 'num_created_application', 'num_paid_application_fee']].melt(
        id_vars=['date'], 
        value_vars=['num_tours', 'num_id_verified', 'num_prequalified', 'num_created_application', 'num_paid_application_fee'],
        var_name='funnel_stage', 
        value_name='count'
    )

    # Add a new column for nice names
    display_name_mapping = {
        'num_tours': 'Total',
        'num_id_verified': 'ID Verified',
        'num_prequalified': 'Prequalified',
        'num_created_application': 'Created Application',
        'num_paid_application_fee': 'Paid Application Fee'
    }
    chart_data['funnel_stage_display'] = chart_data['funnel_stage'].map(display_name_mapping)

    # Create grouped bar chart
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('yearmonthdate(date):O', title='Tour Creation Date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        xOffset=alt.X('funnel_stage_display:O', sort=list(display_name_mapping.values())),
        y=alt.Y('count:Q', title='# Tours'),
        color=alt.Color(
            'funnel_stage_display:O',
            title='Farthest Funnel Stage',
            scale=alt.Scale(
                domain=list(display_name_mapping.values()),
                range=[GRAY, LIGHT_TEAL, TEAL, LIGHT_PURPLE, PURPLE]
            ),
            legend=alt.Legend()
        ),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('funnel_stage_display:O', title='Farthest Funnel Stage'), 
            alt.Tooltip('count:Q', title='# Tours')
        ]
    ).properties(
        width=800,
        height=400
    )
    st.altair_chart(chart, use_container_width=True)


def homes_with_zero_tours(grouped_tours_df):
    st.subheader("% of Homes with Zero Tours")

    # Metrics
    st.metric("% of Homes with Zero Tours", f"{grouped_tours_df['perc_homes_with_zero_tours'].mean() * 100:.2f}%")

    # First bar chart - Number of homes listed
    first_bars = alt.Chart(grouped_tours_df).mark_bar(color=LIGHT_GRAY).encode(
        x=alt.X('yearmonthdate(date):O', title='Date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y('num_homes_listed:Q', 
                title='Count',
                axis=alt.Axis(titleColor=GRAY)),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('num_homes_listed:Q', 
                        title='Homes Listed', 
                        format=',.0f'),
            alt.Tooltip('perc_homes_with_zero_tours:Q', 
                        format='.1%', 
                        title='% with Zero Tours')
        ]
    )

    # Second bar chart - Number of homes with zero tours
    second_bars = alt.Chart(grouped_tours_df).mark_bar(color=TEAL).encode(
        x=alt.X('yearmonthdate(date):O'),
        y=alt.Y('num_homes_with_zero_tours:Q'),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('num_homes_with_zero_tours:Q', 
                        title='Homes with Zero Tours', 
                        format=',.0f'),
            alt.Tooltip('perc_homes_with_zero_tours:Q', 
                        format='.1%', 
                        title='% with Zero Tours')
        ]
    )

    # Conversion rate labels (second bar / first bar)
    text = alt.Chart(grouped_tours_df).mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    ).encode(
        x=alt.X('yearmonthdate(date):O'),
        y=alt.Y('num_homes_with_zero_tours:Q'),
        text=alt.Text('perc_homes_with_zero_tours:Q', format='.0%'),
        opacity=alt.condition(
            'isValid(datum.perc_homes_with_zero_tours)',
            alt.value(1),
            alt.value(0)
        )
    )

    combined_chart = (first_bars + second_bars + text).properties(
        width=800,
        height=400
    )
    st.altair_chart(combined_chart, use_container_width=True)


    

    

