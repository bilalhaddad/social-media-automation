"""
Chaos engineering tests for Peace Map API
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


class TestChaosEngineering:
    """Test chaos engineering scenarios"""
    
    def test_rapid_request_burst(self, client, auth_headers):
        """Test rapid request burst scenario"""
        # Create test data
        for i in range(10):
            supplier_data = {
                "name": f"Burst Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"burst-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://burst-{i}.com",
                "description": f"Burst Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Rapid request burst
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 100 concurrent threads rapidly
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
        
        # Should handle burst reasonably
        assert success_count >= 80  # At least 80% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 5.0  # Average response time under 5s
        
        print(f"Rapid Request Burst Results:")
        print(f"  Total requests: 100")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 100 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_sustained_high_load(self, client, auth_headers):
        """Test sustained high load scenario"""
        # Create test data
        for i in range(50):
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
        
        # Sustained high load
        start_time = time.time()
        request_count = 0
        success_count = 0
        total_response_time = 0
        
        # Simulate sustained high load
        while time.time() - start_time < 60:  # 1 minute
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
            time.sleep(0.1)
        
        # Calculate statistics
        success_rate = success_count / request_count if request_count > 0 else 0
        avg_response_time = total_response_time / success_count if success_count > 0 else 0
        
        # Should maintain reasonable performance
        assert success_rate >= 0.7  # At least 70% success rate
        assert avg_response_time < 10.0  # Average response time under 10s
        
        print(f"Sustained High Load Results:")
        print(f"  Duration: 60 seconds")
        print(f"  Total requests: {request_count}")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_rate * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_mixed_operation_chaos(self, client, auth_headers):
        """Test mixed operation chaos scenario"""
        # Create initial data
        for i in range(20):
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
                "name": f"Chaos Supplier {supplier_id}",
                "location": f"Location {supplier_id}",
                "contact_email": f"chaos-{supplier_id}@example.com",
                "contact_phone": f"+123456789{supplier_id % 10}",
                "website": f"https://chaos-{supplier_id}.com",
                "description": f"Chaos Supplier {supplier_id} Description"
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
        
        def make_update_request(supplier_id):
            update_data = {
                "name": f"Updated Chaos Supplier {supplier_id}",
                "contact_email": f"updated-chaos-{supplier_id}@example.com"
            }
            
            start_time = time.time()
            response = client.put(
                f"/api/v1/suppliers/{supplier_id}",
                data=json.dumps(update_data),
                headers=auth_headers
            )
            end_time = time.time()
            
            results.put({
                "type": "update",
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "supplier_id": supplier_id
            })
        
        def make_delete_request(supplier_id):
            start_time = time.time()
            response = client.delete(f"/api/v1/suppliers/{supplier_id}", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "type": "delete",
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "supplier_id": supplier_id
            })
        
        # Create mixed chaos threads
        threads = []
        
        # 50 read requests
        for _ in range(50):
            thread = threading.Thread(target=make_read_request)
            threads.append(thread)
            thread.start()
        
        # 25 write requests
        for i in range(25):
            thread = threading.Thread(target=make_write_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 25 update requests
        for i in range(25):
            thread = threading.Thread(target=make_update_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 25 delete requests
        for i in range(25):
            thread = threading.Thread(target=make_delete_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 125
        
        read_success = 0
        write_success = 0
        update_success = 0
        delete_success = 0
        total_read_time = 0
        total_write_time = 0
        total_update_time = 0
        total_delete_time = 0
        
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
            elif result["type"] == "update":
                if result["status_code"] == 200:
                    update_success += 1
                    total_update_time += result["response_time"]
            elif result["type"] == "delete":
                if result["status_code"] == 200:
                    delete_success += 1
                    total_delete_time += result["response_time"]
        
        # Should handle chaos reasonably
        assert read_success >= 40  # At least 80% success rate for reads
        assert write_success >= 20  # At least 80% success rate for writes
        assert update_success >= 20  # At least 80% success rate for updates
        assert delete_success >= 20  # At least 80% success rate for deletes
        
        if read_success > 0:
            avg_read_time = total_read_time / read_success
            assert avg_read_time < 5.0  # Average read time under 5s
        
        if write_success > 0:
            avg_write_time = total_write_time / write_success
            assert avg_write_time < 10.0  # Average write time under 10s
        
        if update_success > 0:
            avg_update_time = total_update_time / update_success
            assert avg_update_time < 10.0  # Average update time under 10s
        
        if delete_success > 0:
            avg_delete_time = total_delete_time / delete_success
            assert avg_delete_time < 10.0  # Average delete time under 10s
        
        print(f"Mixed Operation Chaos Results:")
        print(f"  Read requests: 50, Success: {read_success}, Rate: {read_success / 50 * 100:.1f}%")
        print(f"  Write requests: 25, Success: {write_success}, Rate: {write_success / 25 * 100:.1f}%")
        print(f"  Update requests: 25, Success: {update_success}, Rate: {update_success / 25 * 100:.1f}%")
        print(f"  Delete requests: 25, Success: {delete_success}, Rate: {delete_success / 25 * 100:.1f}%")
        if read_success > 0:
            print(f"  Average read time: {avg_read_time:.3f}s")
        if write_success > 0:
            print(f"  Average write time: {avg_write_time:.3f}s")
        if update_success > 0:
            print(f"  Average update time: {avg_update_time:.3f}s")
        if delete_success > 0:
            print(f"  Average delete time: {avg_delete_time:.3f}s")
    
    def test_error_injection_chaos(self, client, auth_headers):
        """Test error injection chaos scenario"""
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
        
        # Create chaos threads
        threads = []
        
        # 30 valid requests
        for _ in range(30):
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
        assert results.qsize() == 70
        
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
        
        # Should handle error injection
        assert valid_success >= 25  # At least 83% success rate for valid requests
        assert invalid_success >= 15  # At least 75% success rate for invalid requests
        assert malformed_success >= 15  # At least 75% success rate for malformed requests
        
        if valid_success > 0:
            avg_valid_time = total_valid_time / valid_success
            assert avg_valid_time < 2.0  # Average valid time under 2s
        
        if invalid_success > 0:
            avg_invalid_time = total_invalid_time / invalid_success
            assert avg_invalid_time < 1.0  # Average invalid time under 1s
        
        if malformed_success > 0:
            avg_malformed_time = total_malformed_time / malformed_success
            assert avg_malformed_time < 1.0  # Average malformed time under 1s
        
        print(f"Error Injection Chaos Results:")
        print(f"  Valid requests: 30, Success: {valid_success}, Rate: {valid_success / 30 * 100:.1f}%")
        print(f"  Invalid requests: 20, Success: {invalid_success}, Rate: {invalid_success / 20 * 100:.1f}%")
        print(f"  Malformed requests: 20, Success: {malformed_success}, Rate: {malformed_success / 20 * 100:.1f}%")
        if valid_success > 0:
            print(f"  Average valid time: {avg_valid_time:.3f}s")
        if invalid_success > 0:
            print(f"  Average invalid time: {avg_invalid_time:.3f}s")
        if malformed_success > 0:
            print(f"  Average malformed time: {avg_malformed_time:.3f}s")
    
    def test_resource_exhaustion_chaos(self, client, auth_headers):
        """Test resource exhaustion chaos scenario"""
        # Create test data
        for i in range(100):
            supplier_data = {
                "name": f"Resource Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"resource-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://resource-{i}.com",
                "description": f"Resource Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Resource exhaustion test
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 500 concurrent threads (resource exhaustion)
        threads = []
        for _ in range(500):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert results.qsize() == 500
        
        success_count = 0
        total_response_time = 0
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                success_count += 1
                total_response_time += result["response_time"]
        
        # Should handle resource exhaustion with degradation
        assert success_count >= 200  # At least 40% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 20.0  # Average response time under 20s
        
        print(f"Resource Exhaustion Chaos Results:")
        print(f"  Total requests: 500")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 500 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
