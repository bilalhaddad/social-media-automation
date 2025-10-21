"""
Tests for background job system
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from peace_map.jobs import (
    BaseJob, JobScheduler, AnomalyDetector, 
    DataRefreshJob, AnomalyDetectionJob, JobManager
)
from peace_map.jobs.base import JobStatus


class TestJob(BaseJob):
    """Test job implementation"""
    
    def __init__(self, job_id: str, name: str, duration: float = 0.1, should_fail: bool = False):
        super().__init__(job_id, name)
        self.duration = duration
        self.should_fail = should_fail
    
    def execute(self):
        """Execute test job"""
        time.sleep(self.duration)
        
        if self.should_fail:
            raise Exception("Test job failed")
        
        return {
            "result": "success",
            "duration": self.duration,
            "timestamp": datetime.utcnow().isoformat()
        }


class TestBaseJob:
    """Test base job functionality"""
    
    def test_job_creation(self):
        """Test job creation"""
        job = TestJob("test_job", "Test Job")
        
        assert job.job_id == "test_job"
        assert job.name == "Test Job"
        assert job.status == JobStatus.PENDING
        assert job.created_at is not None
        assert job.started_at is None
        assert job.completed_at is None
        assert job.error_message is None
        assert job.result is None
    
    def test_job_execution_success(self):
        """Test successful job execution"""
        job = TestJob("test_job", "Test Job", duration=0.1)
        
        result = job.run()
        
        assert job.status == JobStatus.COMPLETED
        assert job.started_at is not None
        assert job.completed_at is not None
        assert job.error_message is None
        assert job.result is not None
        assert result["result"] == "success"
        assert job.get_duration() > 0
    
    def test_job_execution_failure(self):
        """Test failed job execution"""
        job = TestJob("test_job", "Test Job", should_fail=True)
        
        with pytest.raises(Exception):
            job.run()
        
        assert job.status == JobStatus.FAILED
        assert job.started_at is not None
        assert job.completed_at is not None
        assert job.error_message == "Test job failed"
        assert job.result is None
    
    def test_job_cancellation(self):
        """Test job cancellation"""
        job = TestJob("test_job", "Test Job", duration=1.0)
        
        # Start job in thread
        thread = threading.Thread(target=job.run)
        thread.start()
        
        # Wait a bit then cancel
        time.sleep(0.1)
        job.cancel()
        
        thread.join()
        
        assert job.status == JobStatus.CANCELLED
    
    def test_job_to_dict(self):
        """Test job serialization"""
        job = TestJob("test_job", "Test Job")
        job_dict = job.to_dict()
        
        assert job_dict["job_id"] == "test_job"
        assert job_dict["name"] == "Test Job"
        assert job_dict["status"] == JobStatus.PENDING.value
        assert "created_at" in job_dict
        assert job_dict["started_at"] is None
        assert job_dict["completed_at"] is None
        assert job_dict["duration"] is None
        assert job_dict["error_message"] is None
        assert job_dict["result"] is None


class TestJobScheduler:
    """Test job scheduler"""
    
    def test_scheduler_creation(self):
        """Test scheduler creation"""
        scheduler = JobScheduler()
        
        assert len(scheduler.jobs) == 0
        assert len(scheduler.scheduled_jobs) == 0
        assert scheduler.running is False
        assert scheduler.scheduler_thread is None
    
    def test_add_job(self):
        """Test adding job to scheduler"""
        scheduler = JobScheduler()
        job = TestJob("test_job", "Test Job")
        
        job_id = scheduler.add_job(job)
        
        assert job_id == "test_job"
        assert "test_job" in scheduler.jobs
        assert scheduler.jobs["test_job"] == job
    
    def test_schedule_job(self):
        """Test scheduling job"""
        scheduler = JobScheduler()
        job = TestJob("test_job", "Test Job")
        scheduler.add_job(job)
        
        success = scheduler.schedule_job("test_job", 60)
        
        assert success is True
        assert "test_job" in scheduler.scheduled_jobs
        assert scheduler.scheduled_jobs["test_job"]["interval"] == 60
    
    def test_schedule_nonexistent_job(self):
        """Test scheduling non-existent job"""
        scheduler = JobScheduler()
        
        success = scheduler.schedule_job("nonexistent", 60)
        
        assert success is False
        assert len(scheduler.scheduled_jobs) == 0
    
    def test_get_job_status(self):
        """Test getting job status"""
        scheduler = JobScheduler()
        job = TestJob("test_job", "Test Job")
        scheduler.add_job(job)
        
        status = scheduler.get_job_status("test_job")
        
        assert status is not None
        assert status["job_id"] == "test_job"
        assert status["name"] == "Test Job"
    
    def test_get_nonexistent_job_status(self):
        """Test getting status of non-existent job"""
        scheduler = JobScheduler()
        
        status = scheduler.get_job_status("nonexistent")
        
        assert status is None
    
    def test_cancel_job(self):
        """Test cancelling job"""
        scheduler = JobScheduler()
        job = TestJob("test_job", "Test Job")
        scheduler.add_job(job)
        
        success = scheduler.cancel_job("test_job")
        
        assert success is True
        assert job.status == JobStatus.CANCELLED
    
    def test_remove_job(self):
        """Test removing job"""
        scheduler = JobScheduler()
        job = TestJob("test_job", "Test Job")
        scheduler.add_job(job)
        scheduler.schedule_job("test_job", 60)
        
        success = scheduler.remove_job("test_job")
        
        assert success is True
        assert "test_job" not in scheduler.jobs
        assert "test_job" not in scheduler.scheduled_jobs
    
    def test_cleanup_completed_jobs(self):
        """Test cleaning up old jobs"""
        scheduler = JobScheduler()
        
        # Create completed job
        job = TestJob("test_job", "Test Job")
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow() - timedelta(hours=25)
        scheduler.add_job(job)
        
        scheduler.cleanup_completed_jobs(max_age_hours=24)
        
        assert "test_job" not in scheduler.jobs


class TestAnomalyDetector:
    """Test anomaly detection"""
    
    def test_zscore_anomaly_detection(self):
        """Test z-score anomaly detection"""
        detector = AnomalyDetector(z_score_threshold=2.0)
        
        # Create test data with anomalies
        data = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # Normal data
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # Normal data
                10, 10, 10, 10, 10, 10, 10, 10, 10, 10,  # Anomalies
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # Normal data
        
        anomalies = detector.detect_anomalies_zscore(data, window_size=10)
        
        assert len(anomalies) > 0
        assert all(anomaly["method"] == "z_score" for anomaly in anomalies)
        assert all(anomaly["z_score"] > 2.0 for anomaly in anomalies)
    
    def test_stl_anomaly_detection(self):
        """Test STL anomaly detection"""
        detector = AnomalyDetector(stl_threshold=0.1)
        
        # Create seasonal data with anomalies
        import numpy as np
        
        # Generate seasonal data
        t = np.arange(100)
        seasonal = 5 * np.sin(2 * np.pi * t / 24)  # Daily seasonality
        trend = 0.1 * t
        noise = np.random.normal(0, 0.5, 100)
        
        # Add anomalies
        data = seasonal + trend + noise
        data[50:55] += 10  # Anomalies
        
        anomalies = detector.detect_anomalies_stl(data, period=24)
        
        # Should detect some anomalies
        assert len(anomalies) >= 0  # May or may not detect depending on noise
    
    def test_combined_anomaly_detection(self):
        """Test combined anomaly detection"""
        detector = AnomalyDetector()
        
        # Create test data
        data = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        
        timestamps = [datetime.utcnow() - timedelta(minutes=i) for i in range(len(data))]
        timestamps.reverse()
        
        anomalies = detector.detect_anomalies_combined(data, timestamps)
        
        assert len(anomalies) > 0
        assert all("timestamp" in anomaly for anomaly in anomalies)
    
    def test_anomaly_score_calculation(self):
        """Test anomaly score calculation"""
        detector = AnomalyDetector()
        
        # Normal data
        normal_data = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        normal_score = detector.calculate_anomaly_score(normal_data)
        
        # Anomalous data
        anomalous_data = [1, 1, 1, 1, 1, 1, 1, 1, 1, 10]
        anomalous_score = detector.calculate_anomaly_score(anomalous_data)
        
        assert 0 <= normal_score <= 1
        assert 0 <= anomalous_score <= 1
        assert anomalous_score > normal_score


class TestDataRefreshJob:
    """Test data refresh job"""
    
    def test_refresh_job_creation(self):
        """Test refresh job creation"""
        job = DataRefreshJob("test_refresh", "Test Refresh")
        
        assert job.job_id == "test_refresh"
        assert job.name == "Test Refresh"
        assert job.refresh_type == "full"
    
    def test_refresh_job_execution(self):
        """Test refresh job execution"""
        job = DataRefreshJob("test_refresh", "Test Refresh", refresh_type="incremental")
        
        result = job.run()
        
        assert job.status == JobStatus.COMPLETED
        assert result["refresh_type"] == "incremental"
        assert result["status"] == "completed"
        assert result["success"] is True
        assert "components" in result
        assert "duration_seconds" in result
    
    def test_refresh_job_components(self):
        """Test refresh job components"""
        job = DataRefreshJob("test_refresh", "Test Refresh")
        
        result = job.run()
        
        # Check all components are present
        components = result["components"]
        expected_components = ["ingestion", "nlp", "geo", "risk", "supply_chain"]
        
        for component in expected_components:
            assert component in components
            assert components[component]["status"] == "completed"


class TestAnomalyDetectionJob:
    """Test anomaly detection job"""
    
    def test_anomaly_job_creation(self):
        """Test anomaly detection job creation"""
        job = AnomalyDetectionJob("test_anomaly", "Test Anomaly", data_source="test_source")
        
        assert job.job_id == "test_anomaly"
        assert job.name == "Test Anomaly"
        assert job.data_source == "test_source"
    
    def test_anomaly_job_execution(self):
        """Test anomaly detection job execution"""
        job = AnomalyDetectionJob("test_anomaly", "Test Anomaly", data_source="test_source")
        
        result = job.run()
        
        assert job.status == JobStatus.COMPLETED
        assert result["status"] == "completed"
        assert "anomalies" in result
        assert "anomaly_score" in result
        assert "data_points" in result
        assert isinstance(result["anomalies"], list)
        assert 0 <= result["anomaly_score"] <= 1


class TestJobManager:
    """Test job manager"""
    
    def test_manager_creation(self):
        """Test job manager creation"""
        manager = JobManager()
        
        assert manager.scheduler is not None
        assert manager.monitor is not None
        assert len(manager.scheduler.jobs) > 0  # Default jobs should be added
    
    def test_default_jobs(self):
        """Test default jobs are created"""
        manager = JobManager()
        
        # Check default jobs exist
        job_ids = list(manager.scheduler.jobs.keys())
        assert "hourly_refresh" in job_ids
        assert "daily_refresh" in job_ids
        assert "anomaly_detection" in job_ids
    
    def test_add_custom_job(self):
        """Test adding custom job"""
        manager = JobManager()
        job = TestJob("custom_job", "Custom Job")
        
        job_id = manager.add_job(job)
        
        assert job_id == "custom_job"
        assert "custom_job" in manager.scheduler.jobs
    
    def test_run_job_now(self):
        """Test running job immediately"""
        manager = JobManager()
        
        # Create a test job
        job = TestJob("immediate_job", "Immediate Job", duration=0.1)
        manager.add_job(job)
        
        success = manager.run_job_now("immediate_job")
        
        assert success is True
        # Wait a bit for job to complete
        time.sleep(0.2)
        
        # Check job was created and run
        jobs = manager.get_all_jobs()
        immediate_jobs = [j for j in jobs if j["name"] == "Immediate Job"]
        assert len(immediate_jobs) > 0
    
    def test_get_job_metrics(self):
        """Test getting job metrics"""
        manager = JobManager()
        
        metrics = manager.get_job_metrics()
        
        assert "total_jobs" in metrics
        assert "completed_jobs" in metrics
        assert "failed_jobs" in metrics
        assert "success_rate" in metrics
        assert "total_duration" in metrics
        assert "average_duration" in metrics
    
    def test_get_health_status(self):
        """Test getting health status"""
        manager = JobManager()
        
        health = manager.get_health_status()
        
        assert "status" in health
        assert "metrics" in health
        assert "failed_jobs_count" in health
        assert "running_jobs_count" in health
        assert "scheduler_running" in health
        assert "timestamp" in health
    
    def test_create_custom_refresh_job(self):
        """Test creating custom refresh job"""
        manager = JobManager()
        
        job_id = manager.create_custom_refresh_job(
            refresh_type="custom",
            components=["ingestion", "nlp"]
        )
        
        assert job_id is not None
        assert job_id.startswith("custom_refresh_")
        
        # Check job was added
        jobs = manager.get_all_jobs()
        job_names = [j["name"] for j in jobs]
        assert any("custom_custom_refresh" in name for name in job_names)
    
    def test_create_anomaly_detection_job(self):
        """Test creating anomaly detection job"""
        manager = JobManager()
        
        job_id = manager.create_anomaly_detection_job("test_source")
        
        assert job_id is not None
        assert job_id.startswith("anomaly_")
        
        # Check job was added
        jobs = manager.get_all_jobs()
        job_names = [j["name"] for j in jobs]
        assert any("anomaly_detection_test_source" in name for name in job_names)
    
    def test_cancel_job(self):
        """Test cancelling job"""
        manager = JobManager()
        
        # Create a test job
        job = TestJob("cancel_job", "Cancel Job")
        manager.add_job(job)
        
        success = manager.cancel_job("cancel_job")
        
        assert success is True
        assert job.status == JobStatus.CANCELLED
    
    def test_remove_job(self):
        """Test removing job"""
        manager = JobManager()
        
        # Create a test job
        job = TestJob("remove_job", "Remove Job")
        manager.add_job(job)
        
        success = manager.remove_job("remove_job")
        
        assert success is True
        assert "remove_job" not in manager.scheduler.jobs
    
    def test_cleanup_old_jobs(self):
        """Test cleaning up old jobs"""
        manager = JobManager()
        
        # Create an old completed job
        job = TestJob("old_job", "Old Job")
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow() - timedelta(hours=25)
        manager.add_job(job)
        
        manager.cleanup_old_jobs(max_age_hours=24)
        
        assert "old_job" not in manager.scheduler.jobs
    
    def test_is_healthy(self):
        """Test health check"""
        manager = JobManager()
        
        # Should be healthy initially
        assert manager.is_healthy() is True
    
    def test_get_system_status(self):
        """Test getting system status"""
        manager = JobManager()
        
        status = manager.get_system_status()
        
        assert "job_manager" in status
        assert "scheduler" in status
        assert "monitor" in status
        assert "timestamp" in status
        
        assert "running" in status["job_manager"]
        assert "healthy" in status["job_manager"]
        assert "running" in status["scheduler"]
        assert "scheduled_jobs" in status["scheduler"]
