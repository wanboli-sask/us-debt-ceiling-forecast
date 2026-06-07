import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.theme import style_figure
from config import BASE_DIR
from i18n.bilingual import bl, t
from models.backtest import run_backtest_2023

REPORT_PATH = BASE_DIR / "data" / "backtest_report.json"


@st.cache_data(ttl=3600)
def _load_report() -> dict:
    if REPORT_PATH.exists():
        with open(REPORT_PATH) as f:
            return json.load(f)
    return run_backtest_2023()


def render_backtest_panel():
    if st.button(bl("Run / Refresh Backtest", "运行/刷新回测")):
        st.cache_data.clear()
        run_backtest_2023()
        st.rerun()

    report = _load_report()
    summary = report.get("summary", {})
    constants = report.get("constants", {})

    st.caption(bl(
        f"2023 crisis: limit hit {constants.get('limit_hit_date')} | vote {constants.get('vote_date')} | X-date {constants.get('x_date_actual')}",
        f"2023危机: 触限{constants.get('limit_hit_date')} | 投票{constants.get('vote_date')} | 违约日{constants.get('x_date_actual')}",
    ))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(bl("X-date MAE (days)", "X-date平均误差(天)"), f"{summary.get('xdate_mae_days', 0):.1f}")
    c2.metric(bl("Final X-date error", "最终X-date误差"), f"{summary.get('xdate_final_error_days', 0):.0f} " + bl("days", "天"))
    hit = summary.get("spx_direction_hit_pre", False)
    c3.metric(bl("SPX direction hit", "标普方向命中"), bl("Yes", "是") if hit else bl("No", "否"))
    c4.metric(bl("SPX MAE (pre)", "标普前MAE"), f"{summary.get('spx_mae_pre', 0)*100:.2f}%")

    # Chart 1: X-date timeline
    st.subheader(bl("X-date Prediction Drift", "X-date预测偏差"))
    xtl = report.get("xdate", {}).get("timeline", [])
    if xtl:
        df = pd.DataFrame(xtl)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df["date"], y=df["x_date_pred"], name=bl("Predicted X-date", "预测X-date"), mode="lines+markers"))
        fig1.add_hline(y=constants.get("x_date_actual"), line_dash="dash", line_color="red",
                       annotation_text=bl("Actual X-date", "实际X-date"))
        fig1.update_layout(yaxis_title=bl("Date", "日期"))
        st.plotly_chart(style_figure(fig1, height=360), use_container_width=True)

    # Chart 2: SPX pred vs actual
    st.subheader(bl("SPX ±15d: Predicted vs Actual", "标普±15日: 预测 vs 实际"))
    mkt = report.get("market", {})
    pred_curve = mkt.get("pred_pre_curve", []) + mkt.get("pred_post_curve", [])
    act_curve = mkt.get("actual_spx_curve", [])
    if pred_curve and act_curve:
        pdf = pd.DataFrame(pred_curve)
        adf = pd.DataFrame(act_curve)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=pdf["day_offset"], y=pdf["spx"]*100, name=bl("Predicted", "预测"), mode="lines"))
        fig2.add_trace(go.Scatter(x=adf["day_offset"], y=adf["cumulative_return"]*100, name=bl("Actual", "实际"), mode="lines"))
        fig2.add_vline(x=0, line_dash="dash", line_color="red")
        fig2.update_layout(
            xaxis_title=bl("Days from vote", "距投票日"),
            yaxis_title=bl("SPX cumulative %", "标普累计%"),
        )
        st.plotly_chart(style_figure(fig2, height=360), use_container_width=True)

    # Chart 3: VIX
    st.subheader(bl("VIX Around Vote (Actual)", "投票前后VIX（实际）"))
    vix_curve = mkt.get("actual_vix_curve", [])
    if vix_curve:
        vdf = pd.DataFrame(vix_curve)
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=vdf["day_offset"], y=vdf["level"], name="VIX", line=dict(color="#e74c3c")))
        fig3.add_vline(x=0, line_dash="dash", line_color="red")
        fig3.update_layout(xaxis_title=bl("Days from vote", "距投票日"), yaxis_title="VIX")
        st.plotly_chart(style_figure(fig3, height=320), use_container_width=True)

    # Chart 4: Weight evolution
    st.subheader(bl("AI Weight Learning Simulation", "AI权重学习模拟"))
    wh = report.get("weights", {}).get("history", [])
    if wh:
        wdf = pd.DataFrame(wh)
        fig4 = go.Figure()
        for col, label in [("w_historical", bl("Historical", "历史")), ("w_sentiment", bl("Sentiment", "情绪")), ("w_microstructure", bl("Micro", "微观"))]:
            fig4.add_trace(go.Scatter(x=wdf["date"], y=wdf[col], name=label, mode="lines"))
        fig4.update_layout(yaxis_title=bl("Weight", "权重"))
        st.plotly_chart(style_figure(fig4, height=360), use_container_width=True)

    fw = report.get("weights", {}).get("final_weights", {})
    st.caption(bl(
        f"Final weights: hist={fw.get('historical',0):.2f} sent={fw.get('sentiment',0):.2f} micro={fw.get('microstructure',0):.2f}",
        f"最终权重: 历史={fw.get('historical',0):.2f} 情绪={fw.get('sentiment',0):.2f} 微观={fw.get('microstructure',0):.2f}",
    ))
