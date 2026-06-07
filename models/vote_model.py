import json
from datetime import datetime
from pathlib import Path

from config import BASE_DIR

BASELINE_PATH = BASE_DIR / "data" / "baseline_2027.json"
HISTORICAL_PATH = BASE_DIR / "data" / "historical_votes.json"


def load_vote_windows():
    with open(BASELINE_PATH) as f:
        data = json.load(f)
    return data.get("vote_windows", []), data


def estimate_failed_votes(probability: float) -> int:
    if probability >= 0.5:
        return 3
    if probability >= 0.2:
        return 2
    return 1


def get_vote_forecast() -> dict:
    windows, baseline = load_vote_windows()
    with open(HISTORICAL_PATH) as f:
        historical = json.load(f)

    delays = [abs(h.get("days_to_deadline", 0)) for h in historical]
    median_delay = sorted(delays)[len(delays) // 2] if delays else 3
    mean_delay = sum(delays) / len(delays) if delays else 18

    enriched = []
    for w in windows:
        enriched.append({
            **w,
            "failed_votes_est": estimate_failed_votes(w["probability"]),
            "fy_overlap": w["start"] <= "2027-10-01" <= w["end"],
        })

    return {
        "final_vote_date": baseline["final_vote_date"],
        "final_vote_range": baseline["final_vote_range"],
        "windows": enriched,
        "historical_median_delay_days": median_delay,
        "historical_mean_delay_days": mean_delay,
        "republican_house_delay_premium": 0.40,
    }
