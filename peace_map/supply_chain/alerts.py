"""
Supply chain alert management for Peace Map platform
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from .base import BaseSupplyChainManager, SupplyChainAlert, AlertStatus

logger = logging.getLogger(__name__)


class SupplyChainAlertManager(BaseSupplyChainManager):
    """Manages supply chain alerts and notifications"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("alert_manager", config)
        self.alerts: List[SupplyChainAlert] = []
        self.alert_thresholds = config.get("alert_thresholds", {
            "high_risk": 70.0,
            "critical_risk": 90.0,
            "supplier_disruption": 80.0
        })
        self.alert_retention_days = config.get("alert_retention_days", 90)
        self.auto_resolve_hours = config.get("auto_resolve_hours", 24)
    
    async def initialize(self):
        """Initialize the alert manager"""
        try:
            self.is_initialized = True
            logger.info("Supply chain alert manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize alert manager: {str(e)}")
            raise
    
    async def process_suppliers(self, suppliers: List[Dict[str, Any]]) -> List[SupplyChainAlert]:
        """Process suppliers and generate alerts"""
        alerts = []
        
        for supplier_data in suppliers:
            try:
                # Check for risk-based alerts
                risk_alerts = self._check_risk_alerts(supplier_data)
                alerts.extend(risk_alerts)
                
                # Check for status-based alerts
                status_alerts = self._check_status_alerts(supplier_data)
                alerts.extend(status_alerts)
                
                # Check for location-based alerts
                location_alerts = self._check_location_alerts(supplier_data)
                alerts.extend(location_alerts)
                
            except Exception as e:
                logger.error(f"Error processing supplier alerts: {str(e)}")
                continue
        
        # Add alerts to storage
        self.alerts.extend(alerts)
        
        # Clean up old alerts
        await self._cleanup_old_alerts()
        
        logger.info(f"Generated {len(alerts)} alerts")
        return alerts
    
    def _check_risk_alerts(self, supplier_data: Dict[str, Any]) -> List[SupplyChainAlert]:
        """Check for risk-based alerts"""
        alerts = []
        supplier_id = supplier_data.get("id", "unknown")
        supplier_name = supplier_data.get("name", "Unknown Supplier")
        risk_score = supplier_data.get("risk_score", 0.0)
        
        # High risk alert
        if risk_score >= self.alert_thresholds["high_risk"]:
            alert = SupplyChainAlert(
                id=str(uuid.uuid4()),
                supplier_id=supplier_id,
                alert_type="high_risk",
                severity="high",
                message=f"High risk detected for supplier {supplier_name}: {risk_score:.1f}",
                risk_score=risk_score,
                status=AlertStatus.ACTIVE,
                created_at=datetime.utcnow(),
                metadata={
                    "supplier_name": supplier_name,
                    "threshold": self.alert_thresholds["high_risk"]
                }
            )
            alerts.append(alert)
        
        # Critical risk alert
        if risk_score >= self.alert_thresholds["critical_risk"]:
            alert = SupplyChainAlert(
                id=str(uuid.uuid4()),
                supplier_id=supplier_id,
                alert_type="critical_risk",
                severity="critical",
                message=f"CRITICAL risk detected for supplier {supplier_name}: {risk_score:.1f}",
                risk_score=risk_score,
                status=AlertStatus.ACTIVE,
                created_at=datetime.utcnow(),
                metadata={
                    "supplier_name": supplier_name,
                    "threshold": self.alert_thresholds["critical_risk"]
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_status_alerts(self, supplier_data: Dict[str, Any]) -> List[SupplyChainAlert]:
        """Check for status-based alerts"""
        alerts = []
        supplier_id = supplier_data.get("id", "unknown")
        supplier_name = supplier_data.get("name", "Unknown Supplier")
        status = supplier_data.get("status", "active")
        
        # Suspended supplier alert
        if status == "suspended":
            alert = SupplyChainAlert(
                id=str(uuid.uuid4()),
                supplier_id=supplier_id,
                alert_type="supplier_suspended",
                severity="high",
                message=f"Supplier {supplier_name} has been suspended",
                risk_score=80.0,
                status=AlertStatus.ACTIVE,
                created_at=datetime.utcnow(),
                metadata={
                    "supplier_name": supplier_name,
                    "previous_status": "active"
                }
            )
            alerts.append(alert)
        
        # Inactive supplier alert
        elif status == "inactive":
            alert = SupplyChainAlert(
                id=str(uuid.uuid4()),
                supplier_id=supplier_id,
                alert_type="supplier_inactive",
                severity="medium",
                message=f"Supplier {supplier_name} is inactive",
                risk_score=60.0,
                status=AlertStatus.ACTIVE,
                created_at=datetime.utcnow(),
                metadata={
                    "supplier_name": supplier_name
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_location_alerts(self, supplier_data: Dict[str, Any]) -> List[SupplyChainAlert]:
        """Check for location-based alerts"""
        alerts = []
        supplier_id = supplier_data.get("id", "unknown")
        supplier_name = supplier_data.get("name", "Unknown Supplier")
        country = supplier_data.get("country", "")
        
        # High-risk country alert
        high_risk_countries = ["iran", "north korea", "syria", "russia", "china"]
        if country.lower() in high_risk_countries:
            alert = SupplyChainAlert(
                id=str(uuid.uuid4()),
                supplier_id=supplier_id,
                alert_type="high_risk_country",
                severity="high",
                message=f"Supplier {supplier_name} is located in high-risk country: {country}",
                risk_score=75.0,
                status=AlertStatus.ACTIVE,
                created_at=datetime.utcnow(),
                metadata={
                    "supplier_name": supplier_name,
                    "country": country,
                    "risk_reason": "high_risk_country"
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def create_alert(self, supplier_id: str, alert_type: str, severity: str, 
                    message: str, risk_score: float = 0.0, metadata: Dict[str, Any] = None) -> SupplyChainAlert:
        """Create a new alert"""
        alert = SupplyChainAlert(
            id=str(uuid.uuid4()),
            supplier_id=supplier_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            risk_score=risk_score,
            status=AlertStatus.ACTIVE,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self.alerts.append(alert)
        logger.info(f"Created alert: {alert_type} for supplier {supplier_id}")
        
        return alert
    
    def get_alert(self, alert_id: str) -> Optional[SupplyChainAlert]:
        """Get alert by ID"""
        for alert in self.alerts:
            if alert.id == alert_id:
                return alert
        return None
    
    def get_alerts_by_supplier(self, supplier_id: str) -> List[SupplyChainAlert]:
        """Get alerts for a specific supplier"""
        return [a for a in self.alerts if a.supplier_id == supplier_id]
    
    def get_alerts_by_type(self, alert_type: str) -> List[SupplyChainAlert]:
        """Get alerts by type"""
        return [a for a in self.alerts if a.alert_type == alert_type]
    
    def get_alerts_by_severity(self, severity: str) -> List[SupplyChainAlert]:
        """Get alerts by severity"""
        return [a for a in self.alerts if a.severity == severity]
    
    def get_active_alerts(self) -> List[SupplyChainAlert]:
        """Get active (unresolved) alerts"""
        return [a for a in self.alerts if a.status == AlertStatus.ACTIVE]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        alert = self.get_alert(alert_id)
        if not alert:
            return False
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        
        logger.info(f"Alert {alert_id} acknowledged")
        return True
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        alert = self.get_alert(alert_id)
        if not alert:
            return False
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        
        logger.info(f"Alert {alert_id} resolved")
        return True
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        if not self.alerts:
            return {"total_alerts": 0}
        
        # Count by status
        status_counts = {}
        for alert in self.alerts:
            status = alert.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by type
        type_counts = {}
        for alert in self.alerts:
            alert_type = alert.alert_type
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
        
        # Count by severity
        severity_counts = {}
        for alert in self.alerts:
            severity = alert.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Recent alerts (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_alerts = [a for a in self.alerts if a.created_at >= recent_cutoff]
        
        # Active alerts
        active_alerts = [a for a in self.alerts if a.status == AlertStatus.ACTIVE]
        
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len(active_alerts),
            "recent_alerts_24h": len(recent_alerts),
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "severity_distribution": severity_counts,
            "alert_rate_24h": len(recent_alerts),
            "resolution_rate": len([a for a in self.alerts if a.status == AlertStatus.RESOLVED]) / len(self.alerts) if self.alerts else 0
        }
    
    def get_supplier_alert_summary(self, supplier_id: str) -> Dict[str, Any]:
        """Get alert summary for a specific supplier"""
        supplier_alerts = self.get_alerts_by_supplier(supplier_id)
        
        if not supplier_alerts:
            return {"supplier_id": supplier_id, "total_alerts": 0}
        
        # Count by status
        status_counts = {}
        for alert in supplier_alerts:
            status = alert.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by severity
        severity_counts = {}
        for alert in supplier_alerts:
            severity = alert.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Recent alerts
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent_alerts = [a for a in supplier_alerts if a.created_at >= recent_cutoff]
        
        return {
            "supplier_id": supplier_id,
            "total_alerts": len(supplier_alerts),
            "active_alerts": len([a for a in supplier_alerts if a.status == AlertStatus.ACTIVE]),
            "recent_alerts_7d": len(recent_alerts),
            "status_distribution": status_counts,
            "severity_distribution": severity_counts,
            "last_alert": max(supplier_alerts, key=lambda a: a.created_at).created_at.isoformat() if supplier_alerts else None
        }
    
    async def _cleanup_old_alerts(self):
        """Clean up old alerts"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.alert_retention_days)
        
        # Mark old alerts as expired
        for alert in self.alerts:
            if alert.created_at < cutoff_date and alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.EXPIRED
        
        # Remove expired alerts
        self.alerts = [a for a in self.alerts if a.status != AlertStatus.EXPIRED]
    
    def get_alert_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get alert trends over time"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_alerts = [a for a in self.alerts if a.created_at >= cutoff_date]
        
        if not recent_alerts:
            return {"trend": "no_data"}
        
        # Group by day
        daily_counts = {}
        for alert in recent_alerts:
            date_key = alert.created_at.date().isoformat()
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        # Calculate trend
        dates = sorted(daily_counts.keys())
        if len(dates) >= 2:
            recent_count = daily_counts[dates[-1]]
            older_count = daily_counts[dates[0]]
            trend = "increasing" if recent_count > older_count else "decreasing" if recent_count < older_count else "stable"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "total_alerts": len(recent_alerts),
            "daily_counts": daily_counts,
            "average_daily": len(recent_alerts) / days,
            "period_days": days
        }
    
    def export_alerts(self, format: str = "json") -> str:
        """Export alerts data"""
        if format == "json":
            import json
            
            export_data = {
                "alerts": [
                    {
                        "id": a.id,
                        "supplier_id": a.supplier_id,
                        "alert_type": a.alert_type,
                        "severity": a.severity,
                        "message": a.message,
                        "risk_score": a.risk_score,
                        "status": a.status.value,
                        "created_at": a.created_at.isoformat(),
                        "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                        "metadata": a.metadata
                    }
                    for a in self.alerts
                ],
                "export_timestamp": datetime.utcnow().isoformat(),
                "total_alerts": len(self.alerts)
            }
            
            return json.dumps(export_data, indent=2)
        
        return ""
