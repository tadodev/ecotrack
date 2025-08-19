# app_enhanced.py - Enhanced main application
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu
import logging

# Enhanced imports
from charts.builders_enhanced import create_comprehensive_charts
from data.global_markets import get_global_market_data
from data.us import get_enhanced_us_data, get_fed_probability, get_fred_client
from data.vn_enhanced import get_comprehensive_vn_market_data, get_index_history
from data.te_enhanced import get_comprehensive_vn_data, get_global_economic_context, calculate_economic_score
from ui.pages_enhanced import (
    apply_enhanced_css, enhanced_header_card,
    show_enhanced_overview_page, show_enhanced_vietnam_page,
    show_enhanced_investment_analysis_page, show_enhanced_global_markets_page
)
from ui.pages import show_us_economy_page, show_settings_page  # Keep original US and Settings pages
from utils.logging import init_logging

# Initialize logging
logger = init_logging()


def main():
    """Enhanced main application with comprehensive economic analysis."""
    st.set_page_config(
        page_title="Advanced Economic Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply enhanced styling
    apply_enhanced_css()
    enhanced_header_card()

    # Enhanced top navigation
    selected = option_menu(
        menu_title=None,
        options=[
            "Executive Overview",
            "US Economy",
            "Vietnam Markets",
            "Global Context",
            "Investment Analysis",
            "Economic Research",
            "Settings"
        ],
        icons=[
            "speedometer2",
            "flag-usa",
            "geo-alt",
            "globe",
            "graph-up",
            "bar-chart-line",
            "gear"
        ],
        orientation="horizontal",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "#007bff", "font-size": "16px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "center",
                "margin": "0px",
                "--hover-color": "#eee"
            },
            "nav-link-selected": {"background-color": "#007bff"},
        }
    )

    # Enhanced sidebar controls
    with st.sidebar:
        st.header("🎛️ Advanced Dashboard Controls")

        # Auto-refresh settings
        auto_refresh = st.toggle("Auto Refresh", value=True, help="Refresh data every 10 minutes")
        if auto_refresh:
            refresh_interval = st.selectbox(
                "Refresh Interval",
                options=[5, 10, 15, 30],
                index=1,
                format_func=lambda x: f"{x} minutes"
            )
            st_autorefresh(interval=refresh_interval * 60_000, key="datarefresh")

        # Data settings
        st.markdown("### 📊 Data Configuration")
        data_period = st.selectbox(
            "Historical Data Period",
            options=[6, 12, 18, 24, 36],
            index=1,
            format_func=lambda x: f"{x} months"
        )

        # Analysis settings
        st.markdown("### 🔧 Analysis Settings")
        show_technical = st.checkbox("Technical Indicators", value=True)
        show_correlations = st.checkbox("Correlation Analysis", value=True)
        show_economic_score = st.checkbox("Economic Scoring", value=True)

        # Investment settings
        st.markdown("### 💼 Investment Preferences")
        risk_tolerance = st.selectbox(
            "Risk Tolerance",
            ["Conservative", "Moderate", "Aggressive"],
            index=1
        )
        investment_horizon = st.selectbox(
            "Investment Horizon",
            ["Short-term (< 1 year)", "Medium-term (1-3 years)", "Long-term (3+ years)"],
            index=2
        )

        # Display settings
        st.markdown("### 🎨 Display Options")
        chart_theme = st.selectbox("Chart Theme", ["plotly", "plotly_white", "plotly_dark"])
        show_raw_data = st.checkbox("Show Raw Data Tables", value=False)

        # Quick stats
        st.markdown("---")
        st.markdown("### 📈 Quick Stats")
        st.markdown(f"**Session Time**: {st.session_state.get('session_start', 'New Session')}")
        st.markdown(f"**Data Sources**: 4 Active")
        st.markdown(f"**Last Update**: {st.session_state.get('last_update', 'Loading...')}")

    # Data loading with enhanced error handling and caching
    try:
        with st.spinner("🔄 Loading comprehensive economic data..."):
            # Load all data sources
            data_sources = load_all_data(data_period)

            # Update session state
            st.session_state['last_update'] = data_sources['timestamp']
            if 'session_start' not in st.session_state:
                st.session_state['session_start'] = data_sources['timestamp']

            # Create comprehensive charts
            charts = create_comprehensive_charts(
                data_sources['us_series'],
                data_sources['vn_market'],
                data_sources['vn_economic'],
                data_sources['global_context']
            )

    except Exception as e:
        st.error(f"❌ Data loading error: {str(e)}")
        logger.error(f"Data loading failed: {e}")
        st.stop()

    # Route to enhanced pages
    if selected == "Executive Overview":
        show_enhanced_overview_page(
            data_sources['us_data'],
            data_sources['vn_market'],
            data_sources['vn_economic'],
            data_sources['fed_data'],
            data_sources['global_context']
        )

    elif selected == "US Economy":
        show_us_economy_page(
            data_sources['us_data'],
            data_sources['us_series'],
            data_sources['fed_data']
        )
        # Render US charts
        if charts.get("us_indicators"):
            st.plotly_chart(charts["us_indicators"], use_container_width=True, theme=chart_theme)

    elif selected == "Vietnam Markets":
        show_enhanced_vietnam_page(
            data_sources['vn_market'],
            data_sources['vn_economic'],
            charts,
            show_technical
        )

    elif selected == "Global Context":
        show_enhanced_global_markets_page(
            data_sources['global_context'],
            data_sources['us_data']
        )
        # Render global context charts
        if charts.get("global_context"):
            st.plotly_chart(charts["global_context"], use_container_width=True, theme=chart_theme)

    elif selected == "Investment Analysis":
        show_enhanced_investment_analysis_page(
            data_sources['us_data'],
            data_sources['vn_market'],
            data_sources['vn_economic'],
            data_sources['fed_data'],
            data_sources['global_context'],
            risk_tolerance
        )

    elif selected == "Economic Research":
        show_economic_research_page(
            data_sources,
            charts,
            show_correlations,
            show_economic_score
        )

    elif selected == "Settings":
        show_settings_page(get_fred_client)

    # Raw data display (optional)
    if show_raw_data and st.sidebar.button("📋 Show Raw Data"):
        show_raw_data_section(data_sources)


