import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from PIL import Image
import requests
from io import BytesIO
import os

local_icon = r"C:\projectworks\test_folder\Axis_logo.png"

if os.path.exists(local_icon):
    icon = local_icon
else:
    icon = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Axis_Bank_logo.svg/512px-Axis_Bank_logo.svg.png"

st.set_page_config(
    page_title="Axis Bank Stock Dashboard",
    page_icon=icon,
    layout="wide"
)

@st.cache_data
def load_logo():
    local_path = r"C:\projectworks\test_folder\Axis_logo.png"
    if os.path.exists(local_path):
        return Image.open(local_path)
    try:
        url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Axis_Bank_logo.svg/512px-Axis_Bank_logo.svg.png"
        r = requests.get(url, timeout=5)
        return Image.open(BytesIO(r.content))
    except Exception:
        return None

logo = load_logo()

if logo:
    st.sidebar.image(logo, width=180)

st.sidebar.title("Axis Bank Analyzer")

symbol = st.sidebar.text_input("Stock Symbol", "AXISBANK.NS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))
run = st.sidebar.button("Analyze")

st.title("Axis Bank Stock Dashboard")

if run:
    with st.spinner("Loading data..."):
        df = yf.download(
            symbol,
            start=start_date,
            end=end_date,
            auto_adjust=True,
            progress=False
        )

        if df.empty:
            st.error("No data found for this stock.")
            st.stop()

        df.dropna(inplace=True)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df["Price_Change"] = df["Close"] - df["Open"]
        df["Daily_Return_Pct"] = (df["Close"] / df["Open"] - 1) * 100

        df["SMA_50"] = df["Close"].rolling(50).mean()
        df["SMA_200"] = df["Close"].rolling(200).mean()

        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()

        df["MACD"] = ema12 - ema26
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        rs = gain.rolling(14).mean() / loss.rolling(14).mean()
        df["RSI"] = 100 - (100 / (1 + rs))

        ma20 = df["Close"].rolling(20).mean()
        std20 = df["Close"].rolling(20).std()

        df["BB_Upper"] = ma20 + (2 * std20)
        df["BB_Lower"] = ma20 - (2 * std20)

        df["Month"] = df.index.month_name()
        df["Month_Num"] = df.index.month
        df["Quarter"] = df.index.to_period("Q").astype(str)
        df["Day"] = df.index.day_name()

        df["52W_High"] = df["Close"].rolling(252).max()
        df["52W_Low"] = df["Close"].rolling(252).min()

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Latest Close", f"₹{df['Close'].iloc[-1]:.2f}")
    c2.metric("Avg 52W High", f"₹{df['52W_High'].mean():.2f}")
    c3.metric("Avg 52W Low", f"₹{df['52W_Low'].mean():.2f}")
    c4.metric("Total Volume", f"{int(df['Volume'].sum()):,}")
    c5.metric("Latest RSI", f"{df['RSI'].iloc[-1]:.2f}")

    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close Price"))
    fig_price.add_trace(go.Scatter(x=df.index, y=df["SMA_50"], name="SMA 50"))
    fig_price.add_trace(go.Scatter(x=df.index, y=df["SMA_200"], name="SMA 200"))
    fig_price.update_layout(title="Price with Moving Averages")
    st.plotly_chart(fig_price, use_container_width=True)

    fig_candle = go.Figure()
    fig_candle.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Candlestick"
    ))
    fig_candle.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], name="Bollinger Upper"))
    fig_candle.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], name="Bollinger Lower"))
    fig_candle.update_layout(title="Candlestick with Bollinger Bands")
    st.plotly_chart(fig_candle, use_container_width=True)

    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD"))
    fig_macd.add_trace(go.Scatter(x=df.index, y=df["Signal"], name="Signal Line"))
    fig_macd.update_layout(title="MACD Indicator")
    st.plotly_chart(fig_macd, use_container_width=True)

    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI"))
    fig_rsi.add_hline(y=70, line_dash="dash")
    fig_rsi.add_hline(y=30, line_dash="dash")
    fig_rsi.update_layout(title="Relative Strength Index (RSI)")
    st.plotly_chart(fig_rsi, use_container_width=True)

    monthly = df.groupby(["Month_Num", "Month"])["Volume"].sum().reset_index().sort_values("Month_Num")
    fig_month = go.Figure(go.Bar(y=monthly["Month"], x=monthly["Volume"], orientation="h"))
    fig_month.update_layout(title="Monthly Trading Volume")
    st.plotly_chart(fig_month, use_container_width=True)

    st.download_button(
        "Download CSV",
        df.to_csv().encode("utf-8"),
        f"{symbol}_data.csv",
        "text/csv"
    )
else:
    st.info("Select parameters in the sidebar and click Analyze.")
