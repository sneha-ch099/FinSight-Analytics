
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta

from common import (
    STOCKS,
    TEAL,
    BLUE,
    GREEN,
    ORANGE,
    PURPLE,
    RED,
    MUTED,
    TEXT,
    RISK_FREE_RATE,
    TRADING_DAYS,
    get_stock_prices,
    date_range_from_period,
    prepare_stock_data,
    get_analysis_metrics,
    make_metrics_table,
    format_percent,
    format_number,
    apply_chart_theme,
    apply_global_style,
    show_brand,
    show_hero,
    show_metric_card,
    show_footer,
)

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Performance & Risk | FinSight Analytics",
    page_icon="📊",
    layout="wide"
)

apply_global_style()

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("Performance & Risk")
st.sidebar.caption("Explore historical returns and investment risk.")

stock_names = list(STOCKS.keys())

selected_stocks = st.sidebar.multiselect(
    "Select stocks",
    options=stock_names,
    default=stock_names[:4]
)


period = st.sidebar.selectbox(
    "Analysis period",
    ["1M", "3M", "6M", "1Y", "3Y", "5Y", "Custom Date Range"],
    index=3
)

if period == "Custom Date Range":

    st.sidebar.markdown("### Select your dates")

    start_date = st.sidebar.date_input(
        "Start date",
        value=date.today() - timedelta(days=365),
        min_value=date(2000, 1, 1),
        max_value=date.today(),
        key="risk_start_date"
    )

    end_date = st.sidebar.date_input(
        "End date",
        value=date.today(),
        min_value=date(2000, 1, 1),
        max_value=date.today(),
        key="risk_end_date"
    )

    if start_date >= end_date:
        st.sidebar.error("End date must be after start date.")
        st.stop()


st.sidebar.markdown("---")
st.sidebar.caption("Risk-free rate: 6.5% annually")

# --------------------------------------------------
# BRAND AND HERO
# --------------------------------------------------

show_brand()

show_hero(
    eyebrow="ANALYTICS / PERFORMANCE & RISK",
    title="Measure Performance.",
    highlighted_title="Understand Risk.",
    description=(
        "Evaluate historical stock returns, compare investment "
        "performance and understand the level of risk associated "
        "with each selected stock."
    ),
    chip="RETURNS  •  VOLATILITY  •  RISK-ADJUSTED PERFORMANCE"
)

# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

if not selected_stocks:
    st.warning("Please select at least one stock from the sidebar.")
    st.stop()

# --------------------------------------------------
# LOAD STOCK DATA
# --------------------------------------------------


if period != "Custom Date Range":
    start_date, end_date = date_range_from_period(period)


stock_items = {
    name: STOCKS[name]
    for name in selected_stocks
}

try:
    with st.spinner("Downloading historical stock prices..."):

        raw_prices = get_stock_prices(
            stock_items,
            start_date,
            end_date + timedelta(days=1)
        )

        prices = prepare_stock_data(raw_prices)

        prices = prices.dropna(axis=1, how="all")

        if prices.empty or len(prices) < 2:
            st.error("Insufficient historical stock data.")
            st.stop()

        # Keep only stocks with available data
        available_stocks = [
            name for name in selected_stocks
            if name in prices.columns
        ]

        prices = prices[available_stocks]

        if prices.empty:
            st.error("No selected stocks have available data.")
            st.stop()

        metrics = get_analysis_metrics(prices)

        metrics = metrics.loc[
            metrics.index.intersection(prices.columns)
        ]

except Exception as e:
    st.error(f"Unable to load stock data: {e}")
    st.stop()

if metrics.empty:
    st.error("Unable to calculate performance metrics.")
    st.stop()

returns = prices.pct_change(fill_method=None)

# --------------------------------------------------
# CALCULATE ADDITIONAL RISK METRICS
# --------------------------------------------------

drawdowns = (
    (1 + returns).cumprod()
    / (1 + returns).cumprod().cummax()
    - 1
)

max_drawdowns = drawdowns.min()

rolling_volatility = (
    returns.rolling(window=21).std()
    * np.sqrt(TRADING_DAYS)
)

# --------------------------------------------------
# PAGE INFORMATION
# --------------------------------------------------

