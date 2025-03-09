import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go

# Title for the Streamlit app
st.title('Relative Rotation Graph')

# Mapping tickers to sector names
tickers_names = {
    "XLC": "CSRV",
    "XLY": "CD",
    "XLP": "CS",
    "XLE": "EN",
    "XLF": "FN",
    "XLV": "HC",
    "XLI": "IN",
    "XLB": "MT",
    "XLRE": "RE",
    "XLK": "IT",
    "XLU": "UT",
}

# Define a color palette
colors = [
    'blue', 'orange', 'green', 'red', 'purple', 
    'brown', 'pink', 'gray', 'olive', 'cyan', 'magenta'
]

# Function to fetch historical data
def fetch_hist_data(ticker):
    return yf.download(ticker, period='max')['Adj Close']

# DataFrame to store adjusted close prices
aprc = pd.DataFrame()

# Progress bar initialization
st.write('Extracting price data for US Sector ETFs')
progress_text = 'Extracting price data for US Sector ETFs'
my_bar = st.progress(0, text=progress_text)

# Fetching data for each sector ETF
count = 0
for k, v in tickers_names.items():
    aprc[v] = fetch_hist_data(ticker=k)
    count += 1
    my_bar.progress(count / len(tickers_names))

st.write('Price extraction done...')

st.write('Calculating Relative Strength ratios and momentum for RRG plot...')

# Fetching data for S&P 500
sp500 = yf.download('SPY', period='max')['Adj Close']
sp500.name = 'SP500'

# Joining S&P 500 data with sector ETFs data
aprc = aprc.join(sp500)

# Calculating Relative Strength (RS) and standardizing it
rs = aprc.div(aprc['SP500'], axis=0).mul(100)
rs = (rs - rs.mean()) / rs.std()
rs = rs.replace(np.nan, 0)

# Calculating momentum (3 months rolling return and 1 month rolling return)
mom_raw = aprc.div(sp500, axis=0).mul(100).dropna()
mom3 = mom_raw.pct_change(periods=63)
mom1 = mom_raw.pct_change(periods=21)
mom = np.log(1 + mom3) - np.log(1 + mom1)
mom = mom.replace(np.nan, 0)

# Standardizing momentum
rs_mom = (mom - mom.mean()) / mom.std()
rs_mom = rs_mom.replace(np.nan, 0)

# Slider to select lookback period
lookback_period_selection = st.select_slider(
    'Select a lookback tail period',
    ['LTD*', '3D', '7D', '14D', '21D', '50D', 'MAX**'],
    value='7D'
)

if lookback_period_selection == 'LTD*':
    lookback_period = -1
elif lookback_period_selection == '3D':
    lookback_period = -3
elif lookback_period_selection == '7D':
    lookback_period = -7
elif lookback_period_selection == '14D':
    lookback_period = -14
elif lookback_period_selection == '21D':
    lookback_period = -21
elif lookback_period_selection == '50D':
    lookback_period = -50
elif lookback_period_selection == 'MAX**':
    lookback_period = 0

st.write(r'\* LTD: Last Trading Day')
st.write(r'\** max shows entire history since 2018')

# Create the Plotly figure
fig = go.Figure()

fig.add_shape(type="rect", x0=0, y0=0, x1=3.2, y1=2.2, fillcolor="lightgreen", opacity=0.3, layer="below", line_width=0)
fig.add_shape(type="rect", x0=-3.2, y0=0, x1=0, y1=2.2, fillcolor="lightblue", opacity=0.3, layer="below", line_width=0)
fig.add_shape(type="rect", x0=-3.2, y0=-2.2, x1=0, y1=0, fillcolor="#FFCCCB", opacity=0.3, layer="below", line_width=0)
fig.add_shape(type="rect", x0=0, y0=-2.2, x1=3.2, y1=0, fillcolor="lightyellow", opacity=0.3, layer="below", line_width=0)


# Add scatter and line plots with different colors for each sector
for i, (etf_names, etf) in enumerate(tickers_names.items()):
    fig.add_trace(go.Scatter(
        x=[rs[etf].iloc[-1]],
        y=[rs_mom[etf].iloc[-1]],
        mode='markers',
        name=f'{etf}: {etf_names}',
        marker=dict(color=colors[i], size=10)
    ))
    fig.add_trace(go.Scatter(
        x=rs[etf].iloc[lookback_period:].values,
        y=rs_mom[etf].iloc[lookback_period:].values,
        mode='lines',
        name=f'{etf}: {etf_names}',
        line=dict(color=colors[i], width=1),
        showlegend=False
    ))

# Add quadrants and annotations
fig.add_shape(type="line", x0=0, y0=-2.2, x1=0, y1=2.2, line=dict(color='rgba(200, 200, 200, 1)', width=3))
fig.add_shape(type="line", x0=-3.2, y0=0, x1=3.2, y1=0, line=dict(color='rgba(200, 200, 200, 1)', width=3))
fig.add_annotation(x=1.5, y=1.5, text='Leading'.upper(), showarrow=False)
fig.add_annotation(x=1.5, y=-1.5, text='Weakening'.upper(), showarrow=False)
fig.add_annotation(x=-1.5, y=-1.5, text='Lagging'.upper(), showarrow=False)
fig.add_annotation(x=-1.5, y=1.5, text='Improving'.upper(), showarrow=False)

# Update layout
fig.update_layout(
    autosize=False,
    width=1600,
    height=800,
    title='Relative Rotation Graph'.upper(),
    xaxis_title='Relative Strength'.upper(),
    yaxis_title='Rate of Change (ROC) - Momentum'.upper(),
    xaxis=dict(showgrid=True, gridcolor='rgba(200, 200, 200, 0.5)'),
    yaxis=dict(showgrid=True, gridcolor='rgba(200, 200, 200, 0.5)'),
    legend=dict(orientation='h', yanchor='bottom', y=-0.5, xanchor='center', x=0.5)
)

# Display the plot in the Streamlit app
st.plotly_chart(fig)

# Description of the plot
st.write("""
**Description:**
The Relative Rotation Graph (RRG) visualizes the performance of various sectors relative to the S&P 500. 
Each point represents a sector's relative strength and momentum, helping identify leading, lagging, 
improving, and weakening sectors over time.
\n
Legends: \n 
CSRV: Communication Services, \n
CD: Consumer Discretionary, \n
CS: Consumer Staples, \n
EN: Energy, \n
FN: Financials, \n
HC: Health Care, \n
IN: Industrials, \n
MT: Materials, \n
RE: Real Estate, \n
IT: Information Technology, \n
UT: Utilities \n
""")

st.write("""
         """)

st.write('\n \n \n')
# Disclaimer
st.write("""
**Disclaimer:**
This is not investment advice. The information provided is for educational purposes only and 
should not be considered as financial or investment advice. Please conduct your own research 
or consult a financial advisor before making any investment decisions.
""")
st.write('\n \n \n')
# Copyright notice
st.write("""
**Copyright Notice:**
All calculations and code are © प्रtiक.
""")
