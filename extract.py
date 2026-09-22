from datetime import datetime, timezone
import pandas as pd
import yfinance as yf
from db_utils import get_engine

TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN"]
PERIOD = "3mo"

def extract_ticker(ticker: str) -> pd.DataFrame:
    hist = yf.Ticker(ticker).history(period=PERIOD)
    if hist.empty:
        print(f"No data for {ticker}")
        return pd.DataFrame()

    hist = hist.reset_index()
    return pd.DataFrame({
        "ticker": ticker,
        "trade_date": hist["Date"].dt.date,
        "open": hist["Open"],
        "high": hist["High"],
        "low": hist["Low"],
        "close": hist["Close"],
        "volume": hist["Volume"],
        "ingested_at": datetime.now(timezone.utc),
    })

def run():
    engine = get_engine()
    total = 0
    for ticker in TICKERS:
        df = extract_ticker(ticker)
        if df.empty:
            continue
        df.to_sql("raw_prices", engine, if_exists="append", index=False)
        total += len(df)
        print(f"Loaded {len(df)} rows for {ticker}")
    print(f"Done: {total} rows written")

if __name__ == "__main__":
    run()