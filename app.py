import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from components.daily_report import render_daily_report
from components.market_chart import render_market_forecast
from components.timeline import render_timeline
from components.vix_panel import render_vix_chart, render_vix_overview
from components.backtest_panel import render_backtest_panel
from components.weight_controls import render_weight_controls
from config import BASE_DIR
from db.database import get_snapshots, init_db
from i18n.bilingual import bl, t
from jobs.daily_update import run_daily_update
from models.market_model import forecast_market
from models.vote_model import get_vote_forecast
from models.xdate_model import project_x_date
from models.weight_learner import resolve_weights
from services.fred_client import fetch_fred_bundle, get_fred_status
from services.market_client import get_latest_prices, get_vix_summary
from services.news_sentiment import get_sentiment_summary
from services.treasury_client import fetch_cash_balance, fetch_latest_debt

st.set_page_config(
    page_title="US Debt Ceiling Forecast / 美国债务上限预测",
    page_icon="🏛️",
    layout="wide",
)

init_db()

if "forecast" not in st.session_state:
    st.session_state.forecast = None


def load_forecast(deficit_mult=1.0, em_billions=500.0):
    debt = fetch_latest_debt()
    cash = fetch_cash_balance()
    sentiment = get_sentiment_summary()
    prices = get_latest_prices()
    xdate = project_x_date(
        debt.get("debt_dollars", 39e12),
        cash.get("cash_billions", 650),
        deficit_multiplier=deficit_mult,
        em_billions=em_billions,
    )
    fred_bundle = fetch_fred_bundle()
    resolved = resolve_weights()
    market = forecast_market(
        sentiment_score=sentiment.get("score", 0),
        vix_daily_return=prices.get("vix", {}).get("daily_return", 0),
        tga_change_pct=0.0,
        days_to_xdate=xdate.get("days_to_x", 180),
        ai_weights=resolved.get("ai_weights"),
    )
    return {
        "debt": debt, "cash": cash, "sentiment": sentiment,
        "prices": prices, "xdate": xdate, "vote": get_vote_forecast(),
        "market": market, "fred": fred_bundle, "dgs10": fred_bundle["dgs10"],
        "vix": get_vix_summary(),
    }


def render_disclaimer():
    st.divider()
    st.caption(t("disclaimer.en"))
    st.caption(t("disclaimer.zh"))


def page_overview(data):
    st.header(t("nav.overview"))
    x = data["xdate"]
    c1, c2, c3, c4 = st.columns(4)
    xdate_dt = datetime.strptime(x["x_date_p50"], "%Y-%m-%d").date()
    days_left = (xdate_dt - datetime.now().date()).days
    c1.metric(t("overview.xdate"), x["x_date_p50"])
    c2.metric(t("overview.countdown"), f"{days_left} " + bl("days", "天"))
    c3.metric(t("overview.sentiment"), f"{data['sentiment'].get('score', 0):.3f}")
    risk_map = {"low": t("risk.low"), "medium": t("risk.medium"),
                "high": t("risk.high"), "extreme": t("risk.extreme")}
    c4.metric(t("overview.risk"), risk_map.get(x["risk_level"], x["risk_level"]))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric(t("overview.limit_hit"), x["limit_hit_date"])
    c6.metric(t("overview.final_vote"), data["vote"]["final_vote_date"])
    c7.metric(bl("Debt (T)", "债务(万亿)"), f"${data['debt'].get('debt_trillions', 0):.3f}T")
    c8.metric(bl("Headroom (B)", "剩余额度(十亿)"), f"${data['debt'].get('headroom_billions', 0):.0f}B")

    st.info(
        bl(
            f"X-date range: {x['x_date_p10']} ~ {x['x_date_p90']}",
            f"X-date区间: {x['x_date_p10']} ~ {x['x_date_p90']}",
        )
    )

    st.divider()
    st.subheader(bl("VIX Fear Index / 美股恐慌指数", "VIX Fear Index / 美股恐慌指数"))
    render_vix_overview(data.get("vix", {}))
    render_vix_chart(data.get("vix", {}))


def page_scenario():
    st.header(t("nav.scenario"))
    deficit = st.slider(bl("Deficit multiplier", "赤字倍数"), 0.5, 2.0, 1.0, 0.05)
    em = st.slider(bl("EM headroom (B)", "非常规措施额度(十亿)"), 200, 800, 500, 10)
    default_days = st.slider(bl("Default scenario (days)", "违约情景(天)"), 0, 14, 0)
    if st.button(bl("Recalculate", "重新计算")):
        st.session_state.forecast = load_forecast(deficit, em)
        st.rerun()
    if default_days > 0:
        st.warning(bl(
            f"Default scenario: {default_days}-day technical default may push SPX -8% to -15%",
            f"违约情景: {default_days}天技术性违约可能使标普下跌8%-15%",
        ))


