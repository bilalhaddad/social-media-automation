"""
Performance tests for Peace Map API
"""

import pytest
import time
import json
from datetime import datetime
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


class TestResponseTime:
    """Test response time performance"""
    
    def test_health_check_response_time(self, client):
        """Test health check response time"""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 0.1  # Should respond within 100ms
    
    def test_api_endpoints_response_time(self, client, auth_headers):
        """Test API endpoints response time"""
        endpoints = [
            "/api/v1/suppliers",
            "/api/v1/projects/1/events",
            "/api/v1/risk-index",
            "/api/v1/alerts"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint, headers=auth_headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response.status_code == 200
            assert response_time < 1.0  # Should respond within 1 second
    
    def test_create_operations_response_time(self, client, auth_headers):
        """Test create operations response time"""
        # Test supplier creation
        supplier_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "contact_email": "test@example.com",
            "contact_phone": "+1234567890",
            "website": "https://example.com",
            "description": "Test Supplier Description"
        }
        
        start_time = time.time()
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps(supplier_data),
            headers=auth_headers
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
        
        # Test event creation
        event_data = {
            "title": "Test Event",
            "description": "Test Description",
            "event_type": "protest",
            "location": "Test Location",
            "source": "Test Source",
            "source_confidence": 0.8,
            "published_at": datetime.utcnow().isoformat()
        }
        
        start_time = time.time()
        response = client.post(
            "/api/v1/projects/1/events",
            data=json.dumps(event_data),
            headers=auth_headers
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_update_operations_response_time(self, client, auth_headers):
        """Test update operations response time"""
        # Create supplier first
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
        
        # Test supplier update
        update_data = {
            "name": "Updated Supplier",
            "contact_email": "updated@example.com"
        }
        
        start_time = time.time()
        response = client.put(
            f"/api/v1/suppliers/{supplier_id}",
            data=json.dumps(update_data),
            headers=auth_headers
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_delete_operations_response_time(self, client, auth_headers):
        """Test delete operations response time"""
        # Create supplier first
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
        
        # Test supplier deletion
        start_time = time.time()
        response = client.delete(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second


class TestConcurrentRequests:
    """Test concurrent request performance"""
    
    def test_concurrent_read_requests(self, client, auth_headers):
        """Test concurrent read requests"""
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
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 10
        
        while not results.empty():
            result = results.get()
            assert result["status_code"] == 200
            assert result["response_time"] < 2.0  # Should respond within 2 seconds
    
    def test_concurrent_write_requests(self, client, auth_headers):
        """Test concurrent write requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request(supplier_id):
            supplier_data = {
                "name": f"Supplier {supplier_id}",
                "location": f"Location {supplier_id}",
                "contact_email": f"supplier-{supplier_id}@example.com",
                "contact_phone": f"+123456789{supplier_id}",
                "website": f"https://supplier-{supplier_id}.com",
                "description": f"Supplier {supplier_id} Description"
            }
            
            start_time = time.time()
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 5
        
        while not results.empty():
            result = results.get()
            assert result["status_code"] == 200
            assert result["response_time"] < 2.0  # Should respond within 2 seconds


class TestDataVolume:
    """Test data volume performance"""
    
    def test_large_dataset_creation(self, client, auth_headers):
        """Test large dataset creation performance"""
        start_time = time.time()
        
        # Create multiple suppliers
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
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Should create 100 suppliers within reasonable time
        assert creation_time < 30.0  # 30 seconds max
        
        # Test retrieval performance
        start_time = time.time()
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        end_time = time.time()
        
        retrieval_time = end_time - start_time
        assert response.status_code == 200
        assert retrieval_time < 2.0  # Should retrieve within 2 seconds
        
        data = json.loads(response.data)
        assert len(data["data"]) == 100
        assert data["pagination"]["total"] == 100
    
    def test_large_dataset_filtering(self, client, auth_headers):
        """Test large dataset filtering performance"""
        # Create multiple suppliers with different locations
        for i in range(50):
            supplier_data = {
                "name": f"Supplier {i}",
                "location": f"Location {i % 5}",  # 5 different locations
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
        
        # Test filtering performance
        start_time = time.time()
        response = client.get("/api/v1/suppliers?location=Location 0", headers=auth_headers)
        end_time = time.time()
        
        filtering_time = end_time - start_time
        assert response.status_code == 200
        assert filtering_time < 1.0  # Should filter within 1 second
        
        data = json.loads(response.data)
        assert len(data["data"]) == 10  # 50 suppliers / 5 locations = 10 per location
        assert all(supplier["location"] == "Location 0" for supplier in data["data"])
    
    def test_large_dataset_pagination(self, client, auth_headers):
        """Test large dataset pagination performance"""
        # Create multiple suppliers
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
        
        # Test pagination performance
        for page in range(1, 6):  # 5 pages with 20 items each
            start_time = time.time()
            response = client.get(
                f"/api/v1/suppliers?page={page}&size=20",
                headers=auth_headers
            )
            end_time = time.time()
            
            pagination_time = end_time - start_time
            assert response.status_code == 200
            assert pagination_time < 1.0  # Should paginate within 1 second
            
            data = json.loads(response.data)
            assert len(data["data"]) == 20
            assert data["pagination"]["page"] == page
            assert data["pagination"]["size"] == 20
            assert data["pagination"]["total"] == 100


class TestMemoryUsage:
    """Test memory usage performance"""
    
    def test_memory_usage_creation(self, client, auth_headers):
        """Test memory usage during creation"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create multiple suppliers
        for i in range(1000):
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
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100 * 1024 * 1024  # 100MB max
    
    def test_memory_usage_retrieval(self, client, auth_headers):
        """Test memory usage during retrieval"""
        import psutil
        import os
        
        # Create multiple suppliers first
        for i in range(1000):
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
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Retrieve all suppliers
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        assert response.status_code == 200
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 50 * 1024 * 1024  # 50MB max


class TestDatabasePerformance:
    """Test database performance"""
    
    def test_database_connection_pool(self, client, auth_headers):
        """Test database connection pool performance"""
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
            assert result["response_time"] < 2.0  # Should respond within 2 seconds
    
    def test_database_transaction_performance(self, client, auth_headers):
        """Test database transaction performance"""
        # Test multiple operations in sequence
        start_time = time.time()
        
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
        
        # Delete supplier
        response = client.delete(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
        assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time
        assert total_time < 3.0  # 3 seconds max
