# constants_enhanced.py - Enhanced constants and configuration
from typing import Dict, List, Tuple

# Enhanced Vietnam stock classification
VN_MAJOR_STOCKS = {
    'Banking': {
        'stocks': ['VCB', 'TCB', 'MBB', 'BID', 'CTG', 'VPB', 'ACB', 'TPB', 'STB', 'EIB'],
        'description': 'Commercial banks and financial institutions',
        'weight_in_vnindex': 0.35,  # Approximate weight
        'cyclical': True
    },
    'Real Estate': {
        'stocks': ['VHM', 'VIC', 'VRE', 'KDH', 'DXG', 'NVL', 'BCM', 'KBC', 'HDG'],
        'description': 'Property development and real estate services',
        'weight_in_vnindex': 0.20,
        'cyclical': True
    },
    'Technology': {
        'stocks': ['FPT', 'CMG', 'ELC', 'SVC', 'VGI', 'ITD', 'CSI'],
        'description': 'IT services, software, and technology solutions',
        'weight_in_vnindex': 0.08,
        'cyclical': False
    },
    'Consumer Goods': {
        'stocks': ['VNM', 'MSN', 'MWG', 'PNJ', 'SAB', 'MCH', 'DGW'],
        'description': 'Consumer products, retail, and beverages',
        'weight_in_vnindex': 0.12,
        'cyclical': False
    },
    'Energy & Utilities': {
        'stocks': ['GAS', 'PLX', 'PVD', 'POW', 'REE', 'NT2', 'PVS'],
        'description': 'Oil & gas, electricity, and utilities',
        'weight_in_vnindex': 0.10,
        'cyclical': True
    },
    'Manufacturing': {
        'stocks': ['HPG', 'HSG', 'NKG', 'VNS', 'POM', 'AAA', 'GMD'],
        'description': 'Steel, construction materials, and manufacturing',
        'weight_in_vnindex': 0.10,
        'cyclical': True
    },
    'Aviation & Transport': {
        'stocks': ['VJC', 'HVN', 'ACV', 'VTP'],
        'description': 'Airlines, airports, and transportation services',
        'weight_in_vnindex': 0.05,
        'cyclical': True
    }
}

# VN30 constituent stocks (official list as of 2024)
VN30_CONSTITUENTS = [
    # Banking (largest weight)
    'VCB', 'BID', 'CTG', 'TCB', 'MBB', 'VPB', 'ACB', 'TPB', 'STB',

    # Real Estate
    'VHM', 'VIC', 'VRE', 'KDH', 'NVL', 'DXG',

    # Consumer & Retail
    'VNM', 'MSN', 'MWG', 'PNJ', 'SAB',

    # Energy & Utilities
    'GAS', 'PLX', 'POW', 'REE',

    # Industrials
    'HPG', 'HSG',

    # Technology
    'FPT', 'CMG',

    # Services
    'VJC'  # Aviation
]

# Enhanced US economic indicators with more details
ECONOMIC_INDICATORS = {
    'inflation': {
        'fred': 'CPIAUCSL',
        'name': 'Consumer Price Index',
        'description': 'Measures changes in prices paid by consumers',
        'target_range': (2.0, 3.0),
        'update_frequency': 'monthly',
        'importance': 'high'
    },
    'pce': {
        'fred': 'PCEPI',
        'name': 'PCE Price Index',
        'description': 'Fed\'s preferred inflation measure',
        'target_range': (2.0, 2.5),
        'update_frequency': 'monthly',
        'importance': 'high'
    },
    'unemployment': {
        'fred': 'UNRATE',
        'name': 'Unemployment Rate',
        'description': 'Percentage of labor force unemployed',
        'target_range': (3.5, 5.0),
        'update_frequency': 'monthly',
        'importance': 'high'
    },
    'fed_rate': {
        'fred': 'FEDFUNDS',
        'name': 'Federal Funds Rate',
        'description': 'Overnight interbank lending rate',
        'target_range': None,  # Policy dependent
        'update_frequency': 'monthly',
        'importance': 'critical'
    },
    'gdp': {
        'fred': 'GDP',
        'name': 'Gross Domestic Product',
        'description': 'Total economic output',
        'target_range': (2.0, 4.0),  # YoY growth %
        'update_frequency': 'quarterly',
        'importance': 'high'
    },
    'housing': {
        'fred': 'HOUST',
        'name': 'Housing Starts',
        'description': 'New residential construction',
        'target_range': (1200, 1600),  # Thousands of units
        'update_frequency': 'monthly',
        'importance': 'medium'
    },
    'retail_sales': {
        'fred': 'RSXFS',
        'name': 'Retail Sales',
        'description': 'Consumer spending indicator',
        'target_range': None,
        'update_frequency': 'monthly',
        'importance': 'medium'
    },
    'industrial_production': {
        'fred': 'INDPRO',
        'name': 'Industrial Production',
        'description': 'Manufacturing and mining output',
        'target_range': None,
        'update_frequency': 'monthly',
        'importance': 'medium'
    },
    'treasury_10y': {
        'fred': 'GS10',
        'name': '10-Year Treasury Yield',
        'description': 'Long-term interest rate benchmark',
        'target_range': None,
        'update_frequency': 'daily',
        'importance': 'high'
    },
    'treasury_2y': {
        'fred': 'GS2',
        'name': '2-Year Treasury Yield',
        'description': 'Short-term interest rate benchmark',
        'target_range': None,
        'update_frequency': 'daily',
        'importance': 'medium'
    }
}

