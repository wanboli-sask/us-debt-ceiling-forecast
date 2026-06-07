"""OpenAI-inspired global UI theme for Streamlit."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from i18n.bilingual import bl, t

THEME_CSS_PATH = Path(__file__).with_name("theme.css")

THEME_OPTIONS = ["Charcoal", "Cool Gray", "Warm Gray", "Dim"]

LEGACY_THEME_NAMES = {
    "炭灰": "Charcoal",
    "冷灰": "Cool Gray",
    "暖灰": "Warm Gray",
    "浅暗": "Dim",
}

__all__ = [
    "THEME_OPTIONS",
    "get_current_theme",
    "get_plotly_layout",
    "inject_global_styles",
    "render_disclaimer_block",
    "render_page_header",
    "render_sidebar_brand",
    "render_sidebar_nav_label",
    "render_theme_selector",
    "style_figure",
]

FONT_FAMILY = (
    "Inter, 瘦金体, FZShouJinTiS, FZShouJinTi, STXingkai, Kaiti SC, "
    "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
)


def _plotly_layout(
    text: str,
    muted: str,
    grid: str,
    line: str,
    legend_bg: str,
    legend_border: str,
) -> dict:
    return dict(
        font=dict(family=FONT_FAMILY, color=text, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=24, r=24, t=56, b=40),
        title_font=dict(size=16, color=text),
        xaxis=dict(
            gridcolor=grid,
            linecolor=line,
            tickfont=dict(color=muted),
            title_font=dict(color=muted),
        ),
        yaxis=dict(
            gridcolor=grid,
            linecolor=line,
            tickfont=dict(color=muted),
            title_font=dict(color=muted),
        ),
        legend=dict(bgcolor=legend_bg, bordercolor=legend_border, borderwidth=1),
    )


THEME_PRESETS: dict[str, dict] = {
    "Charcoal": {
        "css": {
            "--oa-bg": "#1c1c1e",
            "--oa-bg-soft": "#242428",
            "--oa-bg-sidebar-top": "#202024",
            "--oa-bg-sidebar-bottom": "#1c1c1e",
            "--oa-card": "#2a2a2e",
            "--oa-text": "#f0f0f3",
            "--oa-text-muted": "#b0b0b8",
            "--oa-border": "#3a3a40",
            "--oa-accent": "#10a37f",
            "--oa-accent-dark": "#f0f0f3",
            "--oa-btn-text": "#1c1c1e",
            "--oa-btn-hover-bg": "#ffffff",
            "--oa-brand-zh": "#f4f4f5",
            "--oa-shadow": "0 1px 2px rgba(0,0,0,.28), 0 4px 16px rgba(0,0,0,.22)",
        },
        "plotly": _plotly_layout(
            text="#f0f0f3",
            muted="#b0b0b8",
            grid="#3a3a40",
            line="#4a4a52",
            legend_bg="rgba(42,42,46,0.92)",
            legend_border="#3a3a40",
        ),
    },
    "Cool Gray": {
        "css": {
            "--oa-bg": "#1e2128",
            "--oa-bg-soft": "#262b33",
            "--oa-bg-sidebar-top": "#1a1d24",
            "--oa-bg-sidebar-bottom": "#1e2128",
            "--oa-card": "#2d333b",
            "--oa-text": "#e8eaed",
            "--oa-text-muted": "#9aa0a8",
            "--oa-border": "#3d4450",
            "--oa-accent": "#10a37f",
            "--oa-accent-dark": "#e8eaed",
            "--oa-btn-text": "#1e2128",
            "--oa-btn-hover-bg": "#ffffff",
            "--oa-brand-zh": "#eef0f4",
            "--oa-shadow": "0 1px 2px rgba(0,0,0,.26), 0 4px 16px rgba(0,0,0,.2)",
        },
        "plotly": _plotly_layout(
            text="#e8eaed",
            muted="#9aa0a8",
            grid="#3d4450",
            line="#4d5563",
            legend_bg="rgba(45,51,59,0.92)",
            legend_border="#3d4450",
        ),
    },
    "Warm Gray": {
        "css": {
            "--oa-bg": "#1f1d1b",
            "--oa-bg-soft": "#282522",
            "--oa-bg-sidebar-top": "#1c1a18",
            "--oa-bg-sidebar-bottom": "#1f1d1b",
            "--oa-card": "#302c28",
            "--oa-text": "#ede8e3",
            "--oa-text-muted": "#a8a099",
            "--oa-border": "#3d3832",
            "--oa-accent": "#10a37f",
            "--oa-accent-dark": "#ede8e3",
            "--oa-btn-text": "#1f1d1b",
            "--oa-btn-hover-bg": "#faf8f5",
            "--oa-brand-zh": "#f2ebe4",
            "--oa-shadow": "0 1px 2px rgba(0,0,0,.3), 0 4px 16px rgba(0,0,0,.22)",
        },
        "plotly": _plotly_layout(
            text="#ede8e3",
            muted="#a8a099",
            grid="#3d3832",
            line="#4d4640",
            legend_bg="rgba(48,44,40,0.92)",
            legend_border="#3d3832",
        ),
    },
    "Dim": {
        "css": {
            "--oa-bg": "#2b2b30",
            "--oa-bg-soft": "#34343a",
            "--oa-bg-sidebar-top": "#26262c",
            "--oa-bg-sidebar-bottom": "#2b2b30",
            "--oa-card": "#3c3c44",
            "--oa-text": "#f5f5f7",
            "--oa-text-muted": "#b8b8c0",
            "--oa-border": "#4a4a54",
            "--oa-accent": "#10a37f",
            "--oa-accent-dark": "#1c1c1e",
            "--oa-btn-text": "#f5f5f7",
            "--oa-btn-hover-bg": "#34343a",
            "--oa-brand-zh": "#fafafa",
            "--oa-shadow": "0 1px 2px rgba(0,0,0,.22), 0 4px 16px rgba(0,0,0,.16)",
        },
        "plotly": _plotly_layout(
            text="#f5f5f7",
            muted="#b8b8c0",
            grid="#4a4a54",
            line="#5a5a64",
            legend_bg="rgba(60,60,68,0.92)",
            legend_border="#4a4a54",
        ),
    },
}


def get_current_theme() -> str:
    theme = st.session_state.get("ui_theme", "Charcoal")
    theme = LEGACY_THEME_NAMES.get(theme, theme)
    return theme if theme in THEME_PRESETS else "Charcoal"


def get_plotly_layout() -> dict:
    return THEME_PRESETS[get_current_theme()]["plotly"]


def style_figure(fig, height: int | None = None):
    fig.update_layout(**get_plotly_layout())
    if height:
        fig.update_layout(height=height)
    return fig


def inject_global_styles():
    st.html(THEME_CSS_PATH)
    preset = THEME_PRESETS[get_current_theme()]["css"]
    vars_css = "\n".join(f"  {key}: {value};" for key, value in preset.items())
    st.html(f"<style>:root {{\n{vars_css}\n}}</style>")


def render_theme_selector():
    if "ui_theme" not in st.session_state:
        st.session_state.ui_theme = "Charcoal"
    else:
        st.session_state.ui_theme = LEGACY_THEME_NAMES.get(
            st.session_state.ui_theme, st.session_state.ui_theme
        )
    st.sidebar.markdown(
        f'<p class="sidebar-section-label">{bl("Theme", "主题")}</p>',
        unsafe_allow_html=True,
    )
    st.session_state.ui_theme = st.sidebar.selectbox(
        bl("Theme", "主题"),
        THEME_OPTIONS,
        index=THEME_OPTIONS.index(get_current_theme()),
        label_visibility="collapsed",
    )


def render_sidebar_brand():
    st.sidebar.markdown(
        f"""
        <div class="app-brand">
            <p class="app-brand-title-en">US Debt Ceiling Forecast</p>
            <p class="app-brand-title-zh">美国债务上限预测</p>
            <hr class="app-brand-divider" />
            <p class="app-brand-tagline">{t("app.subtitle")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_nav_label():
    st.sidebar.markdown(
        f'<p class="sidebar-section-label">{bl("Navigation", "导航")}</p>',
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str | None = None):
    sub = subtitle or ""
    st.markdown(
        f"""
        <div class="page-hero">
            <h1>{title}</h1>
            {f"<p>{sub}</p>" if sub else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_disclaimer_block():
    st.markdown(
        f"""
        <div class="disclaimer-block">
            <div>{t("disclaimer.en")}</div>
            <div style="margin-top:0.35rem;">{t("disclaimer.zh")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
