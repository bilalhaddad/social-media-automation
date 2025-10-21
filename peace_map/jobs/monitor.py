"""
Job monitoring and status tracking
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base import BaseJob, JobStatus
from .scheduler import JobScheduler


class JobMonitor:
    """Monitor and track job execution"""
    
    def __init__(self, scheduler: JobScheduler):
        self.scheduler = scheduler
        self.logger = logging.getLogger("job_monitor")
        self.metrics = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "cancelled_jobs": 0,
            "total_duration": 0.0,
            "average_duration": 0.0
        }
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        return self.scheduler.get_job_status(job_id)
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs"""
        return self.scheduler.get_all_jobs()
    
    def get_job_metrics(self) -> Dict[str, Any]:
        """Get job execution metrics"""
        jobs = self.get_all_jobs()
        
        # Calculate metrics
        total_jobs = len(jobs)
        completed_jobs = len([j for j in jobs if j["status"] == JobStatus.COMPLETED.value])
        failed_jobs = len([j for j in jobs if j["status"] == JobStatus.FAILED.value])
        cancelled_jobs = len([j for j in jobs if j["status"] == JobStatus.CANCELLED.value])
        
        # Calculate duration metrics
        durations = [j["duration"] for j in jobs if j["duration"] is not None]
        total_duration = sum(durations) if durations else 0.0
        average_duration = total_duration / len(durations) if durations else 0.0
        
        # Calculate success rate
        success_rate = completed_jobs / total_jobs if total_jobs > 0 else 0.0
        
        # Get recent jobs (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_jobs = [
            j for j in jobs 
            if j["created_at"] and datetime.fromisoformat(j["created_at"]) > cutoff_time
        ]
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "cancelled_jobs": cancelled_jobs,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "average_duration": average_duration,
            "recent_jobs": len(recent_jobs),
            "scheduled_jobs": len(self.scheduler.scheduled_jobs)
        }
    
    def get_job_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get job history for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        jobs = self.get_all_jobs()
        history = [
            j for j in jobs 
            if j["created_at"] and datetime.fromisoformat(j["created_at"]) > cutoff_time
        ]
        
        # Sort by creation time
        history.sort(key=lambda x: x["created_at"], reverse=True)
        
        return history
    
    def get_failed_jobs(self) -> List[Dict[str, Any]]:
        """Get all failed jobs"""
        jobs = self.get_all_jobs()
        return [j for j in jobs if j["status"] == JobStatus.FAILED.value]
    
    def get_running_jobs(self) -> List[Dict[str, Any]]:
        """Get all currently running jobs"""
        jobs = self.get_all_jobs()
        return [j for j in jobs if j["status"] == JobStatus.RUNNING.value]
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get all scheduled jobs"""
        return self.scheduler.get_scheduled_jobs()
    
    def get_job_performance(self, job_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for jobs"""
        jobs = self.get_all_jobs()
        
        if job_name:
            jobs = [j for j in jobs if j["name"] == job_name]
        
        if not jobs:
            return {"error": "No jobs found"}
        
        # Calculate performance metrics
        durations = [j["duration"] for j in jobs if j["duration"] is not None]
        
        if not durations:
            return {"error": "No duration data available"}
        
        durations.sort()
        
        return {
            "count": len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "average_duration": sum(durations) / len(durations),
            "median_duration": durations[len(durations) // 2],
            "p95_duration": durations[int(len(durations) * 0.95)],
            "p99_duration": durations[int(len(durations) * 0.99)]
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        metrics = self.get_job_metrics()
        failed_jobs = self.get_failed_jobs()
        running_jobs = self.get_running_jobs()
        
        # Determine health status
        if metrics["failed_jobs"] > metrics["completed_jobs"] * 0.1:  # More than 10% failure rate
            health_status = "unhealthy"
        elif len(failed_jobs) > 5:  # More than 5 failed jobs
            health_status = "degraded"
        else:
            health_status = "healthy"
        
        return {
            "status": health_status,
            "metrics": metrics,
            "failed_jobs_count": len(failed_jobs),
            "running_jobs_count": len(running_jobs),
            "scheduler_running": self.scheduler.running,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs"""
        self.scheduler.cleanup_completed_jobs(max_age_hours)
        self.logger.info(f"Cleaned up jobs older than {max_age_hours} hours")
    
    def get_job_summary(self) -> Dict[str, Any]:
        """Get a summary of job status"""
        metrics = self.get_job_metrics()
        health = self.get_health_status()
        recent_jobs = self.get_job_history(1)  # Last hour
        
        return {
            "health_status": health["status"],
            "metrics": metrics,
            "recent_activity": {
                "jobs_last_hour": len(recent_jobs),
                "success_rate": metrics["success_rate"]
            },
            "scheduler_status": {
                "running": self.scheduler.running,
                "scheduled_jobs": len(self.scheduler.scheduled_jobs)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
