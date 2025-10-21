"""
Supplier management for Peace Map platform
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .base import BaseSupplyChainManager, Supplier, SupplierStatus

logger = logging.getLogger(__name__)


class SupplierManager(BaseSupplyChainManager):
    """Manages supplier data and operations"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("supplier_manager", config)
        self.suppliers: List[Supplier] = []
        self.max_suppliers = config.get("max_suppliers", 1000)
        self.auto_geocode = config.get("auto_geocode", True)
    
    async def initialize(self):
        """Initialize the supplier manager"""
        try:
            self.is_initialized = True
            logger.info("Supplier manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize supplier manager: {str(e)}")
            raise
    
    async def process_suppliers(self, suppliers: List[Dict[str, Any]]) -> List[Supplier]:
        """Process supplier data"""
        processed_suppliers = []
        
        for supplier_data in suppliers:
            try:
                # Validate supplier data
                if not self._validate_supplier_data(supplier_data):
                    logger.warning(f"Invalid supplier data: {supplier_data}")
                    continue
                
                # Normalize data
                normalized_data = self._normalize_supplier_data(supplier_data)
                
                # Create supplier object
                supplier = self._create_supplier(normalized_data)
                processed_suppliers.append(supplier)
                
            except Exception as e:
                logger.error(f"Error processing supplier: {str(e)}")
                continue
        
        # Add to internal storage
        self.suppliers.extend(processed_suppliers)
        
        # Limit total suppliers
        if len(self.suppliers) > self.max_suppliers:
            # Keep most recent suppliers
            self.suppliers.sort(key=lambda s: s.created_at, reverse=True)
            self.suppliers = self.suppliers[:self.max_suppliers]
        
        logger.info(f"Processed {len(processed_suppliers)} suppliers")
        return processed_suppliers
    
    def _create_supplier(self, data: Dict[str, Any]) -> Supplier:
        """Create a Supplier object from data"""
        # Generate ID if not provided
        supplier_id = data.get("id", str(uuid.uuid4()))
        
        # Parse dates
        created_at = datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"]
        updated_at = datetime.fromisoformat(data["updated_at"]) if isinstance(data["updated_at"], str) else data["updated_at"]
        
        # Create supplier
        supplier = Supplier(
            id=supplier_id,
            name=data["name"],
            country=data["country"],
            region=data.get("region", ""),
            city=data.get("city", ""),
            latitude=data["latitude"],
            longitude=data["longitude"],
            industry=data.get("industry", ""),
            status=SupplierStatus(data.get("status", SupplierStatus.ACTIVE.value)),
            risk_score=data.get("risk_score", 0.0),
            risk_level=data.get("risk_level", "low"),
            contact_email=data.get("contact_email", ""),
            contact_phone=data.get("contact_phone", ""),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {})
        )
        
        return supplier
    
    def get_supplier(self, supplier_id: str) -> Optional[Supplier]:
        """Get supplier by ID"""
        for supplier in self.suppliers:
            if supplier.id == supplier_id:
                return supplier
        return None
    
    def get_suppliers_by_region(self, country: str = None, region: str = None) -> List[Supplier]:
        """Get suppliers by region"""
        filtered = []
        
        for supplier in self.suppliers:
            if country and supplier.country != country:
                continue
            if region and supplier.region != region:
                continue
            filtered.append(supplier)
        
        return filtered
    
    def get_suppliers_by_risk_level(self, risk_level: str) -> List[Supplier]:
        """Get suppliers by risk level"""
        return [s for s in self.suppliers if s.risk_level == risk_level]
    
    def get_suppliers_by_industry(self, industry: str) -> List[Supplier]:
        """Get suppliers by industry"""
        return [s for s in self.suppliers if s.industry == industry]
    
    def get_suppliers_at_risk(self, threshold: float = 70.0) -> List[Supplier]:
        """Get suppliers with risk score above threshold"""
        return [s for s in self.suppliers if s.risk_score >= threshold]
    
    def update_supplier_risk(self, supplier_id: str, risk_score: float) -> bool:
        """Update supplier risk score"""
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return False
        
        supplier.risk_score = risk_score
        supplier.risk_level = self._calculate_risk_level(risk_score)
        supplier.updated_at = datetime.utcnow()
        
        return True
    
    def update_supplier_status(self, supplier_id: str, status: SupplierStatus) -> bool:
        """Update supplier status"""
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return False
        
        supplier.status = status
        supplier.updated_at = datetime.utcnow()
        
        return True
    
    def delete_supplier(self, supplier_id: str) -> bool:
        """Delete supplier"""
        for i, supplier in enumerate(self.suppliers):
            if supplier.id == supplier_id:
                del self.suppliers[i]
                return True
        return False
    
    def get_supplier_statistics(self) -> Dict[str, Any]:
        """Get supplier statistics"""
        if not self.suppliers:
            return {"total_suppliers": 0}
        
        # Count by status
        status_counts = {}
        for supplier in self.suppliers:
            status = supplier.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by risk level
        risk_counts = {}
        for supplier in self.suppliers:
            risk_level = supplier.risk_level
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        # Count by country
        country_counts = {}
        for supplier in self.suppliers:
            country = supplier.country
            country_counts[country] = country_counts.get(country, 0) + 1
        
        # Count by industry
        industry_counts = {}
        for supplier in self.suppliers:
            industry = supplier.industry
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
        
        # Calculate risk statistics
        risk_scores = [s.risk_score for s in self.suppliers]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        max_risk = max(risk_scores) if risk_scores else 0.0
        min_risk = min(risk_scores) if risk_scores else 0.0
        
        # Count high-risk suppliers
        high_risk_count = len([s for s in self.suppliers if s.risk_score >= 70.0])
        
        return {
            "total_suppliers": len(self.suppliers),
            "status_distribution": status_counts,
            "risk_level_distribution": risk_counts,
            "country_distribution": country_counts,
            "industry_distribution": industry_counts,
            "risk_statistics": {
                "average_risk": round(avg_risk, 2),
                "max_risk": max_risk,
                "min_risk": min_risk,
                "high_risk_count": high_risk_count,
                "high_risk_percentage": round((high_risk_count / len(self.suppliers)) * 100, 1) if self.suppliers else 0
            }
        }
    
    def get_supplier_geographic_distribution(self) -> Dict[str, Any]:
        """Get geographic distribution of suppliers"""
        if not self.suppliers:
            return {"distribution": {}}
        
        # Group by country
        country_data = {}
        for supplier in self.suppliers:
            country = supplier.country
            if country not in country_data:
                country_data[country] = {
                    "count": 0,
                    "suppliers": [],
                    "avg_risk": 0.0,
                    "coordinates": []
                }
            
            country_data[country]["count"] += 1
            country_data[country]["suppliers"].append({
                "id": supplier.id,
                "name": supplier.name,
                "risk_score": supplier.risk_score,
                "risk_level": supplier.risk_level,
                "latitude": supplier.latitude,
                "longitude": supplier.longitude
            })
            country_data[country]["coordinates"].append([supplier.longitude, supplier.latitude])
        
        # Calculate average risk per country
        for country, data in country_data.items():
            risk_scores = [s["risk_score"] for s in data["suppliers"]]
            data["avg_risk"] = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        
        return {
            "distribution": country_data,
            "total_countries": len(country_data),
            "total_suppliers": len(self.suppliers)
        }
    
    def search_suppliers(self, query: str) -> List[Supplier]:
        """Search suppliers by name or industry"""
        query_lower = query.lower()
        results = []
        
        for supplier in self.suppliers:
            if (query_lower in supplier.name.lower() or 
                query_lower in supplier.industry.lower() or
                query_lower in supplier.country.lower()):
                results.append(supplier)
        
        return results
    
    def export_suppliers(self, format: str = "json") -> str:
        """Export suppliers data"""
        if format == "json":
            import json
            
            export_data = {
                "suppliers": [
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
                    for s in self.suppliers
                ],
                "export_timestamp": datetime.utcnow().isoformat(),
                "total_suppliers": len(self.suppliers)
            }
            
            return json.dumps(export_data, indent=2)
        
        return ""
    
    def get_supplier_risk_trends(self, supplier_id: str, days: int = 30) -> Dict[str, Any]:
        """Get risk trends for a specific supplier"""
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return {"error": "Supplier not found"}
        
        # This would typically come from historical data
        # For now, return current risk information
        return {
            "supplier_id": supplier_id,
            "supplier_name": supplier.name,
            "current_risk_score": supplier.risk_score,
            "current_risk_level": supplier.risk_level,
            "last_updated": supplier.updated_at.isoformat(),
            "trend": "stable",  # Would be calculated from historical data
            "note": "Historical trend analysis not yet implemented"
        }
