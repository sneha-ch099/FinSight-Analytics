
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta

from common import (
    STOCKS,
    PALETTE,
    TEAL,
    BLUE,
    GREEN,
    ORANGE,
    PURPLE,
    RED,
    MUTED,
    TEXT,
    get_stock_prices,
    get_latest_quotes,
    prepare_stock_data,
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
    page_title="Market Insights | FinSight Analytics",
    page_icon="🌐",
    layout="wide"
)

apply_global_style()

# --------------------------------------------------
# MARKET CONFIGURATION
# --------------------------------------------------

INDICES = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
}

SECTORS = {
    "IT": ["TCS", "Infosys"],
    "Banking": ["HDFC Bank", "ICICI Bank"],
    "Energy": ["Reliance Industries", "NTPC", "Power Grid"],
    "FMCG": ["ITC"],
    "Automobile": ["Tata Motors", "Maruti Suzuki"],
    "Infrastructure": ["Larsen & Toubro"],
    "Telecom": ["Bharti Airtel"],
}

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("Market Insights")
st.sidebar.caption("Explore Indian equity market trends.")


period = st.sidebar.selectbox(
    "Analysis period",
    ["1M", "3M", "6M", "1Y", "3Y", "5Y", "Custom Date Range"],
    index=3
)

today = date.today()

if period == "Custom Date Range":

    st.sidebar.markdown("### Select your dates")

    start_date = st.sidebar.date_input(
        "Start date",
        value=today - timedelta(days=365),
        min_value=date(2000, 1, 1),
        max_value=today,
        key="market_start_date"
    )

    end_date = st.sidebar.date_input(
        "End date",
        value=today,
        min_value=date(2000, 1, 1),
        max_value=today,
        key="market_end_date"
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
        "3Y": 1095,
        "5Y": 1825,
    }

    start_date = today - timedelta(days=period_days[period])
    end_date = today


if st.sidebar.button("↻ Refresh market data", use_container_width=True):
    get_stock_prices.clear()
    get_latest_quotes.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Data source: Yahoo Finance")
st.sidebar.caption("Historical prices may be delayed.")

# --------------------------------------------------
# BRAND AND HERO
# --------------------------------------------------

show_brand()

show_hero(
    eyebrow="ANALYTICS / INDIAN EQUITY MARKETS",
    title="Explore the market.",
    highlighted_title="Discover the trends.",
    description=(
        "Monitor major Indian market indices, evaluate sector "
        "performance, identify top-performing stocks and understand "
        "overall market direction through interactive analytics."
    ),
    chip="INDICES • SECTORS • MARKET BREADTH • TRENDS"
)

# --------------------------------------------------
# LOAD MARKET DATA
# --------------------------------------------------

stock_items = tuple(STOCKS.items())
index_items = tuple(INDICES.items())

try:
    with st.spinner("Loading Indian market data..."):

        stock_raw = get_stock_prices(
            stock_items,
            start_date,
            end_date + timedelta(days=1)
        )

        index_raw = get_stock_prices(
            index_items,
            start_date,
            end_date + timedelta(days=1)
        )

        stock_prices = prepare_stock_data(stock_raw)
        index_prices = prepare_stock_data(index_raw)

        stock_prices = stock_prices.dropna(axis=1, how="all")
        index_prices = index_prices.dropna(axis=1, how="all")

        if stock_prices.empty or index_prices.empty:
            st.error("Market data is currently unavailable.")
            st.stop()

except Exception as e:
    st.error(f"Unable to load market data: {e}")
    st.info(
        "Check your internet connection and try refreshing "
        "the market data."
    )
    st.stop()

# --------------------------------------------------
# CALCULATIONS
# --------------------------------------------------

stock_returns = stock_prices.pct_change(fill_method=None)
index_returns = index_prices.pct_change(fill_method=None)

stock_latest_returns = stock_returns.iloc[-1].dropna()
index_latest_returns = index_returns.iloc[-1].dropna()

stock_cumulative = (
    stock_prices.iloc[-1] / stock_prices.iloc[0] - 1
)

index_cumulative = (
    index_prices.iloc[-1] / index_prices.iloc[0] - 1
)

# Market breadth
advancing = int((stock_latest_returns > 0).sum())
declining = int((stock_latest_returns < 0).sum())
unchanged = int((stock_latest_returns == 0).sum())

total_stocks = len(stock_latest_returns)

# --------------------------------------------------
# SECTION 1: MARKET OVERVIEW
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">01 / Indian Market Overview</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'A snapshot of the major Indian stock market indices.'
    '</div>',
    unsafe_allow_html=True
)

