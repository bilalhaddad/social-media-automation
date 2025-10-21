"""
Job scheduler for background processing
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from .base import BaseJob, JobStatus


class JobScheduler:
    """Scheduler for background jobs"""
    
    def __init__(self):
        self.jobs: Dict[str, BaseJob] = {}
        self.scheduled_jobs: Dict[str, Dict] = {}
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger("scheduler")
    
    def add_job(self, job: BaseJob) -> str:
        """Add a job to the scheduler"""
        self.jobs[job.job_id] = job
        self.logger.info(f"Added job {job.job_id}: {job.name}")
        return job.job_id
    
    def schedule_job(self, job_id: str, interval_seconds: int, 
                    start_time: Optional[datetime] = None) -> bool:
        """Schedule a job to run at intervals"""
        if job_id not in self.jobs:
            self.logger.error(f"Job {job_id} not found")
            return False
        
        self.scheduled_jobs[job_id] = {
            "interval": interval_seconds,
            "next_run": start_time or datetime.utcnow(),
            "last_run": None
        }
        
        self.logger.info(f"Scheduled job {job_id} to run every {interval_seconds}s")
        return True
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("Job scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        self.logger.info("Job scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Check for jobs that need to run
                for job_id, schedule in self.scheduled_jobs.items():
                    if current_time >= schedule["next_run"]:
                        self._run_scheduled_job(job_id)
                        schedule["last_run"] = current_time
                        schedule["next_run"] = current_time + timedelta(seconds=schedule["interval"])
                
                # Sleep for a short interval
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)
    
    def _run_scheduled_job(self, job_id: str):
        """Run a scheduled job"""
        try:
            job = self.jobs[job_id]
            
            # Skip if job is already running
            if job.status == JobStatus.RUNNING:
                self.logger.warning(f"Job {job_id} is already running, skipping")
                return
            
            # Create a new instance for scheduled runs
            new_job = type(job)(f"{job_id}_{int(time.time())}", job.name, **job.metadata)
            self.jobs[new_job.job_id] = new_job
            
            # Run in a separate thread
            thread = threading.Thread(target=new_job.run, daemon=True)
            thread.start()
            
            self.logger.info(f"Started scheduled job {new_job.job_id}")
            
        except Exception as e:
            self.logger.error(f"Error running scheduled job {job_id}: {e}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status"""
        if job_id in self.jobs:
            return self.jobs[job_id].to_dict()
        return None
    
    def get_all_jobs(self) -> List[Dict]:
        """Get all jobs"""
        return [job.to_dict() for job in self.jobs.values()]
    
    def get_scheduled_jobs(self) -> List[Dict]:
        """Get scheduled jobs"""
        result = []
        for job_id, schedule in self.scheduled_jobs.items():
            job_info = self.get_job_status(job_id)
            if job_info:
                job_info["schedule"] = schedule
                result.append(job_info)
        return result
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        if job_id in self.jobs:
            self.jobs[job_id].cancel()
            return True
        return False
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job from scheduler"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            if job_id in self.scheduled_jobs:
                del self.scheduled_jobs[job_id]
            return True
        return False
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] 
                and job.completed_at and job.completed_at < cutoff_time):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            self.remove_job(job_id)
        
        if jobs_to_remove:
            self.logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
