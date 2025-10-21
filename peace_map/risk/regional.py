"""
Regional risk calculator for Peace Map platform
"""

import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .base import BaseRiskCalculator, RiskScore, RiskFactor, RiskLevel
from ..ingestion.base import Event

logger = logging.getLogger(__name__)


class RegionalRiskCalculator(BaseRiskCalculator):
    """Calculates risk scores for specific regions"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("regional", config)
        
        # Regional risk factors
        self.regional_weights = {
            "event_density": 0.25,
            "event_intensity": 0.20,
            "geographic_risk": 0.15,
            "economic_factors": 0.15,
            "political_stability": 0.15,
            "infrastructure": 0.10
        }
        
        # Merge with config weights
        self.weights.update(self.regional_weights)
        
        # Regional risk parameters
        self.region_size_threshold = config.get("region_size_threshold", 100.0)  # km²
        self.economic_indicators = config.get("economic_indicators", {})
        self.political_stability_scores = config.get("political_stability", {})
        self.infrastructure_scores = config.get("infrastructure", {})
    
    async def initialize(self):
        """Initialize the regional risk calculator"""
        try:
            self.is_initialized = True
            logger.info("Regional risk calculator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize regional risk calculator: {str(e)}")
            raise
    
    async def calculate_risk(self, data: Dict[str, Any], **kwargs) -> RiskScore:
        """Calculate regional risk score"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Extract data
            region = data.get("region", "unknown")
            events = data.get("events", [])
            region_bounds = data.get("region_bounds")
            economic_data = data.get("economic_data", {})
            political_data = data.get("political_data", {})
            infrastructure_data = data.get("infrastructure_data", {})
            
            # Calculate regional risk factors
            factors = []
            
            # Event density factor
            density_factor = self._calculate_event_density_factor(events, region_bounds)
            factors.append(density_factor)
            
            # Event intensity factor
            intensity_factor = self._calculate_event_intensity_factor(events)
            factors.append(intensity_factor)
            
            # Geographic risk factor
            geographic_factor = self._calculate_geographic_risk_factor(region, region_bounds)
            factors.append(geographic_factor)
            
            # Economic factors
            economic_factor = self._calculate_economic_factor(region, economic_data)
            factors.append(economic_factor)
            
            # Political stability factor
            political_factor = self._calculate_political_stability_factor(region, political_data)
            factors.append(political_factor)
            
            # Infrastructure factor
            infrastructure_factor = self._calculate_infrastructure_factor(region, infrastructure_data)
            factors.append(infrastructure_factor)
            
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
                region=region,
                metadata={
                    "region_bounds": region_bounds,
                    "event_count": len(events),
                    "economic_indicators": list(economic_data.keys()),
                    "political_indicators": list(political_data.keys())
                }
            )
            
            return risk_score
            
        except Exception as e:
            logger.error(f"Regional risk calculation failed: {str(e)}")
            return RiskScore(
                overall_score=0.0,
                risk_level=RiskLevel.LOW,
                factors=[],
                confidence=0.0,
                calculated_at=datetime.utcnow(),
                region=data.get("region", "unknown")
            )
    
    def _calculate_event_density_factor(self, events: List[Event], region_bounds: Optional[Dict[str, float]]) -> RiskFactor:
        """Calculate risk factor based on event density"""
        if not events:
            return self._create_risk_factor(
                name="event_density",
                value=0.0,
                weight=self.weights["event_density"],
                description="No events in region",
                source="density_analysis"
            )
        
        # Calculate region area if bounds provided
        if region_bounds:
            area_km2 = self._calculate_region_area(region_bounds)
            if area_km2 > 0:
                density = len(events) / area_km2
                # Normalize density to 0-100 scale
                max_density = 10.0  # events per km²
                normalized_density = min(density / max_density, 1.0) * 100
            else:
                normalized_density = 0.0
        else:
            # Use simple event count normalization
            normalized_density = min(len(events) / 50, 1.0) * 100
        
        return self._create_risk_factor(
            name="event_density",
            value=normalized_density,
            weight=self.weights["event_density"],
            description=f"{len(events)} events in region",
            source="density_analysis",
            confidence=0.8 if region_bounds else 0.5
        )
    
    def _calculate_event_intensity_factor(self, events: List[Event]) -> RiskFactor:
        """Calculate risk factor based on event intensity"""
        if not events:
            return self._create_risk_factor(
                name="event_intensity",
                value=0.0,
                weight=self.weights["event_intensity"],
                description="No events to analyze",
                source="intensity_analysis"
            )
        
        # Calculate intensity based on severity and confidence
        intensity_scores = []
        for event in events:
            # Base intensity from severity
            severity_scores = {
                "low": 20.0,
                "medium": 50.0,
                "high": 80.0,
                "critical": 100.0
            }
            
            severity = event.severity.value if hasattr(event.severity, 'value') else str(event.severity)
            base_intensity = severity_scores.get(severity, 50.0)
            
            # Adjust by confidence
            adjusted_intensity = base_intensity * event.confidence
            intensity_scores.append(adjusted_intensity)
        
        avg_intensity = np.mean(intensity_scores)
        
        return self._create_risk_factor(
            name="event_intensity",
            value=avg_intensity,
            weight=self.weights["event_intensity"],
            description=f"Average intensity: {avg_intensity:.1f}",
            source="intensity_analysis",
            confidence=min(1.0, len(events) / 20)
        )
    
    def _calculate_geographic_risk_factor(self, region: str, region_bounds: Optional[Dict[str, float]]) -> RiskFactor:
        """Calculate risk factor based on geographic characteristics"""
        # Geographic risk factors (simplified)
        geographic_risks = {
            "middle_east": 80.0,
            "africa": 60.0,
            "asia": 40.0,
            "europe": 30.0,
            "americas": 35.0,
            "oceania": 20.0
        }
        
        # Try to match region to known risk areas
        region_lower = region.lower()
        base_risk = 50.0  # Default risk
        
        for risk_region, risk_score in geographic_risks.items():
            if risk_region in region_lower:
                base_risk = risk_score
                break
        
        # Adjust based on region size (smaller regions = higher risk concentration)
        if region_bounds:
            area = self._calculate_region_area(region_bounds)
            if area < self.region_size_threshold:
                base_risk *= 1.2  # Increase risk for smaller regions
            base_risk = min(base_risk, 100.0)
        
        return self._create_risk_factor(
            name="geographic_risk",
            value=base_risk,
            weight=self.weights["geographic_risk"],
            description=f"Geographic risk for {region}",
            source="geographic_analysis",
            confidence=0.7
        )
    
    def _calculate_economic_factor(self, region: str, economic_data: Dict[str, Any]) -> RiskFactor:
        """Calculate risk factor based on economic indicators"""
        if not economic_data:
            # Use default economic risk
            return self._create_risk_factor(
                name="economic_factors",
                value=50.0,
                weight=self.weights["economic_factors"],
                description="No economic data available",
                source="economic_analysis",
                confidence=0.3
            )
        
        # Calculate economic risk from indicators
        economic_risk = 50.0  # Base risk
        
        # GDP per capita (lower = higher risk)
        gdp_per_capita = economic_data.get("gdp_per_capita")
        if gdp_per_capita:
            if gdp_per_capita < 1000:
                economic_risk += 30
            elif gdp_per_capita < 5000:
                economic_risk += 20
            elif gdp_per_capita < 10000:
                economic_risk += 10
        
        # Inflation rate (higher = higher risk)
        inflation = economic_data.get("inflation_rate")
        if inflation:
            if inflation > 10:
                economic_risk += 25
            elif inflation > 5:
                economic_risk += 15
            elif inflation > 2:
                economic_risk += 5
        
        # Unemployment rate (higher = higher risk)
        unemployment = economic_data.get("unemployment_rate")
        if unemployment:
            if unemployment > 15:
                economic_risk += 20
            elif unemployment > 10:
                economic_risk += 10
            elif unemployment > 5:
                economic_risk += 5
        
        economic_risk = min(economic_risk, 100.0)
        
        return self._create_risk_factor(
            name="economic_factors",
            value=economic_risk,
            weight=self.weights["economic_factors"],
            description=f"Economic risk: {economic_risk:.1f}",
            source="economic_analysis",
            confidence=0.8
        )
    
    def _calculate_political_stability_factor(self, region: str, political_data: Dict[str, Any]) -> RiskFactor:
        """Calculate risk factor based on political stability"""
        if not political_data:
            # Use default political risk
            return self._create_risk_factor(
                name="political_stability",
                value=50.0,
                weight=self.weights["political_stability"],
                description="No political data available",
                source="political_analysis",
                confidence=0.3
            )
        
        # Calculate political risk from indicators
        political_risk = 50.0  # Base risk
        
        # Democracy index (lower = higher risk)
        democracy_index = political_data.get("democracy_index")
        if democracy_index:
            if democracy_index < 3:
                political_risk += 30
            elif democracy_index < 5:
                political_risk += 20
            elif democracy_index < 7:
                political_risk += 10
        
        # Corruption perception (higher = higher risk)
        corruption = political_data.get("corruption_index")
        if corruption:
            if corruption > 7:
                political_risk += 25
            elif corruption > 5:
                political_risk += 15
            elif corruption > 3:
                political_risk += 5
        
        # Political stability index (lower = higher risk)
        stability = political_data.get("political_stability")
        if stability:
            if stability < -2:
                political_risk += 25
            elif stability < 0:
                political_risk += 15
            elif stability < 1:
                political_risk += 5
        
        political_risk = min(political_risk, 100.0)
        
        return self._create_risk_factor(
            name="political_stability",
            value=political_risk,
            weight=self.weights["political_stability"],
            description=f"Political risk: {political_risk:.1f}",
            source="political_analysis",
            confidence=0.8
        )
    
    def _calculate_infrastructure_factor(self, region: str, infrastructure_data: Dict[str, Any]) -> RiskFactor:
        """Calculate risk factor based on infrastructure quality"""
        if not infrastructure_data:
            # Use default infrastructure risk
            return self._create_risk_factor(
                name="infrastructure",
                value=50.0,
                weight=self.weights["infrastructure"],
                description="No infrastructure data available",
                source="infrastructure_analysis",
                confidence=0.3
            )
        
        # Calculate infrastructure risk
        infrastructure_risk = 50.0  # Base risk
        
        # Internet penetration (lower = higher risk)
        internet_penetration = infrastructure_data.get("internet_penetration")
        if internet_penetration:
            if internet_penetration < 30:
                infrastructure_risk += 20
            elif internet_penetration < 60:
                infrastructure_risk += 10
        
        # Electricity access (lower = higher risk)
        electricity_access = infrastructure_data.get("electricity_access")
        if electricity_access:
            if electricity_access < 50:
                infrastructure_risk += 25
            elif electricity_access < 80:
                infrastructure_risk += 15
            elif electricity_access < 95:
                infrastructure_risk += 5
        
        # Road quality (lower = higher risk)
        road_quality = infrastructure_data.get("road_quality_index")
        if road_quality:
            if road_quality < 3:
                infrastructure_risk += 15
            elif road_quality < 4:
                infrastructure_risk += 10
            elif road_quality < 5:
                infrastructure_risk += 5
        
        infrastructure_risk = min(infrastructure_risk, 100.0)
        
        return self._create_risk_factor(
            name="infrastructure",
            value=infrastructure_risk,
            weight=self.weights["infrastructure"],
            description=f"Infrastructure risk: {infrastructure_risk:.1f}",
            source="infrastructure_analysis",
            confidence=0.7
        )
    
    def _calculate_region_area(self, bounds: Dict[str, float]) -> float:
        """Calculate area of region in km²"""
        try:
            from geopy.distance import geodesic
            
            # Calculate area using approximate formula
            lat_diff = bounds["north"] - bounds["south"]
            lon_diff = bounds["east"] - bounds["west"]
            
            # Convert to km (approximate)
            lat_km = lat_diff * 111.0  # 1 degree latitude ≈ 111 km
            lon_km = lon_diff * 111.0 * np.cos(np.radians((bounds["north"] + bounds["south"]) / 2))
            
            return lat_km * lon_km
        except Exception:
            return 0.0
    
    def get_regional_comparison(self, risk_scores: List[RiskScore]) -> Dict[str, Any]:
        """Compare risk scores across regions"""
        if not risk_scores:
            return {"comparison": "no_data"}
        
        # Sort by risk score
        sorted_scores = sorted(risk_scores, key=lambda x: x.overall_score, reverse=True)
        
        # Calculate statistics
        scores = [s.overall_score for s in risk_scores]
        
        return {
            "highest_risk_region": sorted_scores[0].region,
            "highest_risk_score": sorted_scores[0].overall_score,
            "lowest_risk_region": sorted_scores[-1].region,
            "lowest_risk_score": sorted_scores[-1].overall_score,
            "average_risk": np.mean(scores),
            "risk_std": np.std(scores),
            "total_regions": len(risk_scores),
            "rankings": [
                {"region": s.region, "score": s.overall_score, "level": s.risk_level.value}
                for s in sorted_scores
            ]
        }