st.caption(
    f"Analysis period: {start_date:%d %b %Y} – "
    f"{end_date:%d %b %Y}  |  "
    f"Stocks analysed: {len(metrics)}"
)

# --------------------------------------------------
# SECTION 1: PERFORMANCE OVERVIEW
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">01 / Performance Overview</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Key indicators showing the performance and risk of your selected stocks.'
    '</div>',
    unsafe_allow_html=True
)

total_stocks = len(metrics)

best_return_stock = metrics["Cumulative Return"].idxmax()
best_return = metrics["Cumulative Return"].max()

best_sharpe_stock = metrics["Sharpe Ratio"].idxmax()
best_sharpe = metrics["Sharpe Ratio"].max()

highest_risk_stock = metrics["Annualized Volatility"].idxmax()
highest_risk = metrics["Annualized Volatility"].max()

average_return = metrics["Cumulative Return"].mean()
average_volatility = metrics["Annualized Volatility"].mean()

c1, c2, c3, c4 = st.columns(4)

with c1:
    show_metric_card(
        "BEST CUMULATIVE RETURN",
        format_percent(best_return),
        best_return_stock,
        GREEN
    )

with c2:
    show_metric_card(
        "BEST SHARPE RATIO",
        format_number(best_sharpe),
        best_sharpe_stock,
        TEAL
    )

with c3:
    show_metric_card(
        "HIGHEST VOLATILITY",
        format_percent(highest_risk),
        highest_risk_stock,
        ORANGE
    )

with c4:
    show_metric_card(
        "AVERAGE RETURN",
        format_percent(average_return),
        f"{total_stocks} stocks analysed",
        BLUE
    )

# --------------------------------------------------
# SECTION 2: PERFORMANCE COMPARISON
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">02 / Performance Comparison</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Compare how each selected stock has performed from a common base of 100.'
    '</div>',
    unsafe_allow_html=True
)

normalized = prices.copy()

for col in normalized.columns:
    valid = normalized[col].dropna()

    if not valid.empty and valid.iloc[0] != 0:
        normalized[col] = normalized[col] / valid.iloc[0] * 100

fig = go.Figure()

colors = [
    TEAL, BLUE, GREEN, ORANGE,
    PURPLE, RED, "#FF7EB6", "#7DD3FC"
]

for i, stock in enumerate(normalized.columns):

    fig.add_trace(
        go.Scatter(
            x=normalized.index,
            y=normalized[stock],
            mode="lines",
            name=stock,
            line=dict(
                color=colors[i % len(colors)],
                width=2
            )
        )
    )

fig.add_hline(
    y=100,
    line_dash="dot",
    line_color=MUTED,
    opacity=0.6
)

apply_chart_theme(
    fig,
    height=440,
    y_title="Normalized Price (Base = 100)",
    title="Stock Performance Comparison"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# SECTION 3: RETURNS AND RISK TABLE
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">03 / Returns & Risk Analysis</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Detailed comparison of returns, volatility and risk-adjusted performance.'
    '</div>',
    unsafe_allow_html=True
)

display_metrics = metrics.copy()

display_metrics["Maximum Drawdown"] = max_drawdowns

display_metrics = display_metrics[
    [
        "First Close",
        "Last Close",
        "Cumulative Return",
        "Annualized Return",
        "Annualized Volatility",
        "Sharpe Ratio",
        "Maximum Drawdown"
    ]
]

display_metrics.index.name = "Stock"

formatted_metrics = make_metrics_table(display_metrics)

formatted_metrics["Annualized Volatility"] = (
    display_metrics["Annualized Volatility"]
    .map(lambda x: f"{x * 100:.2f}%")
    .to_numpy()
)

formatted_metrics["Maximum Drawdown"] = (
    display_metrics["Maximum Drawdown"]
    .map(lambda x: f"{x * 100:.2f}%")
    .to_numpy()
)

st.dataframe(
    formatted_metrics,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# SECTION 4: ROLLING VOLATILITY
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">04 / Rolling Volatility</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Observe how the daily return volatility of each stock changes over time.'
    ' Volatility is annualized using a 21-trading-day rolling window.'
    '</div>',
    unsafe_allow_html=True
)

vol_fig = go.Figure()

