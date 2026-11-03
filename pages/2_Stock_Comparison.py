
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import date, timedelta

from plotly.subplots import make_subplots

from common import (
    STOCKS,
    TEXT,
    MUTED,
    TEAL,
    BLUE,
    GREEN,
    ORANGE,
    PURPLE,
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
    page_title="Stock Comparison | FinSight Analytics",
    page_icon="📈",
    layout="wide",
)

apply_global_style()
show_brand()

show_hero(
    eyebrow="MULTI-STOCK ANALYSIS",
    title="Compare performance.",
    highlighted_title="Measure risk intelligently.",
    description=(
        "Compare Indian equities over the same historical period. "
        "Understand returns, volatility and risk-adjusted performance."
    ),
    chip="NORMALIZED PRICES  •  RETURNS  •  RISK ANALYSIS",
)

# =========================================================
# DATA DOWNLOAD
# =========================================================

@st.cache_data(ttl=600, show_spinner=False)
def download_comparison_data(tickers, start, end):

    prices = {}
    failed = []

    for name, ticker in tickers.items():

        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=False,
                timeout=25,
            )

            if df is None or df.empty:
                failed.append(name)
                continue

            # Handle yfinance MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):

                if ticker in df.columns.get_level_values(-1):
                    df = df.xs(ticker, axis=1, level=-1)

                elif ticker in df.columns.get_level_values(0):
                    df = df.xs(ticker, axis=1, level=0)

                else:
                    df.columns = df.columns.get_level_values(0)

            if "Close" not in df.columns:
                failed.append(name)
                continue

            close = pd.to_numeric(
                df["Close"],
                errors="coerce"
            ).dropna()

            if len(close) < 2:
                failed.append(name)
                continue

            prices[name] = close

        except Exception:
            failed.append(name)

    if not prices:
        raise RuntimeError(
            "No stock price data was returned. "
            "Check your internet connection or ticker symbols."
        )

    price_df = pd.concat(
        prices,
        axis=1
    ).sort_index()

    price_df = price_df[
        ~price_df.index.duplicated(keep="last")
    ]

    price_df = price_df.dropna(how="all")

    return price_df, failed


# =========================================================
# FINANCIAL METRICS
# =========================================================

def calculate_comparison_metrics(prices, risk_free_rate):

    rows = []

    for stock in prices.columns:

        series = prices[stock].dropna()

        if len(series) < 2:
            continue

        returns = series.pct_change(
            fill_method=None
        ).dropna()

        first_price = float(series.iloc[0])
        last_price = float(series.iloc[-1])

        cumulative_return = (
            last_price / first_price
        ) - 1

        # Annualized return using calendar-day CAGR
        elapsed_days = (
            series.index[-1] - series.index[0]
        ).days

        if elapsed_days > 0 and first_price > 0 and last_price > 0:
            annualized_return = (
                (last_price / first_price)
                ** (365.25 / elapsed_days)
            ) - 1
        else:
            annualized_return = np.nan

        # Annualized volatility
        volatility = (
            returns.std(ddof=1) * np.sqrt(252)
            if len(returns) > 1
            else np.nan
        )

        # Annualized Sharpe ratio using daily excess returns
        daily_risk_free = (
            (1 + risk_free_rate) ** (1 / 252)
        ) - 1

        excess_returns = returns - daily_risk_free

        sharpe = (
            excess_returns.mean()
            / returns.std(ddof=1)
            * np.sqrt(252)
            if len(returns) > 1
            and returns.std(ddof=1) > 0
            else np.nan
        )

        rows.append({
            "Stock": stock,
            "First Close": first_price,
            "Latest Close": last_price,
            "Cumulative Return": cumulative_return,
            "Annualized Return": annualized_return,
            "Annualized Volatility": volatility,
            "Sharpe Ratio": sharpe,
            "Observations": len(series),
        })

    if not rows:
        raise RuntimeError(
            "Not enough data to calculate comparison metrics."
        )

    return pd.DataFrame(rows).set_index("Stock")


# =========================================================
# SIDEBAR CONTROLS
# =========================================================

st.sidebar.markdown("## Comparison controls")
st.sidebar.caption("Configure your stock comparison.")