@st.cache_data(ttl=600, show_spinner=False)  # 10-minute cache
def load_all_data(data_period: int) -> dict:
    """Load all data sources with enhanced error handling."""
    import datetime as dt

    data_sources = {
        'timestamp': dt.datetime.now(tz=dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    }

    try:
        # US economic data
        logger.info("Loading US economic data...")
        data_sources['us_data'], data_sources['us_series'] = get_enhanced_us_data(data_period)

        # Fed data
        logger.info("Loading Fed probability data...")
        data_sources['fed_data'] = get_fed_probability()

        # Vietnam market data (enhanced)
        logger.info("Loading Vietnam market data...")
        data_sources['vn_market'] = get_comprehensive_vn_market_data()

        # Vietnam economic data (Trading Economics)
        logger.info("Loading Vietnam economic indicators...")
        data_sources['vn_economic'] = get_comprehensive_vn_data()

        # Global context data
        logger.info("Loading global economic context...")
        data_sources['global_context'] = get_global_economic_context()

        # Global markets (existing)
        logger.info("Loading global markets data...")
        data_sources['global_markets'] = get_global_market_data()

        logger.info("All data sources loaded successfully")

    except Exception as e:
        logger.error(f"Error loading data sources: {e}")
        # Ensure we have at least empty dictionaries to prevent errors
        for key in ['us_data', 'us_series', 'fed_data', 'vn_market', 'vn_economic', 'global_context', 'global_markets']:
            if key not in data_sources:
                data_sources[key] = {}

    return data_sources


def show_economic_research_page(data_sources: dict, charts: dict, show_correlations: bool, show_economic_score: bool):
    """Advanced economic research and analysis page."""
    st.header("🔬 Economic Research & Advanced Analytics")

    # Economic Health Scoring
    if show_economic_score and data_sources['vn_economic']:
        st.subheader("🎯 Vietnam Economic Health Assessment")

        economic_score, rating, key_factors = calculate_economic_score(data_sources['vn_economic'])

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            st.metric("Economic Score", f"{economic_score:.0f}/100", rating)

        with col2:
            # Score trend (would need historical data in real implementation)
            score_change = st.session_state.get('prev_economic_score', economic_score)
            trend = economic_score - score_change
            st.metric("Score Trend", f"{trend:+.1f}",
                      "Improving" if trend > 0 else "Declining" if trend < 0 else "Stable")
            st.session_state['prev_economic_score'] = economic_score

        with col3:
            st.markdown("**Key Economic Factors:**")
            for factor in key_factors[:4]:
                st.write(f"• {factor}")

    # Advanced Analytics Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Correlation Matrix",
        "📈 Trend Analysis",
        "🔮 Predictive Indicators",
        "🌍 Global Linkages"
    ])

    with tab1:
        if show_correlations:
            show_correlation_analysis(data_sources)

    with tab2:
        show_trend_analysis(data_sources, charts)

    with tab3:
        show_predictive_indicators(data_sources)

    with tab4:
        show_global_linkages(data_sources)


