# app.py
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

from charts.builders import create_enhanced_charts
from data.global_markets import get_global_market_data
from data.us import get_enhanced_us_data, get_fed_probability, get_fred_client
from data.vn import get_enhanced_vn_data
from ui.pages import (
    apply_custom_css, header_card,
    show_overview_page, show_us_economy_page, show_vietnam_market_page,
    show_global_markets_page, show_investment_analysis_page, show_settings_page
)


def main():
    st.set_page_config(page_title="Modern Economic Dashboard", page_icon="📈", layout="wide")
    apply_custom_css()
    header_card()

    # --- Top nav ---
    selected = option_menu(
        menu_title=None,
        options=["Overview", "US Economy", "Vietnam Market", "Global Markets", "Investment Analysis", "Settings"],
        icons=["house", "flag", "geo-alt", "globe", "graph-up", "gear"],
        orientation="horizontal",
        default_index=0,
    )

    # --- Sidebar (your existing controls) ---
    with st.sidebar:
        st.header("🎛️ Dashboard Controls")
        auto_refresh = st.toggle("Auto Refresh (10 min)", value=True)
        if auto_refresh:
            st_autorefresh(interval=600_000, key="datarefresh")

        data_period = st.selectbox("Data Period", options=[6, 12, 18, 24], index=1,
                                   format_func=lambda x: f"{x} months")
        show_technical = st.checkbox("Show Technical Indicators", value=True)
        show_recommendations = st.checkbox("Show Investment Recommendations", value=True)
        risk_tolerance = st.selectbox("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"])

        st.markdown("---")
        st.markdown("### 📊 Data Sources")
        st.markdown("- **US Data**: FRED Economic Data")
        st.markdown("- **VN Data**: TCBS (bars-long-term)")
        st.markdown("- **Global**: Yahoo Finance")

    # --- Load data once ---
    with st.spinner("🔄 Loading latest economic data..."):
        us_data, us_series = get_enhanced_us_data(data_period)
        vn_data = get_enhanced_vn_data()
        fed_data = get_fed_probability()
        global_data = get_global_market_data()

    # --- Build charts once ---
    charts = create_enhanced_charts(us_series, vn_data)

    # --- Route pages ---
    if selected == "Overview":
        show_overview_page(us_data, vn_data, fed_data, global_data)

    elif selected == "US Economy":
        show_us_economy_page(us_data, us_series, fed_data)
        # render the US chart here because pages.py says “charts are rendered by caller”
        if charts.get("us_indicators"):
            st.plotly_chart(charts["us_indicators"], use_container_width=True)

    elif selected == "Vietnam Market":
        show_vietnam_market_page(vn_data, charts, show_technical)

    elif selected == "Global Markets":
        show_global_markets_page(global_data)

    elif selected == "Investment Analysis":
        if show_recommendations:
            show_investment_analysis_page(us_data, vn_data, fed_data, risk_tolerance)

    elif selected == "Settings":
        # pass the cached function so .clear() works from the Settings UI
        show_settings_page(get_fred_client)


if __name__ == "__main__":
    main()
