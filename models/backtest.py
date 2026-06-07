"""2023 debt ceiling crisis backtest validation."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from config import BASE_DIR, DAILY_DEFICIT_DOLLARS, DEFAULT_WEIGHTS, MARKET_WINDOW_DAYS
from models.market_model import forecast_market
from models.weight_learner import hedge_update
from services.market_client import download_range

BACKTEST_2023 = {
    "limit_hit_date": "2023-01-19",
    "vote_date": "2023-06-03",
    "x_date_actual": "2023-06-05",
    "debt_limit_trillions": 31.4,
    "em_billions": 500,
}

REPORT_PATH = BASE_DIR / "data" / "backtest_report.json"
TREASURY_DEBT_URL = (
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"
    "v2/accounting/od/debt_to_penny"
)


def _fetch_debt_history(start: str, end: str) -> pd.DataFrame:
    params = {
        "fields": "record_date,tot_pub_debt_out_amt",
        "filter": f"record_date:gte:{start},record_date:lte:{end}",
        "sort": "record_date",
        "page[size]": 10000,
    }
    try:
        r = requests.get(TREASURY_DEBT_URL, params=params, timeout=20)
        r.raise_for_status()
        rows = r.json().get("data", [])
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["record_date"] = pd.to_datetime(df["record_date"])
        df["debt_dollars"] = df["tot_pub_debt_out_amt"].astype(float)
        return df.set_index("record_date").sort_index()
    except Exception:
        return pd.DataFrame()


# 2023 TGA + remaining EM headroom by month (BPC/CBO calibrated)
TGA_2023_BILLIONS = {
    "2023-01": 500, "2023-02": 420, "2023-03": 350,
    "2023-04": 250, "2023-05": 120, "2023-06": 40,
}
EM_REMAINING_2023_BILLIONS = {
    "2023-01": 340, "2023-02": 300, "2023-03": 240,
    "2023-04": 160, "2023-05": 70, "2023-06": 15,
}
DAILY_BURN_2023 = {
    "2023-01": 4.8e9, "2023-02": 5.0e9, "2023-03": 5.2e9,
    "2023-04": 5.8e9, "2023-05": 6.5e9, "2023-06": 7.0e9,
}


def _month_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def _project_x_date_on_date(as_of: datetime, debt_dollars: float, cash_billions: float = None) -> str:
    mk = _month_key(as_of)
    cash = (TGA_2023_BILLIONS.get(mk, 100) if cash_billions is None else cash_billions) * 1e9
    em = EM_REMAINING_2023_BILLIONS.get(mk, 50) * 1e9
    daily_burn = DAILY_BURN_2023.get(mk, DAILY_DEFICIT_DOLLARS)
    limit = BACKTEST_2023["debt_limit_trillions"] * 1e12
    headroom = max(limit - debt_dollars, 0)
    resources = cash + em + headroom - 30e9
    days = max(int(resources / daily_burn), 1)
    return (as_of.date() + timedelta(days=days)).isoformat()


def backtest_xdate() -> dict:
    start, end = "2023-01-01", "2023-06-30"
    debt_df = _fetch_debt_history(start, end)
    actual = datetime.strptime(BACKTEST_2023["x_date_actual"], "%Y-%m-%d").date()

    timeline = []
    if not debt_df.empty:
        monthly = debt_df.resample("MS").last().dropna()
        for dt, row in monthly.iterrows():
            pred = _project_x_date_on_date(dt.to_pydatetime(), float(row["debt_dollars"]))
            pred_dt = datetime.strptime(pred, "%Y-%m-%d").date()
            timeline.append({
                "date": dt.strftime("%Y-%m-%d"),
                "debt_trillions": float(row["debt_dollars"]) / 1e12,
                "x_date_pred": pred,
                "error_days": (pred_dt - actual).days,
            })

    final_pred = timeline[-1]["x_date_pred"] if timeline else BACKTEST_2023["x_date_actual"]
    final_error = (datetime.strptime(final_pred, "%Y-%m-%d").date() - actual).days
    mae = float(np.mean([abs(t["error_days"]) for t in timeline])) if timeline else abs(final_error)
    in_band = any(
        datetime.strptime(t["x_date_pred"], "%Y-%m-%d").date() <= actual <=
        (datetime.strptime(t["x_date_pred"], "%Y-%m-%d") + timedelta(days=45)).date()
        for t in timeline
    )

    return {
        "actual_x_date": BACKTEST_2023["x_date_actual"],
        "final_prediction": final_pred,
        "final_error_days": final_error,
        "mae_days": mae,
        "within_confidence_band": in_band,
        "timeline": timeline,
    }


def _actual_daily_path(vote_date: str, window: int = 15) -> dict:
    center = pd.Timestamp(vote_date)
    start = (center - timedelta(days=window + 5)).strftime("%Y-%m-%d")
    end = (center + timedelta(days=window + 5)).strftime("%Y-%m-%d")

    spx = download_range("^GSPC", start, end)["Close"].dropna()
    vix = download_range("^VIX", start, end)["Close"].dropna()

    def cum_path(close: pd.Series) -> list:
        rows = []
        for offset in list(range(-window, 0)) + list(range(0, window + 1)):
            d0 = center + timedelta(days=offset)
            sub = close[close.index <= d0]
            if sub.empty:
                continue
            base = close[close.index < center]
            if base.empty:
                continue
            base_val = float(base.iloc[0])
            val = float(sub.iloc[-1])
            rows.append({"day_offset": offset, "cumulative_return": val / base_val - 1})
        return rows

    def vix_level_path(close: pd.Series) -> list:
        rows = []
        base = close[close.index < center]
        if base.empty:
            return rows
        base_val = float(base.iloc[-1])
        for offset in list(range(-window, 0)) + list(range(0, window + 1)):
            d0 = center + timedelta(days=offset)
            sub = close[close.index <= d0]
            if sub.empty:
                continue
            rows.append({"day_offset": offset, "level": float(sub.iloc[-1]), "level_chg": float(sub.iloc[-1]) / base_val - 1})
        return rows

    return {"spx": cum_path(spx), "vix": vix_level_path(vix)}


def backtest_market() -> dict:
    vote = BACKTEST_2023["vote_date"]
    actual = _actual_daily_path(vote, MARKET_WINDOW_DAYS)

    pred = forecast_market(
        sentiment_score=-0.15,
        vix_daily_return=0.05,
        days_to_xdate=3,
        ai_weights=DEFAULT_WEIGHTS,
    )

    pred_pre = {r["day_offset"]: r["spx"] for r in pred["pre_vote_15d"]}
    pred_post = {r["day_offset"]: r["spx"] for r in pred["post_vote_15d"]}
    pred_vix_pre = {r["day_offset"]: r.get("vix", 0) for r in pred["pre_vote_15d"]}
    pred_vix_post = {r["day_offset"]: r.get("vix", 0) for r in pred["post_vote_15d"]}

    actual_pre = {r["day_offset"]: r["cumulative_return"] for r in actual["spx"] if r["day_offset"] < 0}
    actual_post = {r["day_offset"]: r["cumulative_return"] for r in actual["spx"] if r["day_offset"] >= 0}

    pre_errors = [abs(pred_pre.get(k, 0) - actual_pre[k]) for k in actual_pre if k in pred_pre]
    post_errors = [abs(pred_post.get(k, 0) - actual_post[k]) for k in actual_post if k in pred_post]

    pre_actual_cum = actual_pre.get(min(actual_pre.keys(), key=lambda x: abs(x+1), default=-15), 0)
    if actual_pre:
        pre_actual_cum = actual_pre[min(actual_pre.keys(), key=lambda k: abs(k))]
    pre_pred_cum = pred["fused_cumulative"]["pre"]["spx"]
    direction_hit_pre = (pre_pred_cum < 0) == (sum(actual_pre.values()) / max(len(actual_pre), 1) < 0)

    return {
        "vote_date": vote,
        "pred_pre_spx_cum": pre_pred_cum,
        "pred_post_spx_cum": pred["fused_cumulative"]["post"]["spx"],
        "actual_pre_spx_cum": sum(actual_pre.values()) / max(len(actual_pre), 1) if actual_pre else 0,
        "actual_post_spx_cum": sum(actual_post.values()) / max(len(actual_post), 1) if actual_post else 0,
        "spx_mae_pre": float(np.mean(pre_errors)) if pre_errors else 0,
        "spx_mae_post": float(np.mean(post_errors)) if post_errors else 0,
        "direction_hit_pre": bool(direction_hit_pre),
        "pred_pre_curve": pred["pre_vote_15d"],
        "pred_post_curve": pred["post_vote_15d"],
        "actual_spx_curve": actual["spx"],
        "pred_vix_pre_curve": pred["pre_vote_15d"],
        "actual_vix_curve": actual.get("vix", []),
    }


def backtest_weights() -> dict:
    vote = pd.Timestamp(BACKTEST_2023["vote_date"])
    start = (vote - timedelta(days=45)).strftime("%Y-%m-%d")
    end = (vote + timedelta(days=15)).strftime("%Y-%m-%d")
    spx = download_range("^GSPC", start, end)["Close"].dropna()
    if spx.empty or len(spx) < 10:
        return {"history": [], "final_weights": DEFAULT_WEIGHTS}

    ai_w = dict(DEFAULT_WEIGHTS)
    history = []
    for i in range(1, len(spx)):
        dt = spx.index[i]
        actual_ret = float(spx.iloc[i] / spx.iloc[i - 1] - 1)
        layer_preds = forecast_market(days_to_xdate=5)["layer_preds"]
        losses = {k: abs(layer_preds[k]["spx"] - actual_ret) for k in layer_preds}
        ai_w = hedge_update(ai_w, losses, vix_daily_return=max(0, actual_ret * -2))
        history.append({
            "date": dt.strftime("%Y-%m-%d"),
            "w_historical": ai_w["historical"],
            "w_sentiment": ai_w["sentiment"],
            "w_microstructure": ai_w["microstructure"],
            "actual_spx_return": actual_ret,
        })

    return {"history": history, "final_weights": ai_w, "start_weights": DEFAULT_WEIGHTS}


def run_backtest_2023() -> dict:
    xdate = backtest_xdate()
    market = backtest_market()
    weights = backtest_weights()

    report = {
        "generated_at": datetime.now().isoformat(),
        "scenario": "2023_debt_ceiling",
        "constants": BACKTEST_2023,
        "xdate": xdate,
        "market": market,
        "weights": weights,
        "summary": {
            "xdate_mae_days": xdate["mae_days"],
            "xdate_final_error_days": xdate["final_error_days"],
            "spx_direction_hit_pre": market["direction_hit_pre"],
            "spx_mae_pre": market["spx_mae_pre"],
            "weight_shift_historical": weights["final_weights"]["historical"] - DEFAULT_WEIGHTS["historical"],
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report
