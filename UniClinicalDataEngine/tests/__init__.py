"""
Tests for UniClinicalDataEngine
UniClinicalDataEngine 的测试
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBase(unittest.TestCase):
    """Base test class with common setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data_dir = Path(__file__).parent / "data"

    def tearDown(self):
        """Clean up after tests."""
        pass


if __name__ == "__main__":
    unittest.main()
