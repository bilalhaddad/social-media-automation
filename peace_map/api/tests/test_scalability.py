"""
Scalability tests for Peace Map API
"""

import pytest
import json
import time
import threading
import queue
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


class TestConcurrentUsers:
    """Test concurrent user scalability"""
    
    def test_concurrent_read_requests(self, client, auth_headers):
        """Test concurrent read requests"""
        # Create test data first
        for i in range(10):
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
        
        # Test concurrent read requests
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
        for _ in range(50):  # 50 concurrent requests
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 50
        
        success_count = 0
        total_response_time = 0
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                success_count += 1
                total_response_time += result["response_time"]
        
        # Should handle most requests successfully
        assert success_count >= 45  # At least 90% success rate
        
        # Average response time should be reasonable
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 2.0  # Should be under 2 seconds on average
    
    def test_concurrent_write_requests(self, client, auth_headers):
        """Test concurrent write requests"""
        results = queue.Queue()
        
        def make_request(supplier_id):
            supplier_data = {
                "name": f"Concurrent Supplier {supplier_id}",
                "location": f"Location {supplier_id}",
                "contact_email": f"concurrent-{supplier_id}@example.com",
                "contact_phone": f"+123456789{supplier_id % 10}",
                "website": f"https://concurrent-{supplier_id}.com",
                "description": f"Concurrent Supplier {supplier_id} Description"
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
                "response_time": end_time - start_time,
                "supplier_id": supplier_id
            })
        
        # Create multiple threads
        threads = []
        for i in range(20):  # 20 concurrent write requests
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 20
        
        success_count = 0
        total_response_time = 0
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                success_count += 1
                total_response_time += result["response_time"]
        
        # Should handle most requests successfully
        assert success_count >= 18  # At least 90% success rate
        
        # Average response time should be reasonable
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 3.0  # Should be under 3 seconds on average
    
    def test_concurrent_mixed_requests(self, client, auth_headers):
        """Test concurrent mixed read/write requests"""
        # Create initial data
        for i in range(5):
            supplier_data = {
                "name": f"Initial Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"initial-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://initial-{i}.com",
                "description": f"Initial Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        results = queue.Queue()
        
        def make_read_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "type": "read",
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        def make_write_request(supplier_id):
            supplier_data = {
                "name": f"Mixed Supplier {supplier_id}",
                "location": f"Location {supplier_id}",
                "contact_email": f"mixed-{supplier_id}@example.com",
                "contact_phone": f"+123456789{supplier_id % 10}",
                "website": f"https://mixed-{supplier_id}.com",
                "description": f"Mixed Supplier {supplier_id} Description"
            }
            
            start_time = time.time()
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            end_time = time.time()
            
            results.put({
                "type": "write",
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "supplier_id": supplier_id
            })
        
        # Create mixed threads
        threads = []
        
        # 30 read requests
        for _ in range(30):
            thread = threading.Thread(target=make_read_request)
            threads.append(thread)
            thread.start()
        
        # 10 write requests
        for i in range(10):
            thread = threading.Thread(target=make_write_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 40
        
        read_success = 0
        write_success = 0
        total_read_time = 0
        total_write_time = 0
        
        while not results.empty():
            result = results.get()
            if result["type"] == "read":
                if result["status_code"] == 200:
                    read_success += 1
                    total_read_time += result["response_time"]
            elif result["type"] == "write":
                if result["status_code"] == 200:
                    write_success += 1
                    total_write_time += result["response_time"]
        
        # Should handle most requests successfully
        assert read_success >= 28  # At least 93% success rate for reads
        assert write_success >= 9   # At least 90% success rate for writes
        
        # Average response times should be reasonable
        if read_success > 0:
            avg_read_time = total_read_time / read_success
            assert avg_read_time < 1.5  # Reads should be fast
        
        if write_success > 0:
            avg_write_time = total_write_time / write_success
            assert avg_write_time < 2.5  # Writes should be reasonable


class TestDataVolume:
    """Test data volume scalability"""
    
    def test_large_dataset_creation(self, client, auth_headers):
        """Test large dataset creation"""
        start_time = time.time()
        
        # Create large number of suppliers
        for i in range(1000):
            supplier_data = {
                "name": f"Supplier {i}",
                "location": f"Location {i % 100}",  # 100 different locations
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
        
        # Should create 1000 suppliers within reasonable time
        assert creation_time < 60.0  # 60 seconds max
        
        # Test retrieval performance
        start_time = time.time()
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        end_time = time.time()
        
        retrieval_time = end_time - start_time
        assert response.status_code == 200
        assert retrieval_time < 3.0  # Should retrieve within 3 seconds
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1000
        assert data["pagination"]["total"] == 1000
    
    def test_large_dataset_filtering(self, client, auth_headers):
        """Test large dataset filtering performance"""
        # Create large dataset
        for i in range(500):
            supplier_data = {
                "name": f"Supplier {i}",
                "location": f"Location {i % 10}",  # 10 different locations
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
        assert filtering_time < 2.0  # Should filter within 2 seconds
        
        data = json.loads(response.data)
        assert len(data["data"]) == 50  # 500 suppliers / 10 locations = 50 per location
        assert all(supplier["location"] == "Location 0" for supplier in data["data"])
    
    def test_large_dataset_pagination(self, client, auth_headers):
        """Test large dataset pagination performance"""
        # Create large dataset
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
        
        # Test pagination performance
        for page in range(1, 11):  # 10 pages with 100 items each
            start_time = time.time()
            response = client.get(
                f"/api/v1/suppliers?page={page}&size=100",
                headers=auth_headers
            )
            end_time = time.time()
            
            pagination_time = end_time - start_time
            assert response.status_code == 200
            assert pagination_time < 1.5  # Should paginate within 1.5 seconds
            
            data = json.loads(response.data)
            assert len(data["data"]) == 100
            assert data["pagination"]["page"] == page
            assert data["pagination"]["size"] == 100
            assert data["pagination"]["total"] == 1000
    
    def test_large_dataset_search(self, client, auth_headers):
        """Test large dataset search performance"""
        # Create large dataset with searchable content
        for i in range(1000):
            supplier_data = {
                "name": f"Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"supplier-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://supplier-{i}.com",
                "description": f"Supplier {i} Description with searchable content"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test search performance
        start_time = time.time()
        response = client.get("/api/v1/suppliers?name=Supplier 500", headers=auth_headers)
        end_time = time.time()
        
        search_time = end_time - start_time
        assert response.status_code == 200
        assert search_time < 2.0  # Should search within 2 seconds
        
        data = json.loads(response.data)
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Supplier 500"


class TestResourceUsage:
    """Test resource usage scalability"""
    
    def test_memory_usage_scalability(self, client, auth_headers):
        """Test memory usage scalability"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create large dataset
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
        assert memory_increase < 200 * 1024 * 1024  # 200MB max
        
        # Test memory usage during retrieval
        start_memory = process.memory_info().rss
        
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        assert response.status_code == 200
        
        end_memory = process.memory_info().rss
        retrieval_memory_increase = end_memory - start_memory
        
        # Memory increase during retrieval should be minimal
        assert retrieval_memory_increase < 50 * 1024 * 1024  # 50MB max
    
    def test_cpu_usage_scalability(self, client, auth_headers):
        """Test CPU usage scalability"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Test CPU usage during creation
        start_time = time.time()
        start_cpu = process.cpu_percent()
        
        # Create large dataset
        for i in range(500):
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
        end_cpu = process.cpu_percent()
        
        creation_time = end_time - start_time
        cpu_increase = end_cpu - start_cpu
        
        # Should complete within reasonable time
        assert creation_time < 30.0  # 30 seconds max
        
        # CPU usage should be reasonable
        assert cpu_increase < 50.0  # 50% max increase
    
    def test_disk_usage_scalability(self, client, auth_headers):
        """Test disk usage scalability"""
        import psutil
        import os
        
        # Get initial disk usage
        disk_usage = psutil.disk_usage('/')
        initial_free = disk_usage.free
        
        # Create large dataset
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
        
        # Check disk usage
        disk_usage = psutil.disk_usage('/')
        final_free = disk_usage.free
        disk_usage_increase = initial_free - final_free
        
        # Disk usage increase should be reasonable
        assert disk_usage_increase < 100 * 1024 * 1024  # 100MB max


class TestPerformanceUnderLoad:
    """Test performance under load"""
    
    def test_response_time_under_load(self, client, auth_headers):
        """Test response time under load"""
        # Create test data
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
        
        # Test response time under load
        response_times = []
        
        for _ in range(100):
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # Calculate statistics
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        # Response times should be reasonable
        assert avg_response_time < 1.0  # Average under 1 second
        assert max_response_time < 2.0   # Max under 2 seconds
        assert min_response_time < 0.5  # Min under 0.5 seconds
    
    def test_throughput_under_load(self, client, auth_headers):
        """Test throughput under load"""
        # Create test data
        for i in range(50):
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
        
        # Test throughput
        start_time = time.time()
        request_count = 0
        
        for _ in range(200):  # 200 requests
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            if response.status_code == 200:
                request_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = request_count / total_time
        
        # Should handle reasonable throughput
        assert throughput > 10.0  # At least 10 requests per second
        assert request_count >= 190  # At least 95% success rate
    
    def test_error_rate_under_load(self, client, auth_headers):
        """Test error rate under load"""
        # Create test data
        for i in range(50):
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
        
        # Test error rate under load
        success_count = 0
        error_count = 0
        
        for _ in range(100):
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            if response.status_code == 200:
                success_count += 1
            else:
                error_count += 1
        
        total_requests = success_count + error_count
        error_rate = error_count / total_requests
        
        # Error rate should be low
        assert error_rate < 0.05  # Less than 5% error rate
        assert success_count >= 95  # At least 95% success rate
