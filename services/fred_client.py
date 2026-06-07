import os
from datetime import datetime, timedelta

import pandas as pd

try:
    from fredapi import Fred
except ImportError:
    Fred = None

from dotenv import load_dotenv
from config import BASE_DIR

load_dotenv(BASE_DIR / ".env")

FRED_SERIES = {
    "tga": "WTREGEN",
    "dgs10": "DGS10",
    "vix": "VIXCLS",
}


def get_fred_status() -> dict:
    key = os.getenv("FRED_API_KEY", "").strip()
    configured = bool(key)
    connected = False
    message_en = "FRED API key not configured — using fallback values."
    message_zh = "未配置 FRED API 密钥 — 使用默认值。"
    if not configured:
        return {
            "configured": False,
            "connected": False,
            "message_en": message_en,
            "message_zh": message_zh,
        }
    try:
        fred = Fred(api_key=key)
        s = fred.get_series("DGS10", datetime.now() - timedelta(days=14))
        connected = not s.empty
        if connected:
            message_en = "FRED API connected successfully."
            message_zh = "FRED API 连接成功。"
        else:
            message_en = "FRED API key set but no data returned."
            message_zh = "已设置 FRED 密钥但未返回数据。"
    except Exception as exc:
        message_en = f"FRED API error: {exc}"
        message_zh = f"FRED API 错误: {exc}"
    return {
        "configured": configured,
        "connected": connected,
        "message_en": message_en,
        "message_zh": message_zh,
    }


def _get_fred():
    key = os.getenv("FRED_API_KEY", "").strip()
    if Fred and key:
        return Fred(api_key=key)
    return None


def fetch_series(series_id: str, days: int = 90) -> pd.Series:
    fred = _get_fred()
    if not fred:
        return pd.Series(dtype=float)
    try:
        end = datetime.now()
        start = end - timedelta(days=days)
        return fred.get_series(series_id, start, end).dropna()
    except Exception:
        return pd.Series(dtype=float)


def fetch_tga_billions() -> tuple[float, str]:
    """Return (TGA in billions, source tag)."""
    s = fetch_series(FRED_SERIES["tga"], days=60)
    if not s.empty:
        return float(s.iloc[-1]) / 1000, "fred"
    return 650.0, "fallback"


def fetch_dgs10() -> tuple[float, str]:
    s = fetch_series(FRED_SERIES["dgs10"], days=30)
    if not s.empty:
        return float(s.iloc[-1]), "fred"
    return 4.2, "fallback"


def fetch_vix_fred() -> tuple[float | None, str]:
    s = fetch_series(FRED_SERIES["vix"], days=30)
    if not s.empty:
        return float(s.iloc[-1]), "fred"
    return None, "fallback"


def fetch_fred_bundle() -> dict:
    tga, tga_src = fetch_tga_billions()
    dgs10, dgs10_src = fetch_dgs10()
    vix, vix_src = fetch_vix_fred()
    status = get_fred_status()
    return {
        "tga_billions": tga,
        "dgs10": dgs10,
        "vix": vix,
        "sources": {"tga": tga_src, "dgs10": dgs10_src, "vix": vix_src},
        "status": status,
    }
