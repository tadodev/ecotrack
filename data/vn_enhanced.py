# data/vn_enhanced.py
import datetime as dt
import logging
import time
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import requests
import streamlit as st
from analysis.indicators import calculate_rsi, get_market_sentiment
from constants_enhanced import VN_MAJOR_STOCKS

logger = logging.getLogger(__name__)

# TCBS API endpoints
TCBS_BARS_URL = "https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/bars-long-term"
TCBS_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://tcbs.com.vn",
    "Referer": "https://tcbs.com.vn/",
}

# Comprehensive index tracking
VIETNAM_INDICES = {
    "VNINDEX": {"name": "VN-Index", "exchange": "HOSE", "type": "index"},
    "VN30": {"name": "VN30", "exchange": "HOSE", "type": "index"},
    "HNXINDEX": {"name": "HNX-Index", "exchange": "HNX", "type": "index"},
    "HNX30": {"name": "HNX30", "exchange": "HNX", "type": "index"},
    "UPCOMINDEX": {"name": "UPCOM-Index", "exchange": "UPCOM", "type": "index"},
}

# VN30 constituent stocks (top 30 by market cap - approximate list)
VN30_STOCKS = [
    'VCB', 'BID', 'CTG', 'TCB', 'MBB', 'VPB', 'ACB', 'TPB', 'STB',  # Banking
    'VHM', 'VIC', 'VRE', 'KDH', 'NVL', 'DXG', 'BCM',  # Real Estate
    'VNM', 'MSN', 'MWG', 'PNJ', 'SAB',  # Consumer
    'GAS', 'PLX', 'POW', 'REE',  # Utilities/Energy
    'HPG', 'HSG', 'NKG',  # Industrials
    'FPT', 'CMG',  # Technology
    'VJC'  # Services
]


def _epoch(d: dt.date) -> int:
    return int(time.mktime(dt.datetime(d.year, d.month, d.day, 0, 0, 0).timetuple()))


