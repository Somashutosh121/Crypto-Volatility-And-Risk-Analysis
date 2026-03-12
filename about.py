import streamlit as st


def show_about():
    st.title("ℹ️ About This Project")

    st.markdown("""
    ## 📊 Crypto Volatility & Risk Analyzer

    This project is designed to analyze cryptocurrency market data 
    using real-time API integration and data visualization techniques.

    ### 🔹 Key Features
    - Live cryptocurrency market prices
    - 7-day historical price trends
    - Auto refresh functionality
    - CSV data export
    - Clean dashboard interface

    ### 🔹 Technologies Used
    - Python
    - Streamlit
    - CoinGecko REST API
    - Pandas
    - Data Visualization

    ### 🔹 Objective
    The goal of this project is to:
    - Fetch real-time crypto data
    - Analyze volatility
    - Visualize trends
    - Provide market insights

    ---
    👨‍💻 Developed as part of Milestone 1 – Data Acquisition
    """)
