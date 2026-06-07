import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from components.daily_report import render_daily_report
from components.market_chart import render_market_forecast
from components.timeline import render_timeline
from components.vix_panel import render_vix_chart, render_vix_overview
from components.backtest_panel import render_backtest_panel
from components.congress_panel import render_congress_panel
from components.yields_panel import render_yields_panel
from components.weight_controls import render_weight_controls
from components.theme import (
    inject_global_styles,
    render_disclaimer_block,
    render_page_header,
    render_sidebar_brand,
    render_sidebar_nav_label,
    render_theme_selector,
)
from config import BASE_DIR
from db.database import init_db
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
from services.yields_client import get_yields_summary

st.set_page_config(
    page_title="US Debt Ceiling Forecast / 美国债务上限预测",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
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
        "yields": get_yields_summary(),
    }


def page_overview(data):
    render_page_header(
        t("nav.overview"),
        bl("Key indicators for the 2027 debt ceiling cycle", "2027 年债务上限周期关键指标"),
    )
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
    debt = data["debt"]
    as_of = debt.get("record_date") or "—"
    debt_help = bl(f"As of {as_of}", f"数据截至 {as_of}")
    c5.metric(t("overview.limit_hit"), x["limit_hit_date"])
    c6.metric(t("overview.final_vote"), data["vote"]["final_vote_date"])
    c7.metric(bl("Debt (T)", "债务(万亿)"), f"${debt.get('debt_trillions', 0):.3f}T", help=debt_help)
    c8.metric(bl("Headroom (B)", "剩余额度(十亿)"), f"${debt.get('headroom_billions', 0):.0f}B", help=debt_help)

    date_range = f"{x['x_date_p10']} ~ {x['x_date_p90']}"
    st.info(f"{bl('X-date range', 'X-date区间')}： {date_range}")

    st.markdown("---")
    st.subheader(t("overview.vix"))
    render_vix_overview(data.get("vix", {}))
    render_vix_chart(data.get("vix", {}))


def page_scenario():
    render_page_header(
        t("nav.scenario"),
        bl("Stress-test assumptions for deficit and extraordinary measures", "调整赤字与非常规措施假设进行压力测试"),
    )
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
    render_page_header(
        t("nav.history"),
        bl("Debt-limit episodes from 2002–2025 with market reactions", "2002–2025 年债务上限事件与市场反应"),
    )
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
render_sidebar_brand()
render_theme_selector()
inject_global_styles()
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

render_sidebar_nav_label()
pages = {
    "overview": t("nav.overview"),
    "timeline": t("nav.timeline"),
    "market": t("nav.market"),
    "daily": t("nav.daily"),
    "scenario": t("nav.scenario"),
    "weights": t("nav.weights"),
    "history": t("nav.history"),
    "congress": t("nav.congress"),
    "yields": t("nav.yields"),
    "backtest": t("nav.backtest"),
}
page = st.sidebar.radio(
    "nav",
    list(pages.keys()),
    format_func=lambda k: pages[k],
    label_visibility="collapsed",
)

if st.session_state.forecast is None:
    with st.spinner(t("common.loading")):
        st.session_state.forecast = load_forecast()

data = st.session_state.forecast

if page == "overview":
    page_overview(data)
elif page == "timeline":
    render_page_header(
        t("nav.timeline"),
        bl("2027 vote windows and milestone dates", "2027 年投票窗口与关键节点"),
    )
    render_timeline()
elif page == "market":
    render_page_header(
        t("nav.market"),
        bl("±15-day market impact around the final vote", "最终投票前后半个月市场冲击"),
    )
    render_market_forecast(
        data["market"],
        vix=data.get("vix"),
        yields=data.get("yields"),
    )
elif page == "daily":
    render_page_header(
        t("nav.daily"),
        bl("Historical snapshots from the daily update pipeline", "每日更新流水线历史快照"),
    )
    render_daily_report()
elif page == "scenario":
    page_scenario()
elif page == "weights":
    render_page_header(
        t("nav.weights"),
        bl("AI adaptive weights with manual override", "AI 自适应权重与手动覆盖"),
    )
    render_weight_controls()
elif page == "history":
    page_history()
elif page == "congress":
    render_page_header(
        t("nav.congress"),
        bl("Current party seat counts in the Senate and House", "参议院与众议院当前党派席位分布"),
    )
    render_congress_panel()
elif page == "yields":
    render_page_header(
        t("nav.yields"),
        bl(
            "US Treasury constant-maturity yields and curve spreads",
            "美国国债恒定到期收益率与期限利差",
        ),
    )
    render_yields_panel(data["yields"])
elif page == "backtest":
    render_page_header(
        t("nav.backtest"),
        bl("Validation against the 2023 debt-ceiling episode", "以 2023 年债务上限事件进行回测验证"),
    )
    render_backtest_panel()

render_disclaimer_block()
