"""
Tests for Peace Map API models
"""

import pytest
from datetime import datetime, date
from peace_map.api.models import db, Event, RiskIndex, Supplier, Alert
from peace_map.api.app import app


@pytest.fixture
def client():
    """Test client fixture"""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def sample_event():
    """Sample event fixture"""
    return Event(
        project_id=1,
        title="Test Event",
        description="Test Description",
        event_type="protest",
        location="Test Location",
        latitude=40.7128,
        longitude=-74.0060,
        source="Test Source",
        source_confidence=0.8,
        published_at=datetime.utcnow(),
        tags=["test", "event"]
    )


@pytest.fixture
def sample_supplier():
    """Sample supplier fixture"""
    return Supplier(
        name="Test Supplier",
        location="Test Location",
        latitude=40.7128,
        longitude=-74.0060,
        contact_email="test@example.com",
        contact_phone="+1234567890",
        website="https://example.com",
        description="Test Supplier Description",
        tags=["test", "supplier"]
    )


@pytest.fixture
def sample_alert():
    """Sample alert fixture"""
    return Alert(
        supplier_id=1,
        risk_threshold=75.0,
        notification_email="alert@example.com",
        notification_phone="+1234567890",
        description="Test Alert",
        tags=["test", "alert"]
    )


class TestEvent:
    """Test Event model"""
    
    def test_create_event(self, client, sample_event):
        """Test creating an event"""
        event = sample_event
        event.save()
        
        assert event.id is not None
        assert event.title == "Test Event"
        assert event.event_type == "protest"
        assert event.source_confidence == 0.8
    
    def test_event_to_dict(self, client, sample_event):
        """Test event to_dict method"""
        event = sample_event
        event.save()
        
        event_dict = event.to_dict()
        
        assert "id" in event_dict
        assert event_dict["title"] == "Test Event"
        assert event_dict["event_type"] == "protest"
        assert event_dict["source_confidence"] == 0.8
    
    def test_event_update(self, client, sample_event):
        """Test updating an event"""
        event = sample_event
        event.save()
        
        event.title = "Updated Event"
        event.description = "Updated Description"
        event.save()
        
        updated_event = Event.query.get(event.id)
        assert updated_event.title == "Updated Event"
        assert updated_event.description == "Updated Description"
    
    def test_event_delete(self, client, sample_event):
        """Test deleting an event"""
        event = sample_event
        event.save()
        event_id = event.id
        
        event.delete()
        
        deleted_event = Event.query.get(event_id)
        assert deleted_event is None


class TestRiskIndex:
    """Test RiskIndex model"""
    
    def test_create_risk_index(self, client):
        """Test creating a risk index"""
        risk_index = RiskIndex(
            region="Test Region",
            date=date.today(),
            composite_score=75.5,
            event_count=10,
            sentiment_score=0.6,
            proximity_score=0.8,
            risk_level="high"
        )
        risk_index.save()
        
        assert risk_index.id is not None
        assert risk_index.region == "Test Region"
        assert risk_index.composite_score == 75.5
        assert risk_index.risk_level == "high"
    
    def test_risk_index_to_dict(self, client):
        """Test risk index to_dict method"""
        risk_index = RiskIndex(
            region="Test Region",
            date=date.today(),
            composite_score=75.5,
            event_count=10,
            sentiment_score=0.6,
            proximity_score=0.8,
            risk_level="high"
        )
        risk_index.save()
        
        risk_dict = risk_index.to_dict()
        
        assert "id" in risk_dict
        assert risk_dict["region"] == "Test Region"
        assert risk_dict["composite_score"] == 75.5
        assert risk_dict["risk_level"] == "high"


class TestSupplier:
    """Test Supplier model"""
    
    def test_create_supplier(self, client, sample_supplier):
        """Test creating a supplier"""
        supplier = sample_supplier
        supplier.save()
        
        assert supplier.id is not None
        assert supplier.name == "Test Supplier"
        assert supplier.location == "Test Location"
        assert supplier.contact_email == "test@example.com"
    
    def test_supplier_to_dict(self, client, sample_supplier):
        """Test supplier to_dict method"""
        supplier = sample_supplier
        supplier.save()
        
        supplier_dict = supplier.to_dict()
        
        assert "id" in supplier_dict
        assert supplier_dict["name"] == "Test Supplier"
        assert supplier_dict["location"] == "Test Location"
        assert supplier_dict["contact_email"] == "test@example.com"
    
    def test_supplier_update(self, client, sample_supplier):
        """Test updating a supplier"""
        supplier = sample_supplier
        supplier.save()
        
        supplier.name = "Updated Supplier"
        supplier.contact_email = "updated@example.com"
        supplier.save()
        
        updated_supplier = Supplier.query.get(supplier.id)
        assert updated_supplier.name == "Updated Supplier"
        assert updated_supplier.contact_email == "updated@example.com"
    
    def test_supplier_delete(self, client, sample_supplier):
        """Test deleting a supplier"""
        supplier = sample_supplier
        supplier.save()
        supplier_id = supplier.id
        
        supplier.delete()
        
        deleted_supplier = Supplier.query.get(supplier_id)
        assert deleted_supplier is None


class TestAlert:
    """Test Alert model"""
    
    def test_create_alert(self, client, sample_alert):
        """Test creating an alert"""
        alert = sample_alert
        alert.save()
        
        assert alert.id is not None
        assert alert.supplier_id == 1
        assert alert.risk_threshold == 75.0
        assert alert.notification_email == "alert@example.com"
    
    def test_alert_to_dict(self, client, sample_alert):
        """Test alert to_dict method"""
        alert = sample_alert
        alert.save()
        
        alert_dict = alert.to_dict()
        
        assert "id" in alert_dict
        assert alert_dict["supplier_id"] == 1
        assert alert_dict["risk_threshold"] == 75.0
        assert alert_dict["notification_email"] == "alert@example.com"
    
    def test_alert_update(self, client, sample_alert):
        """Test updating an alert"""
        alert = sample_alert
        alert.save()
        
        alert.risk_threshold = 80.0
        alert.notification_email = "updated@example.com"
        alert.save()
        
        updated_alert = Alert.query.get(alert.id)
        assert updated_alert.risk_threshold == 80.0
        assert updated_alert.notification_email == "updated@example.com"
    
    def test_alert_delete(self, client, sample_alert):
        """Test deleting an alert"""
        alert = sample_alert
        alert.save()
        alert_id = alert.id
        
        alert.delete()
        
        deleted_alert = Alert.query.get(alert_id)
        assert deleted_alert is None


class TestModelRelationships:
    """Test model relationships"""
    
    def test_supplier_alert_relationship(self, client, sample_supplier, sample_alert):
        """Test supplier-alert relationship"""
        supplier = sample_supplier
        supplier.save()
        
        alert = sample_alert
        alert.supplier_id = supplier.id
        alert.save()
        
        # Test supplier has alert
        supplier_alerts = Alert.query.filter_by(supplier_id=supplier.id).all()
        assert len(supplier_alerts) == 1
        assert supplier_alerts[0].id == alert.id
        
        # Test alert belongs to supplier
        alert_supplier = Supplier.query.get(alert.supplier_id)
        assert alert_supplier.id == supplier.id
