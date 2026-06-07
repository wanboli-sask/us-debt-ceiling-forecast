import json
import sqlite3
from datetime import datetime
from pathlib import Path

from config import DB_PATH


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    schema = (Path(__file__).parent / "schema.sql").read_text()
    with get_connection() as conn:
        conn.executescript(schema)
        conn.commit()


def save_snapshot(data: dict):
    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO daily_snapshots
            (snapshot_date, debt_trillions, cash_billions, x_date_estimate,
             x_date_p10, x_date_p90, sentiment_score, spx_close, tlt_close,
             vix_close, dgs10, risk_level, delta_report)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data.get("snapshot_date"),
                data.get("debt_trillions"),
                data.get("cash_billions"),
                data.get("x_date_estimate"),
                data.get("x_date_p10"),
                data.get("x_date_p90"),
                data.get("sentiment_score"),
                data.get("spx_close"),
                data.get("tlt_close"),
                data.get("vix_close"),
                data.get("dgs10"),
                data.get("risk_level"),
                json.dumps(data.get("delta_report", {})),
            ),
        )
        conn.commit()


def save_weight_record(record: dict):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO weight_history
            (record_date, w_historical, w_sentiment, w_microstructure,
             w_source, mode, hybrid_blend, pred_spx, actual_spx,
             mae_historical, mae_sentiment, mae_microstructure)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                record.get("record_date"),
                record.get("w_historical"),
                record.get("w_sentiment"),
                record.get("w_microstructure"),
                record.get("w_source"),
                record.get("mode"),
                record.get("hybrid_blend"),
                record.get("pred_spx"),
                record.get("actual_spx"),
                record.get("mae_historical"),
                record.get("mae_sentiment"),
                record.get("mae_microstructure"),
            ),
        )
        conn.commit()


def get_weight_history(limit: int = 60):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM weight_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_snapshots(limit: int = 30):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM daily_snapshots ORDER BY snapshot_date DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
