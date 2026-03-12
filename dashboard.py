import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime


# ---------------- LIVE MARKET DATA ----------------
@st.cache_data(ttl=25)
def get_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 5,
        "page": 1,
        "sparkline": False
    }
    r = requests.get(url, params=params, timeout=10)
    return r.json() if r.status_code == 200 else None


# ---------------- DAILY PRICE DATA ----------------
@st.cache_data(ttl=25)
def get_daily_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": 7
    }
    r = requests.get(url, params=params, timeout=10)

    if r.status_code != 200:
        return None

    prices = r.json()["prices"]
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.dropna(inplace=True)

    return df[["date", "price"]]


# ---------------- DASHBOARD ----------------
def show_dashboard():
    st.title("📊 Crypto Market Dashboard")

    # ----- LOGOUT -----
    if st.button("Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.rerun()

    st.divider()

    # ----- AUTO REFRESH -----
    auto_refresh = st.toggle("🔄 Auto Refresh (30 sec)", key="auto_refresh")

    if auto_refresh:
        st.session_state.last_updated = datetime.now().strftime(
            "%a, %d %b %Y · %H:%M:%S"
        )
        time.sleep(30)
        st.rerun()

    # ----- LAYOUT -----
    left, right = st.columns([1, 2])

    # ================= LEFT PANEL =================
    with left:
        st.subheader("📌 Milestone 1: Data Acquisition")
        st.markdown("""
        **Requirements**
        - Python Environment Setup  
        - CoinGecko API Integration  
        - Data storage in CSV format
        - Preprocessing missing values 

        **Outputs**
        - Live crypto prices  
        - Daily historical trends  
        - Verified API connectivity  
        """)

    # ================= RIGHT PANEL =================
    with right:
        st.subheader("🔴 Crypto Data Fetcher")

        btn_col, time_col = st.columns([1, 3])

        # ----- MANUAL REFRESH -----
        with btn_col:
            if st.button("🔄 Manual Refresh", key="manual_refresh"):
                st.session_state.last_updated = datetime.now().strftime(
                    "%a, %d %b %Y · %H:%M:%S"
                )
                st.rerun()

        # ----- LIVE INDICATOR + TIMESTAMP -----
        with time_col:
            blink = "🟢 LIVE" if int(time.time()) % 2 == 0 else "⚫ LIVE"
            if "last_updated" in st.session_state:
                st.caption(f"{blink} | Updated: {st.session_state.last_updated}")
            else:
                st.caption("⚫ LIVE | Not refreshed yet")

        # ----- FETCH DATA -----
        data = get_crypto_data()

        if not data:
            st.error("Failed to load data")
            return

        df = pd.DataFrame(data)[
            ["id", "name", "current_price", "price_change_percentage_24h", "total_volume"]
        ]

        df.columns = [
            "id",
            "Cryptocurrency",
            "Price (USD)",
            "24h Change (%)",
            "Volume (24h)"
        ]

        df.dropna(inplace=True)

        # ----- GREEN / RED COLOR BASED ON PRICE CHANGE -----
        def color_change(val):
            if val > 0:
                return "color: green"
            elif val < 0:
                return "color: red"
            return ""

        styled_df = df.drop(columns=["id"]).style.applymap(
            color_change,
            subset=["24h Change (%)"]
        )

        st.dataframe(styled_df, use_container_width=True)

        # ----- EXPORT CSV BUTTON -----
        st.download_button(
            label="⬇️ Download Live Market CSV",
            data=df.to_csv(index=False),
            file_name="crypto_live_market_data.csv",
            mime="text/csv",
            key="download_live_csv"
        )

    st.divider()

    # ================= DAILY PRICE VISUALIZATION =================
    st.subheader("📈 7-Day Daily Price Trend")

    coin_map = dict(zip(df["Cryptocurrency"], df["id"]))

    selected_coin = st.selectbox(
        "Select Cryptocurrency",
        coin_map.keys(),
        key="coin_selector"
    )

    daily_df = get_daily_price(coin_map[selected_coin])

    if daily_df is not None:
        st.line_chart(
            daily_df.set_index("date")["price"]
        )
    else:
        st.warning("Daily data not available")
