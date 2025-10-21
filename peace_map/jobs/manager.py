"""
Job manager for coordinating background jobs
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .scheduler import JobScheduler
from .monitor import JobMonitor
from .refresh import DataRefreshJob
from .anomaly import AnomalyDetectionJob


class JobManager:
    """Manager for all background jobs"""
    
    def __init__(self):
        self.scheduler = JobScheduler()
        self.monitor = JobMonitor(self.scheduler)
        self.logger = logging.getLogger("job_manager")
        
        # Initialize default jobs
        self._setup_default_jobs()
    
    def _setup_default_jobs(self):
        """Setup default background jobs"""
        # Hourly data refresh job
        refresh_job = DataRefreshJob(
            job_id="hourly_refresh",
            name="hourly_data_refresh",
            refresh_type="incremental"
        )
        self.scheduler.add_job(refresh_job)
        self.scheduler.schedule_job("hourly_refresh", 3600)  # Every hour
        
        # Daily full refresh job
        daily_refresh_job = DataRefreshJob(
            job_id="daily_refresh",
            name="daily_full_refresh",
            refresh_type="full"
        )
        self.scheduler.add_job(daily_refresh_job)
        self.scheduler.schedule_job("daily_refresh", 86400)  # Every 24 hours
        
        # Anomaly detection job
        anomaly_job = AnomalyDetectionJob(
            job_id="anomaly_detection",
            name="anomaly_detection",
            data_source="risk_index"
        )
        self.scheduler.add_job(anomaly_job)
        self.scheduler.schedule_job("anomaly_detection", 7200)  # Every 2 hours
        
        self.logger.info("Default jobs configured")
    
    def start(self):
        """Start the job manager"""
        self.scheduler.start()
        self.logger.info("Job manager started")
    
    def stop(self):
        """Stop the job manager"""
        self.scheduler.stop()
        self.logger.info("Job manager stopped")
    
    def add_job(self, job: BaseJob, schedule_interval: Optional[int] = None) -> str:
        """Add a job to the manager"""
        job_id = self.scheduler.add_job(job)
        
        if schedule_interval:
            self.scheduler.schedule_job(job_id, schedule_interval)
        
        self.logger.info(f"Added job {job_id}: {job.name}")
        return job_id
    
    def run_job_now(self, job_id: str) -> bool:
        """Run a job immediately"""
        job = self.scheduler.jobs.get(job_id)
        if not job:
            self.logger.error(f"Job {job_id} not found")
            return False
        
        # Create a new instance for immediate execution
        new_job = type(job)(f"{job_id}_{int(datetime.utcnow().timestamp())}", job.name, **job.metadata)
        self.scheduler.add_job(new_job)
        
        # Run in a separate thread
        import threading
        thread = threading.Thread(target=new_job.run, daemon=True)
        thread.start()
        
        self.logger.info(f"Started immediate job {new_job.job_id}")
        return True
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        return self.monitor.get_job_status(job_id)
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs"""
        return self.monitor.get_all_jobs()
    
    def get_job_metrics(self) -> Dict[str, Any]:
        """Get job execution metrics"""
        return self.monitor.get_job_metrics()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        return self.monitor.get_health_status()
    
    def get_job_summary(self) -> Dict[str, Any]:
        """Get job summary"""
        return self.monitor.get_job_summary()
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        return self.scheduler.cancel_job(job_id)
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job"""
        return self.scheduler.remove_job(job_id)
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old jobs"""
        self.monitor.cleanup_old_jobs(max_age_hours)
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get scheduled jobs"""
        return self.monitor.get_scheduled_jobs()
    
    def get_failed_jobs(self) -> List[Dict[str, Any]]:
        """Get failed jobs"""
        return self.monitor.get_failed_jobs()
    
    def get_running_jobs(self) -> List[Dict[str, Any]]:
        """Get running jobs"""
        return self.monitor.get_running_jobs()
    
    def create_custom_refresh_job(self, refresh_type: str = "custom", 
                                 components: List[str] = None) -> str:
        """Create a custom refresh job"""
        job_id = f"custom_refresh_{uuid.uuid4().hex[:8]}"
        
        job = DataRefreshJob(
            job_id=job_id,
            name=f"custom_{refresh_type}_refresh",
            refresh_type=refresh_type,
            components=components or []
        )
        
        return self.add_job(job)
    
    def create_anomaly_detection_job(self, data_source: str) -> str:
        """Create an anomaly detection job"""
        job_id = f"anomaly_{uuid.uuid4().hex[:8]}"
        
        job = AnomalyDetectionJob(
            job_id=job_id,
            name=f"anomaly_detection_{data_source}",
            data_source=data_source
        )
        
        return self.add_job(job)
    
    def get_job_performance(self, job_name: Optional[str] = None) -> Dict[str, Any]:
        """Get job performance metrics"""
        return self.monitor.get_job_performance(job_name)
    
    def get_job_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get job history"""
        return self.monitor.get_job_history(hours)
    
    def is_healthy(self) -> bool:
        """Check if the job system is healthy"""
        health = self.get_health_status()
        return health["status"] in ["healthy", "degraded"]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        return {
            "job_manager": {
                "running": self.scheduler.running,
                "healthy": self.is_healthy()
            },
            "scheduler": {
                "running": self.scheduler.running,
                "scheduled_jobs": len(self.scheduler.scheduled_jobs)
            },
            "monitor": self.get_job_summary(),
            "timestamp": datetime.utcnow().isoformat()
        }
