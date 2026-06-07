import pandas as pd
import plotly.express as px
import streamlit as st

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
    st.plotly_chart(fig, use_container_width=True)

    if "vix_close" in df.columns and df["vix_close"].notna().any():
        fig_vix = px.line(
            df, x="snapshot_date", y="vix_close",
            title=bl("VIX Fear Index (30 days)", "VIX恐慌指数（30日）"),
        )
        fig_vix.add_hline(y=30, line_dash="dash",
                          annotation_text=bl("Elevated", "升高"))
        st.plotly_chart(fig_vix, use_container_width=True)

    if "x_date_estimate" in df.columns:
        fig2 = px.line(
            df, x="snapshot_date", y="debt_trillions",
            title=bl("Federal Debt (Trillions)", "联邦债务（万亿）"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(df[[
        "snapshot_date", "debt_trillions", "x_date_estimate",
        "sentiment_score", "risk_level", "spx_close", "vix_close"
    ]].sort_values("snapshot_date", ascending=False), use_container_width=True)
