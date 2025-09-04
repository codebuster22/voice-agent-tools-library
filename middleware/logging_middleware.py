"""
FastAPI middleware for request/response logging with correlation tracking.
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from logging_config import logger, set_request_id, clear_request_context


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses with correlation."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        # Paths to exclude from logging (e.g., health checks)
        self.exclude_paths = exclude_paths or ["/docs", "/openapi.json", "/redoc"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging and correlation."""
        
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Set request ID and start timing
        request_id = set_request_id()
        start_time = time.time()
        
        # Read request body for logging (if present)
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_body = json.loads(body) if body else None
            except (json.JSONDecodeError, UnicodeDecodeError):
                request_body = "<binary_or_invalid_json>"
            except Exception:
                request_body = "<error_reading_body>"
        
        # Log incoming request
        logger.info(
            "Incoming request",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params) if request.query_params else None,
            user_agent=request.headers.get("user-agent"),
            content_type=request.headers.get("content-type")
        )
        
        # Debug level: include request body
        if request_body is not None:
            logger.info(
                "Request body received",
                body=request_body,
                body_size=len(str(request_body)) if request_body else 0
            )
        
        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                response_size=response.headers.get("content-length")
            )
            
            # Clear context after request
            clear_request_context()
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                "Request failed with exception",
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration_ms, 2)
            )
            
            # Clear context after request
            clear_request_context()
            raise