def page_history():
    st.header(t("nav.history"))
    hist_path = BASE_DIR / "data" / "historical_votes.json"
    with open(hist_path) as f:
        cases = json.load(f)
    st.caption(bl(
        f"{len(cases)} debt-limit episodes (2002-2025) from CRS + yfinance",
        f"共 {len(cases)} 次债务上限事件（2002-2025），来源 CRS + yfinance",
    ))
    for c in cases:
        label = c.get("event_id", str(c["year"]))
        title = f"{label} — {bl('Vote', '投票')}: {c['vote_date']}"
        with st.expander(title):
            pc = c.get("party_control", {})
            st.write(bl(
                f"Limit hit: {c['limit_hit_date']} | X-date: {c['x_date']} | "
                f"Days to deadline: {c.get('days_to_deadline', '—')}",
                f"触限: {c['limit_hit_date']} | 违约风险日: {c['x_date']} | "
                f"距截止: {c.get('days_to_deadline', '—')}天",
            ))
            st.write(bl(
                f"Party: POTUS {pc.get('president','?')} / House {pc.get('house','?')} / Senate {pc.get('senate','?')} | Type: {c.get('resolution_type','')}",
                f"党派: 总统{pc.get('president','?')} / 众议院{pc.get('house','?')} / 参议院{pc.get('senate','?')} | 类型: {c.get('resolution_type','')}",
            ))
            col1, col2, col3 = st.columns(3)
            col1.metric(bl("SPX 15d before", "标普前15日"), f"{c['spx_return_15d_before']*100:.2f}%")
            col2.metric(bl("SPX 15d after", "标普后15日"), f"{c['spx_return_15d_after']*100:.2f}%")
            col3.metric(bl("VIX 15d chg", "VIX前15日变化"), f"{c.get('vix_change_15d_before',0)*100:.1f}%")
            st.caption(bl(
                f"TLT before/after: {c.get('tlt_return_15d_before',0)*100:.2f}% / {c.get('tlt_return_15d_after',0)*100:.2f}% | "
                f"10Y bps before/after: {c.get('dgs10_change_bps_15d_before',0):.0f} / {c.get('dgs10_change_bps_15d_after',0):.0f}",
                f"美债ETF前/后: {c.get('tlt_return_15d_before',0)*100:.2f}% / {c.get('tlt_return_15d_after',0)*100:.2f}% | "
                f"10Y基点前/后: {c.get('dgs10_change_bps_15d_before',0):.0f} / {c.get('dgs10_change_bps_15d_after',0):.0f}",
            ))


# Sidebar
st.sidebar.title(t("app.title"))
st.sidebar.caption(t("app.subtitle"))
_fred = get_fred_status()
if not _fred.get("connected"):
    st.sidebar.warning(bl(_fred["message_en"], _fred["message_zh"]))
else:
    st.sidebar.success(bl("FRED API connected", "FRED API 已连接"))

if st.sidebar.button(t("common.run_update")):
    with st.spinner(t("common.loading")):
        run_daily_update()
        st.session_state.forecast = load_forecast()
    st.sidebar.success(bl("Update complete", "更新完成"))

pages = {
    "overview": t("nav.overview"),
    "timeline": t("nav.timeline"),
    "market": t("nav.market"),
    "daily": t("nav.daily"),
    "scenario": t("nav.scenario"),
    "weights": t("nav.weights"),
    "history": t("nav.history"),
    "backtest": t("nav.backtest"),
}
page = st.sidebar.radio(bl("Navigation", "导航"), list(pages.keys()), format_func=lambda k: pages[k])

if st.session_state.forecast is None:
    with st.spinner(t("common.loading")):
        st.session_state.forecast = load_forecast()

data = st.session_state.forecast

if page == "overview":
    page_overview(data)
elif page == "timeline":
    st.header(t("nav.timeline"))
    render_timeline()
elif page == "market":
    st.header(t("nav.market"))
    render_market_forecast(data["market"], data.get("vix"))
elif page == "daily":
    st.header(t("nav.daily"))
    render_daily_report()
elif page == "scenario":
    page_scenario()
elif page == "weights":
    st.header(t("nav.weights"))
    render_weight_controls()
elif page == "history":
    page_history()
elif page == "backtest":
    st.header(t("nav.backtest"))
    render_backtest_panel()

render_disclaimer()
