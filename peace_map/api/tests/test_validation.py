"""
Tests for Peace Map API validation
"""

import pytest
from datetime import datetime, date
from peace_map.api.validation import (
    EventCreate, EventUpdate, EventFilters, EventType, EventStatus,
    SupplierCreate, SupplierUpdate, SupplierFilters,
    AlertCreate, AlertUpdate, AlertFilters, AlertStatus,
    PaginationParams, DateRangeParams, RiskIndexFilters, RiskLevel
)


class TestEventValidation:
    """Test event validation"""
    
    def test_event_create_valid(self):
        """Test valid event creation"""
        event_data = {
            "title": "Test Event",
            "description": "Test Description",
            "event_type": "protest",
            "location": "Test Location",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "source": "Test Source",
            "source_confidence": 0.8,
            "published_at": datetime.utcnow().isoformat(),
            "tags": ["test", "event"]
        }
        
        event = EventCreate(**event_data)
        assert event.title == "Test Event"
        assert event.event_type == EventType.PROTEST
        assert event.source_confidence == 0.8
    
    def test_event_create_invalid_title(self):
        """Test invalid event title"""
        event_data = {
            "title": "",  # Empty title
            "description": "Test Description",
            "event_type": "protest",
            "location": "Test Location",
            "source": "Test Source",
            "source_confidence": 0.8
        }
        
        with pytest.raises(ValueError):
            EventCreate(**event_data)
    
    def test_event_create_invalid_confidence(self):
        """Test invalid source confidence"""
        event_data = {
            "title": "Test Event",
            "description": "Test Description",
            "event_type": "protest",
            "location": "Test Location",
            "source": "Test Source",
            "source_confidence": 1.5  # Invalid confidence
        }
        
        with pytest.raises(ValueError):
            EventCreate(**event_data)
    
    def test_event_create_invalid_coordinates(self):
        """Test invalid coordinates"""
        event_data = {
            "title": "Test Event",
            "description": "Test Description",
            "event_type": "protest",
            "location": "Test Location",
            "latitude": 91.0,  # Invalid latitude
            "longitude": -74.0060,
            "source": "Test Source",
            "source_confidence": 0.8
        }
        
        with pytest.raises(ValueError):
            EventCreate(**event_data)
    
    def test_event_update_valid(self):
        """Test valid event update"""
        update_data = {
            "title": "Updated Event",
            "description": "Updated Description"
        }
        
        event = EventUpdate(**update_data)
        assert event.title == "Updated Event"
        assert event.description == "Updated Description"
    
    def test_event_update_invalid_title(self):
        """Test invalid event update title"""
        update_data = {
            "title": "",  # Empty title
            "description": "Updated Description"
        }
        
        with pytest.raises(ValueError):
            EventUpdate(**update_data)
    
    def test_event_filters_valid(self):
        """Test valid event filters"""
        filters_data = {
            "event_type": "protest",
            "status": "active",
            "source_confidence": 0.8,
            "keywords": ["test", "event"],
            "sentiment": "positive"
        }
        
        filters = EventFilters(**filters_data)
        assert filters.event_type == EventType.PROTEST
        assert filters.status == EventStatus.ACTIVE
        assert filters.source_confidence == 0.8
        assert filters.keywords == ["test", "event"]
        assert filters.sentiment == "positive"
    
    def test_event_filters_invalid_confidence(self):
        """Test invalid event filters confidence"""
        filters_data = {
            "source_confidence": 1.5  # Invalid confidence
        }
        
        with pytest.raises(ValueError):
            EventFilters(**filters_data)
    
    def test_event_filters_invalid_region_polygon(self):
        """Test invalid event filters region polygon"""
        filters_data = {
            "region_polygon": [[-180, -90], [180, 90], [200, 100]]  # Invalid coordinates
        }
        
        with pytest.raises(ValueError):
            EventFilters(**filters_data)


class TestSupplierValidation:
    """Test supplier validation"""
    
    def test_supplier_create_valid(self):
        """Test valid supplier creation"""
        supplier_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "contact_email": "test@example.com",
            "contact_phone": "+1234567890",
            "website": "https://example.com",
            "description": "Test Supplier Description",
            "tags": ["test", "supplier"]
        }
        
        supplier = SupplierCreate(**supplier_data)
        assert supplier.name == "Test Supplier"
        assert supplier.contact_email == "test@example.com"
        assert supplier.website == "https://example.com"
    
    def test_supplier_create_invalid_name(self):
        """Test invalid supplier name"""
        supplier_data = {
            "name": "",  # Empty name
            "location": "Test Location"
        }
        
        with pytest.raises(ValueError):
            SupplierCreate(**supplier_data)
    
    def test_supplier_create_invalid_email(self):
        """Test invalid supplier email"""
        supplier_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "contact_email": "invalid-email"  # Invalid email format
        }
        
        with pytest.raises(ValueError):
            SupplierCreate(**supplier_data)
    
    def test_supplier_create_invalid_website(self):
        """Test invalid supplier website"""
        supplier_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "website": "example.com"  # Missing protocol
        }
        
        supplier = SupplierCreate(**supplier_data)
        assert supplier.website == "https://example.com"  # Should be auto-corrected
    
    def test_supplier_update_valid(self):
        """Test valid supplier update"""
        update_data = {
            "name": "Updated Supplier",
            "contact_email": "updated@example.com"
        }
        
        supplier = SupplierUpdate(**update_data)
        assert supplier.name == "Updated Supplier"
        assert supplier.contact_email == "updated@example.com"
    
    def test_supplier_update_invalid_name(self):
        """Test invalid supplier update name"""
        update_data = {
            "name": "",  # Empty name
            "contact_email": "updated@example.com"
        }
        
        with pytest.raises(ValueError):
            SupplierUpdate(**update_data)
    
    def test_supplier_filters_valid(self):
        """Test valid supplier filters"""
        filters_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "risk_level": "high",
            "min_risk_score": 50.0,
            "max_risk_score": 100.0
        }
        
        filters = SupplierFilters(**filters_data)
        assert filters.name == "Test Supplier"
        assert filters.location == "Test Location"
        assert filters.risk_level == RiskLevel.HIGH
        assert filters.min_risk_score == 50.0
        assert filters.max_risk_score == 100.0
    
    def test_supplier_filters_invalid_risk_scores(self):
        """Test invalid supplier filters risk scores"""
        filters_data = {
            "min_risk_score": 100.0,
            "max_risk_score": 50.0  # Max less than min
        }
        
        with pytest.raises(ValueError):
            SupplierFilters(**filters_data)