stock_options = list(STOCKS.keys())

default_stocks = [
    name for name in [
        "TCS",
        "Infosys",
        "Reliance Industries",
        "HDFC Bank",
        "ICICI Bank",
    ]
    if name in STOCKS
]

if len(default_stocks) < 3:
    default_stocks = stock_options[:min(5, len(stock_options))]

selected_stocks = st.sidebar.multiselect(
    "Select companies",
    options=stock_options,
    default=default_stocks,
    help="Select at least three companies for a meaningful comparison.",
)


period = st.sidebar.selectbox(
    "Historical period",
    ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "Custom Date Range"],
    index=3,
)

period_days = {
    "1M": 30,
    "3M": 90,
    "6M": 182,
    "1Y": 365,
    "2Y": 730,
    "3Y": 1095,
    "5Y": 1825,
}


risk_free_rate = st.sidebar.number_input(
    "Annual risk-free rate (%)",
    min_value=0.0,
    max_value=20.0,
    value=6.5,
    step=0.25,
)

st.sidebar.markdown("---")

chart_choice = st.sidebar.selectbox(
    "Performance chart",
    [
        "Normalized prices",
        "Daily returns",
        "Cumulative returns",
    ],
)

if st.sidebar.button(
    "↻ Refresh comparison data",
    use_container_width=True
):
    download_comparison_data.clear()
    st.rerun()

# =========================================================
# VALIDATE SELECTION
# =========================================================

if len(selected_stocks) < 3:

    st.warning(
        "Please select at least three companies "
        "to use the stock comparison dashboard."
    )

    st.stop()

selected_tickers = {
    name: STOCKS[name]
    for name in selected_stocks
}


end_date = date.today()

if period == "Custom Date Range":

    st.sidebar.markdown("### Select your dates")

    start_date = st.sidebar.date_input(
        "Start date",
        value=end_date - timedelta(days=365),
        min_value=date(2000, 1, 1),
        max_value=end_date,
        key="comparison_start_date",
    )

    end_date = st.sidebar.date_input(
        "End date",
        value=date.today(),
        min_value=date(2000, 1, 1),
        max_value=date.today(),
        key="comparison_end_date",
    )

    if start_date >= end_date:
        st.sidebar.error("End date must be after start date.")
        st.stop()

else:
    start_date = end_date - timedelta(
        days=period_days[period]
    )


# =========================================================
# LOAD DATA
# =========================================================

try:

    with st.spinner("Comparing selected companies..."):

        prices, failed_stocks = download_comparison_data(
            selected_tickers,
            start_date.isoformat(),
            (end_date + timedelta(days=1)).isoformat(),
        )

except Exception as error:

    st.error(str(error))
    st.stop()

if failed_stocks:

    st.warning(
        "Historical data could not be loaded for: "
        + ", ".join(failed_stocks)
        + ". These companies have been excluded from the analysis."
    )

# Remove stocks with insufficient observations
prices = prices.dropna(axis=1, thresh=2)

if prices.shape[1] < 3:

    st.error(
        "Fewer than three companies returned sufficient historical data. "
        "Please select other companies or try a different period."
    )

    st.stop()

# =========================================================
# CALCULATE ANALYSIS
# =========================================================

annual_rf = risk_free_rate / 100

metrics = calculate_comparison_metrics(
    prices,
    annual_rf,
)

returns = prices.pct_change(fill_method=None)

normalized = prices.copy()

for column in normalized.columns:

    first_valid = normalized[column].dropna()

    if not first_valid.empty and first_valid.iloc[0] != 0:

        normalized[column] = (
            normalized[column]
            / first_valid.iloc[0]
        ) * 100

cumulative_returns = (1 + returns).cumprod() * 100

# =========================================================
# SUMMARY
# =========================================================

best_performer = (
    metrics["Cumulative Return"].idxmax()
)

lowest_volatility = (
    metrics["Annualized Volatility"].idxmin()
)

best_sharpe = (
    metrics["Sharpe Ratio"].idxmax()
    if metrics["Sharpe Ratio"].notna().any()
    else "N/A"
)

best_return = metrics["Annualized Return"].idxmax()

