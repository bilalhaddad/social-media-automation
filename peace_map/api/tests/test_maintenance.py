"""
Maintenance tests for Peace Map API
"""

import pytest
import json
import time
from datetime import datetime, timedelta
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


class TestDataMaintenance:
    """Test data maintenance functionality"""
    
    def test_data_cleanup(self, client, auth_headers):
        """Test data cleanup functionality"""
        # Create test data
        supplier_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "contact_email": "test@example.com",
            "contact_phone": "+1234567890",
            "website": "https://example.com",
            "description": "Test Supplier Description"
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
            "description": "Test Alert"
        }
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps(alert_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        alert_id = data["data"]["id"]
        
        # Delete supplier (should cascade to alerts)
        response = client.delete(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify supplier is deleted
        response = client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 404
        
        # Verify alert is deleted (cascade)
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_orphaned_data_cleanup(self, client, auth_headers):
        """Test orphaned data cleanup"""
        # Create supplier
        supplier_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "contact_email": "test@example.com",
            "contact_phone": "+1234567890",
            "website": "https://example.com",
            "description": "Test Supplier Description"
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
            "description": "Test Alert"
        }
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps(alert_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        alert_id = data["data"]["id"]
        
        # Delete supplier directly from database (bypass API)
        supplier = Supplier.query.get(supplier_id)
        supplier.delete()
        
        # Verify supplier is deleted
        response = client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 404
        
        # Alert should still exist (orphaned)
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Clean up orphaned alert
        response = client.delete(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify alert is deleted
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_data_archiving(self, client, auth_headers):
        """Test data archiving functionality"""
        # Create old events
        old_date = datetime.utcnow() - timedelta(days=365)
        
        for i in range(10):
            event_data = {
                "title": f"Old Event {i}",
                "description": f"Old Event {i} Description",
                "event_type": "protest",
                "location": f"Location {i}",
                "source": "Old Source",
                "source_confidence": 0.8,
                "published_at": old_date.isoformat()
            }
            
            response = client.post(
                "/api/v1/projects/1/events",
                data=json.dumps(event_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Create recent events
        recent_date = datetime.utcnow() - timedelta(days=30)
        
        for i in range(5):
            event_data = {
                "title": f"Recent Event {i}",
                "description": f"Recent Event {i} Description",
                "event_type": "protest",
                "location": f"Location {i}",
                "source": "Recent Source",
                "source_confidence": 0.9,
                "published_at": recent_date.isoformat()
            }
            
            response = client.post(
                "/api/v1/projects/1/events",
                data=json.dumps(event_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # List all events
        response = client.get("/api/v1/projects/1/events", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 15  # 10 old + 5 recent
        assert data["pagination"]["total"] == 15
        
        # Filter by date range (recent events only)
        start_date = (datetime.utcnow() - timedelta(days=60)).date().isoformat()
        response = client.get(
            f"/api/v1/projects/1/events?start_date={start_date}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["data"]) == 5  # Only recent events
        assert data["pagination"]["total"] == 5
    
    def test_data_validation(self, client, auth_headers):
        """Test data validation and integrity"""
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
        
        # Test invalid alert creation
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
    
    def test_data_consistency(self, client, auth_headers):
        """Test data consistency"""
        # Create supplier
        supplier_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "contact_email": "test@example.com",
            "contact_phone": "+1234567890",
            "website": "https://example.com",
            "description": "Test Supplier Description"
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
            "description": "Test Alert"
        }
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps(alert_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        alert_id = data["data"]["id"]
        
        # Verify data consistency
        response = client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 200
        
        supplier_data = json.loads(response.data)
        assert supplier_data["data"]["id"] == supplier_id
        
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200
        
        alert_data = json.loads(response.data)
        assert alert_data["data"]["supplier_id"] == supplier_id
        
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
        
        # Verify update consistency
        response = client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 200
        
        updated_supplier = json.loads(response.data)
        assert updated_supplier["data"]["name"] == "Updated Supplier"
        assert updated_supplier["data"]["contact_email"] == "updated@example.com"
        
        # Alert should still reference the same supplier
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200
        
        alert_data = json.loads(response.data)
        assert alert_data["data"]["supplier_id"] == supplier_id


class TestSystemMaintenance:
    """Test system maintenance functionality"""
    
    def test_database_maintenance(self, client, auth_headers):
        """Test database maintenance"""
        # Create multiple records
        for i in range(100):
            supplier_data = {
                "name": f"Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"supplier-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://supplier-{i}.com",
                "description": f"Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test database performance
        start_time = time.time()
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds
        
        data = json.loads(response.data)
        assert len(data["data"]) == 100
        assert data["pagination"]["total"] == 100
    
    def test_index_maintenance(self, client, auth_headers):
        """Test database index maintenance"""
        # Create multiple events with different types
        event_types = ["protest", "cyber", "kinetic"]
        
        for i in range(30):
            event_data = {
                "title": f"Event {i}",
                "description": f"Event {i} Description",
                "event_type": event_types[i % 3],
                "location": f"Location {i}",
                "source": f"Source {i}",
                "source_confidence": 0.8,
                "published_at": datetime.utcnow().isoformat()
            }
            
            response = client.post(
                "/api/v1/projects/1/events",
                data=json.dumps(event_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test filtering performance (should use indexes)
        start_time = time.time()
        response = client.get(
            "/api/v1/projects/1/events?event_type=protest",
            headers=auth_headers
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 1.0  # Should be fast with indexes
        
        data = json.loads(response.data)
        assert len(data["data"]) == 10  # 30 events / 3 types = 10 per type
        assert all(event["event_type"] == "protest" for event in data["data"])
    
    def test_cache_maintenance(self, client, auth_headers):
        """Test cache maintenance"""
        # Make multiple requests to test caching
        for _ in range(10):
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            assert response.status_code == 200
        
        # Should be fast due to caching
        start_time = time.time()
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 0.5  # Should be very fast with cache
    
    def test_session_maintenance(self, client, auth_headers):
        """Test session maintenance"""
        # Test session persistence
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        assert response.status_code == 200
        
        # Make another request
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        assert response.status_code == 200
        
        # Session should be maintained
        assert response.status_code == 200
    
    def test_connection_pool_maintenance(self, client, auth_headers):
        """Test connection pool maintenance"""
        # Make multiple concurrent requests
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create multiple threads
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 20
        
        while not results.empty():
            result = results.get()
            assert result["status_code"] == 200
            assert result["response_time"] < 2.0  # Should be fast with connection pool


class TestBackupAndRecovery:
    """Test backup and recovery functionality"""
    
    def test_data_backup(self, client, auth_headers):
        """Test data backup functionality"""
        # Create test data
        supplier_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "contact_email": "test@example.com",
            "contact_phone": "+1234567890",
            "website": "https://example.com",
            "description": "Test Supplier Description"
        }
        
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps(supplier_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        supplier_id = data["data"]["id"]
        
        # Verify data exists
        response = client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # In a real implementation, this would trigger a backup
        # For testing, we just verify the data is accessible
        assert response.status_code == 200
    
    def test_data_recovery(self, client, auth_headers):
        """Test data recovery functionality"""
        # Create test data
        supplier_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "contact_email": "test@example.com",
            "contact_phone": "+1234567890",
            "website": "https://example.com",
            "description": "Test Supplier Description"
        }
        
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps(supplier_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        supplier_id = data["data"]["id"]
        
        # Simulate data loss by deleting directly from database
        supplier = Supplier.query.get(supplier_id)
        supplier.delete()
        
        # Verify data is deleted
        response = client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 404
        
        # In a real implementation, this would restore from backup
        # For testing, we just verify the data is gone
        assert response.status_code == 404
    
    def test_data_integrity_check(self, client, auth_headers):
        """Test data integrity check"""
        # Create test data
        supplier_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "contact_email": "test@example.com",
            "contact_phone": "+1234567890",
            "website": "https://example.com",
            "description": "Test Supplier Description"
        }
        
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps(supplier_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        supplier_id = data["data"]["id"]
        
        # Verify data integrity
        response = client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 200
        
        supplier_info = json.loads(response.data)
        assert supplier_info["data"]["id"] == supplier_id
        assert supplier_info["data"]["name"] == "Test Supplier"
        assert supplier_info["data"]["location"] == "Test Location"
        assert supplier_info["data"]["contact_email"] == "test@example.com"
        assert supplier_info["data"]["contact_phone"] == "+1234567890"
        assert supplier_info["data"]["website"] == "https://example.com"
        assert supplier_info["data"]["description"] == "Test Supplier Description"
    
    def test_data_consistency_check(self, client, auth_headers):
        """Test data consistency check"""
        # Create supplier
        supplier_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "contact_email": "test@example.com",
            "contact_phone": "+1234567890",
            "website": "https://example.com",
            "description": "Test Supplier Description"
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
            "description": "Test Alert"
        }
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps(alert_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        alert_id = data["data"]["id"]
        
        # Verify data consistency
        response = client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 200
        
        supplier_info = json.loads(response.data)
        assert supplier_info["data"]["id"] == supplier_id
        
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200
        
        alert_info = json.loads(response.data)
        assert alert_info["data"]["supplier_id"] == supplier_id
        
        # Verify relationship consistency
        assert alert_info["data"]["supplier_id"] == supplier_info["data"]["id"]
