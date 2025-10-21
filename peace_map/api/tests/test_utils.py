"""
Utility tests for Peace Map API
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


class TestDataValidation:
    """Test data validation utilities"""
    
    def test_event_data_validation(self, client):
        """Test event data validation"""
        # Valid event data
        valid_data = {
            "title": "Test Event",
            "description": "Test Description",
            "event_type": "protest",
            "location": "Test Location",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "source": "Test Source",
            "source_confidence": 0.8,
            "published_at": datetime.utcnow(),
            "tags": ["test", "event"]
        }
        
        event = Event(**valid_data)
        assert event.title == "Test Event"
        assert event.event_type == "protest"
        assert event.source_confidence == 0.8
        
        # Invalid event data
        invalid_data = {
            "title": "",  # Empty title
            "description": "Test Description",
            "event_type": "protest",
            "location": "Test Location",
            "source": "Test Source",
            "source_confidence": 0.8
        }
        
        with pytest.raises(ValueError):
            Event(**invalid_data)
    
    def test_supplier_data_validation(self, client):
        """Test supplier data validation"""
        # Valid supplier data
        valid_data = {
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
        
        supplier = Supplier(**valid_data)
        assert supplier.name == "Test Supplier"
        assert supplier.contact_email == "test@example.com"
        assert supplier.website == "https://example.com"
        
        # Invalid supplier data
        invalid_data = {
            "name": "",  # Empty name
            "location": "Test Location",
            "contact_email": "invalid-email"  # Invalid email
        }
        
        with pytest.raises(ValueError):
            Supplier(**invalid_data)
    
    def test_alert_data_validation(self, client):
        """Test alert data validation"""
        # Valid alert data
        valid_data = {
            "supplier_id": 1,
            "risk_threshold": 75.0,
            "notification_email": "alert@example.com",
            "notification_phone": "+1234567890",
            "description": "Test Alert",
            "tags": ["test", "alert"]
        }
        
        alert = Alert(**valid_data)
        assert alert.supplier_id == 1
        assert alert.risk_threshold == 75.0
        assert alert.notification_email == "alert@example.com"
        
        # Invalid alert data
        invalid_data = {
            "supplier_id": 1,
            "risk_threshold": 150.0,  # Invalid threshold
            "notification_email": "invalid-email"  # Invalid email
        }
        
        with pytest.raises(ValueError):
            Alert(**invalid_data)


class TestDataRelationships:
    """Test data relationships"""
    
    def test_supplier_alert_relationship(self, client):
        """Test supplier-alert relationship"""
        # Create supplier
        supplier = Supplier(
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
        supplier.save()
        
        # Create alert for supplier
        alert = Alert(
            supplier_id=supplier.id,
            risk_threshold=75.0,
            notification_email="alert@example.com",
            notification_phone="+1234567890",
            description="Test Alert",
            tags=["test", "alert"]
        )
        alert.save()
        
        # Verify relationship
        assert alert.supplier_id == supplier.id
        
        # Test supplier has alert
        supplier_alerts = Alert.query.filter_by(supplier_id=supplier.id).all()
        assert len(supplier_alerts) == 1
        assert supplier_alerts[0].id == alert.id
        
        # Test alert belongs to supplier
        alert_supplier = Supplier.query.get(alert.supplier_id)
        assert alert_supplier.id == supplier.id
    
    def test_event_project_relationship(self, client):
        """Test event-project relationship"""
        # Create event
        event = Event(
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
        event.save()
        
        # Verify relationship
        assert event.project_id == 1
        
        # Test project has event
        project_events = Event.query.filter_by(project_id=1).all()
        assert len(project_events) == 1
        assert project_events[0].id == event.id


class TestDataPersistence:
    """Test data persistence"""
    
    def test_event_persistence(self, client):
        """Test event data persistence"""
        # Create event
        event = Event(
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
        event.save()
        
        # Verify event is saved
        assert event.id is not None
        
        # Retrieve event
        retrieved_event = Event.query.get(event.id)
        assert retrieved_event is not None
        assert retrieved_event.title == "Test Event"
        assert retrieved_event.event_type == "protest"
        assert retrieved_event.source_confidence == 0.8
        
        # Update event
        retrieved_event.title = "Updated Event"
        retrieved_event.description = "Updated Description"
        retrieved_event.save()
        
        # Verify update
        updated_event = Event.query.get(event.id)
        assert updated_event.title == "Updated Event"
        assert updated_event.description == "Updated Description"
        
        # Delete event
        updated_event.delete()
        
        # Verify deletion
        deleted_event = Event.query.get(event.id)
        assert deleted_event is None
    
    def test_supplier_persistence(self, client):
        """Test supplier data persistence"""
        # Create supplier
        supplier = Supplier(
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
        supplier.save()
        
        # Verify supplier is saved
        assert supplier.id is not None
        
        # Retrieve supplier
        retrieved_supplier = Supplier.query.get(supplier.id)
        assert retrieved_supplier is not None
        assert retrieved_supplier.name == "Test Supplier"
        assert retrieved_supplier.contact_email == "test@example.com"
        assert retrieved_supplier.website == "https://example.com"
        
        # Update supplier
        retrieved_supplier.name = "Updated Supplier"
        retrieved_supplier.contact_email = "updated@example.com"
        retrieved_supplier.save()
        
        # Verify update
        updated_supplier = Supplier.query.get(supplier.id)
        assert updated_supplier.name == "Updated Supplier"
        assert updated_supplier.contact_email == "updated@example.com"
        
        # Delete supplier
        updated_supplier.delete()
        
        # Verify deletion
        deleted_supplier = Supplier.query.get(supplier.id)
        assert deleted_supplier is None
    
    def test_alert_persistence(self, client):
        """Test alert data persistence"""
        # Create supplier first
        supplier = Supplier(
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
        supplier.save()
        
        # Create alert
        alert = Alert(
            supplier_id=supplier.id,
            risk_threshold=75.0,
            notification_email="alert@example.com",
            notification_phone="+1234567890",
            description="Test Alert",
            tags=["test", "alert"]
        )
        alert.save()
        
        # Verify alert is saved
        assert alert.id is not None
        
        # Retrieve alert
        retrieved_alert = Alert.query.get(alert.id)
        assert retrieved_alert is not None
        assert retrieved_alert.supplier_id == supplier.id
        assert retrieved_alert.risk_threshold == 75.0
        assert retrieved_alert.notification_email == "alert@example.com"
        
        # Update alert
        retrieved_alert.risk_threshold = 80.0
        retrieved_alert.notification_email = "updated@example.com"
        retrieved_alert.save()
        
        # Verify update
        updated_alert = Alert.query.get(alert.id)
        assert updated_alert.risk_threshold == 80.0
        assert updated_alert.notification_email == "updated@example.com"
        
        # Delete alert
        updated_alert.delete()
        
        # Verify deletion
        deleted_alert = Alert.query.get(alert.id)
        assert deleted_alert is None


class TestDataQueries:
    """Test data queries"""
    
    def test_event_queries(self, client):
        """Test event queries"""
        # Create multiple events
        events_data = [
            {
                "project_id": 1,
                "title": "Protest Event",
                "description": "Protest Description",
                "event_type": "protest",
                "location": "City A",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "source": "Source 1",
                "source_confidence": 0.8,
                "published_at": datetime.utcnow(),
                "tags": ["protest", "city-a"]
            },
            {
                "project_id": 1,
                "title": "Cyber Event",
                "description": "Cyber Description",
                "event_type": "cyber",
                "location": "City B",
                "latitude": 41.8781,
                "longitude": -87.6298,
                "source": "Source 2",
                "source_confidence": 0.9,
                "published_at": datetime.utcnow(),
                "tags": ["cyber", "city-b"]
            }
        ]
        
        for event_data in events_data:
            event = Event(**event_data)
            event.save()
        
        # Query all events
        all_events = Event.query.all()
        assert len(all_events) == 2
        
        # Query events by project
        project_events = Event.query.filter_by(project_id=1).all()
        assert len(project_events) == 2
        
        # Query events by type
        protest_events = Event.query.filter_by(event_type="protest").all()
        assert len(protest_events) == 1
        assert protest_events[0].title == "Protest Event"
        
        cyber_events = Event.query.filter_by(event_type="cyber").all()
        assert len(cyber_events) == 1
        assert cyber_events[0].title == "Cyber Event"
        
        # Query events by location
        city_a_events = Event.query.filter_by(location="City A").all()
        assert len(city_a_events) == 1
        assert city_a_events[0].title == "Protest Event"
        
        city_b_events = Event.query.filter_by(location="City B").all()
        assert len(city_b_events) == 1
        assert city_b_events[0].title == "Cyber Event"
        
        # Query events by source confidence
        high_confidence_events = Event.query.filter(Event.source_confidence >= 0.9).all()
        assert len(high_confidence_events) == 1
        assert high_confidence_events[0].title == "Cyber Event"
        
        # Query events by tags
        protest_tag_events = Event.query.filter(Event.tags.contains(["protest"])).all()
        assert len(protest_tag_events) == 1
        assert protest_tag_events[0].title == "Protest Event"
        
        cyber_tag_events = Event.query.filter(Event.tags.contains(["cyber"])).all()
        assert len(cyber_tag_events) == 1
        assert cyber_tag_events[0].title == "Cyber Event"
    
    def test_supplier_queries(self, client):
        """Test supplier queries"""
        # Create multiple suppliers
        suppliers_data = [
            {
                "name": "Supplier A",
                "location": "City A",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "contact_email": "supplier-a@example.com",
                "contact_phone": "+1234567890",
                "website": "https://supplier-a.com",
                "description": "Supplier A Description",
                "tags": ["supplier", "city-a"]
            },
            {
                "name": "Supplier B",
                "location": "City B",
                "latitude": 41.8781,
                "longitude": -87.6298,
                "contact_email": "supplier-b@example.com",
                "contact_phone": "+1234567891",
                "website": "https://supplier-b.com",
                "description": "Supplier B Description",
                "tags": ["supplier", "city-b"]
            }
        ]
        
        for supplier_data in suppliers_data:
            supplier = Supplier(**supplier_data)
            supplier.save()
        
        # Query all suppliers
        all_suppliers = Supplier.query.all()
        assert len(all_suppliers) == 2
        
        # Query suppliers by name
        supplier_a = Supplier.query.filter_by(name="Supplier A").first()
        assert supplier_a is not None
        assert supplier_a.location == "City A"
        assert supplier_a.contact_email == "supplier-a@example.com"
        
        supplier_b = Supplier.query.filter_by(name="Supplier B").first()
        assert supplier_b is not None
        assert supplier_b.location == "City B"
        assert supplier_b.contact_email == "supplier-b@example.com"
        
        # Query suppliers by location
        city_a_suppliers = Supplier.query.filter_by(location="City A").all()
        assert len(city_a_suppliers) == 1
        assert city_a_suppliers[0].name == "Supplier A"
        
        city_b_suppliers = Supplier.query.filter_by(location="City B").all()
        assert len(city_b_suppliers) == 1
        assert city_b_suppliers[0].name == "Supplier B"
        
        # Query suppliers by tags
        city_a_tag_suppliers = Supplier.query.filter(Supplier.tags.contains(["city-a"])).all()
        assert len(city_a_tag_suppliers) == 1
        assert city_a_tag_suppliers[0].name == "Supplier A"
        
        city_b_tag_suppliers = Supplier.query.filter(Supplier.tags.contains(["city-b"])).all()
        assert len(city_b_tag_suppliers) == 1
        assert city_b_tag_suppliers[0].name == "Supplier B"
    
    def test_alert_queries(self, client):
        """Test alert queries"""
        # Create supplier first
        supplier = Supplier(
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
        supplier.save()
        
        # Create multiple alerts
        alerts_data = [
            {
                "supplier_id": supplier.id,
                "risk_threshold": 70.0,
                "notification_email": "alert-1@example.com",
                "notification_phone": "+1234567890",
                "description": "Alert 1",
                "tags": ["alert", "threshold-70"]
            },
            {
                "supplier_id": supplier.id,
                "risk_threshold": 80.0,
                "notification_email": "alert-2@example.com",
                "notification_phone": "+1234567891",
                "description": "Alert 2",
                "tags": ["alert", "threshold-80"]
            }
        ]
        
        for alert_data in alerts_data:
            alert = Alert(**alert_data)
            alert.save()
        
        # Query all alerts
        all_alerts = Alert.query.all()
        assert len(all_alerts) == 2
        
        # Query alerts by supplier
        supplier_alerts = Alert.query.filter_by(supplier_id=supplier.id).all()
        assert len(supplier_alerts) == 2
        
        # Query alerts by risk threshold
        low_threshold_alerts = Alert.query.filter(Alert.risk_threshold <= 75.0).all()
        assert len(low_threshold_alerts) == 1
        assert low_threshold_alerts[0].risk_threshold == 70.0
        
        high_threshold_alerts = Alert.query.filter(Alert.risk_threshold >= 75.0).all()
        assert len(high_threshold_alerts) == 1
        assert high_threshold_alerts[0].risk_threshold == 80.0
        
        # Query alerts by tags
        threshold_70_alerts = Alert.query.filter(Alert.tags.contains(["threshold-70"])).all()
        assert len(threshold_70_alerts) == 1
        assert threshold_70_alerts[0].risk_threshold == 70.0
        
        threshold_80_alerts = Alert.query.filter(Alert.tags.contains(["threshold-80"])).all()
        assert len(threshold_80_alerts) == 1
        assert threshold_80_alerts[0].risk_threshold == 80.0
