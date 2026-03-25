"""
Base Real Interface

This module provides the base class for all real interface implementations.
It includes common functionality for HTTP requests, caching, rate limiting,
and error handling.
"""

import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time

from medical_task_suite.utils.cache_manager import CacheManager
from medical_task_suite.utils.rate_limiter import RateLimiter
from medical_task_suite.utils.logger import get_logger


class BaseRealInterface(ABC):
    """
    Base class for real interface implementations.

    This class provides common functionality for:
    - HTTP requests with retry logic
    - Caching to reduce API calls
    - Rate limiting to comply with API limits
    - Comprehensive error handling
    - Logging for debugging and monitoring
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the base real interface.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1)
        self.cache_ttl = config.get('cache_ttl', 3600)

        # Initialize cache
        cache_config = config.get('cache', {})
        cache_enabled = cache_config.get('enabled', True)
        if cache_enabled:
            self.cache = CacheManager(
                ttl=self.cache_ttl,
                max_size=cache_config.get('max_size', 1000)
            )
        else:
            self.cache = None

        # Initialize rate limiter if configured
        rate_limit = config.get('rate_limit')
        if rate_limit:
            self.rate_limiter = RateLimiter(
                max_calls=rate_limit,
                period=config.get('rate_limit_period', 60.0)
            )
        else:
            self.rate_limiter = None

        # Initialize logger
        self.logger = get_logger(self.__class__.__name__)

        # Session for connection pooling
        self.session = requests.Session()
        self.is_connected = False

    def _make_request(
        self,
        url: str,
        method: str = 'GET',
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        use_cache: bool = True,
        skip_rate_limit: bool = False
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic, caching, and rate limiting.

        Args:
            url: Request URL
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data
            headers: Request headers
            use_cache: Whether to use caching
            skip_rate_limit: Whether to skip rate limiting

        Returns:
            Response JSON as dictionary

        Raises:
            requests.RequestException: On request failure after retries
        """
        # Check cache first
        if use_cache and self.cache and method == 'GET':
            cache_key = self._generate_cache_key(url, params, data)
            cached_response = self.cache.get(cache_key)
            if cached_response is not None:
                self.logger.debug(f"Cache hit for {url}")
                return cached_response

        # Rate limiting
        if self.rate_limiter and not skip_rate_limit:
            wait_time = self.rate_limiter.get_wait_time()
            if wait_time > 0:
                self.logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                time.sleep(wait_time)

            self.rate_limiter.acquire()

        # Make request with retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=headers,
                    timeout=self.timeout
                )

                # Check for HTTP errors
                response.raise_for_status()

                # Parse JSON response
                result = response.json()

                # Cache successful GET requests
                if use_cache and self.cache and method == 'GET':
                    self.cache.set(result, cache_key)

                return result

            except requests.HTTPError as e:
                last_exception = e
                self.logger.warning(
                    f"HTTP error on attempt {attempt + 1}/{self.max_retries}: {e}"
                )

                # Don't retry client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    raise

            except requests.RequestException as e:
                last_exception = e
                self.logger.warning(
                    f"Request error on attempt {attempt + 1}/{self.max_retries}: {e}"
                )

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait = self.retry_delay * (2 ** attempt)
                self.logger.debug(f"Retrying after {wait}s...")
                time.sleep(wait)

        # All retries failed
        self.logger.error(f"Request failed after {self.max_retries} attempts")
        raise requests.RequestException(
            f"Request failed after {self.max_retries} attempts: {last_exception}"
        ) from last_exception

    def _generate_cache_key(self, url: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> str:
        """
        Generate a cache key for a request.

        Args:
            url: Request URL
            params: Query parameters
            data: Request data

        Returns:
            Cache key string
        """
        import hashlib
        import json

        key_data = {
            'url': url,
            'params': params,
            'data': data
        }

        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the service.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the service."""
        pass

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get cache statistics.

        Returns:
            Cache statistics dictionary or None if cache disabled
        """
        if self.cache:
            return self.cache.get_stats()
        return None

    def get_rate_limiter_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get rate limiter statistics.

        Returns:
            Rate limiter statistics dictionary or None if not configured
        """
        if self.rate_limiter:
            return self.rate_limiter.get_stats()
        return None

    def clear_cache(self):
        """Clear the cache."""
        if self.cache:
            self.cache.clear()
            self.logger.info("Cache cleared")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, 'session'):
            self.session.close()
