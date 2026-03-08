#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Data Adapters
数据适配器的测试
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from ..adapters import JSONAdapter, CSVAdapter, ExcelAdapter


class TestJSONAdapter(unittest.TestCase):
    """Test cases for JSON adapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = JSONAdapter()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_json_array(self):
        """Test loading JSON array."""
        test_data = [
            {"id": 1, "name": "Test 1"},
            {"id": 2, "name": "Test 2"},
        ]

        test_file = os.path.join(self.temp_dir, "test.json")
        with open(test_file, "w") as f:
            json.dump(test_data, f)

        result = self.adapter.load(test_file)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Test 1")

    def test_load_json_object_with_data_key(self):
        """Test loading JSON object with 'data' key."""
        test_data = {
            "metadata": {"count": 2},
            "data": [
                {"id": 1, "name": "Test 1"},
                {"id": 2, "name": "Test 2"},
            ]
        }

        test_file = os.path.join(self.temp_dir, "test.json")
        with open(test_file, "w") as f:
            json.dump(test_data, f)

        result = self.adapter.load(test_file)
        self.assertEqual(len(result), 2)

    def test_load_jsonl(self):
        """Test loading JSON Lines format."""
        test_file = os.path.join(self.temp_dir, "test.jsonl")
        with open(test_file, "w") as f:
            f.write('{"id": 1, "name": "Test 1"}\n')
            f.write('{"id": 2, "name": "Test 2"}\n')

        result = self.adapter.load(test_file)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Test 1")

    def test_save_json(self):
        """Test saving to JSON format."""
        test_data = [
            {"id": 1, "name": "Test 1"},
            {"id": 2, "name": "Test 2"},
        ]

        test_file = os.path.join(self.temp_dir, "output.json")
        self.adapter.save(test_data, test_file)

        self.assertTrue(os.path.exists(test_file))

        with open(test_file, "r") as f:
            result = json.load(f)

        self.assertEqual(len(result), 2)

    def test_save_jsonl(self):
        """Test saving to JSON Lines format."""
        test_data = [
            {"id": 1, "name": "Test 1"},
            {"id": 2, "name": "Test 2"},
        ]

        test_file = os.path.join(self.temp_dir, "output.jsonl")
        self.adapter.save(test_data, test_file, format="jsonl")

        self.assertTrue(os.path.exists(test_file))

        result = self.adapter.load(test_file)
        self.assertEqual(len(result), 2)


class TestCSVAdapter(unittest.TestCase):
    """Test cases for CSV adapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = CSVAdapter()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_csv(self):
        """Test loading CSV file."""
        test_file = os.path.join(self.temp_dir, "test.csv")
        with open(test_file, "w", newline="") as f:
            f.write("id,name\n")
            f.write("1,Test 1\n")
            f.write("2,Test 2\n")

        result = self.adapter.load(test_file)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Test 1")

    def test_save_csv(self):
        """Test saving to CSV format."""
        test_data = [
            {"id": 1, "name": "Test 1"},
            {"id": 2, "name": "Test 2"},
        ]

        test_file = os.path.join(self.temp_dir, "output.csv")
        self.adapter.save(test_data, test_file)

        self.assertTrue(os.path.exists(test_file))

        result = self.adapter.load(test_file)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Test 1")


class TestExcelAdapter(unittest.TestCase):
    """Test cases for Excel adapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = ExcelAdapter()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_load_xlsx(self):
        """Test saving and loading xlsx file."""
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl not installed")

        test_data = [
            {"id": 1, "name": "Test 1"},
            {"id": 2, "name": "Test 2"},
        ]

        test_file = os.path.join(self.temp_dir, "output.xlsx")
        self.adapter.save(test_data, test_file)

        self.assertTrue(os.path.exists(test_file))

        result = self.adapter.load(test_file)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Test 1")


if __name__ == "__main__":
    unittest.main()
