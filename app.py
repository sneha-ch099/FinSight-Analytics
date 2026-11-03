
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from common import (
    STOCKS,
    PALETTE,
    BLUE,
    GREEN,
    TEAL,
    ORANGE,
    PURPLE,
    MUTED,
    get_stock_prices,
    get_latest_quotes,
    prepare_stock_data,
    get_analysis_metrics,
    normalize_prices,
    daily_returns,
    moving_average,
    build_insights,
    format_percent,
    format_number,
    format_currency,
    format_quote_change,
    make_metrics_table,
    apply_chart_theme,
    apply_global_style,
    show_brand,
    show_hero,
    show_metric_card,
    show_footer,
)

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="FinSight Analytics | Market Overview",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_style()

# =========================================================
# BRANDING
# =========================================================

show_brand()

show_hero(
    eyebrow="INDIAN EQUITY INTELLIGENCE",
    title="Understand the market.",
    highlighted_title="Make informed comparisons.",
    description=(
        "Track stock performance, evaluate investment risk "
        "and explore financial insights through interactive analytics."
    ),
    chip="MARKET ANALYSIS  •  PERFORMANCE  •  RISK",
)


# =========================================================
# SIDEBAR CONTROLS
# =========================================================

st.sidebar.markdown("## Analysis controls")
st.sidebar.caption("Configure your market analysis.")

selected_stocks = st.sidebar.multiselect(
    "Select companies",
    options=list(STOCKS.keys()),
    default=[
        "TCS",
        "Infosys",
        "Reliance Industries",
        "HDFC Bank",
        "ICICI Bank",
    ],
    max_selections=8,
    help="Select at least three companies for comparison.",
)

period = st.sidebar.selectbox(
    "Historical period",
    ["1M", "3M", "6M", "1Y", "3Y", "5Y", "Custom"],
    index=3,
)

today = date.today()

if period == "Custom":
    start_date = st.sidebar.date_input(
        "Start date",
        value=today - timedelta(days=365),
        max_value=today,
    )

    end_date = st.sidebar.date_input(
        "End date",
        value=today,
        max_value=today,
    )
else:
    period_days = {
        "1M": 30,
        "3M": 90,
        "6M": 182,
        "1Y": 365,
        "3Y": 1095,
        "5Y": 1825,
    }

    start_date = today - timedelta(days=period_days[period])
    end_date = today

risk_free_rate = (
    st.sidebar.number_input(
        "Annual risk-free rate (%)",
        min_value=0.0,
        max_value=30.0,
        value=6.5,
        step=0.25,
    )
    / 100
)

refresh = st.sidebar.button(
    "↻ Refresh market data",
    use_container_width=True,
)

if refresh:
    get_stock_prices.clear()
    get_latest_quotes.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Data source: Yahoo Finance")
st.sidebar.caption("Quote snapshots may be delayed.")

# =========================================================
# VALIDATE USER INPUT
# =========================================================

if len(selected_stocks) < 3:
    st.warning("Please select at least three stocks to continue.")
    st.stop()

if start_date >= end_date:
    st.error("The start date must be earlier than the end date.")
    st.stop()

stock_items = tuple(
    (name, STOCKS[name])
    for name in selected_stocks
)

# =========================================================
# LOAD HISTORICAL DATA
# =========================================================

try:
    with st.spinner("Loading historical stock market data..."):
        raw_prices = get_stock_prices(
            stock_items,
            start_date,
            end_date + timedelta(days=1),
        )

        prices = prepare_stock_data(raw_prices)

    available_stocks = [
        name for name in selected_stocks
        if name in prices.columns
    ]

    prices = prices[available_stocks]

    if prices.empty or len(prices) < 2:
        st.error(
            "Not enough historical observations were returned. "
            "Please select a longer period."
        )
        st.stop()

    metrics = get_analysis_metrics(
        prices,
        risk_free_rate=risk_free_rate,
    )

    metrics = metrics.loc[
        metrics.index.intersection(available_stocks)
    ]

except Exception as error:
    st.error(f"Unable to load market data: {error}")
    st.info(
        "Check your internet connection, selected companies "
        "and date range, then try refreshing."
    )
    st.stop()

missing_stocks = [
    name for name in selected_stocks
    if name not in available_stocks
]

