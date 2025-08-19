# ui/pages_enhanced.py
import pandas as pd
import streamlit as st
from typing import Dict, Any, List
import plotly.graph_objects as go

from analysis.indicators import format_number
from analysis.investment_enhanced import (
    generate_comprehensive_investment_recommendation,
    get_sector_investment_rationale
)
from data.te_enhanced import calculate_economic_score
from charts.builders_enhanced import create_economic_score_gauge
from constants_enhanced import VN_MAJOR_STOCKS


def apply_enhanced_css():
    """Enhanced CSS with more sophisticated styling."""
    st.markdown("""
    <style>
    .main > div { padding-top: 2rem; }

    /* Enhanced metric cards */
    .stMetric {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.2rem;
        border-radius: 0.8rem;
        border-left: 4px solid #007bff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        color: #1f2937 !important;
        transition: transform 0.2s ease;
    }
    .stMetric:hover { transform: translateY(-2px); }

    .metric-positive { border-left-color: #28a745 !important; background: linear-gradient(135deg, #f8fff8 0%, #e8f5e8 100%); }
    .metric-negative { border-left-color: #dc3545 !important; background: linear-gradient(135deg, #fff8f8 0%, #f5e8e8 100%); }
    .metric-neutral  { border-left-color: #ffc107 !important; background: linear-gradient(135deg, #fffdf8 0%, #f5f3e8 100%); }
    .metric-excellent { border-left-color: #17a2b8 !important; background: linear-gradient(135deg, #f8fdff 0%, #e8f4f8 100%); }

    /* Fix metric label/value styling */
    .stMetric [data-testid="stMetricLabel"],
    .stMetric [data-testid="stMetricValue"],
    .stMetric [data-testid="stMetricDelta"] {
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        border: 0 !important;
        color: #1f2937 !important;
        opacity: 1 !important;
    }

    /* Enhanced cards */
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem; 
        border-radius: 1rem; 
        color: white; 
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }

    .economic-score-card {
        background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }

    .analysis-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.8rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 4px solid #007bff;
        margin-bottom: 1rem;
    }

    .recommendation-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 0.8rem;
        color: white;
        margin-bottom: 1rem;
    }

    /* Alert styles */
    .alert-success { background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); border-color: #c3e6cb; color: #155724; }
    .alert-warning { background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); border-color: #ffeaa7; color: #856404; }
    .alert-danger  { background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); border-color: #f5c6cb; color: #721c24; }
    .alert-info    { background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%); border-color: #bee5eb; color: #0c5460; }

    .alert-success, .alert-warning, .alert-danger, .alert-info {
        padding: 1rem; 
        border-radius: 0.5rem; 
        border-left: 4px solid; 
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    /* Enhanced tables */
    .stDataFrame {
        border-radius: 0.5rem;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0.5rem 0.5rem 0 0;
        padding: 0.5rem 1rem;
    }
    </style>
    """, unsafe_allow_html=True)


