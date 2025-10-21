"""
API models for Peace Map platform
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    message: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: Optional[str] = Field(default="asc", description="Sort order (asc/desc)")


class DateRangeParams(BaseModel):
    """Date range parameters"""
    start_date: Optional[datetime] = Field(default=None, description="Start date")
    end_date: Optional[datetime] = Field(default=None, description="End date")


class GeoBoundsParams(BaseModel):
    """Geographic bounds parameters"""
    north: float = Field(..., ge=-90, le=90, description="Northern boundary")
    south: float = Field(..., ge=-90, le=90, description="Southern boundary")
    east: float = Field(..., ge=-180, le=180, description="Eastern boundary")
    west: float = Field(..., ge=-180, le=180, description="Western boundary")


class EventFilters(BaseModel):
    """Event filtering parameters"""
    categories: Optional[List[str]] = Field(default=None, description="Event categories")
    severities: Optional[List[str]] = Field(default=None, description="Event severities")
    sources: Optional[List[str]] = Field(default=None, description="Event sources")
    countries: Optional[List[str]] = Field(default=None, description="Countries")
    regions: Optional[List[str]] = Field(default=None, description="Regions")
    min_confidence: Optional[float] = Field(default=None, ge=0, le=1, description="Minimum confidence")
    max_confidence: Optional[float] = Field(default=None, ge=0, le=1, description="Maximum confidence")


class RiskFilters(BaseModel):
    """Risk filtering parameters"""
    regions: Optional[List[str]] = Field(default=None, description="Regions")
    risk_levels: Optional[List[str]] = Field(default=None, description="Risk levels")
    min_score: Optional[float] = Field(default=None, ge=0, le=100, description="Minimum risk score")
    max_score: Optional[float] = Field(default=None, ge=0, le=100, description="Maximum risk score")


class SupplierFilters(BaseModel):
    """Supplier filtering parameters"""
    countries: Optional[List[str]] = Field(default=None, description="Countries")
    regions: Optional[List[str]] = Field(default=None, description="Regions")
    industries: Optional[List[str]] = Field(default=None, description="Industries")
    statuses: Optional[List[str]] = Field(default=None, description="Statuses")
    risk_levels: Optional[List[str]] = Field(default=None, description="Risk levels")
    min_risk_score: Optional[float] = Field(default=None, ge=0, le=100, description="Minimum risk score")
    max_risk_score: Optional[float] = Field(default=None, ge=0, le=100, description="Maximum risk score")


class AlertFilters(BaseModel):
    """Alert filtering parameters"""
    alert_types: Optional[List[str]] = Field(default=None, description="Alert types")
    severities: Optional[List[str]] = Field(default=None, description="Severities")
    statuses: Optional[List[str]] = Field(default=None, description="Statuses")
    supplier_ids: Optional[List[str]] = Field(default=None, description="Supplier IDs")


class EventCreate(BaseModel):
    """Event creation model"""
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    source: str = Field(..., description="Event source")
    source_url: Optional[str] = Field(default=None, description="Source URL")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Location data")
    category: str = Field(..., description="Event category")
    severity: str = Field(..., description="Event severity")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    tags: Optional[List[str]] = Field(default=None, description="Event tags")


class EventUpdate(BaseModel):
    """Event update model"""
    title: Optional[str] = Field(default=None, description="Event title")
    description: Optional[str] = Field(default=None, description="Event description")
    category: Optional[str] = Field(default=None, description="Event category")
    severity: Optional[str] = Field(default=None, description="Event severity")
    confidence: Optional[float] = Field(default=None, ge=0, le=1, description="Confidence score")
    tags: Optional[List[str]] = Field(default=None, description="Event tags")


class SupplierCreate(BaseModel):
    """Supplier creation model"""
    name: str = Field(..., description="Supplier name")
    country: str = Field(..., description="Country")
    region: Optional[str] = Field(default=None, description="Region")
    city: Optional[str] = Field(default=None, description="City")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    industry: Optional[str] = Field(default=None, description="Industry")
    contact_email: Optional[str] = Field(default=None, description="Contact email")
    contact_phone: Optional[str] = Field(default=None, description="Contact phone")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class SupplierUpdate(BaseModel):
    """Supplier update model"""
    name: Optional[str] = Field(default=None, description="Supplier name")
    country: Optional[str] = Field(default=None, description="Country")
    region: Optional[str] = Field(default=None, description="Region")
    city: Optional[str] = Field(default=None, description="City")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="Longitude")
    industry: Optional[str] = Field(default=None, description="Industry")
    contact_email: Optional[str] = Field(default=None, description="Contact email")
    contact_phone: Optional[str] = Field(default=None, description="Contact phone")
    status: Optional[str] = Field(default=None, description="Status")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class AlertCreate(BaseModel):
    """Alert creation model"""
    supplier_id: str = Field(..., description="Supplier ID")
    alert_type: str = Field(..., description="Alert type")
    severity: str = Field(..., description="Severity")
    message: str = Field(..., description="Alert message")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class AlertUpdate(BaseModel):
    """Alert update model"""
    status: Optional[str] = Field(default=None, description="Alert status")
    message: Optional[str] = Field(default=None, description="Alert message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class RiskCalculationRequest(BaseModel):
    """Risk calculation request model"""
    region: str = Field(..., description="Region")
    events: Optional[List[Dict[str, Any]]] = Field(default=None, description="Events data")
    port_locations: Optional[List[Dict[str, Any]]] = Field(default=None, description="Port locations")
    economic_data: Optional[Dict[str, Any]] = Field(default=None, description="Economic data")
    political_data: Optional[Dict[str, Any]] = Field(default=None, description="Political data")
    infrastructure_data: Optional[Dict[str, Any]] = Field(default=None, description="Infrastructure data")
    time_window_days: Optional[int] = Field(default=30, ge=1, le=365, description="Time window in days")


class CSVUploadRequest(BaseModel):
    """CSV upload request model"""
    filename: str = Field(..., description="Filename")
    content_type: str = Field(..., description="Content type")
    file_size: int = Field(..., ge=1, le=10485760, description="File size in bytes")  # 10MB max


class GeoLayerRequest(BaseModel):
    """Geo layer request model"""
    layer_name: str = Field(..., description="Layer name")
    bounds: Optional[GeoBoundsParams] = Field(default=None, description="Geographic bounds")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Layer filters")


class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Any] = Field(..., description="Items")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class EventResponse(BaseModel):
    """Event response model"""
    id: str
    title: str
    description: str
    source: str
    source_url: Optional[str]
    published_at: datetime
    location: Optional[Dict[str, Any]]
    category: str
    severity: str
    confidence: float
    tags: List[str]
    language: str = "en"
    sentiment_score: Optional[float] = None


class SupplierResponse(BaseModel):
    """Supplier response model"""
    id: str
    name: str
    country: str
    region: Optional[str]
    city: Optional[str]
    latitude: float
    longitude: float
    industry: Optional[str]
    status: str
    risk_score: float
    risk_level: str
    contact_email: Optional[str]
    contact_phone: Optional[str]
    created_at: datetime
    updated_at: datetime


class AlertResponse(BaseModel):
    """Alert response model"""
    id: str
    supplier_id: str
    alert_type: str
    severity: str
    message: str
    risk_score: float
    status: str
    created_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]


class RiskScoreResponse(BaseModel):
    """Risk score response model"""
    overall_score: float
    risk_level: str
    factors: List[Dict[str, Any]]
    confidence: float
    calculated_at: datetime
    region: Optional[str]


class GeoFeatureResponse(BaseModel):
    """Geo feature response model"""
    id: str
    geometry: Dict[str, Any]
    properties: Dict[str, Any]
    style: Optional[Dict[str, Any]] = None


class GeoLayerResponse(BaseModel):
    """Geo layer response model"""
    name: str
    type: str
    style: str
    visible: bool
    opacity: float
    z_index: int
    feature_count: int
    last_update: Optional[datetime]


class StatisticsResponse(BaseModel):
    """Statistics response model"""
    total_events: int
    total_suppliers: int
    total_alerts: int
    active_alerts: int
    average_risk_score: float
    risk_distribution: Dict[str, int]
    geographic_distribution: Dict[str, int]
    industry_distribution: Dict[str, int]
