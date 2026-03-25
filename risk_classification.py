import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import numpy as np

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def show_milestone4():

    # ---------------------------------------
    # DARK UI STYLE
    # ---------------------------------------
    st.markdown("""
    <style>
    .stApp {
        background-color: #0f172a;
        color: white;
    }
    .card {
        padding: 8px;
        border-radius: 10px;
        margin-bottom: 8px;
        font-size: 13px;
    }
    .high { background-color: #7f1d1d; }
    .medium { background-color: #78350f; }
    .low { background-color: #064e3b; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Risk Classification Dashboard")

    crypto_ids = ["bitcoin", "ethereum", "cardano", "solana", "dogecoin"]

    # ---------------------------------------
    # FETCH DATA
    # ---------------------------------------
    @st.cache_data(ttl=60)
    def get_data(coin):
        url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
        params = {"vs_currency": "usd", "days": 30}

        try:
            res = requests.get(url, params=params)

            if res.status_code != 200:
                return None

            data = res.json()

            if "prices" not in data:
                return None

            prices = pd.DataFrame(data["prices"], columns=["time", "price"])
            prices["returns"] = prices["price"].pct_change()

            mean = prices["returns"].mean()
            std = prices["returns"].std()

            sharpe = (mean / std) * np.sqrt(365) if std != 0 else 0
            volatility = std * np.sqrt(365) * 100

            return {
                "Crypto": coin.upper(),
                "Price": prices["price"].iloc[-1],
                "Volatility": volatility,
                "Sharpe": sharpe
            }

        except:
            return None

    data = [get_data(c) for c in crypto_ids]
    data = [d for d in data if d is not None]

    if not data:
        st.error("⚠️ API Error: Unable to fetch crypto data.")
        st.stop()

    df = pd.DataFrame(data)

    # ---------------------------------------
    # RISK CLASSIFICATION
    # ---------------------------------------
    def classify(v):
        if v > 20:
            return "High"
        elif v > 10:
            return "Medium"
        else:
            return "Low"

    df["Risk"] = df["Volatility"].apply(classify)

    # ---------------------------------------
    # RISK CARDS
    # ---------------------------------------
    st.subheader("📊 Risk Categories")

    col1, col2, col3 = st.columns(3)

    def render_box(title, data, css):
        st.markdown(f"### {title} ({len(data)})")
        for _, row in data.iterrows():
            st.markdown(f"""
            <div class="card {css}">
                <b>{row['Crypto']}</b> | ${row['Price']:.2f}<br>
                📉 {row['Volatility']:.1f}% | 📊 {row['Sharpe']:.2f}
            </div>
            """, unsafe_allow_html=True)

    with col1:
        render_box("🔴 High", df[df["Risk"]=="High"], "high")

    with col2:
        render_box("🟡 Medium", df[df["Risk"]=="Medium"], "medium")

    with col3:
        render_box("🟢 Low", df[df["Risk"]=="Low"], "low")

    # ---------------------------------------
    # DONUT CHART
    # ---------------------------------------
    st.subheader("📈 Risk Distribution")

    order = ["High", "Medium", "Low"]
    risk_counts = df["Risk"].value_counts().reindex(order, fill_value=0).reset_index()
    risk_counts.columns = ["Risk", "Count"]

    summary = df.groupby("Risk").agg({
        "Sharpe": "mean",
        "Volatility": "mean"
    }).reset_index()

    merged = pd.merge(risk_counts, summary, on="Risk", how="left")

    fig = px.pie(
        merged,
        values="Count",
        names="Risk",
        hole=0.65
    )

    fig.update_traces(
        textinfo="label+percent",
        marker=dict(
            colors=["#ef4444", "#facc15", "#22c55e"],
            line=dict(color="#0f172a", width=2)
        ),
        pull=[0.08, 0.04, 0.02],
        customdata=merged[["Sharpe", "Volatility"]].values,
        hovertemplate=
        "<b>%{label}</b><br>" +
        "Count: %{value}<br>" +
        "Sharpe: %{customdata[0]:.2f}<br>" +
        "Volatility: %{customdata[1]:.2f}%"
    )

    fig.update_layout(
        annotations=[dict(
            text=f"Total<br>{len(df)}",
            x=0.5, y=0.5,
            showarrow=False,
            font_size=18,
            font_color="white"
        )],
        paper_bgcolor="#0f172a",
        font=dict(color="white"),
        legend=dict(orientation="h", y=-0.1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------
    # TABLE
    # ---------------------------------------
    st.subheader("📋 Detailed Data")
    st.dataframe(df)

    # ---------------------------------------
    # CSV DOWNLOAD
    # ---------------------------------------
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, "crypto_report.csv", "text/csv")

    # ---------------------------------------
    # PDF DOWNLOAD
    # ---------------------------------------
    def generate_pdf(df):
        file_path = "crypto_risk_report.pdf"
        doc = SimpleDocTemplate(file_path)

        styles = getSampleStyleSheet()
        elements = [Paragraph("Crypto Risk Report", styles["Title"])]

        data = [df.columns.tolist()] + df.values.tolist()

        table = Table(data)
        table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 1, colors.black)
        ]))

        elements.append(table)
        doc.build(elements)

        return file_path

    pdf = generate_pdf(df)

    with open(pdf, "rb") as f:
        st.download_button("📄 Download PDF", f, "crypto_report.pdf")