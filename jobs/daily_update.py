import json
import logging
from datetime import datetime

from config import LOG_DIR
from db.database import get_snapshots, init_db, save_snapshot, save_weight_record
from models.market_model import forecast_market
from models.weight_learner import hedge_update, load_user_prefs, resolve_weights, save_user_prefs
from models.xdate_model import project_x_date
from models.vote_model import get_vote_forecast
from services.fred_client import fetch_fred_bundle
from services.market_client import get_latest_prices
from services.news_sentiment import get_sentiment_summary
from services.treasury_client import fetch_cash_balance, fetch_latest_debt

LOG_FILE = LOG_DIR / "daily_update.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("daily_update")


def run_daily_update(deficit_multiplier: float = 1.0) -> dict:
    log.info("Starting daily update")
    init_db()

    debt = fetch_latest_debt()
    cash = fetch_cash_balance()
    fred = fetch_fred_bundle()
    tga = fred["tga_billions"]
    dgs10 = fred["dgs10"]
    fred_status = fred["status"]

    prices = get_latest_prices()
    if fred.get("vix") and prices.get("vix", {}).get("close") is None:
        prices.setdefault("vix", {})["close"] = fred["vix"]

    sentiment = get_sentiment_summary()

    treasury_cash = cash.get("cash_billions")
    cash_billions = tga
    if treasury_cash and treasury_cash > 1:
        cash_billions = treasury_cash
    elif treasury_cash and tga > treasury_cash:
        cash_billions = tga
    prev_snaps = get_snapshots(2)
    tga_change_pct = 0.0
    if prev_snaps and prev_snaps[0].get("cash_billions"):
        prev_tga = prev_snaps[0]["cash_billions"]
        if prev_tga:
            tga_change_pct = (cash_billions - prev_tga) / prev_tga

    xdate = project_x_date(
        debt_dollars=debt.get("debt_dollars", 39e12),
        cash_billions=cash_billions,
        deficit_multiplier=deficit_multiplier,
    )

    vix_ret = prices.get("vix", {}).get("daily_return", 0)
    market = forecast_market(
        sentiment_score=sentiment.get("score", 0),
        vix_daily_return=vix_ret,
        tga_change_pct=tga_change_pct,
        days_to_xdate=xdate.get("days_to_x", 180),
    )

    prefs = load_user_prefs()
    delta = {
        "fred_connected": fred_status.get("connected", False),
        "fred_sources": fred.get("sources", {}),
        "tga_change_pct": tga_change_pct,
        "news_count": sentiment.get("count", 0),
    }
    if prev_snaps:
        prev = prev_snaps[0]
        if prev.get("x_date_estimate"):
            delta["x_date_shift_days"] = (
                datetime.strptime(xdate["x_date_p50"], "%Y-%m-%d")
                - datetime.strptime(prev["x_date_estimate"], "%Y-%m-%d")
            ).days
        delta["sentiment_change"] = sentiment.get("score", 0) - (prev.get("sentiment_score") or 0)
        delta["weight_change"] = None

    alerts = []
    if not fred_status.get("connected"):
        alerts.append({
            "type": "fred",
            "en": fred_status.get("message_en"),
            "zh": fred_status.get("message_zh"),
        })
    if sentiment.get("score", 0) < -0.3:
        alerts.append({"type": "sentiment", "en": "Negative debt-ceiling news sentiment", "zh": "债务上限新闻情绪偏负面"})
    if xdate.get("risk_level") in ("high", "extreme"):
        alerts.append({"type": "risk", "en": f"Risk level: {xdate['risk_level']}", "zh": f"风险等级: {xdate['risk_level']}"})

    snapshot = {
        "snapshot_date": datetime.now().date().isoformat(),
        "debt_trillions": debt.get("debt_trillions"),
        "cash_billions": cash_billions,
        "x_date_estimate": xdate["x_date_p50"],
        "x_date_p10": xdate["x_date_p10"],
        "x_date_p90": xdate["x_date_p90"],
        "sentiment_score": sentiment.get("score", 0),
        "spx_close": prices.get("spx", {}).get("close"),
        "tlt_close": prices.get("tlt", {}).get("close"),
        "vix_close": prices.get("vix", {}).get("close"),
        "dgs10": dgs10,
        "risk_level": xdate["risk_level"],
        "delta_report": {**delta, "alerts": alerts},
    }
    save_snapshot(snapshot)
    log.info("Snapshot saved: %s", snapshot["snapshot_date"])

    weight_record = None
    if not prefs.get("locked") and prefs.get("mode") != "manual":
        layer_preds = market["layer_preds"]
        actual_spx = prices.get("spx", {}).get("daily_return", 0)
        losses = {k: abs(layer_preds[k]["spx"] - actual_spx) for k in layer_preds}
        ai_w = resolve_weights().get("ai_weights") or prefs.get("weights")
        new_ai = hedge_update(ai_w, losses, vix_ret)
        prefs["ai_weights"] = new_ai
        save_user_prefs(prefs)
        resolved = resolve_weights(ai_weights=new_ai, user_prefs=prefs)
        weight_record = {
            "record_date": snapshot["snapshot_date"],
            "w_historical": resolved["weights"]["historical"],
            "w_sentiment": resolved["weights"]["sentiment"],
            "w_microstructure": resolved["weights"]["microstructure"],
            "w_source": resolved["source"],
            "mode": resolved["mode"],
            "hybrid_blend": resolved["hybrid_blend"],
            "pred_spx": market["fused_cumulative"]["pre"]["spx"],
            "actual_spx": actual_spx,
            "mae_historical": losses["historical"],
            "mae_sentiment": losses["sentiment"],
            "mae_microstructure": losses["microstructure"],
        }
        save_weight_record(weight_record)
        log.info("Weight record saved")

    result = {
        "snapshot": snapshot,
        "xdate": xdate,
        "vote": get_vote_forecast(),
        "market": market,
        "sentiment": sentiment,
        "fred": fred,
        "delta": delta,
        "alerts": alerts,
        "weight_record": weight_record,
    }
    log.info("Daily update complete. FRED connected=%s", fred_status.get("connected"))
    return result
