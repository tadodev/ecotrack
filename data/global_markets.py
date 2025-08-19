# data/global_markets.py - FIXED VERSION
import logging
from typing import Dict, Optional, Tuple
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Properly mapped Yahoo Finance symbols
GLOBAL_INDICES = {
    '^GSPC': 'S&P 500',
    '^DJI': 'Dow Jones',
    '^IXIC': 'NASDAQ',
    '^FTSE': 'FTSE 100',
    '^N225': 'Nikkei 225',
    '^HSI': 'Hang Seng',
}

# Additional instruments
CURRENCIES_AND_COMMODITIES = {
    'EURUSD=X': 'EUR/USD',
    'GBPUSD=X': 'GBP/USD',
    'USDJPY=X': 'USD/JPY',
    'DX-Y.NYB': 'US Dollar Index',
    'CL=F': 'Crude Oil',
    'GC=F': 'Gold',
    'BTC-USD': 'Bitcoin',
    'USDVND=X': 'USD/VND'  # Vietnam Dong - may or may not work
}

# Vietnam-related ETFs and proxies
VN_RELATED_INSTRUMENTS = {
    'VEA': 'Vanguard Emerging Markets',
    'EEM': 'iShares MSCI Emerging Markets',
    'VWO': 'Vanguard Emerging Markets Stock',
    'FEM': 'First Trust Emerging Markets AlphaDEX'
}


def _safe_download(symbol: str, period: str = '7d', interval: str = '1d') -> Optional[pd.DataFrame]:
    """Safely download data from Yahoo Finance with comprehensive error handling."""
    try:
        # FIXED: Remove show_errors parameter that doesn't exist in older yfinance versions
        # Also handle different yfinance versions by trying different parameter combinations

        # First try with progress=False only
        try:
            hist = yf.download(symbol, period=period, interval=interval, progress=False)
        except TypeError:
            # If progress parameter doesn't work, try without it
            try:
                hist = yf.download(symbol, period=period, interval=interval)
            except Exception:
                # Last resort - use Ticker object approach
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period, interval=interval)

        if hist is None or hist.empty:
            logger.info(f"No data returned for {symbol}")
            return None

        # Check if we have the required columns
        if 'Close' not in hist.columns:
            logger.warning(f"No Close price data for {symbol}")
            return None

        # Need at least 2 data points for change calculation
        if len(hist) < 2:
            logger.info(f"Insufficient data for {symbol} (only {len(hist)} points)")
            return None

        # Clean the data
        hist = hist.dropna(subset=['Close'])

        if len(hist) < 2:
            logger.info(f"Insufficient clean data for {symbol}")
            return None

        return hist

    except Exception as e:
        logger.warning(f"Download failed for {symbol}: {e}")
        return None


def _calculate_change_metrics(hist: pd.DataFrame) -> Tuple[float, float, float]:
    """Calculate price change metrics from historical data."""
    try:
        close_prices = hist['Close'].dropna()

        if len(close_prices) < 2:
            return np.nan, np.nan, np.nan

        latest = float(close_prices.iloc[-1])
        prev = float(close_prices.iloc[-2])

        # Daily change
        daily_change = ((latest / prev) - 1) * 100 if prev != 0 else 0.0

        # Weekly change (if we have enough data)
        weekly_change = 0.0
        if len(close_prices) >= 7:
            try:
                week_ago = float(close_prices.iloc[-7])
                weekly_change = ((latest / week_ago) - 1) * 100 if week_ago != 0 else 0.0
            except (IndexError, ValueError):
                pass

        return latest, daily_change, weekly_change

    except Exception as e:
        logger.warning(f"Error calculating change metrics: {e}")
        return np.nan, np.nan, np.nan


