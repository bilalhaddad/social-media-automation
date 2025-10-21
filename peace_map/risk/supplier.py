"""
Supplier risk calculator for Peace Map platform
"""

import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .base import BaseRiskCalculator, RiskScore, RiskFactor, RiskLevel

logger = logging.getLogger(__name__)


class SupplierRiskCalculator(BaseRiskCalculator):
    """Calculates risk scores for suppliers"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("supplier", config)
        
        # Supplier risk factors
        self.supplier_weights = {
            "location_risk": 0.25,
            "financial_stability": 0.20,
            "operational_risk": 0.20,
            "compliance_risk": 0.15,
            "supply_chain_tier": 0.10,
            "historical_performance": 0.10
        }
        
        # Merge with config weights
        self.weights.update(self.supplier_weights)
        
        # Supplier risk parameters
        self.financial_thresholds = config.get("financial_thresholds", {
            "credit_rating_min": 600,
            "debt_ratio_max": 0.6,
            "profit_margin_min": 0.05
        })
        self.compliance_requirements = config.get("compliance_requirements", [
            "iso_9001", "iso_14001", "ohsas_18001", "sa_8000"
        ])
    
    async def initialize(self):
        """Initialize the supplier risk calculator"""
        try:
            self.is_initialized = True
            logger.info("Supplier risk calculator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize supplier risk calculator: {str(e)}")
            raise
    
    async def calculate_risk(self, data: Dict[str, Any], **kwargs) -> RiskScore:
        """Calculate supplier risk score"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Extract supplier data
            supplier = data.get("supplier", {})
            supplier_id = supplier.get("id", "unknown")
            
            # Calculate supplier risk factors
            factors = []
            
            # Location risk factor
            location_factor = self._calculate_location_risk_factor(supplier)
            factors.append(location_factor)
            
            # Financial stability factor
            financial_factor = self._calculate_financial_stability_factor(supplier)
            factors.append(financial_factor)
            
            # Operational risk factor
            operational_factor = self._calculate_operational_risk_factor(supplier)
            factors.append(operational_factor)
            
            # Compliance risk factor
            compliance_factor = self._calculate_compliance_risk_factor(supplier)
            factors.append(compliance_factor)
            
            # Supply chain tier factor
            tier_factor = self._calculate_supply_chain_tier_factor(supplier)
            factors.append(tier_factor)
            
            # Historical performance factor
            performance_factor = self._calculate_historical_performance_factor(supplier)
            factors.append(performance_factor)
            
            # Calculate weighted score
            overall_score, confidence = self.calculate_weighted_score(factors)
            
            # Normalize score
            overall_score = self.normalize_score(overall_score)
            
            # Get risk level
            risk_level = self.get_risk_level(overall_score)
            
            # Create risk score
            risk_score = RiskScore(
                overall_score=overall_score,
                risk_level=risk_level,
                factors=factors,
                confidence=confidence,
                calculated_at=datetime.utcnow(),
                region=supplier.get("country", "unknown"),
                metadata={
                    "supplier_id": supplier_id,
                    "supplier_name": supplier.get("name", "Unknown"),
                    "industry": supplier.get("industry", "Unknown"),
                    "country": supplier.get("country", "Unknown")
                }
            )
            
            return risk_score
            
        except Exception as e:
            logger.error(f"Supplier risk calculation failed: {str(e)}")
            return RiskScore(
                overall_score=0.0,
                risk_level=RiskLevel.LOW,
                factors=[],
                confidence=0.0,
                calculated_at=datetime.utcnow(),
                region=data.get("supplier", {}).get("country", "unknown")
            )
    
    def _calculate_location_risk_factor(self, supplier: Dict[str, Any]) -> RiskFactor:
        """Calculate risk factor based on supplier location"""
        country = supplier.get("country", "unknown")
        region = supplier.get("region", "unknown")
        
        # Country risk scores (simplified)
        country_risks = {
            "united_states": 20.0,
            "canada": 25.0,
            "germany": 30.0,
            "japan": 25.0,
            "australia": 30.0,
            "united_kingdom": 35.0,
            "france": 40.0,
            "italy": 50.0,
            "spain": 55.0,
            "china": 60.0,
            "india": 70.0,
            "brazil": 65.0,
            "russia": 80.0,
            "iran": 90.0,
            "north_korea": 95.0
        }
        
        # Get base country risk
        country_lower = country.lower()
        base_risk = 50.0  # Default risk
        
        for risk_country, risk_score in country_risks.items():
            if risk_country in country_lower:
                base_risk = risk_score
                break
        
        # Adjust for region within country
        if "middle_east" in region.lower():
            base_risk += 15
        elif "africa" in region.lower():
            base_risk += 10
        elif "asia" in region.lower() and country_lower not in ["japan", "south_korea", "singapore"]:
            base_risk += 5
        
        base_risk = min(base_risk, 100.0)
        
        return self._create_risk_factor(
            name="location_risk",
            value=base_risk,
            weight=self.weights["location_risk"],
            description=f"Location risk for {country}, {region}",
            source="geographic_analysis",
            confidence=0.8
        )
    
    def _calculate_financial_stability_factor(self, supplier: Dict[str, Any]) -> RiskFactor:
        """Calculate risk factor based on financial stability"""
        financial_data = supplier.get("financial_data", {})
        
        if not financial_data:
            return self._create_risk_factor(
                name="financial_stability",
                value=50.0,
                weight=self.weights["financial_stability"],
                description="No financial data available",
                source="financial_analysis",
                confidence=0.3
            )
        
        financial_risk = 50.0  # Base risk
        
        # Credit rating
        credit_rating = financial_data.get("credit_rating")
        if credit_rating:
            if credit_rating < self.financial_thresholds["credit_rating_min"]:
                financial_risk += 30
            elif credit_rating < 700:
                financial_risk += 20
            elif credit_rating < 750:
                financial_risk += 10
        
        # Debt ratio
        debt_ratio = financial_data.get("debt_ratio")
        if debt_ratio:
            if debt_ratio > self.financial_thresholds["debt_ratio_max"]:
                financial_risk += 25
            elif debt_ratio > 0.4:
                financial_risk += 15
            elif debt_ratio > 0.2:
                financial_risk += 5
        
        # Profit margin
        profit_margin = financial_data.get("profit_margin")
        if profit_margin:
            if profit_margin < self.financial_thresholds["profit_margin_min"]:
                financial_risk += 20
            elif profit_margin < 0.1:
                financial_risk += 10
            elif profit_margin < 0.15:
                financial_risk += 5
        
        # Revenue growth
        revenue_growth = financial_data.get("revenue_growth")
        if revenue_growth:
            if revenue_growth < -10:
                financial_risk += 20
            elif revenue_growth < 0:
                financial_risk += 10
            elif revenue_growth < 5:
                financial_risk += 5
        
        financial_risk = min(financial_risk, 100.0)
        
        return self._create_risk_factor(
            name="financial_stability",
            value=financial_risk,
            weight=self.weights["financial_stability"],
            description=f"Financial risk: {financial_risk:.1f}",
            source="financial_analysis",
            confidence=0.8
        )
    
    def _calculate_operational_risk_factor(self, supplier: Dict[str, Any]) -> RiskFactor:
        """Calculate risk factor based on operational characteristics"""
        operational_data = supplier.get("operational_data", {})
        
        if not operational_data:
            return self._create_risk_factor(
                name="operational_risk",
                value=50.0,
                weight=self.weights["operational_risk"],
                description="No operational data available",
                source="operational_analysis",
                confidence=0.3
            )
        
        operational_risk = 50.0  # Base risk
        
        # Production capacity
        capacity_utilization = operational_data.get("capacity_utilization")
        if capacity_utilization:
            if capacity_utilization > 95:
                operational_risk += 20  # Overcapacity risk
            elif capacity_utilization < 50:
                operational_risk += 15  # Underutilization risk
        
        # Quality metrics
        defect_rate = operational_data.get("defect_rate")
        if defect_rate:
            if defect_rate > 5:
                operational_risk += 25
            elif defect_rate > 2:
                operational_risk += 15
            elif defect_rate > 1:
                operational_risk += 5
        
        # Delivery performance
        on_time_delivery = operational_data.get("on_time_delivery_rate")
        if on_time_delivery:
            if on_time_delivery < 80:
                operational_risk += 20
            elif on_time_delivery < 90:
                operational_risk += 10
            elif on_time_delivery < 95:
                operational_risk += 5
        
        # Employee turnover
        turnover_rate = operational_data.get("employee_turnover_rate")
        if turnover_rate:
            if turnover_rate > 20:
                operational_risk += 15
            elif turnover_rate > 10:
                operational_risk += 10
            elif turnover_rate > 5:
                operational_risk += 5
        
        operational_risk = min(operational_risk, 100.0)
        
        return self._create_risk_factor(
            name="operational_risk",
            value=operational_risk,
            weight=self.weights["operational_risk"],
            description=f"Operational risk: {operational_risk:.1f}",
            source="operational_analysis",
            confidence=0.7
        )
    
    def _calculate_compliance_risk_factor(self, supplier: Dict[str, Any]) -> RiskFactor:
        """Calculate risk factor based on compliance status"""
        certifications = supplier.get("certifications", [])
        compliance_history = supplier.get("compliance_history", {})
        
        compliance_risk = 50.0  # Base risk
        
        # Check required certifications
        missing_certifications = []
        for cert in self.compliance_requirements:
            if cert not in certifications:
                missing_certifications.append(cert)
        
        if missing_certifications:
            compliance_risk += len(missing_certifications) * 15
        
        # Check compliance violations
        violations = compliance_history.get("violations", 0)
        if violations > 0:
            compliance_risk += violations * 20
        
        # Check audit results
        audit_score = compliance_history.get("last_audit_score")
        if audit_score:
            if audit_score < 60:
                compliance_risk += 30
            elif audit_score < 80:
                compliance_risk += 20
            elif audit_score < 90:
                compliance_risk += 10
        
        compliance_risk = min(compliance_risk, 100.0)
        
        return self._create_risk_factor(
            name="compliance_risk",
            value=compliance_risk,
            weight=self.weights["compliance_risk"],
            description=f"Compliance risk: {compliance_risk:.1f}",
            source="compliance_analysis",
            confidence=0.8
        )
    
    def _calculate_supply_chain_tier_factor(self, supplier: Dict[str, Any]) -> RiskFactor:
        """Calculate risk factor based on supply chain tier"""
        tier = supplier.get("supply_chain_tier", "unknown")
        
        # Tier risk scores (higher tier = higher risk)
        tier_risks = {
            "tier_1": 20.0,    # Direct suppliers
            "tier_2": 40.0,    # Sub-suppliers
            "tier_3": 60.0,    # Sub-sub-suppliers
            "tier_4": 80.0,    # Deep tier suppliers
            "unknown": 50.0    # Unknown tier
        }
        
        tier_risk = tier_risks.get(tier.lower(), 50.0)
        
        return self._create_risk_factor(
            name="supply_chain_tier",
            value=tier_risk,
            weight=self.weights["supply_chain_tier"],
            description=f"Supply chain tier risk: {tier}",
            source="supply_chain_analysis",
            confidence=0.9
        )
    
    def _calculate_historical_performance_factor(self, supplier: Dict[str, Any]) -> RiskFactor:
        """Calculate risk factor based on historical performance"""
        performance_data = supplier.get("performance_data", {})
        
        if not performance_data:
            return self._create_risk_factor(
                name="historical_performance",
                value=50.0,
                weight=self.weights["historical_performance"],
                description="No performance data available",
                source="performance_analysis",
                confidence=0.3
            )
        
        performance_risk = 50.0  # Base risk
        
        # Delivery performance over time
        delivery_trend = performance_data.get("delivery_trend")
        if delivery_trend:
            if delivery_trend < -10:  # Declining performance
                performance_risk += 25
            elif delivery_trend < -5:
                performance_risk += 15
            elif delivery_trend < 0:
                performance_risk += 5
        
        # Quality trend
        quality_trend = performance_data.get("quality_trend")
        if quality_trend:
            if quality_trend < -5:  # Declining quality
                performance_risk += 20
            elif quality_trend < -2:
                performance_risk += 10
            elif quality_trend < 0:
                performance_risk += 5
        
        # Relationship duration (longer = lower risk)
        relationship_years = performance_data.get("relationship_years", 0)
        if relationship_years > 10:
            performance_risk -= 10
        elif relationship_years > 5:
            performance_risk -= 5
        elif relationship_years < 1:
            performance_risk += 15
        
        performance_risk = max(0.0, min(performance_risk, 100.0))
        
        return self._create_risk_factor(
            name="historical_performance",
            value=performance_risk,
            weight=self.weights["historical_performance"],
            description=f"Performance risk: {performance_risk:.1f}",
            source="performance_analysis",
            confidence=0.7
        )
    
    def get_supplier_risk_summary(self, risk_scores: List[RiskScore]) -> Dict[str, Any]:
        """Get summary of supplier risk scores"""
        if not risk_scores:
            return {"summary": "no_data"}
        
        # Calculate statistics
        scores = [s.overall_score for s in risk_scores]
        risk_levels = [s.risk_level.value for s in risk_scores]
        
        # Count by risk level
        level_counts = {}
        for level in risk_levels:
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Find highest and lowest risk suppliers
        sorted_scores = sorted(risk_scores, key=lambda x: x.overall_score, reverse=True)
        
        return {
            "total_suppliers": len(risk_scores),
            "average_risk": np.mean(scores),
            "max_risk": max(scores),
            "min_risk": min(scores),
            "risk_std": np.std(scores),
            "risk_level_distribution": level_counts,
            "highest_risk_supplier": {
                "name": sorted_scores[0].metadata.get("supplier_name", "Unknown"),
                "score": sorted_scores[0].overall_score,
                "level": sorted_scores[0].risk_level.value
            },
            "lowest_risk_supplier": {
                "name": sorted_scores[-1].metadata.get("supplier_name", "Unknown"),
                "score": sorted_scores[-1].overall_score,
                "level": sorted_scores[-1].risk_level.value
            }
        }
    
    def get_suppliers_at_risk(self, risk_scores: List[RiskScore], threshold: float = 70.0) -> List[Dict[str, Any]]:
        """Get suppliers with risk above threshold"""
        at_risk = []
        
        for score in risk_scores:
            if score.overall_score >= threshold:
                at_risk.append({
                    "supplier_id": score.metadata.get("supplier_id"),
                    "supplier_name": score.metadata.get("supplier_name"),
                    "risk_score": score.overall_score,
                    "risk_level": score.risk_level.value,
                    "country": score.metadata.get("country"),
                    "industry": score.metadata.get("industry")
                })
        
        return at_risk
