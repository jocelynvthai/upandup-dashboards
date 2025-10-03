import streamlit as st
import pandas as pd
import altair as alt
from tabs.utils import LIGHT_GRAY, GRAY, TEAL, DARK_TEAL, PURPLE


def inquiries_grouped(filtered_inquiries_df):
    # Overall aggregation
    overall_df = filtered_inquiries_df.groupby('date').agg(
        num_homes_listed=('rental_site_name', lambda x: x.isna().sum()),
        num_inquiries=('num_inquiries', 'sum'),
        num_filled_out_prequalification_form=('num_filled_out_prequalification_form', 'sum'),
        num_prequalified=('num_prequalified', 'sum'),
    )
    # Zillow aggregation
    zillow_df = filtered_inquiries_df[filtered_inquiries_df['rental_site_name'] == 'zillow'].groupby('date').agg(
        zillow_num_inquiries=('num_inquiries', 'sum'),
        zillow_num_filled_out_prequalification_form=('num_filled_out_prequalification_form', 'sum'),
        zillow_num_prequalified=('num_prequalified', 'sum'),
    )
    # Rently aggregation
    rently_df = filtered_inquiries_df[filtered_inquiries_df['rental_site_name'] == 'rently'].groupby('date').agg(
        rently_num_inquiries=('num_inquiries', 'sum'),
        rently_num_filled_out_prequalification_form=('num_filled_out_prequalification_form', 'sum'),
        rently_num_prequalified=('num_prequalified', 'sum'),
    )
    # Combine all dataframes
    grouped_inquiries_df = pd.concat([overall_df, zillow_df, rently_df], axis=1).reset_index()
    grouped_inquiries_df['num_inquiries_per_home'] = grouped_inquiries_df['num_inquiries'] / grouped_inquiries_df['num_homes_listed']
    grouped_inquiries_df['perc_inquiries_filled_out_prequalification_form'] = grouped_inquiries_df['num_filled_out_prequalification_form'] / grouped_inquiries_df['num_inquiries']
    grouped_inquiries_df['perc_inquiries_prequalified'] = grouped_inquiries_df['num_prequalified'] / grouped_inquiries_df['num_inquiries']
    grouped_inquiries_df['zillow_num_inquiries_per_home'] = grouped_inquiries_df['zillow_num_inquiries'] / grouped_inquiries_df['num_homes_listed']
    grouped_inquiries_df['zillow_perc_inquiries_filled_out_prequalification_form'] = grouped_inquiries_df['zillow_num_filled_out_prequalification_form'] / grouped_inquiries_df['zillow_num_inquiries']
    grouped_inquiries_df['zillow_perc_inquiries_prequalified'] = grouped_inquiries_df['zillow_num_prequalified'] / grouped_inquiries_df['zillow_num_inquiries']
    grouped_inquiries_df['rently_num_inquiries_per_home'] = grouped_inquiries_df['rently_num_inquiries'] / grouped_inquiries_df['num_homes_listed']
    grouped_inquiries_df['rently_perc_inquiries_filled_out_prequalification_form'] = grouped_inquiries_df['rently_num_filled_out_prequalification_form'] / grouped_inquiries_df['rently_num_inquiries']
    grouped_inquiries_df['rently_perc_inquiries_prequalified'] = grouped_inquiries_df['rently_num_prequalified'] / grouped_inquiries_df['rently_num_inquiries']

    # Zero inquiries
    property_inquiries = filtered_inquiries_df.groupby(['date', 'address']).agg(
        total_inquiries_per_property=('num_inquiries', 'sum')
    ).reset_index()
    zero_inquiries = property_inquiries.groupby('date').agg(
        num_homes_with_zero_inquiries=('total_inquiries_per_property', lambda x: (x == 0).sum())
    )
    grouped_inquiries_df = grouped_inquiries_df.merge(zero_inquiries, left_on='date', right_index=True)
    grouped_inquiries_df['perc_homes_with_zero_inquiries'] = grouped_inquiries_df['num_homes_with_zero_inquiries'] / grouped_inquiries_df['num_homes_listed']
    return grouped_inquiries_df


