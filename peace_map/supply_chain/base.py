"""
Base supply chain management for Peace Map platform
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SupplierStatus(str, Enum):
    """Supplier status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class AlertStatus(str, Enum):
    """Alert status enumeration"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    EXPIRED = "expired"


@dataclass
class Supplier:
    """Supplier data structure"""
    id: str
    name: str
    country: str
    region: str
    city: str
    latitude: float
    longitude: float
    industry: str
    status: SupplierStatus
    risk_score: float
    risk_level: str
    contact_email: str
    contact_phone: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SupplyChainAlert:
    """Supply chain alert data structure"""
    id: str
    supplier_id: str
    alert_type: str
    severity: str
    message: str
    risk_score: float
    status: AlertStatus
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseSupplyChainManager(ABC):
    """Abstract base class for supply chain management"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self):
        """Initialize the supply chain manager"""
        pass
    
    @abstractmethod
    async def process_suppliers(self, suppliers: List[Dict[str, Any]]) -> List[Supplier]:
        """
        Process supplier data
        
        Args:
            suppliers: List of supplier data dictionaries
            
        Returns:
            List of processed Supplier objects
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get manager status"""
        return {
            "name": self.name,
            "initialized": self.is_initialized,
            "config": self.config
        }
    
    def _validate_supplier_data(self, supplier_data: Dict[str, Any]) -> bool:
        """Validate supplier data"""
        required_fields = ["name", "country", "latitude", "longitude"]
        
        for field in required_fields:
            if field not in supplier_data or not supplier_data[field]:
                return False
        
        # Validate coordinates
        try:
            lat = float(supplier_data["latitude"])
            lon = float(supplier_data["longitude"])
            
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return False
        except (ValueError, TypeError):
            return False
        
        return True
    
    def _normalize_supplier_data(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize supplier data"""
        normalized = supplier_data.copy()
        
        # Normalize coordinates
        if "latitude" in normalized:
            normalized["latitude"] = float(normalized["latitude"])
        if "longitude" in normalized:
            normalized["longitude"] = float(normalized["longitude"])
        
        # Normalize strings
        string_fields = ["name", "country", "region", "city", "industry", "contact_email", "contact_phone"]
        for field in string_fields:
            if field in normalized:
                normalized[field] = str(normalized[field]).strip()
        
        # Set defaults
        normalized.setdefault("status", SupplierStatus.ACTIVE.value)
        normalized.setdefault("risk_score", 0.0)
        normalized.setdefault("risk_level", "low")
        normalized.setdefault("created_at", datetime.utcnow().isoformat())
        normalized.setdefault("updated_at", datetime.utcnow().isoformat())
        
        return normalized
    
    def _calculate_risk_level(self, risk_score: float) -> str:
        """Calculate risk level from score"""
        if risk_score >= 80:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"
