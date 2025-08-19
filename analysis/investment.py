# analysis/investment.py
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from analysis.indicators import format_number


def analyze_fed_vietnam_correlation(us_data: Dict, vn_data: Dict, global_context: Dict) -> Dict[str, Any]:
    """
    Analyze correlation between US Fed policy and Vietnam markets.
    """
    analysis = {
        "fed_impact_score": 0,  # -100 to +100
        "key_factors": [],
        "recommendations": [],
        "risk_level": "Medium"
    }

    # Fed Funds Rate Impact
    if "fed_rate" in us_data:
        fed_rate = us_data["fed_rate"]["value"]

        if fed_rate > 5.0:
            analysis["fed_impact_score"] -= 30
            analysis["key_factors"].append(f"🔴 High Fed rate ({fed_rate:.2f}%) pressures emerging markets")
            analysis["risk_level"] = "High"
        elif fed_rate < 2.0:
            analysis["fed_impact_score"] += 20
            analysis["key_factors"].append(f"🟢 Low Fed rate ({fed_rate:.2f}%) supports EM flows")

        # Rate direction matters
        if "mom_change" in us_data["fed_rate"] and us_data["fed_rate"]["mom_change"]:
            mom_change = us_data["fed_rate"]["mom_change"]
            if mom_change > 0.1:  # Rising rates
                analysis["fed_impact_score"] -= 15
                analysis["key_factors"].append("🔴 Rising US rates create headwinds")
            elif mom_change < -0.1:  # Falling rates
                analysis["fed_impact_score"] += 15
                analysis["key_factors"].append("🟢 Falling US rates support EM")

    # US Inflation Impact
    if "inflation" in us_data:
        inflation = us_data["inflation"]["value"]

        if inflation > 4.0:
            analysis["fed_impact_score"] -= 20
            analysis["key_factors"].append(f"🔴 High US inflation ({inflation:.1f}%) may force Fed hawkishness")
        elif inflation < 2.5:
            analysis["fed_impact_score"] += 15
            analysis["key_factors"].append(f"🟢 Moderate US inflation ({inflation:.1f}%) allows Fed flexibility")

    # Dollar strength (if available)
    if "dxy" in global_context:
        dxy_change = global_context["dxy"].get("change")
        if dxy_change:
            if dxy_change > 2:
                analysis["fed_impact_score"] -= 25
                analysis["key_factors"].append("🔴 Strong USD creates EM outflows")
            elif dxy_change < -2:
                analysis["fed_impact_score"] += 20
                analysis["key_factors"].append("🟢 Weak USD supports EM inflows")

    # Vietnam market technicals
    if "indices" in vn_data and "vnindex" in vn_data["indices"]:
        vni = vn_data["indices"]["vnindex"]
        if vni.get("rsi"):
            rsi = vni["rsi"]
            if rsi < 35:
                analysis["fed_impact_score"] += 10
                analysis["key_factors"].append("🟢 VN-Index oversold, potential reversal")
            elif rsi > 65:
                analysis["fed_impact_score"] -= 10
                analysis["key_factors"].append("🔴 VN-Index overbought, vulnerable to correction")

    # Generate recommendations
    if analysis["fed_impact_score"] > 20:
        analysis["recommendations"].extend([
            "🟢 Favorable Fed environment for Vietnam exposure",
            "💡 Consider increasing Vietnam allocation",
            "📈 Focus on growth sectors (Tech, Consumer)"
        ])
        analysis["risk_level"] = "Low"
    elif analysis["fed_impact_score"] < -20:
        analysis["recommendations"].extend([
            "🔴 Challenging Fed environment for Vietnam",
            "⚖️ Reduce Vietnam exposure or hedge currency risk",
            "🛡️ Focus on defensive sectors (Utilities, Consumer Staples)"
        ])
        analysis["risk_level"] = "High"
    else:
        analysis["recommendations"].extend([
            "🟡 Mixed Fed signals - cautious approach",
            "📊 Monitor Fed communications closely",
            "⚖️ Maintain balanced sector allocation"
        ])

    return analysis


