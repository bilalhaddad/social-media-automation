"""
Benchmark tests for Peace Map API
"""

import pytest
import json
import time
import statistics
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


class TestAPIBenchmarks:
    """Test API performance benchmarks"""
    
    def test_health_check_benchmark(self, client):
        """Benchmark health check endpoint"""
        response_times = []
        
        for _ in range(100):
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Health check should be very fast
        assert avg_response_time < 0.05  # Average under 50ms
        assert median_response_time < 0.05  # Median under 50ms
        assert p95_response_time < 0.1  # 95th percentile under 100ms
        assert p99_response_time < 0.2  # 99th percentile under 200ms
        
        print(f"Health Check Benchmark:")
        print(f"  Average: {avg_response_time:.3f}s")
        print(f"  Median: {median_response_time:.3f}s")
        print(f"  95th percentile: {p95_response_time:.3f}s")
        print(f"  99th percentile: {p99_response_time:.3f}s")
    
    def test_suppliers_list_benchmark(self, client, auth_headers):
        """Benchmark suppliers list endpoint"""
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
        
        # Benchmark list endpoint
        response_times = []
        
        for _ in range(50):
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # List endpoint should be fast
        assert avg_response_time < 0.5  # Average under 500ms
        assert median_response_time < 0.5  # Median under 500ms
        assert p95_response_time < 1.0  # 95th percentile under 1s
        assert p99_response_time < 2.0  # 99th percentile under 2s
        
        print(f"Suppliers List Benchmark:")
        print(f"  Average: {avg_response_time:.3f}s")
        print(f"  Median: {median_response_time:.3f}s")
        print(f"  95th percentile: {p95_response_time:.3f}s")
        print(f"  99th percentile: {p99_response_time:.3f}s")
    
    def test_suppliers_create_benchmark(self, client, auth_headers):
        """Benchmark suppliers create endpoint"""
        response_times = []
        
        for i in range(50):
            supplier_data = {
                "name": f"Benchmark Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"benchmark-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://benchmark-{i}.com",
                "description": f"Benchmark Supplier {i} Description"
            }
            
            start_time = time.time()
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Create endpoint should be reasonable
        assert avg_response_time < 1.0  # Average under 1s
        assert median_response_time < 1.0  # Median under 1s
        assert p95_response_time < 2.0  # 95th percentile under 2s
        assert p99_response_time < 3.0  # 99th percentile under 3s
        
        print(f"Suppliers Create Benchmark:")
        print(f"  Average: {avg_response_time:.3f}s")
        print(f"  Median: {median_response_time:.3f}s")
        print(f"  95th percentile: {p95_response_time:.3f}s")
        print(f"  99th percentile: {p99_response_time:.3f}s")
    
    def test_suppliers_update_benchmark(self, client, auth_headers):
        """Benchmark suppliers update endpoint"""
        # Create test suppliers
        supplier_ids = []
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
            
            data = json.loads(response.data)
            supplier_ids.append(data["data"]["id"])
        
        # Benchmark update endpoint
        response_times = []
        
        for i, supplier_id in enumerate(supplier_ids):
            update_data = {
                "name": f"Updated Supplier {i}",
                "contact_email": f"updated-{i}@example.com"
            }
            
            start_time = time.time()
            response = client.put(
                f"/api/v1/suppliers/{supplier_id}",
                data=json.dumps(update_data),
                headers=auth_headers
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Update endpoint should be reasonable
        assert avg_response_time < 1.0  # Average under 1s
        assert median_response_time < 1.0  # Median under 1s
        assert p95_response_time < 2.0  # 95th percentile under 2s
        assert p99_response_time < 3.0  # 99th percentile under 3s
        
        print(f"Suppliers Update Benchmark:")
        print(f"  Average: {avg_response_time:.3f}s")
        print(f"  Median: {median_response_time:.3f}s")
        print(f"  95th percentile: {p95_response_time:.3f}s")
        print(f"  99th percentile: {p99_response_time:.3f}s")
    
    def test_suppliers_delete_benchmark(self, client, auth_headers):
        """Benchmark suppliers delete endpoint"""
        # Create test suppliers
        supplier_ids = []
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
            
            data = json.loads(response.data)
            supplier_ids.append(data["data"]["id"])
        
        # Benchmark delete endpoint
        response_times = []
        
        for supplier_id in supplier_ids:
            start_time = time.time()
            response = client.delete(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Delete endpoint should be reasonable
        assert avg_response_time < 1.0  # Average under 1s
        assert median_response_time < 1.0  # Median under 1s
        assert p95_response_time < 2.0  # 95th percentile under 2s
        assert p99_response_time < 3.0  # 99th percentile under 3s
        
        print(f"Suppliers Delete Benchmark:")
        print(f"  Average: {avg_response_time:.3f}s")
        print(f"  Median: {median_response_time:.3f}s")
        print(f"  95th percentile: {p95_response_time:.3f}s")
        print(f"  99th percentile: {p99_response_time:.3f}s")


class TestDatabaseBenchmarks:
    """Test database performance benchmarks"""
    
    def test_database_insert_benchmark(self, client, auth_headers):
        """Benchmark database insert performance"""
        response_times = []
        
        for i in range(100):
            supplier_data = {
                "name": f"DB Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"db-supplier-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://db-supplier-{i}.com",
                "description": f"DB Supplier {i} Description"
            }
            
            start_time = time.time()
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Database insert should be reasonable
        assert avg_response_time < 1.0  # Average under 1s
        assert median_response_time < 1.0  # Median under 1s
        assert p95_response_time < 2.0  # 95th percentile under 2s
        assert p99_response_time < 3.0  # 99th percentile under 3s
        
        print(f"Database Insert Benchmark:")
        print(f"  Average: {avg_response_time:.3f}s")
        print(f"  Median: {median_response_time:.3f}s")
        print(f"  95th percentile: {p95_response_time:.3f}s")
        print(f"  99th percentile: {p99_response_time:.3f}s")
    
    def test_database_select_benchmark(self, client, auth_headers):
        """Benchmark database select performance"""
        # Create test data
        for i in range(100):
            supplier_data = {
                "name": f"DB Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"db-supplier-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://db-supplier-{i}.com",
                "description": f"DB Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Benchmark select performance
        response_times = []
        
        for _ in range(50):
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Database select should be fast
        assert avg_response_time < 0.5  # Average under 500ms
        assert median_response_time < 0.5  # Median under 500ms
        assert p95_response_time < 1.0  # 95th percentile under 1s
        assert p99_response_time < 2.0  # 99th percentile under 2s
        
        print(f"Database Select Benchmark:")
        print(f"  Average: {avg_response_time:.3f}s")
        print(f"  Median: {median_response_time:.3f}s")
        print(f"  95th percentile: {p95_response_time:.3f}s")
        print(f"  99th percentile: {p99_response_time:.3f}s")
    
    def test_database_update_benchmark(self, client, auth_headers):
        """Benchmark database update performance"""
        # Create test data
        supplier_ids = []
        for i in range(100):
            supplier_data = {
                "name": f"DB Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"db-supplier-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://db-supplier-{i}.com",
                "description": f"DB Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
            
            data = json.loads(response.data)
            supplier_ids.append(data["data"]["id"])
        
        # Benchmark update performance
        response_times = []
        
        for i, supplier_id in enumerate(supplier_ids):
            update_data = {
                "name": f"Updated DB Supplier {i}",
                "contact_email": f"updated-db-{i}@example.com"
            }
            
            start_time = time.time()
            response = client.put(
                f"/api/v1/suppliers/{supplier_id}",
                data=json.dumps(update_data),
                headers=auth_headers
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Database update should be reasonable
        assert avg_response_time < 1.0  # Average under 1s
        assert median_response_time < 1.0  # Median under 1s
        assert p95_response_time < 2.0  # 95th percentile under 2s
        assert p99_response_time < 3.0  # 99th percentile under 3s
        
        print(f"Database Update Benchmark:")
        print(f"  Average: {avg_response_time:.3f}s")
        print(f"  Median: {median_response_time:.3f}s")
        print(f"  95th percentile: {p95_response_time:.3f}s")
        print(f"  99th percentile: {p99_response_time:.3f}s")
    
    def test_database_delete_benchmark(self, client, auth_headers):
        """Benchmark database delete performance"""
        # Create test data
        supplier_ids = []
        for i in range(100):
            supplier_data = {
                "name": f"DB Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"db-supplier-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://db-supplier-{i}.com",
                "description": f"DB Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
            
            data = json.loads(response.data)
            supplier_ids.append(data["data"]["id"])
        
        # Benchmark delete performance
        response_times = []
        
        for supplier_id in supplier_ids:
            start_time = time.time()
            response = client.delete(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == 200
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Database delete should be reasonable
        assert avg_response_time < 1.0  # Average under 1s
        assert median_response_time < 1.0  # Median under 1s
        assert p95_response_time < 2.0  # 95th percentile under 2s
        assert p99_response_time < 3.0  # 99th percentile under 3s
        
        print(f"Database Delete Benchmark:")
        print(f"  Average: {avg_response_time:.3f}s")
        print(f"  Median: {median_response_time:.3f}s")
        print(f"  95th percentile: {p95_response_time:.3f}s")
        print(f"  99th percentile: {p99_response_time:.3f}s")


class TestMemoryBenchmarks:
    """Test memory usage benchmarks"""
    
    def test_memory_usage_benchmark(self, client, auth_headers):
        """Benchmark memory usage"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create large dataset
        for i in range(1000):
            supplier_data = {
                "name": f"Memory Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"memory-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://memory-{i}.com",
                "description": f"Memory Supplier {i} Description"
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
        
        print(f"Memory Usage Benchmark:")
        print(f"  Initial memory: {initial_memory / 1024 / 1024:.2f} MB")
        print(f"  Final memory: {final_memory / 1024 / 1024:.2f} MB")
        print(f"  Memory increase: {memory_increase / 1024 / 1024:.2f} MB")
    
    def test_memory_efficiency_benchmark(self, client, auth_headers):
        """Benchmark memory efficiency"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Test memory usage during operations
        memory_usage = []
        
        for i in range(100):
            supplier_data = {
                "name": f"Efficiency Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"efficiency-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://efficiency-{i}.com",
                "description": f"Efficiency Supplier {i} Description"
            }
            
            # Measure memory before operation
            memory_before = process.memory_info().rss
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
            
            # Measure memory after operation
            memory_after = process.memory_info().rss
            memory_usage.append(memory_after - memory_before)
        
        # Calculate statistics
        avg_memory_usage = statistics.mean(memory_usage)
        median_memory_usage = statistics.median(memory_usage)
        max_memory_usage = max(memory_usage)
        
        # Memory usage should be reasonable
        assert avg_memory_usage < 1024 * 1024  # Average under 1MB per operation
        assert median_memory_usage < 1024 * 1024  # Median under 1MB per operation
        assert max_memory_usage < 5 * 1024 * 1024  # Max under 5MB per operation
        
        print(f"Memory Efficiency Benchmark:")
        print(f"  Average memory per operation: {avg_memory_usage / 1024:.2f} KB")
        print(f"  Median memory per operation: {median_memory_usage / 1024:.2f} KB")
        print(f"  Max memory per operation: {max_memory_usage / 1024:.2f} KB")


class TestThroughputBenchmarks:
    """Test throughput benchmarks"""
    
    def test_requests_per_second_benchmark(self, client, auth_headers):
        """Benchmark requests per second"""
        # Create test data
        for i in range(50):
            supplier_data = {
                "name": f"Throughput Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"throughput-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://throughput-{i}.com",
                "description": f"Throughput Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Benchmark requests per second
        start_time = time.time()
        request_count = 0
        
        for _ in range(200):  # 200 requests
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            if response.status_code == 200:
                request_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        requests_per_second = request_count / total_time
        
        # Should handle reasonable throughput
        assert requests_per_second > 10.0  # At least 10 requests per second
        assert request_count >= 190  # At least 95% success rate
        
        print(f"Requests Per Second Benchmark:")
        print(f"  Total requests: {request_count}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Requests per second: {requests_per_second:.2f}")
    
    def test_concurrent_throughput_benchmark(self, client, auth_headers):
        """Benchmark concurrent throughput"""
        import threading
        import queue
        
        # Create test data
        for i in range(50):
            supplier_data = {
                "name": f"Concurrent Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"concurrent-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://concurrent-{i}.com",
                "description": f"Concurrent Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Benchmark concurrent throughput
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
        
        # Calculate statistics
        success_count = 0
        total_response_time = 0
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                success_count += 1
                total_response_time += result["response_time"]
        
        # Should handle concurrent requests
        assert success_count >= 45  # At least 90% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 2.0  # Average response time under 2s
        
        print(f"Concurrent Throughput Benchmark:")
        print(f"  Total requests: 50")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 50 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
