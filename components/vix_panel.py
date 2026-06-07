import plotly.graph_objects as go
import streamlit as st

from components.theme import style_figure
from i18n.bilingual import bl, t


def render_vix_overview(vix: dict):
    close = vix.get("close")
    if close is None:
        st.warning(bl("VIX data unavailable", "恐慌指数数据暂不可用"))
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        bl("VIX Fear Index", "VIX恐慌指数"),
        f"{close:.2f}",
        delta=f"{vix.get('daily_return', 0)*100:+.2f}%",
    )
    c2.metric(bl("15D Change", "15日变化"), f"{vix.get('return_15d', 0)*100:+.2f}%")
    fear_label = bl(vix["fear_level_en"], vix["fear_level_zh"])
    c3.metric(bl("Fear Level", "恐慌等级"), fear_label)
    c4.metric(
        bl("Debt-Ceiling Signal", "债务上限信号"),
        bl("Elevated if VIX > 25", "VIX>25时升高") if close > 25 else bl("Moderate", "中等"),
    )


def render_vix_chart(vix: dict):
    df = vix.get("history")
    if df is None or df.empty:
        st.info(bl("No VIX history available", "暂无VIX历史数据"))
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"], mode="lines",
        name=bl("VIX", "恐慌指数"),
        line=dict(color="#e74c3c", width=2),
        fill="tozeroy", fillcolor="rgba(231,76,60,0.1)",
    ))
    for level, label_en, label_zh in [
        (20, "Normal ceiling (20)", "正常上限(20)"),
        (30, "Elevated (30)", "升高(30)"),
        (40, "High fear (40)", "高恐慌(40)"),
    ]:
        fig.add_hline(y=level, line_dash="dot", line_color="#52525b",
                      annotation_text=bl(label_en, label_zh))
    fig.update_layout(
        title=bl("VIX Fear Index — 90 Day History", "VIX恐慌指数 — 近90日走势"),
        xaxis_title=bl("Date", "日期"),
        yaxis_title=bl("VIX Level", "VIX水平"),
        showlegend=False,
    )
    st.plotly_chart(style_figure(fig, height=380), use_container_width=True)


def render_vix_forecast(market: dict, vix: dict):
    pre = market.get("pre_vote_15d", [])
    post = market.get("post_vote_15d", [])
    if not pre and not post:
        return

    current = vix.get("close") or 20.0
    all_days = [p["day_offset"] for p in pre] + [p["day_offset"] for p in post]
    vix_path = [current * (1 + p.get("vix", 0)) for p in pre + post]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=all_days, y=vix_path, mode="lines+markers",
        name=bl("VIX Forecast", "VIX预测"),
        line=dict(color="#e67e22", width=2),
    ))
    fig.add_hline(y=30, line_dash="dash", line_color="#f39c12",
                  annotation_text=bl("Elevated (30)", "升高(30)"))
    fig.add_vline(x=0, line_dash="dash", line_color="red",
                  annotation_text=bl("Vote Day", "投票日"))
    fig.update_layout(
        title=bl("VIX Forecast ±15 Days Around Vote", "投票前后半个月VIX预测"),
        xaxis_title=bl("Days from Vote", "距投票日天数"),
        yaxis_title=bl("VIX Level", "VIX水平"),
    )
    st.plotly_chart(style_figure(fig, height=380), use_container_width=True)

    fused = market.get("fused_cumulative", {})
    pre_vix = fused.get("pre", {}).get("vix", 0)
    post_vix = fused.get("post", {}).get("vix", 0)
    col1, col2 = st.columns(2)
    col1.metric(bl("Pre-Vote VIX Change", "投票前VIX变化"), f"{pre_vix*100:+.1f}%")
    col2.metric(bl("Post-Vote VIX Change", "投票后VIX变化"), f"{post_vix*100:+.1f}%")
