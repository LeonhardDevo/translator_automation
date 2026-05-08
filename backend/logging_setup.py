"""
Centralized logging setup for AI Translation Service
Creates comprehensive logs of all backend operations in the logs directory
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from pythonjsonlogger import jsonlogger
import os

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.fromtimestamp(record.created).isoformat()
        if log_record.get('level'):
            log_record['level'] = record.levelname
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

def setup_comprehensive_logging():
    """Setup comprehensive logging to capture all backend operations in the logs directory"""
    
    # Create a general log file for all operations (one per day)
    general_log_file = LOGS_DIR / f"backend_operations_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create file handler for comprehensive logging (append mode to add to existing daily file)
    file_handler = logging.FileHandler(general_log_file, mode='a', encoding='utf-8')
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Create console handler for real-time monitoring
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Also create a specific logger for the application
    app_logger = logging.getLogger("ai_translation_service")
    
    # Create structured log file for detailed operations (one per day)
    structured_log_file = LOGS_DIR / f"structured_backend_log_{datetime.now().strftime('%Y%m%d')}.json"
    
    # Check if structured handler already exists to prevent duplicates
    existing_handlers = [h for h in app_logger.handlers if isinstance(h, logging.FileHandler)]
    for handler in existing_handlers:
        app_logger.removeHandler(handler)
    
    # Create structured log handler in append mode
    structured_handler = logging.FileHandler(structured_log_file, mode='a', encoding='utf-8')
    structured_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s %(correlation_id)s %(user_id)s %(request_id)s'
    )
    structured_handler.setFormatter(structured_formatter)
    app_logger.addHandler(structured_handler)
    
    # Store log file paths in environment for reference
    os.environ['CURRENT_BACKEND_LOG'] = str(general_log_file)
    os.environ['CURRENT_STRUCTURED_LOG'] = str(structured_log_file)
    
    app_logger.info("Comprehensive logging initialized", extra={
        'log_file': str(general_log_file),
        'structured_log_file': str(structured_log_file)
    })
    
    return app_logger
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create file handler for comprehensive logging
    file_handler = logging.FileHandler(general_log_file, encoding='utf-8')
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Create console handler for real-time monitoring
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Also create a specific logger for the application
    app_logger = logging.getLogger("ai_translation_service")
    
    # Create structured log file for detailed operations
    structured_log_file = LOGS_DIR / f"structured_backend_log_{datetime.now().strftime('%Y%m%d')}.json"
    structured_handler = logging.FileHandler(structured_log_file, encoding='utf-8')
    structured_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s %(correlation_id)s %(user_id)s %(request_id)s'
    )
    structured_handler.setFormatter(structured_formatter)
    app_logger.addHandler(structured_handler)
    
    # Store log file paths in environment for reference
    os.environ['CURRENT_BACKEND_LOG'] = str(general_log_file)
    os.environ['CURRENT_STRUCTURED_LOG'] = str(structured_log_file)
    
    app_logger.info("Comprehensive logging initialized", extra={
        'log_file': str(general_log_file),
        'structured_log_file': str(structured_log_file)
    })
    
    return app_logger

def get_logger(name: str = "ai_translation_service"):
    """Get a configured logger instance"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        # If no handlers are configured, set up basic logging to avoid "No handlers" warning
        handler = logging.NullHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger