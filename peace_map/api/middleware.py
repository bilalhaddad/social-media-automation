"""
Middleware for Peace Map API
"""

import time
import logging
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import uuid

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging middleware for request/response logging"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        logger.info(f"Request {request_id}: {request.method} {request.url}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(f"Response {request_id}: {response.status_code} in {process_time:.3f}s")
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(f"Error {request_id}: {str(e)} in {process_time:.3f}s")
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Internal server error",
                    "request_id": request_id,
                    "message": "An unexpected error occurred"
                },
                headers={"X-Request-ID": request_id}
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Clean old entries
        current_time = time.time()
        self.requests = {
            ip: timestamps for ip, timestamps in self.requests.items()
            if any(ts > current_time - 60 for ts in timestamps)
        }
        
        # Check rate limit
        if client_ip in self.requests:
            # Remove timestamps older than 1 minute
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip] 
                if ts > current_time - 60
            ]
            
            if len(self.requests[client_ip]) >= self.calls_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {self.calls_per_minute} per minute"
                    }
                )
        
        # Add current request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for headers and validation"""
    
    async def dispatch(self, request: Request, call_next):
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class ValidationMiddleware(BaseHTTPMiddleware):
    """Request validation middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            return JSONResponse(
                status_code=413,
                content={
                    "success": False,
                    "error": "Request too large",
                    "message": "Request body exceeds 10MB limit"
                }
            )
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith(("application/json", "multipart/form-data", "text/csv")):
                return JSONResponse(
                    status_code=415,
                    content={
                        "success": False,
                        "error": "Unsupported media type",
                        "message": "Content-Type must be application/json, multipart/form-data, or text/csv"
                    }
                )
        
        # Process request
        response = await call_next(request)
        return response


def setup_middleware(app):
    """Setup all middleware for the application"""
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware, calls_per_minute=60)
    
    # Add security middleware
    app.add_middleware(SecurityMiddleware)
    
    # Add validation middleware
    app.add_middleware(ValidationMiddleware)
    
    logger.info("Middleware setup completed")
