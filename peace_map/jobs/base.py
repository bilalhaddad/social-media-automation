"""
Base job class for background processing
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BaseJob(ABC):
    """Base class for background jobs"""
    
    def __init__(self, job_id: str, name: str, **kwargs):
        self.job_id = job_id
        self.name = name
        self.status = JobStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.metadata = kwargs
        self.logger = logging.getLogger(f"job.{name}")
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """Execute the job logic"""
        pass
    
    def run(self) -> Dict[str, Any]:
        """Run the job with status tracking"""
        try:
            self.status = JobStatus.RUNNING
            self.started_at = datetime.utcnow()
            self.logger.info(f"Starting job {self.job_id}: {self.name}")
            
            # Execute the job
            result = self.execute()
            
            # Mark as completed
            self.status = JobStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            self.result = result
            
            duration = (self.completed_at - self.started_at).total_seconds()
            self.logger.info(f"Completed job {self.job_id} in {duration:.2f}s")
            
            return result
            
        except Exception as e:
            # Mark as failed
            self.status = JobStatus.FAILED
            self.completed_at = datetime.utcnow()
            self.error_message = str(e)
            
            duration = (self.completed_at - self.started_at).total_seconds() if self.started_at else 0
            self.logger.error(f"Failed job {self.job_id} after {duration:.2f}s: {e}")
            
            raise
    
    def cancel(self):
        """Cancel the job"""
        if self.status == JobStatus.RUNNING:
            self.status = JobStatus.CANCELLED
            self.completed_at = datetime.utcnow()
            self.logger.info(f"Cancelled job {self.job_id}")
    
    def get_duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.get_duration(),
            "error_message": self.error_message,
            "result": self.result,
            "metadata": self.metadata
        }
