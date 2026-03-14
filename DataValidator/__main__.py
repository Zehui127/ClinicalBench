#!/usr/bin/env python3
"""
Main entry point for DataValidator module.

Allows running the validator as:
    python -m DataValidator tasks.json
"""

from .cli import main

if __name__ == "__main__":
    main()
