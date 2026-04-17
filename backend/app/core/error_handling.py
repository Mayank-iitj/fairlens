"""
Production-Ready Error Handling and Logging System.
Centralized error management with structured logging and error codes.
"""
import logging
import logging.config
import json
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCode(str, Enum):
    """Standardized error codes."""
    # Validation errors (400-level)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    
    # Authentication errors (401-level)
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    
    # Permission errors (403-level)
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Not found errors (404-level)
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    AUDIT_NOT_FOUND = "AUDIT_NOT_FOUND"
    
    # Conflict errors (409-level)
    CONFLICT = "CONFLICT"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    
    # Processing errors (422-level)
    PROCESSING_FAILED = "PROCESSING_FAILED"
    DATA_PIPELINE_ERROR = "DATA_PIPELINE_ERROR"
    FAIRNESS_COMPUTATION_ERROR = "FAIRNESS_COMPUTATION_ERROR"
    REPORT_GENERATION_ERROR = "REPORT_GENERATION_ERROR"
    
    # Server errors (500-level)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    
    # Unknown error
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class APIError(Exception):
    """Base class for API errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode,
        status_code: int,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize API error."""
        self.message = message
        self.code = code
        self.status_code = status_code
        self.severity = severity
        self.details = details or {}
        self.original_error = original_error
        self.timestamp = datetime.utcnow().isoformat()
        
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "status": self.status_code,
                "severity": self.severity.value,
                "timestamp": self.timestamp,
                "details": self.details
            }
        }


def setup_logging():
    """Configure structured logging for production."""
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s"
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": "%(timestamp)s %(level)s %(name)s %(message)s"
            }
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout"
            },
            "detailed": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "detailed",
                "stream": "ext://sys.stderr"
            },
            "file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "detailed",
                "filename": "logs/fairlens.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10
            }
        },
        "loggers": {
            "": {
                "level": "INFO",
                "handlers": ["default", "file"]
            },
            "app": {
                "level": "DEBUG",
                "handlers": ["default", "file"],
                "propagate": False
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["detailed"]
            }
        }
    }
    
    try:
        # Create logs directory
        import os
        os.makedirs("logs", exist_ok=True)
    except Exception:
        pass
    
    logging.config.dictConfig(logging_config)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling across all routes."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and handle errors."""
        try:
            response = await call_next(request)
            return response
        except APIError as e:
            logger = logging.getLogger(__name__)
            logger.error(
                f"API Error: {e.code} - {e.message}",
                extra={
                    "code": e.code.value,
                    "status": e.status_code,
                    "severity": e.severity.value,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            return JSONResponse(
                status_code=e.status_code,
                content=e.to_dict()
            )
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": "HTTP_ERROR",
                        "message": e.detail,
                        "status": e.status_code
                    }
                }
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception(
                "Unhandled exception",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": type(e).__name__
                }
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": ErrorCode.INTERNAL_ERROR.value,
                        "message": "Internal server error",
                        "status": 500,
                        "severity": ErrorSeverity.CRITICAL.value,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )


class ErrorLogger:
    """Centralized error logging utility."""
    
    def __init__(self, name: str):
        """Initialize error logger."""
        self.logger = logging.getLogger(name)
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        level: str = "error"
    ):
        """
        Log an error with context.
        
        Args:
            error: The exception
            context: Additional context information
            level: Logging level (debug, info, warning, error, critical)
        """
        log_func = getattr(self.logger, level)
        
        extra = {
            "error_type": type(error).__name__,
            "traceback": traceback.format_exc()
        }
        
        if context:
            extra.update(context)
        
        log_func(str(error), extra=extra)
    
    def log_api_error(
        self,
        error: APIError,
        request_context: Optional[Dict[str, Any]] = None
    ):
        """Log an API error."""
        context = {
            "code": error.code.value,
            "message": error.message,
            "severity": error.severity.value,
            "details": error.details
        }
        
        if request_context:
            context.update(request_context)
        
        level = "warning" if error.severity == ErrorSeverity.LOW else "error"
        self.log_error(error, context, level)


def add_error_handlers(app: FastAPI):
    """Register all error handlers with FastAPI app."""
    
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        logger = logging.getLogger(__name__)
        logger.error(
            f"API Error {exc.code}: {exc.message}",
            extra={
                "code": exc.code.value,
                "status": exc.status_code,
                "severity": exc.severity.value
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "status": exc.status_code,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger = logging.getLogger(__name__)
        logger.exception(
            "Unhandled exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "Internal server error. Support has been notified.",
                    "status": 500,
                    "severity": ErrorSeverity.CRITICAL.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )


# Export logging setup function
__all__ = [
    "setup_logging",
    "ErrorHandlingMiddleware",
    "ErrorLogger",
    "APIError",
    "ErrorCode",
    "ErrorSeverity",
    "add_error_handlers"
]