class TestAlertValidation:
    """Test alert validation"""
    
    def test_alert_create_valid(self):
        """Test valid alert creation"""
        alert_data = {
            "supplier_id": 1,
            "risk_threshold": 75.0,
            "notification_email": "alert@example.com",
            "notification_phone": "+1234567890",
            "description": "Test Alert",
            "tags": ["test", "alert"]
        }
        
        alert = AlertCreate(**alert_data)
        assert alert.supplier_id == 1
        assert alert.risk_threshold == 75.0
        assert alert.notification_email == "alert@example.com"
    
    def test_alert_create_invalid_threshold(self):
        """Test invalid alert threshold"""
        alert_data = {
            "supplier_id": 1,
            "risk_threshold": 150.0  # Invalid threshold
        }
        
        with pytest.raises(ValueError):
            AlertCreate(**alert_data)
    
    def test_alert_create_invalid_email(self):
        """Test invalid alert email"""
        alert_data = {
            "supplier_id": 1,
            "risk_threshold": 75.0,
            "notification_email": "invalid-email"  # Invalid email format
        }
        
        with pytest.raises(ValueError):
            AlertCreate(**alert_data)
    
    def test_alert_update_valid(self):
        """Test valid alert update"""
        update_data = {
            "risk_threshold": 80.0,
            "notification_email": "updated@example.com"
        }
        
        alert = AlertUpdate(**update_data)
        assert alert.risk_threshold == 80.0
        assert alert.notification_email == "updated@example.com"
    
    def test_alert_update_invalid_threshold(self):
        """Test invalid alert update threshold"""
        update_data = {
            "risk_threshold": 150.0  # Invalid threshold
        }
        
        with pytest.raises(ValueError):
            AlertUpdate(**update_data)
    
    def test_alert_filters_valid(self):
        """Test valid alert filters"""
        filters_data = {
            "status": "active",
            "risk_level": "high",
            "supplier_id": 1,
            "min_risk_score": 50.0,
            "max_risk_score": 100.0
        }
        
        filters = AlertFilters(**filters_data)
        assert filters.status == AlertStatus.ACTIVE
        assert filters.risk_level == RiskLevel.HIGH
        assert filters.supplier_id == 1
        assert filters.min_risk_score == 50.0
        assert filters.max_risk_score == 100.0
    
    def test_alert_filters_invalid_risk_scores(self):
        """Test invalid alert filters risk scores"""
        filters_data = {
            "min_risk_score": 100.0,
            "max_risk_score": 50.0  # Max less than min
        }
        
        with pytest.raises(ValueError):
            AlertFilters(**filters_data)


class TestPaginationValidation:
    """Test pagination validation"""
    
    def test_pagination_valid(self):
        """Test valid pagination"""
        pagination_data = {
            "page": 1,
            "size": 20
        }
        
        pagination = PaginationParams(**pagination_data)
        assert pagination.page == 1
        assert pagination.size == 20
    
    def test_pagination_invalid_page(self):
        """Test invalid pagination page"""
        pagination_data = {
            "page": 0,  # Invalid page
            "size": 20
        }
        
        with pytest.raises(ValueError):
            PaginationParams(**pagination_data)
    
    def test_pagination_invalid_size(self):
        """Test invalid pagination size"""
        pagination_data = {
            "page": 1,
            "size": 200  # Invalid size
        }
        
        with pytest.raises(ValueError):
            PaginationParams(**pagination_data)


class TestDateRangeValidation:
    """Test date range validation"""
    
    def test_date_range_valid(self):
        """Test valid date range"""
        date_range_data = {
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 12, 31)
        }
        
        date_range = DateRangeParams(**date_range_data)
        assert date_range.start_date == date(2024, 1, 1)
        assert date_range.end_date == date(2024, 12, 31)
    
    def test_date_range_invalid(self):
        """Test invalid date range"""
        date_range_data = {
            "start_date": date(2024, 12, 31),
            "end_date": date(2024, 1, 1)  # End before start
        }
        
        with pytest.raises(ValueError):
            DateRangeParams(**date_range_data)


class TestRiskIndexValidation:
    """Test risk index validation"""
    
    def test_risk_index_filters_valid(self):
        """Test valid risk index filters"""
        filters_data = {
            "region": "Test Region",
            "risk_level": "high",
            "min_score": 50.0,
            "max_score": 100.0
        }
        
        filters = RiskIndexFilters(**filters_data)
        assert filters.region == "Test Region"
        assert filters.risk_level == RiskLevel.HIGH
        assert filters.min_score == 50.0
        assert filters.max_score == 100.0
    
    def test_risk_index_filters_invalid_scores(self):
        """Test invalid risk index filters scores"""
        filters_data = {
            "min_score": 100.0,
            "max_score": 50.0  # Max less than min
        }
        
        with pytest.raises(ValueError):
            RiskIndexFilters(**filters_data)
