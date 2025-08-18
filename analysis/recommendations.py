# analysis/recommendations.py
from typing import Dict, Any, List


def get_sector_rationale(sector, performance, risk_tolerance):
    rationales = {
        "Banking": "Defensive play with dividend yield, benefits from rate normalization",
        "Technology": "High growth potential, digital transformation theme",
        "Real Estate": "Inflation hedge, infrastructure development",
        "Energy": "Essential sector, commodity cycle play",
        "Manufacturing": "Export growth, supply chain diversification",
        "Aviation": "Recovery play, tourism rebound",
    }
    base = rationales.get(sector, "Sector diversification")
    if performance > 2:
        return f"{base} - Strong momentum"
    if performance < -2:
        return f"{base} - Value opportunity"
    return base


def generate_investment_recommendation(us_data: Dict, vn_data: Dict, fed_data: Dict) -> Dict[str, Any]:
    recs: List[str] = []
    risk_level = "Medium"

    # Fed rate
    if 'fed_rate' in us_data:
        fed_rate = us_data['fed_rate']['value']
        if fed_rate > 5:
            recs.append("⚠️ High Fed rates may pressure EM incl. Vietnam")
            risk_level = "High"
        elif fed_rate < 2:
            recs.append("✅ Low Fed rates generally support emerging markets")

    # Inflation
    if 'inflation' in us_data:
        infl = us_data['inflation']['value']
        if infl > 3:
            recs.append("📊 High US inflation may delay rate cuts")
        elif infl < 2:
            recs.append("📈 Low inflation may prompt accommodation")

    # VN
    if 'vnindex' in vn_data and 'error' not in vn_data:
        vn = vn_data['vnindex']
        price = vn.get('price', 0)
        rsi = vn.get('rsi')
        if price:
            if price < 1200:
                recs.append("🔥 VN-Index at attractive levels - consider accumulating")
                risk_level = "Low"
            elif price > 1400:
                recs.append("⚖️ VN-Index at elevated levels - be cautious")
                risk_level = "High"
        if rsi is not None:
            if rsi < 30:
                recs.append("📉 VN market oversold - potential opportunity")
            elif rsi > 70:
                recs.append("📈 VN market overbought - consider taking profits")

    if 'sectors' in vn_data and vn_data['sectors']:
        best = max(vn_data['sectors'].items(), key=lambda x: x[1]['avg_return'])
        recs.append(f"🏆 Best performing sector: {best[0]} ({best[1]['avg_return']:.2f}%)")

    if not recs:
        recs.append("📊 Monitor market conditions - mixed signals")

    return {
        'recommendations': recs,
        'risk_level': risk_level,
        'summary': f"Current risk level: {risk_level}. Based on {len(recs)} key factors."
    }
