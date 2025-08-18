# data/te.py
# TradingEconomics integration (hard-keyed)
# - Latest Vietnam macro snapshot: get_vn_te_latest()
# - Historical series: get_vn_te_series()
# Uses keys.DEFAULT_TRADINGECONOMICS_API_KEY ("user:pass" format)

import datetime as dt
import urllib.parse as _up
from typing import Dict, List, Optional

import pandas as pd
import requests
import streamlit as st

from config.keys import load_tradingEconomic_key

TE_BASE = "https://api.tradingeconomics.com"

# Canonical indicator mapping (TradingEconomics display names)
TE_VN_INDICATORS: Dict[str, Dict[str, str]] = {
    "inflation_rate": {"te": "Inflation Rate", "name": "Inflation Rate", "unit_hint": "%"},
    "gdp_growth_yoy": {"te": "GDP Annual Growth Rate", "name": "GDP Annual Growth Rate", "unit_hint": "%"},
    "policy_rate": {"te": "Interest Rate", "name": "Policy Rate", "unit_hint": "%"},
    "manufacturing_pmi": {"te": "Manufacturing PMI", "name": "Manufacturing PMI", "unit_hint": "Index"},
    "industrial_yoy": {"te": "Industrial Production (YoY)", "name": "Industrial Production (YoY)", "unit_hint": "%"},
    "retail_sales_yoy": {"te": "Retail Sales YoY", "name": "Retail Sales (YoY)", "unit_hint": "%"},
    "unemployment_rate": {"te": "Unemployment Rate", "name": "Unemployment Rate", "unit_hint": "%"},
    "balance_of_trade": {"te": "Balance of Trade", "name": "Balance of Trade", "unit_hint": "USD"},
    "current_account": {"te": "Current Account", "name": "Current Account", "unit_hint": "USD"},
    "fx_reserves": {"te": "Foreign Exchange Reserves", "name": "FX Reserves", "unit_hint": "USD"},
}


def _te_cred() -> str:
    """Always use the hard-coded TradingEconomics key prepared in keys.py."""
    return load_tradingEconomic_key()  # "username:password"


def _get(url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
    """GET with timeout; return None on any HTTP/network error."""
    try:
        r = requests.get(url, params=params, timeout=12)
        if not r.ok:
            return None
        return r
    except Exception:
        return None


def _as_float(x):
    try:
        if x in (None, "", "NaN"):
            return None
        return float(x)
    except Exception:
        return None


@st.cache_data(ttl=900)
def get_vn_te_latest(picks: Optional[Dict[str, Dict]] = None) -> Dict[str, Dict]:
    """
    Latest values for Vietnam indicators.
    Returns: {key: {'name','value','previous','date','unit'}}
    Keys default to TE_VN_INDICATORS unless 'picks' supplied.
    """
    cred = _te_cred()
    url = f"{TE_BASE}/indicators/country/vietnam"
    r = _get(url, {"c": cred, "format": "json"})
    out: Dict[str, Dict] = {}
    if not r:
        return out

    try:
        items = r.json() or []
    except Exception:
        return out

    wanted = {v["te"].lower(): (k, v) for k, v in (picks or TE_VN_INDICATORS).items()}
    for it in items:
        te_name = (it.get("Category") or it.get("Indicator") or it.get("indicator") or "").lower()
        if te_name not in wanted:
            continue
        k, meta = wanted[te_name]
        val = _as_float(it.get("Last") or it.get("LatestValue") or it.get("Value"))
        prev = _as_float(it.get("Previous") or it.get("Prior"))
        date = it.get("Date") or it.get("LatestValueDate") or it.get("DateTime")
        unit = it.get("Unit") or meta.get("unit_hint", "")
        out[k] = {"name": meta["name"], "value": val, "previous": prev, "date": date, "unit": unit}
    return out


def _hist_endpoint(ind_name: str) -> str:
    enc = _up.quote(ind_name, safe="")
    return f"{TE_BASE}/historical/country/vietnam/indicator/{enc}"


@st.cache_data(ttl=1800)
def get_vn_te_series(keys: List[str], years_back: int = 5) -> Dict[str, pd.Series]:
    """
    Historical series for requested keys (using TE_VN_INDICATORS mapping).
    Returns: {key: pd.Series(values indexed by pandas datetime)}
    """
    cred = _te_cred()
    start = (dt.date.today() - dt.timedelta(days=365 * years_back)).isoformat()
    series: Dict[str, pd.Series] = {}

    for k in keys:
        te_name = TE_VN_INDICATORS.get(k, {}).get("te")
        if not te_name:
            continue
        url = _hist_endpoint(te_name)
        r = _get(url, {"c": cred, "format": "json", "d1": start})
        if not r:
            continue
        try:
            data = r.json() or []
        except Exception:
            continue
        if not data:
            continue

        df = pd.DataFrame(data)
        if "Date" not in df or "Value" not in df:
            continue
        idx = pd.to_datetime(df["Date"], errors="coerce")
        vals = pd.to_numeric(df["Value"], errors="coerce")
        s = pd.Series(vals.values, index=idx).dropna().sort_index()
        series[k] = s

    return series
