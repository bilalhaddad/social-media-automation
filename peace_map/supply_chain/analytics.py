"""
Supply chain analytics for Peace Map platform
"""

import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .base import BaseSupplyChainManager, Supplier, SupplyChainAlert

logger = logging.getLogger(__name__)


class SupplyChainAnalytics(BaseSupplyChainManager):
    """Provides analytics and insights for supply chain data"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("analytics", config)
        self.suppliers: List[Supplier] = []
        self.alerts: List[SupplyChainAlert] = []
        self.risk_thresholds = config.get("risk_thresholds", {
            "low": 30,
            "medium": 60,
            "high": 80,
            "critical": 90
        })
    
    async def initialize(self):
        """Initialize the analytics manager"""
        try:
            self.is_initialized = True
            logger.info("Supply chain analytics initialized")
        except Exception as e:
            logger.error(f"Failed to initialize analytics: {str(e)}")
            raise
    
    async def process_suppliers(self, suppliers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process suppliers for analytics"""
        # This method is not used for analytics, but required by base class
        return []
    
    def set_data(self, suppliers: List[Supplier], alerts: List[SupplyChainAlert]):
        """Set data for analysis"""
        self.suppliers = suppliers
        self.alerts = alerts
    
    def get_supply_chain_overview(self) -> Dict[str, Any]:
        """Get overall supply chain overview"""
        if not self.suppliers:
            return {"overview": "no_data"}
        
        # Basic statistics
        total_suppliers = len(self.suppliers)
        active_suppliers = len([s for s in self.suppliers if s.status.value == "active"])
        
        # Risk distribution
        risk_distribution = self._calculate_risk_distribution()
        
        # Geographic distribution
        geographic_distribution = self._calculate_geographic_distribution()
        
        # Industry distribution
        industry_distribution = self._calculate_industry_distribution()
        
        # Alert statistics
        alert_stats = self._calculate_alert_statistics()
        
        # Risk trends
        risk_trends = self._calculate_risk_trends()
        
        return {
            "total_suppliers": total_suppliers,
            "active_suppliers": active_suppliers,
            "inactive_suppliers": total_suppliers - active_suppliers,
            "risk_distribution": risk_distribution,
            "geographic_distribution": geographic_distribution,
            "industry_distribution": industry_distribution,
            "alert_statistics": alert_stats,
            "risk_trends": risk_trends,
            "overall_risk_score": self._calculate_overall_risk_score(),
            "supply_chain_health": self._calculate_supply_chain_health()
        }
    
    def _calculate_risk_distribution(self) -> Dict[str, Any]:
        """Calculate risk distribution across suppliers"""
        if not self.suppliers:
            return {}
        
        # Count by risk level
        risk_levels = {}
        risk_scores = []
        
        for supplier in self.suppliers:
            risk_level = supplier.risk_level
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
            risk_scores.append(supplier.risk_score)
        
        # Calculate statistics
        avg_risk = np.mean(risk_scores)
        max_risk = np.max(risk_scores)
        min_risk = np.min(risk_scores)
        std_risk = np.std(risk_scores)
        
        # High-risk suppliers
        high_risk_count = len([s for s in self.suppliers if s.risk_score >= self.risk_thresholds["high"]])
        critical_risk_count = len([s for s in self.suppliers if s.risk_score >= self.risk_thresholds["critical"]])
        
        return {
            "risk_levels": risk_levels,
            "statistics": {
                "average_risk": round(avg_risk, 2),
                "max_risk": max_risk,
                "min_risk": min_risk,
                "std_risk": round(std_risk, 2)
            },
            "high_risk_suppliers": high_risk_count,
            "critical_risk_suppliers": critical_risk_count,
            "high_risk_percentage": round((high_risk_count / len(self.suppliers)) * 100, 1) if self.suppliers else 0
        }
    
    def _calculate_geographic_distribution(self) -> Dict[str, Any]:
        """Calculate geographic distribution of suppliers"""
        if not self.suppliers:
            return {}
        
        # Group by country
        country_data = {}
        for supplier in self.suppliers:
            country = supplier.country
            if country not in country_data:
                country_data[country] = {
                    "count": 0,
                    "suppliers": [],
                    "avg_risk": 0.0,
                    "high_risk_count": 0
                }
            
            country_data[country]["count"] += 1
            country_data[country]["suppliers"].append({
                "id": supplier.id,
                "name": supplier.name,
                "risk_score": supplier.risk_score,
                "risk_level": supplier.risk_level
            })
            
            if supplier.risk_score >= self.risk_thresholds["high"]:
                country_data[country]["high_risk_count"] += 1
        
        # Calculate average risk per country
        for country, data in country_data.items():
            risk_scores = [s["risk_score"] for s in data["suppliers"]]
            data["avg_risk"] = round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else 0.0
        
        # Sort by count
        sorted_countries = sorted(country_data.items(), key=lambda x: x[1]["count"], reverse=True)
        
        return {
            "countries": dict(sorted_countries),
            "total_countries": len(country_data),
            "top_countries": [{"country": k, "count": v["count"]} for k, v in sorted_countries[:10]]
        }
    
    def _calculate_industry_distribution(self) -> Dict[str, Any]:
        """Calculate industry distribution of suppliers"""
        if not self.suppliers:
            return {}
        
        # Group by industry
        industry_data = {}
        for supplier in self.suppliers:
            industry = supplier.industry or "Unknown"
            if industry not in industry_data:
                industry_data[industry] = {
                    "count": 0,
                    "avg_risk": 0.0,
                    "suppliers": []
                }
            
            industry_data[industry]["count"] += 1
            industry_data[industry]["suppliers"].append(supplier.risk_score)
        
        # Calculate average risk per industry
        for industry, data in industry_data.items():
            if data["suppliers"]:
                data["avg_risk"] = round(sum(data["suppliers"]) / len(data["suppliers"]), 2)
                data["max_risk"] = max(data["suppliers"])
                data["min_risk"] = min(data["suppliers"])
            else:
                data["avg_risk"] = 0.0
                data["max_risk"] = 0.0
                data["min_risk"] = 0.0
        
        # Sort by count
        sorted_industries = sorted(industry_data.items(), key=lambda x: x[1]["count"], reverse=True)
        
        return {
            "industries": dict(sorted_industries),
            "total_industries": len(industry_data),
            "top_industries": [{"industry": k, "count": v["count"]} for k, v in sorted_industries[:10]]
        }
    
    def _calculate_alert_statistics(self) -> Dict[str, Any]:
        """Calculate alert statistics"""
        if not self.alerts:
            return {"total_alerts": 0}
        
        # Count by status
        status_counts = {}
        for alert in self.alerts:
            status = alert.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by severity
        severity_counts = {}
        for alert in self.alerts:
            severity = alert.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by type
        type_counts = {}
        for alert in self.alerts:
            alert_type = alert.alert_type
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
        
        # Recent alerts
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent_alerts = [a for a in self.alerts if a.created_at >= recent_cutoff]
        
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len([a for a in self.alerts if a.status.value == "active"]),
            "recent_alerts_7d": len(recent_alerts),
            "status_distribution": status_counts,
            "severity_distribution": severity_counts,
            "type_distribution": type_counts
        }
    
    def _calculate_risk_trends(self) -> Dict[str, Any]:
        """Calculate risk trends over time"""
        # This would typically analyze historical data
        # For now, return basic trend information
        return {
            "trend": "stable",
            "note": "Historical trend analysis requires time-series data"
        }
    
    def _calculate_overall_risk_score(self) -> float:
        """Calculate overall supply chain risk score"""
        if not self.suppliers:
            return 0.0
        
        # Weighted average of supplier risk scores
        total_risk = sum(s.risk_score for s in self.suppliers)
        return round(total_risk / len(self.suppliers), 2)
    
    def _calculate_supply_chain_health(self) -> Dict[str, Any]:
        """Calculate overall supply chain health score"""
        if not self.suppliers:
            return {"health_score": 0, "status": "unknown"}
        
        # Calculate health score based on multiple factors
        factors = []
        
        # Risk factor (lower risk = better health)
        avg_risk = self._calculate_overall_risk_score()
        risk_health = max(0, 100 - avg_risk)
        factors.append(risk_health)
        
        # Active supplier factor
        active_ratio = len([s for s in self.suppliers if s.status.value == "active"]) / len(self.suppliers)
        active_health = active_ratio * 100
        factors.append(active_health)
        
        # Alert factor (fewer alerts = better health)
        if self.alerts:
            active_alerts = len([a for a in self.alerts if a.status.value == "active"])
            alert_health = max(0, 100 - (active_alerts * 5))  # Each active alert reduces health by 5 points
        else:
            alert_health = 100
        factors.append(alert_health)
        
        # Calculate overall health score
        health_score = sum(factors) / len(factors)
        
        # Determine health status
        if health_score >= 80:
            status = "excellent"
        elif health_score >= 60:
            status = "good"
        elif health_score >= 40:
            status = "fair"
        elif health_score >= 20:
            status = "poor"
        else:
            status = "critical"
        
        return {
            "health_score": round(health_score, 2),
            "status": status,
            "factors": {
                "risk_health": round(risk_health, 2),
                "active_health": round(active_health, 2),
                "alert_health": round(alert_health, 2)
            }
        }
    
    def get_supplier_risk_analysis(self, supplier_id: str) -> Dict[str, Any]:
        """Get detailed risk analysis for a specific supplier"""
        supplier = next((s for s in self.suppliers if s.id == supplier_id), None)
        if not supplier:
            return {"error": "Supplier not found"}
        
        # Get supplier alerts
        supplier_alerts = [a for a in self.alerts if a.supplier_id == supplier_id]
        
        # Calculate risk factors
        risk_factors = {
            "base_risk_score": supplier.risk_score,
            "risk_level": supplier.risk_level,
            "status": supplier.status.value,
            "location_risk": self._calculate_location_risk(supplier),
            "alert_risk": self._calculate_alert_risk(supplier_alerts),
            "industry_risk": self._calculate_industry_risk(supplier.industry)
        }
        
        # Calculate composite risk
        composite_risk = self._calculate_composite_risk(risk_factors)
        
        return {
            "supplier_id": supplier_id,
            "supplier_name": supplier.name,
            "risk_factors": risk_factors,
            "composite_risk": composite_risk,
            "alerts": {
                "total": len(supplier_alerts),
                "active": len([a for a in supplier_alerts if a.status.value == "active"]),
                "recent": len([a for a in supplier_alerts if a.created_at >= datetime.utcnow() - timedelta(days=30)])
            },
            "recommendations": self._generate_recommendations(risk_factors, supplier_alerts)
        }
    
    def _calculate_location_risk(self, supplier: Supplier) -> float:
        """Calculate location-based risk"""
        # Simplified location risk calculation
        high_risk_countries = ["iran", "north korea", "syria", "russia"]
        if supplier.country.lower() in high_risk_countries:
            return 80.0
        
        # Medium risk countries
        medium_risk_countries = ["china", "venezuela", "cuba"]
        if supplier.country.lower() in medium_risk_countries:
            return 60.0
        
        # Default risk
        return 30.0
    
    def _calculate_alert_risk(self, alerts: List[SupplyChainAlert]) -> float:
        """Calculate risk based on alerts"""
        if not alerts:
            return 0.0
        
        # Weight alerts by severity
        risk_score = 0.0
        for alert in alerts:
            if alert.severity == "critical":
                risk_score += 25
            elif alert.severity == "high":
                risk_score += 15
            elif alert.severity == "medium":
                risk_score += 10
            else:
                risk_score += 5
        
        return min(risk_score, 100.0)
    
    def _calculate_industry_risk(self, industry: str) -> float:
        """Calculate industry-based risk"""
        if not industry:
            return 50.0
        
        # High-risk industries
        high_risk_industries = ["defense", "aerospace", "nuclear", "chemical"]
        if any(risk_industry in industry.lower() for risk_industry in high_risk_industries):
            return 70.0
        
        # Medium-risk industries
        medium_risk_industries = ["pharmaceutical", "medical", "energy", "mining"]
        if any(risk_industry in industry.lower() for risk_industry in medium_risk_industries):
            return 50.0
        
        # Default risk
        return 30.0
    
    def _calculate_composite_risk(self, risk_factors: Dict[str, Any]) -> float:
        """Calculate composite risk score"""
        weights = {
            "base_risk_score": 0.4,
            "location_risk": 0.2,
            "alert_risk": 0.2,
            "industry_risk": 0.2
        }
        
        composite_risk = 0.0
        for factor, weight in weights.items():
            if factor in risk_factors:
                composite_risk += risk_factors[factor] * weight
        
        return round(composite_risk, 2)
    
    def _generate_recommendations(self, risk_factors: Dict[str, Any], alerts: List[SupplyChainAlert]) -> List[str]:
        """Generate recommendations based on risk analysis"""
        recommendations = []
        
        # High risk score recommendations
        if risk_factors["base_risk_score"] >= 80:
            recommendations.append("Consider diversifying supplier base to reduce concentration risk")
        
        # Location risk recommendations
        if risk_factors["location_risk"] >= 70:
            recommendations.append("Evaluate alternative suppliers in lower-risk regions")
        
        # Alert-based recommendations
        active_alerts = [a for a in alerts if a.status.value == "active"]
        if len(active_alerts) >= 3:
            recommendations.append("Address active alerts to improve supplier relationship")
        
        # Industry risk recommendations
        if risk_factors["industry_risk"] >= 60:
            recommendations.append("Implement enhanced due diligence for high-risk industry suppliers")
        
        # Default recommendations
        if not recommendations:
            recommendations.append("Continue monitoring supplier performance and risk indicators")
        
        return recommendations
    
    def get_supply_chain_insights(self) -> Dict[str, Any]:
        """Get key insights about the supply chain"""
        if not self.suppliers:
            return {"insights": "no_data"}
        
        insights = []
        
        # Risk concentration insights
        high_risk_suppliers = [s for s in self.suppliers if s.risk_score >= self.risk_thresholds["high"]]
        if len(high_risk_suppliers) > len(self.suppliers) * 0.2:  # More than 20% high risk
            insights.append(f"High risk concentration: {len(high_risk_suppliers)} suppliers ({len(high_risk_suppliers)/len(self.suppliers)*100:.1f}%) are high risk")
        
        # Geographic concentration insights
        country_counts = {}
        for supplier in self.suppliers:
            country_counts[supplier.country] = country_counts.get(supplier.country, 0) + 1
        
        max_country = max(country_counts.items(), key=lambda x: x[1])
        if max_country[1] > len(self.suppliers) * 0.3:  # More than 30% in one country
            insights.append(f"Geographic concentration: {max_country[1]} suppliers ({max_country[1]/len(self.suppliers)*100:.1f}%) are in {max_country[0]}")
        
        # Alert insights
        if self.alerts:
            active_alerts = [a for a in self.alerts if a.status.value == "active"]
            if len(active_alerts) > 0:
                insights.append(f"Active alerts: {len(active_alerts)} unresolved alerts require attention")
        
        return {
            "insights": insights,
            "total_insights": len(insights),
            "supply_chain_health": self._calculate_supply_chain_health()
        }
