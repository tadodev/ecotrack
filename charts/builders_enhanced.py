# charts/builders_enhanced.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Optional

from data.vn_enhanced import get_index_history


def create_comprehensive_charts(us_series, vn_market_data, vn_economic_data, global_context):
    """
    Create comprehensive charts incorporating all enhanced data sources.
    """
    charts = {}

    # Enhanced US indicators chart
    charts['us_indicators'] = create_us_indicators_chart(us_series)

    # Vietnam indices comparison
    charts['vn_indices_comparison'] = create_vietnam_indices_comparison(vn_market_data)

    # VN30 analysis charts
    charts['vn30_analysis'] = create_vn30_analysis_charts(vn_market_data)

    # Vietnam economic dashboard
    charts['vn_economic_dashboard'] = create_vietnam_economic_dashboard(vn_economic_data)

    # Market breadth analysis
    charts['market_breadth'] = create_market_breadth_chart(vn_market_data)

    # Sector performance heatmap
    charts['sector_heatmap'] = create_sector_heatmap(vn_market_data)

    # Global context chart
    charts['global_context'] = create_global_context_chart(global_context, us_series)

    # Fed vs Vietnam correlation
    charts['fed_vietnam_correlation'] = create_fed_vietnam_correlation_chart(us_series, vn_market_data)

    return charts


def create_us_indicators_chart(us_series):
    """Enhanced US economic indicators with additional context."""
    if not us_series:
        return None

    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Inflation vs Fed Target', 'Fed Funds Rate Path',
            'Unemployment Rate', 'GDP Growth (YoY %)',
            'Retail Sales Growth', 'Industrial Production'
        ),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    # Inflation with target band
    if 'inflation' in us_series and len(us_series['inflation']) > 12:
        yoy = us_series['inflation'].pct_change(12) * 100
        fig.add_trace(go.Scatter(x=yoy.index, y=yoy.values, name='Inflation',
                                 line=dict(color='red', width=2)), row=1, col=1)
        # Add Fed target band
        fig.add_hline(y=2, line_dash="dash", line_color="green",
                      annotation_text="Fed Target", row=1, col=1)
        fig.add_hrect(y0=1.5, y1=2.5, line_width=0, fillcolor="green",
                      opacity=0.1, row=1, col=1)

    # Fed Funds Rate
    if 'fed_rate' in us_series:
        fed = us_series['fed_rate']
        fig.add_trace(go.Scatter(x=fed.index, y=fed.values, name='Fed Rate',
                                 line=dict(color='blue', width=2)), row=1, col=2)

    # Unemployment
    if 'unemployment' in us_series:
        un = us_series['unemployment']
        fig.add_trace(go.Scatter(x=un.index, y=un.values, name='Unemployment',
                                 line=dict(color='orange', width=2)), row=2, col=1)
        # Add natural rate reference
        fig.add_hline(y=4, line_dash="dot", line_color="gray",
                      annotation_text="Natural Rate ~4%", row=2, col=1)

    # GDP Growth
    if 'gdp' in us_series and len(us_series['gdp']) > 5:
        gdp_yoy = us_series['gdp'].pct_change(4) * 100
        fig.add_trace(go.Scatter(x=gdp_yoy.index, y=gdp_yoy.values, name='GDP YoY %',
                                 line=dict(color='green', width=2)), row=2, col=2)
        fig.add_hline(y=0, line_dash="dot", line_color="black", row=2, col=2)

    # Retail Sales
    if 'retail_sales' in us_series and len(us_series['retail_sales']) > 12:
        retail_yoy = us_series['retail_sales'].pct_change(12) * 100
        fig.add_trace(go.Scatter(x=retail_yoy.index, y=retail_yoy.values, name='Retail Sales YoY',
                                 line=dict(color='purple', width=2)), row=3, col=1)

    # Industrial Production
    if 'industrial_production' in us_series and len(us_series['industrial_production']) > 12:
        ip_yoy = us_series['industrial_production'].pct_change(12) * 100
        fig.add_trace(go.Scatter(x=ip_yoy.index, y=ip_yoy.values, name='Industrial Production YoY',
                                 line=dict(color='brown', width=2)), row=3, col=2)
        fig.add_hline(y=0, line_dash="dot", line_color="black", row=3, col=2)

    fig.update_layout(
        height=800,
        title_text='US Economic Indicators Dashboard - Enhanced',
        showlegend=False
    )

    return fig


