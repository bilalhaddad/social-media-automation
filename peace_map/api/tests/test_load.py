"""
Load tests for Peace Map API
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


class TestLoadTesting:
    """Test load testing functionality"""
    
    def test_light_load(self, client, auth_headers):
        """Test light load (10 concurrent users)"""
        # Create test data
        for i in range(10):
            supplier_data = {
                "name": f"Light Load Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"light-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://light-{i}.com",
                "description": f"Light Load Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test light load
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 10 concurrent threads
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
        
        success_count = 0
        total_response_time = 0
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                success_count += 1
                total_response_time += result["response_time"]
        
        # Should handle light load well
        assert success_count >= 9  # At least 90% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 1.0  # Average response time under 1s
        
        print(f"Light Load Test Results:")
        print(f"  Total requests: 10")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 10 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_medium_load(self, client, auth_headers):
        """Test medium load (50 concurrent users)"""
        # Create test data
        for i in range(50):
            supplier_data = {
                "name": f"Medium Load Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"medium-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://medium-{i}.com",
                "description": f"Medium Load Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test medium load
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 50 concurrent threads
        threads = []
        for _ in range(50):
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
        
        # Should handle medium load reasonably
        assert success_count >= 45  # At least 90% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 2.0  # Average response time under 2s
        
        print(f"Medium Load Test Results:")
        print(f"  Total requests: 50")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 50 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_heavy_load(self, client, auth_headers):
        """Test heavy load (100 concurrent users)"""
        # Create test data
        for i in range(100):
            supplier_data = {
                "name": f"Heavy Load Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"heavy-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://heavy-{i}.com",
                "description": f"Heavy Load Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test heavy load
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 100 concurrent threads
        threads = []
        for _ in range(100):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 100
        
        success_count = 0
        total_response_time = 0
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                success_count += 1
                total_response_time += result["response_time"]
        
        # Should handle heavy load with some degradation
        assert success_count >= 80  # At least 80% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 5.0  # Average response time under 5s
        
        print(f"Heavy Load Test Results:")
        print(f"  Total requests: 100")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 100 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_extreme_load(self, client, auth_headers):
        """Test extreme load (200 concurrent users)"""
        # Create test data
        for i in range(200):
            supplier_data = {
                "name": f"Extreme Load Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"extreme-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://extreme-{i}.com",
                "description": f"Extreme Load Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test extreme load
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 200 concurrent threads
        threads = []
        for _ in range(200):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 200
        
        success_count = 0
        total_response_time = 0
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                success_count += 1
                total_response_time += result["response_time"]
        
        # Should handle extreme load with significant degradation
        assert success_count >= 100  # At least 50% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 10.0  # Average response time under 10s
        
        print(f"Extreme Load Test Results:")
        print(f"  Total requests: 200")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 200 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")


class TestSustainedLoad:
    """Test sustained load testing"""
    
    def test_sustained_light_load(self, client, auth_headers):
        """Test sustained light load (10 users for 5 minutes)"""
        # Create test data
        for i in range(10):
            supplier_data = {
                "name": f"Sustained Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"sustained-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://sustained-{i}.com",
                "description": f"Sustained Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test sustained load
        start_time = time.time()
        request_count = 0
        success_count = 0
        total_response_time = 0
        
        # Simulate 5 minutes of sustained load (reduced for testing)
        while time.time() - start_time < 30:  # 30 seconds for testing
            results = queue.Queue()
            
            def make_request():
                start_time = time.time()
                response = client.get("/api/v1/suppliers", headers=auth_headers)
                end_time = time.time()
                
                results.put({
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                })
            
            # Create 10 concurrent threads
            threads = []
            for _ in range(10):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Process results
            while not results.empty():
                result = results.get()
                request_count += 1
                if result["status_code"] == 200:
                    success_count += 1
                    total_response_time += result["response_time"]
            
            # Small delay between batches
            time.sleep(1)
        
        # Calculate statistics
        success_rate = success_count / request_count if request_count > 0 else 0
        avg_response_time = total_response_time / success_count if success_count > 0 else 0
        
        # Should maintain good performance
        assert success_rate >= 0.9  # At least 90% success rate
        assert avg_response_time < 2.0  # Average response time under 2s
        
        print(f"Sustained Light Load Test Results:")
        print(f"  Duration: 30 seconds")
        print(f"  Total requests: {request_count}")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_rate * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_sustained_medium_load(self, client, auth_headers):
        """Test sustained medium load (50 users for 5 minutes)"""
        # Create test data
        for i in range(50):
            supplier_data = {
                "name": f"Sustained Medium Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"sustained-medium-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://sustained-medium-{i}.com",
                "description": f"Sustained Medium Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test sustained load
        start_time = time.time()
        request_count = 0
        success_count = 0
        total_response_time = 0
        
        # Simulate 5 minutes of sustained load (reduced for testing)
        while time.time() - start_time < 30:  # 30 seconds for testing
            results = queue.Queue()
            
            def make_request():
                start_time = time.time()
                response = client.get("/api/v1/suppliers", headers=auth_headers)
                end_time = time.time()
                
                results.put({
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                })
            
            # Create 50 concurrent threads
            threads = []
            for _ in range(50):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Process results
            while not results.empty():
                result = results.get()
                request_count += 1
                if result["status_code"] == 200:
                    success_count += 1
                    total_response_time += result["response_time"]
            
            # Small delay between batches
            time.sleep(1)
        
        # Calculate statistics
        success_rate = success_count / request_count if request_count > 0 else 0
        avg_response_time = total_response_time / success_count if success_count > 0 else 0
        
        # Should maintain reasonable performance
        assert success_rate >= 0.8  # At least 80% success rate
        assert avg_response_time < 3.0  # Average response time under 3s
        
        print(f"Sustained Medium Load Test Results:")
        print(f"  Duration: 30 seconds")
        print(f"  Total requests: {request_count}")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_rate * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")


class TestStressTesting:
    """Test stress testing functionality"""
    
    def test_stress_test_read_operations(self, client, auth_headers):
        """Test stress test for read operations"""
        # Create test data
        for i in range(100):
            supplier_data = {
                "name": f"Stress Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"stress-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://stress-{i}.com",
                "description": f"Stress Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Stress test read operations
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 200 concurrent threads
        threads = []
        for _ in range(200):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 200
        
        success_count = 0
        total_response_time = 0
        error_count = 0
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                success_count += 1
                total_response_time += result["response_time"]
            else:
                error_count += 1
        
        # Should handle stress test
        assert success_count >= 100  # At least 50% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 10.0  # Average response time under 10s
        
        print(f"Stress Test Read Operations Results:")
        print(f"  Total requests: 200")
        print(f"  Successful requests: {success_count}")
        print(f"  Error requests: {error_count}")
        print(f"  Success rate: {success_count / 200 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_stress_test_write_operations(self, client, auth_headers):
        """Test stress test for write operations"""
        results = queue.Queue()
        
        def make_request(supplier_id):
            supplier_data = {
                "name": f"Stress Write Supplier {supplier_id}",
                "location": f"Location {supplier_id}",
                "contact_email": f"stress-write-{supplier_id}@example.com",
                "contact_phone": f"+123456789{supplier_id % 10}",
                "website": f"https://stress-write-{supplier_id}.com",
                "description": f"Stress Write Supplier {supplier_id} Description"
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
        
        # Create 100 concurrent threads
        threads = []
        for i in range(100):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 100
        
        success_count = 0
        total_response_time = 0
        error_count = 0
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                success_count += 1
                total_response_time += result["response_time"]
            else:
                error_count += 1
        
        # Should handle stress test
        assert success_count >= 80  # At least 80% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 5.0  # Average response time under 5s
        
        print(f"Stress Test Write Operations Results:")
        print(f"  Total requests: 100")
        print(f"  Successful requests: {success_count}")
        print(f"  Error requests: {error_count}")
        print(f"  Success rate: {success_count / 100 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_stress_test_mixed_operations(self, client, auth_headers):
        """Test stress test for mixed operations"""
        # Create initial data
        for i in range(50):
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
                "name": f"Stress Mixed Supplier {supplier_id}",
                "location": f"Location {supplier_id}",
                "contact_email": f"stress-mixed-{supplier_id}@example.com",
                "contact_phone": f"+123456789{supplier_id % 10}",
                "website": f"https://stress-mixed-{supplier_id}.com",
                "description": f"Stress Mixed Supplier {supplier_id} Description"
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
        
        # 100 read requests
        for _ in range(100):
            thread = threading.Thread(target=make_read_request)
            threads.append(thread)
            thread.start()
        
        # 50 write requests
        for i in range(50):
            thread = threading.Thread(target=make_write_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 150
        
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
        
        # Should handle stress test
        assert read_success >= 80  # At least 80% success rate for reads
        assert write_success >= 40  # At least 80% success rate for writes
        
        if read_success > 0:
            avg_read_time = total_read_time / read_success
            assert avg_read_time < 5.0  # Average read time under 5s
        
        if write_success > 0:
            avg_write_time = total_write_time / write_success
            assert avg_write_time < 10.0  # Average write time under 10s
        
        print(f"Stress Test Mixed Operations Results:")
        print(f"  Total read requests: 100")
        print(f"  Successful read requests: {read_success}")
        print(f"  Read success rate: {read_success / 100 * 100:.1f}%")
        print(f"  Total write requests: 50")
        print(f"  Successful write requests: {write_success}")
        print(f"  Write success rate: {write_success / 50 * 100:.1f}%")
        if read_success > 0:
            print(f"  Average read time: {avg_read_time:.3f}s")
        if write_success > 0:
            print(f"  Average write time: {avg_write_time:.3f}s")
