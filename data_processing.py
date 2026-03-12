import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# ===============================
# Milestone 2 – Risk Dashboard
# ===============================

def show_milestone2():

    st.title("📌 Milestone 2 -Data Processing and Calculation")
    st.markdown("Live Risk Analysis using Log Returns")

    # -----------------------------
    # Sidebar Controls
    # -----------------------------

    st.sidebar.header("⚙ Controls")

    timeframe = st.sidebar.radio(
        "Select Timeframe",
        ["30D", "90D", "1Y"]
    )

    refresh = st.sidebar.button("🔄 Refresh Data")

    # -----------------------------
    # Timeframe Logic
    # -----------------------------

    if timeframe == "30D":
        days = 30
    elif timeframe == "90D":
        days = 90
    else:
        days = 365

    start_date = datetime.today() - timedelta(days=days)
    end_date = datetime.today()

    # -----------------------------
    # Download Data
    # -----------------------------

    assets = {
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
        "SOL": "SOL-USD",
        "ADA": "ADA-USD",
        "DOGE": "DOGE-USD"
    }

    df = yf.download(
        list(assets.values()),
        start=start_date,
        end=end_date,
        progress=False
    )["Close"]

    df.columns = assets.keys()
    df = df.fillna(method="ffill")

    # -----------------------------
    # Log Returns
    # -----------------------------

    log_returns = np.log(df / df.shift(1)).dropna()

    # -----------------------------
    # Risk Calculations
    # -----------------------------

    daily_volatility = log_returns.std()
    annual_volatility = daily_volatility * np.sqrt(252)

    mean_return = log_returns.mean()
    sharpe_ratio = mean_return / daily_volatility

    # Parametric VaR (95%)
    z_score = 1.65
    var_95 = mean_return - z_score * daily_volatility

    # Beta (vs BTC)
    benchmark = log_returns["BTC"]
    beta_values = {}

    for asset in log_returns.columns:
        if asset != "BTC":
            covariance = np.cov(log_returns[asset], benchmark)[0][1]
            market_variance = np.var(benchmark)
            beta_values[asset] = covariance / market_variance
        else:
            beta_values["BTC"] = 1.0

    beta_series = pd.Series(beta_values)

    # -----------------------------
    # Logo Mapping
    # -----------------------------

    logos = {
        "BTC": "https://cryptologos.cc/logos/bitcoin-btc-logo.png",
        "ETH": "https://cryptologos.cc/logos/ethereum-eth-logo.png",
        "SOL": "https://cryptologos.cc/logos/solana-sol-logo.png",
        "ADA": "https://cryptologos.cc/logos/cardano-ada-logo.png",
        "DOGE": "https://cryptologos.cc/logos/dogecoin-doge-logo.png"
    }

    # -----------------------------
    # Create Table with Color Coding
    # -----------------------------

    crypto_with_logo = []
    volatility_styles = []

    high_threshold = annual_volatility.quantile(0.66)
    low_threshold = annual_volatility.quantile(0.33)

    for asset in annual_volatility.index:

        crypto_with_logo.append(
            f'<img src="{logos[asset]}" width="25"> {asset}'
        )

        vol_value = annual_volatility[asset]

        if vol_value >= high_threshold:
            volatility_styles.append("background-color:#ff4d4d; color:white;")
        elif vol_value <= low_threshold:
            volatility_styles.append("background-color:#4CAF50; color:white;")
        else:
            volatility_styles.append("background-color:#ffa500; color:white;")

    metrics_table = pd.DataFrame({
        "Cryptocurrency": crypto_with_logo,
        "Annual Volatility": annual_volatility.values,
        "Sharpe Ratio": sharpe_ratio.values,
        "Beta (vs BTC)": beta_series.values,
        "VaR (95%)": var_95.values
    })

    # Convert to HTML
    html_table = metrics_table.to_html(escape=False, index=False)

    # Inject color styling into Annual Volatility column
    for i, style in enumerate(volatility_styles):
        html_table = html_table.replace(
            f"<td>{annual_volatility.values[i]}</td>",
            f'<td style="{style}">{annual_volatility.values[i]:.4f}</td>'
        )

    # -----------------------------
    # Layout (Wider Table)
    # -----------------------------

    col1, col2 = st.columns([3.5, 1])

    with col1:
        st.subheader("📌 Risk Metrics Table")
        st.write(html_table, unsafe_allow_html=True)

    with col2:
        st.subheader("🏆 Risk Insights")
        st.success(f"🔥 Most Volatile: {annual_volatility.idxmax()}")
        st.success(f"🏆 Best Sharpe: {sharpe_ratio.idxmax()}")

    # -----------------------------
    # Volatility Ranking Chart
    # -----------------------------

    st.subheader("📊 Annual Volatility Comparison")
    st.bar_chart(annual_volatility.sort_values(ascending=False))

    # -----------------------------
    # Rolling Volatility (Fixed 30-Day)
    # -----------------------------

    rolling_volatility = log_returns.rolling(window=30).std() * np.sqrt(252)

    st.subheader(f"📈 30-Day Rolling Volatility ({timeframe} Data)")
    st.line_chart(rolling_volatility)

    st.markdown("---")
    st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
