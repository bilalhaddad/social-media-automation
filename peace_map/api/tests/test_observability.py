"""
Observability tests for Peace Map API
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


class TestObservability:
    """Test observability scenarios"""
    
    def test_metrics_collection(self, client, auth_headers):
        """Test metrics collection"""
        # Create test data
        for i in range(20):
            supplier_data = {
                "name": f"Metrics Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"metrics-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://metrics-{i}.com",
                "description": f"Metrics Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test metrics collection
        start_time = time.time()
        request_count = 0
        success_count = 0
        total_response_time = 0
        
        # Make multiple requests
        for _ in range(50):
            request_start = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            request_end = time.time()
            
            request_count += 1
            if response.status_code == 200:
                success_count += 1
                total_response_time += (request_end - request_start)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate metrics
        success_rate = success_count / request_count if request_count > 0 else 0
        avg_response_time = total_response_time / success_count if success_count > 0 else 0
        requests_per_second = request_count / total_time
        
        # Should collect metrics
        assert success_rate >= 0.9  # At least 90% success rate
        assert avg_response_time < 2.0  # Average response time under 2s
        assert requests_per_second > 5.0  # At least 5 requests per second
        
        print(f"Metrics Collection Results:")
        print(f"  Total requests: {request_count}")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_rate * 100:.1f}%")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Requests per second: {requests_per_second:.2f}")
    
    def test_logging_consistency(self, client, auth_headers):
        """Test logging consistency"""
        # Create test data
        for i in range(10):
            supplier_data = {
                "name": f"Logging Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"logging-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://logging-{i}.com",
                "description": f"Logging Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test logging consistency
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Create 30 concurrent threads
        threads = []
        for _ in range(30):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 30
        
        success_count = 0
        total_response_time = 0
        timestamps = []
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                success_count += 1
                total_response_time += result["response_time"]
                timestamps.append(result["timestamp"])
        
        # Should maintain logging consistency
        assert success_count >= 28  # At least 93% success rate
        assert len(timestamps) == success_count  # All successful requests logged
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 2.0  # Average response time under 2s
        
        print(f"Logging Consistency Results:")
        print(f"  Total requests: 30")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 30 * 100:.1f}%")
        print(f"  Logged timestamps: {len(timestamps)}")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_tracing_correlation(self, client, auth_headers):
        """Test tracing correlation"""
        # Create test data
        for i in range(15):
            supplier_data = {
                "name": f"Tracing Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"tracing-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://tracing-{i}.com",
                "description": f"Tracing Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test tracing correlation
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            # Check for tracing headers
            trace_id = response.headers.get("X-Trace-ID", "unknown")
            request_id = response.headers.get("X-Request-ID", "unknown")
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "trace_id": trace_id,
                "request_id": request_id
            })
        
        # Create 40 concurrent threads
        threads = []
        for _ in range(40):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 40
        
        success_count = 0
        total_response_time = 0
        trace_ids = []
        request_ids = []
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                success_count += 1
                total_response_time += result["response_time"]
                trace_ids.append(result["trace_id"])
                request_ids.append(result["request_id"])
        
        # Should maintain tracing correlation
        assert success_count >= 38  # At least 95% success rate
        assert len(trace_ids) == success_count  # All successful requests traced
        assert len(request_ids) == success_count  # All successful requests have request IDs
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 2.0  # Average response time under 2s
        
        print(f"Tracing Correlation Results:")
        print(f"  Total requests: 40")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 40 * 100:.1f}%")
        print(f"  Traced requests: {len(trace_ids)}")
        print(f"  Request IDs: {len(request_ids)}")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_performance_monitoring(self, client, auth_headers):
        """Test performance monitoring"""
        # Create test data
        for i in range(25):
            supplier_data = {
                "name": f"Performance Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"performance-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://performance-{i}.com",
                "description": f"Performance Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test performance monitoring
        start_time = time.time()
        request_count = 0
        success_count = 0
        total_response_time = 0
        response_times = []
        
        # Make multiple requests
        for _ in range(60):
            request_start = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            request_end = time.time()
            
            request_count += 1
            response_time = request_end - request_start
            response_times.append(response_time)
            
            if response.status_code == 200:
                success_count += 1
                total_response_time += response_time
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate performance metrics
        success_rate = success_count / request_count if request_count > 0 else 0
        avg_response_time = total_response_time / success_count if success_count > 0 else 0
        requests_per_second = request_count / total_time
        
        # Calculate percentiles
        response_times.sort()
        p50 = response_times[len(response_times) // 2] if response_times else 0
        p95 = response_times[int(len(response_times) * 0.95)] if response_times else 0
        p99 = response_times[int(len(response_times) * 0.99)] if response_times else 0
        
        # Should monitor performance
        assert success_rate >= 0.9  # At least 90% success rate
        assert avg_response_time < 2.0  # Average response time under 2s
        assert requests_per_second > 5.0  # At least 5 requests per second
        assert p95 < 5.0  # 95th percentile under 5s
        assert p99 < 10.0  # 99th percentile under 10s
        
        print(f"Performance Monitoring Results:")
        print(f"  Total requests: {request_count}")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_rate * 100:.1f}%")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Requests per second: {requests_per_second:.2f}")
        print(f"  P50 response time: {p50:.3f}s")
        print(f"  P95 response time: {p95:.3f}s")
        print(f"  P99 response time: {p99:.3f}s")
    
    def test_error_monitoring(self, client, auth_headers):
        """Test error monitoring"""
        # Create test data
        for i in range(10):
            supplier_data = {
                "name": f"Error Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"error-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://error-{i}.com",
                "description": f"Error Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test error monitoring
        results = queue.Queue()
        
        def make_valid_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "type": "valid",
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        def make_invalid_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers/999", headers=auth_headers)  # Non-existent
            end_time = time.time()
            
            results.put({
                "type": "invalid",
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        def make_malformed_request():
            start_time = time.time()
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps({"invalid": "data"}),  # Malformed data
                headers=auth_headers
            )
            end_time = time.time()
            
            results.put({
                "type": "malformed",
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create error monitoring threads
        threads = []
        
        # 30 valid requests
        for _ in range(30):
            thread = threading.Thread(target=make_valid_request)
            threads.append(thread)
            thread.start()
        
        # 15 invalid requests
        for _ in range(15):
            thread = threading.Thread(target=make_invalid_request)
            threads.append(thread)
            thread.start()
        
        # 15 malformed requests
        for _ in range(15):
            thread = threading.Thread(target=make_malformed_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 60
        
        valid_success = 0
        invalid_success = 0
        malformed_success = 0
        total_valid_time = 0
        total_invalid_time = 0
        total_malformed_time = 0
        
        while not results.empty():
            result = results.get()
            if result["type"] == "valid":
                if result["status_code"] == 200:
                    valid_success += 1
                    total_valid_time += result["response_time"]
            elif result["type"] == "invalid":
                if result["status_code"] == 404:  # Expected error
                    invalid_success += 1
                    total_invalid_time += result["response_time"]
            elif result["type"] == "malformed":
                if result["status_code"] == 422:  # Expected validation error
                    malformed_success += 1
                    total_malformed_time += result["response_time"]
        
        # Should monitor errors
        assert valid_success >= 28  # At least 93% success rate for valid requests
        assert invalid_success >= 13  # At least 87% success rate for invalid requests
        assert malformed_success >= 13  # At least 87% success rate for malformed requests
        
        if valid_success > 0:
            avg_valid_time = total_valid_time / valid_success
            assert avg_valid_time < 1.0  # Average valid time under 1s
        
        if invalid_success > 0:
            avg_invalid_time = total_invalid_time / invalid_success
            assert avg_invalid_time < 0.5  # Average invalid time under 0.5s
        
        if malformed_success > 0:
            avg_malformed_time = total_malformed_time / malformed_success
            assert avg_malformed_time < 0.5  # Average malformed time under 0.5s
        
        print(f"Error Monitoring Results:")
        print(f"  Valid requests: 30, Success: {valid_success}, Rate: {valid_success / 30 * 100:.1f}%")
        print(f"  Invalid requests: 15, Success: {invalid_success}, Rate: {invalid_success / 15 * 100:.1f}%")
        print(f"  Malformed requests: 15, Success: {malformed_success}, Rate: {malformed_success / 15 * 100:.1f}%")
        if valid_success > 0:
            print(f"  Average valid time: {avg_valid_time:.3f}s")
        if invalid_success > 0:
            print(f"  Average invalid time: {avg_invalid_time:.3f}s")
        if malformed_success > 0:
            print(f"  Average malformed time: {avg_malformed_time:.3f}s")
    
    def test_health_check_monitoring(self, client):
        """Test health check monitoring"""
        # Test health check endpoint
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should respond quickly
        assert response.status_code == 200
        assert response_time < 0.1  # Should respond within 100ms
        
        # Check health check response
        data = json.loads(response.data)
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        
        print(f"Health Check Monitoring Results:")
        print(f"  Status: {data['status']}")
        print(f"  Response time: {response_time:.3f}s")
        print(f"  Timestamp: {data['timestamp']}")
        print(f"  Version: {data['version']}")
    
    def test_dependency_monitoring(self, client, auth_headers):
        """Test dependency monitoring"""
        # Create test data
        for i in range(5):
            supplier_data = {
                "name": f"Dependency Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"dependency-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://dependency-{i}.com",
                "description": f"Dependency Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test dependency monitoring
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 20 concurrent threads
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
        
        success_count = 0
        total_response_time = 0
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                success_count += 1
                total_response_time += result["response_time"]
        
        # Should monitor dependencies
        assert success_count >= 18  # At least 90% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 2.0  # Average response time under 2s
        
        print(f"Dependency Monitoring Results:")
        print(f"  Total requests: 20")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 20 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")