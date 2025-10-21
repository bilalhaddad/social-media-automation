"""
Tests for Peace Map API error handling
"""

import pytest
from fastapi import HTTPException
from peace_map.api.errors import (
    PeaceMapError, ValidationError, NotFoundError, ConflictError,
    RateLimitError, ExternalServiceError, DatabaseError,
    create_error_response, http_exception_handler, validation_exception_handler,
    peace_map_error_handler, general_exception_handler
)
from fastapi import Request
from fastapi.exceptions import RequestValidationError


@pytest.fixture
def mock_request():
    """Mock request fixture"""
    request = MagicMock()
    request.state.request_id = "test-request-id"
    return request


class TestCustomExceptions:
    """Test custom exceptions"""
    
    def test_peace_map_error(self):
        """Test PeaceMapError base exception"""
        error = PeaceMapError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_validation_error(self):
        """Test ValidationError exception"""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, PeaceMapError)
    
    def test_not_found_error(self):
        """Test NotFoundError exception"""
        error = NotFoundError("Resource not found")
        assert str(error) == "Resource not found"
        assert isinstance(error, PeaceMapError)
    
    def test_conflict_error(self):
        """Test ConflictError exception"""
        error = ConflictError("Resource conflict")
        assert str(error) == "Resource conflict"
        assert isinstance(error, PeaceMapError)
    
    def test_rate_limit_error(self):
        """Test RateLimitError exception"""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert isinstance(error, PeaceMapError)
    
    def test_external_service_error(self):
        """Test ExternalServiceError exception"""
        error = ExternalServiceError("External service error")
        assert str(error) == "External service error"
        assert isinstance(error, PeaceMapError)
    
    def test_database_error(self):
        """Test DatabaseError exception"""
        error = DatabaseError("Database error")
        assert str(error) == "Database error"
        assert isinstance(error, PeaceMapError)


class TestErrorResponse:
    """Test error response creation"""
    
    def test_create_error_response_basic(self):
        """Test basic error response creation"""
        response = create_error_response(
            status_code=400,
            error="Validation Error",
            message="Invalid input"
        )
        
        assert response.status_code == 400
        content = response.body.decode()
        assert "Validation Error" in content
        assert "Invalid input" in content
        assert "success" in content
        assert "false" in content
    
    def test_create_error_response_with_details(self):
        """Test error response with details"""
        details = {"field": "value", "code": 123}
        response = create_error_response(
            status_code=422,
            error="Validation Error",
            message="Request validation failed",
            details=details
        )
        
        assert response.status_code == 422
        content = response.body.decode()
        assert "Validation Error" in content
        assert "Request validation failed" in content
        assert "details" in content
    
    def test_create_error_response_with_request_id(self):
        """Test error response with request ID"""
        response = create_error_response(
            status_code=500,
            error="Internal Server Error",
            message="An unexpected error occurred",
            request_id="test-request-id"
        )
        
        assert response.status_code == 500
        content = response.body.decode()
        assert "Internal Server Error" in content
        assert "test-request-id" in content


