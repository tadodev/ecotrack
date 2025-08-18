# data/us.py
import logging
from typing import Tuple, Dict

import pandas as pd
import streamlit as st
from fredapi import Fred
from tenacity import retry, stop_after_attempt, wait_fixed

from config.keys import load_fred_key
from constants import ECONOMIC_INDICATORS

logger = logging.getLogger(__name__)


@st.cache_resource
def get_fred_client():
    key = load_fred_key()
    try:
        return Fred(api_key=key) if key else None
    except Exception as e:
        logger.error(f"FRED init failed: {e}")
        return None


@st.cache_data(ttl=1800)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_enhanced_us_data(months_back: int = 12) -> Tuple[Dict, Dict]:
    fred = get_fred_client()
    if not fred:
        return {}, {}
    data, series_data = {}, {}
    start_date = pd.Timestamp.now() - pd.DateOffset(months=months_back)
    for key, cfg in ECONOMIC_INDICATORS.items():
        try:
            series = fred.get_series(cfg['fred'], start=start_date).dropna()
            if series is None or len(series) == 0:
                continue
            series_data[key] = series
            latest_value = series.iloc[-1]
            latest_date = series.index[-1]
            # GDP YoY% (quarterly)
            if key == 'gdp' and len(series) >= 5:
                yoy = (series.iloc[-1] / series.iloc[-5] - 1) * 100
                data[key] = {'value': float(yoy), 'date': latest_date.strftime('%Y-%m-%d'), 'name': cfg['name']}
            # CPI/PCE YoY%
            elif key in ['inflation', 'pce'] and len(series) >= 13:
                yoy = (series.iloc[-1] / series.iloc[-13] - 1) * 100
                data[key] = {'value': float(yoy), 'latest': float(latest_value),
                             'date': latest_date.strftime('%Y-%m-%d'), 'name': cfg['name']}
            else:
                obj = {'value': float(latest_value), 'date': latest_date.strftime('%Y-%m-%d'), 'name': cfg['name']}
                if len(series) >= 2:
                    mom = (series.iloc[-1] / series.iloc[-2] - 1) * 100
                    obj['mom_change'] = float(mom)
                data[key] = obj
        except Exception as e:
            logger.error(f"Error fetching {key}: {e}")
            continue
    return data, series_data


@st.cache_data(ttl=1800)
def get_fed_probability():
    """Heuristic Fed gauge from 10Y - Fed Funds (NOT CME probabilities)."""
    fred = get_fred_client()
    if not fred:
        return {'error': 'FRED not available'}
    try:
        fed_rate = fred.get_series('FEDFUNDS', limit=12).dropna()
        t10y = fred.get_series('GS10', limit=12).dropna()
        if len(fed_rate) and len(t10y):
            cur_fed = float(fed_rate.iloc[-1])
            cur_10y = float(t10y.iloc[-1])
            spread = cur_10y - cur_fed
            if spread < 0:
                cut_prob = 75
            elif spread < 1:
                cut_prob = 50
            else:
                cut_prob = 25
            return {
                'heuristic': True,
                'next_meeting': {'cut_25bp': f"{cut_prob}%", 'hold': f"{100 - cut_prob}%", 'raise_25bp': '5%'},
                'yield_curve': float(spread),
                'fed_rate': cur_fed,
                'treasury_10y': cur_10y,
                'note': 'Heuristic from yield curve; not CME probabilities.'
            }
    except Exception as e:
        logger.error(f"Fed gauge error: {e}")
    return {'error': 'Unable to compute heuristic gauge'}
