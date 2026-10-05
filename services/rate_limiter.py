"""
Smart Rate Limiter for Murf API
Prevents HTTP 429 errors by controlling request frequency
"""

import asyncio
import time
from typing import List
import logging

logger = logging.getLogger(__name__)


class MurfRateLimiter:
    """
    Smart rate limiter for Murf API to prevent 429 errors.
    
    Features:
    - Sliding window rate limiting
    - Burst control with semaphore
    - Automatic backoff on rate limit hits
    - Per-minute request tracking
    """
    
    def __init__(self, requests_per_minute: int = 20, burst_limit: int = 3):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute
            burst_limit: Maximum concurrent requests
        """
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.request_times: List[float] = []
        self.semaphore = asyncio.Semaphore(burst_limit)
        self.total_requests = 0
        self.total_waits = 0
        
        logger.info(f"🚦 Rate limiter initialized: {requests_per_minute} req/min, burst: {burst_limit}")
    
    async def acquire(self) -> bool:
        """
        Acquire permission to make a request.
        Waits if rate limit would be exceeded.
        
        Returns:
            True when permission granted
        """
        async with self.semaphore:
            now = time.time()
            
            # Remove requests older than 1 minute (sliding window)
            self.request_times = [t for t in self.request_times if now - t < 60]
            
            # Check if we need to wait
            if len(self.request_times) >= self.requests_per_minute:
                # Calculate wait time until oldest request expires
                oldest_request = self.request_times[0]
                wait_time = 60 - (now - oldest_request) + 0.1  # Add small buffer
                
                if wait_time > 0:
                    self.total_waits += 1
                    logger.info(f"⏳ Rate limit: waiting {wait_time:.1f}s ({len(self.request_times)} requests in window)")
                    await asyncio.sleep(wait_time)
                    
                    # Update now after waiting
                    now = time.time()
                    # Clean up again after waiting
                    self.request_times = [t for t in self.request_times if now - t < 60]
            
            # Record this request
            self.request_times.append(now)
            self.total_requests += 1
            
            return True
    
    async def acquire_with_delay(self, min_delay: float = 0.5) -> bool:
        """
        Acquire with guaranteed minimum delay between requests.
        Useful for pre-generation to be extra conservative.
        
        Args:
            min_delay: Minimum seconds between requests
            
        Returns:
            True when permission granted
        """
        await self.acquire()
        
        # Add minimum delay
        if min_delay > 0:
            await asyncio.sleep(min_delay)
        
        return True
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        return {
            "total_requests": self.total_requests,
            "total_waits": self.total_waits,
            "current_window_requests": len(self.request_times),
            "requests_per_minute": self.requests_per_minute,
            "burst_limit": self.burst_limit
        }
    
    def reset(self):
        """Reset rate limiter statistics"""
        self.request_times.clear()
        self.total_requests = 0
        self.total_waits = 0
        logger.info("🔄 Rate limiter reset")
