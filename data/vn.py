# data/vn.py - FIXED VERSION
import datetime as dt
import logging
import time
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import requests
import streamlit as st
from analysis.indicators import calculate_rsi, get_market_sentiment
from constants import VN_MAJOR_STOCKS

logger = logging.getLogger(__name__)

# TCBS API endpoints
TCBS_BARS_URL = "https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/bars-long-term"
TCBS_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://tcbs.com.vn",
    "Referer": "https://tcbs.com.vn/",
}

# Comprehensive index tracking - FIXED: Use correct TCBS symbols
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
    """Convert date to epoch timestamp."""
    return int(time.mktime(dt.datetime(d.year, d.month, d.day, 0, 0, 0).timetuple()))


def _is_valid_symbol(symbol: str) -> bool:
    """Check if symbol is valid for TCBS API."""
    if not symbol or not isinstance(symbol, str):
        return False

    # Filter out invalid symbols
    invalid_symbols = ['DESCRIPTION', 'NAME', 'ERROR', 'NULL', 'UNDEFINED']
    symbol_upper = symbol.upper().strip()

    if symbol_upper in invalid_symbols:
        return False

    # Must be alphanumeric and reasonable length
    if not symbol_upper.replace('-', '').replace('_', '').isalnum():
        return False

    if len(symbol_upper) > 10 or len(symbol_upper) < 2:
        return False

    return True


