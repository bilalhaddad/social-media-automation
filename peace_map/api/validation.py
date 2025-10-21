"""
Request validation for Peace Map API
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import re


class EventType(str, Enum):
    """Event type enumeration"""
    PROTEST = "protest"
    CYBER = "cyber"
    KINETIC = "kinetic"
    OTHER = "other"


class EventStatus(str, Enum):
    """Event status enumeration"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status enumeration"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    
    @validator('page')
    def validate_page(cls, v):
        if v < 1:
            raise ValueError('Page must be greater than 0')
        return v
    
    @validator('size')
    def validate_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Page size must be between 1 and 100')
        return v


class DateRangeParams(BaseModel):
    """Date range parameters"""
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class EventFilters(BaseModel):
    """Event filters"""
    event_type: Optional[EventType] = Field(None, description="Event type filter")
    status: Optional[EventStatus] = Field(None, description="Event status filter")
    source_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Source confidence filter")
    region_polygon: Optional[List[List[float]]] = Field(None, description="Region polygon filter")
    keywords: Optional[List[str]] = Field(None, description="Keywords filter")
    sentiment: Optional[str] = Field(None, description="Sentiment filter")
    
    @validator('region_polygon')
    def validate_region_polygon(cls, v):
        if v:
            for point in v:
                if len(point) != 2:
                    raise ValueError('Each point must have exactly 2 coordinates (longitude, latitude)')
                if not (-180 <= point[0] <= 180):
                    raise ValueError('Longitude must be between -180 and 180')
                if not (-90 <= point[1] <= 90):
                    raise ValueError('Latitude must be between -90 and 90')
        return v


class RiskIndexFilters(BaseModel):
    """Risk index filters"""
    region: Optional[str] = Field(None, description="Region filter")
    risk_level: Optional[RiskLevel] = Field(None, description="Risk level filter")
    min_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Minimum risk score")
    max_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Maximum risk score")
    
    @validator('max_score')
    def validate_max_score(cls, v, values):
        if v and 'min_score' in values and values['min_score'] and v < values['min_score']:
            raise ValueError('Max score must be greater than or equal to min score')
        return v


class SupplierFilters(BaseModel):
    """Supplier filters"""
    name: Optional[str] = Field(None, description="Supplier name filter")
    location: Optional[str] = Field(None, description="Supplier location filter")
    risk_level: Optional[RiskLevel] = Field(None, description="Risk level filter")
    min_risk_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Minimum risk score")
    max_risk_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Maximum risk score")
    
    @validator('max_risk_score')
    def validate_max_risk_score(cls, v, values):
        if v and 'min_risk_score' in values and values['min_risk_score'] and v < values['min_risk_score']:
            raise ValueError('Max risk score must be greater than or equal to min risk score')
        return v


class AlertFilters(BaseModel):
    """Alert filters"""
    status: Optional[AlertStatus] = Field(None, description="Alert status filter")
    risk_level: Optional[RiskLevel] = Field(None, description="Risk level filter")
    supplier_id: Optional[int] = Field(None, description="Supplier ID filter")
    min_risk_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Minimum risk score")
    max_risk_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Maximum risk score")
    
    @validator('max_risk_score')
    def validate_max_risk_score(cls, v, values):
        if v and 'min_risk_score' in values and values['min_risk_score'] and v < values['min_risk_score']:
            raise ValueError('Max risk score must be greater than or equal to min risk score')
        return v


class EventCreate(BaseModel):
    """Event creation model"""
    title: str = Field(..., min_length=1, max_length=500, description="Event title")
    description: Optional[str] = Field(None, max_length=2000, description="Event description")
    event_type: EventType = Field(..., description="Event type")
    location: str = Field(..., min_length=1, max_length=200, description="Event location")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Event latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Event longitude")
    source: str = Field(..., min_length=1, max_length=100, description="Event source")
    source_confidence: float = Field(..., ge=0.0, le=1.0, description="Source confidence")
    published_at: Optional[datetime] = Field(None, description="Event publication date")
    tags: Optional[List[str]] = Field(None, description="Event tags")
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip() if v else None
    
    @validator('location')
    def validate_location(cls, v):
        if not v.strip():
            raise ValueError('Location cannot be empty')
        return v.strip()
    
    @validator('source')
    def validate_source(cls, v):
        if not v.strip():
            raise ValueError('Source cannot be empty')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            for tag in v:
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
                if len(tag) > 50:
                    raise ValueError('Tag cannot be longer than 50 characters')
        return v


