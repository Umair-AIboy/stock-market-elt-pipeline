CREATE TABLE IF NOT EXISTS raw_prices (
    id          BIGSERIAL PRIMARY KEY,
    ticker      TEXT NOT NULL,
    trade_date  DATE NOT NULL,
    open        NUMERIC,
    high        NUMERIC,
    low         NUMERIC,
    close       NUMERIC,
    volume      BIGINT,
    ingested_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staging_prices (
    ticker      TEXT NOT NULL,
    trade_date  DATE NOT NULL,
    open        NUMERIC,
    high        NUMERIC,
    low         NUMERIC,
    close       NUMERIC,
    volume      BIGINT,
    PRIMARY KEY (ticker, trade_date)
);

CREATE TABLE IF NOT EXISTS mart_daily_summary (
    ticker              TEXT NOT NULL,
    trade_date          DATE NOT NULL,
    close               NUMERIC,
    ma_20               NUMERIC,
    ma_50               NUMERIC,
    daily_pct_change    NUMERIC,
    trend_since_start   TEXT,
    PRIMARY KEY (ticker, trade_date)
);