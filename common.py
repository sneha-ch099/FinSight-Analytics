from datetime import date, timedelta
from turtle import color

from matplotlib.pyplot import fill
import pandas as pd
import streamlit as st

from finance_functions import (
    download_prices,
    fetch_latest_quotes,
    calculate_metrics,
    build_insights,
    normalize_prices,
    daily_returns,
    moving_average,
)

# =========================================================
# FINSIGHT ANALYTICS - SHARED CONFIGURATION
# =========================================================

st_theme = {
    "BG": "#07111F",
    "PANEL": "#0D1B2A",
    "BORDER": "#1D3A50",
    "TEXT": "#EDF6FF",
    "MUTED": "#91A9BE",
    "TEAL": "#19D3C5",
    "BLUE": "#48A9FF",
    "GREEN": "#27D6A0",
    "PURPLE": "#A78BFA",
    "ORANGE": "#F6B65B",
    "RED": "#FF667D",
}

BG = st_theme["BG"]
PANEL = st_theme["PANEL"]
BORDER = st_theme["BORDER"]
TEXT = st_theme["TEXT"]
MUTED = st_theme["MUTED"]
TEAL = st_theme["TEAL"]
BLUE = st_theme["BLUE"]
GREEN = st_theme["GREEN"]
PURPLE = st_theme["PURPLE"]
ORANGE = st_theme["ORANGE"]
RED = st_theme["RED"]

PALETTE = [
    BLUE, GREEN, ORANGE, PURPLE, "#FF7EB6", TEAL,
    "#B5D66B", "#F28C52", "#7DD3FC", "#C4A1FF",
    "#F9A8D4", "#A3E635",
]

STOCKS = {
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "Reliance Industries": "RELIANCE.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "ITC": "ITC.NS",
    "Larsen & Toubro": "LT.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "NTPC": "NTPC.NS",
    "Power Grid": "POWERGRID.NS",
}

RISK_FREE_RATE = 0.065
TRADING_DAYS = 252


# =========================================================
# SHARED DATA LOADING
# =========================================================

@st.cache_data(ttl=300, show_spinner=False)
def get_stock_prices(stock_items, start_date, end_date):
    """Download historical adjusted closing prices."""
    return download_prices(
        dict(stock_items),
        start_date.isoformat(),
        end_date.isoformat(),
    )


@st.cache_data(ttl=300, show_spinner=False)
def get_latest_quotes(stock_items):
    """Fetch latest available daily quote snapshots."""
    return fetch_latest_quotes(dict(stock_items))


def prepare_stock_data(prices):
    """Clean price data without filling dates before a stock's first observation."""
    prices = prices.copy()
    prices = prices.sort_index()
    prices = prices[~prices.index.duplicated(keep="last")]
    prices = prices.dropna(how="all")

    for column in prices.columns:
        first_valid = prices[column].first_valid_index()

        if first_valid is not None:
            prices.loc[first_valid:, column] = (
                prices.loc[first_valid:, column].ffill()
            )

    return prices


def get_analysis_metrics(prices, risk_free_rate=RISK_FREE_RATE):
    """Calculate return, volatility and Sharpe metrics."""
    return calculate_metrics(
        prices,
        risk_free_rate=risk_free_rate,
    )


# =========================================================
# FORMATTING
# =========================================================

def format_percent(value, decimals=2):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value * 100:+.{decimals}f}%"


def format_number(value, decimals=2):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}"


def format_currency(value, decimals=2):
    if value is None or pd.isna(value):
        return "N/A"
    return f"₹{value:,.{decimals}f}"


def format_quote_change(value):
    """
    fetch_latest_quotes returns change_pct in percentage points.
    Example: 2.5 means +2.5%, not 0.025.
    """
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:+.2f}%"


def make_metrics_table(metrics):
    output = metrics.reset_index().copy()

    percentage_columns = [
        "Cumulative Return",
        "Annualized Return",
        "Annualized Volatility",
    ]

    for column in percentage_columns:
        if column in output.columns:
            output[column] = output[column].map(format_percent)

    number_columns = [
        "First Close",
        "Last Close",
        "Sharpe Ratio",
    ]

    for column in number_columns:
        if column in output.columns:
            output[column] = output[column].map(format_number)

    return output


