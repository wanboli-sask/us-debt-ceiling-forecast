import os
import re
from datetime import datetime, timedelta

import pandas as pd

try:
    from fredapi import Fred
except ImportError:
    Fred = None

from dotenv import load_dotenv
from config import BASE_DIR

load_dotenv(BASE_DIR / ".env")

FRED_KEY_URL = "https://fred.stlouisfed.org/docs/api/api_key.html"
FRED_KEY_PATTERN = re.compile(r"^[a-z0-9]{32}$")
FRED_PLACEHOLDER_KEYS = {
    "your_fred_api_key_here",
    "your_32_char_key",
    "your_32_char_key_here",
    "paste_your_key_here",
}

FRED_SERIES = {
    "tga": "WTREGEN",
    "dgs10": "DGS10",
    "vix": "VIXCLS",
}


def _read_fred_key() -> str:
    return os.getenv("FRED_API_KEY", "").strip()


def _is_valid_fred_key(key: str) -> bool:
    return bool(key) and bool(FRED_KEY_PATTERN.match(key))


def _fred_key_state() -> tuple[str | None, str]:
    """Return (usable_key_or_none, state) where state is missing|placeholder|invalid|valid."""
    key = _read_fred_key()
    if not key:
        return None, "missing"
    if key.lower() in FRED_PLACEHOLDER_KEYS:
        return None, "placeholder"
    if not _is_valid_fred_key(key):
        return None, "invalid"
    return key, "valid"


def get_fred_status() -> dict:
    key, state = _fred_key_state()
    connected = False
    if state == "missing":
        message_en = "FRED API key not configured — using fallback values."
        message_zh = "未配置 FRED API 密钥 — 使用默认值。"
        return {
            "configured": False,
            "connected": False,
            "message_en": message_en,
            "message_zh": message_zh,
        }
    if state == "placeholder":
        message_en = (
            "FRED API key is still a placeholder. Register for a free 32-character key at "
            f"{FRED_KEY_URL} and set FRED_API_KEY in .env — using fallback values."
        )
        message_zh = (
            "FRED API 密钥仍为占位符。请在 "
            f"{FRED_KEY_URL} 免费注册获取 32 位密钥并写入 .env — 当前使用默认值。"
        )
        return {
            "configured": False,
            "connected": False,
            "message_en": message_en,
            "message_zh": message_zh,
        }
    if state == "invalid":
        message_en = (
            "FRED API key must be a 32-character lowercase alphanumeric string. "
            f"Get one at {FRED_KEY_URL} — using fallback values."
        )
        message_zh = (
            "FRED API 密钥须为 32 位小写字母数字。请在 "
            f"{FRED_KEY_URL} 获取 — 当前使用默认值。"
        )
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
        "configured": True,
        "connected": connected,
        "message_en": message_en,
        "message_zh": message_zh,
    }


def _get_fred():
    key, state = _fred_key_state()
    if Fred and state == "valid" and key:
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
