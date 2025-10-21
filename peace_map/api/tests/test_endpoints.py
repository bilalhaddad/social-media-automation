"""
Tests for Peace Map API endpoints
"""

import pytest
import json
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
def auth_headers():
    """Authentication headers fixture"""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def sample_event_data():
    """Sample event data fixture"""
    return {
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


@pytest.fixture
def sample_supplier_data():
    """Sample supplier data fixture"""
    return {
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


@pytest.fixture
def sample_alert_data():
    """Sample alert data fixture"""
    return {
        "supplier_id": 1,
        "risk_threshold": 75.0,
        "notification_email": "alert@example.com",
        "notification_phone": "+1234567890",
        "description": "Test Alert",
        "tags": ["test", "alert"]
    }


class TestEventEndpoints:
    """Test event endpoints"""
    
    def test_list_events(self, client, auth_headers):
        """Test listing events"""
        # Create test event
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
        
        # Test list events
        response = client.get("/api/v1/projects/1/events", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "Test Event"
    
    def test_get_event(self, client, auth_headers):
        """Test getting a specific event"""
        # Create test event
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
        
        # Test get event
        response = client.get(f"/api/v1/projects/1/events/{event.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["title"] == "Test Event"
        assert data["data"]["event_type"] == "protest"
    
    def test_create_event(self, client, auth_headers, sample_event_data):
        """Test creating an event"""
        response = client.post(
            "/api/v1/projects/1/events",
            data=json.dumps(sample_event_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["title"] == "Test Event"
        assert data["data"]["event_type"] == "protest"
    
    def test_update_event(self, client, auth_headers):
        """Test updating an event"""
        # Create test event
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
        
        # Update event
        update_data = {
            "title": "Updated Event",
            "description": "Updated Description"
        }
        
        response = client.put(
            f"/api/v1/projects/1/events/{event.id}",
            data=json.dumps(update_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["title"] == "Updated Event"
        assert data["data"]["description"] == "Updated Description"
    
    def test_delete_event(self, client, auth_headers):
        """Test deleting an event"""
        # Create test event
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
        
        # Delete event
        response = client.delete(f"/api/v1/projects/1/events/{event.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        
        # Verify event is deleted
        deleted_event = Event.query.get(event.id)
        assert deleted_event is None


class TestRiskIndexEndpoints:
    """Test risk index endpoints"""
    
    def test_get_risk_index(self, client, auth_headers):
        """Test getting risk index data"""
        # Create test risk index
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
        
        # Test get risk index
        response = client.get("/api/v1/risk-index", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["region"] == "Test Region"
        assert data["data"][0]["composite_score"] == 75.5


class TestSupplierEndpoints:
    """Test supplier endpoints"""
    
    def test_list_suppliers(self, client, auth_headers):
        """Test listing suppliers"""
        # Create test supplier
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
        
        # Test list suppliers
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Test Supplier"
    
    def test_get_supplier(self, client, auth_headers):
        """Test getting a specific supplier"""
        # Create test supplier
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
        
        # Test get supplier
        response = client.get(f"/api/v1/suppliers/{supplier.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["name"] == "Test Supplier"
        assert data["data"]["contact_email"] == "test@example.com"
    
    def test_create_supplier(self, client, auth_headers, sample_supplier_data):
        """Test creating a supplier"""
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps(sample_supplier_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["name"] == "Test Supplier"
        assert data["data"]["contact_email"] == "test@example.com"
    
    def test_update_supplier(self, client, auth_headers):
        """Test updating a supplier"""
        # Create test supplier
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
        
        # Update supplier
        update_data = {
            "name": "Updated Supplier",
            "contact_email": "updated@example.com"
        }
        
        response = client.put(
            f"/api/v1/suppliers/{supplier.id}",
            data=json.dumps(update_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Supplier"
        assert data["data"]["contact_email"] == "updated@example.com"
    
    def test_delete_supplier(self, client, auth_headers):
        """Test deleting a supplier"""
        # Create test supplier
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
        
        # Delete supplier
        response = client.delete(f"/api/v1/suppliers/{supplier.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        
        # Verify supplier is deleted
        deleted_supplier = Supplier.query.get(supplier.id)
        assert deleted_supplier is None


class TestAlertEndpoints:
    """Test alert endpoints"""
    
    def test_list_alerts(self, client, auth_headers):
        """Test listing alerts"""
        # Create test supplier and alert
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
        
        alert = Alert(
            supplier_id=supplier.id,
            risk_threshold=75.0,
            notification_email="alert@example.com",
            notification_phone="+1234567890",
            description="Test Alert",
            tags=["test", "alert"]
        )
        alert.save()
        
        # Test list alerts
        response = client.get("/api/v1/alerts", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["supplier_id"] == supplier.id
        assert data["data"][0]["risk_threshold"] == 75.0
    
    def test_get_alert(self, client, auth_headers):
        """Test getting a specific alert"""
        # Create test supplier and alert
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
        
        alert = Alert(
            supplier_id=supplier.id,
            risk_threshold=75.0,
            notification_email="alert@example.com",
            notification_phone="+1234567890",
            description="Test Alert",
            tags=["test", "alert"]
        )
        alert.save()
        
        # Test get alert
        response = client.get(f"/api/v1/alerts/{alert.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["supplier_id"] == supplier.id
        assert data["data"]["risk_threshold"] == 75.0
    
    def test_create_alert(self, client, auth_headers, sample_alert_data):
        """Test creating an alert"""
        # Create test supplier first
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
        
        # Update alert data with supplier ID
        sample_alert_data["supplier_id"] = supplier.id
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps(sample_alert_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["supplier_id"] == supplier.id
        assert data["data"]["risk_threshold"] == 75.0
    
    def test_update_alert(self, client, auth_headers):
        """Test updating an alert"""
        # Create test supplier and alert
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
        
        alert = Alert(
            supplier_id=supplier.id,
            risk_threshold=75.0,
            notification_email="alert@example.com",
            notification_phone="+1234567890",
            description="Test Alert",
            tags=["test", "alert"]
        )
        alert.save()
        
        # Update alert
        update_data = {
            "risk_threshold": 80.0,
            "notification_email": "updated@example.com"
        }
        
        response = client.put(
            f"/api/v1/alerts/{alert.id}",
            data=json.dumps(update_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["risk_threshold"] == 80.0
        assert data["data"]["notification_email"] == "updated@example.com"
    
    def test_delete_alert(self, client, auth_headers):
        """Test deleting an alert"""
        # Create test supplier and alert
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
        
        alert = Alert(
            supplier_id=supplier.id,
            risk_threshold=75.0,
            notification_email="alert@example.com",
            notification_phone="+1234567890",
            description="Test Alert",
            tags=["test", "alert"]
        )
        alert.save()
        
        # Delete alert
        response = client.delete(f"/api/v1/alerts/{alert.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        
        # Verify alert is deleted
        deleted_alert = Alert.query.get(alert.id)
        assert deleted_alert is None
    
    def test_acknowledge_alert(self, client, auth_headers):
        """Test acknowledging an alert"""
        # Create test supplier and alert
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
        
        alert = Alert(
            supplier_id=supplier.id,
            risk_threshold=75.0,
            notification_email="alert@example.com",
            notification_phone="+1234567890",
            description="Test Alert",
            tags=["test", "alert"]
        )
        alert.save()
        
        # Acknowledge alert
        response = client.post(f"/api/v1/alerts/{alert.id}/acknowledge", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["status"] == "acknowledged"
    
    def test_resolve_alert(self, client, auth_headers):
        """Test resolving an alert"""
        # Create test supplier and alert
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
        
        alert = Alert(
            supplier_id=supplier.id,
            risk_threshold=75.0,
            notification_email="alert@example.com",
            notification_phone="+1234567890",
            description="Test Alert",
            tags=["test", "alert"]
        )
        alert.save()
        
        # Resolve alert
        response = client.post(f"/api/v1/alerts/{alert.id}/resolve", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["status"] == "resolved"