index_columns = st.columns(2)

for i, index_name in enumerate(INDICES):

    with index_columns[i]:

        if index_name not in index_prices.columns:
            st.warning(f"{index_name} data unavailable.")
            continue

        current_value = index_prices[index_name].iloc[-1]
        previous_value = index_prices[index_name].iloc[-2]

        daily_change = (
            current_value / previous_value - 1
        )

        cumulative_change = index_cumulative[index_name]

        show_metric_card(
            index_name.upper(),
            f"{current_value:,.2f}",
            (
                f"Daily: {daily_change:+.2%} "
                f"| Period: {cumulative_change:+.2%}"
            ),
            GREEN if daily_change >= 0 else RED
        )

# --------------------------------------------------
# SECTION 2: INDEX PERFORMANCE
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">02 / Index Performance</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Compare the historical movement of Nifty 50 and Sensex.'
    '</div>',
    unsafe_allow_html=True
)

normalized_indices = (
    index_prices / index_prices.iloc[0] * 100
)

index_fig = go.Figure()

for i, index_name in enumerate(normalized_indices.columns):

    index_fig.add_trace(
        go.Scatter(
            x=normalized_indices.index,
            y=normalized_indices[index_name],
            mode="lines",
            name=index_name,
            line=dict(
                color=[TEAL, BLUE][i % 2],
                width=2.5
            )
        )
    )

index_fig.add_hline(
    y=100,
    line_dash="dot",
    line_color=ORANGE
)

apply_chart_theme(
    index_fig,
    height=420,
    y_title="Normalized Index (Base = 100)",
    title="Nifty 50 vs Sensex"
)

st.plotly_chart(index_fig, use_container_width=True)

# --------------------------------------------------
# SECTION 3: SECTOR PERFORMANCE
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">03 / Sector Performance</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Compare the selected companies grouped by their business sectors.'
    '</div>',
    unsafe_allow_html=True
)

sector_results = []

for sector, companies in SECTORS.items():

    available = [
        company for company in companies
        if company in stock_cumulative.index
    ]

    if not available:
        continue

    sector_return = stock_cumulative[available].mean()

    sector_results.append({
        "Sector": sector,
        "Average Return": sector_return,
        "Companies": len(available)
    })

sector_df = pd.DataFrame(sector_results)

sector_df = sector_df.sort_values(
    "Average Return",
    ascending=False
)

sector_fig = go.Figure()

sector_fig.add_trace(
    go.Bar(
        x=sector_df["Sector"],
        y=sector_df["Average Return"] * 100,
        marker_color=[
            GREEN if value >= 0 else RED
            for value in sector_df["Average Return"]
        ],
        text=sector_df["Average Return"].map(
            lambda x: f"{x:+.2%}"
        ),
        textposition="outside"
    )
)

apply_chart_theme(
    sector_fig,
    height=400,
    y_title="Average Historical Return (%)",
    title="Sector-wise Performance"
)

st.plotly_chart(sector_fig, use_container_width=True)

st.caption(
    "Sector returns are simple averages of the selected "
    "companies' price returns, not official sector index returns."
)

# --------------------------------------------------
# SECTION 4: TOP GAINERS AND LOSERS
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">04 / Top Gainers & Losers</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Identify the strongest and weakest performers based on '
    'their latest available daily price movements.'
    '</div>',
    unsafe_allow_html=True
)

gainers = stock_latest_returns[
    stock_latest_returns > 0
].sort_values(ascending=False).head(5)

losers = stock_latest_returns[
    stock_latest_returns < 0
].sort_values(ascending=True).head(5)

gain_col, loss_col = st.columns(2)

with gain_col:

    st.markdown("#### 🟢 Top Gainers")

    gain_df = pd.DataFrame({
        "Company": gainers.index,
        "Daily Change": gainers.values
    })

    st.dataframe(
        gain_df.style.format({
            "Daily Change": "{:+.2%}"
        }),
        use_container_width=True,
        hide_index=True
    )

with loss_col:

    st.markdown("#### 🔴 Top Losers")

    loss_df = pd.DataFrame({
        "Company": losers.index,
        "Daily Change": losers.values
    })

    st.dataframe(
        loss_df.style.format({
            "Daily Change": "{:+.2%}"
        }),
        use_container_width=True,
        hide_index=True
    )

# --------------------------------------------------
# SECTION 5: MARKET BREADTH
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">05 / Market Breadth</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Understand how many selected stocks advanced or declined '
    'during the latest available trading session.'
    '</div>',
    unsafe_allow_html=True
)

