"""
Base NLP processor for Peace Map platform
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProcessingStatus(str, Enum):
    """Status of NLP processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingResult:
    """Result of NLP processing operation"""
    status: ProcessingStatus
    data: Any
    confidence: float
    metadata: Dict[str, Any]
    error: Optional[str] = None


class BaseNLPProcessor(ABC):
    """Abstract base class for NLP processors"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_initialized = False
        self.model = None
    
    @abstractmethod
    async def initialize(self):
        """Initialize the NLP processor"""
        pass
    
    @abstractmethod
    async def process(self, text: str, **kwargs) -> ProcessingResult:
        """
        Process text data
        
        Args:
            text: Input text to process
            **kwargs: Additional processing parameters
            
        Returns:
            ProcessingResult with processed data
        """
        pass
    
    @abstractmethod
    async def process_batch(self, texts: List[str], **kwargs) -> List[ProcessingResult]:
        """
        Process multiple texts in batch
        
        Args:
            texts: List of input texts
            **kwargs: Additional processing parameters
            
        Returns:
            List of ProcessingResult objects
        """
        pass
    
    def validate_config(self) -> bool:
        """Validate processor configuration"""
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get processor status"""
        return {
            "name": self.name,
            "initialized": self.is_initialized,
            "config": self.config
        }
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text before processing"""
        if not text:
            return ""
        
        # Basic text cleaning
        text = text.strip()
        
        # Remove extra whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _calculate_confidence(self, result_data: Any, metadata: Dict[str, Any]) -> float:
        """Calculate confidence score for processing result"""
        # Default confidence calculation
        # Subclasses should override for specific confidence metrics
        return 0.8
    
    def _create_result(self, status: ProcessingStatus, data: Any, confidence: float = None, metadata: Dict[str, Any] = None, error: str = None) -> ProcessingResult:
        """Create a processing result"""
        if confidence is None:
            confidence = self._calculate_confidence(data, metadata or {})
        
        return ProcessingResult(
            status=status,
            data=data,
            confidence=confidence,
            metadata=metadata or {},
            error=error
        )
