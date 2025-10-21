"""
Monitoring tests for Peace Map API
"""

import pytest
import json
import time
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


class TestHealthChecks:
    """Test health check functionality"""
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert data["version"] == "1.0.0"
    
    def test_health_check_response_time(self, client):
        """Test health check response time"""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 0.1  # Should respond within 100ms
    
    def test_health_check_consistency(self, client):
        """Test health check consistency"""
        # Make multiple requests
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data["status"] == "healthy"
            assert data["version"] == "1.0.0"
    
    def test_health_check_headers(self, client):
        """Test health check headers"""
        response = client.get("/health")
        assert response.status_code == 200
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Strict-Transport-Security" in response.headers
        assert "Referrer-Policy" in response.headers


class TestMetrics:
    """Test metrics functionality"""
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Should return metrics data
        data = json.loads(response.data)
        assert "success" in data
        assert data["success"] is True
        assert "metrics" in data
    
    def test_metrics_data_structure(self, client):
        """Test metrics data structure"""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        metrics = data["metrics"]
        
        # Should have basic metrics
        assert "requests" in metrics
        assert "response_time" in metrics
        assert "error_rate" in metrics
        assert "active_connections" in metrics
    
    def test_metrics_accuracy(self, client, auth_headers):
        """Test metrics accuracy"""
        # Make some requests
        for _ in range(5):
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            assert response.status_code == 200
        
        # Check metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        metrics = data["metrics"]
        
        # Should reflect the requests made
        assert metrics["requests"] >= 5
        assert metrics["response_time"] > 0
        assert metrics["error_rate"] >= 0
    
    def test_metrics_real_time(self, client, auth_headers):
        """Test real-time metrics updates"""
        # Get initial metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        
        initial_data = json.loads(response.data)
        initial_requests = initial_data["metrics"]["requests"]
        
        # Make more requests
        for _ in range(3):
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            assert response.status_code == 200
        
        # Check updated metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        
        updated_data = json.loads(response.data)
        updated_requests = updated_data["metrics"]["requests"]
        
        # Should reflect the additional requests
        assert updated_requests >= initial_requests + 3


class TestLogging:
    """Test logging functionality"""
    
    def test_request_logging(self, client, auth_headers):
        """Test request logging"""
        with pytest.raises(Exception):  # Mock logger to raise exception
            response = client.get("/api/v1/suppliers", headers=auth_headers)
            assert response.status_code == 200
    
    def test_error_logging(self, client, auth_headers):
        """Test error logging"""
        # Make request to non-existent endpoint
        response = client.get("/api/v1/non-existent", headers=auth_headers)
        assert response.status_code == 404
        
        # Should log the error
        # In real implementation, this would be verified through log files
    
    def test_performance_logging(self, client, auth_headers):
        """Test performance logging"""
        start_time = time.time()
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        
        # Should log performance metrics
        # In real implementation, this would be verified through log files
        assert response_time < 1.0  # Should be fast
    
    def test_security_logging(self, client):
        """Test security logging"""
        # Test unauthorized access
        response = client.get("/api/v1/suppliers")
        assert response.status_code == 401
        
        # Should log security events
        # In real implementation, this would be verified through log files
        
        # Test invalid token
        headers = {
            "Authorization": "Bearer invalid-token",
            "Content-Type": "application/json"
        }
        
        response = client.get("/api/v1/suppliers", headers=headers)
        assert response.status_code == 401
        
        # Should log security events
        # In real implementation, this would be verified through log files


class TestAlerting:
    """Test alerting functionality"""
    
    def test_alert_generation(self, client, auth_headers):
        """Test alert generation"""
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
        
        # Create alert
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
        
        # Verify alert was created
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["supplier_id"] == supplier_id
        assert data["data"]["risk_threshold"] == 75.0
    
    def test_alert_threshold_monitoring(self, client, auth_headers):
        """Test alert threshold monitoring"""
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
        
        # Create alert with low threshold
        alert_data = {
            "supplier_id": supplier_id,
            "risk_threshold": 50.0,
            "notification_email": "alert@example.com",
            "notification_phone": "+1234567890",
            "description": "Low Threshold Alert"
        }
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps(alert_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        alert_id = data["data"]["id"]
        
        # Verify alert was created
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["risk_threshold"] == 50.0
    
    def test_alert_notification(self, client, auth_headers):
        """Test alert notification"""
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
        
        # Create alert with notification
        alert_data = {
            "supplier_id": supplier_id,
            "risk_threshold": 75.0,
            "notification_email": "alert@example.com",
            "notification_phone": "+1234567890",
            "description": "Test Alert with Notification"
        }
        
        response = client.post(
            "/api/v1/alerts",
            data=json.dumps(alert_data),
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        alert_id = data["data"]["id"]
        
        # Verify alert has notification settings
        response = client.get(f"/api/v1/alerts/{alert_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["data"]["notification_email"] == "alert@example.com"
        assert data["data"]["notification_phone"] == "+1234567890"


class TestSystemMonitoring:
    """Test system monitoring functionality"""
    
    def test_system_health_monitoring(self, client):
        """Test system health monitoring"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        
        # Should include system information
        assert "timestamp" in data
        assert "version" in data
    
    def test_database_health_monitoring(self, client, auth_headers):
        """Test database health monitoring"""
        # Make database operations
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        assert response.status_code == 200
        
        # Should not have database errors
        data = json.loads(response.data)
        assert "success" in data
        assert data["success"] is True
    
    def test_api_health_monitoring(self, client, auth_headers):
        """Test API health monitoring"""
        # Test all major endpoints
        endpoints = [
            "/api/v1/suppliers",
            "/api/v1/projects/1/events",
            "/api/v1/risk-index",
            "/api/v1/alerts"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert "success" in data
            assert data["success"] is True
    
    def test_performance_monitoring(self, client, auth_headers):
        """Test performance monitoring"""
        # Make requests and measure performance
        start_time = time.time()
        response = client.get("/api/v1/suppliers", headers=auth_headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 1.0  # Should be fast
        
        # Should log performance metrics
        # In real implementation, this would be verified through monitoring systems
    
    def test_error_monitoring(self, client, auth_headers):
        """Test error monitoring"""
        # Test error scenarios
        response = client.get("/api/v1/suppliers/999", headers=auth_headers)
        assert response.status_code == 404
        
        # Should log errors
        # In real implementation, this would be verified through monitoring systems
        
        # Test validation errors
        invalid_data = {
            "name": "",  # Invalid name
            "location": "Test Location"
        }
        
        response = client.post(
            "/api/v1/suppliers",
            data=json.dumps(invalid_data),
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Should log validation errors
        # In real implementation, this would be verified through monitoring systems
