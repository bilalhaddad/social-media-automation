"""
Error handling for Peace Map API
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


class PeaceMapError(Exception):
    """Base exception for Peace Map API"""
    pass


class ValidationError(PeaceMapError):
    """Validation error"""
    pass


class NotFoundError(PeaceMapError):
    """Resource not found error"""
    pass


class ConflictError(PeaceMapError):
    """Resource conflict error"""
    pass


class RateLimitError(PeaceMapError):
    """Rate limit exceeded error"""
    pass


class ExternalServiceError(PeaceMapError):
    """External service error"""
    pass


class DatabaseError(PeaceMapError):
    """Database error"""
    pass


def create_error_response(
    status_code: int,
    error: str,
    message: str,
    details: dict = None,
    request_id: str = None
) -> JSONResponse:
    """Create standardized error response"""
    
    content = {
        "success": False,
        "error": error,
        "message": message
    }
    
    if details:
        content["details"] = details
    
    if request_id:
        content["request_id"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    
    request_id = getattr(request.state, 'request_id', None)
    
    return create_error_response(
        status_code=exc.status_code, exc.detail, exc.detail, request_id=request_id
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions"""
    
    request_id = getattr(request.state, 'request_id', None)
    
    return create_error_response(
        status_code=422,
        error="Validation Error",
        message="Request validation failed",
        details=exc.errors(),
        request_id=request_id
    )


async def peace_map_error_handler(request: Request, exc: PeaceMapError):
    """Handle Peace Map specific errors"""
    
    request_id = getattr(request.state, 'request_id', None)
    
    if isinstance(exc, ValidationError):
        return create_error_response(
            status_code=400,
            error="Validation Error",
            message=str(exc),
            request_id=request_id
        )
    elif isinstance(exc, NotFoundError):
        return create_error_response(
            status_code=404,
            error="Not Found",
            message=str(exc),
            request_id=request_id
        )
    elif isinstance(exc, ConflictError):
        return create_error_response(
            status_code=409,
            error="Conflict",
            message=str(exc),
            request_id=request_id
        )
    elif isinstance(exc, RateLimitError):
        return create_error_response(
            status_code=429,
            error="Rate Limit Exceeded",
            message=str(exc),
            request_id=request_id
        )
    elif isinstance(exc, ExternalServiceError):
        return create_error_response(
            status_code=502,
            error="External Service Error",
            message=str(exc),
            request_id=request_id
        )
    elif isinstance(exc, DatabaseError):
        return create_error_response(
            status_code=500,
            error="Database Error",
            message=str(exc),
            request_id=request_id
        )
    else:
        return create_error_response(
            status_code=500,
            error="Internal Server Error",
            message=str(exc),
            request_id=request_id
        )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    
    request_id = getattr(request.state, 'request_id', None)
    
    # Log the error
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return create_error_response(
        status_code=500,
        error="Internal Server Error",
        message="An unexpected error occurred",
        request_id=request_id
    )


def setup_error_handlers(app):
    """Setup error handlers for the application"""
    
    # Add exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PeaceMapError, peace_map_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Error handlers setup completed")
