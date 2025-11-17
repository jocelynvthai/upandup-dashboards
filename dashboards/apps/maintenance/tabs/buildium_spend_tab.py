import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

from data import all_management_expenses_data, owned_homes_data, budget_by_month_data, imputed_daily_budget_data
from tabs.utils import (
    all_management_expenses_data_clean,
    owned_homes_data_clean,
    budget_by_month_data_clean,
    imputed_daily_budget_data_clean,
    seasonality_chart,
    projected_current_month_df,
    TEAL,
    PURPLE,
    PINK, 
    CURRENT_YEAR, 
    MONTH_ORDER,
    CURRENT_MONTH_PROJECTED
)


def buildium_spend_filters(credentials):
    # filters
    col_date_range, col_category_group = st.columns(2)
    with col_date_range:
        date_range = st.date_input("Pick a period range", 
                                value=(datetime(2023, 1, 1),  datetime.now()), 
                                format='MM/DD/YYYY',
                                help="The period range to filter the data type selected",
                                key='buildium_spend_date_range')
        if len(date_range) != 2:
            st.stop()
        else:
            filtered_all_management_expenses_df = all_management_expenses_data_clean(all_management_expenses_data(credentials, date_range[0], date_range[1]))
            filtered_owned_homes_df = owned_homes_data_clean(owned_homes_data(credentials, date_range[0]))
            filtered_budget_by_month_df = budget_by_month_data_clean(budget_by_month_data(credentials, date_range[0]))
            filtered_imputed_daily_budget_df = imputed_daily_budget_data_clean(imputed_daily_budget_data(credentials, date_range[0]))
    with col_category_group:
        category_group = st.multiselect("Select a category group", ['All'] + sorted(list(filtered_all_management_expenses_df['category_group'].unique())), default='run_rate', key='buildium_spend_category_group')
        if 'All' not in category_group:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['category_group'].isin(category_group)]
            if (len(category_group) == 1) and (category_group[0] in ['run_rate', 'common_area_maintenance', 'turn']):
                filtered_budget_by_month_df = filtered_budget_by_month_df[filtered_budget_by_month_df['management_category'] == category_group[0]]
                filtered_imputed_daily_budget_df = filtered_imputed_daily_budget_df[filtered_imputed_daily_budget_df['management_category'] == category_group[0]]

    col_gl_account, col_vendor = st.columns(2)
    with col_gl_account:
        selected_gl_accounts = st.multiselect("Select a GL account", ['All'] + sorted(list(filtered_all_management_expenses_df['gl_account'].unique())), default='All', key='buildium_spend_gl_account')
        if 'All' not in selected_gl_accounts:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['gl_account'].isin(selected_gl_accounts)]
    with col_vendor:
        selected_vendors = st.multiselect("Select a vendor", ['All'] + sorted(list(filtered_all_management_expenses_df['vendor'].unique())), default='All', key='buildium_spend_vendor', help="vendor format is 'Company Name (Contact Name)' or 'Contact Name'")
        if 'All' not in selected_vendors:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['vendor'].isin(selected_vendors)]

    col_fund, col_market = st.columns(2)
    with col_fund:
        selected_funds = st.multiselect("Select a fund", ['All'] + sorted(list(filtered_all_management_expenses_df['fund'].unique())), default='All', key='buildium_spend_fund')
        if 'All' not in selected_funds:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['fund'].isin(selected_funds)]
            filtered_owned_homes_df = filtered_owned_homes_df[filtered_owned_homes_df['fund'].isin(selected_funds)]
            filtered_budget_by_month_df = filtered_budget_by_month_df[filtered_budget_by_month_df['fund'].isin(selected_funds)]
            filtered_imputed_daily_budget_df = filtered_imputed_daily_budget_df[filtered_imputed_daily_budget_df['fund'].isin(selected_funds)]
    with col_market:
        market_options = list(filtered_all_management_expenses_df['market'].unique())
        market_sorted = sorted(market_options, key=lambda x: (pd.isna(x), str(x).lower()))
        selected_markets = st.multiselect("Select a market", ['All'] + sorted(market_options, key=lambda x: (pd.isna(x), str(x).lower())), default='All', key='buildium_spend_market')
        if 'All' not in selected_markets:
            filtered_all_management_expenses_df = filtered_all_management_expenses_df[filtered_all_management_expenses_df['market'].isin(selected_markets)]
            filtered_owned_homes_df = filtered_owned_homes_df[filtered_owned_homes_df['market'].isin(selected_markets)]

    return filtered_all_management_expenses_df, filtered_owned_homes_df, filtered_budget_by_month_df, filtered_imputed_daily_budget_df


