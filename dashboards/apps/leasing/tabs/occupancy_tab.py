import streamlit as st

def occupancy_forecast(projected_economic_occupancy_df, budget_economic_occupancy_df):
    st.subheader("Occupancy Forecast")

    st.write('Projected Economic Occupancy')
    st.dataframe(projected_economic_occupancy_df)
   
    st.write('Budget Economic Occupancy')
    st.dataframe(budget_economic_occupancy_df)

def occupancy_targets():
    st.subheader("Occupancy Targets")
