import streamlit as st
import pandas as pd


@st.cache_data
def get_data(_credentials):
    query = """
        SELECT * 
        FROM `_` 
    """
    data = pd.read_gbq(query, credentials=_credentials)
    return data