class TestExceptionHandlers:
    """Test exception handlers"""
    
    def test_http_exception_handler(self, mock_request):
        """Test HTTP exception handler"""
        exc = HTTPException(status_code=404, detail="Not found")
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 404
        content = response.body.decode()
        assert "Not found" in content
        assert "test-request-id" in content
    
    def test_validation_exception_handler(self, mock_request):
        """Test validation exception handler"""
        errors = [
            {"loc": ["field"], "msg": "Field is required", "type": "value_error"}
        ]
        exc = RequestValidationError(errors)
        response = await validation_exception_handler(mock_request, exc)
        
        assert response.status_code == 422
        content = response.body.decode()
        assert "Validation Error" in content
        assert "Request validation failed" in content
        assert "test-request-id" in content
    
    def test_peace_map_error_handler_validation(self, mock_request):
        """Test Peace Map error handler for validation error"""
        exc = ValidationError("Invalid input")
        response = await peace_map_error_handler(mock_request, exc)
        
        assert response.status_code == 400
        content = response.body.decode()
        assert "Validation Error" in content
        assert "Invalid input" in content
        assert "test-request-id" in content
    
    def test_peace_map_error_handler_not_found(self, mock_request):
        """Test Peace Map error handler for not found error"""
        exc = NotFoundError("Resource not found")
        response = await peace_map_error_handler(mock_request, exc)
        
        assert response.status_code == 404
        content = response.body.decode()
        assert "Not Found" in content
        assert "Resource not found" in content
        assert "test-request-id" in content
    
    def test_peace_map_error_handler_conflict(self, mock_request):
        """Test Peace Map error handler for conflict error"""
        exc = ConflictError("Resource conflict")
        response = await peace_map_error_handler(mock_request, exc)
        
        assert response.status_code == 409
        content = response.body.decode()
        assert "Conflict" in content
        assert "Resource conflict" in content
        assert "test-request-id" in content
    
    def test_peace_map_error_handler_rate_limit(self, mock_request):
        """Test Peace Map error handler for rate limit error"""
        exc = RateLimitError("Rate limit exceeded")
        response = await peace_map_error_handler(mock_request, exc)
        
        assert response.status_code == 429
        content = response.body.decode()
        assert "Rate Limit Exceeded" in content
        assert "Rate limit exceeded" in content
        assert "test-request-id" in content
    
    def test_peace_map_error_handler_external_service(self, mock_request):
        """Test Peace Map error handler for external service error"""
        exc = ExternalServiceError("External service error")
        response = await peace_map_error_handler(mock_request, exc)
        
        assert response.status_code == 502
        content = response.body.decode()
        assert "External Service Error" in content
        assert "External service error" in content
        assert "test-request-id" in content
    
    def test_peace_map_error_handler_database(self, mock_request):
        """Test Peace Map error handler for database error"""
        exc = DatabaseError("Database error")
        response = await peace_map_error_handler(mock_request, exc)
        
        assert response.status_code == 500
        content = response.body.decode()
        assert "Database Error" in content
        assert "Database error" in content
        assert "test-request-id" in content
    
    def test_peace_map_error_handler_generic(self, mock_request):
        """Test Peace Map error handler for generic error"""
        exc = PeaceMapError("Generic error")
        response = await peace_map_error_handler(mock_request, exc)
        
        assert response.status_code == 500
        content = response.body.decode()
        assert "Internal Server Error" in content
        assert "Generic error" in content
        assert "test-request-id" in content
    
    def test_general_exception_handler(self, mock_request):
        """Test general exception handler"""
        exc = Exception("Unexpected error")
        response = await general_exception_handler(mock_request, exc)
        
        assert response.status_code == 500
        content = response.body.decode()
        assert "Internal Server Error" in content
        assert "An unexpected error occurred" in content
        assert "test-request-id" in content


class TestErrorHandlerIntegration:
    """Test error handler integration"""
    
    def test_error_handler_setup(self):
        """Test error handler setup"""
        from peace_map.api.errors import setup_error_handlers
        
        # Should not raise any exceptions
        try:
            setup_error_handlers(app)
        except Exception as e:
            pytest.fail(f"setup_error_handlers raised {e}")
    
    def test_error_handler_consistency(self, mock_request):
        """Test error handler response consistency"""
        # Test different error types return consistent format
        error_types = [
            (ValidationError("Test"), 400),
            (NotFoundError("Test"), 404),
            (ConflictError("Test"), 409),
            (RateLimitError("Test"), 429),
            (ExternalServiceError("Test"), 502),
            (DatabaseError("Test"), 500)
        ]
        
        for error, expected_status in error_types:
            response = await peace_map_error_handler(mock_request, error)
            assert response.status_code == expected_status
            
            content = response.body.decode()
            assert "success" in content
            assert "false" in content
            assert "error" in content
            assert "message" in content
            assert "test-request-id" in content
    
    def test_error_handler_logging(self, mock_request):
        """Test error handler logging"""
        with patch('peace_map.api.errors.logger') as mock_logger:
            exc = Exception("Test error")
            response = await general_exception_handler(mock_request, exc)
            
            # Should log the error
            assert mock_logger.error.called
            assert response.status_code == 500
    
    def test_error_handler_performance(self, mock_request):
        """Test error handler performance"""
        import time
        
        start_time = time.time()
        exc = ValidationError("Test error")
        response = await peace_map_error_handler(mock_request, exc)
        end_time = time.time()
        
        # Should handle errors quickly
        assert end_time - start_time < 0.1
        assert response.status_code == 400
