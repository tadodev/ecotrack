# data/global_markets.py
import logging

import streamlit as st
import yfinance as yf

logger = logging.getLogger(__name__)


@st.cache_data(ttl=3600)
def get_global_market_data():
    indices = {
        '^GSPC': 'S&P 500', '^DJI': 'Dow Jones', '^IXIC': 'NASDAQ',
        '^FTSE': 'FTSE 100', '^N225': 'Nikkei 225', '^HSI': 'Hang Seng'
    }
    data = {}
    for sym, name in indices.items():
        try:
            hist = yf.download(sym, period='7d', interval='1d', progress=False)
            if len(hist) >= 2:
                latest = float(hist['Close'].iloc[-1])
                prev = float(hist['Close'].iloc[-2])
                chg = (latest / prev - 1) * 100 if prev else 0.0
                data[sym] = {'name': name, 'price': latest, 'change_pct': float(chg), 'currency': 'USD'}
        except Exception as e:
            logger.warning(f"{sym} failed: {e}")
    return data
