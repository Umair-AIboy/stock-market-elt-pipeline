-- Step A: raw -> staging, keeping only the latest ingest per (ticker, date)
INSERT INTO staging_prices (ticker, trade_date, open, high, low, close, volume)
SELECT DISTINCT ON (ticker, trade_date)
    ticker, trade_date, open, high, low, close, volume
FROM raw_prices
WHERE close IS NOT NULL
ORDER BY ticker, trade_date, ingested_at DESC
ON CONFLICT (ticker, trade_date) DO UPDATE SET
    open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
    close = EXCLUDED.close, volume = EXCLUDED.volume;

-- Step B: staging -> mart, computing moving averages and trend
INSERT INTO mart_daily_summary (ticker, trade_date, close, ma_20, ma_50, daily_pct_change, trend_since_start)
SELECT
    ticker,
    trade_date,
    close,
    AVG(close) OVER (PARTITION BY ticker ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma_20,
    AVG(close) OVER (PARTITION BY ticker ORDER BY trade_date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS ma_50,
    ROUND(100.0 * (close - LAG(close) OVER (PARTITION BY ticker ORDER BY trade_date))
          / NULLIF(LAG(close) OVER (PARTITION BY ticker ORDER BY trade_date), 0), 2) AS daily_pct_change,
    CASE
        WHEN close > FIRST_VALUE(close) OVER (PARTITION BY ticker ORDER BY trade_date) THEN 'Uptrend'
        WHEN close < FIRST_VALUE(close) OVER (PARTITION BY ticker ORDER BY trade_date) THEN 'Downtrend'
        ELSE 'Stable'
    END AS trend_since_start
FROM staging_prices
ON CONFLICT (ticker, trade_date) DO UPDATE SET
    close = EXCLUDED.close, ma_20 = EXCLUDED.ma_20, ma_50 = EXCLUDED.ma_50,
    daily_pct_change = EXCLUDED.daily_pct_change, trend_since_start = EXCLUDED.trend_since_start;