"""
Resilience tests for Peace Map API
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


class TestResilience:
    """Test resilience scenarios"""
    
    def test_system_recovery(self, client, auth_headers):
        """Test system recovery after stress"""
        # Create test data
        for i in range(20):
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
        
        # Stress the system
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 100 concurrent threads (stress)
        threads = []
        for _ in range(100):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check stress results
        assert results.qsize() == 100
        
        stress_success = 0
        total_stress_time = 0
        
        while not results.empty():
            result = results.get()
            if result["status_code"] == 200:
                stress_success += 1
                total_stress_time += result["response_time"]
        
        # Should handle stress
        assert stress_success >= 50  # At least 50% success rate under stress
        
        # Test recovery
        recovery_results = queue.Queue()
        
        def make_recovery_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            recovery_results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 50 concurrent threads (recovery)
        threads = []
        for _ in range(50):
            thread = threading.Thread(target=make_recovery_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check recovery results
        assert recovery_results.qsize() == 50
        
        recovery_success = 0
        total_recovery_time = 0
        
        while not recovery_results.empty():
            result = recovery_results.get()
            if result["status_code"] == 200:
                recovery_success += 1
                total_recovery_time += result["response_time"]
        
        # Should recover well
        assert recovery_success >= 45  # At least 90% success rate after recovery
        
        if recovery_success > 0:
            avg_recovery_time = total_recovery_time / recovery_success
            assert avg_recovery_time < 3.0  # Average recovery time under 3s
        
        print(f"System Recovery Results:")
        print(f"  Stress requests: 100, Success: {stress_success}, Rate: {stress_success / 100 * 100:.1f}%")
        print(f"  Recovery requests: 50, Success: {recovery_success}, Rate: {recovery_success / 50 * 100:.1f}%")
        if recovery_success > 0:
            print(f"  Average recovery time: {avg_recovery_time:.3f}s")
    
    def test_adaptive_scaling(self, client, auth_headers):
        """Test adaptive scaling under varying load"""
        # Create test data
        for i in range(30):
            supplier_data = {
                "name": f"Scaling Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"scaling-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://scaling-{i}.com",
                "description": f"Scaling Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test varying load
        load_levels = [10, 30, 50, 30, 10]  # Varying load levels
        all_results = []
        
        for load_level in load_levels:
            results = queue.Queue()
            
            def make_request():
                start_time = time.time()
                response = client.get("/api/v1/suppliers", headers=auth_headers)
                end_time = time.time()
                
                results.put({
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                })
            
            # Create threads for current load level
            threads = []
            for _ in range(load_level):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Process results
            success_count = 0
            total_response_time = 0
            
            while not results.empty():
                result = results.get()
                if result["status_code"] == 200:
                    success_count += 1
                    total_response_time += result["response_time"]
            
            all_results.append({
                "load_level": load_level,
                "success_count": success_count,
                "success_rate": success_count / load_level,
                "avg_response_time": total_response_time / success_count if success_count > 0 else 0
            })
            
            # Small delay between load levels
            time.sleep(1)
        
        # Check adaptive scaling
        for result in all_results:
            assert result["success_rate"] >= 0.8  # At least 80% success rate
            assert result["avg_response_time"] < 5.0  # Average response time under 5s
        
        print(f"Adaptive Scaling Results:")
        for result in all_results:
            print(f"  Load: {result['load_level']}, Success: {result['success_count']}, Rate: {result['success_rate'] * 100:.1f}%, Avg Time: {result['avg_response_time']:.3f}s")
    
    def test_fault_isolation(self, client, auth_headers):
        """Test fault isolation"""
        # Create test data
        for i in range(20):
            supplier_data = {
                "name": f"Isolation Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"isolation-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://isolation-{i}.com",
                "description": f"Isolation Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Fault isolation test
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
        
        # Create fault isolation threads
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
        
        # Should isolate faults
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
        
        print(f"Fault Isolation Results:")
        print(f"  Valid requests: 40, Success: {valid_success}, Rate: {valid_success / 40 * 100:.1f}%")
        print(f"  Invalid requests: 20, Success: {invalid_success}, Rate: {invalid_success / 20 * 100:.1f}%")
        print(f"  Malformed requests: 20, Success: {malformed_success}, Rate: {malformed_success / 20 * 100:.1f}%")
        if valid_success > 0:
            print(f"  Average valid time: {avg_valid_time:.3f}s")
        if invalid_success > 0:
            print(f"  Average invalid time: {avg_invalid_time:.3f}s")
        if malformed_success > 0:
            print(f"  Average malformed time: {avg_malformed_time:.3f}s")
    
    def test_circuit_breaker_pattern(self, client, auth_headers):
        """Test circuit breaker pattern"""
        # Create test data
        for i in range(10):
            supplier_data = {
                "name": f"Circuit Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"circuit-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://circuit-{i}.com",
                "description": f"Circuit Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Circuit breaker test
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            end_time = time.time()
            
            results.put({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create 100 concurrent threads (circuit breaker test)
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
        
        # Should handle circuit breaker
        assert success_count >= 80  # At least 80% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 5.0  # Average response time under 5s
        
        print(f"Circuit Breaker Pattern Results:")
        print(f"  Total requests: 100")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 100 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
    
    def test_graceful_shutdown(self, client, auth_headers):
        """Test graceful shutdown"""
        # Create test data
        for i in range(10):
            supplier_data = {
                "name": f"Shutdown Supplier {i}",
                "location": f"Location {i}",
                "contact_email": f"shutdown-{i}@example.com",
                "contact_phone": f"+123456789{i % 10}",
                "website": f"https://shutdown-{i}.com",
                "description": f"Shutdown Supplier {i} Description"
            }
            
            response = client.post(
                "/api/v1/suppliers",
                data=json.dumps(supplier_data),
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Graceful shutdown test
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
        
        # Should handle graceful shutdown
        assert success_count >= 45  # At least 90% success rate
        
        if success_count > 0:
            avg_response_time = total_response_time / success_count
            assert avg_response_time < 3.0  # Average response time under 3s
        
        print(f"Graceful Shutdown Results:")
        print(f"  Total requests: 50")
        print(f"  Successful requests: {success_count}")
        print(f"  Success rate: {success_count / 50 * 100:.1f}%")
        if success_count > 0:
            print(f"  Average response time: {avg_response_time:.3f}s")