def _tcbs_bars(symbol: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    """Get OHLCV data from TCBS API."""
    params = {
        "ticker": symbol.upper(),
        "type": "index" if symbol.upper() in VIETNAM_INDICES else "stock",
        "resolution": "D",
        "from": _epoch(start),
        "to": _epoch(end),
    }

    try:
        r = requests.get(TCBS_BARS_URL, headers=TCBS_HEADERS, params=params, timeout=12)
        r.raise_for_status()
        data = r.json().get("data", [])

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df.columns = [c.lower() for c in df.columns]

        # Handle different date formats
        if "tradingdate" in df.columns:
            dates = pd.to_datetime(df["tradingdate"]).dt.tz_localize("Asia/Ho_Chi_Minh")
        elif "time" in df.columns:
            dates = pd.to_datetime(df["time"], unit="ms").dt.tz_localize("Asia/Ho_Chi_Minh")
        else:
            dates = pd.date_range(start=start, end=end, freq="B", tz="Asia/Ho_Chi_Minh")[:len(df)]

        df["date"] = dates

        for col in ("open", "high", "low", "close", "volume"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                df[col] = np.nan

        df["code"] = symbol.upper()
        return df[["code", "date", "open", "high", "low", "close", "volume"]].sort_values("date")

    except Exception as e:
        logger.error(f"TCBS bars error for {symbol}: {e}")
        return pd.DataFrame()


def _calculate_technical_indicators(df: pd.DataFrame) -> Dict:
    """Calculate comprehensive technical indicators."""
    if df.empty or 'close' not in df:
        return {}

    close = df['close'].dropna()
    if len(close) < 20:
        return {}

    indicators = {}

    # RSI
    rsi = calculate_rsi(close)
    if len(rsi.dropna()) > 0:
        indicators['rsi'] = float(rsi.iloc[-1])
        indicators['rsi_signal'], indicators['rsi_sentiment'] = get_market_sentiment(indicators['rsi'])

    # Moving Averages
    if len(close) >= 20:
        indicators['sma_20'] = float(close.rolling(20).mean().iloc[-1])
    if len(close) >= 50:
        indicators['sma_50'] = float(close.rolling(50).mean().iloc[-1])
    if len(close) >= 200:
        indicators['sma_200'] = float(close.rolling(200).mean().iloc[-1])

    # Bollinger Bands
    if len(close) >= 20:
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        indicators['bb_upper'] = float((sma20 + 2 * std20).iloc[-1])
        indicators['bb_lower'] = float((sma20 - 2 * std20).iloc[-1])
        indicators['bb_position'] = float((close.iloc[-1] - indicators['bb_lower']) /
                                          (indicators['bb_upper'] - indicators['bb_lower']))

    # Support and Resistance
    if len(close) >= 20:
        recent_high = close.rolling(20).max().iloc[-1]
        recent_low = close.rolling(20).min().iloc[-1]
        indicators['resistance'] = float(recent_high)
        indicators['support'] = float(recent_low)

    # Volatility (20-day)
    if len(close) >= 20:
        returns = close.pct_change().dropna()
        if len(returns) >= 20:
            indicators['volatility_20d'] = float(returns.rolling(20).std().iloc[-1] * np.sqrt(252) * 100)

    return indicators


def _last_change_pct(series: pd.Series) -> Optional[float]:
    """Calculate last period percentage change."""
    series = series.dropna()
    if len(series) < 2:
        return None
    prev, last = float(series.iloc[-2]), float(series.iloc[-1])
    if prev == 0:
        return None
    return (last / prev - 1.0) * 100.0


@st.cache_data(ttl=900)
def get_comprehensive_vn_market_data() -> Dict:
    """Get comprehensive Vietnam market data including all major indices."""
    data = {}
    today = dt.date.today()
    start_recent = today - dt.timedelta(days=14)
    start_analysis = today - dt.timedelta(days=180)

    try:
        # Get all major indices
        indices_data = {}
        for code, info in VIETNAM_INDICES.items():
            df_recent = _tcbs_bars(code, start_recent, today)
            if not df_recent.empty:
                price = float(df_recent["close"].iloc[-1])
                change_pct = _last_change_pct(df_recent["close"]) or 0.0
                volume = float(df_recent["volume"].iloc[-1]) if "volume" in df_recent else 0.0

                # Get technical indicators with longer history
                df_long = _tcbs_bars(code, start_analysis, today)
                technical = _calculate_technical_indicators(df_long)

                indices_data[code.lower()] = {
                    "name": info["name"],
                    "price": price,
                    "change_pct": change_pct,
                    "volume": volume,
                    "exchange": info["exchange"],
                    **technical
                }

        data["indices"] = indices_data

        # Enhanced sector analysis
        data["sectors"] = get_enhanced_sector_performance()

        # VN30 specific analysis
        data["vn30_analysis"] = get_vn30_analysis()

        # Top stocks with more metrics
        data["top_stocks"] = get_enhanced_top_stocks_performance()

        # Market breadth analysis
        data["market_breadth"] = calculate_market_breadth()

        # Market correlation analysis
        data["correlations"] = calculate_market_correlations()

    except Exception as e:
        logger.error(f"Comprehensive VN market data error: {e}")
        data["error"] = str(e)

    return data


@st.cache_data(ttl=1800)
def get_enhanced_sector_performance() -> Dict[str, Dict]:
    """Enhanced sector performance with more metrics."""
    today = dt.date.today()
    start = today - dt.timedelta(days=30)  # More data for better analysis
    sectors = {}

    for sector, tickers in VN_MAJOR_STOCKS.items():
        stats = []
        for ticker in list(dict.fromkeys(tickers)):
            df = _tcbs_bars(ticker, start, today)
            if df.empty:
                continue

            close_series = df["close"].dropna()
            if len(close_series) < 2:
                continue

            current_price = float(close_series.iloc[-1])
            daily_change = _last_change_pct(close_series) or 0.0
            volume = float(df["volume"].iloc[-1]) if "volume" in df else 0.0

            # Weekly and monthly performance
            weekly_change = 0.0
            monthly_change = 0.0
            if len(close_series) >= 7:
                weekly_change = ((current_price / float(close_series.iloc[-7])) - 1) * 100
            if len(close_series) >= 21:
                monthly_change = ((current_price / float(close_series.iloc[-21])) - 1) * 100

            stats.append({
                "symbol": ticker,
                "price": current_price,
                "change_1d": daily_change,
                "change_1w": weekly_change,
                "change_1m": monthly_change,
                "volume": volume
            })

        if stats:
            sectors[sector] = {
                "stock_count": len(stats),
                "avg_return_1d": float(np.mean([s["change_1d"] for s in stats])),
                "avg_return_1w": float(np.mean([s["change_1w"] for s in stats])),
                "avg_return_1m": float(np.mean([s["change_1m"] for s in stats])),
                "total_volume": float(np.sum([s["volume"] for s in stats])),
                "winners": len([s for s in stats if s["change_1d"] > 0]),
                "losers": len([s for s in stats if s["change_1d"] < 0]),
                "best_performer": max(stats, key=lambda x: x["change_1d"])["symbol"],
                "worst_performer": min(stats, key=lambda x: x["change_1d"])["symbol"],
                "stocks": stats
            }

    return sectors


@st.cache_data(ttl=1200)
def get_vn30_analysis() -> Dict:
    """Detailed VN30 analysis including constituent performance."""
    today = dt.date.today()
    start = today - dt.timedelta(days=30)

    vn30_stocks = []
    for stock in VN30_STOCKS:
        df = _tcbs_bars(stock, start, today)
        if df.empty:
            continue

        close_series = df["close"].dropna()
        if len(close_series) < 2:
            continue

        current_price = float(close_series.iloc[-1])
        daily_change = _last_change_pct(close_series) or 0.0
        volume = float(df["volume"].iloc[-1]) if "volume" in df else 0.0

        # Calculate contribution to VN30 (simplified - equal weight assumption)
        contribution = daily_change / len(VN30_STOCKS)

        vn30_stocks.append({
            "symbol": stock,
            "price": current_price,
            "change_pct": daily_change,
            "volume": volume,
            "contribution": contribution
        })

    # Sort by contribution to index
    vn30_stocks.sort(key=lambda x: abs(x["contribution"]), reverse=True)

    # Calculate VN30 metrics
    if vn30_stocks:
        avg_change = np.mean([s["change_pct"] for s in vn30_stocks])
        total_volume = np.sum([s["volume"] for s in vn30_stocks])
        advancing = len([s for s in vn30_stocks if s["change_pct"] > 0])
        declining = len([s for s in vn30_stocks if s["change_pct"] < 0])

        return {
            "constituents": vn30_stocks,
            "avg_change": float(avg_change),
            "total_volume": float(total_volume),
            "advancing": advancing,
            "declining": declining,
            "unchanged": len(vn30_stocks) - advancing - declining,
            "advance_decline_ratio": advancing / declining if declining > 0 else None,
            "top_contributors": vn30_stocks[:5],
            "top_detractors": sorted(vn30_stocks, key=lambda x: x["contribution"])[:5]
        }

    return {}


@st.cache_data(ttl=1200)
def get_enhanced_top_stocks_performance(limit: int = 30) -> List[Dict]:
    """Enhanced top stocks performance with more metrics."""
    today = dt.date.today()
    start = today - dt.timedelta(days=30)

    all_stocks = []
    for sector_stocks in VN_MAJOR_STOCKS.values():
        all_stocks.extend(sector_stocks)
    all_stocks.extend(VN30_STOCKS)  # Include VN30 stocks

    unique_stocks = list(dict.fromkeys(all_stocks))
    stock_data = []

    for stock in unique_stocks:
        df = _tcbs_bars(stock, start, today)
        if df.empty:
            continue

        close_series = df["close"].dropna()
        if len(close_series) < 2:
            continue

        current_price = float(close_series.iloc[-1])
        daily_change = _last_change_pct(close_series) or 0.0
        volume = float(df["volume"].iloc[-1]) if "volume" in df else 0.0

        # Additional metrics
        weekly_change = 0.0
        monthly_change = 0.0
        if len(close_series) >= 7:
            weekly_change = ((current_price / float(close_series.iloc[-7])) - 1) * 100
        if len(close_series) >= 21:
            monthly_change = ((current_price / float(close_series.iloc[-21])) - 1) * 100

        # Volume analysis
        avg_volume = float(df["volume"].rolling(10).mean().iloc[-1]) if len(df) >= 10 else volume
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0

        # Find sector
        sector = "Other"
        for s, stocks in VN_MAJOR_STOCKS.items():
            if stock in stocks:
                sector = s
                break

        stock_data.append({
            "symbol": stock,
            "sector": sector,
            "price": current_price,
            "change_pct": daily_change,
            "change_1w": weekly_change,
            "change_1m": monthly_change,
            "volume": volume,
            "avg_volume_10d": avg_volume,
            "volume_ratio": volume_ratio,
            "is_vn30": stock in VN30_STOCKS
        })

    # Sort by daily performance
    stock_data.sort(key=lambda x: x["change_pct"], reverse=True)
    return stock_data[:limit]


@st.cache_data(ttl=1800)
def calculate_market_breadth() -> Dict:
    """Calculate market breadth indicators."""
    today = dt.date.today()
    start = today - dt.timedelta(days=7)

    all_stocks = []
    for stocks in VN_MAJOR_STOCKS.values():
        all_stocks.extend(stocks)
    all_stocks.extend(VN30_STOCKS)
    unique_stocks = list(dict.fromkeys(all_stocks))

    advancing = 0
    declining = 0
    unchanged = 0
    total_volume_up = 0
    total_volume_down = 0

    for stock in unique_stocks:
        df = _tcbs_bars(stock, start, today)
        if df.empty:
            continue

        change = _last_change_pct(df["close"])
        volume = float(df["volume"].iloc[-1]) if len(df) > 0 else 0

        if change is None:
            continue

        if change > 0.1:  # > 0.1% threshold
            advancing += 1
            total_volume_up += volume
        elif change < -0.1:  # < -0.1% threshold
            declining += 1
            total_volume_down += volume
        else:
            unchanged += 1

    total_stocks = advancing + declining + unchanged

    if total_stocks == 0:
        return {}

    return {
        "advancing": advancing,
        "declining": declining,
        "unchanged": unchanged,
        "advance_decline_ratio": advancing / declining if declining > 0 else None,
        "advance_decline_line": (advancing - declining) / total_stocks * 100,
        "up_volume": total_volume_up,
        "down_volume": total_volume_down,
        "volume_ratio": total_volume_up / total_volume_down if total_volume_down > 0 else None,
        "breadth_momentum": "Positive" if advancing > declining else "Negative" if declining > advancing else "Neutral"
    }


@st.cache_data(ttl=1800)
def calculate_market_correlations() -> Dict:
    """Calculate correlations between major indices and sectors."""
    today = dt.date.today()
    start = today - dt.timedelta(days=90)

    correlations = {}

    try:
        # Get data for major indices
        vnindex_df = _tcbs_bars("VNINDEX", start, today)
        vn30_df = _tcbs_bars("VN30", start, today)

        if not vnindex_df.empty and not vn30_df.empty:
            # Calculate correlation between VN-Index and VN30
            merged_df = pd.merge(
                vnindex_df[['date', 'close']].rename(columns={'close': 'vnindex'}),
                vn30_df[['date', 'close']].rename(columns={'close': 'vn30'}),
                on='date'
            )

            if len(merged_df) > 30:
                vni_returns = merged_df['vnindex'].pct_change().dropna()
                vn30_returns = merged_df['vn30'].pct_change().dropna()

                if len(vni_returns) > 20 and len(vn30_returns) > 20:
                    correlation = vni_returns.corr(vn30_returns)
                    correlations['vnindex_vn30'] = float(correlation)

        # Sector correlations with VN-Index would go here
        # (simplified for now due to complexity)

    except Exception as e:
        logger.error(f"Correlation calculation error: {e}")

    return correlations


@st.cache_data(ttl=900)
def get_index_history(index_code: str, days: int = 90) -> pd.DataFrame:
    """Get historical data for any Vietnam index."""
    today = dt.date.today()
    start = today - dt.timedelta(days=days)
    df = _tcbs_bars(index_code, start, today)

    if df.empty:
        return df

    return df.set_index("date")[["open", "high", "low", "close", "volume"]].copy()