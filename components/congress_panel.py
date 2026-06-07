from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.theme import style_figure
from i18n.bilingual import bl, t
from services.congress_client import (
    PARTY_COLORS,
    load_congress_composition,
    refresh_congress_composition,
)

PARTY_LABELS = {
    "Democrat": ("Democrat", "民主党"),
    "Republican": ("Republican", "共和党"),
    "Independent": ("Independent", "独立人士"),
    "Other": ("Other", "其他"),
}

HEADER_HEIGHT = 128
TABLE_HEIGHT = 220
CHART_HEIGHT = 360
CHART_SLOT_HEIGHT = CHART_HEIGHT + 48


def _party_label(party: str) -> str:
    en, zh = PARTY_LABELS.get(party, (party, party))
    return bl(en, zh)


def _chamber_chart(chamber: dict, title: str) -> go.Figure:
    parties = chamber.get("parties", {})
    order = ["Democrat", "Republican", "Independent", "Other"]
    labels = []
    values = []
    colors = []
    for party in order:
        if party in parties:
            labels.append(_party_label(party))
            values.append(parties[party])
            colors.append(PARTY_COLORS.get(party, "#7f8c8d"))
    for party, count in parties.items():
        if party not in order:
            labels.append(_party_label(party))
            values.append(count)
            colors.append(PARTY_COLORS.get(party, "#7f8c8d"))

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=values,
            textposition="outside",
        )
    )
    fig.update_layout(
        title=title,
        yaxis_title=bl("Seats", "席位数"),
        showlegend=False,
    )
    return style_figure(fig, height=CHART_HEIGHT)


def _party_table(chamber: dict) -> pd.DataFrame | None:
    parties = chamber.get("parties", {})
    total = chamber.get("total", 0)
    if not parties:
        return None

    rows = [
        {
            bl("Party", "党派"): _party_label(p),
            bl("Seats", "席位"): n,
            bl("Share", "占比"): f"{n / total * 100:.1f}%" if total else "—",
        }
        for p, n in sorted(parties.items(), key=lambda x: -x[1])
    ]
    return pd.DataFrame(rows)


def _render_chamber_header(chamber: dict, chamber_key: str):
    with st.container(height=HEADER_HEIGHT, border=False):
        title = t(f"congress.{chamber_key}")
        majority = chamber.get("majority")
        total = chamber.get("total", 0)

        st.subheader(title)
        m1, m2 = st.columns(2)
        m1.metric(bl("Total seats", "总席位"), total)
        m2.metric(
            bl("Largest party", "最大党派"),
            _party_label(majority) if majority else "—",
        )


def _render_chamber_table(chamber: dict):
    with st.container(height=TABLE_HEIGHT, border=False):
        df = _party_table(chamber)
        if df is None:
            st.warning(bl("No seat data available.", "暂无席位数据。"))
            return
        st.dataframe(df, hide_index=True, use_container_width=True, height=TABLE_HEIGHT - 16)


def _render_chamber_chart(chamber: dict, chamber_key: str):
    with st.container(height=CHART_SLOT_HEIGHT, border=False):
        parties = chamber.get("parties", {})
        if not parties:
            return
        title = t(f"congress.{chamber_key}")
        st.plotly_chart(_chamber_chart(chamber, title), use_container_width=True)


def render_congress_panel():
    if st.button(bl("Refresh seat counts", "刷新席位数据")):
        with st.spinner(t("common.loading")):
            refresh_congress_composition()
        st.rerun()

    data = load_congress_composition()
    if not data:
        with st.spinner(t("common.loading")):
            try:
                data = refresh_congress_composition()
            except Exception as exc:
                st.error(bl(f"Unable to load Congress data: {exc}", f"无法加载国会数据: {exc}"))
                return

    updated = data.get("updated_at", "")
    try:
        updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        updated_text = updated_dt.strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        updated_text = updated or "—"

    congress_num = data.get("congress")
    caption = bl(
        f"Source: {data.get('source', '—')} | Congress: {congress_num} | Updated: {updated_text}",
        f"来源: {data.get('source', '—')} | 第 {congress_num} 届国会 | 更新: {updated_text}",
    )
    if data.get("stale"):
        caption += " | " + bl("Showing cached data (fetch failed)", "显示缓存数据（拉取失败）")
    st.caption(caption)

    senate = data.get("senate", {})
    house = data.get("house", {})

    col_s, col_h = st.columns(2, gap="large")
    with col_s:
        _render_chamber_header(senate, "senate")
    with col_h:
        _render_chamber_header(house, "house")

    col_s, col_h = st.columns(2, gap="large")
    with col_s:
        _render_chamber_table(senate)
    with col_h:
        _render_chamber_table(house)

    col_s, col_h = st.columns(2, gap="large")
    with col_s:
        _render_chamber_chart(senate, "senate")
    with col_h:
        _render_chamber_chart(house, "house")

    st.info(
        bl(
            "Senate Independents (e.g. Sanders, King) caucus with Democrats for committee leadership.",
            "参议院独立议员（如 Sanders、King）通常与民主党党团合作。",
        )
    )
