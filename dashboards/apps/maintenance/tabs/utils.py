import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime

LIGHT_GRAY = "#d3d3d3"
GRAY = "#808080" 
LIGHT_RED = "#ffcdd2"
RED = "#f44336"
ORANGE = "#ffa500"
YELLOW = "#ffd700"
GREEN = "#5cdb97"
LIGHT_TEAL = "#5cc9b8" 
TEAL = "#15b8a6" 
DARK_TEAL = "#0E8074"
LIGHT_PURPLE = "#d1c4e9" 
PURPLE = "#9575cd" 
DARK_PURPLE = "#512da8" 
PINK = "#ffc0cb"
PASTEL_LILAC = "#E4C1F9"
PASTEL_LIGHT_BLUE = "#C6DEF1"
PASTEL_SOFT_PINK = "#F6BDC0"
PASTEL_YELLOW = "#F7E1A0"
PASTEL_MINT = "#C9E4DE"

CURRENT_YEAR = datetime.now().year

MONTH_ORDER = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]


def all_management_expenses_data_clean(all_management_expenses_df):
    cleaned_all_management_expenses_df = all_management_expenses_df.copy()

    # week & month end dates
    cleaned_all_management_expenses_df['date_time'] = pd.to_datetime(cleaned_all_management_expenses_df['date'])
    cleaned_all_management_expenses_df['week_end'] = (cleaned_all_management_expenses_df['date_time'] + pd.to_timedelta(6 - cleaned_all_management_expenses_df['date_time'].dt.weekday, unit='d')).dt.strftime('%Y-%m-%d')
    cleaned_all_management_expenses_df['month_end'] = (cleaned_all_management_expenses_df['date_time'] + pd.offsets.MonthEnd(0)).dt.strftime('%Y-%m-%d')
    cleaned_all_management_expenses_df['month'] = cleaned_all_management_expenses_df['date_time'].dt.strftime('%B')
    cleaned_all_management_expenses_df['year'] = cleaned_all_management_expenses_df['date_time'].dt.year

    # gl account
    cleaned_all_management_expenses_df['gl_account'] = cleaned_all_management_expenses_df['gl_account_number'] + ' (' + cleaned_all_management_expenses_df['gl_account_name'] + ')'

    # vendor
    cleaned_all_management_expenses_df['vendor_company_name'] = (
        cleaned_all_management_expenses_df['vendor_company_name'] 
        .apply(lambda x: x.strip() if isinstance(x, str) else x)
        .replace([None, '', 'None', 'nan', 'NaN'], np.nan)         
    )
    cleaned_all_management_expenses_df['vendor_contact_name'] = (
        cleaned_all_management_expenses_df['vendor_contact_name']
        .apply(lambda x: x.strip() if isinstance(x, str) else x)
        .replace([None, '', 'None', 'nan', 'NaN'], np.nan)
    )
    cleaned_all_management_expenses_df['vendor'] = np.select(
        [
            cleaned_all_management_expenses_df['vendor_contact_name'].notna() & cleaned_all_management_expenses_df['vendor_company_name'].notna(),
            cleaned_all_management_expenses_df['vendor_contact_name'].notna() & cleaned_all_management_expenses_df['vendor_company_name'].isna(),
            cleaned_all_management_expenses_df['vendor_contact_name'].isna() & cleaned_all_management_expenses_df['vendor_company_name'].notna(),
        ],
        [
            cleaned_all_management_expenses_df['vendor_company_name'] + ' (' + cleaned_all_management_expenses_df['vendor_contact_name'] + ')', 
            '(' + cleaned_all_management_expenses_df['vendor_contact_name'] + ')', 
            cleaned_all_management_expenses_df['vendor_company_name'],
        ],
        default='No vendor'
    )

    # category group & type
    cleaned_all_management_expenses_df[['category_group', 'category_type']] = cleaned_all_management_expenses_df['category'].apply(
        lambda x: pd.Series([
            x.replace('_r_m', '') if 'r_m' in x else 
            x.replace('_capex', '') if 'capex' in x else
            'common_area_maintenance' if x == 'common_area_maintenance' else
            np.nan,
            'R&M' if 'r_m' in x else 
            'Capex' if 'capex' in x else 
            'Common Area Maintenance' if x == 'common_area_maintenance' else 
            np.nan
        ])
    )

    # latchel invoice link
    cleaned_all_management_expenses_df['latchel_invoice_link'] = (
        cleaned_all_management_expenses_df['latchel_invoice_id'].apply(
            lambda x: f'https://app.latchel.com/admin/invoices/{x}' if x is not None else ''
        )
    )

    return cleaned_all_management_expenses_df


def owned_homes_data_clean(owned_homes_df):
    cleaned_owned_homes_df = owned_homes_df.copy()
    cleaned_owned_homes_df['date_time'] = pd.to_datetime(cleaned_owned_homes_df['date'])
    cleaned_owned_homes_df['month'] = cleaned_owned_homes_df['date_time'].dt.strftime('%B')
    cleaned_owned_homes_df['year'] = cleaned_owned_homes_df['date_time'].dt.year
    cleaned_owned_homes_df['date'] = cleaned_owned_homes_df['date_time'].dt.strftime('%Y-%m-%d')
    return cleaned_owned_homes_df


def budget_by_month_data_clean(budget_by_month_df):
    cleaned_budget_by_month_df = budget_by_month_df.copy()
    cleaned_budget_by_month_df['date_time'] = pd.to_datetime(cleaned_budget_by_month_df['date'])
    cleaned_budget_by_month_df['month'] = cleaned_budget_by_month_df['date_time'].dt.strftime('%B')
    cleaned_budget_by_month_df['year'] = cleaned_budget_by_month_df['date_time'].dt.year
    cleaned_budget_by_month_df['date'] = cleaned_budget_by_month_df['date_time'].dt.strftime('%Y-%m-%d')
    return cleaned_budget_by_month_df[cleaned_budget_by_month_df['year'] == CURRENT_YEAR]


def seasonality_chart(seasonality_df, spend_col, spend_title, budget_year=False):
    PASTEL_PALETTE = [PASTEL_LILAC, PASTEL_LIGHT_BLUE, PASTEL_SOFT_PINK, PASTEL_MINT]
    
    # convert year to string, if not already 
    seasonality_df['year'] = seasonality_df['year'].astype(str)
    years = [y for y in seasonality_df['year'].unique() if y not in [str(CURRENT_YEAR), 'Budget']]
    color_scale = alt.Scale(
        domain=years + [str(CURRENT_YEAR)] + (['Budget'] if budget_year else []),
        range=PASTEL_PALETTE[:len(years)] + [TEAL] + ([PASTEL_YELLOW] if budget_year else [])
    )
    seasonality_chart = (
        alt.Chart(seasonality_df)
        .mark_line(point=True)
        .encode(
            x=alt.X('month', sort=MONTH_ORDER, title='Month'),
            y=alt.Y(spend_col, title=spend_title),
            color=alt.Color('year:N', title='Year', scale=color_scale),
            strokeWidth=alt.condition(
                f"datum.year == {CURRENT_YEAR}", alt.value(3), alt.value(1.5)
            ),
            tooltip=['year', 'month', spend_col]
        )
        .properties(width=700, height=400)
        .interactive()
    )
    st.altair_chart(seasonality_chart, use_container_width=True)