if missing_stocks:
    st.warning(
        "Historical data was unavailable for: "
        + ", ".join(missing_stocks)
    )

if metrics.empty:
    st.error("No valid stock metrics could be calculated.")
    st.stop()

# =========================================================
# DATA PREPARATION
# =========================================================

normalized = normalize_prices(prices)
daily = daily_returns(prices)
moving_average_20 = moving_average(prices, 20)

colors = {
    stock: PALETTE[index % len(PALETTE)]
    for index, stock in enumerate(prices.columns)
}

cumulative = metrics["Cumulative Return"].dropna()
annual_returns = metrics["Annualized Return"].dropna()
volatility = metrics["Annualized Volatility"].dropna()
sharpe = metrics["Sharpe Ratio"].dropna()

best_stock = cumulative.idxmax() if not cumulative.empty else "N/A"
best_annual = annual_returns.idxmax() if not annual_returns.empty else "N/A"
lowest_vol = volatility.idxmin() if not volatility.empty else "N/A"
best_sharpe = sharpe.idxmax() if not sharpe.empty else "N/A"

# =========================================================
# DATA STATUS
# =========================================================

st.markdown(
    f"""
    <div style="color:{MUTED};font-size:11px;margin:5px 0 18px">
        ● Historical data: {prices.index.min().date()} to {prices.index.max().date()}
        &nbsp; | &nbsp; {len(metrics)} companies analysed
        &nbsp; | &nbsp; {period} period
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# MARKET KPI CARDS
# =========================================================


kpi_columns = st.columns(4, gap="medium")

with kpi_columns[0]:
    show_metric_card(
        "COMPANIES ANALYSED",
        str(len(metrics)),
        "Selected NSE companies",
        BLUE,
    )

with kpi_columns[1]:
    show_metric_card(
        "TOP PERFORMER",
        best_stock,
        (
            format_percent(cumulative.get(best_stock))
            if best_stock != "N/A" else "Unavailable"
        ),
        GREEN,
    )

with kpi_columns[2]:
    show_metric_card(
        "BEST ANNUALISED RETURN",
        best_annual,
        (
            format_percent(annual_returns.get(best_annual))
            if best_annual != "N/A" else "Unavailable"
        ),
        TEAL,
    )

with kpi_columns[3]:
    show_metric_card(
        "BEST SHARPE RATIO",
        best_sharpe,
        (
            format_number(sharpe.get(best_sharpe))
            if best_sharpe != "N/A" else "Unavailable"
        ),
        PURPLE,
    )


# =========================================================
# MAIN CHART AND LATEST QUOTES
# =========================================================

st.markdown(
    '<div class="section-heading">Market performance</div>',
    unsafe_allow_html=True,
)

left, right = st.columns([1.65, 1])

with left:
    chart_choice = st.selectbox(
        "Explore historical data",
        [
            "Normalized Price Performance",
            "Closing Price",
            "Daily Returns",
            "20-Day Moving Average",
        ],
    )

    if chart_choice == "Normalized Price Performance":
        chart_data = normalized
        y_title = "Indexed price (base 100)"

    elif chart_choice == "Closing Price":
        chart_data = prices
        y_title = "Closing price (₹)"

    elif chart_choice == "Daily Returns":
        chart_data = daily * 100
        y_title = "Daily return (%)"

    else:
        chart_data = moving_average_20
        y_title = "20-day moving average (₹)"

    fig = px.line(
        chart_data,
        x=chart_data.index,
        y=chart_data.columns,
        color_discrete_sequence=[
            colors[stock] for stock in chart_data.columns
        ],
        labels={
            "value": y_title,
            "x": "Date",
            "variable": "Company",
        },
    )

    if chart_choice == "Normalized Price Performance":
        fig.add_hline(
            y=100,
            line_dash="dot",
            line_color=ORANGE,
            annotation_text="Base 100",
        )

    if chart_choice == "Daily Returns":
        fig.add_hline(
            y=0,
            line_dash="dot",
            line_color=ORANGE,
        )

    st.plotly_chart(
        apply_chart_theme(
            fig,
            height=390,
            y_title=y_title,
        ),
        use_container_width=True,
    )

with right:
    st.markdown("#### Latest available quotes")

    try:
        quotes = get_latest_quotes(stock_items)
        quote_rows = []

        for stock in available_stocks:
            quote = quotes.get(stock, {})

            price = quote.get("price")
            change = quote.get("change_pct")

            quote_rows.append(
                {
                    "Company": stock,
                    "Price": (
                        format_currency(price)
                        if price is not None
                        else "Unavailable"
                    ),
                    "Change": format_quote_change(change),
                    "As of": quote.get("time", "Unavailable"),
                }
            )

        st.dataframe(
            pd.DataFrame(quote_rows),
            use_container_width=True,
            hide_index=True,
            height=290,
        )

    except Exception:
        st.info("Latest quote snapshots are currently unavailable.")

    st.caption(
        "Quote snapshots use the latest available daily data "
        "and are not guaranteed to be real-time."
    )

# =========================================================
# RISK VS RETURN AND GROWTH CHARTS
# =========================================================

st.markdown(
    '<div class="section-heading">Performance and risk insights</div>',
    unsafe_allow_html=True,
)

chart_left, chart_right = st.columns(2)

with chart_left:
    growth = (
        (1 + daily.fillna(0)).cumprod() * 100
    )

    growth_fig = px.line(
        growth,
        x=growth.index,
        y=growth.columns,
        color_discrete_sequence=[
            colors[stock] for stock in growth.columns
        ],
        labels={
            "value": "Growth of ₹100",
            "x": "Date",
            "variable": "Company",
        },
    )

    st.plotly_chart(
        apply_chart_theme(
            growth_fig,
            height=340,
            y_title="Illustrative value (₹)",
            title="Illustrative growth of ₹100",
        ),
        use_container_width=True,
    )

with chart_right:
    scatter_data = metrics.reset_index()

    risk_fig = px.scatter(
        scatter_data,
        x="Annualized Volatility",
        y="Annualized Return",
        text="Stock",
        color="Stock",
        color_discrete_map=colors,
        size="Trading Observations",
        hover_data=[
            "Cumulative Return",
            "Sharpe Ratio",
        ],
    )

    risk_fig.update_xaxes(tickformat=".0%")
    risk_fig.update_yaxes(tickformat=".0%")
    risk_fig.update_traces(textposition="top center")

    st.plotly_chart(
        apply_chart_theme(
            risk_fig,
            height=340,
            y_title="Annualized return",
            title="Risk versus return",
        ),
        use_container_width=True,
    )

# =========================================================
# KEY BUSINESS INSIGHTS
# =========================================================

st.markdown(
    '<div class="section-heading">Key market insights</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-sub">What the selected historical data indicates.</div>',
    unsafe_allow_html=True,
)

insight_columns = st.columns(3)

with insight_columns[0]:
    if best_stock != "N/A":
        st.markdown(
            f"""
            <div class="insight">
                <div class="insight-title">🏆 Strongest performer</div>
                <div class="insight-copy">
                    {best_stock} recorded a cumulative price return of
                    {format_percent(cumulative[best_stock])}.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with insight_columns[1]:
    if lowest_vol != "N/A":
        st.markdown(
            f"""
            <div class="insight">
                <div class="insight-title">🛡️ Lowest historical volatility</div>
                <div class="insight-copy">
                    {lowest_vol} had annualized volatility of
                    {format_percent(volatility[lowest_vol])}.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with insight_columns[2]:
    if best_sharpe != "N/A":
        st.markdown(
            f"""
            <div class="insight">
                <div class="insight-title">⚖️ Best risk-adjusted return</div>
                <div class="insight-copy">
                    {best_sharpe} had a Sharpe ratio of
                    {format_number(sharpe[best_sharpe])}.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with st.expander("Read detailed financial interpretation"):
    st.text(build_insights(metrics))

# =========================================================
# DOWNLOAD REPORT
# =========================================================

st.markdown(
    '<div class="section-heading">Download analysis</div>',
    unsafe_allow_html=True,
)

download_col1, download_col2 = st.columns([1, 3])

with download_col1:
    st.download_button(
        label="↓ Download metrics CSV",
        data=metrics.reset_index().to_csv(index=False).encode("utf-8"),
        file_name="finsight_stock_metrics.csv",
        mime="text/csv",
        use_container_width=True,
    )

with download_col2:
    st.caption(
        "Export the calculated performance and risk metrics "
        "for further analysis in Excel."
    )

# =========================================================
# FOOTER
# =========================================================

show_footer()
