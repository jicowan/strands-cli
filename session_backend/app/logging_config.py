"""Logging configuration with structured logging support."""

import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from .config import get_settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info'):
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Custom text formatter for human-readable logging."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def setup_logging(settings: Optional[Any] = None) -> None:
    """Set up logging configuration based on settings."""
    if settings is None:
        settings = get_settings()
    
    # Determine formatter based on log format setting
    if settings.log_format.lower() == 'json':
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    configure_logger_levels()
    
    logging.info("Logging configured with level=%s, format=%s", 
                settings.log_level, settings.log_format)


def configure_logger_levels() -> None:
    """Configure specific logger levels to reduce noise."""
    # Reduce noise from third-party libraries
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('asyncpg').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def log_request_response(request_id: str, method: str, path: str, 
                        status_code: int, duration_ms: float) -> None:
    """Log HTTP request/response information."""
    logger = get_logger('session_backend.api')
    logger.info(
        "HTTP request completed",
        extra={
            'request_id': request_id,
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'event_type': 'http_request'
        }
    )


def log_database_operation(operation: str, table: str, duration_ms: float, 
                          success: bool, error: Optional[str] = None) -> None:
    """Log database operation information."""
    logger = get_logger('session_backend.database')
    
    log_data = {
        'operation': operation,
        'table': table,
        'duration_ms': duration_ms,
        'success': success,
        'event_type': 'database_operation'
    }
    
    if error:
        log_data['error'] = error
        logger.error("Database operation failed", extra=log_data)
    else:
        logger.info("Database operation completed", extra=log_data)


def log_configuration_event(event: str, details: Dict[str, Any]) -> None:
    """Log configuration-related events."""
    logger = get_logger('session_backend.config')
    logger.info(
        f"Configuration event: {event}",
        extra={
            'event_type': 'configuration',
            'event': event,
            **details
        }
    )