def create_vietnam_indices_comparison(vn_market_data):
    """Compare performance of all Vietnam indices."""
    if 'indices' not in vn_market_data:
        return None

    indices = vn_market_data['indices']

    # Create comparison chart
    names = []
    prices = []
    changes = []

    for code, data in indices.items():
        names.append(data['name'])
        prices.append(data['price'])
        changes.append(data['change_pct'])

    if not names:
        return None

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Index Levels', 'Daily Performance %'),
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )

    # Index levels (normalized to show relative performance)
    fig.add_trace(go.Bar(x=names, y=prices, name='Index Level',
                         marker_color='lightblue'), row=1, col=1)

    # Daily changes with color coding
    colors = ['green' if x > 0 else 'red' if x < 0 else 'gray' for x in changes]
    fig.add_trace(go.Bar(x=names, y=changes, name='Daily Change %',
                         marker_color=colors), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="black", row=2, col=1)

    fig.update_layout(
        height=600,
        title_text='Vietnam Indices Comparison',
        showlegend=False
    )

    return fig


def create_vn30_analysis_charts(vn_market_data):
    """Create comprehensive VN30 analysis charts."""
    if 'vn30_analysis' not in vn_market_data or not vn_market_data['vn30_analysis']:
        return None

    vn30_data = vn_market_data['vn30_analysis']

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('VN30 Top Contributors', 'VN30 Top Detractors',
                        'Advance/Decline Analysis', 'Volume Analysis'),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "pie"}, {"type": "bar"}]]
    )

    # Top Contributors
    if 'top_contributors' in vn30_data:
        contributors = vn30_data['top_contributors'][:5]
        symbols = [c['symbol'] for c in contributors]
        contributions = [c['contribution'] for c in contributors]

        fig.add_trace(go.Bar(x=symbols, y=contributions, name='Contributors',
                             marker_color='green'), row=1, col=1)

    # Top Detractors
    if 'top_detractors' in vn30_data:
        detractors = vn30_data['top_detractors'][:5]
        symbols = [d['symbol'] for d in detractors]
        contributions = [d['contribution'] for d in detractors]

        fig.add_trace(go.Bar(x=symbols, y=contributions, name='Detractors',
                             marker_color='red'), row=1, col=2)

    # Advance/Decline Pie
    advancing = vn30_data.get('advancing', 0)
    declining = vn30_data.get('declining', 0)
    unchanged = vn30_data.get('unchanged', 0)

    fig.add_trace(go.Pie(labels=['Advancing', 'Declining', 'Unchanged'],
                         values=[advancing, declining, unchanged],
                         marker_colors=['green', 'red', 'gray']), row=2, col=1)

    # Volume analysis would go here if we had sector volume data
    if 'constituents' in vn30_data:
        constituents = vn30_data['constituents'][:10]  # Top 10 by volume
        symbols = [c['symbol'] for c in constituents]
        volumes = [c['volume'] for c in constituents]

        fig.add_trace(go.Bar(x=symbols, y=volumes, name='Volume',
                             marker_color='blue'), row=2, col=2)

    fig.update_layout(
        height=700,
        title_text='VN30 Comprehensive Analysis',
        showlegend=False
    )

    return fig


def create_vietnam_economic_dashboard(vn_economic_data):
    """Create Vietnam economic indicators dashboard."""
    if not vn_economic_data:
        return None

    # Select key indicators for visualization
    key_indicators = [
        'gdp_growth_yoy', 'inflation_rate', 'manufacturing_pmi',
        'policy_rate', 'balance_of_trade', 'fx_reserves'
    ]

    available_indicators = {k: v for k, v in vn_economic_data.items()
                            if k in key_indicators and v.get('value') is not None}

    if not available_indicators:
        return None

    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=[v['name'] for v in available_indicators.values()][:6],
        specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
               [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]]
    )

    positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)]

    for i, (key, data) in enumerate(available_indicators.items()):
        if i >= 6:  # Only show first 6 indicators
            break

        row, col = positions[i]
        current_value = data['value']
        previous_value = data.get('previous')

        # Determine color based on indicator type and change
        if key in ['gdp_growth_yoy', 'manufacturing_pmi', 'fx_reserves']:
            # Higher is better
            color = "green" if current_value > (previous_value or 0) else "red"
        elif key in ['inflation_rate', 'policy_rate']:
            # Moderate levels are better
            if key == 'inflation_rate':
                color = "green" if 2 <= current_value <= 4 else "red"
            else:
                color = "blue"  # Neutral for policy rate
        else:
            color = "blue"  # Neutral

        delta_dict = {}
        if previous_value is not None:
            delta_dict = {
                "reference": previous_value,
                "position": "bottom",
                "relative": False
            }

        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=current_value,
            title={"text": f"{data['name']}<br><span style='font-size:0.8em;color:gray'>{data.get('unit', '')}</span>"},
            delta=delta_dict,
            gauge={
                "axis": {"range": [None, None]},
                "bar": {"color": color},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "gray"
            }
        ), row=row, col=col)

    fig.update_layout(
        height=600,
        title_text='Vietnam Economic Indicators Dashboard',
        font={"size": 12}
    )

    return fig


