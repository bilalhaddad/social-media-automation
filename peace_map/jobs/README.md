# Peace Map Background Jobs

This module provides a comprehensive background job system for the Peace Map project, including data refresh, anomaly detection, and job monitoring.

## Features

- **Job Scheduler**: Manages scheduled and immediate job execution
- **Anomaly Detection**: STL and z-score based anomaly detection
- **Data Refresh**: Automated data refresh with component-specific updates
- **Job Monitoring**: Real-time job status tracking and metrics
- **Health Monitoring**: System health checks and performance metrics

## Components

### Core Classes

- `BaseJob`: Abstract base class for all background jobs
- `JobScheduler`: Manages job scheduling and execution
- `JobMonitor`: Tracks job execution and provides metrics
- `JobManager`: Coordinates all job operations

### Job Types

- `DataRefreshJob`: Refreshes data from all sources
- `AnomalyDetectionJob`: Detects anomalies in data streams

## Usage

### Basic Setup

```python
from peace_map.jobs import JobManager

# Initialize job manager
job_manager = JobManager()

# Start the system
job_manager.start()

# Get system status
status = job_manager.get_system_status()
print(f"System healthy: {status['job_manager']['healthy']}")
```

### Running Jobs

```python
# Run a job immediately
job_manager.run_job_now("hourly_refresh")

# Create custom jobs
custom_job_id = job_manager.create_custom_refresh_job(
    refresh_type="custom",
    components=["ingestion", "nlp"]
)

# Create anomaly detection job
anomaly_job_id = job_manager.create_anomaly_detection_job("risk_index")
```

### Monitoring

```python
# Get job metrics
metrics = job_manager.get_job_metrics()
print(f"Success rate: {metrics['success_rate']:.2%}")

# Get failed jobs
failed_jobs = job_manager.get_failed_jobs()
for job in failed_jobs:
    print(f"Failed: {job['name']} - {job['error_message']}")

# Get job history
history = job_manager.get_job_history(hours=24)
print(f"Jobs in last 24h: {len(history)}")
```

## Default Jobs

The system automatically configures these default jobs:

1. **Hourly Refresh** (`hourly_refresh`): Incremental data refresh every hour
2. **Daily Refresh** (`daily_refresh`): Full data refresh every 24 hours  
3. **Anomaly Detection** (`anomaly_detection`): Risk index anomaly detection every 2 hours

## Anomaly Detection

The system supports two anomaly detection methods:

### Z-Score Method
- Calculates z-scores for data points
- Flags values exceeding threshold (default: 2.0)
- Good for detecting statistical outliers

### STL Decomposition
- Seasonal and Trend decomposition using Loess
- Detects anomalies in residuals
- Good for time series with seasonal patterns

### Combined Detection
- Uses both methods for comprehensive detection
- Avoids duplicate alerts
- Provides severity scoring

## Job Status

Jobs can have the following statuses:

- `PENDING`: Job created but not started
- `RUNNING`: Job currently executing
- `COMPLETED`: Job finished successfully
- `FAILED`: Job failed with error
- `CANCELLED`: Job was cancelled

## Health Monitoring

The system provides comprehensive health monitoring:

```python
# Get health status
health = job_manager.get_health_status()
print(f"Status: {health['status']}")
print(f"Failed jobs: {health['failed_jobs_count']}")

# Check if system is healthy
if job_manager.is_healthy():
    print("System is healthy")
else:
    print("System has issues")
```

## Performance Metrics

Track job performance with detailed metrics:

```python
# Get performance for specific job type
performance = job_manager.get_job_performance("data_refresh")
print(f"Average duration: {performance['average_duration']:.2f}s")
print(f"95th percentile: {performance['p95_duration']:.2f}s")

# Get overall metrics
metrics = job_manager.get_job_metrics()
print(f"Total jobs: {metrics['total_jobs']}")
print(f"Success rate: {metrics['success_rate']:.2%}")
```

## Configuration

### Environment Variables

```bash
# Redis configuration
REDIS_URL=redis://localhost:6379/0

# Job configuration
JOB_CLEANUP_HOURS=24
ANOMALY_ZSCORE_THRESHOLD=2.0
ANOMALY_STL_THRESHOLD=0.1
```

### Customization

```python
# Create custom refresh job with specific components
job_id = job_manager.create_custom_refresh_job(
    refresh_type="selective",
    components=["ingestion", "risk"]  # Only refresh these components
)

# Schedule custom job
job_manager.scheduler.schedule_job(job_id, 1800)  # Every 30 minutes
```

## Error Handling

The system includes comprehensive error handling:

- Automatic retry for transient failures
- Error logging and tracking
- Failed job reporting
- Health status monitoring

## Cleanup

Automatically clean up old completed jobs:

```python
# Clean up jobs older than 24 hours (default)
job_manager.cleanup_old_jobs()

# Clean up jobs older than 48 hours
job_manager.cleanup_old_jobs(max_age_hours=48)
```

## Integration

The job system integrates with:

- **API**: Job status endpoints
- **Database**: Job persistence
- **Monitoring**: Health checks and metrics
- **Logging**: Comprehensive logging

## Dependencies

- `celery`: Distributed task queue
- `redis`: Message broker and caching
- `numpy`: Numerical computations
- `scipy`: Statistical functions
- `statsmodels`: Time series analysis
- `schedule`: Job scheduling
- `APScheduler`: Advanced scheduling
