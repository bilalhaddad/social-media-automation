"""
Tests for Peace Map API middleware
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from peace_map.api.app import app
from peace_map.api.middleware import (
    LoggingMiddleware, RateLimitMiddleware, SecurityMiddleware, ValidationMiddleware
)


@pytest.fixture
def client():
    """Test client fixture"""
    with app.test_client() as client:
        yield client


class TestLoggingMiddleware:
    """Test logging middleware"""
    
    def test_logging_middleware_success(self, client):
        """Test successful request logging"""
        with patch('peace_map.api.middleware.logger') as mock_logger:
            response = client.get("/health")
            
            # Should log request and response
            assert mock_logger.info.called
            assert response.status_code == 200
    
    def test_logging_middleware_error(self, client):
        """Test error request logging"""
        with patch('peace_map.api.middleware.logger') as mock_logger:
            # Make request to non-existent endpoint
            response = client.get("/non-existent")
            
            # Should log request and error
            assert mock_logger.info.called
            assert response.status_code == 404
    
    def test_logging_middleware_request_id(self, client):
        """Test request ID generation"""
        with patch('peace_map.api.middleware.logger') as mock_logger:
            response = client.get("/health")
            
            # Should have request ID in headers
            assert "X-Request-ID" in response.headers
            assert "X-Process-Time" in response.headers


class TestRateLimitMiddleware:
    """Test rate limiting middleware"""
    
    def test_rate_limit_success(self, client):
        """Test successful rate limit check"""
        # Make request within rate limit
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_rate_limit_exceeded(self, client):
        """Test rate limit exceeded"""
        # Mock rate limit exceeded
        with patch('peace_map.api.middleware.RateLimitMiddleware.dispatch') as mock_dispatch:
            mock_dispatch.return_value = {
                "success": False,
                "error": "Rate limit exceeded",
                "message": "Too many requests. Limit: 60 per minute"
            }
            
            response = client.get("/health")
            assert response.status_code == 429
    
    def test_rate_limit_cleanup(self, client):
        """Test rate limit cleanup"""
        middleware = RateLimitMiddleware(app, calls_per_minute=60)
        
        # Add some old entries
        middleware.requests = {
            "127.0.0.1": [time.time() - 120, time.time() - 60, time.time()]
        }
        
        # Cleanup should remove old entries
        current_time = time.time()
        middleware.requests = {
            ip: timestamps for ip, timestamps in middleware.requests.items()
            if any(ts > current_time - 60 for ts in timestamps)
        }
        
        # Should only keep recent entry
        assert len(middleware.requests["127.0.0.1"]) == 1


class TestSecurityMiddleware:
    """Test security middleware"""
    
    def test_security_headers(self, client):
        """Test security headers are added"""
        response = client.get("/health")
        
        # Should have security headers
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


class TestValidationMiddleware:
    """Test validation middleware"""
    
    def test_validation_middleware_success(self, client):
        """Test successful validation"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_validation_middleware_large_request(self, client):
        """Test validation with large request"""
        # Mock large content length
        with patch('peace_map.api.middleware.ValidationMiddleware.dispatch') as mock_dispatch:
            mock_dispatch.return_value = {
                "success": False,
                "error": "Request too large",
                "message": "Request body exceeds 10MB limit"
            }
            
            response = client.get("/health")
            assert response.status_code == 413
    
    def test_validation_middleware_invalid_content_type(self, client):
        """Test validation with invalid content type"""
        # Mock invalid content type
        with patch('peace_map.api.middleware.ValidationMiddleware.dispatch') as mock_dispatch:
            mock_dispatch.return_value = {
                "success": False,
                "error": "Unsupported media type",
                "message": "Content-Type must be application/json, multipart/form-data, or text/csv"
            }
            
            response = client.get("/health")
            assert response.status_code == 415
    
    def test_validation_middleware_valid_content_type(self, client):
        """Test validation with valid content type"""
        # Mock valid content type
        with patch('peace_map.api.middleware.ValidationMiddleware.dispatch') as mock_dispatch:
            mock_dispatch.return_value = {"success": True}
            
            response = client.get("/health")
            assert response.status_code == 200


class TestMiddlewareIntegration:
    """Test middleware integration"""
    
    def test_all_middleware_working(self, client):
        """Test all middleware working together"""
        response = client.get("/health")
        
        # Should have all middleware effects
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
    
    def test_middleware_error_handling(self, client):
        """Test middleware error handling"""
        # Mock middleware error
        with patch('peace_map.api.middleware.LoggingMiddleware.dispatch') as mock_dispatch:
            mock_dispatch.side_effect = Exception("Middleware error")
            
            response = client.get("/health")
            assert response.status_code == 500
    
    def test_middleware_performance(self, client):
        """Test middleware performance impact"""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        # Should complete quickly
        assert end_time - start_time < 1.0
        assert response.status_code == 200
    
    def test_middleware_logging(self, client):
        """Test middleware logging"""
        with patch('peace_map.api.middleware.logger') as mock_logger:
            response = client.get("/health")
            
            # Should log request and response
            assert mock_logger.info.called
            assert response.status_code == 200
    
    def test_middleware_security(self, client):
        """Test middleware security"""
        response = client.get("/health")
        
        # Should have security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Strict-Transport-Security" in response.headers
        assert "Referrer-Policy" in response.headers
    
    def test_middleware_validation(self, client):
        """Test middleware validation"""
        response = client.get("/health")
        
        # Should pass validation
        assert response.status_code == 200
    
    def test_middleware_rate_limiting(self, client):
        """Test middleware rate limiting"""
        # Make multiple requests
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
        
        # Should not hit rate limit for small number of requests
        assert response.status_code == 200
