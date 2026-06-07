#!/usr/bin/env python3
"""Verify daily update pipeline and FRED configuration."""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import DB_PATH
from jobs.daily_update import run_daily_update
from services.fred_client import get_fred_status


def main():
    status = get_fred_status()
    print("FRED configured:", status["configured"])
    print("FRED connected:", status["connected"])
    print("EN:", status["message_en"])
    print("ZH:", status["message_zh"])
    print("--- running daily update ---")
    result = run_daily_update()
    snap = result["snapshot"]
    print("Snapshot date:", snap["snapshot_date"])
    print("Debt (T):", snap.get("debt_trillions"))
    print("Cash/TGA (B):", snap.get("cash_billions"))
    print("DGS10:", snap.get("dgs10"))
    print("X-date:", snap.get("x_date_estimate"))
    print("Alerts:", json.dumps(result.get("alerts", []), indent=2))

    conn = sqlite3.connect(DB_PATH)
    n_snap = conn.execute("SELECT COUNT(*) FROM daily_snapshots").fetchone()[0]
    n_wt = conn.execute("SELECT COUNT(*) FROM weight_history").fetchone()[0]
    conn.close()
    print("DB snapshots:", n_snap)
    print("DB weight_history:", n_wt)
    ok = bool(snap.get("debt_trillions") and snap.get("x_date_estimate"))
    print("VERIFY:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
