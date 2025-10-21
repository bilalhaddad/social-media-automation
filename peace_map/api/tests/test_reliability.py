"""
Reliability tests for Peace Map API
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


class TestReliability:
    """Test reliability scenarios"""
    
    def test_continuous_operation(self, client, auth_headers):
        """Test continuous operation reliability"""
        # Create test data
        for i in range(10):
            supplier_data = {
                "name": f"Continuous Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"continuous-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://continuous-{i}.com",
                "description": f"Continuous Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Continuous operation test
        start_time = time.time()
        request_count = 0
        success_count = 0
        total_response_time = 0
        
        # Simulate continuous operation
        while time.time() - start_time < 30:  # 30 seconds
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
            time.sleep(0.5)
        
        # Calculate statistics
        success_rate = success_count / request_count if request_count > 0 else 0
        avg_response_time = total_response_time / success_count if success_count > 0 else 0
        
        # Should maintain high reliability
        assert success_rate >= 0.95  # At least 95% success rate
        assert avg_response_time < 2.0  # Average response time under 2s
        
        print(f"Continuous Operation Results:")
        print(f"  Duration: 30 seconds")
        print(f"  Total requests: {request_count}")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_rate * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_fault_tolerance(self, client, auth_headers):
        """Test fault tolerance"""
        # Create test data
        for i in range(20):
            supplier_data = {
                "name": f"Fault Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"fault-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://fault-{i}.com",
                "description": f"Fault Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Fault tolerance test
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
        
        # Create fault tolerance threads
        threads = []
        
        # 40 valid requests
        for _ in range(40):
            thread = threading.Thread(target=make_valid_request)
            threads.append(thread)
            thread.start()
        
        # 20 invalid requests
        for _ in range(20):
            thread = threading.Thread(target=make_invalid_request)
            threads.append(thread)
            thread.start()
        
        # 20 malformed requests
        for _ in range(20):
            thread = threading.Thread(target=make_malformed_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 80
        
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
        
        # Should handle faults gracefully
        assert valid_success >= 38  # At least 95% success rate for valid requests
        assert invalid_success >= 18  # At least 90% success rate for invalid requests
        assert malformed_success >= 18  # At least 90% success rate for malformed requests
        
        if valid_success > 0:
            avg_valid_time = total_valid_time / valid_success
            assert avg_valid_time < 1.0  # Average valid time under 1s
        
        if invalid_success > 0:
            avg_invalid_time = total_invalid_time / invalid_success
            assert avg_invalid_time < 0.5  # Average invalid time under 0.5s
        
        if malformed_success > 0:
            avg_malformed_time = total_malformed_time / malformed_success
            assert avg_malformed_time < 0.5  # Average malformed time under 0.5s
        
        print(f"Fault Tolerance Results:")
        print(f"  Valid requests: 40, Success: {valid_success}, Rate: {valid_success / 40 * 100:.1f}%")
        print(f"  Invalid requests: 20, Success: {invalid_success}, Rate: {invalid_success / 20 * 100:.1f}%")
        print(f"  Malformed requests: 20, Success: {malformed_success}, Rate: {malformed_success / 20 * 100:.1f}%")
        if valid_success > 0:
            print(f"  Average valid time: {avg_valid_time:.3f}s")
        if invalid_success > 0:
            print(f"  Average invalid time: {avg_invalid_time:.3f}s")
        if malformed_success > 0:
            print(f"  Average malformed time: {avg_malformed_time:.3f}s")
    
    def test_recovery_after_failure(self, client, auth_headers):
        """Test recovery after failure"""
        # Create test data
        for i in range(10):
            supplier_data = {
                "name": f"Recovery Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"recovery-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://recovery-{i}.com",
                "description": f"Recovery Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Recovery test
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
        
        # Should recover and handle requests
        assert success_count >= 45  # At least 90% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 3.0  # Average response time under 3s
        
        print(f"Recovery After Failure Results:")
        print(f"  Total requests: 50")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 50 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_data_consistency_under_load(self, client, auth_headers):
        """Test data consistency under load"""
        # Create test data
        for i in range(20):
            supplier_data = {
                "name": f"Consistency Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"consistency-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://consistency-{i}.com",
                "description": f"Consistency Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Data consistency test
        results = queue.Queue()
        
        def make_read_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "type": "read",
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "data": json.loads(response.data) if response.status_code == 200 else None
            })
        
        def make_write_request(supplier_id):
            supplier_data = {
                "name": f"Consistency Write Supplier {supplier_id}",
                "location": f"Location {supplier_id}",
                "contact_email": f"consistency-write-{supplier_id}@example.com",
                "contact_phone": f"+123456789{supplier_id % 10}",
                "website": f"https://consistency-write-{supplier_id}.com",
                "description": f"Consistency Write Supplier {supplier_id} Description"
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
        
        # Create consistency test threads
        threads = []
        
        # 30 read requests
        for _ in range(30):
            thread = threading.Thread(target=make_read_request)
            threads.append(thread)
            thread.start()
        
        # 20 write requests
        for i in range(20):
            thread = threading.Thread(target=make_write_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 50
        
        read_success = 0
        write_success = 0
        total_read_time = 0
        total_write_time = 0
        data_consistency_errors = 0
        
        while not results.empty():
            result = results.get()
            if result["type"] == "read":
                if result["status_code"] == 200:
                    read_success += 1
                    total_read_time += result["response_time"]
                    
                    # Check data consistency
                    if result["data"] and "data" in result["data"]:
                        suppliers = result["data"]["data"]
                        for supplier in suppliers:
                            if not supplier.get("name") or not supplier.get("location"):
                                data_consistency_errors += 1
            elif result["type"] == "write":
                if result["status_code"] == 200:
                    write_success += 1
                    total_write_time += result["response_time"]
        
        # Should maintain data consistency
        assert read_success >= 28  # At least 93% success rate for reads
        assert write_success >= 18  # At least 90% success rate for writes
        assert data_consistency_errors == 0  # No data consistency errors
        
        if read_success > 0:
            avg_read_time = total_read_time / read_success
            assert avg_read_time < 2.0  # Average read time under 2s
        
        if write_success > 0:
            avg_write_time = total_write_time / write_success
            assert avg_write_time < 3.0  # Average write time under 3s
        
        print(f"Data Consistency Under Load Results:")
        print(f"  Read requests: 30, Success: {read_success}, Rate: {read_success / 30 * 100:.1f}%")
        print(f"  Write requests: 20, Success: {write_success}, Rate: {write_success / 20 * 100:.1f}%")
        print(f"  Data consistency errors: {data_consistency_errors}")
        if read_success > 0:
            print(f"  Average read time: {avg_read_time:.3f}s")
        if write_success > 0:
            print(f"  Average write time: {avg_write_time:.3f}s")
    
    def test_graceful_degradation(self, client, auth_headers):
        """Test graceful degradation under stress"""
        # Create test data
        for i in range(50):
            supplier_data = {
                "name": f"Degradation Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"degradation-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://degradation-{i}.com",
                "description": f"Degradation Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Graceful degradation test
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 200 concurrent threads (stress)
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
        
        # Should degrade gracefully
        assert success_count >= 100  # At least 50% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 10.0  # Average response time under 10s
        
        print(f"Graceful Degradation Results:")
        print(f"  Total requests: 200")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 200 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
