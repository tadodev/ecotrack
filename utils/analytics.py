# utils/analytics.py - Advanced analytics and correlation engine
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
import scipy
logger = logging.getLogger(__name__)


class EconomicAnalyzer:
    """Advanced economic analysis and correlation engine."""

    def __init__(self):
        self.correlation_cache = {}
        self.trend_cache = {}

    def calculate_economic_momentum(self, economic_data: Dict[str, Dict]) -> Dict[str, float]:
        """
        Calculate momentum scores for various economic indicators.
        Returns scores from -100 to +100.
        """
        momentum_scores = {}

        for indicator, data in economic_data.items():
            if not isinstance(data, dict) or 'value' not in data:
                continue

            current_value = data.get('value')
            previous_value = data.get('previous')
            change = data.get('change')

            if current_value is None:
                continue

            # Base momentum calculation
            momentum = 0

            if change is not None and abs(change) > 0.1:
                # Directional momentum based on change
                momentum += np.tanh(change / 10) * 50  # Normalized to -50 to +50

            # Add level-based momentum for key indicators
            if indicator == 'gdp_growth_yoy' and current_value is not None:
                if current_value > 6.5:
                    momentum += 30
                elif current_value < 5.0:
                    momentum -= 20

            elif indicator == 'manufacturing_pmi' and current_value is not None:
                momentum += (current_value - 50) * 2  # PMI above/below 50

            elif indicator == 'inflation_rate' and current_value is not None:
                # Optimal inflation around 2-4%
                if 2 <= current_value <= 4:
                    momentum += 20
                elif current_value > 6 or current_value < 1:
                    momentum -= 30

            momentum_scores[indicator] = np.clip(momentum, -100, 100)

        return momentum_scores

    def detect_regime_changes(self, time_series_data: Dict[str, pd.Series]) -> Dict[str, Dict]:
        """
        Detect potential regime changes in economic time series.
        """
        regime_changes = {}

        for indicator, series in time_series_data.items():
            if series is None or len(series) < 30:
                continue

            # Calculate rolling statistics
            window = min(20, len(series) // 3)
            rolling_mean = series.rolling(window).mean()
            rolling_std = series.rolling(window).std()

            # Detect significant shifts
            current_mean = rolling_mean.iloc[-5:].mean() if len(rolling_mean) >= 5 else rolling_mean.iloc[-1]
            historical_mean = rolling_mean.iloc[:-10].mean() if len(rolling_mean) >= 15 else rolling_mean.iloc[0]

            # Calculate regime change probability
            if abs(current_mean - historical_mean) > rolling_std.iloc[-1] * 1.5:
                regime_probability = min(abs(current_mean - historical_mean) / (rolling_std.iloc[-1] * 2), 1.0)
                direction = "upward" if current_mean > historical_mean else "downward"

                regime_changes[indicator] = {
                    'probability': regime_probability,
                    'direction': direction,
                    'current_level': current_mean,
                    'historical_level': historical_mean,
                    'significance': 'high' if regime_probability > 0.7 else 'medium' if regime_probability > 0.4 else 'low'
                }

        return regime_changes

    def calculate_sector_rotation_signals(self, sector_data: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Analyze sector rotation patterns and generate signals.
        """
        if not sector_data:
            return {}

        # Calculate relative strength
        sector_performance = {}
        for sector, data in sector_data.items():
            perf_1d = data.get('avg_return_1d', 0)
            perf_1w = data.get('avg_return_1w', 0)
            perf_1m = data.get('avg_return_1m', 0)

            # Weighted performance score
            weighted_score = (perf_1d * 0.2 + perf_1w * 0.3 + perf_1m * 0.5)
            sector_performance[sector] = weighted_score

        # Rank sectors
        sorted_sectors = sorted(sector_performance.items(), key=lambda x: x[1], reverse=True)

        # Identify rotation patterns
        top_performers = [s[0] for s in sorted_sectors[:2]]
        bottom_performers = [s[0] for s in sorted_sectors[-2:]]

        # Generate rotation signals
        rotation_signals = {
            'leading_sectors': top_performers,
            'lagging_sectors': bottom_performers,
            'rotation_strength': abs(sorted_sectors[0][1] - sorted_sectors[-1][1]),
            'market_breadth': len([s for s in sector_performance.values() if s > 0]) / len(sector_performance),
            'recommendation': self._generate_rotation_recommendation(sorted_sectors)
        }

        return rotation_signals

    def _generate_rotation_recommendation(self, sorted_sectors: List[Tuple[str, float]]) -> str:
        """Generate sector rotation recommendation based on performance."""
        if not sorted_sectors:
            return "Insufficient data for recommendation"

        top_sector, top_perf = sorted_sectors[0]
        bottom_sector, bottom_perf = sorted_sectors[-1]

        performance_spread = top_perf - bottom_perf

        if performance_spread > 5:
            return f"Strong rotation into {top_sector} - consider overweight"
        elif performance_spread > 2:
            return f"Moderate rotation favoring {top_sector}"
        elif performance_spread < -2:
            return "Defensive positioning recommended - broad-based weakness"
        else:
            return "Balanced allocation - no clear rotation pattern"

    def calculate_market_stress_index(self, market_data: Dict) -> Dict[str, Any]:
        """
        Calculate a composite market stress index for Vietnam markets.
        """
        stress_components = {}
        total_stress = 0
        component_count = 0

        # Volatility stress
        if 'indices' in market_data:
            for index_name, index_data in market_data['indices'].items():
                volatility = index_data.get('volatility_20d', 0)
                if volatility > 0:
                    # Normalize volatility stress (0-30 scale)
                    vol_stress = min(volatility * 1.5, 30)
                    stress_components[f'{index_name}_volatility'] = vol_stress
                    total_stress += vol_stress
                    component_count += 1

        # Technical stress
        if 'indices' in market_data and 'vnindex' in market_data['indices']:
            vnindex = market_data['indices']['vnindex']
            rsi = vnindex.get('rsi', 50)

            # RSI-based stress (extreme RSI = higher stress)
            rsi_stress = max(abs(rsi - 50) - 20, 0) * 0.5  # 0-15 scale
            stress_components['rsi_extremes'] = rsi_stress
            total_stress += rsi_stress
            component_count += 1

        # Breadth stress
        if 'market_breadth' in market_data:
            breadth = market_data['market_breadth']
            advancing = breadth.get('advancing', 0)
            declining = breadth.get('declining', 0)
            total = advancing + declining

            if total > 0:
                ad_ratio = advancing / total
                # Low breadth = high stress
                breadth_stress = (0.5 - ad_ratio) * 40 if ad_ratio < 0.5 else 0  # 0-20 scale
                stress_components['market_breadth'] = breadth_stress
                total_stress += breadth_stress
                component_count += 1

        # Sector dispersion stress
        if 'sectors' in market_data:
            sector_returns = [data.get('avg_return_1d', 0) for data in market_data['sectors'].values()]
            if sector_returns:
                sector_dispersion = np.std(sector_returns)
                dispersion_stress = min(sector_dispersion * 2, 15)  # 0-15 scale
                stress_components['sector_dispersion'] = dispersion_stress
                total_stress += dispersion_stress
                component_count += 1

        # Calculate composite stress index (0-100 scale)
        composite_stress = (total_stress / component_count) * (100 / 30) if component_count > 0 else 50
        composite_stress = np.clip(composite_stress, 0, 100)

        # Determine stress level
        if composite_stress > 75:
            stress_level = "Extreme"
        elif composite_stress > 60:
            stress_level = "High"
        elif composite_stress > 40:
            stress_level = "Moderate"
        elif composite_stress > 25:
            stress_level = "Low"
        else:
            stress_level = "Very Low"

        return {
            'composite_stress_index': composite_stress,
            'stress_level': stress_level,
            'stress_components': stress_components,
            'interpretation': self._interpret_stress_level(stress_level, composite_stress)
        }

    def _interpret_stress_level(self, stress_level: str, stress_value: float) -> str:
        """Provide interpretation of market stress levels."""
        interpretations = {
            "Extreme": "Market experiencing severe stress. Consider defensive positioning and risk reduction.",
            "High": "Elevated market stress. Monitor positions closely and avoid new risk-taking.",
            "Moderate": "Some market stress present. Selective approach recommended.",
            "Low": "Normal market conditions. Standard risk management applies.",
            "Very Low": "Low stress environment. May consider increasing risk exposure."
        }
        return interpretations.get(stress_level, "Unable to interpret stress level")

    def detect_divergences(self, market_data: Dict, economic_data: Dict) -> List[Dict]:
        """
        Detect divergences between market performance and economic indicators.
        """
        divergences = []

        # Market performance proxy
        market_performance = 0
        if 'indices' in market_data and 'vnindex' in market_data['indices']:
            market_performance = market_data['indices']['vnindex'].get('change_pct', 0)

        # Economic performance proxy
        economic_momentum = self.calculate_economic_momentum(economic_data)
        avg_economic_momentum = np.mean(list(economic_momentum.values())) if economic_momentum else 0

        # Detect market-economic divergence
        if market_performance > 2 and avg_economic_momentum < -20:
            divergences.append({
                'type': 'bearish_divergence',
                'description': 'Market rising despite weak economic indicators',
                'severity': 'medium',
                'recommendation': 'Monitor for potential correction'
            })
        elif market_performance < -2 and avg_economic_momentum > 20:
            divergences.append({
                'type': 'bullish_divergence',
                'description': 'Market declining despite strong economic indicators',
                'severity': 'medium',
                'recommendation': 'Potential buying opportunity'
            })

        # Sector-market divergences
        if 'sectors' in market_data:
            sector_performance = [data.get('avg_return_1d', 0) for data in market_data['sectors'].values()]
            avg_sector_performance = np.mean(sector_performance) if sector_performance else 0

            if abs(market_performance - avg_sector_performance) > 3:
                divergences.append({
                    'type': 'sector_divergence',
                    'description': f'Index diverging from average sector performance by {abs(market_performance - avg_sector_performance):.1f}%',
                    'severity': 'low',
                    'recommendation': 'Check for index concentration effects'
                })

        return divergences

    def generate_tactical_signals(self, us_data: Dict, vn_market: Dict, vn_economic: Dict, global_context: Dict) -> \
    Dict[str, Any]:
        """
        Generate comprehensive tactical trading/investment signals.
        """
        signals = {
            'overall_signal': 'NEUTRAL',
            'confidence': 0.5,
            'time_horizon': 'medium_term',
            'key_drivers': [],
            'risk_factors': [],
            'tactical_recommendations': []
        }

        signal_score = 0
        signal_count = 0

        # Fed policy signal
        if 'fed_rate' in us_data:
            fed_rate = us_data['fed_rate']['value']
            if fed_rate > 5:
                signal_score -= 2
                signals['risk_factors'].append('High Fed rate pressures EM')
            elif fed_rate < 2:
                signal_score += 2
                signals['key_drivers'].append('Accommodative Fed policy')
            signal_count += 1

        # Vietnam economic signal
        economic_momentum = self.calculate_economic_momentum(vn_economic)
        if economic_momentum:
            avg_momentum = np.mean(list(economic_momentum.values()))
            if avg_momentum > 20:
                signal_score += 1
                signals['key_drivers'].append('Strong Vietnam economic momentum')
            elif avg_momentum < -20:
                signal_score -= 1
                signals['risk_factors'].append('Weak Vietnam economic momentum')
            signal_count += 1

        # Market technical signal
        if 'indices' in vn_market and 'vnindex' in vn_market['indices']:
            vnindex = vn_market['indices']['vnindex']
            rsi = vnindex.get('rsi', 50)

            if rsi < 35:
                signal_score += 1
                signals['key_drivers'].append('Oversold market conditions')
            elif rsi > 65:
                signal_score -= 1
                signals['risk_factors'].append('Overbought market conditions')
            signal_count += 1

        # Currency signal
        if 'usd_vnd' in global_context:
            vnd_change = global_context['usd_vnd'].get('change', 0)
            if vnd_change < -2:  # VND strengthening
                signal_score += 0.5
                signals['key_drivers'].append('VND strength supports foreign investment')
            elif vnd_change > 3:  # VND weakening significantly
                signal_score -= 0.5
                signals['risk_factors'].append('VND weakness may pressure foreign flows')
            signal_count += 1

        # Generate overall signal
        if signal_count > 0:
            avg_signal = signal_score / signal_count
            if avg_signal > 1:
                signals['overall_signal'] = 'BULLISH'
                signals['confidence'] = min(avg_signal / 2, 1.0)
            elif avg_signal < -1:
                signals['overall_signal'] = 'BEARISH'
                signals['confidence'] = min(abs(avg_signal) / 2, 1.0)
            else:
                signals['overall_signal'] = 'NEUTRAL'
                signals['confidence'] = 0.5

        # Generate tactical recommendations
        if signals['overall_signal'] == 'BULLISH':
            signals['tactical_recommendations'] = [
                'Consider increasing Vietnam equity allocation',
                'Focus on cyclical and growth sectors',
                'Monitor for entry opportunities on pullbacks'
            ]
        elif signals['overall_signal'] == 'BEARISH':
            signals['tactical_recommendations'] = [
                'Reduce Vietnam equity exposure',
                'Focus on defensive sectors',
                'Consider hedging currency risk'
            ]
        else:
            signals['tactical_recommendations'] = [
                'Maintain neutral allocation',
                'Focus on stock selection over timing',
                'Monitor key drivers for directional signals'
            ]

        return signals


class PortfolioOptimizer:
    """Portfolio optimization and risk management utilities."""

    def __init__(self):
        self.risk_models = {}

    def calculate_optimal_weights(self, expected_returns: np.ndarray, cov_matrix: np.ndarray,
                                  risk_tolerance: float = 0.5) -> np.ndarray:
        """
        Calculate optimal portfolio weights using mean-variance optimization.
        """
        try:
            # Simple mean-variance optimization
            n_assets = len(expected_returns)

            # Risk aversion parameter (higher = more risk averse)
            risk_aversion = 2 / risk_tolerance if risk_tolerance > 0 else 4

            # Calculate optimal weights: w = (1/λ) * Σ^(-1) * μ
            inv_cov = np.linalg.pinv(cov_matrix)  # Use pseudo-inverse for stability
            optimal_weights = np.dot(inv_cov, expected_returns) / risk_aversion

            # Normalize weights to sum to 1
            optimal_weights = optimal_weights / np.sum(optimal_weights)

            # Apply constraints (no short selling, max position limits)
            optimal_weights = np.clip(optimal_weights, 0, 0.4)  # Max 40% in any asset
            optimal_weights = optimal_weights / np.sum(optimal_weights)  # Renormalize

            return optimal_weights

        except Exception as e:
            logger.error(f"Portfolio optimization error: {e}")
            # Return equal weights as fallback
            return np.ones(len(expected_returns)) / len(expected_returns)

    def calculate_risk_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate comprehensive risk metrics for a return series."""
        if returns.empty or len(returns) < 2:
            return {}

        metrics = {}

        # Basic risk metrics
        metrics['volatility_annualized'] = returns.std() * np.sqrt(252)
        metrics['downside_deviation'] = returns[returns < 0].std() * np.sqrt(252)
        metrics['max_drawdown'] = self._calculate_max_drawdown(returns)

        # VaR metrics
        metrics['var_95'] = np.percentile(returns, 5)
        metrics['var_99'] = np.percentile(returns, 1)
        metrics['cvar_95'] = returns[returns <= metrics['var_95']].mean()

        # Higher moment risks
        metrics['skewness'] = returns.skew()
        metrics['kurtosis'] = returns.kurtosis()

        # Risk-adjusted returns
        if metrics['volatility_annualized'] > 0:
            metrics['sharpe_ratio'] = (returns.mean() * 252) / metrics['volatility_annualized']
        else:
            metrics['sharpe_ratio'] = 0

        return metrics

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown from return series."""
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        return drawdown.min()


# Utility functions
def calculate_correlation_matrix(data_dict: Dict[str, pd.Series]) -> pd.DataFrame:
    """Calculate correlation matrix from multiple time series."""
    df = pd.DataFrame(data_dict)
    return df.corr()


def identify_outliers(series: pd.Series, method: str = 'iqr') -> pd.Series:
    """Identify outliers in a time series."""
    if method == 'iqr':
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return (series < lower_bound) | (series > upper_bound)
    elif method == 'zscore':
        z_scores = np.abs((series - series.mean()) / series.std())
        return z_scores > 3
    else:
        return pd.Series([False] * len(series), index=series.index)


def smooth_series(series: pd.Series, method: str = 'ewm', window: int = 10) -> pd.Series:
    """Smooth a time series using various methods."""
    if method == 'ewm':
        return series.ewm(span=window).mean()
    elif method == 'rolling':
        return series.rolling(window).mean()
    elif method == 'savgol':
        from scipy.signal import savgol_filter
        return pd.Series(savgol_filter(series.values, window, 2), index=series.index)
    else:
        return series