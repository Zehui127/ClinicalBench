"""
Cache Manager for API Responses

This module provides a simple in-memory caching mechanism to reduce
API calls and improve performance.
"""

import hashlib
import json
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from threading import Lock


class CacheManager:
    """
    Thread-safe in-memory cache manager.

    This class provides caching functionality with TTL (Time To Live) support.
    It's designed to cache API responses and other expensive operations.
    """

    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        """
        Initialize the cache manager.

        Args:
            ttl: Time to live for cache entries in seconds (default: 1 hour)
            max_size: Maximum number of items to store in cache
        """
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.ttl = ttl
        self.max_size = max_size
        self.lock = Lock()
        self.hits = 0
        self.misses = 0

    def _generate_key(self, *args, **kwargs) -> str:
        """
        Generate a cache key from arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            MD5 hash of the arguments
        """
        # Create a deterministic string representation of arguments
        key_data = json.dumps({
            "args": args,
            "kwargs": sorted(kwargs.items())  # Sort for consistent keys
        }, sort_keys=True, default=str)

        # Generate hash
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, *args, **kwargs) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            *args: Arguments to generate cache key
            **kwargs: Keyword arguments to generate cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        key = self._generate_key(*args, **kwargs)

        with self.lock:
            if key in self.cache:
                data, expiry = self.cache[key]

                # Check if entry has expired
                if datetime.now() < expiry:
                    self.hits += 1
                    return data
                else:
                    # Remove expired entry
                    del self.cache[key]

            self.misses += 1
            return None

    def set(self, value: Any, *args, **kwargs):
        """
        Set a value in cache.

        Args:
            value: Value to cache
            *args: Arguments to generate cache key
            **kwargs: Keyword arguments to generate cache key
        """
        key = self._generate_key(*args, **kwargs)

        with self.lock:
            # Enforce max size by removing oldest entries if needed
            if len(self.cache) >= self.max_size and key not in self.cache:
                # Remove the first (oldest) entry
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]

            # Set entry with expiry
            expiry = datetime.now() + timedelta(seconds=self.ttl)
            self.cache[key] = (value, expiry)

    def clear(self):
        """Clear all cached entries."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def remove(self, *args, **kwargs):
        """
        Remove a specific entry from cache.

        Args:
            *args: Arguments to generate cache key
            **kwargs: Keyword arguments to generate cache key
        """
        key = self._generate_key(*args, **kwargs)

        with self.lock:
            if key in self.cache:
                del self.cache[key]

    def cleanup_expired(self):
        """Remove all expired entries from cache."""
        now = datetime.now()

        with self.lock:
            expired_keys = [
                key for key, (_, expiry) in self.cache.items()
                if expiry < now
            ]

            for key in expired_keys:
                del self.cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': f"{hit_rate:.2f}%",
                'ttl': self.ttl
            }

    def __len__(self) -> int:
        """Get current cache size."""
        return len(self.cache)

    def __contains__(self, item) -> bool:
        """Check if an item is in the cache (ignoring expiry for quick check)."""
        return self.get(item) is not None


class CachedFunction:
    """
    Decorator for caching function results.

    Usage:
        @CachedFunction(ttl=3600)
        def expensive_function(arg1, arg2):
            # ... expensive computation ...
            return result
    """

    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        """
        Initialize the cached function decorator.

        Args:
            ttl: Time to live for cache entries in seconds
            max_size: Maximum number of items to store in cache
        """
        self.cache = CacheManager(ttl=ttl, max_size=max_size)

    def __call__(self, func):
        """Decorate a function with caching."""

        def wrapped(*args, **kwargs):
            # Try to get from cache
            cached_value = self.cache.get(func.__name__, *args, **kwargs)
            if cached_value is not None:
                return cached_value

            # Call the function and cache the result
            result = func(*args, **kwargs)
            self.cache.set(result, func.__name__, *args, **kwargs)

            return result

        # Add cache control methods to wrapped function
        wrapped.cache = self.cache
        wrapped.cache_clear = self.cache.clear
        wrapped.cache_stats = self.cache.get_stats

        return wrapped