# =========================================================
# CHART DESIGN
# =========================================================


def apply_chart_theme(fig, height=370, y_title=None, title=None):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, family="Arial", size=11),
        margin=dict(l=25, r=20, t=75, b=30),
        height=height,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.10,
            x=0.02,
            font=dict(size=10),
        ),
        title=dict(
            text=title or "",
            font=dict(size=15, color=TEXT),
            x=0.02,
            y=0.98,
        ),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(145,169,190,.10)",
        zeroline=False,
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(145,169,190,.10)",
        zeroline=False,
        title=y_title,
    )
    fig.update_layout(legend_title_text="")
    return fig



# =========================================================
# SHARED DESIGN
# =========================================================


def apply_global_style():
    st.markdown(
        f"""
        <style>

        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');

        /* STOCK SELECTION TAGS */
        [data-baseweb="tag"] {{
            background-color: rgba(25, 211, 197, 0.16) !important;
            border: 1px solid rgba(25, 211, 197, 0.35) !important;
        }}

        [data-baseweb="tag"] span {{
            color: #19D3C5 !important;
        }}

        [data-baseweb="tag"] svg {{
            fill: #19D3C5 !important;
        }}

        /* MAIN BACKGROUND */
        .stApp {{
            background:
                radial-gradient(ellipse at 10% 0%, rgba(25,211,197,.07), transparent 30%),
                #07111F;
            color: {TEXT};
            font-family: 'DM Sans', sans-serif;
        }}

        /* TOP HEADER */
        [data-testid="stHeader"] {{
            background: #07111F;
            height: 3.5rem;
        }}

        /* MAIN CONTENT SPACING */
        .block-container {{
            max-width: 1500px;
            padding-top: 3.5rem;
            padding-bottom: 3rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }}

        /* SIDEBAR */
        [data-testid="stSidebar"] {{
            background: #0A1928;
            border-right: 1px solid {BORDER};
        }}

        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 1.5rem;
        }}

        /* TYPOGRAPHY */
        h1, h2, h3, h4 {{
            font-family: 'Manrope', sans-serif !important;
            color: {TEXT} !important;
        }}

        p, label {{
            font-family: 'DM Sans', sans-serif;
        }}

        /* BRAND */
        .brand {{
            display: flex;
            align-items: center;
            gap: 13px;
            padding: 0 0 22px;
        }}

        .brand-mark {{
            width: 46px;
            height: 46px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(25,211,197,.12);
            border: 1px solid rgba(25,211,197,.35);
            color: {TEAL};
            font-size: 27px;
            font-weight: 800;
        }}

        .brand-name {{
            font-family: 'Manrope', sans-serif;
            font-size: 24px;
            font-weight: 800;
            color: {TEXT};
        }}

        .brand-name span {{
            color: {TEAL};
        }}

        .brand-sub {{
            color: {MUTED};
            font-size: 10px;
            letter-spacing: 1.8px;
            text-transform: uppercase;
        }}

        /* HERO */
        .hero {{
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 34px 38px;
            margin: 12px 0 30px;
            background:
                radial-gradient(circle at 85% 20%, rgba(25,211,197,.12), transparent 30%),
                linear-gradient(120deg, #10263A, #0A1727);
        }}

        .eyebrow {{
            color: {TEAL};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}

        .hero-title {{
            font-family: 'Manrope', sans-serif;
            font-size: clamp(30px, 3.2vw, 44px);
            font-weight: 800;
            line-height: 1.2;
            margin: 13px 0;
            color: {TEXT};
        }}

        .hero-title span {{
            color: {TEAL};
        }}

        .hero-copy {{
            color: #B3C5D7;
            font-size: 14px;
            line-height: 1.8;
            max-width: 760px;
        }}

        .hero-chip {{
            display: inline-block;
            margin-top: 18px;
            padding: 8px 13px;
            border: 1px solid rgba(25,211,197,.3);
            border-radius: 30px;
            color: {TEAL};
            font-size: 10px;
            letter-spacing: 1px;
        }}

        /* SECTION HEADINGS */
        .section-heading {{
            font-family: 'Manrope', sans-serif;
            font-size: 19px;
            font-weight: 800;
            margin: 28px 0 5px;
            color: {TEXT};
        }}

        .section-sub {{
            color: {MUTED};
            font-size: 12px;
            line-height: 1.7;
            margin-bottom: 17px;
        }}

        /* KPI CARDS */
        .kpi-card {{
            min-height: 120px;
            padding: 19px;
            border: 1px solid {BORDER};
            border-radius: 15px;
            background: #0D1B2A;
        }}

        .kpi-label {{
            color: {MUTED};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: .7px;
        }}

        .kpi-value {{
            font-family: 'Manrope', sans-serif;
            font-size: 21px;
            font-weight: 800;
            margin-top: 13px;
            overflow-wrap: anywhere;
        }}

        .kpi-detail {{
            color: {TEAL};
            font-size: 11px;
            margin-top: 7px;
        }}

        /* INSIGHT CARDS */
        .insight {{
            padding: 17px;
            border: 1px solid {BORDER};
            border-radius: 14px;
            background: #0D1B2A;
            margin: 8px 0;
            min-height: 105px;
        }}

        .insight-title {{
            color: {TEXT};
            font-size: 13px;
            font-weight: 700;
        }}

        .insight-copy {{
            color: {MUTED};
            font-size: 12px;
            line-height: 1.7;
            margin-top: 9px;
        }}

        /* CHARTS */
        div[data-testid="stPlotlyChart"] {{
            border: 1px solid {BORDER};
            border-radius: 15px;
            background: #0D1B2A;
            padding: 10px;
            margin-bottom: 15px;
        }}

        /* TABLES */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {BORDER};
            border-radius: 12px;
            overflow: hidden;
        }}

        /* BUTTONS */
        div.stButton > button,
        div.stDownloadButton > button {{
            border-radius: 10px;
            border: 1px solid {BORDER};
            background: #10263A;
            color: {TEXT};
            font-weight: 600;
            min-height: 42px;
        }}

        div.stButton > button[kind="primary"] {{
            background: {TEAL};
            color: #07111F;
            border: none;
        }}

        /* INPUTS */
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {{
            background: #0B1B2A;
            border-color: {BORDER};
            border-radius: 9px;
        }}

        /* DIVIDERS */
        hr {{
            border-color: {BORDER};
            margin: 25px 0;
        }}

        /* FOOTER */
        footer {{
            visibility: hidden;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )




# =========================================================
# REUSABLE UI COMPONENTS
# =========================================================

def show_brand():
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">↗</div>
            <div>
                <div class="brand-name">FinSight <span>Analytics</span></div>
                <div class="brand-sub">Indian equity intelligence platform</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_hero(eyebrow, title, highlighted_title, description, chip=""):
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">{eyebrow}</div>
            <div class="hero-title">{title}<br>
                <span>{highlighted_title}</span>
            </div>
            <p class="hero-copy">{description}</p>
            <div class="hero-chip">{chip}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_metric_card(label, value, detail, color=TEAL):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value" style="color:{color}">{value}</div>
            <div class="kpi-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_footer():
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align:center;color:#91A9BE;font-size:11px;line-height:1.8">
            <b style="color:#19D3C5">FINSIGHT ANALYTICS</b>
            · Educational financial analytics platform<br>
            Historical prices and derived metrics are for educational analysis,
            not investment advice. Quote snapshots may be delayed.
            Price-only returns exclude dividends, taxes and transaction costs.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# SHARED DATE RANGE
# =========================================================

def date_range_from_period(period):
    today = date.today()

    days = {
        "1M": 30,
        "3M": 90,
        "6M": 182,
        "1Y": 365,
        "3Y": 1095,
        "5Y": 1825,
    }

    if period not in days:
        period = "1Y"

    return today - timedelta(days=days[period]), today
