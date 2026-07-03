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
    """Create a seeded random number generator"""
    random.seed(seed)
    def random_func():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        return seed / 0x7fffffff
    return random_func


# Generate simulated stock data
def generate_bars(symbol: str, start_date: datetime, end_date: datetime, max_bars: int = 950) -> pd.DataFrame:
    """Generate simulated stock price data with realistic movements"""
    seed = sum(ord(c) for c in symbol) + int(start_date.timestamp())
    rng = seeded_random(seed)
    
    # Base price by symbol
    base_prices = {"AXISBANK.NS": 800, "RELIANCE.NS": 2500, "TCS.NS": 3500, "INFY.NS": 1500}
    base_price = base_prices.get(symbol, 100)
    
    price = base_price * (0.8 + rng() * 0.4)
    volatility = 0.02 + rng() * 0.01
    
    data = []
    current = start_date
    bar_count = 0
    
    while current <= end_date and bar_count < max_bars:
        # Skip weekends
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
    """Add technical indicators to the dataframe"""
    df = df.copy()
    
    # Calculate SMA
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    
    # Calculate EMA
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    
    # Calculate MACD
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Signal']
    
    # Calculate RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    # Calculate 52-week high/low
    df['High_52W'] = df['High'].rolling(window=252).max()
    df['Low_52W'] = df['Low'].rolling(window=252).min()
    
    # Daily return percentage
    df['Daily_Return'] = df['Close'].pct_change() * 100
    
    return df


