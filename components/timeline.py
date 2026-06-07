import json
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from components.theme import style_figure
from config import BASE_DIR
from i18n.bilingual import bl, t

BASELINE_PATH = BASE_DIR / "data" / "baseline_2027.json"


def render_timeline():
    with open(BASELINE_PATH) as f:
        baseline = json.load(f)

    events = [
        ("limit_hit", baseline["limit_hit_date"], baseline["limit_hit_range"], "#e67e22"),
        ("x_date", baseline["x_date"], baseline["x_date_range"], "#e74c3c"),
        ("final_vote", baseline["final_vote_date"], baseline["final_vote_range"], "#3498db"),
        ("fy2028", "2027-10-01", ["2027-10-01", "2027-10-01"], "#9b59b6"),
    ]
    for w in baseline.get("vote_windows", []):
        events.append((
            w["id"],
            w["start"],
            [w["start"], w["end"]],
            "#2ecc71",
        ))

    fig = go.Figure()
    for i, (name, center, rng, color) in enumerate(events):
        fig.add_trace(go.Scatter(
            x=[rng[0], rng[1]],
            y=[i, i],
            mode="lines+markers",
            name=name,
            line=dict(color=color, width=8),
            marker=dict(size=10),
        ))

    fig.update_layout(
        title=bl("2027 Debt Ceiling Timeline", "2027年债务上限时间线"),
        xaxis_title=bl("Date", "日期"),
        yaxis=dict(showticklabels=False),
        showlegend=True,
    )
    st.plotly_chart(style_figure(fig, height=400), use_container_width=True)

    for w in baseline.get("vote_windows", []):
        st.markdown(
            f"**{w['start']} ~ {w['end']}** ({w['probability']*100:.0f}%) — "
            f"{bl(w['rationale_en'], w['rationale_zh'])}"
        )
