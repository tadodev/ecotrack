# analysis/indicators.py
import numpy as np
import pandas as pd


def format_number(value, decimals=2, suffix="", prefix=""):
    try:
        if pd.isna(value) or value is None:
            return "N/A"
        num = float(value)
        if abs(num) >= 1e12:
            s = f"{num / 1e12:.{decimals}f}T"
        elif abs(num) >= 1e9:
            s = f"{num / 1e9:.{decimals}f}B"
        elif abs(num) >= 1e6:
            s = f"{num / 1e6:.{decimals}f}M"
        elif abs(num) >= 1e3:
            s = f"{num / 1e3:.{decimals}f}K"
        else:
            s = f"{num:,.{decimals}f}"
        return f"{prefix}{s}{suffix}"
    except Exception:
        return "N/A"


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI (EMA smoothing)."""
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / (avg_loss.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi


def get_market_sentiment(rsi_value):
    if rsi_value is None or pd.isna(rsi_value):
        return "Unknown", "neutral"
    if rsi_value > 70:
        return "Overbought", "negative"
    if rsi_value < 30:
        return "Oversold", "positive"
    return "Neutral", "neutral"
