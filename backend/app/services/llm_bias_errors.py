"""
Error handling and validation utilities for LLM bias detection.
Production-ready error handling with proper logging and recovery.
"""
import logging
from enum import Enum
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BiasDetectionErrorCode(Enum):
    """Error codes for bias detection operations."""
    INVALID_INPUT = "INVALID_INPUT"
    TEXT_TOO_SHORT = "TEXT_TOO_SHORT"
    TEXT_TOO_LONG = "TEXT_TOO_LONG"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    DATABASE_ERROR = "DATABASE_ERROR"
    INVALID_ANALYSIS_ID = "INVALID_ANALYSIS_ID"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    UNAUTHORIZED = "UNAUTHORIZED"


class BiasDetectionError(Exception):
    """Base exception for bias detection errors."""
    
    def __init__(
        self,
        error_code: BiasDetectionErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
        }


class InputValidationError(BiasDetectionError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=BiasDetectionErrorCode.INVALID_INPUT,
            message=message,
            details=details,
            status_code=400,
        )


class TextLengthError(BiasDetectionError):
    """Raised when text length is out of bounds."""
    
    def __init__(self, length: int, min_length: int = 10, max_length: int = 10000):
        if length < min_length:
            error_code = BiasDetectionErrorCode.TEXT_TOO_SHORT
            message = f"Text is too short. Minimum {min_length} characters required, got {length}."
        else:
            error_code = BiasDetectionErrorCode.TEXT_TOO_LONG
            message = f"Text is too long. Maximum {max_length} characters allowed, got {length}."
        
        super().__init__(
            error_code=error_code,
            message=message,
            details={"length": length, "min_length": min_length, "max_length": max_length},
            status_code=400,
        )


class AnalysisFailedError(BiasDetectionError):
    """Raised when analysis fails."""
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=BiasDetectionErrorCode.ANALYSIS_FAILED,
            message=f"LLM bias analysis failed: {reason}",
            details=details,
            status_code=500,
        )


class DatabaseError(BiasDetectionError):
    """Raised when database operations fail."""
    
    def __init__(self, operation: str, reason: str):
        super().__init__(
            error_code=BiasDetectionErrorCode.DATABASE_ERROR,
            message=f"Database error during {operation}: {reason}",
            details={"operation": operation},
            status_code=500,
        )


class RateLimitError(BiasDetectionError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            error_code=BiasDetectionErrorCode.RATE_LIMIT_EXCEEDED,
            message="Rate limit exceeded. Please try again later.",
            details={"retry_after": retry_after},
            status_code=429,
        )


class TextValidator:
    """Validates text input for bias detection."""
    
    MIN_LENGTH = 10
    MAX_LENGTH = 10000
    
    @staticmethod
    def validate(text: str) -> None:
        """
        Validate text input.
        
        Args:
            text: Text to validate
            
        Raises:
            InputValidationError: If text is invalid
            TextLengthError: If text length is out of bounds
        """
        if not isinstance(text, str):
            raise InputValidationError(
                "Input must be a string",
                details={"type": type(text).__name__}
            )
        
        if not text or not text.strip():
            raise InputValidationError(
                "Input text cannot be empty",
                details={"length": 0}
            )
        
        text_length = len(text)
        if text_length < TextValidator.MIN_LENGTH or text_length > TextValidator.MAX_LENGTH:
            raise TextLengthError(
                text_length,
                TextValidator.MIN_LENGTH,
                TextValidator.MAX_LENGTH
            )
        
        logger.debug(f"Text validation passed: {text_length} characters")


class BatchAnalysisValidator:
    """Validates batch analysis requests."""
    
    MIN_ITEMS = 1
    MAX_ITEMS = 100
    
    @staticmethod
    def validate(texts: list) -> None:
        """
        Validate batch of texts.
        
        Args:
            texts: List of texts to validate
            
        Raises:
            InputValidationError: If batch is invalid
        """
        if not isinstance(texts, list):
            raise InputValidationError(
                "Texts must be a list",
                details={"type": type(texts).__name__}
            )
        
        count = len(texts)
        if count < BatchAnalysisValidator.MIN_ITEMS or count > BatchAnalysisValidator.MAX_ITEMS:
            raise InputValidationError(
                f"Batch must contain between {BatchAnalysisValidator.MIN_ITEMS} and {BatchAnalysisValidator.MAX_ITEMS} texts",
                details={"count": count, "min": BatchAnalysisValidator.MIN_ITEMS, "max": BatchAnalysisValidator.MAX_ITEMS}
            )
        
        # Validate each text
        for idx, text in enumerate(texts):
            try:
                TextValidator.validate(text)
            except BiasDetectionError as e:
                e.details["index"] = idx
                raise
        
        logger.debug(f"Batch validation passed: {count} texts")


class RateLimiter:
    """Simple rate limiter for API endpoints."""
    
    def __init__(self, max_requests_per_minute: int = 30):
        """
        Initialize rate limiter.
        
        Args:
            max_requests_per_minute: Maximum requests allowed per minute
        """
        self.max_requests = max_requests_per_minute
        self.requests: Dict[str, list] = {}
    
    def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if within limit, False otherwise
        """
        import time
        current_time = time.time()
        minute_ago = current_time - 60
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > minute_ago
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        
        self.requests[user_id].append(current_time)
        return True


# Global rate limiter instance
_rate_limiter = RateLimiter(max_requests_per_minute=30)


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


def log_analysis_error(
    user_id: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log analysis error for debugging and monitoring.
    
    Args:
        user_id: ID of user performing the analysis
        error: The exception that occurred
        context: Additional context information
    """
    log_data = {
        "user_id": user_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {},
    }
    
    if isinstance(error, BiasDetectionError):
        logger.error(f"Bias detection error: {error.to_dict()}")
    else:
        logger.error(f"Unexpected error during bias analysis: {log_data}")
