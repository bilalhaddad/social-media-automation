"""
Base risk calculator for Peace Map platform
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskFactor:
    """Individual risk factor"""
    name: str
    value: float
    weight: float
    description: str
    source: str
    confidence: float = 1.0


@dataclass
class RiskScore:
    """Risk score result"""
    overall_score: float
    risk_level: RiskLevel
    factors: List[RiskFactor]
    confidence: float
    calculated_at: datetime
    region: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseRiskCalculator(ABC):
    """Abstract base class for risk calculators"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.weights = config.get("weights", {})
        self.thresholds = config.get("thresholds", {
            "low": 30.0,
            "medium": 50.0,
            "high": 70.0,
            "critical": 90.0
        })
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self):
        """Initialize the risk calculator"""
        pass
    
    @abstractmethod
    async def calculate_risk(self, data: Dict[str, Any], **kwargs) -> RiskScore:
        """
        Calculate risk score
        
        Args:
            data: Input data for risk calculation
            **kwargs: Additional parameters
            
        Returns:
            RiskScore object
        """
        pass
    
    def get_risk_level(self, score: float) -> RiskLevel:
        """Get risk level from score"""
        if score >= self.thresholds["critical"]:
            return RiskLevel.CRITICAL
        elif score >= self.thresholds["high"]:
            return RiskLevel.HIGH
        elif score >= self.thresholds["medium"]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def normalize_score(self, score: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
        """Normalize score to 0-100 range"""
        return max(min_val, min(max_val, score))
    
    def calculate_weighted_score(self, factors: List[RiskFactor]) -> Tuple[float, float]:
        """Calculate weighted risk score and confidence"""
        if not factors:
            return 0.0, 0.0
        
        total_weight = sum(factor.weight for factor in factors)
        if total_weight == 0:
            return 0.0, 0.0
        
        weighted_score = sum(factor.value * factor.weight for factor in factors) / total_weight
        avg_confidence = sum(factor.confidence for factor in factors) / len(factors)
        
        return weighted_score, avg_confidence
    
    def get_status(self) -> Dict[str, Any]:
        """Get calculator status"""
        return {
            "name": self.name,
            "initialized": self.is_initialized,
            "weights": self.weights,
            "thresholds": self.thresholds
        }
    
    def _create_risk_factor(self, name: str, value: float, weight: float = 1.0, 
                          description: str = "", source: str = "", confidence: float = 1.0) -> RiskFactor:
        """Create a risk factor"""
        return RiskFactor(
            name=name,
            value=value,
            weight=weight,
            description=description,
            source=source,
            confidence=confidence
        )
    
    def _apply_temporal_decay(self, score: float, days_old: int, decay_factor: float = 0.95) -> float:
        """Apply temporal decay to risk score"""
        if days_old <= 0:
            return score
        
        decay = decay_factor ** days_old
        return score * decay
    
    def _calculate_confidence(self, factors: List[RiskFactor]) -> float:
        """Calculate overall confidence from factors"""
        if not factors:
            return 0.0
        
        # Weight confidence by factor importance
        total_weight = sum(factor.weight for factor in factors)
        if total_weight == 0:
            return 0.0
        
        weighted_confidence = sum(
            factor.confidence * factor.weight for factor in factors
        ) / total_weight
        
        return weighted_confidence