def analyze_vietnam_macro_market_correlation(vn_economic: Dict, vn_market: Dict) -> Dict[str, Any]:
    """
    Analyze correlation between Vietnam economic indicators and market performance.
    """
    analysis = {
        "macro_score": 50,  # 0-100 scale
        "economic_drivers": [],
        "market_implications": [],
        "sector_rotation": {}
    }

    # GDP Growth Impact
    if "gdp_growth_yoy" in vn_economic:
        gdp_data = vn_economic["gdp_growth_yoy"]
        gdp_growth = gdp_data.get("value")
        if gdp_growth:
            if gdp_growth > 6.5:
                analysis["macro_score"] += 15
                analysis["economic_drivers"].append(f"🟢 Strong GDP growth ({gdp_growth:.1f}%)")
                analysis["sector_rotation"]["growth_favored"] = ["Technology", "Real Estate", "Manufacturing"]
            elif gdp_growth < 5.0:
                analysis["macro_score"] -= 10
                analysis["economic_drivers"].append(f"🔴 Slow GDP growth ({gdp_growth:.1f}%)")
                analysis["sector_rotation"]["defensive_favored"] = ["Banking", "Utilities"]

    # Inflation Impact
    if "inflation_rate" in vn_economic:
        inflation_data = vn_economic["inflation_rate"]
        inflation = inflation_data.get("value")
        if inflation:
            if 2 <= inflation <= 4:
                analysis["macro_score"] += 10
                analysis["economic_drivers"].append(f"🟢 Healthy inflation ({inflation:.1f}%)")
            elif inflation > 5:
                analysis["macro_score"] -= 15
                analysis["economic_drivers"].append(f"🔴 High inflation ({inflation:.1f}%)")
                analysis["sector_rotation"]["inflation_hedge"] = ["Real Estate", "Energy", "Manufacturing"]

    # Manufacturing PMI
    if "manufacturing_pmi" in vn_economic:
        pmi_data = vn_economic["manufacturing_pmi"]
        pmi = pmi_data.get("value")
        if pmi:
            if pmi > 52:
                analysis["macro_score"] += 12
                analysis["economic_drivers"].append(f"🟢 Expanding manufacturing (PMI: {pmi:.1f})")
                analysis["sector_rotation"]["manufacturing_cycle"] = ["Manufacturing", "Technology", "Energy"]
            elif pmi < 50:
                analysis["macro_score"] -= 12
                analysis["economic_drivers"].append(f"🔴 Contracting manufacturing (PMI: {pmi:.1f})")

    # Trade Balance
    if "balance_of_trade" in vn_economic:
        trade_data = vn_economic["balance_of_trade"]
        trade_balance = trade_data.get("value")
        if trade_balance:
            if trade_balance > 2:
                analysis["macro_score"] += 8
                analysis["economic_drivers"].append(f"🟢 Strong trade surplus (${trade_balance:.1f}B)")
                analysis["sector_rotation"]["export_beneficiary"] = ["Manufacturing", "Technology"]
            elif trade_balance < -1:
                analysis["macro_score"] -= 8
                analysis["economic_drivers"].append(f"🔴 Trade deficit (${trade_balance:.1f}B)")

    # Policy Rate Impact
    if "policy_rate" in vn_economic:
        policy_data = vn_economic["policy_rate"]
        policy_rate = policy_data.get("value")
        policy_change = policy_data.get("change")

        if policy_rate and policy_change:
            if policy_change < -0.25:  # Rate cuts
                analysis["macro_score"] += 10
                analysis["economic_drivers"].append(f"🟢 Accommodative policy (Rate: {policy_rate:.2f}% ↓)")
                analysis["sector_rotation"]["rate_sensitive"] = ["Real Estate", "Banking", "Technology"]
            elif policy_change > 0.25:  # Rate hikes
                analysis["macro_score"] -= 8
                analysis["economic_drivers"].append(f"🔴 Tightening policy (Rate: {policy_rate:.2f}% ↑)")

    # Market implications based on macro score
    if analysis["macro_score"] > 70:
        analysis["market_implications"].extend([
            "🚀 Strong macro environment supports risk-on approach",
            "📈 Favor cyclical and growth sectors",
            "💰 Consider increasing Vietnam allocation"
        ])
    elif analysis["macro_score"] < 40:
        analysis["market_implications"].extend([
            "⚠️ Weak macro environment suggests caution",
            "🛡️ Favor defensive sectors and quality names",
            "💱 Consider currency hedging"
        ])
    else:
        analysis["market_implications"].extend([
            "⚖️ Mixed macro signals require selective approach",
            "📊 Focus on bottom-up stock selection",
            "🎯 Maintain sector diversification"
        ])

    return analysis


