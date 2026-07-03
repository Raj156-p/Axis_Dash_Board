📊 Axis Bank Stock Dashboard
Axis Bank Stock Dashboard is a dynamic, Streamlit-based web application engineered for quantitative market analysis and technical visualization of equities. By leveraging Python's analytical stack and the Yahoo Finance API, this project provides a real-time deep dive into price action, volatility, and momentum indicators to assist in algorithmic trading and financial decision-making.

✅ Features
Dynamic Data Ingestion: Automated fetching and preprocessing of live market data via the yfinance API.

Technical Indicators: Real-time computation of 50-day/200-day SMAs, MACD (12/26 EMA), and 14-period RSI.

Volatility Analysis: Interactive candlestick charting integrated with toggleable Bollinger Bands to visualize price deviations.

Interactive UI: Parameterized controls allowing localized zoom constraints, weekend filtering, and dynamic KPI metric rendering.

🚀 Installation
1. Clone the repository:
Bash
git clone https://github.com/your-username/Axis_Bank_Dashboard.git
cd Axis_Bank_Dashboard
2. Install Python dependencies:
Bash
pip install streamlit pandas numpy yfinance plotly Pillow requests
📈 Core Dashboard Capabilities
Trend Identification: The moving average overlays allow users to instantly visualize long-term versus short-term market trends.

Momentum Shifts: The side-by-side MACD and RSI rendering provides immediate visual cues for overbought or oversold market conditions.

Volume Profiling: Aggregated monthly volume charts expose institutional accumulation or distribution phases.

Data Export: Built-in extraction capabilities to download the computed dataframe (including all generated technical indicators) into a CSV for offline algorithmic modeling.

📂 Repository Structure
DashBoard.py: Main Streamlit application script containing the UI logic and data pipeline.

Axis_logo.png: Local fallback asset for UI branding.

README.md: Project documentation and execution instructions.

🛠️ Requirements
Python 3.8+

Streamlit

Pandas & NumPy

yfinance

Plotly

👤 Creator
Raj Suhagiya — B.Sc. Data Science

📧 rajsuhagya@gmail.com
🔗 linkedin.com/in/raj-suhagiya-bb8921317
🐙 - Raj156-p