for i, stock in enumerate(rolling_volatility.columns):

    vol_fig.add_trace(
        go.Scatter(
            x=rolling_volatility.index,
            y=rolling_volatility[stock] * 100,
            mode="lines",
            name=stock,
            line=dict(
                color=colors[i % len(colors)],
                width=2
            )
        )
    )

apply_chart_theme(
    vol_fig,
    height=390,
    y_title="Annualized Volatility (%)",
    title="21-Day Rolling Volatility"
)

st.plotly_chart(vol_fig, use_container_width=True)

# --------------------------------------------------
# SECTION 5: DRAWDOWN ANALYSIS
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">05 / Drawdown Analysis</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Drawdown measures the percentage decline from a previous peak in '
    'cumulative price performance. A larger negative drawdown indicates '
    'a deeper historical decline.'
    '</div>',
    unsafe_allow_html=True
)

dd_fig = go.Figure()

for i, stock in enumerate(drawdowns.columns):

    dd_fig.add_trace(
        go.Scatter(
            x=drawdowns.index,
            y=drawdowns[stock] * 100,
            mode="lines",
            name=stock,
            line=dict(
                color=colors[i % len(colors)],
                width=2
            )
        )
    )

apply_chart_theme(
    dd_fig,
    height=390,
    y_title="Drawdown (%)",
    title="Historical Drawdown"
)

st.plotly_chart(dd_fig, use_container_width=True)

# --------------------------------------------------
# SECTION 6: RISK VS RETURN
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">06 / Risk vs Return</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Compare annualized return against annualized volatility to understand '
    'the relationship between potential return and historical risk.'
    '</div>',
    unsafe_allow_html=True
)

risk_fig = go.Figure()

risk_fig.add_trace(
    go.Scatter(
        x=metrics["Annualized Volatility"] * 100,
        y=metrics["Annualized Return"] * 100,
        mode="markers+text",
        text=metrics.index,
        textposition="top center",
        marker=dict(
            size=13,
            color=colors[:len(metrics)] if len(metrics) <= len(colors)
            else [colors[i % len(colors)] for i in range(len(metrics))],
            line=dict(width=1, color=TEXT)
        )
    )
)

apply_chart_theme(
    risk_fig,
    height=430,
    y_title="Annualized Return (%)",
    title="Risk vs Return Distribution"
)

risk_fig.update_layout(
    xaxis_title="Annualized Volatility (%)"
)

st.plotly_chart(risk_fig, use_container_width=True)

# --------------------------------------------------
# SECTION 7: AUTOMATIC INSIGHTS
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">07 / Performance Insights</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Automatically generated observations based on the selected stocks.'
    '</div>',
    unsafe_allow_html=True
)

insight_col1, insight_col2 = st.columns(2)

with insight_col1:

    show_metric_card(
        "STRONGEST PERFORMER",
        best_return_stock,
        f"Cumulative return: {format_percent(best_return)}",
        GREEN
    )

    show_metric_card(
        "LOWEST VOLATILITY",
        metrics["Annualized Volatility"].idxmin(),
        f"Volatility: {format_percent(metrics['Annualized Volatility'].min())}",
        TEAL
    )

with insight_col2:

    show_metric_card(
        "HIGHEST RISK",
        highest_risk_stock,
        f"Volatility: {format_percent(highest_risk)}",
        ORANGE
    )

    show_metric_card(
        "BEST RISK-ADJUSTED STOCK",
        best_sharpe_stock,
        f"Sharpe ratio: {format_number(best_sharpe)}",
        BLUE
    )

# --------------------------------------------------
# SECTION 8: DOWNLOAD REPORT
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">08 / Export Analysis</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Download the calculated performance and risk metrics.'
    '</div>',
    unsafe_allow_html=True
)

csv_data = display_metrics.reset_index().to_csv(index=False)

st.download_button(
    label="Download Performance & Risk Report (CSV)",
    data=csv_data,
    file_name="FinSight_Performance_Risk.csv",
    mime="text/csv",
    use_container_width=True
)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Methodology: Annualized return and volatility use 252 trading days. "
    f"Sharpe ratio uses a {RISK_FREE_RATE:.1%} annual risk-free rate. "
    "Drawdown is calculated from cumulative daily price returns. "
    "Historical results do not guarantee future performance."
)

show_footer()
