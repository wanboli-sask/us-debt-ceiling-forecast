#!/usr/bin/env python3
"""Build data/historical_votes.json from CRS dates + yfinance market metrics."""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.market_client import compute_window_metrics

# CRS R41814 + BPC X-date timeline (2000-2025 key debt-limit episodes)
EVENTS = [
    {
        "year": 2002, "limit_hit_date": "2002-02-20", "x_date": "2002-06-28",
        "vote_date": "2002-06-28", "days_to_deadline": 0,
        "party_control": {"president": "R", "house": "R", "senate": "D"},
        "resolution_type": "increase",
    },
    {
        "year": 2003, "limit_hit_date": "2003-02-20", "x_date": "2003-05-27",
        "vote_date": "2003-05-27", "days_to_deadline": 0,
        "party_control": {"president": "R", "house": "R", "senate": "R"},
        "resolution_type": "increase",
    },
    {
        "year": 2008, "limit_hit_date": "2008-03-05", "x_date": "2008-07-30",
        "vote_date": "2008-07-30", "days_to_deadline": 0,
        "party_control": {"president": "R", "house": "D", "senate": "D"},
        "resolution_type": "increase",
    },
    {
        "year": 2010, "limit_hit_date": "2010-02-04", "x_date": "2010-08-02",
        "vote_date": "2010-02-12", "days_to_deadline": 171,
        "party_control": {"president": "D", "house": "D", "senate": "D"},
        "resolution_type": "increase",
    },
    {
        "year": 2011, "limit_hit_date": "2011-05-16", "x_date": "2011-08-02",
        "vote_date": "2011-08-02", "days_to_deadline": 0,
        "party_control": {"president": "D", "house": "R", "senate": "D"},
        "resolution_type": "increase",
    },
    {
        "year": 2013, "limit_hit_date": "2013-05-19", "x_date": "2013-10-17",
        "vote_date": "2013-10-17", "days_to_deadline": 0,
        "party_control": {"president": "D", "house": "R", "senate": "D"},
        "resolution_type": "suspend_cr",
    },
    {
        "year": 2014, "limit_hit_date": "2014-03-15", "x_date": "2014-10-17",
        "vote_date": "2014-02-15", "days_to_deadline": 244,
        "party_control": {"president": "D", "house": "R", "senate": "D"},
        "resolution_type": "suspend",
    },
    {
        "year": 2015, "limit_hit_date": "2015-03-16", "x_date": "2015-11-03",
        "vote_date": "2015-11-02", "days_to_deadline": 1,
        "party_control": {"president": "D", "house": "R", "senate": "R"},
        "resolution_type": "suspend",
    },
    {
        "year": 2017, "limit_hit_date": "2017-03-16", "x_date": "2017-11-01",
        "vote_date": "2017-09-08", "days_to_deadline": 54,
        "party_control": {"president": "R", "house": "R", "senate": "R"},
        "resolution_type": "suspend_cr",
    },
    {
        "year": 2018, "limit_hit_date": "2018-03-02", "x_date": "2018-03-15",
        "vote_date": "2018-02-09", "days_to_deadline": 34,
        "party_control": {"president": "R", "house": "R", "senate": "R"},
        "resolution_type": "suspend",
    },
    {
        "year": 2019, "limit_hit_date": "2019-03-02", "x_date": "2019-09-01",
        "vote_date": "2019-08-02", "days_to_deadline": 30,
        "party_control": {"president": "R", "house": "D", "senate": "R"},
        "resolution_type": "suspend",
    },
    {
        "year": 2021, "limit_hit_date": "2021-08-01", "x_date": "2021-10-18",
        "vote_date": "2021-10-14", "days_to_deadline": -4,
        "party_control": {"president": "D", "house": "D", "senate": "D"},
        "resolution_type": "increase",
        "event_id": "2021_oct",
    },
    {
        "year": 2021, "limit_hit_date": "2021-10-18", "x_date": "2021-12-15",
        "vote_date": "2021-12-16", "days_to_deadline": -1,
        "party_control": {"president": "D", "house": "D", "senate": "D"},
        "resolution_type": "increase",
        "event_id": "2021_dec",
    },
    {
        "year": 2023, "limit_hit_date": "2023-01-19", "x_date": "2023-06-05",
        "vote_date": "2023-06-03", "days_to_deadline": 2,
        "party_control": {"president": "D", "house": "R", "senate": "D"},
        "resolution_type": "suspend",
    },
    {
        "year": 2025, "limit_hit_date": "2025-01-02", "x_date": "2025-07-04",
        "vote_date": "2025-07-04", "days_to_deadline": 0,
        "party_control": {"president": "R", "house": "R", "senate": "R"},
        "resolution_type": "increase",
    },
]

OUTPUT = ROOT / "data" / "historical_votes.json"


def build():
    records = []
    for ev in EVENTS:
        label = ev.get("event_id", str(ev["year"]))
        print(f"Fetching metrics for {label} vote {ev['vote_date']}...")
        metrics = compute_window_metrics(ev["vote_date"], window=15)
        record = {**ev, **metrics}
        records.append(record)

    records.sort(key=lambda r: r["vote_date"])
    OUTPUT.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {OUTPUT}")


if __name__ == "__main__":
    build()
