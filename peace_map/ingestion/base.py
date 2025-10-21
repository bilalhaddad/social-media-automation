"""
Base ingestion connector for Peace Map platform
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class EventCategory(str, Enum):
    """Event categories for classification"""
    PROTEST = "protest"
    CYBER = "cyber"
    KINETIC = "kinetic"
    ECONOMIC = "economic"
    ENVIRONMENTAL = "environmental"
    POLITICAL = "political"
    UNKNOWN = "unknown"


class EventSeverity(str, Enum):
    """Event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Event:
    """Standardized event data structure"""
    id: str
    title: str
    description: str
    source: str
    source_url: Optional[str]
    published_at: datetime
    location: Optional[Dict[str, Any]]  # {"lat": float, "lon": float, "country": str, "region": str}
    category: EventCategory
    severity: EventSeverity
    confidence: float  # 0.0 to 1.0
    raw_data: Dict[str, Any]
    tags: List[str]
    language: str = "en"
    sentiment_score: Optional[float] = None
    embedding: Optional[List[float]] = None


class BaseIngestionConnector(ABC):
    """Abstract base class for data ingestion connectors"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.last_update: Optional[datetime] = None
        self.is_enabled = config.get("enabled", True)
        self.update_interval = config.get("update_interval", 3600)  # 1 hour default
        self.retry_attempts = config.get("retry_attempts", 3)
        self.retry_delay = config.get("retry_delay", 60)
    
    @abstractmethod
    async def fetch_events(self, since: Optional[datetime] = None) -> List[Event]:
        """
        Fetch events from the data source
        
        Args:
            since: Only fetch events after this timestamp
            
        Returns:
            List of Event objects
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate connector configuration
        
        Returns:
            True if configuration is valid
        """
        pass
    
    def should_update(self) -> bool:
        """
        Check if connector should update based on interval
        
        Returns:
            True if update is needed
        """
        if not self.last_update:
            return True
        
        time_since_update = (datetime.utcnow() - self.last_update).total_seconds()
        return time_since_update >= self.update_interval
    
    async def update_last_fetch_time(self):
        """Update the last fetch timestamp"""
        self.last_update = datetime.utcnow()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get connector status information
        
        Returns:
            Dictionary with status information
        """
        return {
            "name": self.name,
            "enabled": self.is_enabled,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "update_interval": self.update_interval,
            "should_update": self.should_update()
        }
    
    def _normalize_event_data(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw event data to standard format
        
        Args:
            raw_event: Raw event data from source
            
        Returns:
            Normalized event data
        """
        # This method can be overridden by subclasses for specific normalization
        return raw_event
    
    def _extract_location(self, raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract location information from raw event data
        
        Args:
            raw_event: Raw event data
            
        Returns:
            Location dictionary or None
        """
        # Default implementation - subclasses should override
        return None
    
    def _classify_event(self, title: str, description: str) -> EventCategory:
        """
        Classify event into category based on content
        
        Args:
            title: Event title
            description: Event description
            
        Returns:
            Event category
        """
        # Simple keyword-based classification
        # In production, this would use ML models
        content = f"{title} {description}".lower()
        
        if any(keyword in content for keyword in ["protest", "demonstration", "rally", "strike"]):
            return EventCategory.PROTEST
        elif any(keyword in content for keyword in ["cyber", "hack", "breach", "malware"]):
            return EventCategory.CYBER
        elif any(keyword in content for keyword in ["attack", "bomb", "violence", "conflict"]):
            return EventCategory.KINETIC
        elif any(keyword in content for keyword in ["economic", "financial", "market", "trade"]):
            return EventCategory.ECONOMIC
        elif any(keyword in content for keyword in ["environment", "climate", "disaster", "flood"]):
            return EventCategory.ENVIRONMENTAL
        elif any(keyword in content for keyword in ["political", "election", "government", "policy"]):
            return EventCategory.POLITICAL
        else:
            return EventCategory.UNKNOWN
    
    def _assess_severity(self, title: str, description: str) -> EventSeverity:
        """
        Assess event severity based on content
        
        Args:
            title: Event title
            description: Event description
            
        Returns:
            Event severity level
        """
        # Simple keyword-based severity assessment
        content = f"{title} {description}".lower()
        
        critical_keywords = ["death", "killed", "casualties", "crisis", "emergency", "critical"]
        high_keywords = ["attack", "violence", "conflict", "threat", "danger"]
        medium_keywords = ["incident", "disruption", "concern", "warning"]
        
        if any(keyword in content for keyword in critical_keywords):
            return EventSeverity.CRITICAL
        elif any(keyword in content for keyword in high_keywords):
            return EventSeverity.HIGH
        elif any(keyword in content for keyword in medium_keywords):
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW
    
    def _calculate_confidence(self, raw_event: Dict[str, Any]) -> float:
        """
        Calculate confidence score for event
        
        Args:
            raw_event: Raw event data
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Simple confidence calculation based on available data
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on data completeness
        if raw_event.get("title"):
            confidence += 0.1
        if raw_event.get("description"):
            confidence += 0.1
        if raw_event.get("location"):
            confidence += 0.1
        if raw_event.get("source_url"):
            confidence += 0.1
        if raw_event.get("published_at"):
            confidence += 0.1
        
        return min(confidence, 1.0)
