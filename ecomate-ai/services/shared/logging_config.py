"""Centralized logging configuration for EcoMate AI services.

Provides structured logging with JSON format, configurable levels,
and integration with monitoring systems.
"""

import logging
import logging.config
import json
import os
from typing import Dict, Any
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process': record.process,
            'thread': record.thread
        }
        
        # Add extra fields if present
        extra_fields = [
            'request_id', 'user_id', 'duration', 'status_code',
            'error_id', 'error_type', 'client_ip', 'method', 'url',
            'model_type', 'api_type', 'workflow_id', 'task_id'
        ]
        
        for field in extra_fields:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class HealthCheckFilter(logging.Filter):
    """Filter to reduce noise from health check endpoints."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out health check requests unless they're errors."""
        if hasattr(record, 'url') and '/health' in record.url:
            return record.levelno >= logging.WARNING
        return True


def get_logging_config(log_level: str = None, enable_health_filter: bool = True) -> Dict[str, Any]:
    """Get logging configuration dictionary.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_health_filter: Whether to filter health check logs
    
    Returns:
        Logging configuration dictionary
    """
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'structured': {
                '()': StructuredFormatter,
            },
            'simple': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'filters': {
            'health_check': {
                '()': HealthCheckFilter,
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'structured',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': log_level,
                'formatter': 'structured',
                'filename': 'logs/ecomate.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'structured',
                'filename': 'logs/ecomate_errors.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            'ecomate': {
                'level': log_level,
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console']
        }
    }
    
    # Add health check filter if enabled
    if enable_health_filter:
        config['handlers']['console']['filters'] = ['health_check']
        config['handlers']['file']['filters'] = ['health_check']
    
    return config


def setup_logging(log_level: str = None, enable_health_filter: bool = True) -> None:
    """Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_health_filter: Whether to filter health check logs
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Apply logging configuration
    config = get_logging_config(log_level, enable_health_filter)
    logging.config.dictConfig(config)
    
    # Set up root logger
    logger = logging.getLogger('ecomate')
    logger.info('Logging configuration initialized', extra={
        'log_level': log_level or os.getenv('LOG_LEVEL', 'INFO'),
        'health_filter_enabled': enable_health_filter
    })


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f'ecomate.{name}')