def num_inquiries(grouped_inquiries_df, selected_time_granularity):
    st.subheader("# Inquiries per Home")

    # Metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("(Overall)", f"{grouped_inquiries_df['num_inquiries'].sum():,.0f}")
    with col2:
        st.metric(f"Avg per home per {selected_time_granularity}", f"{grouped_inquiries_df['num_inquiries_per_home'].mean().round(2):.2f}")
    with col3:
        st.metric("(Zillow)", f"{grouped_inquiries_df['zillow_num_inquiries'].sum():,.0f}")
    with col4:
        st.metric(f"Avg per home per {selected_time_granularity}", f"{grouped_inquiries_df['zillow_num_inquiries_per_home'].mean().round(2):.2f}")
    with col5:
        st.metric("(Rently)", f"{grouped_inquiries_df['rently_num_inquiries'].sum():,.0f}")
    with col6:
        st.metric(f"Avg per home per {selected_time_granularity}", f"{grouped_inquiries_df['rently_num_inquiries_per_home'].mean().round(2):.2f}")
    
    # Chart
    chart_data = pd.melt(
        grouped_inquiries_df,
        id_vars=['date'],
        value_vars=[
            'num_inquiries_per_home',
            'zillow_num_inquiries_per_home',
            'rently_num_inquiries_per_home'
        ],
        var_name='source',
        value_name='inquires_per_home'
    )
    source_labels = {
        'num_inquiries_per_home': 'Overall',
        'zillow_num_inquiries_per_home': 'Zillow',
        'rently_num_inquiries_per_home': 'Rently'
    }
    chart_data['source'] = chart_data['source'].map(source_labels)

    # Bar chart for inquiries per home
    bar_chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('yearmonthdate(date):O', title='Date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        xOffset=alt.X('source:N', sort=['Zillow', 'Rently', 'Overall']),
        y=alt.Y('inquires_per_home:Q', title='Inquiries per Home'),
        color=alt.Color('source:N', title='Source', scale=alt.Scale(
            domain=['Zillow', 'Rently', 'Overall'],
            range=[TEAL, PURPLE, GRAY]
        )),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('source:N', title='Source'),
            alt.Tooltip('inquires_per_home:Q', title='Inquiries/Home', format='.2f')
        ]
    )
    
    # Line chart for num_homes_listed (using same y-axis scale)
    line_chart = alt.Chart(grouped_inquiries_df).mark_line(
        point={'color': LIGHT_GRAY},
        color=LIGHT_GRAY
    ).encode(
        x=alt.X('yearmonthdate(date):O'),
        y=alt.Y('num_homes_listed:Q', title='Inquiries per Home'),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('num_homes_listed:Q', title='Homes Listed')
        ]
    )
    
    # Combine charts with shared y-axis and set properties
    combined_chart = (bar_chart + line_chart).properties(
        width=800, 
        height=400,
        padding={"bottom": 60} 
    )
    st.altair_chart(combined_chart, use_container_width=True)


def inquiries_filled_out_prequalification_form(grouped_inquiries_df):
    st.subheader("% of Inquiries Filled Out Prequalification Form")

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall", f'{grouped_inquiries_df["num_filled_out_prequalification_form"].sum() * 100  / grouped_inquiries_df["num_inquiries"].sum():.2f}%')
    with col2:
        st.metric("Zillow", f'{grouped_inquiries_df["zillow_num_filled_out_prequalification_form"].sum() * 100  / grouped_inquiries_df["zillow_num_inquiries"].sum():.2f}%')
    with col3:
        st.metric("Rently", f'{grouped_inquiries_df["rently_num_filled_out_prequalification_form"].sum() * 100  / grouped_inquiries_df["rently_num_inquiries"].sum():.2f}%')

    # Chart
    chart_data = pd.melt(
        grouped_inquiries_df,
        id_vars=['date'],
        value_vars=[
            'perc_inquiries_filled_out_prequalification_form',
            'zillow_perc_inquiries_filled_out_prequalification_form',
            'rently_perc_inquiries_filled_out_prequalification_form'
        ],
        var_name='source',
        value_name='percentage'
    )
    source_labels = {
        'perc_inquiries_filled_out_prequalification_form': 'Overall',
        'zillow_perc_inquiries_filled_out_prequalification_form': 'Zillow',
        'rently_perc_inquiries_filled_out_prequalification_form': 'Rently'
    }
    chart_data['source'] = chart_data['source'].map(source_labels)
    
    # Line chart for inquiries filled out prequalification form
    line_chart = alt.Chart(chart_data).mark_line(point=True).encode(
        x=alt.X('yearmonthdate(date):O', title='Date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y('percentage:Q', title='% Inquiries Filled Out Prequalification Form', axis=alt.Axis(format='.0%')),
        color=alt.Color('source:N', title='Source', scale=alt.Scale(
            domain=['Zillow', 'Rently', 'Overall'],
            range=[TEAL, PURPLE, GRAY]
        )),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('source:N', title='Source'),
            alt.Tooltip('percentage:Q', title='% Filled Out Form', format='.2%')
        ]
    ).properties(
        width=800,
        height=400
    )
    st.altair_chart(line_chart, use_container_width=True)


