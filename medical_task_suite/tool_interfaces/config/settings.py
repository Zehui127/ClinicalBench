"""
Interface Configuration Management

This module provides configuration management for medical tool interfaces,
including settings for FHIR, OpenFDA, and other real API implementations.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class InterfaceConfig:
    """
    Configuration manager for tool interfaces.

    This class handles loading and accessing configuration for both
    stub and real interface implementations.
    """

    _instance: Optional['InterfaceConfig'] = None

    def __new__(cls) -> 'InterfaceConfig':
        """Singleton pattern to ensure only one config instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize configuration (only once)."""
        if self._initialized:
            return

        self.config_dir = Path(__file__).parent
        self.api_config = self._load_api_config()
        self.use_real = self._get_use_real_setting()
        self.fallback_to_stub = self.api_config.get('interface', {}).get('fallback_to_stub', True)
        self._initialized = True

    def _load_api_config(self) -> Dict[str, Any]:
        """
        Load API configuration from YAML file.

        Returns:
            Dictionary containing API configuration
        """
        config_file = self.config_dir / "api_config.yaml"

        if not config_file.exists():
            # Return default config if file doesn't exist
            return self._get_default_config()

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            # Log warning and return default config
            print(f"Warning: Could not load api_config.yaml: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when YAML file is not available."""
        return {
            'fhir': {
                'base_url': 'https://hapi.fhir.org/baseR4',
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 1,
                'cache_ttl': 3600
            },
            'openfda': {
                'base_url': 'https://api.fda.gov',
                'drug_label_endpoint': '/drug/label.json',
                'drug_event_endpoint': '/drug/event.json',
                'api_key': os.getenv('OPENFDA_API_KEY'),
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 1,
                'rate_limit': 240,
                'rate_limit_burst': 10,
                'cache_ttl': 3600
            },
            'cache': {
                'enabled': True,
                'default_ttl': 3600,
                'max_size': 1000
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'interface': {
                'use_real': False,
                'fallback_to_stub': True,
                'timeout_fallback': 5
            }
        }

    def _get_use_real_setting(self) -> bool:
        """
        Determine whether to use real interfaces.

        Checks environment variable and config file. Environment variable
        takes precedence over config file setting.

        Returns:
            True if real interfaces should be used, False for stubs
        """
        env_value = os.getenv('USE_REAL_INTERFACES', '').lower()
        if env_value in ('true', '1', 'yes', 'on'):
            return True
        if env_value in ('false', '0', 'no', 'off'):
            return False

        # Fall back to config file setting
        return self.api_config.get('interface', {}).get('use_real', False)

    def get_fhir_config(self) -> Dict[str, Any]:
        """
        Get FHIR configuration.

        Returns:
            Dictionary with FHIR API configuration
        """
        return self.api_config.get('fhir', {})

    def get_openfda_config(self) -> Dict[str, Any]:
        """
        Get OpenFDA configuration.

        Returns:
            Dictionary with OpenFDA API configuration
        """
        config = self.api_config.get('openfda', {})

        # Override API key from environment if set
        env_key = os.getenv('OPENFDA_API_KEY')
        if env_key:
            config['api_key'] = env_key

        return config

    def get_cache_config(self) -> Dict[str, Any]:
        """
        Get cache configuration.

        Returns:
            Dictionary with cache settings
        """
        return self.api_config.get('cache', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.

        Returns:
            Dictionary with logging settings
        """
        return self.api_config.get('logging', {})

    def is_real_enabled(self) -> bool:
        """
        Check if real interfaces are enabled.

        Returns:
            True if real interfaces should be used
        """
        return self.use_real

    def should_fallback_to_stub(self) -> bool:
        """
        Check if should fallback to stub on error.

        Returns:
            True if fallback is enabled
        """
        return self.fallback_to_stub

    def get_timeout_fallback(self) -> int:
        """
        Get timeout before falling back to stub.

        Returns:
            Timeout in seconds
        """
        return self.api_config.get('interface', {}).get('timeout_fallback', 5)


# Global config instance
_config: Optional[InterfaceConfig] = None


def get_config() -> InterfaceConfig:
    """
    Get the global configuration instance.

    Returns:
        InterfaceConfig singleton instance
    """
    global _config
    if _config is None:
        _config = InterfaceConfig()
    return _config


def reload_config():
    """
    Reload configuration from file.

    This is primarily useful for testing or when config file changes.
    """
    global _config
    _config = None
    return get_config()
