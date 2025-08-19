# data/te.py
# Enhanced Trading Economics integration for Vietnam
import datetime as dt
import urllib.parse as _up
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
import streamlit as st
import numpy as np

from config.keys import load_tradingEconomic_key

TE_BASE = "https://api.tradingeconomics.com"

# Comprehensive Vietnam economic indicators
TE_VN_INDICATORS: Dict[str, Dict[str, str]] = {
    # Core Economic Indicators
    "inflation_rate": {"te": "Inflation Rate", "name": "Inflation Rate", "unit_hint": "%"},
    "gdp_growth_yoy": {"te": "GDP Annual Growth Rate", "name": "GDP Annual Growth Rate", "unit_hint": "%"},
    "policy_rate": {"te": "Interest Rate", "name": "Policy Rate", "unit_hint": "%"},

    # Manufacturing & Business
    "manufacturing_pmi": {"te": "Manufacturing PMI", "name": "Manufacturing PMI", "unit_hint": "Index"},
    "industrial_yoy": {"te": "Industrial Production", "name": "Industrial Production", "unit_hint": "%"},
    "retail_sales_yoy": {"te": "Retail Sales YoY", "name": "Retail Sales YoY", "unit_hint": "%"},

    # Labor Market
    "unemployment_rate": {"te": "Unemployment Rate", "name": "Unemployment Rate", "unit_hint": "%"},

    # Trade & External
    "balance_of_trade": {"te": "Balance of Trade", "name": "Balance of Trade", "unit_hint": "USD Billion"},
    "current_account": {"te": "Current Account", "name": "Current Account", "unit_hint": "USD Billion"},
    "fx_reserves": {"te": "Foreign Exchange Reserves", "name": "FX Reserves", "unit_hint": "USD Billion"},
    "exports": {"te": "Exports", "name": "Exports", "unit_hint": "USD Billion"},
    "imports": {"te": "Imports", "name": "Imports", "unit_hint": "USD Billion"},

    # Financial Markets
    "government_bond_10y": {"te": "Government Bond 10Y", "name": "10Y Bond Yield", "unit_hint": "%"},
    "money_supply_m2": {"te": "Money Supply M2", "name": "Money Supply M2", "unit_hint": "%"},

    # Additional Indicators
    "foreign_direct_investment": {"te": "Foreign Direct Investment", "name": "FDI", "unit_hint": "USD Billion"},
    "business_confidence": {"te": "Business Confidence", "name": "Business Confidence", "unit_hint": "Index"},
    "consumer_confidence": {"te": "Consumer Confidence", "name": "Consumer Confidence", "unit_hint": "Index"},
}

# Currency and commodity indicators that affect Vietnam
GLOBAL_INDICATORS = {
    "usd_vnd": {"country": "vietnam", "te": "Currency", "name": "USD/VND Exchange Rate"},
    "dxy": {"country": "united-states", "te": "Currency Index", "name": "US Dollar Index"},
    "oil_brent": {"country": "united-kingdom", "te": "Crude Oil", "name": "Brent Oil Price"},
    "gold": {"country": "united-states", "te": "Gold", "name": "Gold Price"},
    "copper": {"country": "united-states", "te": "Copper", "name": "Copper Price"},
}


def _te_cred() -> str:
    return load_tradingEconomic_key()