def inquiries_prequalified(grouped_inquiries_df):
    st.subheader("% of Inquiries Prequalified")

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall", f'{grouped_inquiries_df["num_prequalified"].sum() * 100  / grouped_inquiries_df["num_inquiries"].sum():.2f}%')
    with col2:
        st.metric("Zillow", f'{grouped_inquiries_df["zillow_num_prequalified"].sum() * 100  / grouped_inquiries_df["zillow_num_inquiries"].sum():.2f}%')
    with col3:
        st.metric("Rently", f'{grouped_inquiries_df["rently_num_prequalified"].sum() * 100  / grouped_inquiries_df["rently_num_inquiries"].sum():.2f}%')

    # Chart
    chart_data = pd.melt(
        grouped_inquiries_df,
        id_vars=['date'],
        value_vars=[
            'perc_inquiries_prequalified',
            'zillow_perc_inquiries_prequalified',
            'rently_perc_inquiries_prequalified'
        ],
        var_name='source',
        value_name='percentage'
    )
    source_labels = {
        'perc_inquiries_prequalified': 'Overall',
        'zillow_perc_inquiries_prequalified': 'Zillow',
        'rently_perc_inquiries_prequalified': 'Rently'
    }
    chart_data['source'] = chart_data['source'].map(source_labels)

    # Line chart for inquiries filled out prequalification form
    line_chart = alt.Chart(chart_data).mark_line(point=True).encode(
        x=alt.X('yearmonthdate(date):O', title='Date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y('percentage:Q', title='% Inquiries Prequalified', axis=alt.Axis(format='.0%')),
        color=alt.Color('source:N', title='Source', scale=alt.Scale(
            domain=['Zillow', 'Rently', 'Overall'],
            range=[TEAL, PURPLE, GRAY]
        )),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('source:N', title='Source'),
            alt.Tooltip('percentage:Q', title='% Prequalified', format='.2%')
        ]
    ).properties(
        width=800,
        height=400
    )
    st.altair_chart(line_chart, use_container_width=True)


def homes_with_zero_inquiries(grouped_inquiries_df):
    st.subheader("% of Homes with Zero Inquiries")

    # Metrics
    st.metric("% of Homes with Zero Inquiries", f"{grouped_inquiries_df['perc_homes_with_zero_inquiries'].mean() * 100:.2f}%")

    # First bar chart - Number of homes listed
    first_bars = alt.Chart(grouped_inquiries_df).mark_bar(color=LIGHT_GRAY).encode(
        x=alt.X('yearmonthdate(date):O', title='Date', axis=alt.Axis(format='%Y-%m-%d', labelAngle=-90)),
        y=alt.Y('num_homes_listed:Q', 
                title='Count',
                axis=alt.Axis(titleColor=GRAY)),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('num_homes_listed:Q', 
                        title='Homes Listed', 
                        format=',.0f'),
            alt.Tooltip('perc_homes_with_zero_inquiries:Q', 
                        format='.1%', 
                        title='% with Zero Inquiries')
        ]
    )

    # Second bar chart - Number of homes with zero inquiries
    second_bars = alt.Chart(grouped_inquiries_df).mark_bar(color=TEAL).encode(
        x=alt.X('yearmonthdate(date):O'),
        y=alt.Y('num_homes_with_zero_inquiries:Q'),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('num_homes_with_zero_inquiries:Q', 
                        title='Homes with Zero Inquiries', 
                        format=',.0f'),
            alt.Tooltip('perc_homes_with_zero_inquiries:Q', 
                        format='.1%', 
                        title='% with Zero Inquiries')
        ]
    )

    # Conversion rate labels (second bar / first bar)
    text = alt.Chart(grouped_inquiries_df).mark_text(
        align='center',
        baseline='bottom',
        dy=-2, 
        color=DARK_TEAL
    ).encode(
        x=alt.X('yearmonthdate(date):O'),
        y=alt.Y('num_homes_with_zero_inquiries:Q'),
        text=alt.Text('perc_homes_with_zero_inquiries:Q', format='.0%'),
        opacity=alt.condition(
            'isValid(datum.perc_homes_with_zero_inquiries)',
            alt.value(1),
            alt.value(0)
        )
    )

    combined_chart = (first_bars + second_bars + text).properties(
        width=800,
        height=400
    )
    st.altair_chart(combined_chart, use_container_width=True)


    