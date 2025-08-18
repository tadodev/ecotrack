# charts/builders.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data.vn import get_vnindex_history


def vnindex_candlestick(days: int = 90):
    """Standalone VN-Index candlestick built from TCBS data."""
    hist = get_vnindex_history(days=days)
    if hist is None or hist.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist["open"], high=hist["high"], low=hist["low"], close=hist["close"],
        name="VN-Index"
    ))
    fig.add_trace(go.Scatter(x=hist.index, y=hist["close"].rolling(20).mean(),
                             name="SMA 20", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=hist.index, y=hist["close"].rolling(50).mean(),
                             name="SMA 50", line=dict(width=1)))
    fig.update_layout(
        title="VN-Index Technical (TCBS)",
        yaxis_title="Price",
        xaxis_title="Date",
        height=500
    )
    return fig


def create_enhanced_charts(us_series, vn_data):
    """
    Returns:
      charts['us_indicators']   -> US macro subplots
      charts['vn_technical']    -> VN-Index candlestick (TCBS)
      charts['vn_sectors']      -> Sector avg returns
      charts['vn_top_leaders']  -> Top 10 stock leaders (bar)
    """
    charts = {}

    # --- US indicators ---
    if us_series:
        fig_us = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Inflation (YoY %)', 'Fed Funds Rate (%)',
                            'Unemployment (%)', 'GDP YoY %'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        if 'inflation' in us_series and len(us_series['inflation']) > 12:
            yoy = us_series['inflation'].pct_change(12) * 100
            fig_us.add_trace(go.Scatter(x=yoy.index, y=yoy.values, name='Inflation'), row=1, col=1)

        if 'fed_rate' in us_series:
            fed = us_series['fed_rate']
            fig_us.add_trace(go.Scatter(x=fed.index, y=fed.values, name='Fed Rate'), row=1, col=2)

        if 'unemployment' in us_series:
            un = us_series['unemployment']
            fig_us.add_trace(go.Scatter(x=un.index, y=un.values, name='Unemployment'), row=2, col=1)

        if 'gdp' in us_series and len(us_series['gdp']) > 5:
            gdp_yoy = us_series['gdp'].pct_change(4) * 100
            fig_us.add_trace(go.Scatter(x=gdp_yoy.index, y=gdp_yoy.values, name='GDP YoY %'), row=2, col=2)

        fig_us.update_layout(height=600, title_text='US Economic Indicators Dashboard')
        charts['us_indicators'] = fig_us

    # --- VN technical (TCBS) ---
    if isinstance(vn_data, dict) and 'vnindex' in vn_data and 'error' not in vn_data:
        hist = get_vnindex_history(days=120)
        if hist is not None and not hist.empty:
            fig_vn = go.Figure()
            if {'open', 'high', 'low', 'close'}.issubset(hist.columns):
                fig_vn.add_trace(go.Candlestick(
                    x=hist.index, open=hist['open'], high=hist['high'],
                    low=hist['low'], close=hist['close'], name="VN-Index"
                ))
            else:
                fig_vn.add_trace(go.Scatter(x=hist.index, y=hist['close'], name='VN-Index'))

            sma20 = hist['close'].rolling(20).mean()
            sma50 = hist['close'].rolling(50).mean()
            fig_vn.add_trace(go.Scatter(x=hist.index, y=sma20, name='SMA 20', line=dict(width=1)))
            fig_vn.add_trace(go.Scatter(x=hist.index, y=sma50, name='SMA 50', line=dict(width=1)))

            vninfo = vn_data.get('vnindex', {})
            if 'support' in vninfo:
                fig_vn.add_hline(y=vninfo['support'], line_dash='dash', annotation_text='Support')
            if 'resistance' in vninfo:
                fig_vn.add_hline(y=vninfo['resistance'], line_dash='dash', annotation_text='Resistance')

            fig_vn.update_layout(title='VN-Index Technical Analysis',
                                 yaxis_title='Price', xaxis_title='Date', height=500)
            charts['vn_technical'] = fig_vn

    # --- VN sectors ---
    if isinstance(vn_data, dict) and vn_data.get('sectors'):
        names = list(vn_data['sectors'].keys())
        rets = [vn_data['sectors'][s]['avg_return'] for s in names]
        fig_sec = px.bar(
            x=names, y=rets,
            title='Vietnam Sector Performance (Daily %)',
            color=rets, color_continuous_scale='RdYlGn'
        )
        fig_sec.update_layout(height=400, xaxis_title="Sector", yaxis_title="Avg Return (%)")
        charts['vn_sectors'] = fig_sec

    # --- TOP 10 leaders (bar) ---
    if isinstance(vn_data, dict) and vn_data.get('top_stocks'):
        top10 = vn_data['top_stocks'][:10]
        df = pd.DataFrame(top10)
        if not df.empty:
            # Horizontal bar: leaders at top
            df = df.sort_values("change_pct", ascending=True)  # so largest shows at top in horizontal chart
            fig_top = px.bar(
                df, x="change_pct", y="symbol", orientation="h",
                title="Top 10 Stock Leaders (Daily %)",
                color="change_pct", color_continuous_scale="RdYlGn"
            )
            fig_top.update_layout(height=450, xaxis_title="Change (%)", yaxis_title="Stock")
            charts['vn_top_leaders'] = fig_top

    return charts