def generate_comprehensive_investment_recommendation(
        us_data: Dict,
        vn_economic: Dict,
        vn_market: Dict,
        global_context: Dict,
        fed_data: Dict,
        risk_tolerance: str
) -> Dict[str, Any]:
    """
    Generate comprehensive investment recommendations incorporating all data sources.
    """

    # Run sub-analyses
    fed_analysis = analyze_fed_vietnam_correlation(us_data, vn_market, global_context)
    macro_analysis = analyze_vietnam_macro_market_correlation(vn_economic, vn_market)

    # Combine analyses
    overall_score = (fed_analysis["fed_impact_score"] + 50 + macro_analysis["macro_score"]) / 2

    recommendations = []
    risk_factors = []
    opportunities = []

    # Market timing assessment
    market_timing = "Neutral"
    if overall_score > 65:
        market_timing = "Favorable"
        recommendations.append("🟢 Market conditions favor Vietnam exposure")
    elif overall_score < 40:
        market_timing = "Unfavorable"
        recommendations.append("🔴 Exercise caution with Vietnam exposure")

    # Technical analysis integration
    if "indices" in vn_market:
        for index_name, index_data in vn_market["indices"].items():
            if index_name == "vnindex":
                rsi = index_data.get("rsi")
                if rsi:
                    if rsi < 30:
                        opportunities.append(
                            f"📉 {index_data['name']} oversold (RSI: {rsi:.1f}) - potential entry point")
                    elif rsi > 70:
                        risk_factors.append(
                            f"📈 {index_data['name']} overbought (RSI: {rsi:.1f}) - potential correction ahead")

    # Sector rotation recommendations
    sector_recs = []
    if macro_analysis["sector_rotation"]:
        for category, sectors in macro_analysis["sector_rotation"].items():
            if category == "growth_favored":
                sector_recs.append(f"🚀 Growth environment favors: {', '.join(sectors)}")
            elif category == "defensive_favored":
                sector_recs.append(f"🛡️ Defensive positioning: {', '.join(sectors)}")
            elif category == "inflation_hedge":
                sector_recs.append(f"🔥 Inflation hedge plays: {', '.join(sectors)}")

    # VN30 vs broad market analysis
    if "vn30_analysis" in vn_market and vn_market["vn30_analysis"]:
        vn30 = vn_market["vn30_analysis"]
        if vn30.get("advance_decline_ratio"):
            ad_ratio = vn30["advance_decline_ratio"]
            if ad_ratio > 2:
                opportunities.append("🟢 VN30 shows strong breadth - broad-based rally")
            elif ad_ratio < 0.5:
                risk_factors.append("🔴 VN30 shows weak breadth - selective selling")

    # Risk-adjusted recommendations based on tolerance
    allocation_recs = []
    if risk_tolerance == "Conservative":
        if overall_score > 60:
            allocation_recs.append("💰 Consider 10-15% Vietnam allocation via dividend-focused stocks")
            allocation_recs.append("🏦 Favor Banking and Utilities sectors")
        else:
            allocation_recs.append("💰 Limit Vietnam to 5-8% allocation")
            allocation_recs.append("🛡️ Focus on large-cap, established names only")
    elif risk_tolerance == "Moderate":
        if overall_score > 55:
            allocation_recs.append("⚖️ Consider 15-25% Vietnam allocation")
            allocation_recs.append("📊 Balanced sector approach with growth tilt")
        else:
            allocation_recs.append("⚖️ Maintain 10-15% Vietnam allocation")
            allocation_recs.append("🎯 Focus on quality names and avoid speculative plays")
    else:  # Aggressive
        if overall_score > 50:
            allocation_recs.append("🚀 Consider 25-35% Vietnam allocation")
            allocation_recs.append("📈 Favor growth sectors and small-mid caps")
        else:
            allocation_recs.append("🚀 Consider 15-20% Vietnam allocation")
            allocation_recs.append("⚖️ Balance growth plays with some defensive positions")

    # Currency considerations
    currency_recs = []
    if "usd_vnd" in global_context:
        usd_vnd_change = global_context["usd_vnd"].get("change")
        if usd_vnd_change:
            if abs(usd_vnd_change) > 3:  # Significant currency movement
                currency_recs.append("💱 Consider currency hedging for large positions")
            elif usd_vnd_change < -2:  # VND strengthening
                currency_recs.append("🟢 VND strength provides tailwind for USD investors")

    # Final risk assessment
    risk_level = "Medium"
    if fed_analysis["risk_level"] == "High" or macro_analysis["macro_score"] < 40:
        risk_level = "High"
    elif fed_analysis["risk_level"] == "Low" and macro_analysis["macro_score"] > 70:
        risk_level = "Low"

    return {
        "overall_score": round(overall_score, 1),
        "market_timing": market_timing,
        "risk_level": risk_level,
        "key_recommendations": recommendations + sector_recs + allocation_recs,
        "opportunities": opportunities,
        "risk_factors": risk_factors,
        "currency_considerations": currency_recs,
        "fed_analysis": fed_analysis,
        "macro_analysis": macro_analysis,
        "summary": f"Overall market score: {overall_score:.1f}/100. {market_timing} timing with {risk_level.lower()} risk level."
    }


