
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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
    page_title="Portfolio Lab | FinSight Analytics",
    page_icon="💼",
    layout="wide"
)

apply_global_style()

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("Portfolio Lab")
st.sidebar.caption("Build and analyse your investment portfolio.")

stock_names = list(STOCKS.keys())

selected_stocks = st.sidebar.multiselect(
    "Choose portfolio stocks",
    options=stock_names,
    default=stock_names[:4]
)


period = st.sidebar.selectbox(
    "Historical analysis period",
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
        key="portfolio_start_date"
    )

    end_date = st.sidebar.date_input(
        "End date",
        value=date.today(),
        min_value=date(2000, 1, 1),
        max_value=date.today(),
        key="portfolio_end_date"
    )

    if start_date >= end_date:
        st.sidebar.error("End date must be after start date.")
        st.stop()


investment = st.sidebar.number_input(
    "Total investment amount (₹)",
    min_value=1000,
    max_value=100000000,
    value=100000,
    step=5000
)

st.sidebar.markdown("---")
st.sidebar.caption("Portfolio weights must total 100%.")

# --------------------------------------------------
# BRAND AND HERO
# --------------------------------------------------

show_brand()

show_hero(
    eyebrow="ANALYTICS / PORTFOLIO LAB",
    title="Build Your Portfolio.",
    highlighted_title="Manage Your Risk.",
    description=(
        "Create a customized stock portfolio, allocate your investment "
        "across companies and evaluate expected returns, portfolio risk "
        "and diversification."
    ),
    chip="PORTFOLIO BUILDER  •  ALLOCATION  •  RISK ANALYSIS"
)

# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

if not selected_stocks:
    st.warning("Please select at least one stock from the sidebar.")
    st.stop()

# --------------------------------------------------
# SECTION 1: PORTFOLIO BUILDER
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">01 / Portfolio Builder</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Allocate your investment across the selected companies. '
    'The total allocation must equal 100%.'
    '</div>',
    unsafe_allow_html=True
)

# Create equal-weight defaults
base_weight = round(100 / len(selected_stocks), 2)

default_weights = [
    base_weight for _ in selected_stocks
]

default_weights[-1] = round(
    100 - sum(default_weights[:-1]), 2
)

weights = {}

weight_columns = st.columns(3)

for i, stock in enumerate(selected_stocks):

    with weight_columns[i % 3]:

        weights[stock] = st.number_input(
            f"{stock} allocation (%)",
            min_value=0.0,
            max_value=100.0,
            value=default_weights[i],
            step=1.0,
            key=f"portfolio_weight_{stock}"
        )

total_weight = sum(weights.values())

allocation_col1, allocation_col2 = st.columns(2)

with allocation_col1:
    show_metric_card(
        "TOTAL ALLOCATION",
        f"{total_weight:.2f}%",
        "Target allocation: 100%",
        TEAL if abs(total_weight - 100) < 0.01 else ORANGE
    )

with allocation_col2:
    show_metric_card(
        "TOTAL INVESTMENT",
        f"₹{investment:,.0f}",
        f"{len(selected_stocks)} selected stocks",
        BLUE
    )

if not np.isclose(total_weight, 100, atol=0.01):
    st.warning(
        f"Your allocation is {total_weight:.2f}%. "
        "Please adjust the weights to total exactly 100%."
    )
    st.stop()

weight_series = pd.Series(weights, dtype=float) / 100

# --------------------------------------------------
# LOAD HISTORICAL DATA
# --------------------------------------------------


if period != "Custom Date Range":
    start_date, end_date = date_range_from_period(period)


stock_items = {
    name: STOCKS[name]
    for name in selected_stocks
}

try:

    with st.spinner("Loading portfolio market data..."):

        raw_prices = get_stock_prices(
            stock_items,
            start_date,
            end_date + timedelta(days=1)
        )

        prices = prepare_stock_data(raw_prices)

        prices = prices.dropna(axis=1, how="all")

        available_stocks = [
            stock for stock in selected_stocks
            if stock in prices.columns
        ]

        if len(available_stocks) != len(selected_stocks):
            missing = [
                stock for stock in selected_stocks
                if stock not in available_stocks
            ]

            st.error(
                "Historical data is unavailable for: "
                + ", ".join(missing)
                + ". Please remove these stocks from your selection."
            )
            st.stop()

        prices = prices[selected_stocks]

        if len(prices) < 3:
            st.error("Insufficient historical data.")
            st.stop()

except Exception as e:

    st.error(f"Unable to load portfolio data: {e}")
    st.stop()

# --------------------------------------------------
# PORTFOLIO CALCULATIONS
# --------------------------------------------------

daily_returns = prices.pct_change(fill_method=None)

aligned_returns = daily_returns.dropna(how="any")

if len(aligned_returns) < 2:
    st.error("Not enough common trading observations.")
    st.stop()

# Daily portfolio return
portfolio_returns = (
    aligned_returns * weight_series
).sum(axis=1)

# Portfolio growth
portfolio_growth = (1 + portfolio_returns).cumprod()

portfolio_value = portfolio_growth * investment