def show_correlation_analysis(data_sources: dict):
    """Show correlation analysis between different economic indicators."""
    st.markdown("### 🔗 Economic Indicator Correlations")

    # This would ideally use historical time series data
    # For now, showing conceptual correlations

    correlation_insights = [
        {
            "pair": "US Fed Rate ↔ VN-Index",
            "correlation": -0.65,
            "interpretation": "Strong negative correlation - higher US rates typically pressure VN stocks"
        },
        {
            "pair": "USD/VND ↔ Foreign Investment",
            "correlation": -0.52,
            "interpretation": "Moderate negative correlation - VND strength attracts foreign capital"
        },
        {
            "pair": "Vietnam GDP ↔ VN30 Performance",
            "correlation": 0.73,
            "interpretation": "Strong positive correlation - economic growth drives market performance"
        },
        {
            "pair": "Oil Prices ↔ Vietnam Inflation",
            "correlation": 0.45,
            "interpretation": "Moderate positive correlation - energy costs impact inflation"
        },
        {
            "pair": "China PMI ↔ Vietnam Exports",
            "correlation": 0.58,
            "interpretation": "Moderate positive correlation - China demand affects Vietnam exports"
        }
    ]

    for insight in correlation_insights:
        col1, col2, col3 = st.columns([2, 1, 3])
        with col1:
            st.write(f"**{insight['pair']}**")
        with col2:
            corr = insight['correlation']
            color = "🟢" if abs(corr) > 0.6 else "🟡" if abs(corr) > 0.4 else "🔴"
            st.write(f"{color} {corr:.2f}")
        with col3:
            st.write(insight['interpretation'])


def show_trend_analysis(data_sources: dict, charts: dict):
    """Show trend analysis of key indicators."""
    st.markdown("### 📈 Multi-Factor Trend Analysis")

    # Vietnam Economic Trends
    if data_sources['vn_economic']:
        st.markdown("#### 🇻🇳 Vietnam Economic Momentum")

        trend_indicators = []
        for key, data in data_sources['vn_economic'].items():
            if data.get('value') is not None and data.get('change') is not None:
                change = data['change']
                if abs(change) > 0.1:  # Only show significant changes
                    trend_direction = "📈" if change > 0 else "📉"
                    trend_indicators.append(f"{trend_direction} **{data['name']}**: {change:+.2f}%")

        for indicator in trend_indicators[:6]:
            st.write(indicator)

    # Market Trend Analysis
    if 'indices' in data_sources['vn_market']:
        st.markdown("#### 📊 Market Technical Trends")

        for index_name, index_data in data_sources['vn_market']['indices'].items():
            if index_name in ['vnindex', 'vn30']:
                rsi = index_data.get('rsi')
                sma_50 = index_data.get('sma_50')
                price = index_data.get('price', 0)

                trend_signals = []
                if rsi:
                    if rsi > 70:
                        trend_signals.append("🔴 Overbought")
                    elif rsi < 30:
                        trend_signals.append("🟢 Oversold")
                    else:
                        trend_signals.append("🟡 Neutral RSI")

                if sma_50 and price:
                    if price > sma_50 * 1.02:
                        trend_signals.append("🟢 Above SMA50")
                    elif price < sma_50 * 0.98:
                        trend_signals.append("🔴 Below SMA50")
                    else:
                        trend_signals.append("🟡 Near SMA50")

                if trend_signals:
                    st.write(f"**{index_data['name']}**: {' | '.join(trend_signals)}")


