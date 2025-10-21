"""
End-to-end tests for Peace Map API
"""

import pytest
import json
import time
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


class TestCompleteWorkflow:
    """Test complete end-to-end workflow"""
    
    def test_complete_peace_map_workflow(self, client, auth_headers):
        """Test complete Peace Map workflow"""
        # Step 1: Create events
        events_data = [
            {
                "title": "Protest in City A",
                "description": "Large protest in City A",
                "event_type": "protest",
                "location": "City A",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "source": "News Source 1",
                "source_confidence": 0.9,
                "published_at": datetime.utcnow().isoformat(),
                "tags": ["protest", "city-a"]
            },
            {
                "title": "Cyber Attack on Infrastructure",
                "description": "Cyber attack on critical infrastructure",
                "event_type": "cyber",
                "location": "City B",
                "latitude": 41.8781,
                "longitude": -87.6298,
                "source": "Security Source",
                "source_confidence": 0.95,
                "published_at": datetime.utcnow().isoformat(),
                "tags": ["cyber", "infrastructure"]
            }
        ]
        
        event_ids = []
        for event_data in events_data:
            response = client.post(
                "/api/v1/projects/1/events",
                data=json.dumps(event_data),
                headers=auth_headers
            )
            assert response.status_code == 200
            
            data = json.loads(response.data)
            event_ids.append(data["data"]["id"])
        
        # Step 2: Create suppliers
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
        
        supplier_ids = []
        for supplier_data in suppliers_data:
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
            
            data = json.loads(response.data)
            supplier_ids.append(data["data"]["id"])
        
        # Step 3: Create risk indices
        risk_indices_data = [
            {
                "region": "City A",
                "date": date.today().isoformat(),
                "composite_score": 75.5,
                "event_count": 5,
                "sentiment_score": 0.6,
                "proximity_score": 0.8,
                "risk_level": "high"
            },
            {
                "region": "City B",
                "date": date.today().isoformat(),
                "composite_score": 85.0,
                "event_count": 8,
                "sentiment_score": 0.4,
                "proximity_score": 0.9,
                "risk_level": "critical"
            }
        ]
        
        for risk_data in risk_indices_data:
            risk_index = RiskIndex(**risk_data)
            risk_index.save()
        
        # Step 4: Create alerts
        alerts_data = [
            {
                "supplier_id": supplier_ids[0],
                "risk_threshold": 70.0,
                "notification_email": "alert-a@example.com",
                "notification_phone": "+1234567890",
                "description": "Alert for Supplier A",
                "tags": ["alert", "supplier-a"]
            },
            {
                "supplier_id": supplier_ids[1],
                "risk_threshold": 80.0,
                "notification_email": "alert-b@example.com",
                "notification_phone": "+1234567891",
                "description": "Alert for Supplier B",
                "tags": ["alert", "supplier-b"]
            }
        ]
        
        alert_ids = []
        for alert_data in alerts_data:
            response = client.post(
                "/api/v1/alerts",
                data=json.dumps(alert_data),
                headers=auth_headers
            )
            assert response.status_code == 200
            
            data = json.loads(response.data)
            alert_ids.append(data["data"]["id"])
        
        # Step 5: Test data retrieval and filtering
        # List events
        response = client.get("/api/v1/projects/1/events", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 2
        
        # Filter events by type
        response = client.get(
            "/api/v1/projects/1/events?event_type=protest",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["event_type"] == "protest"
        
        # List suppliers
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 2
        
        # Filter suppliers by location
        response = client.get(
            "/api/v1/suppliers?location=City A",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["location"] == "City A"
        
        # List risk indices
        response = client.get("/api/v1/risk-index", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 2
        
        # Filter risk indices by region
        response = client.get(
            "/api/v1/risk-index?region=City A",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["region"] == "City A"
        
        # List alerts
        response = client.get("/api/v1/alerts", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 2
        
        # Filter alerts by supplier
        response = client.get(
            f"/api/v1/alerts?supplier_id={supplier_ids[0]}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["supplier_id"] == supplier_ids[0]
        
        # Step 6: Test alert management
        # Acknowledge first alert
        response = client.post(
            f"/api/v1/alerts/{alert_ids[0]}/acknowledge",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["status"] == "acknowledged"
        
        # Resolve second alert
        response = client.post(
            f"/api/v1/alerts/{alert_ids[1]}/resolve",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["status"] == "resolved"
        
        # Step 7: Test data updates
        # Update event
        update_data = {
            "title": "Updated Protest in City A",
            "description": "Updated protest description"
        }
        
        response = client.put(
            f"/api/v1/projects/1/events/{event_ids[0]}",
            data=json.dumps(update_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["title"] == "Updated Protest in City A"
        assert data["data"]["description"] == "Updated protest description"
        
        # Update supplier
        update_data = {
            "name": "Updated Supplier A",
            "contact_email": "updated-supplier-a@example.com"
        }
        
        response = client.put(
            f"/api/v1/suppliers/{supplier_ids[0]}",
            data=json.dumps(update_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["name"] == "Updated Supplier A"
        assert data["data"]["contact_email"] == "updated-supplier-a@example.com"
        
        # Update alert
        update_data = {
            "risk_threshold": 85.0,
            "notification_email": "updated-alert-a@example.com"
        }
        
        response = client.put(
            f"/api/v1/alerts/{alert_ids[0]}",
            data=json.dumps(update_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["risk_threshold"] == 85.0
        assert data["data"]["notification_email"] == "updated-alert-a@example.com"
        
        # Step 8: Test data deletion
        # Delete event
        response = client.delete(f"/api/v1/projects/1/events/{event_ids[0]}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify event is deleted
        response = client.get(f"/api/v1/projects/1/events/{event_ids[0]}", headers=auth_headers)
        assert response.status_code == 404
        
        # Delete supplier
        response = client.delete(f"/api/v1/suppliers/{supplier_ids[0]}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify supplier is deleted
        response = client.get(f"/api/v1/suppliers/{supplier_ids[0]}", headers=auth_headers)
        assert response.status_code == 404
        
        # Delete alert
        response = client.delete(f"/api/v1/alerts/{alert_ids[0]}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify alert is deleted
        response = client.get(f"/api/v1/alerts/{alert_ids[0]}", headers=auth_headers)
        assert response.status_code == 404
        
        # Step 9: Verify remaining data
        # Check remaining events
        response = client.get("/api/v1/projects/1/events", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["event_type"] == "cyber"
        
        # Check remaining suppliers
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Supplier B"
        
        # Check remaining alerts
        response = client.get("/api/v1/alerts", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["supplier_id"] == supplier_ids[1]
        
        # Check risk indices
        response = client.get("/api/v1/risk-index", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 2  # Risk indices are not deleted
        assert data["pagination"]["total"] == 2


class TestErrorHandling:
    """Test error handling in end-to-end scenarios"""
    
    def test_error_handling_workflow(self, client, auth_headers):
        """Test error handling in complete workflow"""
        # Test invalid event creation
        invalid_event_data = {
            "title": "",  # Invalid title
            "description": "Test Description",
            "event_type": "protest",
            "location": "Test Location",
            "source": "Test Source",
            "source_confidence": 0.8
        }
        
        response = client.post(
            "/api/v1/projects/1/events",
            data=json.dumps(invalid_event_data),
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
        
        # Test invalid supplier creation
        invalid_supplier_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "contact_email": "invalid-email"  # Invalid email
        }
        
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps(invalid_supplier_data),
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
        
        # Test invalid alert creation (non-existent supplier)
        invalid_alert_data = {
            "supplier_id": 999,  # Non-existent supplier
            "risk_threshold": 75.0,
            "notification_email": "alert@example.com"
        }
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps(invalid_alert_data),
            headers=auth_headers
        )
        assert response.status_code == 404  # Not found error
        
        # Test invalid event update
        response = client.put(
            "/api/v1/projects/1/events/999",  # Non-existent event
            data=json.dumps({"title": "Updated Event"}),
            headers=auth_headers
        )
        assert response.status_code == 404  # Not found error
        
        # Test invalid supplier update
        response = client.put(
            "/api/v1/suppliers/999",  # Non-existent supplier
            data=json.dumps({"name": "Updated Supplier"}),
            headers=auth_headers
        )
        assert response.status_code == 404  # Not found error
        
        # Test invalid alert update
        response = client.put(
            "/api/v1/alerts/999",  # Non-existent alert
            data=json.dumps({"risk_threshold": 80.0}),
            headers=auth_headers
        )
        assert response.status_code == 404  # Not found error
        
        # Test invalid alert acknowledgment
        response = client.post(
            "/api/v1/alerts/999/acknowledge",  # Non-existent alert
            headers=auth_headers
        )
        assert response.status_code == 404  # Not found error
        
        # Test invalid alert resolution
        response = client.post(
            "/api/v1/alerts/999/resolve",  # Non-existent alert
            headers=auth_headers
        )
        assert response.status_code == 404  # Not found error
        
        # Test invalid event deletion
        response = client.delete("/api/v1/projects/1/events/999", headers=auth_headers)
        assert response.status_code == 404  # Not found error
        
        # Test invalid supplier deletion
        response = client.delete("/api/v1/suppliers/999", headers=auth_headers)
        assert response.status_code == 404  # Not found error
        
        # Test invalid alert deletion
        response = client.delete("/api/v1/alerts/999", headers=auth_headers)
        assert response.status_code == 404  # Not found error


class TestPerformance:
    """Test performance in end-to-end scenarios"""
    
    def test_performance_workflow(self, client, auth_headers):
        """Test performance in complete workflow"""
        start_time = time.time()
        
        # Create multiple events
        for i in range(10):
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
        
        # Create multiple suppliers
        for i in range(10):
            supplier_data = {
                "name": f"Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"supplier-{i}@example.com",
                "contact_phone": f"+123456789{i}",
                "website": f"https://supplier-{i}.com",
                "description": f"Supplier {i} Description",
                "tags": ["test", "supplier"]
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # List events with pagination
        response = client.get(
            "/api/v1/projects/1/events?page=1&size=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 5
        assert data["pagination"]["total"] == 10
        
        # List suppliers with pagination
        response = client.get(
            "/api/v1/suppliers?page=1&size=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 5
        assert data["pagination"]["total"] == 10
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        assert execution_time < 10.0  # 10 seconds max
        
        # Test filtering performance
        start_time = time.time()
        
        response = client.get(
            "/api/v1/projects/1/events?event_type=protest",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 10
        assert all(event["event_type"] == "protest" for event in data["data"])
        
        end_time = time.time()
        filtering_time = end_time - start_time
        
        # Filtering should be fast
        assert filtering_time < 1.0  # 1 second max