def create_market_breadth_chart(vn_market_data):
    """Create market breadth analysis chart."""
    if 'market_breadth' not in vn_market_data:
        return None

    breadth = vn_market_data['market_breadth']

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Advance/Decline Ratio', 'Volume Flow'),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )

    # Advance/Decline
    categories = ['Advancing', 'Declining', 'Unchanged']
    values = [breadth.get('advancing', 0), breadth.get('declining', 0), breadth.get('unchanged', 0)]
    colors = ['green', 'red', 'gray']

    fig.add_trace(go.Bar(x=categories, y=values, marker_color=colors, name='Stocks'), row=1, col=1)

    # Volume Flow
    up_volume = breadth.get('up_volume', 0)
    down_volume = breadth.get('down_volume', 0)

    fig.add_trace(go.Bar(x=['Up Volume', 'Down Volume'],
                         y=[up_volume, down_volume],
                         marker_color=['green', 'red'],
                         name='Volume'), row=1, col=2)

    fig.update_layout(
        height=400,
        title_text='Market Breadth Analysis',
        showlegend=False
    )

    return fig


def create_sector_heatmap(vn_market_data):
    """Create sector performance heatmap."""
    if 'sectors' not in vn_market_data:
        return None

    sectors = vn_market_data['sectors']

    # Prepare data for heatmap
    sector_names = list(sectors.keys())
    metrics = ['avg_return_1d', 'avg_return_1w', 'avg_return_1m']
    metric_labels = ['1 Day %', '1 Week %', '1 Month %']

    heatmap_data = []
    for metric in metrics:
        row = []
        for sector in sector_names:
            value = sectors[sector].get(metric, 0)
            row.append(value)
        heatmap_data.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=sector_names,
        y=metric_labels,
        colorscale='RdYlGn',
        zmid=0,
        colorbar=dict(title="Return %")
    ))

    fig.update_layout(
        title='Sector Performance Heatmap',
        height=300,
        xaxis_title="Sectors",
        yaxis_title="Time Period"
    )

    return fig


def create_global_context_chart(global_context, us_series):
    """Create chart showing global economic context affecting Vietnam."""
    if not global_context and not us_series:
        return None

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('USD/VND Exchange Rate', 'Oil Price Impact',
                        'US Dollar Index', 'Gold Price'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    # This would be enhanced with actual time series data
    # For now, showing current levels

    row, col = 1, 1
    for key, data in global_context.items():
        if row > 2:
            break

        name = data.get('name', key)
        value = data.get('value', 0)
        change = data.get('change', 0)

        color = 'green' if change > 0 else 'red' if change < 0 else 'blue'

        fig.add_trace(go.Bar(x=[name], y=[value], marker_color=color,
                             name=f"{change:+.2f}%" if change else "N/A"),
                      row=row, col=col)

        col += 1
        if col > 2:
            col = 1
            row += 1

    fig.update_layout(
        height=500,
        title_text='Global Context - Key Indicators Affecting Vietnam',
        showlegend=False
    )

    return fig


def create_fed_vietnam_correlation_chart(us_series, vn_market_data):
    """Create chart showing Fed policy vs Vietnam market correlation."""
    if not us_series or 'indices' not in vn_market_data:
        return None

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Fed Funds Rate Path', 'Vietnam Market Response'),
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )

    # Fed Funds Rate
    if 'fed_rate' in us_series:
        fed_rate = us_series['fed_rate']
        fig.add_trace(go.Scatter(x=fed_rate.index, y=fed_rate.values,
                                 name='Fed Rate', line=dict(color='blue')), row=1, col=1)

    # This would ideally show VN-Index time series correlated with Fed actions
    # For now, showing current market conditions
    vnindex_data = vn_market_data['indices'].get('vnindex', {})
    if vnindex_data:
        # Create a simple indicator of current market stress
        rsi = vnindex_data.get('rsi', 50)
        change = vnindex_data.get('change_pct', 0)

        fig.add_trace(go.Bar(x=['Market Stress Level'],
                             y=[100 - rsi if rsi else 50],
                             marker_color='red' if change < 0 else 'green'), row=2, col=1)

    fig.update_layout(
        height=500,
        title_text='Fed Policy vs Vietnam Market Correlation Analysis'
    )

    return fig


def create_economic_score_gauge(economic_score: float, rating: str) -> go.Figure:
    """Create a gauge chart for the economic health score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=economic_score,
        title={"text": f"Vietnam Economic Health Score<br><span style='font-size:0.8em'>{rating}</span>"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "lightcoral"},
                {'range': [30, 45], 'color': "lightyellow"},
                {'range': [45, 60], 'color': "lightblue"},
                {'range': [60, 75], 'color': "lightgreen"},
                {'range': [75, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))

    fig.update_layout(height=300)
    return fig