def enhanced_header_card():
    """Enhanced header with more information."""
    current_time = pd.Timestamp.now(tz='Asia/Ho_Chi_Minh')

    st.markdown(f"""
    <div class="info-card">
        <h1>🌍 Advanced Economic & Investment Dashboard</h1>
        <p>Comprehensive real-time analysis of global economic indicators, Vietnam market dynamics, and investment opportunities</p>
        <div style="display: flex; justify-content: space-between; margin-top: 1rem;">
            <div>📊 <strong>Data Sources:</strong> FRED, Trading Economics, TCBS, Yahoo Finance</div>
            <div>🕒 <strong>Last Updated:</strong> {current_time.strftime('%Y-%m-%d %H:%M:%S')} (VN Time)</div>
        </div>
        <div style="margin-top: 0.5rem;">
            <small>💡 Enhanced with VN30 analysis, economic scoring, and comprehensive investment recommendations</small>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_enhanced_overview_page(us_data, vn_market_data, vn_economic_data, fed_data, global_context):
    """Enhanced overview page with comprehensive analysis."""
    st.subheader("🎯 Executive Dashboard")

    # Calculate Vietnam economic score
    economic_score, rating, key_factors = calculate_economic_score(vn_economic_data)

    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if 'inflation' in us_data:
            v = us_data['inflation']['value']
            delta_class = "metric-negative" if v > 3 else "metric-positive" if v < 2 else "metric-neutral"
            st.markdown(f'<div class="stMetric {delta_class}">', unsafe_allow_html=True)
            st.metric("US Inflation (YoY)", f"{v:.2f}%",
                      delta=f"{us_data['inflation'].get('mom_change', 0):+.2f}% MoM")
            st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if 'fed_rate' in us_data:
            v = us_data['fed_rate']['value']
            st.markdown('<div class="stMetric metric-neutral">', unsafe_allow_html=True)
            st.metric("Fed Funds Rate", f"{v:.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        if 'indices' in vn_market_data and 'vnindex' in vn_market_data['indices']:
            vni = vn_market_data['indices']['vnindex']
            p, ch = vni['price'], vni['change_pct']
            delta_class = "metric-positive" if ch > 0 else "metric-negative" if ch < 0 else "metric-neutral"
            st.markdown(f'<div class="stMetric {delta_class}">', unsafe_allow_html=True)
            st.metric("VN-Index", f"{p:,.0f}", f"{ch:+.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        if 'indices' in vn_market_data and 'vn30' in vn_market_data['indices']:
            vn30 = vn_market_data['indices']['vn30']
            p, ch = vn30['price'], vn30['change_pct']
            delta_class = "metric-positive" if ch > 0 else "metric-negative" if ch < 0 else "metric-neutral"
            st.markdown(f'<div class="stMetric {delta_class}">', unsafe_allow_html=True)
            st.metric("VN30", f"{p:,.2f}", f"{ch:+.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        rating_class = ("metric-excellent" if rating == "Excellent" else
                        "metric-positive" if rating == "Good" else
                        "metric-neutral" if rating == "Fair" else "metric-negative")
        st.markdown(f'<div class="stMetric {rating_class}">', unsafe_allow_html=True)
        st.metric("VN Economic Score", f"{economic_score:.0f}/100", rating)
        st.markdown('</div>', unsafe_allow_html=True)

    # Economic Health Score Section
    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    with col1:
        # Economic score gauge
        gauge_fig = create_economic_score_gauge(economic_score, rating)
        st.plotly_chart(gauge_fig, use_container_width=True)

    with col2:
        st.markdown(f"""
        <div class="economic-score-card">
            <h3>Vietnam Economic Health Analysis</h3>
            <p><strong>Overall Rating:</strong> {rating} ({economic_score:.1f}/100)</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Key Economic Factors:**")
        for factor in key_factors[:5]:  # Show top 5 factors
            st.write(f"• {factor}")

    # Market Alerts & Signals
    st.markdown("---")
    st.subheader("🚨 Critical Market Signals")

    alerts = []

    # US Economic Alerts
    if 'inflation' in us_data:
        v = us_data['inflation']['value']
        if v > 4:
            alerts.append(("danger", f"⚠️ US inflation at {v:.1f}% - Fed hawkishness risk"))
        elif v < 2:
            alerts.append(("success", f"✅ US inflation at {v:.1f}% - potential rate cuts"))

    # Vietnam Market Alerts
    if 'indices' in vn_market_data and 'vnindex' in vn_market_data['indices']:
        vni = vn_market_data['indices']['vnindex']
        if vni.get('rsi'):
            rsi = vni['rsi']
            if rsi < 30:
                alerts.append(("success", f"🔥 VN-Index oversold (RSI: {rsi:.1f}) - buying opportunity"))
            elif rsi > 70:
                alerts.append(("warning", f"📈 VN-Index overbought (RSI: {rsi:.1f}) - caution advised"))

    # VN30 Breadth Alert
    if 'vn30_analysis' in vn_market_data and vn_market_data['vn30_analysis']:
        vn30_analysis = vn_market_data['vn30_analysis']
        if vn30_analysis.get('advance_decline_ratio'):
            ad_ratio = vn30_analysis['advance_decline_ratio']
            if ad_ratio > 2:
                alerts.append(("success", f"🟢 Strong VN30 breadth - broad rally ({ad_ratio:.1f}:1)"))
            elif ad_ratio < 0.5:
                alerts.append(("danger", f"🔴 Weak VN30 breadth - selling pressure ({ad_ratio:.1f}:1)"))

    # Economic Alerts
    if economic_score > 75:
        alerts.append(("success", "🚀 Excellent economic conditions favor risk-on positioning"))
    elif economic_score < 40:
        alerts.append(("danger", "⚠️ Poor economic conditions suggest defensive positioning"))

    # Currency Alert
    if global_context.get('usd_vnd', {}).get('change'):
        vnd_change = global_context['usd_vnd']['change']
        if abs(vnd_change) > 3:
            alerts.append(("warning", f"💱 Significant VND movement ({vnd_change:+.2f}%) - currency risk"))

    if alerts:
        cols = st.columns(min(len(alerts), 3))
        for i, (alert_type, message) in enumerate(alerts):
            with cols[i % 3]:
                st.markdown(f'<div class="alert-{alert_type}">{message}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-success">✅ No critical alerts - market conditions stable</div>',
                    unsafe_allow_html=True)

    # Quick Market Overview
    st.markdown("---")
    st.subheader("📊 Market Snapshot")

    tab1, tab2, tab3 = st.tabs(["🌍 Global Markets", "🇻🇳 Vietnam Sectors", "💼 Top Movers"])

    with tab1:
        if global_context:
            cols = st.columns(3)
            for i, (key, data) in enumerate(global_context.items()):
                if i < 6:  # Show first 6
                    with cols[i % 3]:
                        change = data.get('change', 0)
                        emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
                        st.write(f"{emoji} **{data['name']}**: {change:+.2f}%")

    with tab2:
        if 'sectors' in vn_market_data:
            cols = st.columns(2)
            sectors_items = list(vn_market_data['sectors'].items())
            for i, (sector, data) in enumerate(sectors_items):
                with cols[i % 2]:
                    ret = data.get('avg_return_1d', 0)
                    emoji = "🟢" if ret > 0 else "🔴" if ret < 0 else "⚪"
                    winners = data.get('winners', 0)
                    total = data.get('stock_count', 1)
                    st.write(f"{emoji} **{sector}**: {ret:+.2f}% ({winners}/{total} ↑)")

    with tab3:
        if 'top_stocks' in vn_market_data:
            top_stocks = vn_market_data['top_stocks'][:6]
            cols = st.columns(3)
            for i, stock in enumerate(top_stocks):
                with cols[i % 3]:
                    change = stock['change_pct']
                    emoji = "🟢" if change > 0 else "🔴"
                    sector = stock.get('sector', 'Other')
                    st.write(f"{emoji} **{stock['symbol']}** ({sector}): {change:+.2f}%")


def show_enhanced_vietnam_page(vn_market_data, vn_economic_data, charts, show_technical=True):
    """Enhanced Vietnam market page with comprehensive analysis."""
    st.header("🇻🇳 Vietnam Market & Economic Analysis")

    if 'error' in vn_market_data:
        st.error(f"Market data error: {vn_market_data['error']}")
        return

    # Vietnam Indices Overview
    st.subheader("📈 Vietnam Stock Indices")

    if 'indices' in vn_market_data:
        indices = vn_market_data['indices']
        cols = st.columns(len(indices))

        for i, (code, data) in enumerate(indices.items()):
            with cols[i]:
                change = data['change_pct']
                delta_class = "metric-positive" if change > 0 else "metric-negative" if change < 0 else "metric-neutral"
                st.markdown(f'<div class="stMetric {delta_class}">', unsafe_allow_html=True)
                st.metric(
                    label=f"{data['name']} ({data['exchange']})",
                    value=f"{data['price']:,.2f}",
                    delta=f"{change:+.2f}%"
                )
                st.markdown('</div>', unsafe_allow_html=True)

                # Technical indicators
                if show_technical:
                    if data.get('rsi'):
                        st.caption(f"RSI: {data['rsi']:.1f} ({data.get('rsi_signal', 'N/A')})")
                    if data.get('sma_50'):
                        price = data['price']
                        sma50 = data['sma_50']
                        vs_sma = ((price - sma50) / sma50 * 100) if sma50 else 0
                        st.caption(f"vs SMA50: {vs_sma:+.1f}%")

    # VN30 Deep Dive
    st.markdown("---")
    st.subheader("🏆 VN30 Index Analysis")

    if 'vn30_analysis' in vn_market_data and vn_market_data['vn30_analysis']:
        vn30 = vn_market_data['vn30_analysis']

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Advancing Stocks", vn30.get('advancing', 0))
        with col2:
            st.metric("Declining Stocks", vn30.get('declining', 0))
        with col3:
            ad_ratio = vn30.get('advance_decline_ratio', 0)
            st.metric("A/D Ratio", f"{ad_ratio:.2f}" if ad_ratio else "N/A")
        with col4:
            avg_change = vn30.get('avg_change', 0)
            st.metric("Avg Change", f"{avg_change:+.2f}%")

        # VN30 charts
        if charts.get('vn30_analysis'):
            st.plotly_chart(charts['vn30_analysis'], use_container_width=True)

    # Technical Analysis Charts
    if show_technical:
        st.markdown("---")
        st.subheader("📊 Technical Analysis")

        tab1, tab2, tab3 = st.tabs(["Indices Comparison", "Market Breadth", "Sector Heatmap"])

        with tab1:
            if charts.get('vn_indices_comparison'):
                st.plotly_chart(charts['vn_indices_comparison'], use_container_width=True)

        with tab2:
            if charts.get('market_breadth'):
                st.plotly_chart(charts['market_breadth'], use_container_width=True)

                # Market breadth interpretation
                if 'market_breadth' in vn_market_data:
                    breadth = vn_market_data['market_breadth']
                    momentum = breadth.get('breadth_momentum', 'Neutral')
                    if momentum == 'Positive':
                        st.success("🟢 Positive market breadth - broad-based strength")
                    elif momentum == 'Negative':
                        st.error("🔴 Negative market breadth - widespread weakness")
                    else:
                        st.info("🟡 Neutral market breadth - mixed signals")

        with tab3:
            if charts.get('sector_heatmap'):
                st.plotly_chart(charts['sector_heatmap'], use_container_width=True)

    # Economic Indicators
    st.markdown("---")
    st.subheader("🏛️ Vietnam Economic Indicators")

    if vn_economic_data:
        if charts.get('vn_economic_dashboard'):
            st.plotly_chart(charts['vn_economic_dashboard'], use_container_width=True)

        # Economic summary
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Key Economic Metrics:**")
            for key, data in list(vn_economic_data.items())[:6]:
                if data.get('value') is not None:
                    value = data['value']
                    unit = data.get('unit', '')
                    change = data.get('change')
                    change_text = f" ({change:+.1f}%)" if change else ""
                    st.write(f"• **{data['name']}**: {value:.2f}{unit}{change_text}")

        with col2:
            # Calculate and show economic score
            economic_score, rating, factors = calculate_economic_score(vn_economic_data)
            st.markdown(f"""
            <div class="analysis-card">
                <h4>Economic Health Score: {economic_score:.0f}/100</h4>
                <p><strong>Rating:</strong> {rating}</p>
                <p><strong>Key Factors:</strong></p>
                <ul>
                {''.join([f"<li>{factor}</li>" for factor in factors[:3]])}
                </ul>
            </div>
            """, unsafe_allow_html=True)

    # Detailed Stock Analysis
    st.markdown("---")
    st.subheader("📋 Top Stock Performers")

    if 'top_stocks' in vn_market_data:
        # Create enhanced stock table
        top_stocks = vn_market_data['top_stocks'][:20]

        if top_stocks:
            stock_data = []
            for i, stock in enumerate(top_stocks, 1):
                stock_data.append({
                    "Rank": i,
                    "Symbol": stock['symbol'],
                    "Sector": stock.get('sector', 'Other'),
                    "Price": f"{stock['price']:,.0f}",
                    "1D Change": f"{stock['change_pct']:+.2f}%",
                    "1W Change": f"{stock.get('change_1w', 0):+.2f}%",
                    "1M Change": f"{stock.get('change_1m', 0):+.2f}%",
                    "Volume": format_number(stock.get('volume', 0), 0),
                    "Vol Ratio": f"{stock.get('volume_ratio', 1):.1f}x",
                    "VN30": "✓" if stock.get('is_vn30') else ""
                })

            df = pd.DataFrame(stock_data)
            st.dataframe(df, use_container_width=True, hide_index=True)


def show_enhanced_investment_analysis_page(us_data, vn_market_data, vn_economic_data, fed_data, global_context,
                                           risk_tolerance):
    """Enhanced investment analysis with comprehensive recommendations."""
    st.header("💼 Advanced Investment Analysis")

    # Generate comprehensive recommendations
    recommendations = generate_comprehensive_investment_recommendation(
        us_data, vn_economic_data, vn_market_data, global_context, fed_data, risk_tolerance
    )

    # Executive Summary
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"""
        <div class="recommendation-card">
            <h3>Investment Recommendation Summary</h3>
            <p><strong>Overall Score:</strong> {recommendations['overall_score']}/100</p>
            <p><strong>Market Timing:</strong> {recommendations['market_timing']}</p>
            <p><strong>Risk Level:</strong> {recommendations['risk_level']}</p>
            <p>{recommendations['summary']}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="analysis-card">
            <h4>Your Risk Profile</h4>
            <p><strong>{risk_tolerance}</strong></p>
            {get_risk_profile_description(risk_tolerance)}
        </div>
        """, unsafe_allow_html=True)

    # Detailed Analysis Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Key Recommendations",
        "🇺🇸 Fed Impact Analysis",
        "🇻🇳 Vietnam Macro Analysis",
        "📊 Sector Strategy"
    ])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🚀 Investment Opportunities")
            for opportunity in recommendations.get('opportunities', []):
                st.markdown(f'<div class="alert-success">{opportunity}</div>', unsafe_allow_html=True)

            st.markdown("### 💡 Key Recommendations")
            for i, rec in enumerate(recommendations.get('key_recommendations', [])[:8], 1):
                st.write(f"{i}. {rec}")

        with col2:
            st.markdown("### ⚠️ Risk Factors")
            for risk in recommendations.get('risk_factors', []):
                st.markdown(f'<div class="alert-danger">{risk}</div>', unsafe_allow_html=True)

            if recommendations.get('currency_considerations'):
                st.markdown("### 💱 Currency Considerations")
                for curr in recommendations['currency_considerations']:
                    st.markdown(f'<div class="alert-info">{curr}</div>', unsafe_allow_html=True)

    with tab2:
        fed_analysis = recommendations.get('fed_analysis', {})

        col1, col2 = st.columns(2)
        with col1:
            impact_score = fed_analysis.get('fed_impact_score', 0)
            st.metric("Fed Impact Score", f"{impact_score:+d}/100",
                      "Positive for EM" if impact_score > 0 else "Challenging for EM")

            st.markdown("**Fed Policy Assessment:**")
            for factor in fed_analysis.get('key_factors', []):
                st.write(f"• {factor}")

        with col2:
            st.markdown("**Fed-Vietnam Strategy:**")
            for rec in fed_analysis.get('recommendations', []):
                st.write(f"• {rec}")

            # Show Fed correlation chart if available
            if charts.get('fed_vietnam_correlation'):
                st.plotly_chart(charts['fed_vietnam_correlation'], use_container_width=True)

    with tab3:
        macro_analysis = recommendations.get('macro_analysis', {})

        col1, col2 = st.columns(2)
        with col1:
            macro_score = macro_analysis.get('macro_score', 50)
            st.metric("Macro Health Score", f"{macro_score:.0f}/100")

            st.markdown("**Economic Drivers:**")
            for driver in macro_analysis.get('economic_drivers', []):
                st.write(f"• {driver}")

        with col2:
            st.markdown("**Market Implications:**")
            for implication in macro_analysis.get('market_implications', []):
                st.write(f"• {implication}")

            # Sector rotation recommendations
            sector_rotation = macro_analysis.get('sector_rotation', {})
            if sector_rotation:
                st.markdown("**Sector Rotation Themes:**")
                for theme, sectors in sector_rotation.items():
                    theme_name = theme.replace('_', ' ').title()
                    st.write(f"• **{theme_name}**: {', '.join(sectors)}")

    with tab4:
        if 'sectors' in vn_market_data:
            st.markdown("### 🏭 Sector Investment Strategy")

            sectors = vn_market_data['sectors']
            sector_data = []

            for sector, performance in sectors.items():
                rationale = get_sector_investment_rationale(sector, performance, vn_economic_data)

                sector_data.append({
                    "Sector": sector,
                    "1D Return": f"{performance.get('avg_return_1d', 0):+.2f}%",
                    "1W Return": f"{performance.get('avg_return_1w', 0):+.2f}%",
                    "1M Return": f"{performance.get('avg_return_1m', 0):+.2f}%",
                    "Winners/Total": f"{performance.get('winners', 0)}/{performance.get('stock_count', 0)}",
                    "Investment Rationale": rationale
                })

            df = pd.DataFrame(sector_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Show sector heatmap if available
            if charts.get('sector_heatmap'):
                st.plotly_chart(charts['sector_heatmap'], use_container_width=True)

    # Portfolio Allocation Recommendations
    st.markdown("---")
    st.subheader("📈 Recommended Portfolio Allocation")

    allocation_recs = get_portfolio_allocation_recommendations(
        risk_tolerance, recommendations['overall_score'], recommendations['risk_level']
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🇻🇳 Vietnam Allocation")
        st.markdown(allocation_recs['vietnam'])

    with col2:
        st.markdown("### 🌍 Global Context")
        st.markdown(allocation_recs['global'])

    with col3:
        st.markdown("### ⚖️ Risk Management")
        st.markdown(allocation_recs['risk_management'])


def get_risk_profile_description(risk_tolerance: str) -> str:
    """Get risk profile description."""
    profiles = {
        "Conservative": """
        <ul>
        <li>Capital preservation focus</li>
        <li>Steady income preferred</li>
        <li>Low volatility tolerance</li>
        <li>Longer time horizon</li>
        </ul>
        """,
        "Moderate": """
        <ul>
        <li>Balanced growth & income</li>
        <li>Moderate volatility acceptance</li>
        <li>Diversified approach</li>
        <li>Medium-term focus</li>
        </ul>
        """,
        "Aggressive": """
        <ul>
        <li>Growth maximization</li>
        <li>High volatility tolerance</li>
        <li>Active trading approach</li>
        <li>Long-term wealth building</li>
        </ul>
        """
    }
    return profiles.get(risk_tolerance, "")


def get_portfolio_allocation_recommendations(risk_tolerance: str, overall_score: float, risk_level: str) -> Dict[
    str, str]:
    """Get detailed portfolio allocation recommendations."""

    base_allocations = {
        "Conservative": {"vietnam": "5-12%", "bonds": "60-70%", "intl_equity": "20-30%"},
        "Moderate": {"vietnam": "10-20%", "bonds": "40-50%", "intl_equity": "30-45%"},
        "Aggressive": {"vietnam": "15-30%", "bonds": "15-25%", "intl_equity": "45-65%"}
    }

    base = base_allocations[risk_tolerance]

    # Adjust based on conditions
    adjustments = []
    if overall_score > 70:
        adjustments.append("📈 Favorable conditions - consider upper range")
    elif overall_score < 40:
        adjustments.append("📉 Challenging conditions - consider lower range")

    if risk_level == "High":
        adjustments.append("⚠️ High risk environment - reduce allocation")
    elif risk_level == "Low":
        adjustments.append("✅ Low risk environment - potential to increase")

    return {
        "vietnam": f"""
        **Recommended Range:** {base['vietnam']}

        **Sector Focus:**
        - Banking & Financial Services
        - Technology & Export Manufacturing  
        - Consumer Goods & Services

        **Considerations:**
        {chr(10).join([f"• {adj}" for adj in adjustments])}
        """,

        "global": f"""
        **International Equity:** {base['intl_equity']}
        **Fixed Income:** {base['bonds']}

        **Global Themes:**
        - US Large Cap Technology
        - Developed Market Value
        - Emerging Market Selective
        """,

        "risk_management": f"""
        **Key Strategies:**
        • Currency hedging for large VN positions
        • Regular rebalancing (quarterly)
        • Stop-loss levels: -15% for individual stocks
        • Position sizing: Max 5% per single stock

        **Monitoring:**
        • Fed policy changes
        • VN economic indicators
        • USD/VND exchange rate
        """
    }


def show_enhanced_global_markets_page(global_context, us_data):
    """Enhanced global markets page with Vietnam context."""
    st.header("🌍 Global Markets & Vietnam Impact Analysis")

    # Global market overview
    st.subheader("📈 Major Global Indices & Commodities")

    if global_context:
        # Create metrics display
        cols = st.columns(3)
        items = list(global_context.items())

        for i, (key, data) in enumerate(items):
            with cols[i % 3]:
                change = data.get('change', 0)
                delta_class = "metric-positive" if change > 0 else "metric-negative" if change < 0 else "metric-neutral"
                st.markdown(f'<div class="stMetric {delta_class}">', unsafe_allow_html=True)

                # Format value based on indicator type
                value = data.get('value', 0)
                if 'currency' in key.lower():
                    display_value = f"{value:,.0f}"
                elif 'oil' in key.lower() or 'gold' in key.lower():
                    display_value = f"${value:,.2f}"
                else:
                    display_value = f"{value:,.2f}"

                st.metric(
                    label=data['name'],
                    value=display_value,
                    delta=f"{change:+.2f}%"
                )
                st.markdown('</div>', unsafe_allow_html=True)

    # Impact analysis
    st.markdown("---")
    st.subheader("🎯 Impact on Vietnam Markets")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💵 Currency & Capital Flows")

        if 'usd_vnd' in global_context:
            vnd_data = global_context['usd_vnd']
            vnd_change = vnd_data.get('change', 0)

            if abs(vnd_change) > 2:
                impact_level = "High"
                color = "danger"
            elif abs(vnd_change) > 1:
                impact_level = "Medium"
                color = "warning"
            else:
                impact_level = "Low"
                color = "success"

            st.markdown(f"""
            <div class="alert-{color}">
                <strong>VND Impact Level: {impact_level}</strong><br>
                USD/VND change: {vnd_change:+.2f}%<br>
                {"VND strengthening supports foreign investment" if vnd_change < 0 else
            "VND weakening may pressure foreign flows" if vnd_change > 0 else "Stable currency environment"}
            </div>
            """, unsafe_allow_html=True)

        if 'dxy' in global_context:
            dxy_change = global_context['dxy'].get('change', 0)
            st.write(f"• **US Dollar Index**: {dxy_change:+.2f}%")
            if dxy_change > 2:
                st.write("  → Strong USD typically pressures EM currencies and flows")
            elif dxy_change < -2:
                st.write("  → Weak USD typically supports EM investment flows")

    with col2:
        st.markdown("### 🛢️ Commodity Impact")

        commodity_impacts = []
        if 'oil_brent' in global_context:
            oil_change = global_context['oil_brent'].get('change', 0)
            oil_impact = "Positive for energy costs" if oil_change < -5 else "Negative for energy costs" if oil_change > 5 else "Neutral impact"
            commodity_impacts.append(f"• **Oil**: {oil_change:+.2f}% → {oil_impact}")

        if 'copper' in global_context:
            copper_change = global_context['copper'].get('change', 0)
            copper_impact = "Positive for manufacturing" if copper_change > 3 else "Negative for manufacturing" if copper_change < -3 else "Neutral impact"
            commodity_impacts.append(f"• **Copper**: {copper_change:+.2f}% → {copper_impact}")

        if 'gold' in global_context:
            gold_change = global_context['gold'].get('change', 0)
            gold_impact = "Risk-off sentiment" if gold_change > 2 else "Risk-on sentiment" if gold_change < -2 else "Neutral sentiment"
            commodity_impacts.append(f"• **Gold**: {gold_change:+.2f}% → {gold_impact}")

        for impact in commodity_impacts:
            st.write(impact)

    # Fed Policy Global Impact
    if us_data:
        st.markdown("---")
        st.subheader("🏦 Fed Policy Global Transmission")

        col1, col2 = st.columns(2)

        with col1:
            if 'fed_rate' in us_data:
                fed_rate = us_data['fed_rate']['value']
                st.metric("Current Fed Rate", f"{fed_rate:.2f}%")

                if fed_rate > 5:
                    st.error("🔴 High rates create EM headwinds")
                elif fed_rate < 2:
                    st.success("🟢 Low rates support EM flows")
                else:
                    st.info("🟡 Moderate rates - mixed impact")

        with col2:
            if 'inflation' in us_data:
                inflation = us_data['inflation']['value']
                st.metric("US Inflation", f"{inflation:.2f}%")

                if inflation > 3:
                    st.warning("📈 High inflation may force Fed hawkishness")
                elif inflation < 2:
                    st.success("📉 Low inflation allows Fed flexibility")

    # Global correlations and insights
    st.markdown("---")
    st.subheader("🔗 Vietnam Market Correlations")

    correlation_insights = [
        "📊 **US Dollar strength** typically correlates negatively with Vietnam market performance",
        "🛢️ **Oil prices** have mixed impact - negative for inflation but positive for energy sector",
        "📈 **Fed policy** is a key driver of foreign investment flows to Vietnam",
        "🌏 **Regional markets** (China, Korea) often move in tandem with Vietnam",
        "💰 **Commodity prices** affect Vietnam's manufacturing and export competitiveness"
    ]

    for insight in correlation_insights:
        st.write(insight)