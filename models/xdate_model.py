from datetime import datetime, timedelta
import json
from pathlib import Path

from config import (
    BASE_DIR, DAILY_DEFICIT_DOLLARS, DEBT_LIMIT_DOLLARS,
    EM_HEADROOM_BILLIONS, BUFFER_BILLIONS,
)

BASELINE_PATH = BASE_DIR / "data" / "baseline_2027.json"


def _load_baseline():
    with open(BASELINE_PATH) as f:
        return json.load(f)


def project_x_date(
    debt_dollars: float,
    cash_billions: float,
    deficit_multiplier: float = 1.0,
    em_billions: float = None,
) -> dict:
    em = (em_billions or EM_HEADROOM_BILLIONS) * 1e9
    cash = cash_billions * 1e9
    buffer = BUFFER_BILLIONS * 1e9
    daily_burn = DAILY_DEFICIT_DOLLARS * deficit_multiplier

    headroom = max(DEBT_LIMIT_DOLLARS - debt_dollars, 0)
    resources = cash + em + headroom - buffer
    days_to_x = max(int(resources / daily_burn), 1) if daily_burn > 0 else 180

    today = datetime.now().date()
    p50 = today + timedelta(days=days_to_x)
    p10 = today + timedelta(days=max(days_to_x - 45, 1))
    p90 = today + timedelta(days=days_to_x + 45)

    baseline = _load_baseline()
    baseline_x = datetime.strptime(baseline["x_date"], "%Y-%m-%d").date()
    delta_days = (p50 - baseline_x).days

    risk = "low"
    if days_to_x < 120:
        risk = "medium"
    if days_to_x < 60:
        risk = "high"
    if days_to_x < 30:
        risk = "extreme"

    return {
        "x_date_p50": p50.isoformat(),
        "x_date_p10": p10.isoformat(),
        "x_date_p90": p90.isoformat(),
        "days_to_x": days_to_x,
        "delta_from_baseline": delta_days,
        "headroom_billions": headroom / 1e9,
        "resources_billions": resources / 1e9,
        "risk_level": risk,
        "baseline_x_date": baseline["x_date"],
        "limit_hit_date": baseline["limit_hit_date"],
        "limit_hit_range": baseline["limit_hit_range"],
    }
