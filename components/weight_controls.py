import pandas as pd
import plotly.express as px
import streamlit as st

from config import DEFAULT_WEIGHTS
from db.database import get_weight_history
from i18n.bilingual import bl, t
from models.weight_learner import (
    WeightMode, load_user_prefs, resolve_weights, save_user_prefs,
)


def render_weight_controls():
    prefs = load_user_prefs()

    st.subheader(t("weights.mode"))
    mode = st.radio(
        bl("Select mode", "选择模式"),
        [WeightMode.AUTO.value, WeightMode.MANUAL.value, WeightMode.HYBRID.value],
        format_func=lambda x: {
            "auto": bl("Auto", "自动"),
            "manual": bl("Manual", "手动"),
            "hybrid": bl("Hybrid", "混合"),
        }[x],
        index=["auto", "manual", "hybrid"].index(prefs.get("mode", "auto")),
        horizontal=True,
    )

    w = prefs.get("weights", DEFAULT_WEIGHTS)
    hist = st.slider(bl("Historical KNN", "历史KNN"), 0.05, 0.70, w["historical"], 0.01)
    sent = st.slider(bl("Sentiment", "情绪修正"), 0.05, 0.70, w["sentiment"], 0.01)
    micro = st.slider(bl("Microstructure", "微观结构"), 0.05, 0.70, w["microstructure"], 0.01)
    total = hist + sent + micro
    if total > 0:
        user_w = {
            "historical": hist / total,
            "sentiment": sent / total,
            "microstructure": micro / total,
        }
    else:
        user_w = DEFAULT_WEIGHTS

    blend = 0.0
    if mode == WeightMode.HYBRID.value:
        blend = st.slider(
            t("weights.blend"), 0.0, 1.0,
            float(prefs.get("hybrid_blend", 0.0)), 0.05,
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(t("weights.reset")):
            prefs = {"mode": "auto", "hybrid_blend": 0.0, "locked": False, "weights": DEFAULT_WEIGHTS}
            save_user_prefs(prefs)
            st.rerun()
    with col2:
        locked = st.checkbox(t("weights.lock"), value=prefs.get("locked", False))

    prefs.update({
        "mode": mode, "hybrid_blend": blend, "locked": locked, "weights": user_w,
    })
    save_user_prefs(prefs)

    resolved = resolve_weights(user_prefs=prefs)
    st.markdown("### " + bl("Current Effective Weights", "当前生效权重"))
    cw = resolved["weights"]
    c1, c2, c3 = st.columns(3)
    c1.metric(bl("Historical", "历史"), f"{cw['historical']*100:.1f}%")
    c2.metric(bl("Sentiment", "情绪"), f"{cw['sentiment']*100:.1f}%")
    c3.metric(bl("Microstructure", "微观"), f"{cw['microstructure']*100:.1f}%")
    st.caption(bl(f"Source: {resolved['source']}", f"来源: {resolved['source']}"))

    history = get_weight_history(60)
    if history:
        st.subheader(t("weights.evolution"))
        hdf = pd.DataFrame(history).sort_values("record_date")
        fig = px.line(
            hdf, x="record_date",
            y=["w_historical", "w_sentiment", "w_microstructure"],
            title=bl("AI Weight Evolution", "AI权重演变"),
        )
        st.plotly_chart(fig, use_container_width=True)

    return resolved
