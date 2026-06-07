import threading
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

_lock = threading.Lock()
TICKERS = {
    "spx": "^GSPC",
    "tlt": "TLT",
    "vix": "^VIX",
}


def _download(ticker: str, period: str = "6mo") -> pd.DataFrame:
    with _lock:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def get_latest_prices() -> dict:
    out = {}
    for key, ticker in TICKERS.items():
        try:
            df = _download(ticker, "5d")
            if df.empty:
                continue
            close = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2]) if len(df) > 1 else close
            out[key] = {
                "close": close,
                "daily_return": (close - prev) / prev if prev else 0,
            }
        except Exception:
            out[key] = {"close": None, "daily_return": 0}
    return out


def get_history(ticker_key: str, days: int = 180) -> pd.DataFrame:
    ticker = TICKERS.get(ticker_key, ticker_key)
    period = "1y" if days > 90 else "6mo"
    df = _download(ticker, period)
    if df.empty:
        return df
    cutoff = datetime.now() - timedelta(days=days)
    df = df[df.index >= pd.Timestamp(cutoff)]
    return df



def download_range(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download OHLC for a specific calendar date range."""
    with _lock:
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def compute_window_metrics(vote_date: str, window: int = 15) -> dict:
    """Compute ±window-day market metrics around a historical vote date."""
    center = pd.Timestamp(vote_date)
    pad = window + 10
    start = (center - timedelta(days=pad)).strftime("%Y-%m-%d")
    end = (center + timedelta(days=pad)).strftime("%Y-%m-%d")

    tickers = {"spx": "^GSPC", "tlt": "TLT", "vix": "^VIX", "tnx": "^TNX"}
    series: dict[str, pd.Series] = {}
    for key, sym in tickers.items():
        df = download_range(sym, start, end)
        if not df.empty and "Close" in df.columns:
            s = df["Close"].dropna()
            if not s.empty:
                series[key] = s

    def period_return(close: pd.Series, d0: pd.Timestamp, d1: pd.Timestamp) -> float:
        if close.empty or not isinstance(close.index, pd.DatetimeIndex):
            return 0.0
        sub = close[(close.index >= d0) & (close.index <= d1)]
        if len(sub) < 2:
            return 0.0
        return float(sub.iloc[-1] / sub.iloc[0] - 1)

    def level_change_bps(close: pd.Series, d0: pd.Timestamp, d1: pd.Timestamp) -> float:
        if close.empty or not isinstance(close.index, pd.DatetimeIndex):
            return 0.0
        sub = close[(close.index >= d0) & (close.index <= d1)]
        if len(sub) < 2:
            return 0.0
        return float((sub.iloc[-1] - sub.iloc[0]) * 100)

    before_start = center - timedelta(days=window)
    before_end = center - timedelta(days=1)
    after_start = center
    after_end = center + timedelta(days=window)

    spx = series.get("spx", pd.Series(dtype=float))
    tlt = series.get("tlt", pd.Series(dtype=float))
    vix = series.get("vix", pd.Series(dtype=float))
    tnx = series.get("tnx", pd.Series(dtype=float))

    vix_change_before = 0.0
    if not vix.empty and isinstance(vix.index, pd.DatetimeIndex):
        vix_before = vix[(vix.index >= before_start) & (vix.index <= before_end)]
        if len(vix_before) >= 2:
            vix_change_before = float(vix_before.iloc[-1] / vix_before.iloc[0] - 1)

    tlt_before = period_return(tlt, before_start, before_end)
    tlt_after = period_return(tlt, after_start, after_end)
    if tlt.empty and not tnx.empty:
        tlt_before = -period_return(tnx, before_start, before_end) * 0.1
        tlt_after = -period_return(tnx, after_start, after_end) * 0.1

    return {
        "spx_return_15d_before": period_return(spx, before_start, before_end),
        "spx_return_15d_after": period_return(spx, after_start, after_end),
        "tlt_return_15d_before": tlt_before,
        "tlt_return_15d_after": tlt_after,
        "dgs10_change_bps_15d_before": level_change_bps(tnx, before_start, before_end),
        "dgs10_change_bps_15d_after": level_change_bps(tnx, after_start, after_end),
        "vix_change_15d_before": vix_change_before,
    }


def classify_vix_fear(level: float) -> dict:
    """Classify VIX level into fear zones."""
    if level is None or level <= 0:
        return {"level_en": "Unknown", "level_zh": "未知", "color": "#95a5a6"}
    if level < 15:
        return {"level_en": "Low Fear", "level_zh": "低恐慌", "color": "#2ecc71"}
    if level < 20:
        return {"level_en": "Normal", "level_zh": "正常", "color": "#3498db"}
    if level < 30:
        return {"level_en": "Elevated", "level_zh": "升高", "color": "#f39c12"}
    if level < 40:
        return {"level_en": "High Fear", "level_zh": "高恐慌", "color": "#e67e22"}
    return {"level_en": "Extreme Fear", "level_zh": "极度恐慌", "color": "#e74c3c"}


def get_vix_summary() -> dict:
    """Latest VIX (^VIX) with fear classification and 90-day history."""
    try:
        df = get_history("vix", days=120)
        latest = get_latest_prices().get("vix", {})
        close = latest.get("close")
        daily_ret = latest.get("daily_return", 0)

        if close is None and not df.empty:
            close = float(df["Close"].iloc[-1])
            if len(df) > 1:
                prev = float(df["Close"].iloc[-2])
                daily_ret = (close - prev) / prev if prev else 0

        ret_15d = 0.0
        if not df.empty and len(df) >= 15:
            ret_15d = float(df["Close"].iloc[-1] / df["Close"].iloc[-15] - 1)

        fear = classify_vix_fear(close)
        return {
            "close": close,
            "daily_return": daily_ret,
            "return_15d": ret_15d,
            "fear_level_en": fear["level_en"],
            "fear_level_zh": fear["level_zh"],
            "fear_color": fear["color"],
            "history": df,
        }
    except Exception:
        return {
            "close": None,
            "daily_return": 0,
            "return_15d": 0,
            "fear_level_en": "Unknown",
            "fear_level_zh": "未知",
            "fear_color": "#95a5a6",
            "history": pd.DataFrame(),
        }


def compute_return_around_date(ticker_key: str, center_date: str, window: int = 15) -> float:
    df = get_history(ticker_key, days=365)
    if df.empty:
        return 0.0
    center = pd.Timestamp(center_date)
    start = center - timedelta(days=window)
    end = center + timedelta(days=window)
    sub = df[(df.index >= start) & (df.index <= end)]
    if len(sub) < 2:
        return 0.0
    before = sub[sub.index < center]
    after = sub[sub.index >= center]
    if before.empty or after.empty:
        return 0.0
    return float(after["Close"].iloc[-1] / before["Close"].iloc[0] - 1)