# Cumulative portfolio return
cumulative_return = portfolio_growth.iloc[-1] - 1

# Annualized return
annualized_return = (
    portfolio_growth.iloc[-1]
    ** (TRADING_DAYS / len(portfolio_returns))
) - 1

# Annualized portfolio volatility
portfolio_volatility = (
    portfolio_returns.std(ddof=1)
    * np.sqrt(TRADING_DAYS)
)

# Sharpe ratio
portfolio_sharpe = (
    (annualized_return - RISK_FREE_RATE)
    / portfolio_volatility
    if portfolio_volatility > 0
    else np.nan
)

# Portfolio drawdown
portfolio_drawdown = (
    portfolio_growth / portfolio_growth.cummax()
) - 1

maximum_drawdown = portfolio_drawdown.min()

final_value = portfolio_value.iloc[-1]

profit_loss = final_value - investment

# --------------------------------------------------
# SECTION 2: PORTFOLIO PERFORMANCE
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">02 / Portfolio Performance</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Review the historical performance of your customized investment portfolio.'
    '</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    show_metric_card(
        "CURRENT PORTFOLIO VALUE",
        f"₹{final_value:,.2f}",
        f"Initial: ₹{investment:,.0f}",
        BLUE
    )

with c2:
    show_metric_card(
        "CUMULATIVE RETURN",
        f"{cumulative_return:+.2%}",
        "Historical portfolio return",
        GREEN if cumulative_return >= 0 else RED
    )

with c3:
    show_metric_card(
        "PROFIT / LOSS",
        f"₹{profit_loss:+,.2f}",
        "Based on historical price movements",
        GREEN if profit_loss >= 0 else RED
    )

with c4:
    show_metric_card(
        "ANNUALIZED RETURN",
        f"{annualized_return:+.2%}",
        "Estimated from historical observations",
        TEAL
    )

# --------------------------------------------------
# SECTION 3: ASSET ALLOCATION
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">03 / Asset Allocation</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Understand how your total investment is distributed across selected stocks.'
    '</div>',
    unsafe_allow_html=True
)

allocated_amounts = weight_series * investment

allocation_col1, allocation_col2 = st.columns(2)

with allocation_col1:

    allocation_fig = go.Figure(
        data=[
            go.Pie(
                labels=weight_series.index,
                values=weight_series.values * 100,
                hole=0.62,
                textinfo="label+percent",
                marker=dict(
                    colors=[
                        TEAL, BLUE, GREEN, ORANGE,
                        PURPLE, RED, "#FF7EB6", "#7DD3FC",
                        "#B5D66B", "#F28C52", "#C4A1FF", "#A3E635"
                    ]
                )
            )
        ]
    )

    allocation_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=380,
        margin=dict(l=15, r=15, t=35, b=15),
        title="Portfolio Allocation"
    )

    st.plotly_chart(
        allocation_fig,
        use_container_width=True
    )

with allocation_col2:

    allocation_table = pd.DataFrame({
        "Stock": weight_series.index,
        "Weight (%)": weight_series.values * 100,
        "Investment Amount (₹)": allocated_amounts.values
    })

    allocation_table["Weight (%)"] = (
        allocation_table["Weight (%)"].map(
            lambda x: f"{x:.2f}%"
        )
    )

    allocation_table["Investment Amount (₹)"] = (
        allocation_table["Investment Amount (₹)"].map(
            lambda x: f"₹{x:,.2f}"
        )
    )

    st.markdown("#### Investment Distribution")

    st.dataframe(
        allocation_table,
        use_container_width=True,
        hide_index=True
    )

# --------------------------------------------------
# SECTION 4: PORTFOLIO VALUE TREND
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">04 / Portfolio Value Trend</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Track how your portfolio value would have changed over the selected period.'
    '</div>',
    unsafe_allow_html=True
)

value_fig = go.Figure()

value_fig.add_trace(
    go.Scatter(
        x=portfolio_value.index,
        y=portfolio_value.values,
        mode="lines",
        name="Portfolio Value",
        line=dict(color=TEAL, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(25,211,197,0.08)"
    )
)

value_fig.add_hline(
    y=investment,
    line_dash="dot",
    line_color=ORANGE,
    annotation_text="Initial Investment"
)

apply_chart_theme(
    value_fig,
    height=400,
    y_title="Portfolio Value (₹)",
    title="Historical Portfolio Value"
)

st.plotly_chart(
    value_fig,
    use_container_width=True
)

# --------------------------------------------------
# SECTION 5: PORTFOLIO RISK
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">05 / Portfolio Risk Analysis</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Measure the risk associated with your portfolio using volatility, '
    'Sharpe ratio and maximum drawdown.'
    '</div>',
    unsafe_allow_html=True
)

r1, r2, r3 = st.columns(3)

with r1:
    show_metric_card(
        "ANNUALIZED VOLATILITY",
        f"{portfolio_volatility:.2%}",
        "Portfolio standard deviation",
        ORANGE
    )

with r2:
    show_metric_card(
        "SHARPE RATIO",
        f"{portfolio_sharpe:.2f}",
        f"Risk-free rate: {RISK_FREE_RATE:.1%}",
        BLUE
    )

