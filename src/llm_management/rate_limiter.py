"""
Rate Limiter for Azure OpenAI API calls.

Implements token bucket algorithm for rate limiting.
"""

import time
import logging
from typing import Optional
from threading import Lock
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = 60
    tokens_per_minute: Optional[int] = None
    requests_per_day: Optional[int] = None
    tokens_per_day: Optional[int] = None


class RateLimiter:
    """
    Rate limiter using token bucket algorithm.
    
    Supports multiple rate limits:
    - Requests per minute
    - Tokens per minute
    - Requests per day
    - Tokens per day
    """
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.lock = Lock()
        
        # Token buckets (tokens = permits)
        self.request_tokens = config.requests_per_minute
        self.token_tokens = config.tokens_per_minute or float('inf')
        self.request_tokens_daily = config.requests_per_day or float('inf')
        self.token_tokens_daily = config.tokens_per_day or float('inf')
        
        # Timestamps for refill
        self.last_request_refill = time.time()
        self.last_token_refill = time.time()
        self.last_daily_refill = time.time()
        self.daily_request_count = 0
        self.daily_token_count = 0
        
        # Refill rate: tokens per second
        self.request_refill_rate = config.requests_per_minute / 60.0
        self.token_refill_rate = (config.tokens_per_minute / 60.0) if config.tokens_per_minute else float('inf')
    
    def _refill_buckets(self):
        """Refill token buckets based on time elapsed."""
        now = time.time()
        
        with self.lock:
            # Refill per-minute request bucket
            elapsed = now - self.last_request_refill
            if elapsed > 0:
                tokens_to_add = elapsed * self.request_refill_rate
                self.request_tokens = min(
                    self.config.requests_per_minute,
                    self.request_tokens + tokens_to_add
                )
                self.last_request_refill = now
            
            # Refill per-minute token bucket
            if self.config.tokens_per_minute:
                elapsed = now - self.last_token_refill
                if elapsed > 0:
                    tokens_to_add = elapsed * self.token_refill_rate
                    self.token_tokens = min(
                        self.config.tokens_per_minute,
                        self.token_tokens + tokens_to_add
                    )
                    self.last_token_refill = now
            
            # Reset daily counters if new day
            if now - self.last_daily_refill >= 86400:  # 24 hours
                self.daily_request_count = 0
                self.daily_token_count = 0
                self.last_daily_refill = now
    
    def acquire(self, tokens: int = 1) -> float:
        """
        Acquire permission to make API call.
        
        Args:
            tokens: Estimated tokens for the request
            
        Returns:
            Wait time in seconds (0 if immediate, >0 if need to wait)
        """
        self._refill_buckets()
        
        with self.lock:
            wait_time = 0.0
            
            # Check per-minute request limit
            if self.request_tokens < 1:
                wait_time = max(wait_time, (1 - self.request_tokens) / self.request_refill_rate)
            
            # Check per-minute token limit
            if self.config.tokens_per_minute and self.token_tokens < tokens:
                wait_time = max(wait_time, (tokens - self.token_tokens) / self.token_refill_rate)
            
            # Check daily request limit
            if self.config.requests_per_day and self.daily_request_count >= self.config.requests_per_day:
                # Wait until next day
                seconds_until_midnight = 86400 - (time.time() - self.last_daily_refill)
                wait_time = max(wait_time, seconds_until_midnight)
            
            # Check daily token limit
            if self.config.tokens_per_day and self.daily_token_count + tokens > self.config.tokens_per_day:
                # Wait until next day
                seconds_until_midnight = 86400 - (time.time() - self.last_daily_refill)
                wait_time = max(wait_time, seconds_until_midnight)
            
            # If we need to wait, return wait time
            if wait_time > 0:
                return wait_time
            
            # Consume tokens
            self.request_tokens -= 1
            self.token_tokens -= tokens
            self.daily_request_count += 1
            self.daily_token_count += tokens
            
            return 0.0
    
    def wait_if_needed(self, tokens: int = 1):
        """
        Wait if necessary to respect rate limits.
        
        Args:
            tokens: Estimated tokens for the request
        """
        wait_time = self.acquire(tokens)
        if wait_time > 0:
            logger.info(f"Rate limit: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
    
    def record_usage(self, tokens: int):
        """
        Record actual token usage (for accurate daily tracking).
        
        Args:
            tokens: Actual tokens used
        """
        with self.lock:
            # Adjust daily token count with actual usage
            # (subtract estimated, add actual)
            self.daily_token_count += tokens - 1  # We already counted 1 token in acquire()

