import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from pythonjsonlogger import jsonlogger

APP_LOGGER_NAME = "ai_translation_service"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOGS_DIR = PROJECT_ROOT / "logs"

_LOGGING_CONFIGURED = False

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.fromtimestamp(record.created).isoformat()
        if log_record.get('level'):
            log_record['level'] = record.levelname
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

def _resolve_logs_dir(logs_dir: Optional[Path] = None) -> Path:
    configured_dir = logs_dir or os.getenv("BACKEND_LOG_DIR") or DEFAULT_LOGS_DIR
    resolved_dir = Path(configured_dir).expanduser()

    if not resolved_dir.is_absolute():
        resolved_dir = PROJECT_ROOT / resolved_dir

    return resolved_dir.resolve()


def _mark_managed(handler: logging.Handler) -> logging.Handler:
    setattr(handler, "_ai_translation_managed", True)
    return handler


def _remove_managed_handlers(logger: logging.Logger) -> None:
    for handler in logger.handlers[:]:
        if getattr(handler, "_ai_translation_managed", False):
            logger.removeHandler(handler)
            handler.close()


def _create_file_handler(log_file: Path, formatter: logging.Formatter) -> Optional[logging.Handler]:
    try:
        handler = _mark_managed(
            logging.FileHandler(log_file, mode='a', encoding='utf-8')
        )
    except OSError as exc:
        logging.getLogger(APP_LOGGER_NAME).warning(
            "File logging disabled for %s: %s", log_file, exc
        )
        return None

    handler.setFormatter(formatter)
    return handler


def setup_comprehensive_logging(logs_dir: Optional[Path] = None) -> logging.Logger:
    """Configure backend logging once, writing all files to the central logs directory."""
    global _LOGGING_CONFIGURED

    app_logger = logging.getLogger(APP_LOGGER_NAME)
    if _LOGGING_CONFIGURED:
        return app_logger

    resolved_logs_dir = _resolve_logs_dir(logs_dir)
    resolved_logs_dir.mkdir(parents=True, exist_ok=True)

    date_suffix = datetime.now().strftime('%Y%m%d')
    general_log_file = resolved_logs_dir / f"backend_operations_{date_suffix}.log"
    structured_log_file = resolved_logs_dir / f"structured_backend_log_{date_suffix}.json"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    _remove_managed_handlers(root_logger)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = True

    text_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    console_handler = _mark_managed(logging.StreamHandler(sys.stdout))
    console_handler.setFormatter(text_formatter)
    root_logger.addHandler(console_handler)

    file_handler = _create_file_handler(general_log_file, text_formatter)
    if file_handler:
        root_logger.addHandler(file_handler)
        os.environ['CURRENT_BACKEND_LOG'] = str(general_log_file)

    structured_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s %(correlation_id)s %(user_id)s %(request_id)s'
    )
    structured_handler = _create_file_handler(structured_log_file, structured_formatter)
    if structured_handler:
        root_logger.addHandler(structured_handler)
        os.environ['CURRENT_STRUCTURED_LOG'] = str(structured_log_file)

    _LOGGING_CONFIGURED = True
    app_logger.info("Comprehensive logging initialized", extra={
        'log_file': os.environ.get('CURRENT_BACKEND_LOG'),
        'structured_log_file': os.environ.get('CURRENT_STRUCTURED_LOG')
    })

    return app_logger

def get_logger(name: str = "ai_translation_service"):
    """Get a configured logger instance"""
    return logging.getLogger(name)
