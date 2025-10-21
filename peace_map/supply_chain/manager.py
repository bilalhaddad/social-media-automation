"""
Supply chain management system for Peace Map platform
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseSupplyChainManager, Supplier, SupplyChainAlert
from .supplier import SupplierManager
from .upload import CSVUploadManager
from .alerts import SupplyChainAlertManager
from .analytics import SupplyChainAnalytics

logger = logging.getLogger(__name__)


class SupplyChainManager:
    """Main supply chain management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.supplier_manager = SupplierManager(config.get("supplier", {}))
        self.upload_manager = CSVUploadManager(config.get("upload", {}))
        self.alert_manager = SupplyChainAlertManager(config.get("alerts", {}))
        self.analytics = SupplyChainAnalytics(config.get("analytics", {}))
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize all supply chain components"""
        try:
            # Initialize all managers
            await asyncio.gather(
                self.supplier_manager.initialize(),
                self.upload_manager.initialize(),
                self.alert_manager.initialize(),
                self.analytics.initialize()
            )
            
            self.is_initialized = True
            logger.info("Supply chain manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize supply chain manager: {str(e)}")
            raise
    
    async def upload_suppliers_csv(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Upload and process suppliers from CSV file"""
        try:
            # Process CSV file
            upload_result = await self.upload_manager.process_csv_file(file_content, filename)
            
            if not upload_result["success"]:
                return {
                    "success": False,
                    "error": upload_result["error"],
                    "suppliers_processed": 0
                }
            
            # Process suppliers through supplier manager
            suppliers = upload_result["suppliers"]
            processed_suppliers = await self.supplier_manager.process_suppliers([
                {
                    "id": s.id,
                    "name": s.name,
                    "country": s.country,
                    "region": s.region,
                    "city": s.city,
                    "latitude": s.latitude,
                    "longitude": s.longitude,
                    "industry": s.industry,
                    "status": s.status.value,
                    "risk_score": s.risk_score,
                    "risk_level": s.risk_level,
                    "contact_email": s.contact_email,
                    "contact_phone": s.contact_phone,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat(),
                    "metadata": s.metadata
                }
                for s in suppliers
            ])
            
            # Generate alerts for new suppliers
            alerts = await self.alert_manager.process_suppliers([
                {
                    "id": s.id,
                    "name": s.name,
                    "country": s.country,
                    "risk_score": s.risk_score,
                    "status": s.status.value
                }
                for s in processed_suppliers
            ])
            
            # Update analytics data
            self.analytics.set_data(
                self.supplier_manager.suppliers,
                self.alert_manager.alerts
            )
            
            return {
                "success": True,
                "suppliers_processed": len(processed_suppliers),
                "alerts_generated": len(alerts),
                "total_suppliers": len(self.supplier_manager.suppliers),
                "active_alerts": len([a for a in self.alert_manager.alerts if a.status.value == "active"])
            }
            
        except Exception as e:
            logger.error(f"CSV upload failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "suppliers_processed": 0
            }
    
    def get_suppliers(self, filters: Dict[str, Any] = None) -> List[Supplier]:
        """Get suppliers with optional filters"""
        suppliers = self.supplier_manager.suppliers
        
        if not filters:
            return suppliers
        
        # Apply filters
        filtered_suppliers = []
        
        for supplier in suppliers:
            # Country filter
            if "country" in filters and supplier.country != filters["country"]:
                continue
            
            # Region filter
            if "region" in filters and supplier.region != filters["region"]:
                continue
            
            # Industry filter
            if "industry" in filters and supplier.industry != filters["industry"]:
                continue
            
            # Risk level filter
            if "risk_level" in filters and supplier.risk_level != filters["risk_level"]:
                continue
            
            # Status filter
            if "status" in filters and supplier.status.value != filters["status"]:
                continue
            
            # Risk score range filter
            if "min_risk_score" in filters and supplier.risk_score < filters["min_risk_score"]:
                continue
            
            if "max_risk_score" in filters and supplier.risk_score > filters["max_risk_score"]:
                continue
            
            filtered_suppliers.append(supplier)
        
        return filtered_suppliers
    
    def get_supplier(self, supplier_id: str) -> Optional[Supplier]:
        """Get supplier by ID"""
        return self.supplier_manager.get_supplier(supplier_id)
    
    def update_supplier_risk(self, supplier_id: str, risk_score: float) -> bool:
        """Update supplier risk score"""
        success = self.supplier_manager.update_supplier_risk(supplier_id, risk_score)
        
        if success:
            # Update analytics data
            self.analytics.set_data(
                self.supplier_manager.suppliers,
                self.alert_manager.alerts
            )
        
        return success
    
    def get_alerts(self, filters: Dict[str, Any] = None) -> List[SupplyChainAlert]:
        """Get alerts with optional filters"""
        alerts = self.alert_manager.alerts
        
        if not filters:
            return alerts
        
        # Apply filters
        filtered_alerts = []
        
        for alert in alerts:
            # Supplier ID filter
            if "supplier_id" in filters and alert.supplier_id != filters["supplier_id"]:
                continue
            
            # Alert type filter
            if "alert_type" in filters and alert.alert_type != filters["alert_type"]:
                continue
            
            # Severity filter
            if "severity" in filters and alert.severity != filters["severity"]:
                continue
            
            # Status filter
            if "status" in filters and alert.status.value != filters["status"]:
                continue
            
            # Date range filter
            if "start_date" in filters and alert.created_at < filters["start_date"]:
                continue
            
            if "end_date" in filters and alert.created_at > filters["end_date"]:
                continue
            
            filtered_alerts.append(alert)
        
        return filtered_alerts
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        return self.alert_manager.acknowledge_alert(alert_id)
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        return self.alert_manager.resolve_alert(alert_id)
    
    def get_supply_chain_overview(self) -> Dict[str, Any]:
        """Get supply chain overview"""
        # Update analytics data
        self.analytics.set_data(
            self.supplier_manager.suppliers,
            self.alert_manager.alerts
        )
        
        return self.analytics.get_supply_chain_overview()
    
    def get_supplier_analytics(self, supplier_id: str) -> Dict[str, Any]:
        """Get analytics for a specific supplier"""
        # Update analytics data
        self.analytics.set_data(
            self.supplier_manager.suppliers,
            self.alert_manager.alerts
        )
        
        return self.analytics.get_supplier_risk_analysis(supplier_id)
    
    def get_supply_chain_insights(self) -> Dict[str, Any]:
        """Get supply chain insights"""
        # Update analytics data
        self.analytics.set_data(
            self.supplier_manager.suppliers,
            self.alert_manager.alerts
        )
        
        return self.analytics.get_supply_chain_insights()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        supplier_stats = self.supplier_manager.get_supplier_statistics()
        alert_stats = self.alert_manager.get_alert_statistics()
        
        return {
            "suppliers": supplier_stats,
            "alerts": alert_stats,
            "overview": self.get_supply_chain_overview(),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def get_upload_requirements(self) -> Dict[str, Any]:
        """Get CSV upload requirements"""
        return self.upload_manager.get_upload_requirements()
    
    def get_csv_template(self) -> str:
        """Get CSV template for supplier upload"""
        return self.upload_manager.get_csv_template()
    
    def export_suppliers(self, format: str = "json") -> str:
        """Export suppliers data"""
        return self.supplier_manager.export_suppliers(format)
    
    def export_alerts(self, format: str = "json") -> str:
        """Export alerts data"""
        return self.alert_manager.export_alerts(format)
    
    def search_suppliers(self, query: str) -> List[Supplier]:
        """Search suppliers"""
        return self.supplier_manager.search_suppliers(query)
    
    def get_suppliers_at_risk(self, threshold: float = 70.0) -> List[Supplier]:
        """Get suppliers at risk"""
        return self.supplier_manager.get_suppliers_at_risk(threshold)
    
    def get_active_alerts(self) -> List[SupplyChainAlert]:
        """Get active alerts"""
        return self.alert_manager.get_active_alerts()
    
    def get_supplier_alerts(self, supplier_id: str) -> List[SupplyChainAlert]:
        """Get alerts for a specific supplier"""
        return self.alert_manager.get_alerts_by_supplier(supplier_id)
    
    def get_alert_summary(self, supplier_id: str) -> Dict[str, Any]:
        """Get alert summary for a supplier"""
        return self.alert_manager.get_supplier_alert_summary(supplier_id)
    
    def get_geographic_distribution(self) -> Dict[str, Any]:
        """Get geographic distribution of suppliers"""
        return self.supplier_manager.get_supplier_geographic_distribution()
    
    def get_industry_distribution(self) -> Dict[str, Any]:
        """Get industry distribution of suppliers"""
        # This would be implemented in the analytics module
        return self.analytics._calculate_industry_distribution()
    
    def get_risk_distribution(self) -> Dict[str, Any]:
        """Get risk distribution of suppliers"""
        return self.analytics._calculate_risk_distribution()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        return {
            "initialized": self.is_initialized,
            "supplier_manager": self.supplier_manager.get_status(),
            "upload_manager": self.upload_manager.get_status(),
            "alert_manager": self.alert_manager.get_status(),
            "analytics": self.analytics.get_status(),
            "total_suppliers": len(self.supplier_manager.suppliers),
            "total_alerts": len(self.alert_manager.alerts),
            "active_alerts": len([a for a in self.alert_manager.alerts if a.status.value == "active"])
        }
