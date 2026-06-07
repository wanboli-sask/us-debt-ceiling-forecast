import pandas as pd
import plotly.express as px
import streamlit as st

from components.theme import style_figure
from db.database import get_snapshots
from i18n.bilingual import bl


def render_daily_report():
    snaps = get_snapshots(30)
    if not snaps:
        st.info(bl("No snapshots yet. Run daily update first.", "暂无快照，请先运行每日更新。"))
        return

    df = pd.DataFrame(snaps)
    df = df.sort_values("snapshot_date")

    fig = px.line(
        df, x="snapshot_date", y="sentiment_score",
        title=bl("Sentiment Index (30 days)", "情绪指数（30日）"),
    )
    st.plotly_chart(style_figure(fig, height=360), use_container_width=True)

    if "vix_close" in df.columns and df["vix_close"].notna().any():
        fig_vix = px.line(
            df, x="snapshot_date", y="vix_close",
            title=bl("VIX Fear Index (30 days)", "VIX恐慌指数（30日）"),
        )
        fig_vix.add_hline(y=30, line_dash="dash",
                          annotation_text=bl("Elevated", "升高"))
        st.plotly_chart(style_figure(fig_vix, height=360), use_container_width=True)

    if "dgs10" in df.columns and df["dgs10"].notna().any():
        fig_dgs10 = px.line(
            df, x="snapshot_date", y="dgs10",
            title=bl("10Y Treasury Yield (30 days)", "10年期美债收益率（30日）"),
        )
        st.plotly_chart(style_figure(fig_dgs10, height=360), use_container_width=True)

    if "x_date_estimate" in df.columns:
        fig2 = px.line(
            df, x="snapshot_date", y="debt_trillions",
            title=bl("Federal Debt (Trillions)", "联邦债务（万亿）"),
        )
        st.plotly_chart(style_figure(fig2, height=360), use_container_width=True)

    st.dataframe(df[[
        "snapshot_date", "debt_trillions", "x_date_estimate",
        "sentiment_score", "risk_level", "spx_close", "vix_close", "dgs10"
    ]].sort_values("snapshot_date", ascending=False), use_container_width=True)
