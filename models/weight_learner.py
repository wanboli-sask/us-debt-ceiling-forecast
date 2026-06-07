import json
import math
from copy import deepcopy
from enum import Enum
from pathlib import Path

from config import (
    BASE_DIR, DEFAULT_WEIGHTS, HEDGE_ETA,
    MAX_DAILY_WEIGHT_SHIFT, WEIGHT_MAX, WEIGHT_MIN,
)

USER_WEIGHTS_PATH = BASE_DIR / "data" / "user_weights.json"


class WeightMode(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    HYBRID = "hybrid"


def _clamp_weights(w: dict) -> dict:
    keys = ["historical", "sentiment", "microstructure"]
    clipped = {k: min(WEIGHT_MAX, max(WEIGHT_MIN, w[k])) for k in keys}
    total = sum(clipped.values())
    return {k: clipped[k] / total for k in keys}


def load_user_prefs() -> dict:
    if USER_WEIGHTS_PATH.exists():
        with open(USER_WEIGHTS_PATH) as f:
            return json.load(f)
    return {
        "mode": WeightMode.AUTO.value,
        "hybrid_blend": 0.0,
        "locked": False,
        "weights": deepcopy(DEFAULT_WEIGHTS),
    }


def save_user_prefs(prefs: dict):
    USER_WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(USER_WEIGHTS_PATH, "w") as f:
        json.dump(prefs, f, indent=2)


def hedge_update(ai_weights: dict, layer_losses: dict, vix_daily_return: float = 0) -> dict:
    eta = HEDGE_ETA * (1.5 if vix_daily_return > 0.10 else 1.0)
    new_w = {}
    for k in ai_weights:
        loss = layer_losses.get(k, 0.5)
        new_w[k] = ai_weights[k] * math.exp(-eta * loss)

    new_w = _clamp_weights(new_w)
    old = _clamp_weights(ai_weights)
    blended = {}
    for k in new_w:
        delta = new_w[k] - old[k]
        delta = max(-MAX_DAILY_WEIGHT_SHIFT, min(MAX_DAILY_WEIGHT_SHIFT, delta))
        blended[k] = old[k] + delta
    return _clamp_weights(blended)


def resolve_weights(ai_weights: dict = None, user_prefs: dict = None) -> dict:
    prefs = user_prefs or load_user_prefs()
    ai = _clamp_weights(ai_weights or prefs.get("ai_weights") or DEFAULT_WEIGHTS)
    user = _clamp_weights(prefs.get("weights", DEFAULT_WEIGHTS))
    mode = prefs.get("mode", WeightMode.AUTO.value)
    blend = float(prefs.get("hybrid_blend", 0.0))

    if mode == WeightMode.MANUAL.value:
        final = user
        source = "user"
    elif mode == WeightMode.HYBRID.value:
        final = {k: blend * user[k] + (1 - blend) * ai[k] for k in user}
        final = _clamp_weights(final)
        source = "hybrid"
    else:
        final = ai
        source = "ai"

    return {
        "weights": final,
        "ai_weights": ai,
        "user_weights": user,
        "source": source,
        "mode": mode,
        "hybrid_blend": blend,
    }


def fuse_predictions(layer_preds: dict, weights: dict) -> dict:
    keys = ["historical", "sentiment", "microstructure"]
    fused = {}
    assets = set()
    for layer in layer_preds.values():
        assets.update(layer.keys())
    for asset in assets:
        fused[asset] = sum(
            weights[k] * layer_preds[k].get(asset, 0) for k in keys
        )
    contributions = {
        k: {a: weights[k] * layer_preds[k].get(a, 0) for a in assets}
        for k in keys
    }
    return {"fused": fused, "contributions": contributions}
