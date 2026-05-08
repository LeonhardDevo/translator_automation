from backend.logging_setup import get_logger
from datetime import datetime
import traceback
import sys
from typing import Optional

def log_operation(operation: str, details: dict = None, level: str = "info", user_id: Optional[int] = None):
    """
    Log a backend operation with comprehensive details
    
    Args:
        operation: Name/type of operation being performed
        details: Dictionary containing operation-specific details
        level: Logging level ('debug', 'info', 'warning', 'error', 'critical')
        user_id: Optional user ID associated with the operation
    """
    logger = get_logger(__name__)
    
    log_data = {
        "operation": operation,
        "timestamp": datetime.now().isoformat(),
        "details": details or {},
        "user_id": user_id
    }
    
    if level.lower() == "debug":
        logger.debug(f"Operation: {operation}", extra=log_data)
    elif level.lower() == "warning":
        logger.warning(f"Operation: {operation}", extra=log_data)
    elif level.lower() == "error":
        logger.error(f"Operation: {operation}", extra=log_data)
    elif level.lower() == "critical":
        logger.critical(f"Operation: {operation}", extra=log_data)
    else:  
        logger.info(f"Operation: {operation}", extra=log_data)


def log_api_call(endpoint: str, method: str, user_id: Optional[int] = None, 
                request_data: dict = None, response_status: int = None):
    """
    Log API calls for monitoring and audit purposes
    """
    details = {
        "endpoint": endpoint,
        "method": method,
        "request_data": request_data,
        "response_status": response_status
    }
    
    log_operation("api_call", details, "info", user_id)


def log_database_operation(operation: str, table: str, record_id: Optional[int] = None, 
    user_id: Optional[int] = None, success: bool = True, error: str = None):
    """
    Log database operations
    """
    details = {
        "table": table,
        "record_id": record_id,
        "operation": operation,
        "success": success,
        "error": error
    }
    
    log_operation("database_op", details, "info" if success else "error", user_id)


def log_translation_process(document_id: int, user_id: int, input_file: str, 
    target_language: str, status: str, error: str = None):
    """
    Log translation process steps
    """
    details = {
        "document_id": document_id,
        "input_file": input_file,
        "target_language": target_language,
        "status": status,
        "error": error
    }
    
    log_operation("translation_process", details, "info" if status != "failed" else "error", user_id)


def log_error(operation: str, error: Exception, user_id: Optional[int] = None, 
             additional_context: dict = None):
    """
    Log an error with full traceback
    """
    details = {
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "additional_context": additional_context or {}
    }
    
    log_operation("error", details, "error", user_id)


def log_security_event(event_type: str, user_id: Optional[int] = None, ip_address: str = None, 
    details: dict = None):
    """
    Log security-related events
    """
    log_details = {
        "event_type": event_type,
        "ip_address": ip_address,
        "details": details or {}
    }
    
    log_operation("security_event", log_details, "warning", user_id)