@st.cache_data(ttl=3600, show_spinner=False)
def get_global_market_data() -> Dict:
    """Get global market data with enhanced error handling and Vietnam context."""
    data = {}

    logger.info("Fetching global market data...")

    # Process major indices
    indices_processed = 0
    for symbol, name in GLOBAL_INDICES.items():
        try:
            hist = _safe_download(symbol, period='7d', interval='1d')
            if hist is not None:
                latest, daily_change, weekly_change = _calculate_change_metrics(hist)

                if not pd.isna(latest):
                    data[symbol] = {
                        'name': name,
                        'price': latest,
                        'change_pct': daily_change,
                        'change_1w': weekly_change,
                        'currency': 'USD',
                        'category': 'index'
                    }
                    indices_processed += 1
                    logger.info(f"✅ {name}: {latest:.2f} ({daily_change:+.2f}%)")
                else:
                    logger.warning(f"❌ Invalid data for {symbol}")
            else:
                logger.warning(f"❌ No data available for {symbol}")

        except Exception as e:
            logger.error(f"❌ Failed to process {symbol}: {e}")
            continue

    logger.info(f"Successfully processed {indices_processed}/{len(GLOBAL_INDICES)} indices")

    # Process currencies and commodities
    fx_commodities_processed = 0
    for symbol, name in CURRENCIES_AND_COMMODITIES.items():
        try:
            hist = _safe_download(symbol, period='5d', interval='1d')  # Slightly shorter period for FX
            if hist is not None:
                latest, daily_change, weekly_change = _calculate_change_metrics(hist)

                if not pd.isna(latest):
                    # Determine category and currency
                    category = 'currency' if any(
                        x in symbol for x in ['USD', 'EUR', 'GBP', 'JPY', 'VND']) else 'commodity'
                    currency = 'USD' if category == 'commodity' or 'USD' in name else 'N/A'

                    data[symbol] = {
                        'name': name,
                        'price': latest,
                        'change_pct': daily_change,
                        'change_1w': weekly_change,
                        'currency': currency,
                        'category': category
                    }
                    fx_commodities_processed += 1
                    logger.info(
                        f"✅ {name}: {latest:.4f if category == 'currency' else latest:.2f} ({daily_change:+.2f}%)")

        except Exception as e:
            logger.warning(f"❌ Failed to process {symbol}: {e}")
            continue

    logger.info(f"Successfully processed {fx_commodities_processed}/{len(CURRENCIES_AND_COMMODITIES)} FX/commodities")

    # Process Vietnam-related ETFs
    vn_etfs_processed = 0
    for symbol, name in VN_RELATED_INSTRUMENTS.items():
        try:
            hist = _safe_download(symbol, period='7d', interval='1d')
            if hist is not None:
                latest, daily_change, weekly_change = _calculate_change_metrics(hist)

                if not pd.isna(latest):
                    data[symbol] = {
                        'name': name,
                        'price': latest,
                        'change_pct': daily_change,
                        'change_1w': weekly_change,
                        'currency': 'USD',
                        'category': 'etf',
                        'vietnam_related': True
                    }
                    vn_etfs_processed += 1
                    logger.info(f"✅ {name}: {latest:.2f} ({daily_change:+.2f}%)")

        except Exception as e:
            logger.warning(f"❌ Failed to process VN ETF {symbol}: {e}")
            continue

    logger.info(f"Successfully processed {vn_etfs_processed}/{len(VN_RELATED_INSTRUMENTS)} Vietnam-related ETFs")

    # Add market summary
    total_processed = indices_processed + fx_commodities_processed + vn_etfs_processed
    total_attempted = len(GLOBAL_INDICES) + len(CURRENCIES_AND_COMMODITIES) + len(VN_RELATED_INSTRUMENTS)

    data['_summary'] = {
        'total_instruments': total_processed,
        'success_rate': f"{(total_processed / total_attempted) * 100:.1f}%" if total_attempted > 0 else "0%",
        'indices': indices_processed,
        'fx_commodities': fx_commodities_processed,
        'vietnam_etfs': vn_etfs_processed,
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    }

    logger.info(
        f"Global market data fetch completed: {total_processed}/{total_attempted} instruments ({data['_summary']['success_rate']} success rate)")

    return data


@st.cache_data(ttl=1800, show_spinner=False)
def get_vietnam_proxy_indicators() -> Dict:
    """Get indicators that serve as proxies for Vietnam market performance."""
    proxies = {}

    # Regional indices that correlate with Vietnam
    regional_indices = {
        '^STI': 'Singapore Straits Times',
        '^JKSE': 'Jakarta Composite',
        '^KLSE': 'Kuala Lumpur Composite',
        '^SET.BK': 'Thailand SET',
        '000001.SS': 'Shanghai Composite'
    }

    for symbol, name in regional_indices.items():
        try:
            hist = _safe_download(symbol, period='7d')
            if hist is not None:
                latest, daily_change, weekly_change = _calculate_change_metrics(hist)

                if not pd.isna(latest):
                    proxies[symbol] = {
                        'name': name,
                        'price': latest,
                        'change_pct': daily_change,
                        'change_1w': weekly_change,
                        'correlation_with_vn': 'High' if symbol in ['^STI', '^JKSE'] else 'Medium',
                        'category': 'regional_proxy'
                    }

        except Exception as e:
            logger.warning(f"Failed to get proxy data for {symbol}: {e}")
            continue

    return proxies


def get_market_risk_indicators() -> Dict:
    """Get key risk indicators that affect emerging markets including Vietnam."""
    risk_indicators = {}

    # VIX and other volatility measures
    volatility_instruments = {
        '^VIX': 'CBOE Volatility Index',
        '^VXN': 'NASDAQ Volatility Index'
    }

    # Treasury yields (important for EM flows)
    treasury_instruments = {
        '^TNX': '10-Year Treasury Yield',
        '^FVX': '5-Year Treasury Yield',
        '^TYX': '30-Year Treasury Yield'
    }

    all_risk_instruments = {**volatility_instruments, **treasury_instruments}

    for symbol, name in all_risk_instruments.items():
        try:
            hist = _safe_download(symbol, period='5d')
            if hist is not None:
                latest, daily_change, weekly_change = _calculate_change_metrics(hist)

                if not pd.isna(latest):
                    category = 'volatility' if 'VIX' in symbol or 'VXN' in symbol else 'yield'
                    impact = 'High' if symbol in ['^VIX', '^TNX'] else 'Medium'

                    risk_indicators[symbol] = {
                        'name': name,
                        'value': latest,
                        'change_pct': daily_change,
                        'change_1w': weekly_change,
                        'category': category,
                        'vietnam_impact': impact
                    }

        except Exception as e:
            logger.warning(f"Failed to get risk indicator {symbol}: {e}")
            continue

    return risk_indicators