def monthly_volume(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate volume by month"""
    df = df.copy()
    df['Month'] = df['Date'].dt.to_period('M')
    monthly = df.groupby('Month')['Volume'].sum().reset_index()
    monthly['Month'] = monthly['Month'].astype(str)
    return monthly


def format_inr(value: float) -> str:
    """Format as Indian Rupee"""
    return f"₹{value:,.2f}"


def format_compact(value: int) -> str:
    """Format large numbers compactly"""
    if value >= 10000000:
        return f"{value/10000000:.1f} Cr"
    elif value >= 100000:
        return f"{value/100000:.1f} L"
    elif value >= 1000:
        return f"{value/1000:.1f} K"
    return str(value)


# Main application
def main():
    # Header
    st.markdown('<p class="main-header">Axis Bank Stock Dashboard</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Controls")
        
        # Logo and title
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 2rem;">
            <div style="background: #97144D; color: white; width: 44px; height: 44px; border-radius: 12px; 
                        display: flex; align-items: center; justify-content: center; font-size: 1.5rem;">
                🏦
            </div>
            <div>
                <div style="font-weight: 700; color: #1e293b; font-size: 0.875rem;">Axis Bank</div>
                <div style="color: #94a3b8; font-size: 0.75rem;">Stock Analyzer</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Stock symbol input
        symbol = st.text_input("Stock Symbol", value="AXISBANK.NS")
        
        # Date range inputs
        today = datetime.today()
        start_date = st.date_input("Start Date", value=datetime(2023, 1, 1))
        end_date = st.date_input("End Date", value=today)
        
        # Bollinger bands toggle
        show_bollinger = st.checkbox("Show Bollinger Bands", value=True)
        
        # Generate button
        if st.button("🔍 Analyze", use_container_width=True):
            st.session_state['analyze'] = True
        
        if st.button("🔄 Regenerate Scenario", use_container_width=True):
            st.session_state['nonce'] = st.session_state.get('nonce', 0) + 1
        
        # Download CSV button
        if st.session_state.get('df') is not None:
            csv = st.session_state['df'].to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                f"{symbol}_data.csv",
                use_container_width=True
            )
        
        # Disclaimer
        st.markdown("""
        <div style="margin-top: 1.5rem; padding: 0.75rem; background: #f8fafc; 
                    border-radius: 8px; font-size: 0.7rem; color: #94a3b8; line-height: 1.5;">
            <strong>Disclaimer:</strong> Data shown is a simulated market scenario for 
            demonstration purposes only. Not real market data.
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'analyze' not in st.session_state:
        st.session_state['analyze'] = True
    if 'df' not in st.session_state:
        st.session_state['df'] = None
    
    # Generate data
    if st.session_state['analyze'] or st.session_state.get('df') is None:
        if start_date and end_date and start_date < end_date:
            with st.spinner("Generating market data..."):
                df = generate_bars(symbol, datetime.combine(start_date, datetime.min.time()), 
                                   datetime.combine(end_date, datetime.min.time()))
                st.session_state['df'] = df
                st.session_state['symbol'] = symbol
        else:
            st.error("Please select a valid date range (start date must be before end date)")
            return
    
    df = st.session_state['df']
    
    if df is None or len(df) == 0:
        st.warning("No data available. Please adjust your date range and click Analyze.")
        return
    
    # Display info
    st.markdown(f"""
    <p class="sub-header">
        {st.session_state.get('symbol', symbol)} &middot; {start_date} to {end_date} &middot; {len(df)} trading days
    </p>
    """, unsafe_allow_html=True)
    
    # KPI Cards
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2] if len(df) > 1 else last_row
    day_change = last_row['Close'] - prev_row['Close']
    day_change_pct = (day_change / prev_row['Close']) * 100
    
    # Calculate averages for 52W
    h52_valid = df[df['High_52W'].notna()]['High_52W']
    l52_valid = df[df['Low_52W'].notna()]['Low_52W']
    avg_high = h52_valid.mean() if len(h52_valid) > 0 else last_row['High']
    avg_low = l52_valid.mean() if len(l52_valid) > 0 else last_row['Low']
    total_vol = df['Volume'].sum()
    latest_rsi = last_row['RSI'] if pd.notna(last_row['RSI']) else 50
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Latest Close",
            value=format_inr(last_row['Close']),
            delta=f"{day_change_pct:+.2f}%"
        )
    
    with col2:
        st.metric(label="Avg 52W High", value=format_inr(avg_high))
    
    with col3:
        st.metric(label="Avg 52W Low", value=format_inr(avg_low))
    
    with col4:
        st.metric(label="Total Volume", value=format_compact(int(total_vol)))
    
    with col5:
        rsi_status = "Overbought" if latest_rsi > 70 else "Oversold" if latest_rsi < 30 else "Neutral"
        st.metric(label="Latest RSI", value=f"{latest_rsi:.2f}", delta=rsi_status)
    
    st.divider()
    
    # Price Chart with Moving Averages
    st.subheader("📈 Price with Moving Averages")
    
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(
        x=df['Date'], y=df['Close'],
        mode='lines', name='Close',
        line=dict(color='#97144D', width=2)
    ))
    fig_price.add_trace(go.Scatter(
        x=df['Date'], y=df['SMA_50'],
        mode='lines', name='SMA 50',
        line=dict(color='#2563eb', width=1.5)
    ))
    fig_price.add_trace(go.Scatter(
        x=df['Date'], y=df['SMA_200'],
        mode='lines', name='SMA 200',
        line=dict(color='#f59e0b', width=1.5)
    ))
    fig_price.update_layout(
        height=400,
        template='plotly_white',
        xaxis_title='',
        yaxis_title='Price (₹)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    st.plotly_chart(fig_price, use_container_width=True)
    
    # Candlestick Chart
    st.subheader("🕯️ Candlestick with Bollinger Bands")
    
    fig_candle = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=('', 'Volume')
    )
    
    # Candlestick
    fig_candle.add_trace(
        go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='OHLC',
            increasing_line_color='#16a34a',
            decreasing_line_color='#dc2626',
            increasing_fillcolor='#bbf7d0',
            decreasing_fillcolor='#fecaca'
        ),
        row=1, col=1
    )
    
    # Bollinger Bands
    if show_bollinger:
        fig_candle.add_trace(
            go.Scatter(x=df['Date'], y=df['BB_Upper'], name='BB Upper',
                      line=dict(color='#9333ea', width=1, dash='dash'), opacity=0.7),
            row=1, col=1
        )
        fig_candle.add_trace(
            go.Scatter(x=df['Date'], y=df['BB_Middle'], name='BB Middle',
                      line=dict(color='#9333ea', width=1), opacity=0.7),
            row=1, col=1
        )
        fig_candle.add_trace(
            go.Scatter(x=df['Date'], y=df['BB_Lower'], name='BB Lower',
                      line=dict(color='#9333ea', width=1, dash='dash'), opacity=0.7),
            row=1, col=1
        )
    
    # Volume bars
    colors = ['#16a34a' if df.iloc[i]['Close'] >= df.iloc[i]['Open'] else '#dc2626' 
              for i in range(len(df))]
    fig_candle.add_trace(
        go.Bar(x=df['Date'], y=df['Volume'], name='Volume', marker_color=colors, opacity=0.7),
        row=2, col=1
    )
    
    fig_candle.update_layout(
        height=500,
        template='plotly_white',
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='right', x=1),
        xaxis_rangeslider_visible=False,
        margin=dict(l=40, r=40, t=60, b=40)
    )
    fig_candle.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig_candle.update_yaxes(title_text="Volume", row=2, col=1)
    
    st.plotly_chart(fig_candle, use_container_width=True)
    
    # MACD and RSI side by side
    col_macd, col_rsi = st.columns(2)
    
    with col_macd:
        st.subheader("📊 MACD Indicator")
        
        macd_df = df[df['MACD'].notna()].copy()
        
        fig_macd = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.4],
            subplot_titles=('', '')
        )
        
        # Histogram
        colors = ['#16a34a' if h >= 0 else '#dc2626' for h in macd_df['Histogram']]
        fig_macd.add_trace(
            go.Bar(x=macd_df['Date'], y=macd_df['Histogram'], 
                   marker_color=colors, name='Histogram'),
            row=2, col=1
        )
        
        # MACD and Signal lines
        fig_macd.add_trace(
            go.Scatter(x=macd_df['Date'], y=macd_df['MACD'], 
                      name='MACD', line=dict(color='#97144D', width=1.5)),
            row=1, col=1
        )
        fig_macd.add_trace(
            go.Scatter(x=macd_df['Date'], y=macd_df['Signal'], 
                      name='Signal', line=dict(color='#f59e0b', width=1.5)),
            row=1, col=1
        )
        
        # Reference line at 0
        fig_macd.add_hline(y=0, line_dash="solid", line_color="#cbd5e1", row=2, col=1)
        
        fig_macd.update_layout(
            height=300,
            template='plotly_white',
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=40, r=40, t=20, b=40)
        )
        fig_macd.update_yaxes(title_text="MACD", row=1, col=1)
        fig_macd.update_yaxes(title_text="Histogram", row=2, col=1)
        
        st.plotly_chart(fig_macd, use_container_width=True)
    
    with col_rsi:
        st.subheader("📉 Relative Strength Index (RSI)")
        
        rsi_df = df[df['RSI'].notna()].copy()
        
        fig_rsi = go.Figure()
        
        fig_rsi.add_trace(go.Scatter(
            x=rsi_df['Date'], y=rsi_df['RSI'],
            mode='lines', name='RSI',
            line=dict(color='#7c3aed', width=2)
        ))
        
        # Overbought line at 70
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="#dc2626", 
                         annotation_text="70", annotation_position="right")
        # Oversold line at 30
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="#16a34a",
                         annotation_text="30", annotation_position="right")
        
        # Fill areas
        fig_rsi.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, line_width=0)
        fig_rsi.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, line_width=0)
        
        fig_rsi.update_layout(
            height=300,
            template='plotly_white',
            showlegend=False,
            yaxis=dict(range=[0, 100]),
            margin=dict(l=40, r=40, t=20, b=40)
        )
        fig_rsi.update_yaxes(title_text="RSI")
        
        st.plotly_chart(fig_rsi, use_container_width=True)
    
    # Monthly Volume
    st.subheader("📊 Monthly Trading Volume")
    
    monthly_df = monthly_volume(df)
    
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Bar(
        y=monthly_df['Volume'],
        x=monthly_df['Month'],
        name='Volume',
        marker_color='#97144D',
        markercornerradius=4
    ))
    fig_vol.update_layout(
        height=350,
        template='plotly_white',
        xaxis_title='',
        yaxis_title='Volume',
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=60)
    )
    st.plotly_chart(fig_vol, use_container_width=True)
    
    # Recent Data Table
    st.subheader("📋 Recent Data")
    
    recent_df = df.tail(12).iloc[::-1].copy()
    display_df = recent_df[['Date', 'Open', 'High', 'Low', 'Close', 'Daily_Return', 'RSI', 'Volume']].copy()
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
    display_df['Open'] = display_df['Open'].apply(lambda x: f"₹{x:.2f}")
    display_df['High'] = display_df['High'].apply(lambda x: f"₹{x:.2f}")
    display_df['Low'] = display_df['Low'].apply(lambda x: f"₹{x:.2f}")
    display_df['Close'] = display_df['Close'].apply(lambda x: f"₹{x:.2f}")
    display_df['Daily_Return'] = display_df['Daily_Return'].apply(
        lambda x: f"<span style='color: {'#16a34a' if x >= 0 else '#dc2626'}'>{x:+.2f}%</span>" if pd.notna(x) else "-"
    )
    display_df['RSI'] = display_df['RSI'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    display_df['Volume'] = display_df['Volume'].apply(lambda x: format_compact(int(x)))
    display_df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Change %', 'RSI', 'Volume']
    
    st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