def show_predictive_indicators(data_sources: dict):
    """Show leading indicators for Vietnam market prediction."""
    st.markdown("### 🔮 Leading Economic Indicators")

    leading_indicators = [
        {
            "indicator": "US 10Y-2Y Yield Curve",
            "current_status": "Monitor",
            "prediction": "Recession risk indicator for global markets",
            "vietnam_impact": "Medium - affects foreign investment flows"
        },
        {
            "indicator": "Vietnam Manufacturing PMI",
            "current_status": data_sources['vn_economic'].get('manufacturing_pmi', {}).get('value', 'N/A'),
            "prediction": "Leading indicator for GDP growth",
            "vietnam_impact": "High - directly affects market sentiment"
        },
        {
            "indicator": "China Economic Activity",
            "current_status": "Monitor",
            "prediction": "Vietnam's largest trading partner",
            "vietnam_impact": "High - trade and export implications"
        },
        {
            "indicator": "Fed Rate Expectations",
            "current_status": data_sources['fed_data'].get('next_meeting', {}).get('cut_25bp', 'N/A'),
            "prediction": "Drives EM capital flows",
            "vietnam_impact": "High - foreign investment sensitivity"
        }
    ]

    for indicator in leading_indicators:
        with st.expander(f"📊 {indicator['indicator']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Current Status**: {indicator['current_status']}")
                st.write(f"**Predictive Power**: {indicator['prediction']}")
            with col2:
                st.write(f"**Vietnam Impact**: {indicator['vietnam_impact']}")


def show_global_linkages(data_sources: dict):
    """Show Vietnam's linkages with global economy."""
    st.markdown("### 🌍 Vietnam's Global Economic Linkages")

    linkages = [
        {
            "region": "🇺🇸 United States",
            "relationship": "Major export destination & FDI source",
            "key_factors": ["Fed policy", "USD strength", "Trade relations"],
            "current_impact": "Medium positive" if data_sources['fed_data'].get('next_meeting', {}).get('cut_25bp',
                                                                                                        '0%').rstrip(
                '%').replace('+', '').replace('-', '').isdigit() and int(
                data_sources['fed_data'].get('next_meeting', {}).get('cut_25bp', '0%').rstrip('%').replace('+',
                                                                                                           '').replace(
                    '-', '')) > 50 else "Medium negative"
        },
        {
            "region": "🇨🇳 China",
            "relationship": "Largest trading partner",
            "key_factors": ["Manufacturing demand", "Supply chains", "Commodity prices"],
            "current_impact": "High positive"
        },
        {
            "region": "🇪🇺 European Union",
            "relationship": "Key export market & investment source",
            "key_factors": ["Economic growth", "Green transition", "FDI flows"],
            "current_impact": "Medium positive"
        },
        {
            "region": "🌏 ASEAN",
            "relationship": "Regional integration & competition",
            "key_factors": ["Trade agreements", "Supply chain", "Tourism"],
            "current_impact": "High positive"
        }
    ]

    for linkage in linkages:
        with st.container():
            st.markdown(f"#### {linkage['region']}")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Relationship**: {linkage['relationship']}")
            with col2:
                st.write(f"**Key Factors**: {', '.join(linkage['key_factors'])}")
            with col3:
                impact_color = "🟢" if "positive" in linkage['current_impact'] else "🟡" if "neutral" in linkage[
                    'current_impact'] else "🔴"
                st.write(f"**Current Impact**: {impact_color} {linkage['current_impact']}")


def show_raw_data_section(data_sources: dict):
    """Display raw data for debugging/analysis purposes."""
    st.markdown("---")
    st.subheader("📋 Raw Data Explorer")

    data_tabs = st.tabs([
        "US Economic",
        "Vietnam Markets",
        "Vietnam Economic",
        "Global Context"
    ])

    with data_tabs[0]:
        st.json(data_sources['us_data'])

    with data_tabs[1]:
        st.json(data_sources['vn_market'])

    with data_tabs[2]:
        st.json(data_sources['vn_economic'])

    with data_tabs[3]:
        st.json(data_sources['global_context'])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        logger.error(f"Application failed: {e}")
        st.info("Please refresh the page or contact support if the issue persists.")