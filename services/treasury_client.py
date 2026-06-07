import requests
from config import TREASURY_DEBT_URL, TREASURY_CASH_URL, DEBT_LIMIT_DOLLARS


def fetch_latest_debt():
    params = {
        "sort": "-record_date",
        "page[size]": 1,
        "fields": "record_date,tot_pub_debt_out_amt,debt_held_public_amt",
    }
    try:
        r = requests.get(TREASURY_DEBT_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()["data"][0]
        debt = float(data["tot_pub_debt_out_amt"])
        return {
            "record_date": data["record_date"],
            "debt_dollars": debt,
            "debt_trillions": debt / 1e12,
            "headroom_billions": (DEBT_LIMIT_DOLLARS - debt) / 1e9,
        }
    except Exception as e:
        return {"error": str(e), "debt_trillions": 39.0, "headroom_billions": 2104}


def fetch_cash_balance():
    params = {"sort": "-record_date", "page[size]": 5}
    try:
        r = requests.get(TREASURY_CASH_URL, params=params, timeout=15)
        r.raise_for_status()
        rows = r.json()["data"]
        total = sum(float(row.get("open_today_bal", 0) or 0) for row in rows[:1])
        if rows:
            return {
                "record_date": rows[0]["record_date"],
                "cash_billions": total / 1e9 if total else 650.0,
            }
    except Exception:
        pass
    return {"record_date": None, "cash_billions": 650.0}
