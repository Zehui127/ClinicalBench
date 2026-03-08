#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Clinical Data Engine
临床数据处理引擎的测试
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from ..engine import ClinicalDataEngine, PipelineConfig
from ..adapters import JSONAdapter


class TestClinicalDataEngine(unittest.TestCase):
    """Test cases for ClinicalDataEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data = [
            {
                "patient_id": "P001",
                "department": "cardiology",
                "diagnosis": "hypertension",
                "age": 45,
            },
            {
                "patient_id": "P002",
                "department": "nephrology",
                "diagnosis": "ckd",
                "age": 62,
            },
        ]

        # Create test input file
        self.input_file = os.path.join(self.temp_dir, "input.json")
        with open(self.input_file, "w") as f:
            json.dump(self.test_data, f)

        self.output_file = os.path.join(self.temp_dir, "output.json")

    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_engine_initialization(self):
        """Test engine initialization."""
        config = PipelineConfig(
            input_path=self.input_file,
            output_path=self.output_file,
        )

        engine = ClinicalDataEngine(config)
        self.assertIsNotNone(engine)
        self.assertEqual(engine.config.input_path, self.input_file)

    def test_load_data(self):
        """Test loading data."""
        config = PipelineConfig(
            input_path=self.input_file,
            output_path=self.output_file,
        )

        engine = ClinicalDataEngine(config)
        data = engine.load_data()

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["department"], "cardiology")

    def test_save_data(self):
        """Test saving data."""
        config = PipelineConfig(
            input_path=self.input_file,
            output_path=self.output_file,
        )

        engine = ClinicalDataEngine(config)
        engine.save_data(self.test_data)

        self.assertTrue(os.path.exists(self.output_file))

        with open(self.output_file, "r") as f:
            saved_data = json.load(f)

        self.assertEqual(len(saved_data), 2)

    def test_filter_data(self):
        """Test filtering data."""
        config = PipelineConfig(
            input_path=self.input_file,
            output_path=self.output_file,
            filters={"department": "cardiology"},
        )

        engine = ClinicalDataEngine(config)
        filtered = engine.filter_data(self.test_data)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["department"], "cardiology")

    def test_transform_data(self):
        """Test transforming data."""
        def add_uppercase_department(data):
            for record in data:
                record["department_upper"] = record.get("department", "").upper()
            return data

        config = PipelineConfig(
            input_path=self.input_file,
            output_path=self.output_file,
            transformations=[add_uppercase_department],
        )

        engine = ClinicalDataEngine(config)
        transformed = engine.transform(self.test_data)

        self.assertEqual(transformed[0]["department_upper"], "CARDIOLOGY")

    def test_validate_data(self):
        """Test data validation."""
        config = PipelineConfig(
            input_path=self.input_file,
            output_path=self.output_file,
            validate_schema=True,
        )

        engine = ClinicalDataEngine(config)
        is_valid = engine.validate(self.test_data)

        self.assertTrue(is_valid)

    def test_run_pipeline(self):
        """Test complete pipeline execution."""
        config = PipelineConfig(
            input_path=self.input_file,
            output_path=self.output_file,
        )

        engine = ClinicalDataEngine(config)
        result = engine.run_pipeline()

        self.assertTrue(result.success)
        self.assertEqual(result.records_processed, 2)
        self.assertTrue(os.path.exists(self.output_file))


class TestAdapterRegistry(unittest.TestCase):
    """Test cases for adapter registry."""

    def test_default_adapters(self):
        """Test that default adapters are registered."""
        engine = ClinicalDataEngine()

        self.assertIn("json", engine.ADAPTER_REGISTRY)
        self.assertIn("jsonl", engine.ADAPTER_REGISTRY)
        self.assertIn("csv", engine.ADAPTER_REGISTRY)
        self.assertIn("xlsx", engine.ADAPTER_REGISTRY)

    def test_get_adapter(self):
        """Test getting adapter for format."""
        engine = ClinicalDataEngine()

        adapter = engine._get_adapter("json")
        self.assertIsInstance(adapter, JSONAdapter)

    def test_detect_format(self):
        """Test format detection from filename."""
        engine = ClinicalDataEngine()

        self.assertEqual(engine._detect_format("data.json"), "json")
        self.assertEqual(engine._detect_format("data.jsonl"), "jsonl")
        self.assertEqual(engine._detect_format("data.csv"), "csv")
        self.assertEqual(engine._detect_format("data.xlsx"), "xlsx")


if __name__ == "__main__":
    unittest.main()
