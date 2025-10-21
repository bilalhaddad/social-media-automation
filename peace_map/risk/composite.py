"""
Composite risk calculator for Peace Map platform
"""

import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .base import BaseRiskCalculator, RiskScore, RiskFactor, RiskLevel
from ..ingestion.base import Event

logger = logging.getLogger(__name__)


class CompositeRiskCalculator(BaseRiskCalculator):
    """Calculates composite risk scores using multiple factors"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("composite", config)
        
        # Default weights for different risk factors
        self.default_weights = {
            "event_count": 0.3,
            "sentiment": 0.25,
            "proximity_to_ports": 0.2,
            "event_severity": 0.15,
            "temporal_decay": 0.1
        }
        
        # Merge with config weights
        self.weights.update(self.default_weights)
        
        # Risk calculation parameters
        self.max_events_per_region = config.get("max_events_per_region", 100)
        self.sentiment_weight_negative = config.get("sentiment_weight_negative", 1.5)
        self.port_proximity_threshold = config.get("port_proximity_threshold", 50.0)  # km
        self.temporal_decay_factor = config.get("temporal_decay_factor", 0.95)
    
    async def initialize(self):
        """Initialize the composite risk calculator"""
        try:
            self.is_initialized = True
            logger.info("Composite risk calculator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize composite risk calculator: {str(e)}")
            raise
    
    async def calculate_risk(self, data: Dict[str, Any], **kwargs) -> RiskScore:
        """Calculate composite risk score"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Extract data
            events = data.get("events", [])
            region = data.get("region", "unknown")
            port_locations = data.get("port_locations", [])
            time_window_days = data.get("time_window_days", 30)
            
            # Calculate individual risk factors
            factors = []
            
            # Event count factor
            event_count_factor = self._calculate_event_count_factor(events, time_window_days)
            factors.append(event_count_factor)
            
            # Sentiment factor
            sentiment_factor = self._calculate_sentiment_factor(events)
            factors.append(sentiment_factor)
            
            # Proximity to ports factor
            proximity_factor = self._calculate_proximity_factor(events, port_locations)
            factors.append(proximity_factor)
            
            # Event severity factor
            severity_factor = self._calculate_severity_factor(events)
            factors.append(severity_factor)
            
            # Temporal decay factor
            temporal_factor = self._calculate_temporal_factor(events, time_window_days)
            factors.append(temporal_factor)
            
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
                    "time_window_days": time_window_days,
                    "event_count": len(events),
                    "port_count": len(port_locations)
                }
            )
            
            return risk_score
            
        except Exception as e:
            logger.error(f"Risk calculation failed: {str(e)}")
            # Return minimal risk score on error
            return RiskScore(
                overall_score=0.0,
                risk_level=RiskLevel.LOW,
                factors=[],
                confidence=0.0,
                calculated_at=datetime.utcnow(),
                region=data.get("region", "unknown")
            )
    
    def _calculate_event_count_factor(self, events: List[Event], time_window_days: int) -> RiskFactor:
        """Calculate risk factor based on event count"""
        if not events:
            return self._create_risk_factor(
                name="event_count",
                value=0.0,
                weight=self.weights["event_count"],
                description="No events in time window",
                source="event_analysis"
            )
        
        # Filter events by time window
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
        recent_events = [e for e in events if e.published_at >= cutoff_date]
        
        # Calculate normalized event count score
        max_events = self.max_events_per_region
        event_count = len(recent_events)
        normalized_count = min(event_count / max_events, 1.0) * 100
        
        # Apply confidence based on data quality
        confidence = min(1.0, event_count / 10)  # Higher confidence with more events
        
        return self._create_risk_factor(
            name="event_count",
            value=normalized_count,
            weight=self.weights["event_count"],
            description=f"{event_count} events in {time_window_days} days",
            source="event_analysis",
            confidence=confidence
        )
    
    def _calculate_sentiment_factor(self, events: List[Event]) -> RiskFactor:
        """Calculate risk factor based on sentiment analysis"""
        if not events:
            return self._create_risk_factor(
                name="sentiment",
                value=0.0,
                weight=self.weights["sentiment"],
                description="No sentiment data",
                source="sentiment_analysis"
            )
        
        # Calculate average sentiment
        sentiment_scores = []
        for event in events:
            if hasattr(event, 'sentiment_score') and event.sentiment_score is not None:
                sentiment_scores.append(event.sentiment_score)
        
        if not sentiment_scores:
            return self._create_risk_factor(
                name="sentiment",
                value=50.0,  # Neutral sentiment
                weight=self.weights["sentiment"],
                description="No sentiment data available",
                source="sentiment_analysis",
                confidence=0.3
            )
        
        avg_sentiment = np.mean(sentiment_scores)
        
        # Convert sentiment to risk score (negative sentiment = higher risk)
        if avg_sentiment < 0:
            sentiment_risk = abs(avg_sentiment) * 100 * self.sentiment_weight_negative
        else:
            sentiment_risk = (1 - avg_sentiment) * 50  # Positive sentiment reduces risk
        
        sentiment_risk = min(sentiment_risk, 100.0)
        
        return self._create_risk_factor(
            name="sentiment",
            value=sentiment_risk,
            weight=self.weights["sentiment"],
            description=f"Average sentiment: {avg_sentiment:.2f}",
            source="sentiment_analysis",
            confidence=min(1.0, len(sentiment_scores) / 20)  # Higher confidence with more data
        )
    
    def _calculate_proximity_factor(self, events: List[Event], port_locations: List[Dict[str, Any]]) -> RiskFactor:
        """Calculate risk factor based on proximity to ports"""
        if not events or not port_locations:
            return self._create_risk_factor(
                name="proximity_to_ports",
                value=0.0,
                weight=self.weights["proximity_to_ports"],
                description="No proximity data available",
                source="geospatial_analysis"
            )
        
        # Calculate proximity scores for each event
        proximity_scores = []
        
        for event in events:
            if not event.location or not event.location.get("lat") or not event.location.get("lon"):
                continue
            
            event_lat = event.location["lat"]
            event_lon = event.location["lon"]
            
            # Find nearest port
            min_distance = float('inf')
            for port in port_locations:
                if "lat" in port and "lon" in port:
                    try:
                        from geopy.distance import geodesic
                        distance = geodesic(
                            (event_lat, event_lon),
                            (port["lat"], port["lon"])
                        ).kilometers
                        min_distance = min(min_distance, distance)
                    except Exception:
                        continue
            
            if min_distance != float('inf'):
                # Convert distance to risk score (closer = higher risk)
                if min_distance <= self.port_proximity_threshold:
                    proximity_score = (self.port_proximity_threshold - min_distance) / self.port_proximity_threshold * 100
                    proximity_scores.append(proximity_score)
        
        if not proximity_scores:
            return self._create_risk_factor(
                name="proximity_to_ports",
                value=0.0,
                weight=self.weights["proximity_to_ports"],
                description="No events near ports",
                source="geospatial_analysis"
            )
        
        avg_proximity_risk = np.mean(proximity_scores)
        
        return self._create_risk_factor(
            name="proximity_to_ports",
            value=avg_proximity_risk,
            weight=self.weights["proximity_to_ports"],
            description=f"Average proximity risk: {avg_proximity_risk:.1f}",
            source="geospatial_analysis",
            confidence=min(1.0, len(proximity_scores) / 10)
        )
    
    def _calculate_severity_factor(self, events: List[Event]) -> RiskFactor:
        """Calculate risk factor based on event severity"""
        if not events:
            return self._create_risk_factor(
                name="event_severity",
                value=0.0,
                weight=self.weights["event_severity"],
                description="No events to analyze",
                source="severity_analysis"
            )
        
        # Map severity levels to numeric scores
        severity_scores = {
            "low": 20.0,
            "medium": 50.0,
            "high": 80.0,
            "critical": 100.0
        }
        
        event_severities = []
        for event in events:
            severity = event.severity.value if hasattr(event.severity, 'value') else str(event.severity)
            if severity in severity_scores:
                event_severities.append(severity_scores[severity])
        
        if not event_severities:
            return self._create_risk_factor(
                name="event_severity",
                value=0.0,
                weight=self.weights["event_severity"],
                description="No severity data available",
                source="severity_analysis",
                confidence=0.3
            )
        
        # Calculate weighted average severity
        avg_severity = np.mean(event_severities)
        
        return self._create_risk_factor(
            name="event_severity",
            value=avg_severity,
            weight=self.weights["event_severity"],
            description=f"Average severity: {avg_severity:.1f}",
            source="severity_analysis",
            confidence=min(1.0, len(event_severities) / 20)
        )
    
    def _calculate_temporal_factor(self, events: List[Event], time_window_days: int) -> RiskFactor:
        """Calculate risk factor based on temporal patterns"""
        if not events:
            return self._create_risk_factor(
                name="temporal_decay",
                value=0.0,
                weight=self.weights["temporal_decay"],
                description="No temporal data",
                source="temporal_analysis"
            )
        
        # Calculate temporal decay for recent events
        now = datetime.utcnow()
        temporal_scores = []
        
        for event in events:
            days_old = (now - event.published_at).days
            decayed_score = self._apply_temporal_decay(100.0, days_old, self.temporal_decay_factor)
            temporal_scores.append(decayed_score)
        
        avg_temporal_risk = np.mean(temporal_scores)
        
        return self._create_risk_factor(
            name="temporal_decay",
            value=avg_temporal_risk,
            weight=self.weights["temporal_decay"],
            description=f"Temporal decay applied to {len(events)} events",
            source="temporal_analysis",
            confidence=min(1.0, len(events) / 50)
        )
    
    def get_risk_breakdown(self, risk_score: RiskScore) -> Dict[str, Any]:
        """Get detailed breakdown of risk factors"""
        breakdown = {
            "overall_score": risk_score.overall_score,
            "risk_level": risk_score.risk_level.value,
            "confidence": risk_score.confidence,
            "factors": []
        }
        
        for factor in risk_score.factors:
            factor_breakdown = {
                "name": factor.name,
                "value": factor.value,
                "weight": factor.weight,
                "weighted_contribution": factor.value * factor.weight,
                "description": factor.description,
                "source": factor.source,
                "confidence": factor.confidence
            }
            breakdown["factors"].append(factor_breakdown)
        
        return breakdown
    
    def get_risk_trends(self, historical_scores: List[RiskScore]) -> Dict[str, Any]:
        """Analyze risk trends over time"""
        if len(historical_scores) < 2:
            return {"trend": "insufficient_data"}
        
        # Sort by calculation time
        sorted_scores = sorted(historical_scores, key=lambda x: x.calculated_at)
        
        # Calculate trend
        recent_scores = [s.overall_score for s in sorted_scores[-5:]]  # Last 5 scores
        if len(recent_scores) >= 2:
            trend_direction = "increasing" if recent_scores[-1] > recent_scores[0] else "decreasing"
            trend_magnitude = abs(recent_scores[-1] - recent_scores[0])
        else:
            trend_direction = "stable"
            trend_magnitude = 0.0
        
        return {
            "trend": trend_direction,
            "magnitude": trend_magnitude,
            "recent_scores": recent_scores,
            "average_score": np.mean([s.overall_score for s in sorted_scores]),
            "max_score": max(s.overall_score for s in sorted_scores),
            "min_score": min(s.overall_score for s in sorted_scores)
        }
