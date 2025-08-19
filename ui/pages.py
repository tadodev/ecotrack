# ui/pages.py
import os

import pandas as pd
import streamlit as st

from analysis.indicators import format_number
from analysis.recommendations import generate_investment_recommendation
from constants_enhanced import VN_MAJOR_STOCKS


def _fmt_value_unit(val: float, unit: str) -> str:
    """
    Append unit smartly:
    - No space for symbols like %, K, B
    - Space for text units like 'Index'
    """
    tight = {'%', 'K', 'B'}
    return f"{val:.2f}{unit}" if unit in tight else f"{val:.2f} {unit}"


def apply_custom_css():
    st.markdown("""
    <style>
    .main > div { padding-top: 2rem; }

    /* Our metric card wrapper */
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #1f2937 !important;            /* force readable text on light bg */
    }
    .metric-positive { border-left-color: #28a745 !important; }
    .metric-negative { border-left-color: #dc3545 !important; }
    .metric-neutral  { border-left-color: #ffc107 !important; }

    /* FIX: neutralize any 3rd-party badge/label styles and dark-theme opacity */
    .stMetric [data-testid="stMetricLabel"],
    .stMetric [data-testid="stMetricValue"],
    .stMetric [data-testid="stMetricDelta"] {
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        border: 0 !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        color: #1f2937 !important;            /* readable on #f8f9fa */
        opacity: 1 !important;                /* remove dimming from dark theme */
        text-shadow: none !important;
    }
    .stMetric [data-testid="stMetricDelta"] { margin-top: .25rem; }

    /* Prevent any .badge/.label globals inside metric content */
    .stMetric .badge, .stMetric [class*="badge"],
    .stMetric .label, .stMetric [class*="label"] { all: unset; }

    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem; border-radius: 1rem; color: white; margin-bottom: 1rem;
    }
    .alert-success { background-color: #d4edda; border-color: #c3e6cb; color: #155724; padding: 1rem; border-radius: .5rem; border-left: 4px solid #28a745; }
    .alert-warning { background-color: #fff3cd; border-color: #ffeaa7; color: #856404; padding: 1rem; border-radius: .5rem; border-left: 4px solid #ffc107; }
    .alert-danger  { background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; padding: 1rem; border-radius: .5rem; border-left: 4px solid #dc3545; }
    </style>
    """, unsafe_allow_html=True)


def header_card():
    st.markdown(f"""
    <div class="info-card">
        <h1>🌍 Modern Economic & Investment Dashboard</h1>
        <p>Real-time tracking of global economic indicators and Vietnam market analysis</p>
        <p>Last updated: {pd.Timestamp.now(tz='Asia/Ho_Chi_Minh').strftime('%Y-%m-%d %H:%M:%S')} (Vietnam Time)</p>
    </div>
    """, unsafe_allow_html=True)


