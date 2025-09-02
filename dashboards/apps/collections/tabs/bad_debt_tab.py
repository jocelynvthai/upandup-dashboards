import streamlit as st
import altair as alt
import numpy as np
import pandas as pd
from datetime import datetime

from tabs.utils import fund_filter

def bad_debt_over_time_filters(bad_debt_inputs):
    selected_fund = fund_filter(key='bad_debt_over_time_select_fund', data=bad_debt_inputs)
    filtered_bad_debt_inputs = bad_debt_inputs[bad_debt_inputs['fund'] == selected_fund]
    filtered_bad_debt_inputs['bad_debt'] = (filtered_bad_debt_inputs['unpaid_rent_this_month'] - 
                                            filtered_bad_debt_inputs['unpaid_rent_covered_by_wallet'] - 
                                            filtered_bad_debt_inputs['bom_bad_debt_recovered_by_late_collections'])
    return filtered_bad_debt_inputs, selected_fund


def bad_debt_over_time(filtered_bad_debt_inputs):
    st.subheader("Bad Debt Over Time")
    bad_debt = filtered_bad_debt_inputs.copy()

    bad_debt_fund = (
        bad_debt.groupby(['fund', 'month'])
        .agg({'bad_debt': 'sum', 'rent_charged': 'sum', 'unpaid_rent_this_month': 'sum', 'unpaid_rent_covered_by_wallet': 'sum', 'bom_bad_debt_recovered_by_late_collections': 'sum'})
        .reset_index()
    )
    bad_debt_fund['bad_debt_ratio_percent'] = bad_debt_fund['bad_debt'] * 100 / bad_debt_fund['rent_charged']

    # Set 'month' to the 15th of each month for centering
    bad_debt_fund['month'] = (
        pd.to_datetime(bad_debt_fund['month'])
        .dt.to_period('M')
        .dt.to_timestamp()
        + pd.Timedelta(days=7)
    )

    # Create a list of months for the domain (15th of each month)
    all_months = pd.date_range(
        start=(bad_debt_fund['month'].min() - pd.DateOffset(days=15)),
        end=bad_debt_fund['month'].max(),
        freq='MS'
    )
    
    bad_debt_fund['month_str'] = bad_debt_fund['month'].dt.strftime('%Y-%m')
    latest_month = bad_debt_fund['month_str'].max()
    chart = alt.Chart(bad_debt_fund).mark_bar(size=40, color='#15b8a6').encode(
        x=alt.X(
            'month:T',
            title='Month',
            axis=alt.Axis(
                format='%b %Y',
                tickCount='month',
                labelAlign='left'
            ),
            scale=alt.Scale(domain=list(all_months))
        ),
        y=alt.Y('bad_debt_ratio_percent:Q', title='Bad Debt Ratio (%)'),
        color=alt.condition(
            alt.datum.month_str == latest_month,
            alt.value('#15b8a6'), 
            alt.value('#0E8074')  
        ),
        tooltip=[
            alt.Tooltip('month:T', title='Month', format='%b %Y'),
            alt.Tooltip('bad_debt:Q', title='Bad Debt', format=','),
            alt.Tooltip('rent_charged:Q', title='Rent Charged', format=','),
            alt.Tooltip('bad_debt_ratio_percent:Q', title='Bad Debt Ratio (%)', format='.2f'),
        ]
    ).properties(
        width=600
    )
    labels = chart.mark_text(
        align='center',
        baseline='bottom',
        dy=-5
    ).encode(
        text=alt.Text('bad_debt_ratio_percent:Q', format='.2f')
    )
    final_chart = (chart + labels)
    st.altair_chart(final_chart)


def bad_debt_month_to_date(filtered_bad_debt_inputs):
    this_month = filtered_bad_debt_inputs['month'].max().strftime('%B %Y')
    st.subheader(f"({this_month}) Non-Zero Bad Debt")

    this_month_bad_debt_inputs = filtered_bad_debt_inputs[(filtered_bad_debt_inputs['month'] == this_month) & (filtered_bad_debt_inputs['bad_debt'] != 0)]
    display_columns = ['address', 'state', 'move_out_date', 'was_evicted', 'in_evictions', 
                       'rental_status', 'unpaid_rent_this_month', 'unpaid_rent_covered_by_wallet', 
                       'bom_bad_debt_recovered_by_late_collections', 'bad_debt']


    st.dataframe(this_month_bad_debt_inputs[display_columns], hide_index=True,
                column_config={
                    'address': st.column_config.TextColumn(
                        pinned=True,
                    ),
                    'bad_debt': st.column_config.NumberColumn(
                        format="accounting"
                    )
                }
            )




