"""
Risk management system for Peace Map platform
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .base import BaseRiskCalculator, RiskScore, RiskLevel
from .composite import CompositeRiskCalculator
from .regional import RegionalRiskCalculator
from .supplier import SupplierRiskCalculator
from .anomaly import AnomalyDetector

logger = logging.getLogger(__name__)


@dataclass
class RiskAlert:
    """Risk alert data structure"""
    id: str
    region: str
    risk_score: float
    risk_level: RiskLevel
    alert_type: str
    message: str
    created_at: datetime
    acknowledged: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RiskManager:
    """Manages all risk calculation and alerting"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.calculators: Dict[str, BaseRiskCalculator] = {}
        self.alerts: List[RiskAlert] = []
        self.risk_history: List[RiskScore] = []
        self.is_initialized = False
        
        # Initialize calculators
        self._initialize_calculators()
    
    def _initialize_calculators(self):
        """Initialize all risk calculators"""
        calculator_configs = self.config.get("calculators", {})
        
        # Initialize composite risk calculator
        if calculator_configs.get("composite", {}).get("enabled", True):
            composite_config = calculator_configs.get("composite", {})
            self.calculators["composite"] = CompositeRiskCalculator(composite_config)
        
        # Initialize regional risk calculator
        if calculator_configs.get("regional", {}).get("enabled", True):
            regional_config = calculator_configs.get("regional", {})
            self.calculators["regional"] = RegionalRiskCalculator(regional_config)
        
        # Initialize supplier risk calculator
        if calculator_configs.get("supplier", {}).get("enabled", True):
            supplier_config = calculator_configs.get("supplier", {})
            self.calculators["supplier"] = SupplierRiskCalculator(supplier_config)
        
        # Initialize anomaly detector
        if calculator_configs.get("anomaly", {}).get("enabled", True):
            anomaly_config = calculator_configs.get("anomaly", {})
            self.calculators["anomaly"] = AnomalyDetector(anomaly_config)
        
        logger.info(f"Initialized {len(self.calculators)} risk calculators")
    
    async def initialize(self):
        """Initialize all calculators"""
        initialization_tasks = []
        
        for calculator in self.calculators.values():
            initialization_tasks.append(calculator.initialize())
        
        if initialization_tasks:
            await asyncio.gather(*initialization_tasks)
            self.is_initialized = True
            logger.info("Risk manager initialized")
    
    async def calculate_composite_risk(self, data: Dict[str, Any]) -> RiskScore:
        """Calculate composite risk score"""
        if "composite" not in self.calculators:
            raise ValueError("Composite risk calculator not available")
        
        calculator = self.calculators["composite"]
        risk_score = await calculator.calculate_risk(data)
        
        # Store in history
        self.risk_history.append(risk_score)
        
        # Check for alerts
        await self._check_risk_alerts(risk_score)
        
        return risk_score
    
    async def calculate_regional_risk(self, region: str, data: Dict[str, Any]) -> RiskScore:
        """Calculate regional risk score"""
        if "regional" not in self.calculators:
            raise ValueError("Regional risk calculator not available")
        
        data["region"] = region
        calculator = self.calculators["regional"]
        risk_score = await calculator.calculate_risk(data)
        
        # Store in history
        self.risk_history.append(risk_score)
        
        # Check for alerts
        await self._check_risk_alerts(risk_score)
        
        return risk_score
    
    async def calculate_supplier_risk(self, supplier_data: Dict[str, Any]) -> RiskScore:
        """Calculate supplier risk score"""
        if "supplier" not in self.calculators:
            raise ValueError("Supplier risk calculator not available")
        
        data = {"supplier": supplier_data}
        calculator = self.calculators["supplier"]
        risk_score = await calculator.calculate_risk(data)
        
        # Store in history
        self.risk_history.append(risk_score)
        
        # Check for alerts
        await self._check_risk_alerts(risk_score)
        
        return risk_score
    
    async def detect_anomalies(self, data: Dict[str, Any]) -> RiskScore:
        """Detect anomalies in risk patterns"""
        if "anomaly" not in self.calculators:
            raise ValueError("Anomaly detector not available")
        
        calculator = self.calculators["anomaly"]
        risk_score = await calculator.calculate_risk(data)
        
        # Store in history
        self.risk_history.append(risk_score)
        
        # Check for alerts
        await self._check_risk_alerts(risk_score)
        
        return risk_score
    
    async def calculate_all_risks(self, data: Dict[str, Any]) -> Dict[str, RiskScore]:
        """Calculate all types of risk scores"""
        results = {}
        
        # Calculate composite risk
        if "composite" in self.calculators:
            try:
                composite_risk = await self.calculate_composite_risk(data)
                results["composite"] = composite_risk
            except Exception as e:
                logger.error(f"Composite risk calculation failed: {str(e)}")
        
        # Calculate regional risk
        if "regional" in self.calculators and "region" in data:
            try:
                regional_risk = await self.calculate_regional_risk(data["region"], data)
                results["regional"] = regional_risk
            except Exception as e:
                logger.error(f"Regional risk calculation failed: {str(e)}")
        
        # Calculate supplier risk
        if "supplier" in self.calculators and "supplier" in data:
            try:
                supplier_risk = await self.calculate_supplier_risk(data["supplier"])
                results["supplier"] = supplier_risk
            except Exception as e:
                logger.error(f"Supplier risk calculation failed: {str(e)}")
        
        # Detect anomalies
        if "anomaly" in self.calculators:
            try:
                anomaly_risk = await self.detect_anomalies(data)
                results["anomaly"] = anomaly_risk
            except Exception as e:
                logger.error(f"Anomaly detection failed: {str(e)}")
        
        return results
    
    async def _check_risk_alerts(self, risk_score: RiskScore):
        """Check if risk score triggers alerts"""
        alert_thresholds = self.config.get("alert_thresholds", {
            "high": 70.0,
            "critical": 90.0
        })
        
        # Check for high risk alert
        if risk_score.overall_score >= alert_thresholds.get("high", 70.0):
            alert = RiskAlert(
                id=f"alert_{len(self.alerts)}_{datetime.utcnow().timestamp()}",
                region=risk_score.region or "unknown",
                risk_score=risk_score.overall_score,
                risk_level=risk_score.risk_level,
                alert_type="high_risk",
                message=f"High risk detected in {risk_score.region}: {risk_score.overall_score:.1f}",
                created_at=datetime.utcnow(),
                metadata={
                    "calculator": "composite",
                    "confidence": risk_score.confidence
                }
            )
            self.alerts.append(alert)
            logger.warning(f"High risk alert: {alert.message}")
        
        # Check for critical risk alert
        if risk_score.overall_score >= alert_thresholds.get("critical", 90.0):
            alert = RiskAlert(
                id=f"critical_{len(self.alerts)}_{datetime.utcnow().timestamp()}",
                region=risk_score.region or "unknown",
                risk_score=risk_score.overall_score,
                risk_level=risk_score.risk_level,
                alert_type="critical_risk",
                message=f"CRITICAL risk detected in {risk_score.region}: {risk_score.overall_score:.1f}",
                created_at=datetime.utcnow(),
                metadata={
                    "calculator": "composite",
                    "confidence": risk_score.confidence
                }
            )
            self.alerts.append(alert)
            logger.critical(f"Critical risk alert: {alert.message}")
    
    def get_risk_summary(self, region: str = None) -> Dict[str, Any]:
        """Get risk summary for region or overall"""
        if region:
            region_scores = [s for s in self.risk_history if s.region == region]
        else:
            region_scores = self.risk_history
        
        if not region_scores:
            return {"summary": "no_data"}
        
        # Calculate statistics
        scores = [s.overall_score for s in region_scores]
        risk_levels = [s.risk_level.value for s in region_scores]
        
        # Count by risk level
        level_counts = {}
        for level in risk_levels:
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Recent trends
        recent_scores = scores[-10:] if len(scores) >= 10 else scores
        trend = "stable"
        if len(recent_scores) >= 2:
            if recent_scores[-1] > recent_scores[0]:
                trend = "increasing"
            elif recent_scores[-1] < recent_scores[0]:
                trend = "decreasing"
        
        return {
            "total_assessments": len(region_scores),
            "average_risk": sum(scores) / len(scores),
            "max_risk": max(scores),
            "min_risk": min(scores),
            "risk_level_distribution": level_counts,
            "trend": trend,
            "recent_scores": recent_scores,
            "active_alerts": len([a for a in self.alerts if not a.acknowledged]),
            "last_assessment": region_scores[-1].calculated_at.isoformat() if region_scores else None
        }
    
    def get_active_alerts(self, region: str = None) -> List[RiskAlert]:
        """Get active (unacknowledged) alerts"""
        alerts = [a for a in self.alerts if not a.acknowledged]
        
        if region:
            alerts = [a for a in alerts if a.region == region]
        
        return alerts
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alert {alert_id} acknowledged")
                return True
        return False
    
    def get_risk_trends(self, region: str = None, days: int = 30) -> Dict[str, Any]:
        """Get risk trends over time"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        if region:
            region_scores = [s for s in self.risk_history if s.region == region and s.calculated_at >= cutoff_date]
        else:
            region_scores = [s for s in self.risk_history if s.calculated_at >= cutoff_date]
        
        if len(region_scores) < 2:
            return {"trend": "insufficient_data"}
        
        # Sort by date
        region_scores.sort(key=lambda x: x.calculated_at)
        
        # Calculate trend
        scores = [s.overall_score for s in region_scores]
        dates = [s.calculated_at for s in region_scores]
        
        # Simple linear trend
        from scipy import stats
        x = [(d - dates[0]).total_seconds() / 86400 for d in dates]  # Days since first
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, scores)
        
        trend_direction = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
        
        return {
            "trend": trend_direction,
            "slope": slope,
            "correlation": r_value,
            "p_value": p_value,
            "scores": scores,
            "dates": [d.isoformat() for d in dates],
            "period_days": days,
            "data_points": len(region_scores)
        }
    
    def get_calculator_status(self) -> Dict[str, Any]:
        """Get status of all calculators"""
        status = {}
        
        for name, calculator in self.calculators.items():
            status[name] = calculator.get_status()
        
        return status
    
    def get_risk_statistics(self) -> Dict[str, Any]:
        """Get overall risk statistics"""
        if not self.risk_history:
            return {"total_assessments": 0}
        
        # Calculate statistics
        scores = [s.overall_score for s in self.risk_history]
        regions = list(set(s.region for s in self.risk_history if s.region))
        
        # Risk level distribution
        level_counts = {}
        for score in self.risk_history:
            level = score.risk_level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Recent activity
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_assessments = [s for s in self.risk_history if s.calculated_at >= recent_cutoff]
        
        return {
            "total_assessments": len(self.risk_history),
            "unique_regions": len(regions),
            "average_risk": sum(scores) / len(scores),
            "max_risk": max(scores),
            "min_risk": min(scores),
            "risk_level_distribution": level_counts,
            "recent_assessments_24h": len(recent_assessments),
            "active_alerts": len([a for a in self.alerts if not a.acknowledged]),
            "total_alerts": len(self.alerts),
            "last_assessment": self.risk_history[-1].calculated_at.isoformat() if self.risk_history else None
        }
    
    async def train_anomaly_detector(self, historical_data: List[Dict[str, Any]]) -> bool:
        """Train the anomaly detector with historical data"""
        if "anomaly" not in self.calculators:
            logger.warning("Anomaly detector not available")
            return False
        
        anomaly_detector = self.calculators["anomaly"]
        return await anomaly_detector.train_model(historical_data)
    
    def export_risk_data(self, format: str = "json") -> str:
        """Export risk data in specified format"""
        if format == "json":
            import json
            
            export_data = {
                "risk_history": [
                    {
                        "overall_score": s.overall_score,
                        "risk_level": s.risk_level.value,
                        "region": s.region,
                        "confidence": s.confidence,
                        "calculated_at": s.calculated_at.isoformat(),
                        "factors": [
                            {
                                "name": f.name,
                                "value": f.value,
                                "weight": f.weight,
                                "description": f.description
                            }
                            for f in s.factors
                        ]
                    }
                    for s in self.risk_history
                ],
                "alerts": [
                    {
                        "id": a.id,
                        "region": a.region,
                        "risk_score": a.risk_score,
                        "risk_level": a.risk_level.value,
                        "alert_type": a.alert_type,
                        "message": a.message,
                        "created_at": a.created_at.isoformat(),
                        "acknowledged": a.acknowledged
                    }
                    for a in self.alerts
                ]
            }
            
            return json.dumps(export_data, indent=2)
        
        return ""