b1, b2, b3 = st.columns(3)

with b1:
    show_metric_card(
        "ADVANCING STOCKS",
        str(advancing),
        "Positive daily returns",
        GREEN
    )

with b2:
    show_metric_card(
        "DECLINING STOCKS",
        str(declining),
        "Negative daily returns",
        RED
    )

with b3:
    show_metric_card(
        "UNCHANGED STOCKS",
        str(unchanged),
        "No daily price movement",
        BLUE
    )

breadth_fig = go.Figure(
    data=[
        go.Pie(
            labels=["Advancing", "Declining", "Unchanged"],
            values=[advancing, declining, unchanged],
            hole=0.65,
            marker=dict(
                colors=[GREEN, RED, BLUE]
            ),
            textinfo="label+value+percent"
        )
    ]
)

breadth_fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=370,
    title="Market Breadth Distribution"
)

st.plotly_chart(
    breadth_fig,
    use_container_width=True
)

st.caption(
    f"Market breadth is calculated from {total_stocks} selected "
    "companies, not the entire NSE market."
)

# --------------------------------------------------
# SECTION 6: MARKET TRENDS
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">06 / Market Trends</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Examine recent index returns and historical market movements.'
    '</div>',
    unsafe_allow_html=True
)

trend_choice = st.selectbox(
    "Select index",
    list(index_prices.columns)
)

trend_prices = index_prices[trend_choice]

trend_fig = go.Figure()

trend_fig.add_trace(
    go.Scatter(
        x=trend_prices.index,
        y=trend_prices.values,
        mode="lines",
        name=trend_choice,
        line=dict(color=TEAL, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(25,211,197,0.08)"
    )
)

trend_fig.add_trace(
    go.Scatter(
        x=trend_prices.index,
        y=trend_prices.rolling(20).mean(),
        mode="lines",
        name="20-Day Moving Average",
        line=dict(color=ORANGE, width=1.8)
    )
)

apply_chart_theme(
    trend_fig,
    height=420,
    y_title="Index Value",
    title=f"{trend_choice} Historical Trend"
)

st.plotly_chart(
    trend_fig,
    use_container_width=True
)

# --------------------------------------------------
# SECTION 7: AUTOMATED MARKET INSIGHTS
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">07 / Automated Market Insights</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Automatically generated observations from the available market data.'
    '</div>',
    unsafe_allow_html=True
)

insight_col1, insight_col2 = st.columns(2)

strongest_sector = sector_df.iloc[0]
weakest_sector = sector_df.iloc[-1]

with insight_col1:

    show_metric_card(
        "STRONGEST SECTOR",
        strongest_sector["Sector"],
        f"Average return: {strongest_sector['Average Return']:+.2%}",
        GREEN
    )

    show_metric_card(
        "MARKET ADVANCERS",
        str(advancing),
        f"Out of {total_stocks} selected companies",
        TEAL
    )

with insight_col2:

    show_metric_card(
        "WEAKEST SECTOR",
        weakest_sector["Sector"],
        f"Average return: {weakest_sector['Average Return']:+.2%}",
        ORANGE
    )

    market_direction = (
        "Positive" if advancing > declining
        else "Negative" if declining > advancing
        else "Mixed"
    )

    show_metric_card(
        "MARKET DIRECTION",
        market_direction,
        "Based on selected stocks' daily movements",
        BLUE
    )

with st.expander("Read market interpretation"):

    st.write(
        f"""
        **Market direction:** {market_direction}

        **Strongest sector:** {strongest_sector['Sector']} 
        with an average historical return of 
        {strongest_sector['Average Return']:+.2%}.

        **Weakest sector:** {weakest_sector['Sector']} 
        with an average historical return of 
        {weakest_sector['Average Return']:+.2%}.

        **Market breadth:** {advancing} companies advanced, 
        {declining} declined and {unchanged} remained unchanged.

        These observations describe historical price movements 
        and do not predict future market performance.
        """
    )

# --------------------------------------------------
# DOWNLOAD REPORT
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">08 / Export Market Analysis</div>',
    unsafe_allow_html=True
)

report = sector_df.copy()

st.download_button(
    "Download Market Insights CSV",
    data=report.to_csv(index=False),
    file_name="FinSight_Market_Insights.csv",
    mime="text/csv",
    use_container_width=True
)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Data source: Yahoo Finance. Index values, stock movements "
    "and sector averages are based on available historical prices. "
    "This dashboard is intended for educational analysis, "
    "not investment advice."
)

show_footer()
