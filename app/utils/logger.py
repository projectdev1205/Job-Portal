import logging
import logging.config
import sys
from app.config import settings


class ColoredFormatter(logging.Formatter):
    """Colored formatter for development console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{level_color}{record.levelname}{self.COLORS['RESET']}"
        
        # Format the message
        formatted = super().format(record)
        return formatted


def setup_logging() -> None:
    """Setup application logging configuration - console only"""
    
    # Determine log level based on environment
    log_level = "DEBUG" if settings.debug else "INFO"
    
    # Base logging configuration - console only
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(levelname)s - %(name)s - %(message)s"
            },
            "colored": {
                "()": ColoredFormatter,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "colored" if settings.debug else "simple",
                "stream": sys.stdout
            }
        },
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy.pool": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console"]
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Log startup message
    logger = logging.getLogger("app")
    logger.info(f"Logging initialized - Environment: {settings.environment}, Debug: {settings.debug}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the app prefix"""
    return logging.getLogger(f"app.{name}")


# Context manager for request logging
class RequestContext:
    """Context manager for request-specific logging"""
    
    def __init__(self, request_id: str, user_id: str = None, endpoint: str = None):
        self.request_id = request_id
        self.user_id = user_id
        self.endpoint = endpoint
        self.logger = get_logger("request")
    
    def __enter__(self):
        # Store the original factory
        self._original_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self._original_factory(*args, **kwargs)
            record.request_id = self.request_id
            if self.user_id:
                record.user_id = self.user_id
            if self.endpoint:
                record.endpoint = self.endpoint
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original factory
        logging.setLogRecordFactory(self._original_factory)
    
    def log_request(self, method: str, path: str, **kwargs):
        """Log incoming request"""
        self.logger.info(
            f"Request started",
            extra={
                "method": method,
                "path": path,
                **kwargs
            }
        )
    
    def log_response(self, status_code: int, duration_ms: float, **kwargs):
        """Log response"""
        self.logger.info(
            f"Request completed",
            extra={
                "status_code": status_code,
                "duration_ms": duration_ms,
                **kwargs
            }
        )
    
    def log_error(self, error: Exception, **kwargs):
        """Log error with context"""
        self.logger.error(
            f"Request failed: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
                **kwargs
            },
            exc_info=True
        )


# Utility functions for common logging patterns
def log_database_operation(operation: str, table: str, record_id: str = None, **kwargs):
    """Log database operations"""
    logger = get_logger("database")
    logger.info(
        f"Database operation: {operation}",
        extra={
            "operation": operation,
            "table": table,
            "record_id": record_id,
            **kwargs
        }
    )


def log_business_operation(operation: str, user_id: str = None, **kwargs):
    """Log business logic operations"""
    logger = get_logger("business")
    logger.info(
        f"Business operation: {operation}",
        extra={
            "operation": operation,
            "user_id": user_id,
            **kwargs
        }
    )


def log_security_event(event: str, user_id: str = None, ip_address: str = None, **kwargs):
    """Log security-related events"""
    logger = get_logger("security")
    logger.warning(
        f"Security event: {event}",
        extra={
            "event": event,
            "user_id": user_id,
            "ip_address": ip_address,
            **kwargs
        }
    )


def log_performance(operation: str, duration_ms: float, **kwargs):
    """Log performance metrics"""
    logger = get_logger("performance")
    logger.info(
        f"Performance: {operation}",
        extra={
            "operation": operation,
            "duration_ms": duration_ms,
            **kwargs
        }
    )
