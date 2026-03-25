"""
Configuration Management for Tool Interfaces

This module provides configuration management for switching between
stub and real implementations of medical tool interfaces.
"""

from .settings import InterfaceConfig, get_config

__all__ = ['InterfaceConfig', 'get_config']
