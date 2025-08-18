# data/vn.py
import datetime as dt
import logging
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import requests
import streamlit as st

from analysis.indicators import calculate_rsi, get_market_sentiment
from constants import VN_MAJOR_STOCKS

logger = logging.getLogger(__name__)

# TCBS public API used by vnstock explorer/tcbs
# See: vnstock README (tcbs explorer import) and community examples of 'bars-long-term' usage.
TCBS_BARS_URL = "https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/bars-long-term"
TCBS_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://tcbs.com.vn",
    "Referer": "https://tcbs.com.vn/",
}

INDEX_CODES = {"VNINDEX", "HNXINDEX", "UPCOMINDEX", "VN30", "HNX30"}


def _epoch(d: dt.date) -> int:
    return int(time.mktime(dt.datetime(d.year, d.month, d.day, 0, 0, 0).timetuple()))


def _tcbs_bars(symbol: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    """
    Daily OHLCV for a single symbol via TCBS 'bars-long-term'.
    Returns columns: ['code','date','open','high','low','close','volume'] (tz=Asia/Ho_Chi_Minh).
    """
    params = {
        "ticker": symbol.upper(),
        "type": "index" if symbol.upper() in INDEX_CODES else "stock",
        "resolution": "D",
        "from": _epoch(start),
        "to": _epoch(end),
    }
    try:
        r = requests.get(TCBS_BARS_URL, headers=TCBS_HEADERS, params=params, timeout=12)
        r.raise_for_status()
        js = r.json() or {}
        rows = js.get("data") or []
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame()
        # Normalize
        df.columns = [c.lower() for c in df.columns]
        # tradingDate sometimes looks like '2025-06-20T00:00:00+07:00'
        if "tradingdate" in df.columns:
            t = pd.to_datetime(df["tradingdate"]).dt.tz_convert("Asia/Ho_Chi_Minh") if hasattr(
                pd.to_datetime(df["tradingdate"]), "dt"
            ) else pd.to_datetime(df["tradingdate"]).tz_localize("Asia/Ho_Chi_Minh")
        elif "time" in df.columns:
            # occasionally milliseconds epoch
            t = pd.to_datetime(df["time"], unit="ms").dt.tz_localize("Asia/Ho_Chi_Minh")
        else:
            t = pd.date_range(start=start, end=end, freq="B", tz="Asia/Ho_Chi_Minh")[: len(df)]
        df["date"] = t

        for c in ("open", "high", "low", "close", "volume"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            else:
                df[c] = np.nan

        df["code"] = symbol.upper()
        out = df[["code", "date", "open", "high", "low", "close", "volume"]].sort_values("date")
        return out
    except Exception as e:
        logger.error(f"TCBS bars error for {symbol}: {e}")
        return pd.DataFrame()


def _last_change_pct(s: pd.Series) -> Optional[float]:
    s = s.dropna()
    if len(s) < 2: return None
    prev, last = float(s.iloc[-2]), float(s.iloc[-1])
    if prev == 0: return None
    return (last / prev - 1.0) * 100.0


@st.cache_data(ttl=900)
def get_enhanced_vn_data() -> Dict:
    """
    VN-Index snapshot + technicals + sectors + top stocks (TCBS).
    Shape identical to your previous data layer so the UI doesn’t change.
    """
    data: Dict = {}
    try:
        today = dt.date.today()
        start_14 = today - dt.timedelta(days=14)
        start_180 = today - dt.timedelta(days=180)

        # --- VNINDEX snapshot ---
        idx_df = _tcbs_bars("VNINDEX", start_14, today)
        if not idx_df.empty:
            price = float(idx_df["close"].dropna().iloc[-1])
            change_pct = _last_change_pct(idx_df["close"]) or 0.0
            vol = float(idx_df["volume"].dropna().iloc[-1]) if "volume" in idx_df else 0.0
            data["vnindex"] = {"price": price, "change_pct": change_pct, "volume": vol}

            # --- Technicals (RSI / SMA / Support-Resistance) ---
            idx_hist = _tcbs_bars("VNINDEX", start_180, today)
            closes = idx_hist["close"].dropna()
            if not closes.empty:
                rsi = calculate_rsi(closes)
                if rsi is not None and len(rsi.dropna()) > 0:
                    rv = float(rsi.iloc[-1])
                    sig, senti = get_market_sentiment(rv)
                    data["vnindex"].update({"rsi": rv, "rsi_signal": sig, "rsi_sentiment": senti})
                if len(closes) >= 50:
                    data["vnindex"].update({
                        "resistance": float(closes.rolling(20).max().iloc[-1]),
                        "support": float(closes.rolling(20).min().iloc[-1]),
                        "sma_50": float(closes.rolling(50).mean().iloc[-1]),
                    })

        # --- Sectors & top stocks (computed from daily % change over last two bars) ---
        data["sectors"] = get_sector_performance()
        data["top_stocks"] = get_top_stocks_performance()

    except Exception as e:
        logger.error(f"VN data error: {e}")
        data["error"] = str(e)

    return data


@st.cache_data(ttl=1800)
def get_sector_performance() -> Dict[str, Dict]:
    today = dt.date.today()
    start = today - dt.timedelta(days=14)
    sectors: Dict[str, Dict] = {}

    for sector, tickers in VN_MAJOR_STOCKS.items():
        stats = []
        for t in list(dict.fromkeys(tickers)):  # unique & preserve order
            df = _tcbs_bars(t, start, today)
            if df.empty:
                continue
            close = float(df["close"].dropna().iloc[-1])
            chg = _last_change_pct(df["close"]) or 0.0
            vol = float(df["volume"].dropna().iloc[-1]) if "volume" in df else 0.0
            stats.append({"symbol": t, "price": close, "change_pct": chg, "volume": vol})

        if stats:
            sectors[sector] = {
                "avg_return": float(np.mean([s["change_pct"] for s in stats])),
                "total_volume": float(np.sum([s["volume"] for s in stats])),
                "stock_count": len(stats),
            }
    return sectors


@st.cache_data(ttl=1800)
def get_top_stocks_performance(limit: int = 20) -> List[Dict]:
    today = dt.date.today()
    start = today - dt.timedelta(days=14)

    all_ticks: List[str] = []
    for lst in VN_MAJOR_STOCKS.values():
        all_ticks.extend(lst)
    uniq = list(dict.fromkeys(all_ticks))

    out: List[Dict] = []
    for t in uniq:
        df = _tcbs_bars(t, start, today)
        if df.empty:
            continue
        close = float(df["close"].dropna().iloc[-1])
        chg = _last_change_pct(df["close"]) or 0.0
        vol = float(df["volume"].dropna().iloc[-1]) if "volume" in df else 0.0
        out.append({"symbol": t, "price": close, "change_pct": chg, "volume": vol})

    out.sort(key=lambda x: x["change_pct"], reverse=True)
    return out[:limit]


@st.cache_data(ttl=900)
def get_vnindex_history(days: int = 90) -> pd.DataFrame:
    """
    For candlestick charts: returns DataFrame with index=date, cols=open/high/low/close/volume.
    """
    today = dt.date.today()
    start = today - dt.timedelta(days=days)
    df = _tcbs_bars("VNINDEX", start, today)
    if df.empty:
        return df
    out = df.set_index("date")[["open", "high", "low", "close", "volume"]].copy()
    return out
