"""
Logging configuration for automotive voice agent API.
Provides structured logging with request correlation and service call tracking.
"""

import os
import sys
import json
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional
from datetime import datetime
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars


# Context variable for request correlation
request_id_ctx: ContextVar[str] = ContextVar('request_id', default='')


def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_ctx.get('')


def set_request_id(request_id: str = None) -> str:
    """Set request ID in context. Generates UUID if not provided."""
    if not request_id:
        request_id = str(uuid.uuid4())[:8]
    request_id_ctx.set(request_id)
    bind_contextvars(request_id=request_id)
    return request_id


def clear_request_context():
    """Clear request context variables."""
    clear_contextvars()


class JSONProcessor:
    """Custom JSON processor for structured logging."""
    
    def __call__(self, logger, method_name, event_dict):
        """Process log entry into JSON format."""
        # Extract standard fields
        timestamp = datetime.utcnow().isoformat() + 'Z'
        level = event_dict.pop('level', 'info').upper()
        event = event_dict.pop('event', '')
        request_id = event_dict.pop('request_id', get_request_id())
        
        # Build log entry
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'event': event,
            'request_id': request_id,
        }
        
        # Add remaining fields
        if event_dict:
            log_entry.update(event_dict)
        
        return json.dumps(log_entry, separators=(',', ':'))


class HumanProcessor:
    """Human-readable processor for development."""
    
    def __call__(self, logger, method_name, event_dict):
        """Process log entry into human-readable format."""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        level = event_dict.pop('level', 'info').upper()
        event = event_dict.pop('event', '')
        request_id = event_dict.pop('request_id', get_request_id())
        
        # Format base message
        message = f"[{timestamp}] {level:5} [{request_id}] {event}"
        
        # Add context if present
        if event_dict:
            context_items = []
            for key, value in event_dict.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                context_items.append(f"{key}={value}")
            
            if context_items:
                message += " | " + " ".join(context_items)
        
        return message


def configure_logging():
    """Configure structured logging for the application."""
    
    # Determine if we're in development or production
    environment = os.getenv('ENVIRONMENT', 'development')
    log_level = os.getenv('LOG_LEVEL', 'DEBUG').upper()
    
    # Configure processors based on environment
    if environment == 'production':
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            JSONProcessor(),
        ]
    else:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            HumanProcessor(),
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logger
    import logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level, logging.DEBUG),
    )


# Create logger instance
logger = structlog.get_logger("automotive_api")


# Service logging helpers
class ServiceLogger:
    """Helper class for consistent service logging."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = structlog.get_logger("automotive_api")
    
    def log_call(self, operation: str, params: Optional[Dict[str, Any]] = None, level: str = "info"):
        """Log service call start."""
        log_data = {
            "service": self.service_name,
            "operation": operation,
            "status": "calling"
        }
        if params and level.lower() == "debug":
            log_data["params"] = params
            
        getattr(self.logger, level.lower())(
            f"Calling {self.service_name} - {operation}",
            **log_data
        )
    
    def log_response(self, operation: str, success: bool = True, 
                    response: Optional[Any] = None, error: Optional[str] = None,
                    duration_ms: Optional[float] = None, level: str = "info"):
        """Log service call response."""
        log_data = {
            "service": self.service_name,
            "operation": operation,
            "status": "success" if success else "error"
        }
        
        if duration_ms is not None:
            log_data["duration_ms"] = round(duration_ms, 2)
        
        if not success and error:
            log_data["error"] = error
            
        if success and response is not None and level.lower() == "debug":
            # Truncate large responses for logging
            if isinstance(response, (dict, list)):
                response_str = json.dumps(response)
                if len(response_str) > 1000:
                    log_data["response_size"] = len(response_str)
                    log_data["response_preview"] = response_str[:200] + "..."
                else:
                    log_data["response"] = response
            else:
                log_data["response"] = str(response)[:500]
        
        message = f"{self.service_name} - {operation} {'completed' if success else 'failed'}"
        if duration_ms:
            message += f" ({duration_ms:.2f}ms)"
            
        getattr(self.logger, level.lower())(message, **log_data)


# Pre-configured service loggers
google_calendar_logger = ServiceLogger("google_calendar")
railway_api_logger = ServiceLogger("railway_api")
database_logger = ServiceLogger("database")
github_api_logger = ServiceLogger("github_api")