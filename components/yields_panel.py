import plotly.graph_objects as go
import streamlit as st

from components.theme import style_figure
from i18n.bilingual import bl
from services.yields_client import YIELD_META

CURVE_COLORS = {
    "dgs2": "#3498db",
    "dgs5": "#9b59b6",
    "dgs10": "#10a37f",
    "dgs30": "#e67e22",
}


def _source_caption(yields: dict) -> str:
    if yields.get("source") == "fred":
        return bl("Source: FRED (constant maturity)", "来源：FRED 恒定到期收益率")
    return bl("Source: fallback values (FRED unavailable)", "来源：回退默认值（FRED 不可用）")


def render_yields_data_banner(yields: dict):
    as_of = yields.get("as_of_date")
    fetched = yields.get("fetched_at_display", "—")
    if as_of:
        date_html = f'<span class="yields-data-date">{as_of}</span>'
        label = bl("Market data as of", "市场数据截至")
    else:
        date_html = f'<span class="yields-data-date yields-data-date--muted">{bl("N/A", "暂无")}</span>'
        label = bl("Market data date unavailable", "市场数据日期不可用")

    st.markdown(
        f"""
        <div class="yields-data-banner">
            <div class="yields-data-banner-main">
                <span class="yields-data-label">{label}</span>
                {date_html}
            </div>
            <div class="yields-data-fetched">
                {bl("Retrieved at", "获取时间")}:
                <span class="yields-data-fetched-time">{fetched}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_yields_overview(yields: dict):
    latest = yields.get("latest", {})
    dgs10 = latest.get("dgs10")
    if dgs10 is None:
        st.warning(bl("Treasury yield data unavailable", "美债收益率数据暂不可用"))
        return

    change = yields.get("change_15d_bps", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        bl("10Y Treasury Yield", "10年期美债收益率"),
        f"{dgs10:.2f}%",
        delta=f"{change.get('dgs10', 0):+.1f} bps (15D)",
    )
    c2.metric(bl("2Y Yield", "2年期收益率"), f"{latest.get('dgs2', 0):.2f}%")
    c3.metric(
        bl("2s10s Spread", "2s10s利差"),
        f"{yields.get('spread_2s10s_bps', 0):+.1f} bps",
        help=bl(
            "10Y minus 2Y. Negative values often signal recession risk.",
            "10年期减2年期。倒挂常被视为衰退风险信号。",
        ),
    )
    c4.metric(
        bl("10s30s Spread", "10s30s利差"),
        f"{yields.get('spread_10s30s_bps', 0):+.1f} bps",
    )


def render_yield_curve_chart(yields: dict):
    curve = yields.get("curve", [])
    if not curve:
        st.info(bl("No yield curve data", "暂无收益率曲线数据"))
        return

    labels = [bl(c["maturity_en"], c["maturity_zh"]) for c in curve]
    values = [c["yield_pct"] for c in curve]
    colors = [CURVE_COLORS.get(c["key"], "#10a37f") for c in curve]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[f"{v:.2f}%" for v in values],
            textposition="outside",
        )
    )
    fig.update_layout(
        title=bl("US Treasury Yield Curve", "美国国债收益率曲线"),
        yaxis_title=bl("Yield (%)", "收益率(%)"),
        showlegend=False,
    )
    st.plotly_chart(style_figure(fig, height=360), use_container_width=True)


def render_yields_history_chart(yields: dict):
    histories = yields.get("histories", {})
    if not histories or all(s.empty for s in histories.values()):
        st.info(bl("No yield history available", "暂无收益率历史数据"))
        return

    fig = go.Figure()
    for key, series in histories.items():
        if series.empty:
            continue
        label_en = YIELD_META[key]["label_en"]
        label_zh = YIELD_META[key]["label_zh"]
        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines",
                name=bl(label_en, label_zh),
                line=dict(color=CURVE_COLORS.get(key, "#10a37f"), width=2),
            )
        )

    fig.update_layout(
        title=bl("Treasury Yields — 90 Day History", "美债收益率 — 近90日走势"),
        xaxis_title=bl("Date", "日期"),
        yaxis_title=bl("Yield (%)", "收益率(%)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(style_figure(fig, height=400), use_container_width=True)


def render_dgs10_forecast(market: dict, yields: dict):
    pre = market.get("pre_vote_15d", [])
    post = market.get("post_vote_15d", [])
    if not pre and not post:
        return

    base_yield = yields.get("latest", {}).get("dgs10", 4.2)
    all_days = [p["day_offset"] for p in pre] + [p["day_offset"] for p in post]
    yield_path = [base_yield + p.get("dgs10_bps", 0) / 100 for p in pre + post]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=all_days,
            y=yield_path,
            mode="lines+markers",
            name=bl("10Y Yield Forecast", "10年期收益率预测"),
            line=dict(color="#10a37f", width=2.5),
        )
    )
    fig.add_hline(
        y=base_yield,
        line_dash="dot",
        line_color="#52525b",
        annotation_text=bl("Current 10Y", "当前10年期"),
    )
    fig.add_vline(
        x=0,
        line_dash="dash",
        line_color="#a1a1aa",
        annotation_text=bl("Vote Day", "投票日"),
    )
    fig.update_layout(
        title=bl("10Y Yield Forecast ±15 Days Around Vote", "投票前后半个月10年期收益率预测"),
        xaxis_title=bl("Days from Vote", "距投票日天数"),
        yaxis_title=bl("10Y Yield (%)", "10年期收益率(%)"),
    )
    st.plotly_chart(style_figure(fig, height=380), use_container_width=True)

    fused = market.get("fused_cumulative", {})
    pre_bps = fused.get("pre", {}).get("dgs10", 0) * 10000
    post_bps = fused.get("post", {}).get("dgs10", 0) * 10000
    col1, col2 = st.columns(2)
    col1.metric(bl("Pre-Vote 10Y Change", "投票前10Y变化"), f"{pre_bps:+.1f} bps")
    col2.metric(bl("Post-Vote 10Y Change", "投票后10Y变化"), f"{post_bps:+.1f} bps")


def render_yields_table(yields: dict):
    rows = []
    for point in yields.get("curve", []):
        rows.append(
            {
                bl("Maturity", "期限"): bl(point["maturity_en"], point["maturity_zh"]),
                bl("Yield", "收益率"): f"{point['yield_pct']:.2f}%",
                bl("15D Change", "15日变化"): f"{point['change_15d_bps']:+.1f} bps",
                bl("Source", "来源"): point["source"],
            }
        )
    if rows:
        st.dataframe(rows, hide_index=True, use_container_width=True)


def render_yields_panel(yields: dict):
    render_yields_data_banner(yields)
    st.caption(_source_caption(yields))
    render_yields_overview(yields)

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader(bl("Yield Curve", "收益率曲线"))
        render_yield_curve_chart(yields)
    with col_r:
        st.subheader(bl("Maturity Breakdown", "期限明细"))
        render_yields_table(yields)

    st.subheader(bl("Historical Yields", "历史收益率"))
    render_yields_history_chart(yields)