class EventUpdate(BaseModel):
    """Event update model"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Event title")
    description: Optional[str] = Field(None, max_length=2000, description="Event description")
    event_type: Optional[EventType] = Field(None, description="Event type")
    location: Optional[str] = Field(None, min_length=1, max_length=200, description="Event location")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Event latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Event longitude")
    source: Optional[str] = Field(None, min_length=1, max_length=100, description="Event source")
    source_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Source confidence")
    published_at: Optional[datetime] = Field(None, description="Event publication date")
    tags: Optional[List[str]] = Field(None, description="Event tags")
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip() if v else None
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip() if v else None
    
    @validator('location')
    def validate_location(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Location cannot be empty')
        return v.strip() if v else None
    
    @validator('source')
    def validate_source(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Source cannot be empty')
        return v.strip() if v else None
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            for tag in v:
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
                if len(tag) > 50:
                    raise ValueError('Tag cannot be longer than 50 characters')
        return v


class SupplierCreate(BaseModel):
    """Supplier creation model"""
    name: str = Field(..., min_length=1, max_length=200, description="Supplier name")
    location: str = Field(..., min_length=1, max_length=200, description="Supplier location")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Supplier latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Supplier longitude")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    website: Optional[str] = Field(None, description="Supplier website")
    description: Optional[str] = Field(None, max_length=1000, description="Supplier description")
    tags: Optional[List[str]] = Field(None, description="Supplier tags")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('location')
    def validate_location(cls, v):
        if not v.strip():
            raise ValueError('Location cannot be empty')
        return v.strip()
    
    @validator('contact_email')
    def validate_contact_email(cls, v):
        if v:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, v):
                raise ValueError('Invalid email format')
        return v
    
    @validator('website')
    def validate_website(cls, v):
        if v:
            if not v.startswith(('http://', 'https://')):
                v = 'https://' + v
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            for tag in v:
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
                if len(tag) > 50:
                    raise ValueError('Tag cannot be longer than 50 characters')
        return v


class SupplierUpdate(BaseModel):
    """Supplier update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Supplier name")
    location: Optional[str] = Field(None, min_length=1, max_length=200, description="Supplier location")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Supplier latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Supplier longitude")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    website: Optional[str] = Field(None, description="Supplier website")
    description: Optional[str] = Field(None, max_length=1000, description="Supplier description")
    tags: Optional[List[str]] = Field(None, description="Supplier tags")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else None
    
    @validator('location')
    def validate_location(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Location cannot be empty')
        return v.strip() if v else None
    
    @validator('contact_email')
    def validate_contact_email(cls, v):
        if v:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, v):
                raise ValueError('Invalid email format')
        return v
    
    @validator('website')
    def validate_website(cls, v):
        if v:
            if not v.startswith(('http://', 'https://')):
                v = 'https://' + v
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            for tag in v:
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
                if len(tag) > 50:
                    raise ValueError('Tag cannot be longer than 50 characters')
        return v


class AlertCreate(BaseModel):
    """Alert creation model"""
    supplier_id: int = Field(..., description="Supplier ID")
    risk_threshold: float = Field(..., ge=0.0, le=100.0, description="Risk threshold")
    notification_email: Optional[str] = Field(None, description="Notification email")
    notification_phone: Optional[str] = Field(None, description="Notification phone")
    description: Optional[str] = Field(None, max_length=500, description="Alert description")
    tags: Optional[List[str]] = Field(None, description="Alert tags")
    
    @validator('notification_email')
    def validate_notification_email(cls, v):
        if v:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, v):
                raise ValueError('Invalid email format')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            for tag in v:
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
                if len(tag) > 50:
                    raise ValueError('Tag cannot be longer than 50 characters')
        return v


class AlertUpdate(BaseModel):
    """Alert update model"""
    risk_threshold: Optional[float] = Field(None, ge=0.0, le=100.0, description="Risk threshold")
    notification_email: Optional[str] = Field(None, description="Notification email")
    notification_phone: Optional[str] = Field(None, description="Notification phone")
    description: Optional[str] = Field(None, max_length=500, description="Alert description")
    tags: Optional[List[str]] = Field(None, description="Alert tags")
    
    @validator('notification_email')
    def validate_notification_email(cls, v):
        if v:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, v):
                raise ValueError('Invalid email format')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            for tag in v:
                if not tag.strip():
                    raise ValueError('Tag cannot be empty')
                if len(tag) > 50:
                    raise ValueError('Tag cannot be longer than 50 characters')
        return v
