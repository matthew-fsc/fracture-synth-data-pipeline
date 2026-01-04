"""
Retry Handler for Azure OpenAI API calls.

Implements exponential backoff with jitter for retries.
"""

import logging
import random
import time
from typing import Callable, TypeVar, Optional, List
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryHandler:
    """
    Retry handler with exponential backoff and jitter.
    
    Handles common API errors:
    - Rate limit errors (429)
    - Server errors (500-599)
    - Network errors
    - Timeout errors
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_status_codes: Optional[List[int]] = None
    ):
        """
        Initialize retry handler.
        
        Args:
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add jitter to delay
            retryable_status_codes: List of HTTP status codes to retry (default: [429, 500, 502, 503, 504])
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_status_codes = retryable_status_codes or [429, 500, 502, 503, 504]
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        # Exponential backoff
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        # Cap at max_delay
        delay = min(delay, self.max_delay)
        
        # Add jitter (random between 0.5x and 1.5x)
        if self.jitter:
            jitter_factor = 0.5 + random.random()  # 0.5 to 1.5
            delay *= jitter_factor
        
        return delay
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable."""
        # Check for HTTP status codes
        status_code = getattr(error, 'status_code', None)
        if status_code and status_code in self.retryable_status_codes:
            return True
        
        # Check for rate limit errors
        error_message = str(error).lower()
        if 'rate limit' in error_message or '429' in error_message:
            return True
        
        # Check for server errors
        if '500' in error_message or '503' in error_message or '502' in error_message:
            return True
        
        # Check for timeout errors
        if 'timeout' in error_message or 'timed out' in error_message:
            return True
        
        # Check for network errors
        if 'connection' in error_message or 'network' in error_message:
            return True
        
        return False
    
    def retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator to add retry logic to a function.
        
        Args:
            func: Function to wrap with retry logic
            
        Returns:
            Wrapped function with retry logic
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on last attempt
                    if attempt >= self.max_retries:
                        logger.error(f"Max retries ({self.max_retries}) exceeded for {func.__name__}")
                        raise
                    
                    # Check if error is retryable
                    if not self._is_retryable_error(e):
                        logger.warning(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    # Calculate delay and wait
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.max_retries} for {func.__name__} "
                        f"after {delay:.2f}s: {e}"
                    )
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected retry failure in {func.__name__}")
        
        return wrapper
    
    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        @self.retry
        def _execute():
            return func(*args, **kwargs)
        
        return _execute()


# Convenience function for common use case
def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """
    Decorator factory for retry logic.
    
    Usage:
        @with_retry(max_retries=5)
        def my_function():
            ...
    """
    handler = RetryHandler(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay
    )
    return handler.retry