# Vietnam economic indicators (Trading Economics mapping)
VIETNAM_ECONOMIC_INDICATORS = {
    'core_indicators': {
        'gdp_growth_yoy': {
            'name': 'GDP Annual Growth Rate',
            'unit': '%',
            'target_range': (6.0, 7.5),
            'importance': 'critical',
            'frequency': 'quarterly'
        },
        'inflation_rate': {
            'name': 'Inflation Rate',
            'unit': '%',
            'target_range': (2.0, 4.0),
            'importance': 'high',
            'frequency': 'monthly'
        },
        'policy_rate': {
            'name': 'State Bank Policy Rate',
            'unit': '%',
            'target_range': None,
            'importance': 'high',
            'frequency': 'irregular'
        },
        'unemployment_rate': {
            'name': 'Unemployment Rate',
            'unit': '%',
            'target_range': (1.5, 3.0),
            'importance': 'medium',
            'frequency': 'quarterly'
        }
    },
    'business_indicators': {
        'manufacturing_pmi': {
            'name': 'Manufacturing PMI',
            'unit': 'Index',
            'target_range': (50, 60),
            'importance': 'high',
            'frequency': 'monthly'
        },
        'industrial_yoy': {
            'name': 'Industrial Production',
            'unit': '%',
            'target_range': (5.0, 10.0),
            'importance': 'medium',
            'frequency': 'monthly'
        },
        'retail_sales_yoy': {
            'name': 'Retail Sales Growth',
            'unit': '%',
            'target_range': (8.0, 12.0),
            'importance': 'medium',
            'frequency': 'monthly'
        }
    },
    'external_indicators': {
        'balance_of_trade': {
            'name': 'Trade Balance',
            'unit': 'USD Billion',
            'target_range': (1.0, 5.0),
            'importance': 'high',
            'frequency': 'monthly'
        },
        'current_account': {
            'name': 'Current Account Balance',
            'unit': 'USD Billion',
            'target_range': None,
            'importance': 'medium',
            'frequency': 'quarterly'
        },
        'fx_reserves': {
            'name': 'Foreign Exchange Reserves',
            'unit': 'USD Billion',
            'target_range': (80, 120),
            'importance': 'medium',
            'frequency': 'monthly'
        },
        'exports': {
            'name': 'Exports',
            'unit': 'USD Billion',
            'target_range': None,
            'importance': 'medium',
            'frequency': 'monthly'
        },
        'imports': {
            'name': 'Imports',
            'unit': 'USD Billion',
            'target_range': None,
            'importance': 'medium',
            'frequency': 'monthly'
        }
    }
}

# Global economic indicators affecting Vietnam
GLOBAL_INDICATORS = {
    'currencies': {
        'usd_vnd': {
            'symbol': 'USD/VND',
            'name': 'Vietnamese Dong Exchange Rate',
            'impact_on_vietnam': 'high',
            'direction': 'inverse'  # stronger VND = positive for Vietnam
        },
        'dxy': {
            'symbol': 'DXY',
            'name': 'US Dollar Index',
            'impact_on_vietnam': 'high',
            'direction': 'inverse'  # weaker USD = positive for EM
        }
    },
    'commodities': {
        'oil_brent': {
            'symbol': 'BRENT',
            'name': 'Brent Crude Oil',
            'impact_on_vietnam': 'medium',
            'direction': 'mixed'  # affects both costs and energy sector
        },
        'gold': {
            'symbol': 'GOLD',
            'name': 'Gold Price',
            'impact_on_vietnam': 'low',
            'direction': 'positive'  # safe haven demand
        },
        'copper': {
            'symbol': 'COPPER',
            'name': 'Copper Price',
            'impact_on_vietnam': 'medium',
            'direction': 'positive'  # industrial demand indicator
        }
    },
    'bonds': {
        'us_10y': {
            'symbol': 'US10Y',
            'name': 'US 10-Year Treasury Yield',
            'impact_on_vietnam': 'high',
            'direction': 'inverse'  # higher yields = EM outflows
        }
    }
}

