"""
Configuration settings for Peace Map platform
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseSettings, Field
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    url: str = Field(default="postgresql://localhost/peace_map", env="DATABASE_URL")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    echo: bool = Field(default=False, env="DB_ECHO")


class RedisConfig(BaseSettings):
    """Redis configuration"""
    url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")


class APIConfig(BaseSettings):
    """External API configuration"""
    nominatim_url: str = Field(
        default="https://nominatim.openstreetmap.org", 
        env="NOMINATIM_API_URL"
    )
    gdelt_url: str = Field(
        default="https://api.gdeltproject.org/api/v2", 
        env="GDELT_API_URL"
    )
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    rate_limit_per_minute: int = Field(default=60, env="API_RATE_LIMIT")


class SecurityConfig(BaseSettings):
    """Security configuration"""
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_EXPIRE")
    refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_EXPIRE")


class BackgroundJobsConfig(BaseSettings):
    """Background jobs configuration"""
    celery_broker_url: str = Field(default="redis://localhost:6379", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379", env="CELERY_RESULT_BACKEND")
    worker_concurrency: int = Field(default=4, env="WORKER_CONCURRENCY")
    task_serializer: str = Field(default="json", env="TASK_SERIALIZER")
    result_serializer: str = Field(default="json", env="RESULT_SERIALIZER")


class NLPConfig(BaseSettings):
    """NLP processing configuration"""
    model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="NLP_MODEL")
    similarity_threshold: float = Field(default=0.8, env="SIMILARITY_THRESHOLD")
    batch_size: int = Field(default=32, env="NLP_BATCH_SIZE")
    max_text_length: int = Field(default=512, env="MAX_TEXT_LENGTH")


class RiskScoringConfig(BaseSettings):
    """Risk scoring configuration"""
    default_weights: Dict[str, float] = Field(
        default={
            "event_count": 0.3,
            "sentiment": 0.25,
            "proximity_to_ports": 0.2,
            "event_severity": 0.15,
            "temporal_decay": 0.1
        }
    )
    high_risk_threshold: float = Field(default=70.0, env="HIGH_RISK_THRESHOLD")
    medium_risk_threshold: float = Field(default=40.0, env="MEDIUM_RISK_THRESHOLD")
    decay_factor: float = Field(default=0.95, env="RISK_DECAY_FACTOR")


class DataIngestionConfig(BaseSettings):
    """Data ingestion configuration"""
    gdelt_update_interval: int = Field(default=3600, env="GDELT_UPDATE_INTERVAL")  # 1 hour
    rss_update_interval: int = Field(default=1800, env="RSS_UPDATE_INTERVAL")  # 30 minutes
    max_events_per_batch: int = Field(default=1000, env="MAX_EVENTS_PER_BATCH")
    retry_attempts: int = Field(default=3, env="RETRY_ATTEMPTS")
    retry_delay: int = Field(default=60, env="RETRY_DELAY")


class GeospatialConfig(BaseSettings):
    """Geospatial configuration"""
    default_zoom_level: int = Field(default=6, env="DEFAULT_ZOOM_LEVEL")
    max_zoom_level: int = Field(default=18, env="MAX_ZOOM_LEVEL")
    tile_server: str = Field(default="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", env="TILE_SERVER")
    port_chokepoints_file: str = Field(default="data/port_chokepoints.geojson", env="PORT_CHOKEPOINTS_FILE")
    shipping_lanes_file: str = Field(default="data/shipping_lanes.geojson", env="SHIPPING_LANES_FILE")


class AlertingConfig(BaseSettings):
    """Alerting configuration"""
    email_enabled: bool = Field(default=True, env="EMAIL_ALERTS_ENABLED")
    smtp_server: Optional[str] = Field(default=None, env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    webhook_enabled: bool = Field(default=False, env="WEBHOOK_ALERTS_ENABLED")
    webhook_url: Optional[str] = Field(default=None, env="WEBHOOK_URL")


class LoggingConfig(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")
    file_path: Optional[str] = Field(default=None, env="LOG_FILE_PATH")
    max_file_size: int = Field(default=10485760, env="LOG_MAX_FILE_SIZE")  # 10MB
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")


class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.environment = Environment(os.getenv("ENVIRONMENT", "development"))
        
        # Initialize all config sections
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.api = APIConfig()
        self.security = SecurityConfig()
        self.background_jobs = BackgroundJobsConfig()
        self.nlp = NLPConfig()
        self.risk_scoring = RiskScoringConfig()
        self.data_ingestion = DataIngestionConfig()
        self.geospatial = GeospatialConfig()
        self.alerting = AlertingConfig()
        self.logging = LoggingConfig()
        
        # Application settings
        self.app_name = "Peace Map"
        self.app_version = "1.0.0"
        self.debug = self.environment == Environment.DEVELOPMENT
        
        # CORS settings
        self.cors_origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "https://peace-map.example.com"
        ]
        
        # Rate limiting
        self.rate_limit_per_minute = 60
        self.rate_limit_burst = 100
        
        # File upload settings
        self.max_upload_size = 10 * 1024 * 1024  # 10MB
        self.allowed_file_types = [".csv", ".json", ".geojson"]
        
        # Cache settings
        self.cache_ttl = 3600  # 1 hour
        self.cache_max_size = 1000
        
        # Event processing
        self.event_batch_size = 100
        self.event_processing_timeout = 300  # 5 minutes
        
        # Map settings
        self.default_center = [20.0, 0.0]  # [lat, lon]
        self.default_zoom = 2
        self.map_layers = [
            "events",
            "risk_heatmap", 
            "suppliers",
            "ports",
            "shipping_lanes"
        ]
        
        # Risk categories
        self.risk_categories = [
            "protest",
            "cyber", 
            "kinetic",
            "economic",
            "environmental",
            "political"
        ]
        
        # Event types
        self.event_types = [
            "conflict",
            "protest",
            "cyber_attack",
            "terrorism",
            "natural_disaster",
            "economic_crisis",
            "political_instability"
        ]
        
        # Supplier risk levels
        self.supplier_risk_levels = {
            "low": {"min": 0, "max": 30, "color": "#28a745"},
            "medium": {"min": 31, "max": 60, "color": "#ffc107"},
            "high": {"min": 61, "max": 80, "color": "#fd7e14"},
            "critical": {"min": 81, "max": 100, "color": "#dc3545"}
        }


# Global config instance
config = Config()