def _tcbs_bars(symbol: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    """Get OHLCV data from TCBS API - FIXED VERSION."""
    # Validate symbol first
    if not _is_valid_symbol(symbol):
        logger.warning(f"Invalid symbol '{symbol}' - skipping")
        return pd.DataFrame()

    symbol = symbol.upper().strip()

    params = {
        "ticker": symbol,
        "type": "index" if symbol in VIETNAM_INDICES else "stock",
        "resolution": "D",
        "from": _epoch(start),
        "to": _epoch(end),
    }

    try:
        r = requests.get(TCBS_BARS_URL, headers=TCBS_HEADERS, params=params, timeout=15)

        if not r.ok:
            logger.warning(f"TCBS API returned {r.status_code} for {symbol}: {r.text[:200]}")
            return pd.DataFrame()

        json_data = r.json()
        data = json_data.get("data", [])

        if not data:
            logger.info(f"No data returned for {symbol}")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        if df.empty:
            return df

        # Normalize column names
        df.columns = [c.lower().strip() for c in df.columns]

        # FIXED: Handle timezone-aware datetime properly
        dates = None

        if "tradingdate" in df.columns:
            try:
                dates = pd.to_datetime(df["tradingdate"], errors='coerce')
                # Only localize if not already timezone-aware
                if dates.dt.tz is None:
                    dates = dates.dt.tz_localize("Asia/Ho_Chi_Minh")
                else:
                    dates = dates.dt.tz_convert("Asia/Ho_Chi_Minh")
            except Exception as e:
                logger.warning(f"Date parsing error for {symbol}: {e}")

        elif "time" in df.columns:
            try:
                # Handle epoch timestamps
                dates = pd.to_datetime(df["time"], unit="ms", errors='coerce')
                if dates.dt.tz is None:
                    dates = dates.dt.tz_localize("UTC").dt.tz_convert("Asia/Ho_Chi_Minh")
            except Exception as e:
                logger.warning(f"Time parsing error for {symbol}: {e}")

        # Fallback to generated dates if parsing failed
        if dates is None or dates.isna().all():
            logger.info(f"Using fallback dates for {symbol}")
            dates = pd.date_range(
                start=start,
                periods=len(df),
                freq="B",
                tz="Asia/Ho_Chi_Minh"
            )

        df["date"] = dates

        # FIXED: Robust numeric conversion with better error handling
        numeric_cols = ["open", "high", "low", "close", "volume"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                df[col] = np.nan

        # Remove rows with all NaN price data
        price_cols = ["open", "high", "low", "close"]
        df = df.dropna(subset=price_cols, how='all')

        if df.empty:
            logger.info(f"No valid price data for {symbol}")
            return df

        df["code"] = symbol
        result_df = df[["code", "date", "open", "high", "low", "close", "volume"]].sort_values("date")

        logger.info(f"Successfully fetched {len(result_df)} records for {symbol}")
        return result_df

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching data for {symbol}")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {symbol}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"TCBS bars error for {symbol}: {e}")
        return pd.DataFrame()


def _calculate_technical_indicators(df: pd.DataFrame) -> Dict:
    """Calculate comprehensive technical indicators - ENHANCED ERROR HANDLING."""
    if df.empty or 'close' not in df:
        return {}

    try:
        close = df['close'].dropna()
        if len(close) < 5:  # Need minimum data points
            return {}

        indicators = {}

        # RSI - with error handling
        try:
            if len(close) >= 14:
                rsi = calculate_rsi(close)
                if len(rsi.dropna()) > 0:
                    indicators['rsi'] = float(rsi.iloc[-1])
                    indicators['rsi_signal'], indicators['rsi_sentiment'] = get_market_sentiment(indicators['rsi'])
        except Exception as e:
            logger.warning(f"RSI calculation error: {e}")

        # Moving Averages - with error handling
        try:
            if len(close) >= 20:
                sma_20 = close.rolling(20, min_periods=15).mean()
                if not sma_20.empty and not pd.isna(sma_20.iloc[-1]):
                    indicators['sma_20'] = float(sma_20.iloc[-1])

            if len(close) >= 50:
                sma_50 = close.rolling(50, min_periods=30).mean()
                if not sma_50.empty and not pd.isna(sma_50.iloc[-1]):
                    indicators['sma_50'] = float(sma_50.iloc[-1])

            if len(close) >= 200:
                sma_200 = close.rolling(200, min_periods=100).mean()
                if not sma_200.empty and not pd.isna(sma_200.iloc[-1]):
                    indicators['sma_200'] = float(sma_200.iloc[-1])
        except Exception as e:
            logger.warning(f"Moving averages calculation error: {e}")

        # Bollinger Bands
        try:
            if len(close) >= 20:
                sma20 = close.rolling(20, min_periods=15).mean()
                std20 = close.rolling(20, min_periods=15).std()
                if not sma20.empty and not std20.empty:
                    bb_upper = sma20 + 2 * std20
                    bb_lower = sma20 - 2 * std20
                    if not pd.isna(bb_upper.iloc[-1]) and not pd.isna(bb_lower.iloc[-1]):
                        indicators['bb_upper'] = float(bb_upper.iloc[-1])
                        indicators['bb_lower'] = float(bb_lower.iloc[-1])

                        # BB position
                        bb_range = indicators['bb_upper'] - indicators['bb_lower']
                        if bb_range > 0:
                            indicators['bb_position'] = float((close.iloc[-1] - indicators['bb_lower']) / bb_range)
        except Exception as e:
            logger.warning(f"Bollinger Bands calculation error: {e}")

        # Support and Resistance
        try:
            if len(close) >= 20:
                recent_high = close.rolling(20, min_periods=10).max().iloc[-1]
                recent_low = close.rolling(20, min_periods=10).min().iloc[-1]
                if not pd.isna(recent_high) and not pd.isna(recent_low):
                    indicators['resistance'] = float(recent_high)
                    indicators['support'] = float(recent_low)
        except Exception as e:
            logger.warning(f"Support/Resistance calculation error: {e}")

        # Volatility
        try:
            if len(close) >= 20:
                returns = close.pct_change().dropna()
                if len(returns) >= 20:
                    vol_20d = returns.rolling(20, min_periods=15).std()
                    if not vol_20d.empty and not pd.isna(vol_20d.iloc[-1]):
                        indicators['volatility_20d'] = float(vol_20d.iloc[-1] * np.sqrt(252) * 100)
        except Exception as e:
            logger.warning(f"Volatility calculation error: {e}")

        return indicators

    except Exception as e:
        logger.error(f"Technical indicators calculation failed: {e}")
        return {}


def _last_change_pct(series: pd.Series) -> Optional[float]:
    """Calculate last period percentage change - ENHANCED."""
    try:
        series = series.dropna()
        if len(series) < 2:
            return None

        prev, last = float(series.iloc[-2]), float(series.iloc[-1])

        if prev == 0 or pd.isna(prev) or pd.isna(last):
            return None

        change = (last / prev - 1.0) * 100.0

        # Sanity check for extreme values
        if abs(change) > 50:  # > 50% change is suspicious for daily data
            logger.warning(f"Extreme change detected: {change:.2f}%")

        return change
    except Exception:
        return None


@st.cache_data(ttl=900, show_spinner=False)
def get_comprehensive_vn_market_data() -> Dict:
    """Get comprehensive Vietnam market data including all major indices - FIXED."""
    data = {}
    today = dt.date.today()
    start_recent = today - dt.timedelta(days=14)
    start_analysis = today - dt.timedelta(days=180)

    logger.info("Starting comprehensive VN market data fetch...")

    try:
        # Get all major indices with better error handling
        indices_data = {}
        for code, info in VIETNAM_INDICES.items():
            logger.info(f"Fetching data for index: {code}")

            try:
                df_recent = _tcbs_bars(code, start_recent, today)
                if df_recent.empty:
                    logger.warning(f"No recent data for {code}")
                    continue

                price = float(df_recent["close"].iloc[-1])
                change_pct = _last_change_pct(df_recent["close"]) or 0.0
                volume = float(df_recent["volume"].iloc[-1]) if "volume" in df_recent and not pd.isna(
                    df_recent["volume"].iloc[-1]) else 0.0

                # Get technical indicators with longer history
                df_long = _tcbs_bars(code, start_analysis, today)
                technical = _calculate_technical_indicators(df_long) if not df_long.empty else {}

                indices_data[code.lower()] = {
                    "name": info["name"],
                    "price": price,
                    "change_pct": change_pct,
                    "volume": volume,
                    "exchange": info["exchange"],
                    **technical
                }

                logger.info(f"Successfully processed {code}: {price:.2f} ({change_pct:+.2f}%)")

            except Exception as e:
                logger.error(f"Error processing index {code}: {e}")
                continue

        data["indices"] = indices_data
        logger.info(f"Processed {len(indices_data)} indices")

        # Enhanced sector analysis with error handling
        try:
            data["sectors"] = get_enhanced_sector_performance()
            logger.info("Sector performance analysis completed")
        except Exception as e:
            logger.error(f"Sector analysis error: {e}")
            data["sectors"] = {}

        # VN30 specific analysis
        try:
            data["vn30_analysis"] = get_vn30_analysis()
            logger.info("VN30 analysis completed")
        except Exception as e:
            logger.error(f"VN30 analysis error: {e}")
            data["vn30_analysis"] = {}

        # Top stocks with more metrics
        try:
            data["top_stocks"] = get_enhanced_top_stocks_performance()
            logger.info("Top stocks analysis completed")
        except Exception as e:
            logger.error(f"Top stocks analysis error: {e}")
            data["top_stocks"] = []

        # Market breadth analysis
        try:
            data["market_breadth"] = calculate_market_breadth()
            logger.info("Market breadth analysis completed")
        except Exception as e:
            logger.error(f"Market breadth analysis error: {e}")
            data["market_breadth"] = {}

        # Market correlation analysis
        try:
            data["correlations"] = calculate_market_correlations()
            logger.info("Correlation analysis completed")
        except Exception as e:
            logger.error(f"Correlation analysis error: {e}")
            data["correlations"] = {}

        logger.info("Comprehensive VN market data fetch completed successfully")

    except Exception as e:
        logger.error(f"Comprehensive VN market data error: {e}")
        data["error"] = str(e)

    return data


@st.cache_data(ttl=1800, show_spinner=False)
def get_enhanced_sector_performance() -> Dict[str, Dict]:
    """Enhanced sector performance with more metrics - FIXED."""
    today = dt.date.today()
    start = today - dt.timedelta(days=30)
    sectors = {}

    for sector, tickers in VN_MAJOR_STOCKS.items():
        if not isinstance(tickers, (list, dict)):
            continue

        # Handle both dict and list formats
        stock_list = tickers.get('stocks', tickers) if isinstance(tickers, dict) else tickers

        stats = []
        for ticker in stock_list:
            if not _is_valid_symbol(ticker):
                continue

            try:
                df = _tcbs_bars(ticker, start, today)
                if df.empty:
                    continue

                close_series = df["close"].dropna()
                if len(close_series) < 2:
                    continue

                current_price = float(close_series.iloc[-1])
                daily_change = _last_change_pct(close_series) or 0.0
                volume = float(df["volume"].iloc[-1]) if "volume" in df and not pd.isna(df["volume"].iloc[-1]) else 0.0

                # Weekly and monthly performance
                weekly_change = 0.0
                monthly_change = 0.0
                if len(close_series) >= 7:
                    try:
                        weekly_change = ((current_price / float(close_series.iloc[-7])) - 1) * 100
                    except (IndexError, ZeroDivisionError):
                        pass

                if len(close_series) >= 21:
                    try:
                        monthly_change = ((current_price / float(close_series.iloc[-21])) - 1) * 100
                    except (IndexError, ZeroDivisionError):
                        pass

                stats.append({
                    "symbol": ticker,
                    "price": current_price,
                    "change_1d": daily_change,
                    "change_1w": weekly_change,
                    "change_1m": monthly_change,
                    "volume": volume
                })

            except Exception as e:
                logger.warning(f"Error processing {ticker} in sector {sector}: {e}")
                continue

        if stats:
            # Calculate sector metrics safely
            changes_1d = [s["change_1d"] for s in stats if s["change_1d"] is not None]
            changes_1w = [s["change_1w"] for s in stats if s["change_1w"] is not None]
            changes_1m = [s["change_1m"] for s in stats if s["change_1m"] is not None]
            volumes = [s["volume"] for s in stats if s["volume"] is not None]

            sectors[sector] = {
                "stock_count": len(stats),
                "avg_return_1d": float(np.mean(changes_1d)) if changes_1d else 0.0,
                "avg_return_1w": float(np.mean(changes_1w)) if changes_1w else 0.0,
                "avg_return_1m": float(np.mean(changes_1m)) if changes_1m else 0.0,
                "total_volume": float(np.sum(volumes)) if volumes else 0.0,
                "winners": len([s for s in stats if s["change_1d"] and s["change_1d"] > 0]),
                "losers": len([s for s in stats if s["change_1d"] and s["change_1d"] < 0]),
                "best_performer": max(stats, key=lambda x: x["change_1d"] or -999)["symbol"] if stats else None,
                "worst_performer": min(stats, key=lambda x: x["change_1d"] or 999)["symbol"] if stats else None,
                "stocks": stats
            }

    return sectors


@st.cache_data(ttl=1200, show_spinner=False)
def get_vn30_analysis() -> Dict:
    """Detailed VN30 analysis including constituent performance - FIXED."""
    today = dt.date.today()
    start = today - dt.timedelta(days=30)

    vn30_stocks = []
    for stock in VN30_STOCKS:
        if not _is_valid_symbol(stock):
            continue

        try:
            df = _tcbs_bars(stock, start, today)
            if df.empty:
                continue

            close_series = df["close"].dropna()
            if len(close_series) < 2:
                continue

            current_price = float(close_series.iloc[-1])
            daily_change = _last_change_pct(close_series) or 0.0
            volume = float(df["volume"].iloc[-1]) if "volume" in df and not pd.isna(df["volume"].iloc[-1]) else 0.0

            # Calculate contribution to VN30 (simplified - equal weight assumption)
            contribution = daily_change / len(VN30_STOCKS) if VN30_STOCKS else 0

            vn30_stocks.append({
                "symbol": stock,
                "price": current_price,
                "change_pct": daily_change,
                "volume": volume,
                "contribution": contribution
            })

        except Exception as e:
            logger.warning(f"Error processing VN30 stock {stock}: {e}")
            continue

    if not vn30_stocks:
        return {}

    # Sort by contribution to index
    vn30_stocks.sort(key=lambda x: abs(x["contribution"]), reverse=True)

    # Calculate VN30 metrics
    changes = [s["change_pct"] for s in vn30_stocks if s["change_pct"] is not None]
    volumes = [s["volume"] for s in vn30_stocks if s["volume"] is not None]

    avg_change = np.mean(changes) if changes else 0.0
    total_volume = np.sum(volumes) if volumes else 0.0
    advancing = len([s for s in vn30_stocks if s["change_pct"] and s["change_pct"] > 0])
    declining = len([s for s in vn30_stocks if s["change_pct"] and s["change_pct"] < 0])

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


@st.cache_data(ttl=1200, show_spinner=False)
def get_enhanced_top_stocks_performance(limit: int = 30) -> List[Dict]:
    """Enhanced top stocks performance with more metrics - FIXED."""
    today = dt.date.today()
    start = today - dt.timedelta(days=30)

    all_stocks = []
    for sector_data in VN_MAJOR_STOCKS.values():
        if isinstance(sector_data, dict):
            all_stocks.extend(sector_data.get('stocks', []))
        elif isinstance(sector_data, list):
            all_stocks.extend(sector_data)

    all_stocks.extend(VN30_STOCKS)
    unique_stocks = list(dict.fromkeys(all_stocks))  # Remove duplicates while preserving order

    stock_data = []

    for stock in unique_stocks:
        if not _is_valid_symbol(stock):
            continue

        try:
            df = _tcbs_bars(stock, start, today)
            if df.empty:
                continue

            close_series = df["close"].dropna()
            if len(close_series) < 2:
                continue

            current_price = float(close_series.iloc[-1])
            daily_change = _last_change_pct(close_series) or 0.0
            volume = float(df["volume"].iloc[-1]) if "volume" in df and not pd.isna(df["volume"].iloc[-1]) else 0.0

            # Additional metrics with error handling
            weekly_change = 0.0
            monthly_change = 0.0

            if len(close_series) >= 7:
                try:
                    weekly_change = ((current_price / float(close_series.iloc[-7])) - 1) * 100
                except (IndexError, ZeroDivisionError):
                    pass

            if len(close_series) >= 21:
                try:
                    monthly_change = ((current_price / float(close_series.iloc[-21])) - 1) * 100
                except (IndexError, ZeroDivisionError):
                    pass

            # Volume analysis
            avg_volume = 0.0
            volume_ratio = 1.0

            if len(df) >= 10:
                try:
                    avg_vol_series = df["volume"].rolling(10).mean()
                    if not avg_vol_series.empty and not pd.isna(avg_vol_series.iloc[-1]):
                        avg_volume = float(avg_vol_series.iloc[-1])
                        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
                except Exception:
                    pass

            # Find sector
            sector = "Other"
            for s, sector_data in VN_MAJOR_STOCKS.items():
                stocks_list = sector_data.get('stocks', sector_data) if isinstance(sector_data, dict) else sector_data
                if stock in stocks_list:
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

        except Exception as e:
            logger.warning(f"Error processing top stock {stock}: {e}")
            continue

    # Sort by daily performance
    stock_data.sort(key=lambda x: x["change_pct"] or -999, reverse=True)
    return stock_data[:limit]


@st.cache_data(ttl=1800, show_spinner=False)
def calculate_market_breadth() -> Dict:
    """Calculate market breadth indicators - FIXED."""
    today = dt.date.today()
    start = today - dt.timedelta(days=7)

    all_stocks = []
    for sector_data in VN_MAJOR_STOCKS.values():
        if isinstance(sector_data, dict):
            all_stocks.extend(sector_data.get('stocks', []))
        elif isinstance(sector_data, list):
            all_stocks.extend(sector_data)

    all_stocks.extend(VN30_STOCKS)
    unique_stocks = list(dict.fromkeys(all_stocks))

    advancing = 0
    declining = 0
    unchanged = 0
    total_volume_up = 0
    total_volume_down = 0

    for stock in unique_stocks:
        if not _is_valid_symbol(stock):
            continue

        try:
            df = _tcbs_bars(stock, start, today)
            if df.empty:
                continue

            change = _last_change_pct(df["close"])
            volume = float(df["volume"].iloc[-1]) if len(df) > 0 and "volume" in df and not pd.isna(
                df["volume"].iloc[-1]) else 0

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

        except Exception as e:
            logger.warning(f"Error calculating breadth for {stock}: {e}")
            continue

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


@st.cache_data(ttl=1800, show_spinner=False)
def calculate_market_correlations() -> Dict:
    """Calculate correlations between major indices and sectors - FIXED."""
    today = dt.date.today()
    start = today - dt.timedelta(days=90)
    correlations = {}

    try:
        # Get data for major indices
        vnindex_df = _tcbs_bars("VNINDEX", start, today)
        vn30_df = _tcbs_bars("VN30", start, today)

        if not vnindex_df.empty and not vn30_df.empty:
            try:
                # Calculate correlation between VN-Index and VN30
                merged_df = pd.merge(
                    vnindex_df[['date', 'close']].rename(columns={'close': 'vnindex'}),
                    vn30_df[['date', 'close']].rename(columns={'close': 'vn30'}),
                    on='date',
                    how='inner'
                )

                if len(merged_df) > 30:
                    vni_returns = merged_df['vnindex'].pct_change().dropna()
                    vn30_returns = merged_df['vn30'].pct_change().dropna()

                    if len(vni_returns) > 20 and len(vn30_returns) > 20:
                        correlation = vni_returns.corr(vn30_returns)
                        if not pd.isna(correlation):
                            correlations['vnindex_vn30'] = float(correlation)

            except Exception as e:
                logger.warning(f"Correlation calculation error: {e}")

        # Additional correlations could be added here
        logger.info("Correlation analysis completed")

    except Exception as e:
        logger.error(f"Correlation calculation error: {e}")

    return correlations


@st.cache_data(ttl=900, show_spinner=False)
def get_index_history(index_code: str, days: int = 90) -> pd.DataFrame:
    """Get historical data for any Vietnam index - FIXED."""
    if not _is_valid_symbol(index_code):
        logger.warning(f"Invalid index code: {index_code}")
        return pd.DataFrame()

    today = dt.date.today()
    start = today - dt.timedelta(days=days)

    try:
        df = _tcbs_bars(index_code, start, today)

        if df.empty:
            logger.info(f"No historical data found for {index_code}")
            return df

        # Ensure we have the required columns
        required_cols = ["open", "high", "low", "close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = np.nan

        return df.set_index("date")[required_cols].copy()

    except Exception as e:
        logger.error(f"Error fetching history for {index_code}: {e}")
        return pd.DataFrame()