import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from PIL import Image
import requests
from io import BytesIO
import os
import random

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Axis Bank Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# CUSTOM STYLING (Matched to Video)
# --------------------------------------------------
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1e293b; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1rem; color: #64748b; margin-bottom: 2rem; }
    
    .kpi-container { display: flex; gap: 1rem; margin-bottom: 2rem; }
    
    .kpi-card-main {
        flex: 1;
        background: #97144D;
        border-radius: 12px;
        padding: 1.5rem 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .kpi-card-neutral {
        flex: 1;
        background: white;
        border-radius: 12px;
        padding: 1.5rem 1rem;
        border: 1px solid #e2e8f0;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .kpi-label { font-size: 0.75rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; opacity: 0.8; margin-bottom: 0.5rem; }
    .kpi-label-neutral { font-size: 0.75rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; color: #64748b; margin-bottom: 0.5rem; }
    
    .kpi-value { font-size: 1.8rem; font-weight: 700; margin-bottom: 0.2rem; }
    .kpi-value-neutral { font-size: 1.8rem; font-weight: 700; color: #1e293b; margin-bottom: 0.2rem; }
    
    .kpi-hint { font-size: 0.8rem; opacity: 0.9; }
    .kpi-hint-neutral { font-size: 0.8rem; color: #64748b; }
    
    .kpi-hint-up { font-size: 0.85rem; color: #a3e635; font-weight: 600; }
    .kpi-hint-down { font-size: 0.85rem; color: #f87171; font-weight: 600; }
    
    .stButton>button { width: 100%; border-radius: 6px; }
    .btn-analyze>button { background-color: #97144D; color: white; border: none; }
    .btn-analyze>button:hover { background-color: #7a0f3d; color: white; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
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

def seeded_random(seed: int):
    random.seed(seed)
    def random_func():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        return seed / 0x7fffffff
    return random_func

def format_compact(value: float) -> str:
    if value >= 10000000:
        return f"{value/10000000:.1f} Cr"
    elif value >= 100000:
        return f"{value/100000:.1f} L"
    elif value >= 1000:
        return f"{value/1000:.1f} K"
    return str(int(value))

# --------------------------------------------------
# SIMULATED DATA GENERATOR
# --------------------------------------------------
def generate_bars(symbol: str, start_date: datetime, end_date: datetime, seed_offset: int) -> pd.DataFrame:
    seed = sum(ord(c) for c in symbol) + int(start_date.timestamp()) + seed_offset
    rng = seeded_random(seed)
    
    base_price = 800 if "AXIS" in symbol else 100
    price = base_price * (0.8 + rng() * 0.4)
    volatility = 0.02 + rng() * 0.01
    
    data = []
    current = start_date
    
    while current <= end_date:
        if current.weekday() < 5:  # Skip weekends
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
        current += timedelta(days=1)
    
    df = pd.DataFrame(data)
    
    # Calculate indicators
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
    df['Daily_Return_Pct'] = df['Close'].pct_change() * 100
    
    return df.dropna().reset_index(drop=True)

# --------------------------------------------------
# MAIN APPLICATION
# --------------------------------------------------
def main():
    # Session States
    if 'data_seed' not in st.session_state:
        st.session_state.data_seed = 42
    if 'analyze' not in st.session_state:
        st.session_state.analyze = True

    # Sidebar
    with st.sidebar:
        logo = load_logo()
        if logo:
            st.image(logo, width=150)
            
        st.markdown("### Stock Symbol")
        symbol = st.text_input("", value="AXISBANK.NS", label_visibility="collapsed")
        
        start_date = st.date_input("Start Date", value=pd.to_datetime("2025-01-01"))
        end_date = st.date_input("End Date", value=pd.to_datetime("2026-04-30"))
        
        show_bollinger = st.checkbox("Show Bollinger Bands", value=True)
        
        st.markdown('<div class="btn-analyze">', unsafe_allow_html=True)
        if st.button("▶ Analyze", use_container_width=True):
            st.session_state.analyze = True
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("↻ Regenerate Scenario", use_container_width=True):
            st.session_state.data_seed = random.randint(1, 100000)
            st.session_state.analyze = True
            
        # Download logic prepared (button rendered after data generation)
        download_placeholder = st.empty()
        
        st.markdown("""
        <div style='font-size: 0.75rem; color: #64748b; margin-top: 2rem;'>
        Data shown is a simulated market scenario for demonstration, computing the same technical indicators (SMA, MACD, RSI, Bollinger Bands) used in the original dashboard.
        </div>
        """, unsafe_allow_html=True)

    # Main Dashboard Header
    st.markdown('<div class="main-header">Axis Bank Stock Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Advanced technical analysis and market indicators</div>', unsafe_allow_html=True)

    if st.session_state.analyze:
        with st.spinner("Generating scenario data..."):
            df = generate_bars(
                symbol, 
                datetime.combine(start_date, datetime.min.time()), 
                datetime.combine(end_date, datetime.min.time()),
                st.session_state.data_seed
            )
            st.session_state.df = df
            st.session_state.analyze = False 

    if 'df' not in st.session_state or st.session_state.df is None or st.session_state.df.empty:
        st.warning("No data available for the selected range.")
        return

    df = st.session_state.df

    # Populate Download Button
    csv = df.to_csv(index=False).encode('utf-8')
    with download_placeholder:
        st.download_button(
            label="⤓ Download CSV",
            data=csv,
            file_name=f"{symbol}_simulated_data.csv",
            mime="text/csv",
            use_container_width=True
        )

    # --------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    change = latest['Close'] - prev['Close']
    change_pct = (change / prev['Close']) * 100
    
    change_class = "kpi-hint-up" if change >= 0 else "kpi-hint-down"
    change_sign = "+" if change >= 0 else ""
    
    avg_52h = df['High_52W'].mean()
    avg_52l = df['Low_52W'].mean()
    total_vol = df['Volume'].sum()
    
    kpi_html = f"""
    <div class="kpi-container">
        <div class="kpi-card-main">
            <div class="kpi-label">LATEST CLOSE</div>
            <div class="kpi-value">₹{latest['Close']:,.2f}</div>
            <div class="{change_class}">{change_sign}{change_pct:.2f}%</div>
        </div>
        <div class="kpi-card-neutral">
            <div class="kpi-label-neutral">AVG 52W HIGH</div>
            <div class="kpi-value-neutral">₹{avg_52h:,.2f}</div>
            <div class="kpi-hint-neutral">Rolling Maximum</div>
        </div>
        <div class="kpi-card-neutral">
            <div class="kpi-label-neutral">AVG 52W LOW</div>
            <div class="kpi-value-neutral">₹{avg_52l:,.2f}</div>
            <div class="kpi-hint-neutral">Rolling Minimum</div>
        </div>
        <div class="kpi-card-neutral">
            <div class="kpi-label-neutral">TOTAL VOLUME</div>
            <div class="kpi-value-neutral">{format_compact(total_vol)}</div>
            <div class="kpi-hint-neutral">Shares Traded</div>
        </div>
        <div class="kpi-card-neutral">
            <div class="kpi-label-neutral">LATEST RSI</div>
            <div class="kpi-value-neutral">{latest['RSI']:.2f}</div>
            <div class="kpi-hint-neutral">{'Overbought' if latest['RSI']>70 else 'Oversold' if latest['RSI']<30 else 'Neutral'}</div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)

    # --------------------------------------------------
    # CHART 1: Price with Moving Averages
    # --------------------------------------------------
    st.markdown("#### Price with Moving Averages")
    st.markdown("<span style='color:#64748b; font-size:0.9rem;'>Close Price, SMA 50 and SMA 200</span>", unsafe_allow_html=True)
    
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='Close', line=dict(color='#97144D', width=2)))
    fig_price.add_trace(go.Scatter(x=df['Date'], y=df['SMA_200'], name='SMA 200', line=dict(color='#eab308', width=2)))
    fig_price.add_trace(go.Scatter(x=df['Date'], y=df['SMA_50'], name='SMA 50', line=dict(color='#3b82f6', width=2)))
    
    fig_price.update_layout(
        height=400, margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
    )
    st.plotly_chart(fig_price, use_container_width=True)

    # --------------------------------------------------
    # CHART 2: Candlestick + Bollinger (WITH CLARITY FIX)
    # --------------------------------------------------
    st.markdown("#### Candlestick with Bollinger Bands")
    st.markdown("<span style='color:#64748b; font-size:0.9rem;'>OHLC price action</span>", unsafe_allow_html=True)
    
    fig_candle = go.Figure()
    fig_candle.add_trace(go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='Candlestick',
        increasing_line_color='#22c55e', decreasing_line_color='#ef4444'
    ))
    
    if show_bollinger:
        fig_candle.add_trace(go.Scatter(x=df['Date'], y=df['BB_Upper'], name='Bollinger Upper', line=dict(color='rgba(168, 85, 247, 0.5)', dash='dash')))
        fig_candle.add_trace(go.Scatter(x=df['Date'], y=df['BB_Middle'], name='Bollinger Middle', line=dict(color='rgba(168, 85, 247, 0.8)', dash='dot')))
        fig_candle.add_trace(go.Scatter(x=df['Date'], y=df['BB_Lower'], name='Bollinger Lower', line=dict(color='rgba(168, 85, 247, 0.5)', dash='dash')))

    # CLARITY FIX: Remove range slider, hide weekends, and set default view to last 90 days
    last_date = df['Date'].max()
    start_view = last_date - timedelta(days=90) # Zoom into recent 3 months by default

    fig_candle.update_layout(
        height=450, margin=dict(l=20, r=20, t=20, b=20),
        xaxis_rangeslider_visible=False, # Fix 1: Removes the bulky bottom slider
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(
            showgrid=True, gridcolor='#f1f5f9',
            range=[start_view, last_date], # Fix 2: Auto-zoom so candles aren't squashed
            rangebreaks=[dict(bounds=["sat", "mon"])] # Fix 3: Remove empty weekend gaps
        ),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
    )
    st.plotly_chart(fig_candle, use_container_width=True)

    # --------------------------------------------------
    # ROW 3: MACD & RSI (Side by Side)
    # --------------------------------------------------
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### MACD Indicator")
        st.markdown("<span style='color:#64748b; font-size:0.9rem;'>12/26 EMA with 9-period signal</span>", unsafe_allow_html=True)
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Bar(x=df['Date'], y=df['Histogram'], name='Histogram', marker_color='rgba(151, 20, 77, 0.5)'))
        fig_macd.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], name='MACD', line=dict(color='#97144D')))
        fig_macd.add_trace(go.Scatter(x=df['Date'], y=df['Signal'], name='Signal', line=dict(color='#eab308')))
        fig_macd.update_layout(
            height=300, margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='#f1f5f9', rangebreaks=[dict(bounds=["sat", "mon"])]),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
        )
        st.plotly_chart(fig_macd, use_container_width=True)

    with col2:
        st.markdown("#### Relative Strength Index (RSI)")
        st.markdown("<span style='color:#64748b; font-size:0.9rem;'>14-period, overbought/oversold bands</span>", unsafe_allow_html=True)
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name='RSI', line=dict(color='#8b5cf6')))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ef4444")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="#22c55e")
        fig_rsi.update_layout(
            height=300, margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='#f1f5f9', rangebreaks=[dict(bounds=["sat", "mon"])]),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
        )
        st.plotly_chart(fig_rsi, use_container_width=True)

    # --------------------------------------------------
    # CHART 4: Monthly Volume
    # --------------------------------------------------
    st.markdown("#### Monthly Trading Volume")
    st.markdown("<span style='color:#64748b; font-size:0.9rem;'>Aggregated share volume by month</span>", unsafe_allow_html=True)
    
    df['Month_Year'] = df['Date'].dt.to_period('M').astype(str)
    monthly_vol = df.groupby('Month_Year')['Volume'].sum().reset_index()
    
    fig_vol = go.Figure(go.Bar(
        y=monthly_vol['Month_Year'], 
        x=monthly_vol['Volume'], 
        orientation='h', 
        marker_color='#97144D'
    ))
    fig_vol.update_layout(
        height=350, margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
        yaxis=dict(showgrid=False, autorange="reversed")
    )
    st.plotly_chart(fig_vol, use_container_width=True)

    # --------------------------------------------------
    # RECENT DATA TABLE
    # --------------------------------------------------
    st.markdown("#### Recent Data")
    st.markdown("<span style='color:#64748b; font-size:0.9rem;'>Last 12 trading days</span>", unsafe_allow_html=True)
    
    recent_df = df.tail(12).sort_values('Date', ascending=False).copy()
    
    # Format the dataframe for display
    display_df = pd.DataFrame({
        'DATE': recent_df['Date'].dt.strftime('%Y-%m-%d'),
        'OPEN': recent_df['Open'].apply(lambda x: f"{x:.2f}"),
        'HIGH': recent_df['High'].apply(lambda x: f"{x:.2f}"),
        'LOW': recent_df['Low'].apply(lambda x: f"{x:.2f}"),
        'CLOSE': recent_df['Close'].apply(lambda x: f"{x:.2f}"),
        'CHANGE %': recent_df['Daily_Return_Pct'], 
        'RSI': recent_df['RSI'].apply(lambda x: f"{x:.1f}"),
        'VOLUME': recent_df['Volume'].apply(lambda x: f"{x/100000:.1f} L")
    })

    # Render table with styled change percentages
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "CHANGE %": st.column_config.NumberColumn(
                "CHANGE %",
                format="%+.2f%%",
            )
        }
    )

if __name__ == "__main__":
    main()
