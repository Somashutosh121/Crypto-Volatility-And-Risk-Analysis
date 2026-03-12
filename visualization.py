import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import time  # added for retry delay

def show_milestone3():

    # ===============================
    # DARK THEME
    # ===============================
    st.markdown("""
        <style>
        .stApp {
            background-color: #0E1117;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("📊 Crypto Risk Analytics Dashboard")

    # ===============================
    # COINS
    # ===============================
    COINS = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "ADA": "cardano"
    }

    # ===============================
    # FETCH DATA
    # ===============================
    @st.cache_data
    def fetch_data(days=365):

        all_data = []

        for symbol, coin_id in COINS.items():

            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {"vs_currency": "usd", "days": days}

            try:
                response = requests.get(url, params=params)
                time.sleep(1)  # avoid rate-limit

                # Retry once if failed
                if response.status_code != 200:
                    response = requests.get(url, params=params)
                    time.sleep(1)
                    if response.status_code != 200:
                        st.warning(f"Failed to fetch data for {symbol}")
                        continue

                data = response.json()

                # Check prices key
                if "prices" not in data:
                    st.warning(f"No price data for {symbol}")
                    continue

                prices = data["prices"]

                df = pd.DataFrame(prices, columns=["timestamp", "Close"])
                df["Date"] = pd.to_datetime(df["timestamp"], unit="ms")
                df["Crypto"] = symbol
                df = df[["Date", "Crypto", "Close"]]

                df["Returns"] = df["Close"].pct_change()
                df["Volatility"] = df["Returns"].rolling(7).std()

                df.dropna(inplace=True)
                all_data.append(df)

            except Exception as e:
                st.warning(f"Error fetching {symbol}: {e}")
                continue

        if len(all_data) == 0:
            st.error("No crypto data could be loaded.")
            return pd.DataFrame()

        return pd.concat(all_data)

    df = fetch_data()

    if df.empty:
        st.stop()

    # ===============================
    # CUSTOM BUTTON CRYPTO SELECTOR
    # ===============================
    st.subheader("Select Cryptocurrencies")

    if "selected_coins" not in st.session_state:
        st.session_state.selected_coins = list(COINS.keys())

    button_cols = st.columns(len(COINS))

    for i, coin in enumerate(COINS.keys()):
        if button_cols[i].button(coin):
            if coin in st.session_state.selected_coins:
                st.session_state.selected_coins.remove(coin)
            else:
                st.session_state.selected_coins.append(coin)

    selected_crypto = st.session_state.selected_coins

    st.write("Selected:", ", ".join(selected_crypto))

    # ===============================
    # DATE FILTER
    # ===============================
    date_range = st.date_input(
        "Select Date Range",
        [df["Date"].min(), df["Date"].max()]
    )

    filtered_df = df[
        (df["Crypto"].isin(selected_crypto)) &
        (df["Date"] >= pd.to_datetime(date_range[0])) &
        (df["Date"] <= pd.to_datetime(date_range[1]))
    ]

    # ===============================
    # PRICE & VOLATILITY
    # ===============================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Price Trend")
        fig_price = px.line(
            filtered_df,
            x="Date",
            y="Close",
            color="Crypto",
            template="plotly_dark"
        )
        st.plotly_chart(fig_price, use_container_width=True)

    with col2:
        st.subheader("📉 Volatility Trend")
        fig_vol = px.line(
            filtered_df,
            x="Date",
            y="Volatility",
            color="Crypto",
            template="plotly_dark"
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    # ===============================
    # RISK RETURN + KPI COLUMN
    # ===============================
    col3, col4 = st.columns([2,1])

    with col3:
        st.subheader("⚖ Risk-Return Analysis")
        risk_return = filtered_df.groupby("Crypto").agg({
            "Returns": "mean",
            "Volatility": "mean"
        }).reset_index()
        risk_return["Size"] = risk_return["Returns"].abs() * 400

        fig_scatter = px.scatter(
            risk_return,
            x="Volatility",
            y="Returns",
            color="Crypto",
            size="Size",
            template="plotly_dark",
            height=350
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ===============================
    # KPI CALCULATIONS
    # ===============================
    volatility = filtered_df["Volatility"].mean()
    avg_return = filtered_df["Returns"].mean()
    sharpe = 0
    if filtered_df["Returns"].std() != 0:
        sharpe = avg_return / filtered_df["Returns"].std()

    beta = 0
    if "BTC" in selected_crypto:
        btc_df = filtered_df[filtered_df["Crypto"] == "BTC"][["Date","Returns"]]
        btc_df = btc_df.rename(columns={"Returns":"BTC_Returns"})
        merged = pd.merge(filtered_df, btc_df, on="Date", how="inner")
        if not merged.empty:
            covariance = np.cov(merged["Returns"], merged["BTC_Returns"])[0][1]
            btc_variance = merged["BTC_Returns"].var()
            if btc_variance != 0:
                beta = covariance / btc_variance

    if volatility < 0.02:
        risk_level = "Low Risk"
        risk_color = "#2ca02c"
    elif volatility < 0.05:
        risk_level = "Medium Risk"
        risk_color = "#ff7f0e"
    else:
        risk_level = "High Risk"
        risk_color = "#d62728"

    # ===============================
    # KPI COLUMN
    # ===============================
    with col4:
        st.subheader("📊 Metrics")

        def small_kpi(title, value, color):
            st.markdown(f"""
                <div style="
                    background-color: {color};
                    padding: 12px;
                    margin-bottom: 10px;
                    border-radius: 8px;
                    text-align: center;
                    color: white;
                    font-size: 14px;
                    box-shadow: 0px 3px 8px rgba(0,0,0,0.4);
                ">
                    <strong>{title}</strong><br>
                    {value}
                </div>
            """, unsafe_allow_html=True)

        small_kpi("Volatility", round(volatility,4), "#1f77b4")
        small_kpi("Avg Return", round(avg_return,4), "#2ca02c")
        small_kpi("Sharpe Ratio", round(sharpe,4), "#ff7f0e")
        small_kpi("Beta vs BTC", round(beta,4), "#9467bd")
        small_kpi("Risk Level", risk_level, risk_color)