def _get(url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
    try:
        r = requests.get(url, params=params, timeout=15)
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
def get_comprehensive_vn_data() -> Dict[str, Dict]:
    """
    Get comprehensive Vietnam economic data from Trading Economics.
    Returns: {indicator_key: {'name','value','previous','date','unit','change'}}
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

    wanted = {v["te"].lower(): (k, v) for k, v in TE_VN_INDICATORS.items()}

    for item in items:
        te_name = (item.get("Category") or item.get("Indicator") or "").lower()
        if te_name not in wanted:
            continue

        key, meta = wanted[te_name]
        val = _as_float(item.get("Last") or item.get("LatestValue"))
        prev = _as_float(item.get("Previous") or item.get("Prior"))
        date = item.get("Date") or item.get("LatestValueDate")
        unit = item.get("Unit") or meta.get("unit_hint", "")

        # Calculate change
        change = None
        if val is not None and prev is not None and prev != 0:
            change = ((val - prev) / abs(prev)) * 100

        out[key] = {
            "name": meta["name"],
            "value": val,
            "previous": prev,
            "date": date,
            "unit": unit,
            "change": change
        }

    return out


@st.cache_data(ttl=1800)
def get_global_economic_context() -> Dict[str, Dict]:
    """Get global indicators that impact Vietnam markets."""
    cred = _te_cred()
    out = {}

    for key, config in GLOBAL_INDICATORS.items():
        country = config["country"]
        indicator = config["te"]

        url = f"{TE_BASE}/indicators/country/{country}"
        r = _get(url, {"c": cred, "format": "json"})

        if not r:
            continue

        try:
            items = r.json() or []
            for item in items:
                item_name = (item.get("Category") or item.get("Indicator") or "").lower()
                if indicator.lower() in item_name:
                    val = _as_float(item.get("Last") or item.get("LatestValue"))
                    prev = _as_float(item.get("Previous"))
                    date = item.get("Date")

                    change = None
                    if val is not None and prev is not None and prev != 0:
                        change = ((val - prev) / abs(prev)) * 100

                    out[key] = {
                        "name": config["name"],
                        "value": val,
                        "previous": prev,
                        "date": date,
                        "change": change
                    }
                    break
        except Exception:
            continue

    return out


@st.cache_data(ttl=1800)
def get_vn_economic_series(keys: List[str], years_back: int = 3) -> Dict[str, pd.Series]:
    """Get historical series for Vietnam economic indicators."""
    cred = _te_cred()
    start = (dt.date.today() - dt.timedelta(days=365 * years_back)).isoformat()
    series: Dict[str, pd.Series] = {}

    for key in keys:
        if key not in TE_VN_INDICATORS:
            continue

        te_name = TE_VN_INDICATORS[key]["te"]
        encoded_name = _up.quote(te_name, safe="")
        url = f"{TE_BASE}/historical/country/vietnam/indicator/{encoded_name}"

        r = _get(url, {"c": cred, "format": "json", "d1": start})
        if not r:
            continue

        try:
            data = r.json() or []
            if not data:
                continue

            df = pd.DataFrame(data)
            if "Date" not in df or "Value" not in df:
                continue

            idx = pd.to_datetime(df["Date"], errors="coerce")
            vals = pd.to_numeric(df["Value"], errors="coerce")
            s = pd.Series(vals.values, index=idx).dropna().sort_index()

            if len(s) > 0:
                series[key] = s

        except Exception:
            continue

    return series


def calculate_economic_score(vn_data: Dict[str, Dict]) -> Tuple[float, str, List[str]]:
    """
    Calculate a composite economic health score for Vietnam (0-100).
    Returns: (score, rating, key_factors)
    """
    score = 50  # neutral starting point
    factors = []

    # GDP Growth (weight: 25%)
    if "gdp_growth_yoy" in vn_data and vn_data["gdp_growth_yoy"]["value"] is not None:
        gdp_growth = vn_data["gdp_growth_yoy"]["value"]
        if gdp_growth > 6.5:
            score += 15
            factors.append(f"🟢 Strong GDP growth ({gdp_growth:.1f}%)")
        elif gdp_growth > 5.0:
            score += 10
            factors.append(f"🟡 Moderate GDP growth ({gdp_growth:.1f}%)")
        else:
            score -= 10
            factors.append(f"🔴 Slow GDP growth ({gdp_growth:.1f}%)")

    # Inflation (weight: 20%)
    if "inflation_rate" in vn_data and vn_data["inflation_rate"]["value"] is not None:
        inflation = vn_data["inflation_rate"]["value"]
        if 2 <= inflation <= 4:
            score += 12
            factors.append(f"🟢 Healthy inflation ({inflation:.1f}%)")
        elif inflation < 2 or inflation > 6:
            score -= 8
            factors.append(f"🔴 Concerning inflation ({inflation:.1f}%)")
        else:
            score += 5
            factors.append(f"🟡 Elevated inflation ({inflation:.1f}%)")

    # Manufacturing PMI (weight: 15%)
    if "manufacturing_pmi" in vn_data and vn_data["manufacturing_pmi"]["value"] is not None:
        pmi = vn_data["manufacturing_pmi"]["value"]
        if pmi > 52:
            score += 10
            factors.append(f"🟢 Expanding manufacturing (PMI: {pmi:.1f})")
        elif pmi > 50:
            score += 5
            factors.append(f"🟡 Slight expansion (PMI: {pmi:.1f})")
        else:
            score -= 8
            factors.append(f"🔴 Contracting manufacturing (PMI: {pmi:.1f})")

    # Trade Balance (weight: 15%)
    if "balance_of_trade" in vn_data and vn_data["balance_of_trade"]["value"] is not None:
        trade_balance = vn_data["balance_of_trade"]["value"]
        if trade_balance > 1:
            score += 8
            factors.append(f"🟢 Trade surplus (${trade_balance:.1f}B)")
        elif trade_balance > -1:
            score += 3
            factors.append(f"🟡 Balanced trade (${trade_balance:.1f}B)")
        else:
            score -= 5
            factors.append(f"🔴 Trade deficit (${trade_balance:.1f}B)")

    # FX Reserves (weight: 10%)
    if "fx_reserves" in vn_data and vn_data["fx_reserves"]["value"] is not None:
        fx_reserves = vn_data["fx_reserves"]["value"]
        if fx_reserves > 100:
            score += 7
            factors.append(f"🟢 Strong FX reserves (${fx_reserves:.0f}B)")
        elif fx_reserves > 80:
            score += 3
        else:
            score -= 3

    # Policy Rate trend (weight: 15%)
    if "policy_rate" in vn_data and vn_data["policy_rate"]["value"] is not None:
        policy_rate = vn_data["policy_rate"]["value"]
        change = vn_data["policy_rate"].get("change")
        if change is not None:
            if change < -0.25:  # Rate cuts
                score += 8
                factors.append(f"🟢 Accommodative policy (Rate: {policy_rate:.2f}%, ↓)")
            elif change > 0.25:  # Rate hikes
                score -= 5
                factors.append(f"🔴 Tightening policy (Rate: {policy_rate:.2f}%, ↑)")
            else:
                score += 3
                factors.append(f"🟡 Stable policy (Rate: {policy_rate:.2f}%)")

    # Normalize score
    score = max(0, min(100, score))

    # Determine rating
    if score >= 75:
        rating = "Excellent"
    elif score >= 60:
        rating = "Good"
    elif score >= 45:
        rating = "Fair"
    elif score >= 30:
        rating = "Poor"
    else:
        rating = "Critical"

    return score, rating, factors