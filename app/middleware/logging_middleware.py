import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import get_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""
    
    def __init__(self, app, skip_paths: list = None):
        super().__init__(app)
        self.logger = get_logger("middleware")
        self.skip_paths = skip_paths or ["/health", "/docs", "/openapi.json", "/favicon.ico"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        
        # Add request ID to request state for use in handlers
        request.state.request_id = request_id
        
        # Log request start
        self.logger.info(
            f"Request started: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query_params": query_params,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "user_id": user_id
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            self.logger.info(
                f"Request completed: {method} {path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "response_size": response.headers.get("content-length"),
                    "user_id": user_id
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration even for errors
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            self.logger.error(
                f"Request failed: {method} {path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "duration_ms": duration_ms,
                    "user_id": user_id
                },
                exc_info=True
            )
            
            # Re-raise the exception
            raise


class DatabaseLoggingMiddleware:
    """Middleware for logging database operations"""
    
    def __init__(self):
        self.logger = get_logger("database")
    
    def log_query(self, query: str, params: dict = None, duration_ms: float = None):
        """Log SQL query execution"""
        self.logger.debug(
            "SQL Query executed",
            extra={
                "query": query,
                "params": params,
                "duration_ms": duration_ms
            }
        )
    
    def log_connection(self, operation: str, **kwargs):
        """Log database connection events"""
        self.logger.info(
            f"Database connection: {operation}",
            extra={
                "operation": operation,
                **kwargs
            }
        )


class SecurityLoggingMiddleware:
    """Middleware for logging security events"""
    
    def __init__(self):
        self.logger = get_logger("security")
    
    def log_authentication_attempt(self, email: str, success: bool, ip_address: str = None):
        """Log authentication attempts"""
        level = "info" if success else "warning"
        getattr(self.logger, level)(
            f"Authentication attempt: {'success' if success else 'failed'}",
            extra={
                "email": email,
                "success": success,
                "ip_address": ip_address,
                "event_type": "authentication"
            }
        )
    
    def log_authorization_failure(self, user_id: str, resource: str, action: str, ip_address: str = None):
        """Log authorization failures"""
        self.logger.warning(
            "Authorization failure",
            extra={
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "ip_address": ip_address,
                "event_type": "authorization_failure"
            }
        )
    
    def log_suspicious_activity(self, activity: str, ip_address: str = None, user_id: str = None):
        """Log suspicious activities"""
        self.logger.warning(
            f"Suspicious activity: {activity}",
            extra={
                "activity": activity,
                "ip_address": ip_address,
                "user_id": user_id,
                "event_type": "suspicious_activity"
            }
        )
