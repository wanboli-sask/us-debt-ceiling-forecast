
CREATE TABLE IF NOT EXISTS daily_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL UNIQUE,
    debt_trillions REAL,
    cash_billions REAL,
    x_date_estimate TEXT,
    x_date_p10 TEXT,
    x_date_p90 TEXT,
    sentiment_score REAL,
    spx_close REAL,
    tlt_close REAL,
    vix_close REAL,
    dgs10 REAL,
    risk_level TEXT,
    delta_report TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weight_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_date TEXT NOT NULL,
    w_historical REAL,
    w_sentiment REAL,
    w_microstructure REAL,
    w_source TEXT,
    mode TEXT,
    hybrid_blend REAL,
    pred_spx REAL,
    actual_spx REAL,
    mae_historical REAL,
    mae_sentiment REAL,
    mae_microstructure REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pred_date TEXT NOT NULL,
    vote_date TEXT,
    asset TEXT,
    day_offset INTEGER,
    pred_value REAL,
    layer TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