# Investment analysis parameters
INVESTMENT_PARAMETERS = {
    'risk_levels': {
        'Conservative': {
            'max_single_position': 0.05,  # 5% max
            'max_sector_weight': 0.25,  # 25% max
            'max_vietnam_allocation': 0.15,  # 15% max
            'preferred_sectors': ['Banking', 'Consumer Goods', 'Utilities'],
            'avoid_sectors': ['Aviation', 'Speculative Tech']
        },
        'Moderate': {
            'max_single_position': 0.08,  # 8% max
            'max_sector_weight': 0.35,  # 35% max
            'max_vietnam_allocation': 0.25,  # 25% max
            'preferred_sectors': ['Banking', 'Technology', 'Consumer Goods', 'Manufacturing'],
            'avoid_sectors': ['High Beta Stocks']
        },
        'Aggressive': {
            'max_single_position': 0.12,  # 12% max
            'max_sector_weight': 0.45,  # 45% max
            'max_vietnam_allocation': 0.40,  # 40% max
            'preferred_sectors': ['Technology', 'Real Estate', 'Manufacturing', 'Aviation'],
            'avoid_sectors': []
        }
    },
    'rebalancing_triggers': {
        'sector_deviation': 0.05,  # 5% from target
        'position_deviation': 0.03,  # 3% from target
        'time_frequency': 90,  # days
        'volatility_trigger': 0.25  # 25% volatility spike
    }
}

# Economic scoring weights
ECONOMIC_SCORING_WEIGHTS = {
    'gdp_growth_yoy': 0.25,  # 25% weight
    'inflation_rate': 0.20,  # 20% weight
    'manufacturing_pmi': 0.15,  # 15% weight
    'balance_of_trade': 0.15,  # 15% weight
    'policy_rate_trend': 0.15,  # 15% weight
    'fx_reserves': 0.10  # 10% weight
}

# Technical analysis parameters
TECHNICAL_PARAMETERS = {
    'rsi': {
        'period': 14,
        'overbought': 70,
        'oversold': 30
    },
    'moving_averages': {
        'short': 20,
        'medium': 50,
        'long': 200
    },
    'bollinger_bands': {
        'period': 20,
        'std_dev': 2
    },
    'support_resistance': {
        'lookback_period': 20,
        'min_touches': 2
    }
}

# Market timing signals
MARKET_TIMING_SIGNALS = {
    'bullish_signals': [
        'RSI < 35 and rising',
        'Price > SMA20 > SMA50',
        'Volume expansion on up days',
        'Sectoral breadth > 60%',
        'Fed rate cuts expected'
    ],
    'bearish_signals': [
        'RSI > 70 and falling',
        'Price < SMA20 < SMA50',
        'Volume expansion on down days',
        'Sectoral breadth < 40%',
        'Fed rate hikes expected'
    ],
    'neutral_signals': [
        'RSI between 40-60',
        'Mixed technical signals',
        'Low volatility environment',
        'Sectoral breadth 40-60%'
    ]
}

# Vietnam market specific parameters
VIETNAM_MARKET_PARAMS = {
    'trading_hours': {
        'morning_session': ('09:00', '11:30'),
        'afternoon_session': ('13:00', '15:00'),
        'timezone': 'Asia/Ho_Chi_Minh'
    },
    'market_cap_tiers': {
        'large_cap': 50000,  # > 50T VND
        'mid_cap': 10000,  # 10-50T VND
        'small_cap': 1000  # 1-10T VND
    },
    'liquidity_tiers': {
        'high_liquidity': 100_000_000_000,  # > 100B VND daily
        'medium_liquidity': 10_000_000_000,  # 10-100B VND daily
        'low_liquidity': 1_000_000_000  # < 1B VND daily
    },
    'volatility_thresholds': {
        'low': 0.02,  # < 2% daily
        'normal': 0.04,  # 2-4% daily
        'high': 0.06,  # 4-6% daily
        'extreme': 0.10  # > 10% daily
    }
}

# Correlation matrix templates (for reference)
EXPECTED_CORRELATIONS = {
    'fed_rate_vs_vnindex': -0.65,
    'usd_vnd_vs_foreign_flows': -0.52,
    'vn_gdp_vs_vn30': 0.73,
    'oil_vs_vn_inflation': 0.45,
    'china_pmi_vs_vn_exports': 0.58,
    'us_10y_vs_vn_bonds': 0.82,
    'vn_manufacturing_vs_hpg': 0.71
}

# Data source configurations
DATA_SOURCES = {
    'fred': {
        'base_url': 'https://api.stlouisfed.org/fred/',
        'rate_limit': 120,  # requests per minute
        'cache_ttl': 3600  # 1 hour
    },
    'trading_economics': {
        'base_url': 'https://api.tradingeconomics.com/',
        'rate_limit': 100,  # requests per hour
        'cache_ttl': 900  # 15 minutes
    },
    'tcbs': {
        'base_url': 'https://apipubaws.tcbs.com.vn/',
        'rate_limit': 1000,  # requests per hour
        'cache_ttl': 300  # 5 minutes for market data
    },
    'yahoo_finance': {
        'rate_limit': 2000,  # requests per hour
        'cache_ttl': 600  # 10 minutes
    }
}