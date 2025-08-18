# constants.py
VN_MAJOR_STOCKS = {
    'Banking': ['VCB', 'TCB', 'MBB', 'BID', 'CTG', 'VPB'],
    'Energy': ['GAS', 'PLX', 'PVD', 'POW', 'REE'],
    'Real Estate': ['VHM', 'VIC', 'KDH', 'DXG', 'NVL'],
    'Technology': ['FPT', 'CMG', 'ELC', 'SVC'],
    'Manufacturing': ['HPG', 'HSG', 'NKG', 'VNM', 'MSN'],
    'Aviation': ['VJC']
}

ECONOMIC_INDICATORS = {
    'inflation': {'fred': 'CPIAUCSL', 'name': 'Consumer Price Index'},
    'pce': {'fred': 'PCEPI', 'name': 'PCE Price Index'},
    'unemployment': {'fred': 'UNRATE', 'name': 'Unemployment Rate'},
    'fed_rate': {'fred': 'FEDFUNDS', 'name': 'Federal Funds Rate'},
    'gdp': {'fred': 'GDP', 'name': 'Gross Domestic Product'},
    'housing': {'fred': 'HOUST', 'name': 'Housing Starts'},
    'retail_sales': {'fred': 'RSXFS', 'name': 'Retail Sales'},
    'industrial_production': {'fred': 'INDPRO', 'name': 'Industrial Production'},
}