def show_overview_page(us_data, vn_data, fed_data, global_data):
    st.subheader("🎯 Key Metrics at a Glance")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if 'inflation' in us_data:
            v = us_data['inflation']['value']
            delta_class = "metric-negative" if v > 3 else "metric-positive" if v < 2 else "metric-neutral"
            st.markdown(f'<div class="stMetric {delta_class}">', unsafe_allow_html=True)
            delta_val = us_data['inflation'].get('mom_change')  # None if not provided
            if delta_val is None:
                st.metric("US Inflation (YoY)", f"{v:.2f}%")
            else:
                st.metric("US Inflation (YoY)", f"{v:.2f}%", delta=f"{delta_val:+.2f}% MoM")
            st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        if 'fed_rate' in us_data:
            v = us_data['fed_rate']['value']
            st.markdown('<div class="stMetric metric-neutral">', unsafe_allow_html=True)
            st.metric("Fed Funds Rate", f"{v:.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        if 'vnindex' in vn_data and 'error' not in vn_data:
            p = vn_data['vnindex']['price'];
            ch = vn_data['vnindex']['change_pct']
            delta_class = "metric-positive" if ch > 0 else "metric-negative" if ch < 0 else "metric-neutral"
            st.markdown(f'<div class="stMetric {delta_class}">', unsafe_allow_html=True)
            st.metric("VN-Index", f"{p:,.0f}", f"{ch:+.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        if fed_data and 'next_meeting' in fed_data:
            st.markdown('<div class="stMetric metric-neutral">', unsafe_allow_html=True)
            st.metric("Fed Cut Gauge", fed_data['next_meeting'].get('cut_25bp', 'N/A'))
            st.markdown('</div>', unsafe_allow_html=True)
            if fed_data.get('heuristic'): st.caption("Heuristic gauge (not CME probabilities)")

    st.markdown("---")
    st.subheader("🚨 Market Alerts & Signals")
    alerts = []
    if 'inflation' in us_data:
        v = us_data['inflation']['value']
        if v > 4:
            alerts.append(("danger", f"⚠️ US inflation at {v:.1f}% - above target"))
        elif v < 2:
            alerts.append(("success", f"✅ US inflation at {v:.1f}% - rate cuts possible"))
    if 'vnindex' in vn_data and vn_data['vnindex'].get('rsi') is not None:
        rsi = vn_data['vnindex']['rsi']
        if rsi < 30:
            alerts.append(("success", f"🔥 VN-Index oversold (RSI: {rsi:.1f})"))
        elif rsi > 70:
            alerts.append(("warning", f"📈 VN-Index overbought (RSI: {rsi:.1f})"))
    if 'yield_curve' in fed_data and isinstance(fed_data['yield_curve'], (int, float)):
        yc = fed_data['yield_curve']
        if yc < 0: alerts.append(("warning", f"📉 Inverted yield curve ({yc:.2f}%)"))
    if alerts:
        for typ, msg in alerts:
            st.markdown(f'<div class="alert-{typ}">{msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-success">✅ No critical alerts</div>', unsafe_allow_html=True)

    st.subheader("📊 Quick Market Overview")
    c1, c2 = st.columns(2)
    with c1:
        if global_data:
            st.markdown("**🌍 Global Markets Today**")
            for _, d in list(global_data.items())[:4]:
                emo = "🟢" if d['change_pct'] > 0 else "🔴" if d['change_pct'] < 0 else "⚪"
                st.write(f"{emo} {d['name']}: {d['change_pct']:+.2f}%")
    with c2:
        if 'sectors' in vn_data and vn_data['sectors']:
            st.markdown("**🇻🇳 Vietnam Sectors Today**")
            for s, d in list(vn_data['sectors'].items())[:4]:
                emo = "🟢" if d['avg_return'] > 0 else "🔴" if d['avg_return'] < 0 else "⚪"
                st.write(f"{emo} {s}: {d['avg_return']:+.2f}%")


def show_us_economy_page(us_data, us_series, fed_data):
    st.header("🇺🇸 United States Economic Dashboard")

    if not us_data:
        st.info("FRED key missing or data unavailable. Set a key in Settings.")
        return

    # --- Key Economic Indicators ---
    st.subheader("📈 Key Economic Indicators")
    cols = st.columns(4)

    ind_list = [
        ('inflation', 'Inflation (CPI YoY)', '%', 'Price changes in consumer goods'),
        ('pce', 'PCE Inflation', '%', 'Fed preferred inflation'),
        ('unemployment', 'Unemployment Rate', '%', 'Share of unemployed'),
        ('fed_rate', 'Fed Funds Rate', '%', 'Policy rate'),
        ('gdp', 'GDP Growth YoY', '%', 'Real activity proxy'),
        ('housing', 'Housing Starts', 'K', 'New residential construction'),
        ('retail_sales', 'Retail Sales', 'B', 'Consumer spending'),
        ('industrial_production', 'Industrial Production', 'Index', 'Manufacturing output'),
    ]

    for i, (k, label, unit, desc) in enumerate(ind_list):
        with cols[i % 4]:
            if k in us_data:
                d = us_data[k]
                val = d['value']
                st.metric(
                    label=label,
                    value=_fmt_value_unit(val, unit),
                    help=f"{desc} (Latest: {d['date']})"
                )
                # Only show MoM if present and non-null
                if 'mom_change' in d and d['mom_change'] is not None:
                    st.caption(f"MoM: {d['mom_change']:+.2f}%")

    st.markdown("---")

    # --- Fed Policy ---
    st.subheader("🏦 Federal Reserve Policy Analysis")
    c1, c2 = st.columns([2, 1])

    with c1:
        if fed_data and 'error' not in fed_data:
            st.markdown("**Next FOMC (Heuristic)**")
            if 'next_meeting' in fed_data:
                m = fed_data['next_meeting']
                a, b, c = st.columns(3)
                a.metric("25bp Cut", m.get('cut_25bp', 'N/A'))
                b.metric("Hold", m.get('hold', 'N/A'))
                c.metric("25bp Hike", m.get('raise_25bp', 'N/A'))
            if 'yield_curve' in fed_data:
                yc = fed_data['yield_curve']
                st.metric("10Y-Fed Spread", f"{yc:.2f}%", help="<0 = inverted")
                if yc < 0:
                    st.warning("🚨 Inverted yield curve")
            if fed_data.get('heuristic'):
                st.caption("Heuristic gauge (not CME probabilities)")
        else:
            st.error("Fed data unavailable")

    with c2:
        st.markdown("**Key Drivers**")
        facts = []
        if 'inflation' in us_data:
            v = us_data['inflation']['value']
            facts.append(
                "🔴 Inflation above target" if v > 3
                else "🟢 Inflation below target" if v < 2
                else "🟡 Inflation near target"
            )
        if 'unemployment' in us_data:
            u = us_data['unemployment']['value']
            facts.append(
                "🔴 Tight labor" if u < 4
                else "🟢 Slack labor" if u > 6
                else "🟡 Moderate"
            )
        for f in facts:
            st.write(f)

    st.subheader("📊 Economic Trends Visualization")
    # charts are rendered by caller if available


def show_vietnam_market_page(vn_data, charts, show_technical=True):
    st.header("🇻🇳 Vietnam Stock Market Dashboard")
    if 'error' in vn_data:
        st.error(f"Error: {vn_data['error']}")
        return
    if 'vnindex' in vn_data:
        vn = vn_data['vnindex']
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Current Level", f"{vn.get('price', 0):,.0f}", f"{vn.get('change_pct', 0):+.2f}%")
        with c2:
            st.metric("Volume", format_number(vn.get('volume', 0), 0))
        with c3:
            if show_technical and vn.get('rsi') is not None:
                st.metric("RSI (14)", f"{vn['rsi']:.1f}", vn.get('rsi_signal', 'Neutral'))
        with c4:
            if vn.get('sma_50'):
                sma = vn['sma_50'];
                price = vn.get('price', 0)
                dist = ((price - sma) / sma * 100) if sma else 0
                st.metric("vs SMA50", f"{dist:+.1f}%")
    st.subheader("📈 VN-Index Technical Chart")
    if charts.get('vn_technical'): st.plotly_chart(charts['vn_technical'], use_container_width=True)

    st.subheader("🏭 Sector Performance")
    if charts.get('vn_sectors'):
        st.plotly_chart(charts['vn_sectors'], use_container_width=True)

    # --- Top 10 leaders: chart + table ---
    st.markdown("### 🏅 Top 10 Stock Leaders (Daily %)")

    # Chart from builders.py
    if charts.get('vn_top_leaders'):
        st.plotly_chart(charts['vn_top_leaders'], use_container_width=True)

    # Detail table with Sector column
    if vn_data.get('top_stocks'):
        # Build reverse map: symbol -> sector
        sector_of = {sym: sector for sector, syms in VN_MAJOR_STOCKS.items() for sym in syms}

        leaders = vn_data['top_stocks'][:10]
        rows = []
        for i, s in enumerate(leaders, 1):
            rows.append({
                "Rank": i,
                "Stock": s["symbol"],
                "Sector": sector_of.get(s["symbol"], "—"),
                "Price": f"{s['price']:,.0f}",
                "Change (%)": f"{s['change_pct']:+.2f}%",
                "Volume": format_number(s.get("volume", 0), 0),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)


def show_global_markets_page(global_data):
    st.header("🌍 Global Markets Dashboard")
    if not global_data:
        st.error("No data")
        return
    st.subheader("📈 Major Global Indices")
    cols = st.columns(3)
    for i, (_, d) in enumerate(global_data.items()):
        with cols[i % 3]:
            delta_class = "metric-positive" if d['change_pct'] > 0 else "metric-negative" if d[
                                                                                                 'change_pct'] < 0 else "metric-neutral"
            st.markdown(f'<div class="stMetric {delta_class}">', unsafe_allow_html=True)
            st.metric(label=d['name'], value=f"{d['price']:,.2f} {d.get('currency', 'USD')}",
                      delta=f"{d['change_pct']:+.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)


def show_investment_analysis_page(us_data, vn_data, fed_data, risk_tolerance):
    st.header("📊 Investment Analysis & Recommendations")
    rec = generate_investment_recommendation(us_data, vn_data, fed_data)
    s1, s2 = st.columns([2, 1])
    with s1:
        st.markdown(f"**Current Risk Level:** {rec['risk_level']}")
        st.markdown(f"**Analysis Summary:** {rec['summary']}")
        st.markdown("**Key Recommendations:**")
        for i, r in enumerate(rec['recommendations'], 1):
            st.write(f"{i}. {r}")
    with s2:
        st.markdown(f"**Your Risk Profile:** {risk_tolerance}")
        if risk_tolerance == "Conservative":
            st.info("💰 Focus on capital preservation and income")
            alloc = "60% Bonds, 30% Stocks, 10% Cash"
        elif risk_tolerance == "Moderate":
            st.info("⚖️ Balanced approach")
            alloc = "40% Bonds, 50% Stocks, 10% Cash"
        else:
            st.info("🚀 Growth-focused")
            alloc = "20% Bonds, 70% Stocks, 10% Cash"
        st.markdown(f"**Suggested Allocation:** {alloc}")


def show_settings_page(get_fred_client):
    st.header("⚙️ Dashboard Settings")
    st.subheader("🔑 API Configuration")
    c1, c2 = st.columns(2)
    with c1:
        fred = get_fred_client()
        source = ("st.secrets" if 'FRED_API_KEY' in st.secrets and st.secrets['FRED_API_KEY'] else
                  "Environment variable" if 'FRED_API_KEY' in os.environ else
                  "Session" if st.session_state.get('fred_api_key') else "Default (fallback)")
        st.markdown("**FRED API**")
        st.write(f"Status: {'🟢 Connected' if fred else '🟡 Using fallback/Not Connected'}")
        st.write(f"Source: {source}")
    with c2:
        st.markdown("**Set/Override FRED Key (session only)**")
        new_key = st.text_input("Enter FRED API Key (session only)", type='password')
        d1, d2 = st.columns(2)
        with d1:
            if st.button("Use This Key Now", type='primary'):
                if new_key:
                    st.session_state['fred_api_key'] = new_key.strip()
                    get_fred_client.clear()
                    st.success("Session key set. Refreshing FRED client...")
                else:
                    st.warning("Enter a valid key")
        with d2:
            if st.button("Clear Session Key"):
                st.session_state.pop('fred_api_key', None)
                get_fred_client.clear()
                st.info("Session key cleared")