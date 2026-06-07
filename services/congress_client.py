"""Fetch and cache US House/Senate party seat counts."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import requests

from config import BASE_DIR

LEGISLATORS_URL = (
    "https://unitedstates.github.io/congress-legislators/legislators-current.json"
)
COMPOSITION_PATH = BASE_DIR / "data" / "congress_composition.json"

PARTY_COLORS = {
    "Democrat": "#2e86de",
    "Republican": "#e74c3c",
    "Independent": "#95a5a6",
    "Other": "#7f8c8d",
}


def _normalize_party(party: str | None) -> str:
    if not party:
        return "Other"
    low = party.lower()
    if "democrat" in low:
        return "Democrat"
    if "republican" in low:
        return "Republican"
    if "independent" in low:
        return "Independent"
    return party.strip().title() or "Other"


def _latest_term(legislator: dict) -> dict:
    terms = legislator.get("terms") or []
    return terms[-1] if terms else {}


def _count_chamber(legislators: list[dict], chamber_type: str) -> dict:
    parties: dict[str, int] = {}
    for leg in legislators:
        term = _latest_term(leg)
        if term.get("type") != chamber_type:
            continue
        party = _normalize_party(term.get("party"))
        parties[party] = parties.get(party, 0) + 1
    total = sum(parties.values())
    majority = max(parties, key=parties.get) if parties else None
    return {"total": total, "majority": majority, "parties": parties}


def fetch_congress_composition() -> dict:
    """Pull current legislators and aggregate party counts by chamber."""
    r = requests.get(LEGISLATORS_URL, timeout=30)
    r.raise_for_status()
    legislators = r.json()
    senate = _count_chamber(legislators, "sen")
    house = _count_chamber(legislators, "rep")
    return {
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "unitedstates/congress-legislators",
        "congress": _infer_congress(),
        "senate": senate,
        "house": house,
    }


def _infer_congress() -> int:
    now = datetime.now()
    year = now.year
    if now.month == 1 and now.day < 3:
        year -= 1
    return (year - 1789) // 2 + 1


def save_congress_composition(data: dict) -> None:
    COMPOSITION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(COMPOSITION_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_congress_composition() -> dict | None:
    if not COMPOSITION_PATH.exists():
        return None
    with open(COMPOSITION_PATH, encoding="utf-8") as f:
        return json.load(f)


def refresh_congress_composition() -> dict:
    try:
        data = fetch_congress_composition()
        save_congress_composition(data)
        data["stale"] = False
        return data
    except Exception as exc:
        cached = load_congress_composition()
        if cached:
            cached = dict(cached)
            cached["stale"] = True
            cached["error"] = str(exc)
            return cached
        raise
