import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import numpy as np


# KEVIN TO DO
def conversion_rates(conversion_rates_df):
    st.subheader("Conversion Rates")
    st.write(conversion_rates_df)