st.markdown(
    f"""
    <div style="font-size:12px;color:{MUTED};margin:15px 0 22px">
        Historical data: {prices.index.min().date()}
        to {prices.index.max().date()}
        &nbsp; | &nbsp; {len(prices.columns)} companies analysed
        &nbsp; | &nbsp; Selected period: {start_date} to {end_date}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Comparison highlights")

c1, c2, c3, c4 = st.columns(4, gap="medium")

with c1:
    show_metric_card(
        "COMPANIES ANALYSED",
        str(len(prices.columns)),
        "Successfully loaded stocks",
        BLUE,
    )

with c2:
    show_metric_card(
        "TOP PERFORMER",
        best_performer,
        f"{metrics.loc[best_performer, 'Cumulative Return']:+.2%} cumulative return",
        GREEN,
    )

with c3:
    show_metric_card(
        "BEST ANNUALISED RETURN",
        best_return,
        f"{metrics.loc[best_return, 'Annualized Return']:+.2%}",
        TEAL,
    )

with c4:
    show_metric_card(
        "BEST SHARPE RATIO",
        best_sharpe,
        (
            f"{metrics.loc[best_sharpe, 'Sharpe Ratio']:.2f}"
            if best_sharpe != "N/A"
            else "Not available"
        ),
        PURPLE,
    )

# =========================================================
# NORMALIZED PERFORMANCE CHART
# =========================================================

st.markdown("---")
st.markdown("### Relative price performance")

st.caption(
    "Every stock starts at a common base value of 100. "
    "This makes percentage performance easier to compare."
)

fig = go.Figure()

palette = [
    TEAL,
    BLUE,
    ORANGE,
    PURPLE,
    GREEN,
    "#F472B6",
    "#A3E635",
    "#F59E0B",
]

if chart_choice == "Normalized prices":

    chart_data = normalized
    y_title = "Indexed price (base 100)"

elif chart_choice == "Daily returns":

    chart_data = returns * 100
    y_title = "Daily return (%)"

else:

    chart_data = cumulative_returns
    y_title = "Growth of 100"

for i, stock in enumerate(chart_data.columns):

    fig.add_trace(
        go.Scatter(
            x=chart_data.index,
            y=chart_data[stock],
            name=stock,
            mode="lines",
            line=dict(
                color=palette[i % len(palette)],
                width=2,
            ),
            connectgaps=False,
        )
    )

if chart_choice == "Normalized prices":

    fig.add_hline(
        y=100,
        line_dash="dot",
        line_color=ORANGE,
        annotation_text="Base 100",
    )

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT, size=11),
    height=480,
    margin=dict(l=25, r=25, t=45, b=25),
    hovermode="x unified",
    legend=dict(
        orientation="h",
        y=1.12,
        x=0,
        title_text="",
    ),
)

fig.update_xaxes(
    title_text="Date",
    showgrid=True,
    gridcolor="rgba(145,169,190,.10)",
)

fig.update_yaxes(
    title_text=y_title,
    showgrid=True,
    gridcolor="rgba(145,169,190,.10)",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

# =========================================================
# RISK AND RETURN COMPARISON
# =========================================================

st.markdown("---")
st.markdown("### Risk versus return")

st.caption(
    "Compare annualized return against annualized volatility. "
    "Lower volatility with higher return may indicate a more favourable "
    "historical risk-return profile."
)

risk_fig = go.Figure()

for i, stock in enumerate(metrics.index):

    row = metrics.loc[stock]

    if pd.isna(row["Annualized Volatility"]) or pd.isna(
        row["Annualized Return"]
    ):
        continue

    risk_fig.add_trace(
        go.Scatter(
            x=[row["Annualized Volatility"] * 100],
            y=[row["Annualized Return"] * 100],
            mode="markers+text",
            name=stock,
            text=[stock],
            textposition="top center",
            marker=dict(
                size=17,
                color=palette[i % len(palette)],
                line=dict(width=1, color="white"),
            ),
            hovertemplate=(
                "<b>" + stock + "</b><br>"
                "Annualized volatility: %{x:.2f}%<br>"
                "Annualized return: %{y:.2f}%"
                "<extra></extra>"
            ),
        )
    )

risk_fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT, size=11),
    height=440,
    margin=dict(l=25, r=25, t=35, b=25),
    showlegend=False,
)

risk_fig.update_xaxes(
    title_text="Annualized volatility (%)",
    showgrid=True,
    gridcolor="rgba(145,169,190,.10)",
)

risk_fig.update_yaxes(
    title_text="Annualized return (%)",
    showgrid=True,
    gridcolor="rgba(145,169,190,.10)",
)

st.plotly_chart(
    risk_fig,
    use_container_width=True,
)

# =========================================================
# METRICS TABLE
# =========================================================

st.markdown("---")
st.markdown("### Financial performance comparison")

st.caption(
    "Compare cumulative return, annualized return, volatility and Sharpe ratio."
)

display_metrics = metrics.copy()

display_metrics["Cumulative Return"] = (
    display_metrics["Cumulative Return"].map(
        lambda x: f"{x:.2%}"
    )
)

display_metrics["Annualized Return"] = (
    display_metrics["Annualized Return"].map(
        lambda x: f"{x:.2%}"
    )
)

display_metrics["Annualized Volatility"] = (
    display_metrics["Annualized Volatility"].map(
        lambda x: f"{x:.2%}"
    )
)

display_metrics["Sharpe Ratio"] = (
    display_metrics["Sharpe Ratio"].map(
        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
    )
)

display_metrics["First Close"] = (
    display_metrics["First Close"].map(
        lambda x: f"₹{x:,.2f}"
    )
)

display_metrics["Latest Close"] = (
    display_metrics["Latest Close"].map(
        lambda x: f"₹{x:,.2f}"
    )
)

st.dataframe(
    display_metrics,
    use_container_width=True,
)

# =========================================================
# PERFORMANCE RANKING
# =========================================================

st.markdown("---")
st.markdown("### Performance ranking")

ranking = metrics.sort_values(
    "Cumulative Return",
    ascending=False,
)

for rank, (stock, row) in enumerate(
    ranking.iterrows(),
    start=1
):

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.markdown(f"**{rank}. {stock}**")

    with col2:
        st.progress(
            max(
                0.0,
                min(
                    1.0,
                    (row["Cumulative Return"] + 1) / 2
                )
            )
        )

    with col3:
        st.markdown(
            f"**{row['Cumulative Return']:+.2%}**"
        )

# =========================================================
# BUSINESS INSIGHTS
# =========================================================

st.markdown("---")
st.markdown("### What the numbers tell us")

insight1, insight2 = st.columns(2)

with insight1:

    st.info(
        f"**Strongest cumulative performance: {best_performer}**\n\n"
        f"It recorded a historical cumulative return of "
        f"{metrics.loc[best_performer, 'Cumulative Return']:+.2%}."
    )

with insight2:

    st.info(
        f"**Lowest historical volatility: {lowest_volatility}**\n\n"
        f"Its annualized volatility was "
        f"{metrics.loc[lowest_volatility, 'Annualized Volatility']:.2%}."
    )

st.markdown(
    """
    **How to interpret the results**

    - Higher cumulative return indicates stronger price performance over the selected period.
    - Higher annualized return represents a higher compounded historical growth rate.
    - Higher volatility means greater historical price fluctuations.
    - A higher Sharpe ratio indicates better historical excess return per unit of risk.
    - These results depend on the selected dates and risk-free rate.
    """
)

# =========================================================
# DOWNLOAD REPORT
# =========================================================

st.markdown("---")
st.markdown("### Export comparison report")

download_data = metrics.copy()

st.download_button(
    "↓ Download comparison metrics (CSV)",
    data=download_data.to_csv().encode("utf-8"),
    file_name="FinSight_Stock_Comparison.csv",
    mime="text/csv",
    use_container_width=False,
)

st.caption(
    "Methodology: Prices use adjusted daily closing data. "
    "Annualized return uses calendar-day CAGR. "
    "Annualized volatility uses daily return standard deviation × √252. "
    "Sharpe ratio uses daily excess returns and annualizes by √252. "
    "Price-only returns exclude transaction costs and taxes."
)

st.caption(
    "Historical performance does not predict future returns. "
    "This platform is for educational and analytical purposes, "
    "not investment advice."
)

show_footer()
