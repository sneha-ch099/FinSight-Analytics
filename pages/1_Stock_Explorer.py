
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta

from common import (
    STOCKS,
    TEXT,
    MUTED,
    TEAL,
    BLUE,
    GREEN,
    ORANGE,
    PURPLE,
    BORDER,
    apply_global_style,
    apply_chart_theme,
    show_brand,
    show_hero,
    show_metric_card,
    show_footer,
    format_currency,
    format_percent,
)

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Stock Explorer | FinSight Analytics",
    page_icon="📊",
    layout="wide",
)

apply_global_style()
show_brand()

show_hero(
    eyebrow="INDIVIDUAL STOCK ANALYSIS",
    title="Explore every move.",
    highlighted_title="Understand every signal.",
    description=(
        "Study individual Indian equities through interactive price charts, "
        "trading volume and technical indicators."
    ),
    chip="CANDLESTICKS  •  TECHNICAL ANALYSIS  •  PRICE HISTORY",
)

# =========================================================
# DATA DOWNLOAD
# =========================================================

@st.cache_data(ttl=600, show_spinner=False)
def load_stock_history(ticker, start, end):
    data = yf.download(
        ticker,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=False,
        timeout=25,
    )

    if data is None or data.empty:
        return pd.DataFrame()

    # Handle yfinance MultiIndex columns
    if isinstance(data.columns, pd.MultiIndex):
        if ticker in data.columns.get_level_values(-1):
            data = data.xs(ticker, axis=1, level=-1)
        elif ticker in data.columns.get_level_values(0):
            data = data.xs(ticker, axis=1, level=0)
        else:
            data.columns = data.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close", "Volume"]

    if not all(column in data.columns for column in required):
        return pd.DataFrame()

    data = data[required].copy()
    data = data.apply(pd.to_numeric, errors="coerce")
    data = data.dropna(subset=["Open", "High", "Low", "Close"])

    if data.empty:
        return data

    # Moving averages
    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()

    # RSI (14-day)
    change = data["Close"].diff()
    gain = change.clip(lower=0)
    loss = -change.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / 14,
        min_periods=14,
        adjust=False,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / 14,
        min_periods=14,
        adjust=False,
    ).mean()

    relative_strength = avg_gain / avg_loss.replace(0, np.nan)
    data["RSI"] = 100 - (100 / (1 + relative_strength))

    # MACD
    ema12 = data["Close"].ewm(span=12, adjust=False).mean()
    ema26 = data["Close"].ewm(span=26, adjust=False).mean()

    data["MACD"] = ema12 - ema26
    data["Signal"] = data["MACD"].ewm(
        span=9,
        adjust=False,
    ).mean()

    data["MACD_Hist"] = data["MACD"] - data["Signal"]

    return data


# =========================================================
# SIDEBAR CONTROLS
# =========================================================

st.sidebar.markdown("## Stock Explorer")
st.sidebar.caption("Choose a company and analysis period.")

selected_stock = st.sidebar.selectbox(
    "Select company",
    list(STOCKS.keys()),
    index=0,
)


period = st.sidebar.selectbox(
    "Historical period",
    ["1M", "3M", "6M", "1Y", "2Y", "5Y", "Custom Date Range"],
    index=3,
)

end_date = date.today()

if period == "Custom Date Range":

    st.sidebar.markdown("### Select your dates")

    start_date = st.sidebar.date_input(
        "Start date",
        value=end_date - timedelta(days=365),
        min_value=date(2000, 1, 1),
        max_value=end_date,
        key="explorer_start_date",
    )

    end_date = st.sidebar.date_input(
        "End date",
        value=date.today(),
        min_value=date(2000, 1, 1),
        max_value=date.today(),
        key="explorer_end_date",
    )

    if start_date >= end_date:
        st.sidebar.error("End date must be after start date.")
        st.stop()

else:

    period_days = {
        "1M": 30,
        "3M": 90,
        "6M": 182,
        "1Y": 365,
        "2Y": 730,
        "5Y": 1825,
    }

    start_date = end_date - timedelta(days=period_days[period])

st.sidebar.markdown("---")
st.sidebar.markdown("### Chart settings")

