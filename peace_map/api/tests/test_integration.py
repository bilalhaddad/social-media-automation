"""
Integration tests for Peace Map API
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


class TestEventWorkflow:
    """Test complete event workflow"""
    
    def test_create_event_workflow(self, client, auth_headers):
        """Test complete event creation workflow"""
        # Create event
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
        
        response = client.post(
            "/api/v1/projects/1/events",
            data=json.dumps(event_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        event_id = data["data"]["id"]
        
        # Get event
        response = client.get(f"/api/v1/projects/1/events/{event_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["title"] == "Test Event"
        assert data["data"]["event_type"] == "protest"
        
        # Update event
        update_data = {
            "title": "Updated Event",
            "description": "Updated Description"
        }
        
        response = client.put(
            f"/api/v1/projects/1/events/{event_id}",
            data=json.dumps(update_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["title"] == "Updated Event"
        assert data["data"]["description"] == "Updated Description"
        
        # Delete event
        response = client.delete(f"/api/v1/projects/1/events/{event_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify event is deleted
        response = client.get(f"/api/v1/projects/1/events/{event_id}", headers=auth_headers)
        assert response.status_code == 404


class TestSupplierWorkflow:
    """Test complete supplier workflow"""
    
    def test_create_supplier_workflow(self, client, auth_headers):
        """Test complete supplier creation workflow"""
        # Create supplier
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
        
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps(supplier_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        supplier_id = data["data"]["id"]
        
        # Get supplier
        response = client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["name"] == "Test Supplier"
        assert data["data"]["contact_email"] == "test@example.com"
        
        # Update supplier
        update_data = {
            "name": "Updated Supplier",
            "contact_email": "updated@example.com"
        }
        
        response = client.put(
            f"/api/v1/suppliers/{supplier_id}",
            data=json.dumps(update_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["name"] == "Updated Supplier"
        assert data["data"]["contact_email"] == "updated@example.com"
        
        # Delete supplier
        response = client.delete(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify supplier is deleted
        response = client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 404


class TestAlertWorkflow:
    """Test complete alert workflow"""
    
    def test_create_alert_workflow(self, client, auth_headers):
        """Test complete alert creation workflow"""
        # Create supplier first
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
        
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps(supplier_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        supplier_id = data["data"]["id"]
        
        # Create alert
        alert_data = {
            "supplier_id": supplier_id,
            "risk_threshold": 75.0,
            "notification_email": "alert@example.com",
            "notification_phone": "+1234567890",
            "description": "Test Alert",
            "tags": ["test", "alert"]
        }
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps(alert_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        alert_id = data["data"]["id"]
        
        # Get alert
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["supplier_id"] == supplier_id
        assert data["data"]["risk_threshold"] == 75.0
        
        # Acknowledge alert
        response = client.post(f"/api/v1/alerts/{alert_id}/acknowledge", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["status"] == "acknowledged"
        
        # Resolve alert
        response = client.post(f"/api/v1/alerts/{alert_id}/resolve", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["status"] == "resolved"
        
        # Delete alert
        response = client.delete(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify alert is deleted
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 404


class TestDataRelationships:
    """Test data relationships"""
    
    def test_supplier_alert_relationship(self, client, auth_headers):
        """Test supplier-alert relationship"""
        # Create supplier
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
        
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps(supplier_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        supplier_id = data["data"]["id"]
        
        # Create alert for supplier
        alert_data = {
            "supplier_id": supplier_id,
            "risk_threshold": 75.0,
            "notification_email": "alert@example.com",
            "notification_phone": "+1234567890",
            "description": "Test Alert",
            "tags": ["test", "alert"]
        }
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps(alert_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        alert_id = data["data"]["id"]
        
        # Verify relationship
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["supplier_id"] == supplier_id
        
        # List alerts for supplier
        response = client.get(f"/api/v1/alerts?supplier_id={supplier_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["supplier_id"] == supplier_id


class TestFilteringAndPagination:
    """Test filtering and pagination"""
    
    def test_event_filtering(self, client, auth_headers):
        """Test event filtering"""
        # Create multiple events
        events_data = [
            {
                "title": "Protest Event",
                "description": "Protest Description",
                "event_type": "protest",
                "location": "Test Location",
                "source": "Test Source",
                "source_confidence": 0.8,
                "published_at": datetime.utcnow().isoformat(),
                "tags": ["test", "protest"]
            },
            {
                "title": "Cyber Event",
                "description": "Cyber Description",
                "event_type": "cyber",
                "location": "Test Location",
                "source": "Test Source",
                "source_confidence": 0.9,
                "published_at": datetime.utcnow().isoformat(),
                "tags": ["test", "cyber"]
            }
        ]
        
        for event_data in events_data:
            response = client.post(
                "/api/v1/projects/1/events",
                data=json.dumps(event_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Filter by event type
        response = client.get(
            "/api/v1/projects/1/events?event_type=protest",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["event_type"] == "protest"
        
        # Filter by source confidence
        response = client.get(
            "/api/v1/projects/1/events?source_confidence=0.9",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["source_confidence"] == 0.9
    
    def test_supplier_filtering(self, client, auth_headers):
        """Test supplier filtering"""
        # Create multiple suppliers
        suppliers_data = [
            {
                "name": "Supplier A",
                "location": "Location A",
                "contact_email": "supplier-a@example.com",
                "contact_phone": "+1234567890",
                "website": "https://supplier-a.com",
                "description": "Supplier A Description",
                "tags": ["test", "supplier-a"]
            },
            {
                "name": "Supplier B",
                "location": "Location B",
                "contact_email": "supplier-b@example.com",
                "contact_phone": "+1234567891",
                "website": "https://supplier-b.com",
                "description": "Supplier B Description",
                "tags": ["test", "supplier-b"]
            }
        ]
        
        for supplier_data in suppliers_data:
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Filter by name
        response = client.get(
            "/api/v1/suppliers?name=Supplier A",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Supplier A"
        
        # Filter by location
        response = client.get(
            "/api/v1/suppliers?location=Location B",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["location"] == "Location B"
    
    def test_pagination(self, client, auth_headers):
        """Test pagination"""
        # Create multiple events
        for i in range(25):
            event_data = {
                "title": f"Event {i}",
                "description": f"Event {i} Description",
                "event_type": "protest",
                "location": f"Location {i}",
                "source": "Test Source",
                "source_confidence": 0.8,
                "published_at": datetime.utcnow().isoformat(),
                "tags": ["test", "event"]
            }
            
            response = client.post(
                "/api/v1/projects/1/events",
                data=json.dumps(event_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test first page
        response = client.get(
            "/api/v1/projects/1/events?page=1&size=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 10
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["size"] == 10
        assert data["pagination"]["total"] == 25
        assert data["pagination"]["pages"] == 3
        
        # Test second page
        response = client.get(
            "/api/v1/projects/1/events?page=2&size=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 10
        assert data["pagination"]["page"] == 2
        
        # Test last page
        response = client.get(
            "/api/v1/projects/1/events?page=3&size=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 5  # Remaining events
        assert data["pagination"]["page"] == 3
