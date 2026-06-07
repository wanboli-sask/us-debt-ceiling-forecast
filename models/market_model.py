import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from config import BASE_DIR, MARKET_WINDOW_DAYS
from models.weight_learner import fuse_predictions, resolve_weights

HISTORICAL_PATH = BASE_DIR / "data" / "historical_votes.json"
BASELINE_PATH = BASE_DIR / "data" / "baseline_2027.json"


def _load_historical():
    with open(HISTORICAL_PATH) as f:
        return json.load(f)


def _load_baseline():
    with open(BASELINE_PATH) as f:
        return json.load(f)


def _knn_predict(context: dict) -> dict:
    hist = _load_historical()
    features = []
    targets = []
    for h in hist:
        features.append([
            abs(h.get("days_to_deadline", 10)),
            1 if h.get("party_control", {}).get("house") == "R" else 0,
            1 if h.get("resolution_type", "").startswith("suspend") else 0,
        ])
        targets.append([
            h.get("spx_return_15d_before", -0.038),
            h.get("tlt_return_15d_before", 0.01),
            h.get("dgs10_change_bps_15d_before", -22) / 10000,
            h.get("vix_change_15d_before", 0.2),
        ])

    x = np.array(features)
    y = np.array(targets)
    q = np.array([
        context.get("days_to_xdate", 30),
        1 if context.get("republican_house", True) else 0,
        1 if context.get("suspend_expected", True) else 0,
    ])
    dists = np.linalg.norm(x - q, axis=1)
    weights = 1 / (dists + 1e-6)
    weights /= weights.sum()
    pred = (y.T @ weights).tolist()
    return {
        "spx": pred[0], "tlt": pred[1], "dgs10": pred[2], "vix": pred[3],
    }


def _sentiment_layer(sentiment_score: float, days_to_vote: int) -> dict:
    proximity = 1.05 ** max(15 - days_to_vote, 0) if days_to_vote <= 15 else 1.0
    adj = sentiment_score * proximity
    return {
        "spx": adj * -0.05,
        "tlt": adj * 0.02,
        "dgs10": adj * -0.003,
        "vix": max(0, -adj * 0.3),
    }


def _micro_layer(vix_daily_return: float, tga_change_pct: float) -> dict:
    stress = max(vix_daily_return, 0)
    liquidity = -tga_change_pct * 0.5
    return {
        "spx": -stress * 0.5 + liquidity * 0.1,
        "tlt": stress * 0.3 + liquidity * 0.05,
        "dgs10": -stress * 0.02,
        "vix": stress * 2,
    }


def _daily_curve(cumulative: dict, window: int, direction: str) -> list:
    days = list(range(-window, 0) if direction == "pre" else range(0, window + 1))
    curve = []
    peak_day = 7 if direction == "pre" else 3
    for d in days:
        t = abs(d) / window
        shape = np.exp(-((abs(d) - peak_day) ** 2) / 18)
        curve.append({
            "day_offset": d,
            "spx": cumulative["spx"] * shape * t,
            "tlt": cumulative["tlt"] * shape * t,
            "dgs10_bps": cumulative["dgs10"] * 10000 * shape * t,
            "vix": cumulative["vix"] * shape * t,
        })
    return curve


def forecast_market(
    sentiment_score: float = 0.0,
    vix_daily_return: float = 0.0,
    tga_change_pct: float = 0.0,
    days_to_xdate: int = 30,
    ai_weights: dict = None,
) -> dict:
    baseline = _load_baseline()
    vote_date = datetime.strptime(baseline["final_vote_date"], "%Y-%m-%d")
    days_to_vote = (vote_date.date() - datetime.now().date()).days

    context = {
        "days_to_xdate": days_to_xdate,
        "republican_house": True,
        "suspend_expected": True,
    }

    hist_pred = _knn_predict(context)
    sent_pred = _sentiment_layer(sentiment_score, days_to_vote)
    micro_pred = _micro_layer(vix_daily_return, tga_change_pct)

    layer_preds = {
        "historical": hist_pred,
        "sentiment": sent_pred,
        "microstructure": micro_pred,
    }

    resolved = resolve_weights(ai_weights=ai_weights)
    fused = fuse_predictions(layer_preds, resolved["weights"])

    pre_cum = {k: fused["fused"][k] for k in fused["fused"]}
    post_cum = {
        "spx": abs(pre_cum["spx"]) * 0.8 + 0.025,
        "tlt": pre_cum["tlt"] * 0.5 + 0.01,
        "dgs10": -pre_cum["dgs10"] * 0.3 + 0.001,
        "vix": -pre_cum["vix"] * 0.4,
    }

    p10_spx = pre_cum["spx"] * 1.3
    p90_spx = pre_cum["spx"] * 0.7

    return {
        "vote_date": baseline["final_vote_date"],
        "pre_vote_15d": _daily_curve(pre_cum, MARKET_WINDOW_DAYS, "pre"),
        "post_vote_15d": _daily_curve(post_cum, MARKET_WINDOW_DAYS, "post"),
        "cumulative_bands": {
            "pre": {"spx_p10": p10_spx, "spx_p50": pre_cum["spx"], "spx_p90": p90_spx},
            "post": {
                "spx_p10": post_cum["spx"] * 0.6,
                "spx_p50": post_cum["spx"],
                "spx_p90": post_cum["spx"] * 1.4,
            },
        },
        "layer_preds": layer_preds,
        "layer_weights": resolved,
        "layer_contributions": fused["contributions"],
        "fused_cumulative": {"pre": pre_cum, "post": post_cum},
    }