with r3:
    show_metric_card(
        "MAXIMUM DRAWDOWN",
        f"{maximum_drawdown:.2%}",
        "Largest historical decline from a peak",
        RED
    )

drawdown_fig = go.Figure()

drawdown_fig.add_trace(
    go.Scatter(
        x=portfolio_drawdown.index,
        y=portfolio_drawdown.values * 100,
        mode="lines",
        name="Portfolio Drawdown",
        line=dict(color=RED, width=2),
        fill="tozeroy",
        fillcolor="rgba(255,102,125,0.10)"
    )
)

apply_chart_theme(
    drawdown_fig,
    height=350,
    y_title="Drawdown (%)",
    title="Portfolio Drawdown History"
)

st.plotly_chart(
    drawdown_fig,
    use_container_width=True
)

# --------------------------------------------------
# SECTION 6: DIVERSIFICATION ANALYSIS
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">06 / Diversification Analysis</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-sub">'
    'Examine how the selected stocks move in relation to one another '
    'using historical return correlations.'
    '</div>',
    unsafe_allow_html=True
)

correlation_matrix = aligned_returns.corr()

correlation_fig = go.Figure(
    data=go.Heatmap(
        z=correlation_matrix.values,
        x=correlation_matrix.columns,
        y=correlation_matrix.index,
        colorscale="RdBu",
        zmin=-1,
        zmax=1,
        text=np.round(correlation_matrix.values, 2),
        texttemplate="%{text}",
        colorbar=dict(title="Correlation")
    )
)

correlation_fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=430,
    title="Stock Return Correlation Matrix",
    margin=dict(l=25, r=25, t=60, b=30)
)

st.plotly_chart(
    correlation_fig,
    use_container_width=True
)

st.caption(
    "Correlation ranges from -1 to +1. Positive values indicate "
    "stocks tend to move in the same direction, while negative "
    "values indicate opposite movements."
)

# --------------------------------------------------
# SECTION 7: INDIVIDUAL STOCK CONTRIBUTION
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">07 / Stock Contribution</div>',
    unsafe_allow_html=True
)

individual_returns = prices.iloc[-1] / prices.iloc[0] - 1

contribution = pd.DataFrame({
    "Stock": selected_stocks,
    "Portfolio Weight (%)": weight_series.values * 100,
    "Investment Amount (₹)": allocated_amounts.values,
    "Historical Stock Return (%)": (
        individual_returns.reindex(selected_stocks).values * 100
    ),
})

contribution["Weighted Return Contribution (%)"] = (
    contribution["Portfolio Weight (%)"]
    * contribution["Historical Stock Return (%)"]
    / 100
)

st.dataframe(
    contribution.style.format({
        "Portfolio Weight (%)": "{:.2f}%",
        "Investment Amount (₹)": "₹{:,.2f}",
        "Historical Stock Return (%)": "{:+.2f}%",
        "Weighted Return Contribution (%)": "{:+.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# SECTION 8: PORTFOLIO INSIGHTS
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">08 / Portfolio Insights</div>',
    unsafe_allow_html=True
)

best_stock = individual_returns.idxmax()
worst_stock = individual_returns.idxmin()

highest_weight_stock = weight_series.idxmax()

insight_col1, insight_col2 = st.columns(2)

with insight_col1:

    show_metric_card(
        "BEST PERFORMING STOCK",
        best_stock,
        f"Historical return: {individual_returns[best_stock]:+.2%}",
        GREEN
    )

    show_metric_card(
        "LARGEST ALLOCATION",
        highest_weight_stock,
        f"Portfolio weight: {weight_series[highest_weight_stock]:.2%}",
        TEAL
    )

with insight_col2:

    show_metric_card(
        "WEAKEST PERFORMING STOCK",
        worst_stock,
        f"Historical return: {individual_returns[worst_stock]:+.2%}",
        ORANGE
    )

    show_metric_card(
        "PORTFOLIO RISK",
        f"{portfolio_volatility:.2%}",
        "Annualized historical volatility",
        BLUE
    )

# --------------------------------------------------
# SECTION 9: DOWNLOAD REPORT
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">09 / Export Portfolio Report</div>',
    unsafe_allow_html=True
)

report = contribution.copy()

report["Portfolio Value (₹)"] = final_value
report["Portfolio Return (%)"] = cumulative_return * 100
report["Portfolio Volatility (%)"] = portfolio_volatility * 100
report["Portfolio Sharpe Ratio"] = portfolio_sharpe

st.download_button(
    label="Download Portfolio Analysis (CSV)",
    data=report.to_csv(index=False),
    file_name="FinSight_Portfolio_Report.csv",
    mime="text/csv",
    use_container_width=True
)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Methodology: Portfolio returns are calculated using weighted daily "
    "stock returns. Annualized volatility uses 252 trading days. "
    "Historical portfolio value assumes daily rebalancing to the selected "
    "weights. Dividends, taxes and transaction costs are excluded. "
    "Historical performance does not guarantee future results."
)

show_footer()
