"""US Treasury constant-maturity yields from FRED."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from services.fred_client import fetch_series

YIELD_KEYS = ("dgs2", "dgs5", "dgs10", "dgs30")

YIELD_META = {
    "dgs2": {"fred": "DGS2", "label_en": "2Y", "label_zh": "2年期", "fallback": 4.5},
    "dgs5": {"fred": "DGS5", "label_en": "5Y", "label_zh": "5年期", "fallback": 4.3},
    "dgs10": {"fred": "DGS10", "label_en": "10Y", "label_zh": "10年期", "fallback": 4.2},
    "dgs30": {"fred": "DGS30", "label_en": "30Y", "label_zh": "30年期", "fallback": 4.5},
}

HISTORY_DAYS = 120
CHANGE_WINDOW = 15


def _latest_value(series: pd.Series, fallback: float) -> tuple[float, str]:
    if series.empty:
        return fallback, "fallback"
    return float(series.iloc[-1]), "fred"


def _change_bps(series: pd.Series, window: int = CHANGE_WINDOW) -> float:
    if series.empty or len(series) <= window:
        return 0.0
    return float((series.iloc[-1] - series.iloc[-1 - window]) * 100)


def _latest_observation_date(histories: dict[str, pd.Series]) -> str | None:
    dates: list[pd.Timestamp] = []
    for series in histories.values():
        if not series.empty:
            dates.append(pd.Timestamp(series.index[-1]))
    if not dates:
        return None
    return max(dates).strftime("%Y-%m-%d")


def get_yields_summary() -> dict:
    latest: dict[str, float] = {}
    sources: dict[str, str] = {}
    histories: dict[str, pd.Series] = {}
    change_15d_bps: dict[str, float] = {}

    for key in YIELD_KEYS:
        meta = YIELD_META[key]
        history = fetch_series(meta["fred"], days=HISTORY_DAYS)
        histories[key] = history
        value, source = _latest_value(history, meta["fallback"])
        latest[key] = value
        sources[key] = source
        change_15d_bps[key] = _change_bps(history)

    spread_2s10s_bps = (latest["dgs10"] - latest["dgs2"]) * 100
    spread_10s30s_bps = (latest["dgs30"] - latest["dgs10"]) * 100

    curve = [
        {
            "key": key,
            "maturity_en": YIELD_META[key]["label_en"],
            "maturity_zh": YIELD_META[key]["label_zh"],
            "yield_pct": latest[key],
            "change_15d_bps": change_15d_bps[key],
            "source": sources[key],
        }
        for key in YIELD_KEYS
    ]

    any_fred = any(src == "fred" for src in sources.values())
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0)

    return {
        "latest": latest,
        "sources": sources,
        "histories": histories,
        "change_15d_bps": change_15d_bps,
        "spread_2s10s_bps": spread_2s10s_bps,
        "spread_10s30s_bps": spread_10s30s_bps,
        "curve": curve,
        "source": "fred" if any_fred else "fallback",
        "as_of_date": _latest_observation_date(histories),
        "fetched_at": fetched_at.isoformat(),
        "fetched_at_display": fetched_at.strftime("%Y-%m-%d %H:%M UTC"),
    }
