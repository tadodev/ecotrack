# config/keys.py
import os
from typing import Optional

import streamlit as st

# Keep a fallback hard-coded key as user requested
DEFAULT_FRED_API_KEY = '9bbdd64461cdace97de896c6fd419f0d'
DEFAULT_TRADINGECONOMICS_API_KEY = '73cd05b20de2414:i9qi2pwaviu6vzx'


def load_fred_key() -> Optional[str]:
    """Resolve FRED key from secrets, env, session, then fallback to default."""
    # 1) Secrets
    try:
        if 'FRED_API_KEY' in st.secrets and st.secrets['FRED_API_KEY']:
            return st.secrets['FRED_API_KEY']
    except Exception:
        pass
    # 2) Environment
    env_key = os.getenv('FRED_API_KEY')
    if env_key:
        return env_key
    # 3) Session (from Settings UI)
    sess_key = st.session_state.get('fred_api_key')
    if sess_key:
        return sess_key
    # 4) Fallback hard-coded (explicitly requested)
    return DEFAULT_FRED_API_KEY


def load_tradingEconomic_key() -> Optional[str]:
    return DEFAULT_TRADINGECONOMICS_API_KEY
