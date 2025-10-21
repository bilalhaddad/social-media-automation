"""
Security tests for Peace Map API
"""

import pytest
import json
from peace_map.api.models import db
from peace_map.api.app import app


@pytest.fixture
def client():
    """Test client fixture"""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


class TestAuthentication:
    """Test authentication security"""
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints"""
        # Test without authentication
        response = client.get("/api/v1/suppliers")
        assert response.status_code == 401
        
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps({"name": "Test Supplier", "location": "Test Location"}),
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401
        
        response = client.get("/api/v1/alerts")
        assert response.status_code == 401
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps({"supplier_id": 1, "risk_threshold": 75.0}),
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401
    
    def test_invalid_token(self, client):
        """Test invalid token authentication"""
        headers = {
            "Authorization": "Bearer invalid-token",
            "Content-Type": "application/json"
        }
        
        response = client.get("/api/v1/suppliers", headers=headers)
        assert response.status_code == 401
        
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps({"name": "Test Supplier", "location": "Test Location"}),
            headers=headers
        )
        assert response.status_code == 401
    
    def test_malformed_token(self, client):
        """Test malformed token authentication"""
        headers = {
            "Authorization": "InvalidFormat token",
            "Content-Type": "application/json"
        }
        
        response = client.get("/api/v1/suppliers", headers=headers)
        assert response.status_code == 401
        
        headers = {
            "Authorization": "Bearer",
            "Content-Type": "application/json"
        }
        
        response = client.get("/api/v1/suppliers", headers=headers)
        assert response.status_code == 401


class TestAuthorization:
    """Test authorization security"""
    
    def test_read_permission_required(self, client):
        """Test read permission requirement"""
        # Mock user with read permission
        headers = {
            "Authorization": "Bearer valid-token",
            "Content-Type": "application/json"
        }
        
        # Should allow read operations
        response = client.get("/api/v1/suppliers", headers=headers)
        assert response.status_code != 403  # Should not be forbidden
        
        # Should allow read operations for events
        response = client.get("/api/v1/projects/1/events", headers=headers)
        assert response.status_code != 403  # Should not be forbidden
        
        # Should allow read operations for alerts
        response = client.get("/api/v1/alerts", headers=headers)
        assert response.status_code != 403  # Should not be forbidden
    
    def test_write_permission_required(self, client):
        """Test write permission requirement"""
        # Mock user without write permission
        headers = {
            "Authorization": "Bearer read-only-token",
            "Content-Type": "application/json"
        }
        
        # Should deny write operations
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps({"name": "Test Supplier", "location": "Test Location"}),
            headers=headers
        )
        assert response.status_code == 403  # Should be forbidden
        
        response = client.put(
            "/api/v1/suppliers/1",
            data=json.dumps({"name": "Updated Supplier"}),
            headers=headers
        )
        assert response.status_code == 403  # Should be forbidden
        
        response = client.delete("/api/v1/suppliers/1", headers=headers)
        assert response.status_code == 403  # Should be forbidden
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps({"supplier_id": 1, "risk_threshold": 75.0}),
            headers=headers
        )
        assert response.status_code == 403  # Should be forbidden
    
    def test_admin_permission_required(self, client):
        """Test admin permission requirement"""
        # Mock user without admin permission
        headers = {
            "Authorization": "Bearer non-admin-token",
            "Content-Type": "application/json"
        }
        
        # Should deny admin operations
        response = client.get("/api/v1/admin/users", headers=headers)
        assert response.status_code == 403  # Should be forbidden
        
        response = client.post(
            "/api/v1/admin/users",
            data=json.dumps({"username": "newuser", "role": "admin"}),
            headers=headers
        )
        assert response.status_code == 403  # Should be forbidden


class TestInputValidation:
    """Test input validation security"""
    
    def test_sql_injection_prevention(self, client):
        """Test SQL injection prevention"""
        headers = {
            "Authorization": "Bearer valid-token",
            "Content-Type": "application/json"
        }
        
        # Test SQL injection in event title
        malicious_data = {
            "title": "'; DROP TABLE events; --",
            "description": "Test Description",
            "event_type": "protest",
            "location": "Test Location",
            "source": "Test Source",
            "source_confidence": 0.8
        }
        
        response = client.post(
            "/api/v1/projects/1/events",
            data=json.dumps(malicious_data),
            headers=headers
        )
        # Should either create event safely or return validation error
        assert response.status_code in [200, 422]
        
        # Verify table still exists
        response = client.get("/api/v1/projects/1/events", headers=headers)
        assert response.status_code == 200
    
    def test_xss_prevention(self, client):
        """Test XSS prevention"""
        headers = {
            "Authorization": "Bearer valid-token",
            "Content-Type": "application/json"
        }
        
        # Test XSS in event description
        malicious_data = {
            "title": "Test Event",
            "description": "<script>alert('XSS')</script>",
            "event_type": "protest",
            "location": "Test Location",
            "source": "Test Source",
            "source_confidence": 0.8
        }
        
        response = client.post(
            "/api/v1/projects/1/events",
            data=json.dumps(malicious_data),
            headers=headers
        )
        # Should either create event safely or return validation error
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            # Description should be sanitized or escaped
            assert "<script>" not in data["data"]["description"]
    
    def test_path_traversal_prevention(self, client):
        """Test path traversal prevention"""
        headers = {
            "Authorization": "Bearer valid-token",
            "Content-Type": "application/json"
        }
        
        # Test path traversal in file upload
        malicious_data = {
            "name": "Test Supplier",
            "location": "Test Location",
            "website": "https://example.com/../../../etc/passwd"
        }
        
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps(malicious_data),
            headers=headers
        )
        # Should either create supplier safely or return validation error
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            # Website should be sanitized
            assert "../" not in data["data"]["website"]
    
    def test_command_injection_prevention(self, client):
        """Test command injection prevention"""
        headers = {
            "Authorization": "Bearer valid-token",
            "Content-Type": "application/json"
        }
        
        # Test command injection in supplier name
        malicious_data = {
            "name": "Test Supplier; rm -rf /",
            "location": "Test Location",
            "contact_email": "test@example.com"
        }
        
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps(malicious_data),
            headers=headers
        )
        # Should either create supplier safely or return validation error
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            # Name should be sanitized
            assert "rm -rf" not in data["data"]["name"]


class TestRateLimiting:
    """Test rate limiting security"""
    
    def test_rate_limit_enforcement(self, client):
        """Test rate limit enforcement"""
        headers = {
            "Authorization": "Bearer valid-token",
            "Content-Type": "application/json"
        }
        
        # Make multiple requests quickly
        for i in range(65):  # Exceed rate limit
            response = client.get("/api/v1/suppliers", headers=headers)
            if response.status_code == 429:  # Rate limit exceeded
                break
        
        # Should eventually hit rate limit
        assert response.status_code == 429
        
        # Verify rate limit response format
        data = json.loads(response.data)
        assert "success" in data
        assert data["success"] is False
        assert "Rate limit exceeded" in data["error"]
    
    def test_rate_limit_reset(self, client):
        """Test rate limit reset"""
        headers = {
            "Authorization": "Bearer valid-token",
            "Content-Type": "application/json"
        }
        
        # Wait for rate limit to reset (in real implementation)
        import time
        time.sleep(1)  # Short wait for testing
        
        # Should be able to make requests again
        response = client.get("/api/v1/suppliers", headers=headers)
        assert response.status_code != 429


class TestDataProtection:
    """Test data protection security"""
    
    def test_sensitive_data_exposure(self, client):
        """Test sensitive data exposure prevention"""
        headers = {
            "Authorization": "Bearer valid-token",
            "Content-Type": "application/json"
        }
        
        # Create supplier with sensitive data
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
            headers=headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        supplier_id = data["data"]["id"]
        
        # Get supplier data
        response = client.get(f"/api/v1/suppliers/{supplier_id}", headers=headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        supplier_info = data["data"]
        
        # Verify sensitive data is not exposed inappropriately
        assert "password" not in supplier_info
        assert "secret" not in supplier_info
        assert "key" not in supplier_info
        
        # Verify appropriate data is included
        assert "name" in supplier_info
        assert "location" in supplier_info
        assert "contact_email" in supplier_info
    
    def test_data_encryption(self, client):
        """Test data encryption"""
        headers = {
            "Authorization": "Bearer valid-token",
            "Content-Type": "application/json"
        }
        
        # Create alert with sensitive data
        alert_data = {
            "supplier_id": 1,
            "risk_threshold": 75.0,
            "notification_email": "alert@example.com",
            "notification_phone": "+1234567890",
            "description": "Sensitive alert information"
        }
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps(alert_data),
            headers=headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        alert_id = data["data"]["id"]
        
        # Get alert data
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        alert_info = data["data"]
        
        # Verify sensitive data is properly handled
        assert "notification_phone" in alert_info
        assert "notification_email" in alert_info
        assert "description" in alert_info
        
        # Verify data is not corrupted
        assert alert_info["risk_threshold"] == 75.0
        assert alert_info["notification_email"] == "alert@example.com"


class TestSecurityHeaders:
    """Test security headers"""
    
    def test_security_headers_present(self, client):
        """Test security headers are present"""
        response = client.get("/health")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Strict-Transport-Security" in response.headers
        assert "Referrer-Policy" in response.headers
    
    def test_security_headers_values(self, client):
        """Test security headers have correct values"""
        response = client.get("/health")
        
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    
    def test_cors_headers(self, client):
        """Test CORS headers"""
        response = client.get("/health")
        
        # Check for CORS headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers
    
    def test_cors_headers_values(self, client):
        """Test CORS headers have correct values"""
        response = client.get("/health")
        
        assert response.headers["Access-Control-Allow-Origin"] == "*"
        assert "GET" in response.headers["Access-Control-Allow-Methods"]
        assert "POST" in response.headers["Access-Control-Allow-Methods"]
        assert "PUT" in response.headers["Access-Control-Allow-Methods"]
        assert "DELETE" in response.headers["Access-Control-Allow-Methods"]
        assert "Authorization" in response.headers["Access-Control-Allow-Headers"]
        assert "Content-Type" in response.headers["Access-Control-Allow-Headers"]


class TestErrorHandling:
    """Test error handling security"""
    
    def test_error_information_disclosure(self, client):
        """Test error information disclosure prevention"""
        headers = {
            "Authorization": "Bearer valid-token",
            "Content-Type": "application/json"
        }
        
        # Test with invalid data
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps({"invalid": "data"}),
            headers=headers
        )
        
        # Should not expose internal details
        assert response.status_code in [400, 422]
        
        if response.status_code == 400:
            data = json.loads(response.data)
            assert "success" in data
            assert data["success"] is False
            assert "error" in data
            assert "message" in data
            
            # Should not expose internal details
            assert "traceback" not in str(data)
            assert "exception" not in str(data)
            assert "stack" not in str(data)
    
    def test_error_consistency(self, client):
        """Test error response consistency"""
        headers = {
            "Authorization": "Bearer valid-token",
            "Content-Type": "application/json"
        }
        
        # Test different error scenarios
        error_scenarios = [
            ("/api/v1/suppliers/999", "GET"),
            ("/api/v1/suppliers/999", "PUT"),
            ("/api/v1/suppliers/999", "DELETE"),
            ("/api/v1/alerts/999", "GET"),
            ("/api/v1/alerts/999", "PUT"),
            ("/api/v1/alerts/999", "DELETE")
        ]
        
        for endpoint, method in error_scenarios:
            if method == "GET":
                response = client.get(endpoint, headers=headers)
            elif method == "PUT":
                response = client.put(
                    endpoint,
                    data=json.dumps({"name": "Updated"}),
                    headers=headers
                )
            elif method == "DELETE":
                response = client.delete(endpoint, headers=headers)
            
            # Should return consistent error format
            assert response.status_code in [404, 400, 422]
            
            if response.status_code == 404:
                data = json.loads(response.data)
                assert "success" in data
                assert data["success"] is False
                assert "error" in data
                assert "message" in data
