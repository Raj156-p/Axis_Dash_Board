"""
Axis Bank Stock Dashboard
A Streamlit application for stock analysis with technical indicators
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random

# Page configuration
st.set_page_config(
    page_title="Axis Bank Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #97144D;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #97144D 0%, #c41d63 100%);
        border-radius: 16px;
        padding: 1.25rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .kpi-card-neutral {
        background: white;
        border-radius: 16px;
        padding: 1.25rem;
        border: 1px solid #e2e8f0;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .kpi-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        opacity: 0.8;
        margin-bottom: 0.5rem;
    }
    .kpi-value {
        font-size: 1.5rem;
        font-weight: 700;
    }
    .kpi-hint {
        font-size: 0.75rem;
        opacity: 0.9;
        margin-top: 0.25rem;
    }
    .stMetric {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)


# Seeded random for reproducible scenarios
def seeded_random(seed: int):
    random.seed(seed)
    def random_func():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        return seed / 0x7fffffff
    return random_func


# Generate simulated stock data
def generate_bars(symbol: str, start_date: datetime, end_date: datetime, max_bars: int = 950) -> pd.DataFrame:
    seed = sum(ord(c) for c in symbol) + int(start_date.timestamp())
    rng = seeded_random(seed)
    
    base_prices = {"AXISBANK.NS": 800, "RELIANCE.NS": 2500, "TCS.NS": 3500, "INFY.NS": 1500}
    base_price = base_prices.get(symbol, 100)
    
    price = base_price * (0.8 + rng() * 0.4)
    volatility = 0.02 + rng() * 0.01
    
    data = []
    current = start_date
    bar_count = 0
    
    while current <= end_date and bar_count < max_bars:
        if current.weekday() < 5:
            change = (rng() - 0.5) * 2 * volatility
            open_price = price
            close_price = max(1, price * (1 + change))
            high_price = max(open_price, close_price) * (1 + rng() * volatility * 0.5)
            low_price = min(open_price, close_price) * (1 - rng() * volatility * 0.5)
            volume = int(1000000 + rng() * 5000000)
            
            data.append({
                'Date': current,
                'Open': round(open_price, 2),
                'High': round(high_price, 2),
                'Low': round(low_price, 2),
                'Close': round(close_price, 2),
                'Volume': volume
            })
            price = close_price
            bar_count += 1
        current += timedelta(days=1)
    
    df = pd.DataFrame(data)
    return enrich_bars(df)


def enrich_bars(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Signal']
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    df['High_52W'] = df['High'].rolling(window=252).max()
    df['Low_52W'] = df['Low'].rolling(window=252).min()
    df['Daily_Return'] = df['Close'].pct_change() * 100
    return df


def monthly_volume(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['Month'] = df['Date'].dt.to_period('M')
    monthly = df.groupby('Month')['Volume'].sum().reset_index()
    monthly['Month'] = monthly['Month'].astype(str)
    return monthly


def format_inr(value: float) -> str:
    return f"₹{value:,.2f}"


def format_compact(value: int) -> str:
    if value >= 10000000:
        return f"{value/10000000:.1f} Cr"
    elif value >= 100000:
        return f"{value/100000:.1f} L"
    elif value >= 1000:
        return f"{value/1000:.1f} K"
    return str(value)


def main():
    st.markdown('<p class="main-header">Axis Bank Stock Dashboard</p>', unsafe_allow_html=True)
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 📊 Controls")
        symbol = st.text_input("Stock Symbol", value="AXISBANK.NS")
        today = datetime.today()
        start_date = st.date_input("Start Date", value=datetime(2023, 1, 1))
        end_date = st.date_input("End Date", value=today)
        show_bollinger = st.checkbox("Show Bollinger Bands", value=True)
        if st.button("🔍 Analyze", use_container_width=True):
            st.session_state['analyze'] = True
    
    if 'analyze' not in st.session_state:
        st.session_state['analyze'] = True
    if 'df' not in st.session_state:
        st.session_state['df'] = None
    
    if st.session_state['analyze'] or st.session_state.get('df') is None:
        if start_date and end_date and start_date < end_date:
            with st.spinner("Generating market data..."):
                df = generate_bars(symbol, datetime.combine(start_date, datetime.min.time()), 
                                   datetime.combine(end_date, datetime.min.time()))
                st.session_state['df'] = df
                st.session_state['symbol'] = symbol
        else:
            st.error("Please select a valid date range")
            return
    
    df = st.session_state['df']
    if df is None or len(df) == 0:
        st.warning("No data available.")
        return
    
    # Monthly Volume chart (fixed)
    st.subheader("📊 Monthly Trading Volume")
    monthly_df = monthly_volume(df)
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Bar(
        y=monthly_df['Volume'],
        x=monthly_df['Month'],
        name='Volume',
        marker_color='#97144D'
    ))
    fig_vol.update_layout(
        height=350,
        template='plotly_white',
        xaxis_title='',
        yaxis_title='Volume',
        showlegend=False,
        margin=dict(l=40, r=40, t=40
                   ))
