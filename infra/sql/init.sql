CREATE TABLE IF NOT EXISTS transactions (
  event_id TEXT PRIMARY KEY,
  event_ts TIMESTAMPTZ NOT NULL,
  customer_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('BUY','SELL')),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  price NUMERIC(18,4) NOT NULL CHECK (price > 0),
  source_file TEXT,
  ingested_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_customer_ts
  ON transactions(customer_id, event_ts);

CREATE INDEX IF NOT EXISTS idx_transactions_symbol_ts
  ON transactions(symbol, event_ts);