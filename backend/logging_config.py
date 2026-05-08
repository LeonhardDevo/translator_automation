"""
Logging configuration for AI Translation Service with structured logging and correlation IDs
"""
import logging
import json
import sys
from pythonjsonlogger import jsonlogger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid
import time
from fastapi import HTTPException

# Configure structured logging
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            log_record['timestamp'] = record.created
        if log_record.get('level'):
            log_record['level'] = record.levelname
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

def setup_logging():
    """Setup structured logging with correlation IDs"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Create custom formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s %(correlation_id)s %(user_id)s %(request_id)s'
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Commenting out Correlation ID middleware to avoid context manager conflicts
# class CorrelationIdMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         # Generate or extract correlation ID
#         correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
#
#         # Add correlation ID to request state
#         request.state.correlation_id = correlation_id
#
#         try:
#             # Add to response headers
#             response = await call_next(request)
#         except Exception as e:
#             # If there's an exception during processing, return the error response
#             raise e
#
#         response.headers['X-Correlation-ID'] = correlation_id
#
#         return response

# Logging utility functions
def get_logger(name: str):
    """Get a logger with correlation ID support"""
    logger = logging.getLogger(name)
    return logger

def log_request_start(request: Request, logger):
    """Log the start of a request"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    logger.info(
        "Request started",
        extra={
            'correlation_id': correlation_id,
            'method': request.method,
            'url': str(request.url),
            'headers': dict(request.headers),
            'start_time': time.time()
        }
    )

def log_request_end(request: Request, response, logger, start_time: float):
    """Log the end of a request"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    logger.info(
        "Request completed",
        extra={
            'correlation_id': correlation_id,
            'method': request.method,
            'url': str(request.url),
            'status_code': response.status_code,
            'duration': time.time() - start_time,
            'end_time': time.time()
        }
    )

def log_translation_event(logger, correlation_id: str, user_id: str, event_type: str, details: dict = None):
    """Log translation-related events"""
    logger.info(
        f"Translation {event_type}",
        extra={
            'correlation_id': correlation_id,
            'user_id': user_id,
            'event_type': event_type,
            'details': details or {}
        }
    )

def log_security_event(logger, correlation_id: str, user_id: str, event_type: str, severity: str, details: dict = None):
    """Log security-related events"""
    logger.warning(
        f"Security event: {event_type}",
        extra={
            'correlation_id': correlation_id,
            'user_id': user_id,
            'event_type': event_type,
            'severity': severity,
            'details': details or {}
        }
    )