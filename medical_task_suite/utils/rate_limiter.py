"""
Rate Limiter for API Requests

This module provides rate limiting functionality to ensure compliance
with API rate limits and prevent service disruption.
"""

import time
from typing import Optional
from collections import deque
from threading import Lock


class RateLimiter:
    """
    Token bucket rate limiter.

    This class implements a token bucket algorithm for rate limiting.
    It's useful for ensuring API rate limits are not exceeded.
    """

    def __init__(self, max_calls: int, period: float = 60.0):
        """
        Initialize the rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in the period
            period: Time period in seconds (default: 60 seconds)
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: deque = deque()  # Stores timestamps of calls
        self.lock = Lock()

        # Calculate minimum interval between calls
        self.min_interval = period / max_calls if max_calls > 0 else 0

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a call.

        Args:
            blocking: If True, wait until a call slot is available
            timeout: Maximum time to wait in seconds (None = infinite)

        Returns:
            True if permission acquired, False if timeout occurred
        """
        start_time = time.time()

        with self.lock:
            # Clean up expired call records
            now = time.time()
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()

            # Check if we can make a call
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True

            # If not blocking, return immediately
            if not blocking:
                return False

        # If blocking, wait for a slot
        while True:
            # Check timeout
            if timeout is not None and (time.time() - start_time) >= timeout:
                return False

            with self.lock:
                # Clean up expired records
                now = time.time()
                while self.calls and self.calls[0] <= now - self.period:
                    self.calls.popleft()

                # Check if slot available
                if len(self.calls) < self.max_calls:
                    self.calls.append(now)
                    return True

                # Calculate wait time
                if self.calls:
                    wait_time = self.period - (now - self.calls[0])
                    if wait_time > 0:
                        # Release lock while waiting
                        pass
                    else:
                        continue

                # Wait a bit before checking again
                time.sleep(0.1)

    def get_wait_time(self) -> float:
        """
        Get estimated wait time until next call can be made.

        Returns:
            Wait time in seconds (0 if call can be made immediately)
        """
        with self.lock:
            now = time.time()

            # Clean up expired records
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()

            # If under limit, no wait needed
            if len(self.calls) < self.max_calls:
                return 0.0

            # Calculate wait time until oldest call expires
            if self.calls:
                return max(0.0, self.period - (now - self.calls[0]))

            return 0.0

    def reset(self):
        """Reset the rate limiter (clear all call records)."""
        with self.lock:
            self.calls.clear()

    def get_stats(self) -> dict:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with rate limiter stats
        """
        with self.lock:
            now = time.time()

            # Clean up expired records first
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()

            return {
                'calls_in_period': len(self.calls),
                'max_calls': self.max_calls,
                'period': self.period,
                'available_slots': self.max_calls - len(self.calls),
                'wait_time': self.get_wait_time()
            }


class MultiRateLimiter:
    """
    Multi-level rate limiter for complex rate limiting scenarios.

    This class manages multiple rate limiters, useful for APIs with
    multiple rate limit tiers (e.g., per-minute and per-day limits).
    """

    def __init__(self):
        """Initialize the multi-rate limiter."""
        self.limiters: list[RateLimiter] = []
        self.lock = Lock()

    def add_limiter(self, max_calls: int, period: float) -> 'MultiRateLimiter':
        """
        Add a rate limiter.

        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds

        Returns:
            Self for chaining
        """
        with self.lock:
            self.limiters.append(RateLimiter(max_calls, period))
        return self

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission from all limiters.

        Args:
            blocking: If True, wait until all limiters permit
            timeout: Maximum time to wait in seconds

        Returns:
            True if permission acquired from all limiters
        """
        # Try to acquire from all limiters
        for limiter in self.limiters:
            if not limiter.acquire(blocking=blocking, timeout=timeout):
                return False
        return True

    def get_max_wait_time(self) -> float:
        """
        Get maximum wait time across all limiters.

        Returns:
            Maximum wait time in seconds
        """
        max_wait = 0.0
        for limiter in self.limiters:
            wait_time = limiter.get_wait_time()
            if wait_time > max_wait:
                max_wait = wait_time
        return max_wait

    def get_stats(self) -> list:
        """
        Get statistics for all limiters.

        Returns:
            List of statistics dictionaries
        """
        return [limiter.get_stats() for limiter in self.limiters]