def get_sector_investment_rationale(sector: str, performance: Dict, economic_context: Dict) -> str:
    """
    Generate detailed investment rationale for each sector based on current conditions.
    """
    base_rationales = {
        "Banking": "Interest rate beneficiary with strong deposit growth",
        "Technology": "Digital transformation and export growth driver",
        "Real Estate": "Infrastructure development and urbanization theme",
        "Energy": "Essential services with commodity exposure",
        "Manufacturing": "Export manufacturing hub with FDI attraction",
        "Aviation": "Tourism recovery and domestic travel growth"
    }

    base = base_rationales.get(sector, "Diversification play")

    # Add performance context
    if "avg_return_1d" in performance:
        daily_perf = performance["avg_return_1d"]
        if daily_perf > 3:
            base += " - Strong momentum"
        elif daily_perf < -3:
            base += " - Value opportunity emerging"

    # Add economic context
    if sector == "Banking" and "policy_rate" in economic_context:
        policy_data = economic_context["policy_rate"]
        if policy_data.get("change", 0) > 0:
            base += " - Rate hikes support NIM expansion"
        elif policy_data.get("change", 0) < 0:
            base += " - Rate cuts may pressure margins but support lending"

    elif sector == "Real Estate" and "inflation_rate" in economic_context:
        inflation = economic_context["inflation_rate"].get("value", 0)
        if inflation > 3:
            base += " - Real asset inflation hedge"

    elif sector == "Manufacturing" and "balance_of_trade" in economic_context:
        trade_balance = economic_context["balance_of_trade"].get("value", 0)
        if trade_balance > 1:
            base += " - Export strength supports sector"

    return base