show_ma20 = st.sidebar.checkbox("20-day moving average", True)
show_ma50 = st.sidebar.checkbox("50-day moving average", True)
show_ma200 = st.sidebar.checkbox("200-day moving average", True)

show_volume = st.sidebar.checkbox("Trading volume", True)

if st.sidebar.button("↻ Refresh stock data", use_container_width=True):
    load_stock_history.clear()
    st.rerun()

# =========================================================
# LOAD SELECTED STOCK
# =========================================================

ticker = STOCKS[selected_stock]

try:
    with st.spinner(f"Loading {selected_stock} historical data..."):
        data = load_stock_history(
            ticker,
            start_date.isoformat(),
            (end_date + timedelta(days=1)).isoformat(),
        )

except Exception as error:
    st.error(f"Unable to retrieve stock data: {error}")
    st.stop()

if data.empty or len(data) < 2:
    st.error(
        "Historical data is unavailable or insufficient for this company. "
        "Please try another stock or period."
    )
    st.stop()

# =========================================================
# STOCK INFORMATION
# =========================================================

latest = data.iloc[-1]
previous = data.iloc[-2]

latest_price = float(latest["Close"])
previous_price = float(previous["Close"])

price_change = latest_price - previous_price
change_pct = (
    price_change / previous_price * 100
    if previous_price else np.nan
)

first_price = float(data["Close"].iloc[0])
total_return = (
    (latest_price / first_price) - 1
    if first_price else np.nan
)

high_price = float(data["High"].max())
low_price = float(data["Low"].min())