def buildium_spend_bar_chart(all_management_expenses_df, owned_homes_df, imputed_daily_budget_df):
    st.subheader("Buildium Spend per Home (by maintenance category, last 4 weeks)")

    # last 4 weeks data only (MAKE CUSTOMIZABLE LATER)
    start_date = datetime.now() - timedelta(weeks=4)

    # expenses
    grouped_expenses_df = all_management_expenses_df[
        all_management_expenses_df['date'] >= start_date
    ].groupby(['week_end', 'maintenance_category'], as_index=False).agg(total_spend=('amount', 'sum')).reset_index()
    grouped_expenses_df['maintenance_category'] = grouped_expenses_df['maintenance_category'].apply(lambda x: x.replace('_', ' ').title())

    # owned homes
    grouped_homes_df = owned_homes_df[
        (owned_homes_df['time_granularity'] == 'week')
        & (owned_homes_df['date_time'] >= start_date)
        & (owned_homes_df['date_time'] <= datetime.now())
    ].groupby('date').agg(total_homes_owned=('homes_owned', 'sum')).reset_index()

    # budget
    imputed_daily_budget_df['week'] = imputed_daily_budget_df['date_time'].apply(
        lambda x: x + timedelta(days=(6 - x.weekday()))
    )
    grouped_budget_df = imputed_daily_budget_df[
        (imputed_daily_budget_df['week'] >= start_date)
        & (imputed_daily_budget_df['week'] <= datetime.now())
    ].groupby(['week'], as_index=False).agg(budgeted_spend=('amount', 'sum')).reset_index()
    grouped_budget_df['week_end'] = grouped_budget_df['week'].dt.strftime('%Y-%m-%d')

    # merge all data
    grouped_expenses_df = grouped_homes_df.merge(grouped_expenses_df, left_on='date', right_on='week_end', how='left')
    grouped_expenses_df['type'] = 'Actual'
    grouped_budget_df = grouped_budget_df.merge(grouped_expenses_df, on='week_end', how='left')
    formatted_budget_df = grouped_budget_df.groupby(['week_end', 'total_homes_owned'], as_index=False).agg(total_spend=('budgeted_spend', 'max')).reset_index()
    formatted_budget_df['date'] = formatted_budget_df['week_end']
    formatted_budget_df['maintenance_category'] = 'Budget'
    formatted_budget_df['type'] = 'Budget'
    grouped_expenses_df = pd.concat([grouped_expenses_df, formatted_budget_df])

    # format data
    grouped_expenses_df['total_spend_per_home'] = round(grouped_expenses_df['total_spend'].fillna(0) / grouped_expenses_df['total_homes_owned'].fillna(0), 2)
    filler_category = grouped_expenses_df['maintenance_category'].dropna().unique()[0]
    grouped_expenses_df['maintenance_category'] = grouped_expenses_df['maintenance_category'].fillna(filler_category)

    # create bar chart
    chart = alt.Chart(grouped_expenses_df).mark_bar().encode(
        x=alt.X('date', title='Week', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('total_spend_per_home', title='Total Spend per Home', axis=alt.Axis(format='$,.2f')),
        color=alt.Color('maintenance_category', title='Maintenance Category'),
        xOffset=alt.XOffset('type')
    )
    st.altair_chart(chart, use_container_width=True)


def buildium_spend_over_time(all_management_expenses_df, owned_homes_df):
    st.subheader("Buildium Spend Over Time")

    # customize view specifications
    col_time_granularity, col_dimension, col_spend_per_home = st.columns([1, 1, 0.25])
    with col_time_granularity:
        selected_time_granularity = st.selectbox("Select a time granularity", ['week', 'month'], key='buildium_spend_time_granularity')
        st.session_state["time_granularity"] = f'{selected_time_granularity}_end'
        configured_owned_homes_df = owned_homes_df[owned_homes_df['time_granularity'] == selected_time_granularity]
    with col_dimension:
        category_dict = {
            'GL Account': 'gl_account',
            'Vendor': 'vendor',
            'Fund': 'fund',
            'Market': 'market'
        }
        selected_dimension = st.selectbox("Select a dimension", category_dict.keys())
        st.session_state["category"] = category_dict[selected_dimension]
    with col_spend_per_home:
        st.markdown(
            """
            <style>
                .right-align-toggle {
                    display: flex;
                    margin-top: 2rem;
                }
            </style>
            <div class="right-align-toggle">
            """,
            unsafe_allow_html=True
        )
        spend_per_home = st.toggle("$/Home", value=False, key='buildium_spend_over_time_per_home')

    # group, pivot & format data
    grouped_management_expenses_df = (
        all_management_expenses_df
        .groupby([st.session_state["time_granularity"], st.session_state["category"]], dropna=False)
        .agg(total_spend=('amount', 'sum'))
        .reset_index()
    )
    # add spend per home
    if spend_per_home:
        if st.session_state["category"] in configured_owned_homes_df.columns:
            # fund or market dimension
            groupby_cols = ['date', st.session_state["category"]]
            merge_left_on = [st.session_state["time_granularity"], st.session_state["category"]]
            merge_right_on = ['date', st.session_state["category"]]
        else:
            # gl account or vendor dimension
            groupby_cols = ['date']
            merge_left_on = [st.session_state["time_granularity"]]
            merge_right_on = ['date']

        grouped_owned_homes_df = configured_owned_homes_df.groupby(groupby_cols).agg(total_homes_owned=('homes_owned', 'sum')).reset_index()
        grouped_management_expenses_df = grouped_management_expenses_df.merge(grouped_owned_homes_df, 
                                            left_on=merge_left_on, 
                                            right_on=merge_right_on, 
                                            how='left')
        grouped_management_expenses_df['total_spend_per_home'] = grouped_management_expenses_df['total_spend'] / grouped_management_expenses_df['total_homes_owned']

    pivot_df = grouped_management_expenses_df.pivot(
        index=st.session_state["category"],
        columns=st.session_state["time_granularity"],
        values='total_spend_per_home' if spend_per_home else 'total_spend'
    ).fillna(0).reset_index()
    
    value_columns = [col for col in pivot_df.columns if col != st.session_state["category"]]
    styled_pivot_df = pivot_df.style.map(
        lambda v: "color: rgba(0, 0, 0, 0.25)" if v == 0 else "",
        subset=value_columns,
    )
    event = st.dataframe(
        styled_pivot_df,
        on_select="rerun",
        selection_mode=["single-cell"],
        hide_index=True,
        column_config={
            **{
                col: st.column_config.NumberColumn(format="dollar")
                for col in pivot_df.columns
                if col != st.session_state["category"]
            },
            st.session_state["category"]: st.column_config.TextColumn(pinned=True),
        },
    )
    st.caption("<p style='text-align: right;'><i>Select a cell to view the line items</i></p>", unsafe_allow_html=True)

    selected_info = event['selection']
    if len(selected_info['cells']):
        st.session_state["category_filter"] = pivot_df.loc[selected_info['cells'][0][0], st.session_state["category"]]
        st.session_state["time_granularity_filter"] = selected_info['cells'][0][1]
    else:
        st.session_state["category_filter"] = None
        st.session_state["time_granularity_filter"] = None
        

def buildium_spend_seasonality(all_management_expenses_df, owned_homes_df, budget_by_month_df):
    st.subheader("Buildium Spend Seasonality")
    
    # group by year and month
    seasonality_df = (
        all_management_expenses_df
        .groupby(['year', 'month'], as_index=False)
        .agg(total_spend=('amount', 'sum'))
    )
    seasonality_df['month'] = pd.Categorical(seasonality_df['month'], categories=MONTH_ORDER, ordered=True)
    seasonality_df = seasonality_df.sort_values(['year', 'month'])
    
    # add projected current month data
    seasonality_df = pd.concat([
        seasonality_df,
        projected_current_month_df(all_management_expenses_df)
    ], ignore_index=True)

    # add budget data
    grouped_budget_by_month_df = budget_by_month_df.groupby(['year', 'month'], as_index=False).agg(total_spend=('amount', 'sum'))
    grouped_budget_by_month_df.loc[grouped_budget_by_month_df['year'] == CURRENT_YEAR, 'year'] = 'Budget'
    seasonality_df = pd.concat([seasonality_df, grouped_budget_by_month_df])

    # add spend per home
    _, col_spend_per_home = st.columns([2, 0.25])
    with col_spend_per_home:
        spend_per_home = st.toggle("$/Home", value=False, key='buildium_spend_seasonality_per_home')
    if spend_per_home:
        month_owned_homes_df = owned_homes_df[owned_homes_df['time_granularity'] == 'month']
        grouped_month_owned_homes_df = month_owned_homes_df.groupby(['year', 'month'], as_index=False).agg(total_homes_owned=('homes_owned', 'sum'))
        seasonality_df = seasonality_df.merge(grouped_month_owned_homes_df, on=['year', 'month'], how='left')

        # impute value of total_homes_owned for Budget and CURRENT_MONTH_PROJECTED rows
        budget_and_projected_rows = seasonality_df[
            (seasonality_df['year'] == 'Budget')
            | (seasonality_df['year'] == CURRENT_MONTH_PROJECTED)
        ]
        for index, row in budget_and_projected_rows.iterrows():
            homes_owned_this_month = seasonality_df.loc[(
                (seasonality_df['year'] == CURRENT_YEAR)
                & (seasonality_df['month'] == row['month'])
            ), 'total_homes_owned']
            # try to pull the actual total_homes_owned for the corresponding month
            if len(homes_owned_this_month) > 0:
                homes_owned_this_month = homes_owned_this_month.iloc[0]
            # however if this month is in the future, use the number from the current month instead
            else:
                homes_owned_this_month = seasonality_df.loc[(
                    (seasonality_df['year'] == CURRENT_YEAR)
                    & (seasonality_df['month'] == datetime.now().strftime('%B'))
                ), 'total_homes_owned'].iloc[0]
            seasonality_df.loc[
                ((seasonality_df['year'] == 'Budget') | (seasonality_df['year'] == CURRENT_MONTH_PROJECTED))
                & (seasonality_df['month'] == row['month']),
                'total_homes_owned'
            ] = homes_owned_this_month
        
        # compute spend per home
        seasonality_df['total_spend_per_home'] = round(seasonality_df['total_spend'] / seasonality_df['total_homes_owned'], 2)

    # display chart
    seasonality_chart(seasonality_df, 
        spend_col='total_spend_per_home' if spend_per_home else 'total_spend', 
        spend_title='Buildium Spend ($/Home)' if spend_per_home else 'Buildium Spend ($)', 
        budget_year=True, 
    )


def buildium_spend_line_items(all_management_expenses_df):
    if ("time_granularity_filter" in st.session_state and st.session_state["time_granularity_filter"] is not None) and ("category_filter" in st.session_state and st.session_state["category_filter"] is not None):
        st.subheader("Buildium Spend Line Items")    
        
        line_items_df = all_management_expenses_df.copy()
        line_items_df = line_items_df[line_items_df[st.session_state["time_granularity"]] == st.session_state["time_granularity_filter"]]
        line_items_df = line_items_df[line_items_df[st.session_state["category"]] == st.session_state["category_filter"]]

        line_items_cols = [
            'latchel_invoice_link',
            'category_group',
            'category_type',
            'gl_account',
            'address',
            'fund',
            'market',
            'date',
            'amount',
            'description',
            'vendor'
        ]
        def color_category(val):
            if val == 'R&M':
                return f'color: {TEAL}' 
            elif val == 'Capex':
                return f'color: {PURPLE}' 
            elif val == 'Common Area Maintenance':
                return f'color: {PINK}'

        styled_df = (
            line_items_df.assign(
                category_type=pd.Categorical(
                    line_items_df['category_type'], 
                    categories=['R&M', 'Capex', 'Common Area Maintenance'], 
                    ordered=True
                ),
                category_group=pd.Categorical(
                    line_items_df['category_group'], 
                    categories=['make_ready', 'run_rate', 'turn', 'disposition'], 
                    ordered=True
                )
            )
            .sort_values(['category_type', 'category_group'])
            [line_items_cols]
            .style.applymap(color_category, subset=['category_type'])
        )
        st.dataframe(
            styled_df, 
            hide_index=True,
            column_config={
                'latchel_invoice_link': st.column_config.LinkColumn(
                    label="latchel",
                    display_text=":material/link:",
                    width="small",
                    pinned=True,
                ),
                'gl_account': st.column_config.TextColumn(pinned=True),
                'category_group': st.column_config.TextColumn(pinned=True,),
                'category_type': st.column_config.TextColumn(pinned=True),
                'amount': st.column_config.NumberColumn(format="dollar"),
            }
        )


