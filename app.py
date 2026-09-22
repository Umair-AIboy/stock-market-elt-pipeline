import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="Stock Market Warehouse", layout="wide", page_icon="📈")

CARD_CSS = """
<style>
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

h1, .stCaption, .stMarkdown h1 {
    text-align: center !important;
}
[data-testid="stAppViewContainer"] .main .block-container {
    animation: fadeIn 0.6s ease-out;
}

.kpi-card {
    background: #FFFFFF;
    border: 1px solid #111111;
    border-radius: 14px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    animation: fadeInUp 0.5s ease-out backwards;
}
.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}
.kpi-label {
    color: #555555;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 28px;
    font-weight: 800;
    color: #111111;
}
.kpi-delta-up { color: #16A34A; font-size: 14px; font-weight: 700; }
.kpi-delta-down { color: #DC2626; font-size: 14px; font-weight: 700; }

[data-testid="column"]:nth-child(1) .kpi-card { animation-delay: 0.05s; }
[data-testid="column"]:nth-child(2) .kpi-card { animation-delay: 0.15s; }
[data-testid="column"]:nth-child(3) .kpi-card { animation-delay: 0.25s; }
[data-testid="column"]:nth-child(4) .kpi-card { animation-delay: 0.35s; }

.ticker-title {
    text-align: center;
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 4px;
    animation: fadeInUp 0.5s ease-out;
}
</style>
"""
st.markdown(CARD_CSS, unsafe_allow_html=True)


@st.cache_resource
def get_engine():
    host = os.getenv("STOCKDB_HOST", "localhost")
    return create_engine(f"postgresql+psycopg2://airflow:airflow@{host}:5432/stockdata")


@st.cache_data(ttl=300)
def load_tickers(_engine):
    return pd.read_sql("SELECT DISTINCT ticker FROM mart_daily_summary ORDER BY ticker", _engine)["ticker"].tolist()


@st.cache_data(ttl=300)
def load_ticker_detail(_engine, ticker):
    query = """
        SELECT s.ticker, s.trade_date, s.open, s.high, s.low, s.close, s.volume,
               m.ma_20, m.ma_50, m.daily_pct_change, m.trend_since_start
        FROM staging_prices s
        JOIN mart_daily_summary m ON s.ticker = m.ticker AND s.trade_date = m.trade_date
        WHERE s.ticker = %(t)s
        ORDER BY s.trade_date
    """
    return pd.read_sql(query, _engine, params={"t": ticker})


@st.cache_data(ttl=300)
def load_all_latest(_engine):
    query = """
        SELECT ticker, trade_date, close, daily_pct_change, trend_since_start
        FROM mart_daily_summary
        WHERE trade_date = (SELECT MAX(trade_date) FROM mart_daily_summary)
        ORDER BY daily_pct_change DESC NULLS LAST
    """
    return pd.read_sql(query, _engine)


@st.cache_data(ttl=300)
def load_all_history(_engine, tickers):
    query = "SELECT ticker, trade_date, close FROM mart_daily_summary WHERE ticker = ANY(%(tickers)s) ORDER BY trade_date"
    return pd.read_sql(query, _engine, params={"tickers": tickers})


def kpi_card(label, value, delta=None):
    delta_html = ""
    if delta is not None:
        cls = "kpi-delta-up" if delta >= 0 else "kpi-delta-down"
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = f'<div class="{cls}">{arrow} {abs(delta):.2f}%</div>'
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)


engine = get_engine()
tickers = load_tickers(engine)

if not tickers:
    st.warning("No data yet. Trigger the DAG in Airflow first.")
    st.stop()

st.sidebar.title("📈 Stock Warehouse")
st.sidebar.caption("Served from Postgres marts, populated by Airflow.")
view = st.sidebar.radio("View", ["Single ticker", "Compare tickers", "Market leaderboard"])

if view == "Single ticker":
    ticker = st.sidebar.selectbox("Ticker", tickers)
    df = load_ticker_detail(engine, ticker)
    df["trade_date"] = pd.to_datetime(df["trade_date"])

    date_range = st.sidebar.slider(
        "Date range",
        min_value=df["trade_date"].min().to_pydatetime(),
        max_value=df["trade_date"].max().to_pydatetime(),
        value=(df["trade_date"].min().to_pydatetime(), df["trade_date"].max().to_pydatetime()),
    )
    df = df[(df["trade_date"] >= date_range[0]) & (df["trade_date"] <= date_range[1])]

    st.markdown(f'<div class="ticker-title">{ticker}</div>', unsafe_allow_html=True)
    latest = df.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Latest close", f"${latest['close']:.2f}", latest['daily_pct_change'])
    with c2: kpi_card("20-day MA", f"${latest['ma_20']:.2f}" if pd.notna(latest['ma_20']) else "n/a")
    with c3: kpi_card("50-day MA", f"${latest['ma_50']:.2f}" if pd.notna(latest['ma_50']) else "n/a")
    with c4: kpi_card("Trend", latest["trend_since_start"])

    st.markdown("###")

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["trade_date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name="Price", increasing_line_color="#16A34A", decreasing_line_color="#DC2626",
    ))
    fig.add_trace(go.Scatter(x=df["trade_date"], y=df["ma_20"], name="MA 20", line=dict(color="#2563EB", width=1.5, dash="dot")))
    fig.add_trace(go.Scatter(x=df["trade_date"], y=df["ma_50"], name="MA 50", line=dict(color="#D97706", width=1.5, dash="dot")))
    fig.update_layout(
        template="plotly_white", height=480, xaxis_rangeslider_visible=False,
        margin=dict(t=20, b=20), plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig, use_container_width=True)

    vol_fig = go.Figure()
    colors = ["#16A34A" if c >= o else "#DC2626" for o, c in zip(df["open"], df["close"])]
    vol_fig.add_trace(go.Bar(x=df["trade_date"], y=df["volume"], marker_color=colors, name="Volume"))
    vol_fig.update_layout(template="plotly_white", height=180, margin=dict(t=10, b=20), plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
    st.plotly_chart(vol_fig, use_container_width=True)

    with st.expander("Underlying data"):
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False).encode(), f"{ticker}_data.csv", "text/csv")

elif view == "Compare tickers":
    st.markdown('<div class="ticker-title">Compare tickers</div>', unsafe_allow_html=True)
    selected = st.sidebar.multiselect("Tickers to compare", tickers, default=tickers[:3])
    if not selected:
        st.info("Pick at least one ticker from the sidebar.")
        st.stop()

    hist = load_all_history(engine, selected)
    hist["trade_date"] = pd.to_datetime(hist["trade_date"])

    fig = go.Figure()
    for tk in selected:
        sub = hist[hist["ticker"] == tk].sort_values("trade_date")
        if sub.empty:
            continue
        base = sub["close"].iloc[0]
        normalized = (sub["close"] / base - 1) * 100
        fig.add_trace(go.Scatter(x=sub["trade_date"], y=normalized, name=tk, mode="lines"))

    fig.update_layout(
        template="plotly_white", height=500, title="% return since window start",
        yaxis_title="% change", plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.markdown('<div class="ticker-title">Market leaderboard</div>', unsafe_allow_html=True)
    latest = load_all_latest(engine)
    if not latest.empty:
        st.caption(f"As of {latest['trade_date'].iloc[0]}")

    cols = st.columns(3)
    for i, row in latest.iterrows():
        with cols[i % 3]:
            kpi_card(row["ticker"], f"${row['close']:.2f}", row["daily_pct_change"])

    st.markdown("###")
    st.dataframe(latest, use_container_width=True, hide_index=True)