st.markdown(
    f"""
    <div style="margin: 12px 0 20px">
        <div style="font-size:12px;color:{MUTED}">
            NSE : {ticker} &nbsp; | &nbsp;
            Historical period: {start_date} to {end_date} &nbsp; | &nbsp;
            Latest observation: {data.index[-1].date()}
        </div>
        <h2 style="margin:7px 0 0;color:{TEXT}">
            {selected_stock}
        </h2>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# KEY STOCK METRICS
# =========================================================

st.markdown(
    '<div class="section-heading">Stock snapshot</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4, gap="medium")

with k1:
    show_metric_card(
        "LATEST CLOSE",
        format_currency(latest_price),
        f"{price_change:+.2f} ({change_pct:+.2f}%)",
        GREEN if price_change >= 0 else "#FF667D",
    )

with k2:
    show_metric_card(
        "PERIOD RETURN",
        format_percent(total_return),
        f"Based on {period} selected history",
        TEAL if total_return >= 0 else "#FF667D",
    )

with k3:
    show_metric_card(
        "PERIOD HIGH",
        format_currency(high_price),
        "Highest daily high",
        GREEN,
    )

with k4:
    show_metric_card(
        "PERIOD LOW",
        format_currency(low_price),
        "Lowest daily low",
        ORANGE,
    )

# =========================================================
# CANDLESTICK CHART
# =========================================================

st.markdown(
    '<div class="section-heading">Price action</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-sub">Daily candlesticks and selected moving averages.</div>',
    unsafe_allow_html=True,
)

fig = make_subplots(
    rows=2 if show_volume else 1,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.07,
    row_heights=[0.75, 0.25] if show_volume else [1],
)

fig.add_trace(
    go.Candlestick(
        x=data.index,
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name="Price",
        increasing_line_color=GREEN,
        decreasing_line_color="#FF667D",
    ),
    row=1,
    col=1,
)

if show_ma20:
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA20"],
            name="MA 20",
            line=dict(color=TEAL, width=1.5),
        ),
        row=1,
        col=1,
    )

if show_ma50:
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA50"],
            name="MA 50",
            line=dict(color=ORANGE, width=1.5),
        ),
        row=1,
        col=1,
    )

if show_ma200:
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA200"],
            name="MA 200",
            line=dict(color=PURPLE, width=1.5),
        ),
        row=1,
        col=1,
    )

if show_volume:
    volume_colors = [
        GREEN if close >= open_price else "#FF667D"
        for close, open_price in zip(data["Close"], data["Open"])
    ]

    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data["Volume"],
            name="Volume",
            marker_color=volume_colors,
            opacity=0.65,
        ),
        row=2,
        col=1,
    )

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT, size=11),
    height=620 if show_volume else 470,
    margin=dict(l=25, r=25, t=70, b=25),
    hovermode="x unified",
    xaxis_rangeslider_visible=False,
    legend=dict(
        orientation="h",
        y=1.08,
        x=0,
        title_text="",
    ),
)

fig.update_xaxes(
    showgrid=True,
    gridcolor="rgba(145,169,190,.10)",
)

fig.update_yaxes(
    showgrid=True,
    gridcolor="rgba(145,169,190,.10)",
    title_text="Price (₹)",
    row=1,
    col=1,
)

if show_volume:
    fig.update_yaxes(
        title_text="Volume",
        row=2,
        col=1,
    )

st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TECHNICAL INDICATORS
# =========================================================

st.markdown(
    '<div class="section-heading">Technical indicators</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-sub">Momentum and trend analysis using RSI and MACD.</div>',
    unsafe_allow_html=True,
)

left, right = st.columns(2, gap="large")

# RSI
with left:
    rsi_fig = go.Figure()

    rsi_fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["RSI"],
            name="RSI",
            line=dict(color=TEAL, width=2),
        )
    )

    rsi_fig.add_hline(
        y=70,
        line_dash="dash",
        line_color="#FF667D",
        annotation_text="Overbought (70)",
    )

    rsi_fig.add_hline(
        y=30,
        line_dash="dash",
        line_color=GREEN,
        annotation_text="Oversold (30)",
    )

    rsi_fig.update_yaxes(range=[0, 100])

    st.plotly_chart(
        apply_chart_theme(
            rsi_fig,
            height=330,
            y_title="RSI",
            title="Relative Strength Index (14)",
        ),
        use_container_width=True,
    )

# MACD
with right:
    macd_fig = go.Figure()

    macd_fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MACD"],
            name="MACD",
            line=dict(color=BLUE, width=2),
        )
    )

    macd_fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Signal"],
            name="Signal",
            line=dict(color=ORANGE, width=2),
        )
    )

    macd_fig.add_trace(
        go.Bar(
            x=data.index,
            y=data["MACD_Hist"],
            name="Histogram",
            marker_color=TEAL,
            opacity=0.4,
        )
    )

    macd_fig.add_hline(y=0, line_dash="dot")

    st.plotly_chart(
        apply_chart_theme(
            macd_fig,
            height=330,
            y_title="MACD value",
            title="MACD (12, 26, 9)",
        ),
        use_container_width=True,
    )

# =========================================================
# TECHNICAL INTERPRETATION
# =========================================================

latest_rsi = data["RSI"].dropna().iloc[-1]
latest_macd = latest["MACD"]
latest_signal = latest["Signal"]

st.markdown(
    '<div class="section-heading">Technical interpretation</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    if latest_rsi >= 70:
        rsi_status = "Potentially overbought"
        rsi_description = "RSI is above 70, indicating strong recent upward momentum."
    elif latest_rsi <= 30:
        rsi_status = "Potentially oversold"
        rsi_description = "RSI is below 30, indicating weak recent downward momentum."
    else:
        rsi_status = "Neutral RSI range"
        rsi_description = "RSI is between 30 and 70."

    st.info(
        f"**RSI: {latest_rsi:.2f} — {rsi_status}**\n\n"
        f"{rsi_description}"
    )

with col2:
    if latest_macd > latest_signal:
        macd_status = "MACD above signal line"
        macd_description = "Recent momentum is positive relative to the signal line."
    else:
        macd_status = "MACD below signal line"
        macd_description = "Recent momentum is negative relative to the signal line."

    st.info(
        f"**{macd_status}**\n\n"
        f"{macd_description}"
    )

# =========================================================
# HISTORICAL DATA TABLE
# =========================================================

with st.expander("View historical price data"):
    display_data = data.reset_index()

    if "Date" not in display_data.columns:
        display_data = display_data.rename(
            columns={display_data.columns[0]: "Date"}
        )

    st.dataframe(
        display_data.sort_values("Date", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "↓ Download historical data CSV",
        data=display_data.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_stock.replace(' ', '_')}_history.csv",
        mime="text/csv",
    )

# =========================================================
# FOOTER
# =========================================================

st.caption(
    "Technical indicators are historical analytical tools, "
    "not guaranteed trading signals. This page is for educational purposes "
    "and does not provide investment advice."
)

show_footer()
