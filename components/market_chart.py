import plotly.graph_objects as go
import streamlit as st

from components.theme import style_figure
from components.vix_panel import render_vix_forecast
from i18n.bilingual import bl, t


def render_market_forecast(market: dict, vix: dict = None):
    pre = market.get("pre_vote_15d", [])
    post = market.get("post_vote_15d", [])
    all_days = [p["day_offset"] for p in pre] + [p["day_offset"] for p in post]
    spx = [p["spx"] * 100 for p in pre] + [p["spx"] * 100 for p in post]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=all_days, y=spx, mode="lines+markers",
        name=bl("SPX Daily Path (%)", "标普500逐日路径(%)"),
        line=dict(color="#10a37f", width=2.5),
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="#a1a1aa",
                  annotation_text=bl("Vote Day", "投票日"))
    fig.update_layout(
        title=bl("±15-Day Market Forecast Around Vote", "投票前后半个月市场预测"),
        xaxis_title=bl("Days from Vote", "距投票日天数"),
        yaxis_title=bl("Cumulative SPX Return (%)", "标普500累计收益(%)"),
    )
    st.plotly_chart(style_figure(fig, height=420), use_container_width=True)

    bands = market.get("cumulative_bands", {})
    col1, col2 = st.columns(2)
    with col1:
        pre_b = bands.get("pre", {})
        st.subheader(t("market.pre_vote"))
        st.metric(bl("SPX P50", "标普P50"), f"{pre_b.get('spx_p50', 0)*100:.2f}%")
        st.caption(f"P10: {pre_b.get('spx_p10', 0)*100:.2f}% / P90: {pre_b.get('spx_p90', 0)*100:.2f}%")
    with col2:
        post_b = bands.get("post", {})
        st.subheader(t("market.post_vote"))
        st.metric(bl("SPX P50", "标普P50"), f"{post_b.get('spx_p50', 0)*100:.2f}%")
        st.caption(f"P10: {post_b.get('spx_p10', 0)*100:.2f}% / P90: {post_b.get('spx_p90', 0)*100:.2f}%")


    if vix:
        st.divider()
        st.subheader(bl("VIX Fear Index Forecast", "VIX恐慌指数预测"))
        render_vix_forecast(market, vix)