def bad_debt_projection(filtered_bad_debt_inputs):
    st.subheader("Bad Debt Projection")
    
    bad_debt = filtered_bad_debt_inputs[filtered_bad_debt_inputs['month'] == datetime.now().strftime('%Y-%m-01')]
    bad_debt['ontime_rent_collections'] = bad_debt['ontime_rent_collections_succeeded'] + bad_debt['ontime_rent_collections_processing']
    bad_debt['late_rent_collections'] = bad_debt['late_rent_collections_succeeded'] + bad_debt['late_rent_collections_processing']

    today_ocr = bad_debt['ontime_rent_collections'].sum() / bad_debt['rent_charged'].sum()
    today_lcr = 0 if bad_debt['bom_rent_balance'].sum() == 0 else bad_debt['late_rent_collections'].sum() / bad_debt['bom_rent_balance'].sum()


    if today_ocr == 1 and bad_debt['bom_bad_debt_rent'].sum() == 0:
        st.write("100% collected this month and no BOM bad debt!")
    elif not np.isnan(today_ocr) and not np.isnan(today_lcr) and today_ocr != 1 and today_lcr != 1:
        col_new, col_ocr = st.columns([0.5, 1])
        with col_ocr:
            selected_ocr = st.slider("Expected Ontime Collections Rate (OCR) %", 
                                    min_value=today_ocr*100, 
                                    max_value=100.0, 
                                    value=max(96.0, today_ocr*100), 
                                    step=0.5, 
                                    help=f'Minimum value is set to current month\'s OCR: {today_ocr:.2%}')
            expected_ocr = selected_ocr/100

        # Old bad debt recovery with LCR slider
        col_old, col_lcr = st.columns([0.5, 1])
        with col_lcr:
            selected_lcr = st.slider(
                "Expected Late Collections Rate (LCR) %",
                min_value=today_lcr * 100,
                max_value=100.0,
                value=max(25.0, today_lcr*100),
                step=0.5,
                help=f'Minimum value is set to current month\'s LCR: {today_lcr:.2%}'
            )
            expected_lcr = selected_lcr/100


        # Calculate all projections
        total_expected_bad_debt_increase = 0
        unpaid_rentals = bad_debt[bad_debt['ontime_rent_collections'] < bad_debt['rent_charged']]
        for _, ur in unpaid_rentals.iterrows(): 
            amount_unpaid = ur['rent_charged'] - ur['ontime_rent_collections']
            expected_collections_pct = (expected_ocr - today_ocr) / (1 - today_ocr)
            expected_unpaid = amount_unpaid * (1 - expected_collections_pct)
            expected_bad_debt_increase = max(0, expected_unpaid - ur['bom_usable_wallet_or_deposit'])
            total_expected_bad_debt_increase += expected_bad_debt_increase

        total_expected_bad_debt_decrease = 0
        late_rentals = bad_debt[bad_debt['bom_rent_balance'] > 0]
        for _, lr in late_rentals.iterrows():	
            remaining_bom_balance = lr['bom_rent_balance'] - lr['late_rent_collections']
            expected_collections_pct = (expected_lcr - today_lcr) / (1 - today_lcr)
            expected_late_collections = remaining_bom_balance * expected_collections_pct
            expected_bad_debt_decrease = min(lr['bom_bad_debt_rent'], expected_late_collections)
            total_expected_bad_debt_decrease += expected_bad_debt_decrease + lr['bom_bad_debt_recovered_by_late_collections']

        fund_bad_debt_projection = total_expected_bad_debt_increase - total_expected_bad_debt_decrease

        # Calculate percentages of rent charged
        total_rent_charged = bad_debt['rent_charged'].sum()
        new_bad_debt_pct = (total_expected_bad_debt_increase / total_rent_charged) * 100
        recovery_pct = (total_expected_bad_debt_decrease / total_rent_charged) * 100
        net_projection_pct = (fund_bad_debt_projection / total_rent_charged) * 100


        # 1. New bad debt metric
        with col_new:
            st.metric(
                label="Projected New Bad Debt",
                value=f"{new_bad_debt_pct:.2f}%",
                help="""Represents potential new bad debt as a percentage of rent charged.  \n
    Calculated after considering:
    - Current month's collection progress
    - Expected additional on-time collections based on OCR target
    - Available wallet/deposit amounts that can offset unpaid rent"""
            )

        # 2. Old bad debt recovery metric
        with col_old:
            st.metric(
                label="Projected Old Bad Debt Recovery",
                value=f"{recovery_pct if round(recovery_pct, 2) != 0 else abs(recovery_pct):.2f}%",
                help="""Amount of existing bad debt we expect to recover as a percentage of rent charged. \n
    Based on:
    - Current late collection progress
    - Expected additional late collections based on LCR target
    - Bad debt balance from beginning of month"""
            )

        col_net, col_disclaimer = st.columns([0.5, 1])
        with col_net:
            st.metric(
                label=f"Net Bad Debt Projection ({datetime.now().strftime('%B %Y')})",
                value=f"{net_projection_pct:.2f}%",
                help="""The overall expected bad debt position as a percentage of rent charged. \n
    - A negative percentage indicates net recovery (good) 
    - A positive percentage indicates net increase in bad debt (bad)"""
        )
        with col_disclaimer:
            st.markdown("<div style='text-align: right;'><em>*Dragging both sliders to the left will set the projection to the current month's bad debt.</em></div>", unsafe_allow_html=True)
    else:
        st.write("No data for this month!")





