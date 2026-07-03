📈 Axis Bank Stock Dashboard
A robust, Streamlit-based web application engineered for quantitative market analysis and technical visualization of equities. While optimized for Axis Bank (AXISBANK.NS), the architecture supports dynamic symbol ingestion via the Yahoo Finance API.

Live Application: Axis Bank Stock Dashboard

⚡ Core Features
📊 Advanced Visualization: High-fidelity candlestick charting integrated with toggleable Bollinger Bands for volatility analysis. Features automatic weekend filtering and localized zoom constraints to prevent visual clustering.

📉 Technical Overlays:

Moving Averages: 50-day and 200-day Simple Moving Averages (SMA) for trend identification.

Momentum Oscillators: 14-period Relative Strength Index (RSI) with dynamic overbought/oversold threshold indicators.

Trend Following: MACD indicator (12/26 EMA) complete with a 9-period signal line and histogram.

🧮 Real-Time KPI Tracking: Dynamic metric cards calculating day-over-day percentage changes, 52-week rolling highs/lows, and aggregate volume constraints.

📥 Data Pipeline Extraction: One-click CSV export functionality, allowing analysts to download the computed dataset (including all derived technical indicators) for external modeling.

🛠️ Technology Stack
Frontend framework: Streamlit

Data Ingestion: yfinance

Data Manipulation: pandas, numpy

Data Visualization: plotly.graph_objects

🚀 Local Installation & Execution
1. Clone the repository and navigate to the directory

Bash
git clone <repository_url>
cd <repository_directory>
2. Establish a virtual environment (Recommended)

Bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
3. Install dependencies

Bash
pip install -r requirements.txt
(Ensure your requirements.txt includes: streamlit, pandas, numpy, yfinance, plotly, requests, Pillow)

4. Execute the application

Bash
streamlit run DashBoard.py
⚠️ Data Architecture Note
The dashboard relies on the yfinance library, which scrapes Yahoo Finance. Be aware that excessive, rapid calls may result in temporary IP-based rate limiting by Yahoo. The application calculates all technical indicators locally in pandas rather than relying on external indicator APIs, ensuring execution speed and data consistency.
