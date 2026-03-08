#!/usr/bin/env python3
"""
Tau2-Bench Clinical Tasks Validation Script

This script validates the generated tasks.json file to ensure:
1. JSON format is valid
2. All required fields are present
3. Field mappings are correct
4. Data types are appropriate

Usage:
    python validate_tasks.py [--tasks <path_to_tasks.json>]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


# Validation rules
REQUIRED_TOP_LEVEL_FIELDS = ["id", "user_scenario", "evaluation_criteria"]
REQUIRED_USER_SCENARIO_FIELDS = ["instructions"]
REQUIRED_INSTRUCTIONS_FIELDS = ["task_instructions", "domain", "reason_for_call"]


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = True

    def add_error(self, message: str, task_id: str = None):
        """Add an error message."""
        prefix = f"Task {task_id}: " if task_id else ""
        self.errors.append(f"{prefix}{message}")
        self.passed = False

    def add_warning(self, message: str, task_id: str = None):
        """Add a warning message."""
        prefix = f"Task {task_id}: " if task_id else ""
        self.warnings.append(f"{prefix}{message}")

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        if self.passed:
            print("✓ VALIDATION PASSED")
        else:
            print("✗ VALIDATION FAILED")

        print(f"\nErrors: {len(self.errors)}")
        if self.errors:
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  ✗ {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")

        print(f"\nWarnings: {len(self.warnings)}")
        if self.warnings:
            for warning in self.warnings[:10]:  # Show first 10 warnings
                print(f"  ⚠ {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")

        print("=" * 60)


def validate_json_format(file_path: str, result: ValidationResult) -> List[Dict]:
    """Validate JSON file format and load data."""
    print("Validating JSON format...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            result.add_error("Root element must be an array")
            return []

        print(f"✓ JSON is valid, found {len(data)} tasks")
        return data

    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON format: {e}")
        return []
    except Exception as e:
        result.add_error(f"Error reading file: {e}")
        return []


def validate_task_structure(task: Dict[str, Any], result: ValidationResult, index: int):
    """Validate individual task structure."""
    task_id = task.get("id", f"index_{index}")

    # Check required top-level fields
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in task:
            result.add_error(f"Missing required field: '{field}'", task_id)

    # Validate user_scenario
    if "user_scenario" in task:
        user_scenario = task["user_scenario"]

        if not isinstance(user_scenario, dict):
            result.add_error("user_scenario must be an object", task_id)
        else:
            for field in REQUIRED_USER_SCENARIO_FIELDS:
                if field not in user_scenario:
                    result.add_error(f"Missing user_scenario field: '{field}'", task_id)

            # Validate instructions
            if "instructions" in user_scenario:
                instructions = user_scenario["instructions"]

                if not isinstance(instructions, dict):
                    result.add_error("instructions must be an object", task_id)
                else:
                    for field in REQUIRED_INSTRUCTIONS_FIELDS:
                        if field not in instructions:
                            result.add_error(
                                f"Missing instructions field: '{field}'", task_id
                            )

                    # Check domain value
                    if "domain" in instructions:
                        domain = instructions["domain"]
                        if domain != "clinical":
                            result.add_warning(
                                f"Unexpected domain value: '{domain}' (expected 'clinical')",
                                task_id
                            )

    # Validate evaluation_criteria
    if "evaluation_criteria" in task:
        eval_criteria = task["evaluation_criteria"]

        if not isinstance(eval_criteria, dict):
            result.add_error("evaluation_criteria must be an object", task_id)
        else:
            # Check for nl_assertions which are commonly used
            if "nl_assertions" in eval_criteria:
                nl_assertions = eval_criteria["nl_assertions"]

                if not isinstance(nl_assertions, list):
                    result.add_error("nl_assertions must be an array", task_id)
                elif len(nl_assertions) == 0:
                    result.add_warning("nl_assertions is empty", task_id)


def validate_field_mappings(task: Dict[str, Any], result: ValidationResult, index: int):
    """Validate that field mappings from MedAgentBench are preserved correctly."""
    task_id = task.get("id", f"index_{index}")

    # Check that ticket field exists (should be copied from instruction)
    if "ticket" not in task:
        result.add_warning("Missing 'ticket' field (should contain task instruction)", task_id)
    elif not isinstance(task["ticket"], str) or len(task["ticket"]) == 0:
        result.add_warning("'ticket' field is empty", task_id)

    # Check for annotations with source_format
    if "annotations" in task:
        annotations = task["annotations"]

        if "source_format" not in annotations:
            result.add_warning("Missing 'source_format' in annotations", task_id)
        elif annotations["source_format"] != "medagentbench_v2":
            result.add_warning(
                f"Unexpected source_format: '{annotations['source_format']}'",
                task_id
            )

        # Check for expected_answer
        if "expected_answer" not in annotations:
            result.add_warning("Missing 'expected_answer' in annotations (for evaluation)", task_id)
    else:
        result.add_warning("Missing 'annotations' field", task_id)


def validate_data_consistency(task: Dict[str, Any], result: ValidationResult, index: int):
    """Validate data consistency across fields."""
    task_id = task.get("id", f"index_{index}")

    # Check that ticket matches task_instructions
    if "ticket" in task and "user_scenario" in task:
        ticket = task.get("ticket", "")
        instructions = task.get("user_scenario", {}).get("instructions", {})
        task_instructions = instructions.get("task_instructions", "")

        if ticket and task_instructions and ticket != task_instructions:
            result.add_warning(
                "'ticket' field does not match 'task_instructions'",
                task_id
            )

    # Check that nl_assertions contain expected_answer
    if "evaluation_criteria" in task and "annotations" in task:
        eval_criteria = task["evaluation_criteria"]
        annotations = task["annotations"]

        expected_answer = annotations.get("expected_answer", "")
        nl_assertions = eval_criteria.get("nl_assertions", [])

        if expected_answer and nl_assertions:
            # Check if expected_answer is mentioned in nl_assertions
            expected_mentioned = any(expected_answer in assertion for assertion in nl_assertions)
            if not expected_mentioned:
                result.add_warning(
                    f"expected_answer '{expected_answer}' not found in nl_assertions",
                    task_id
                )


def print_statistics(tasks: List[Dict]):
    """Print statistics about the tasks."""
    print("\n" + "=" * 60)
    print("TASK STATISTICS")
    print("=" * 60)

    total = len(tasks)

    # Count tasks with various fields
    with_ticket = sum(1 for t in tasks if "ticket" in t)
    with_annotations = sum(1 for t in tasks if "annotations" in t)
    with_nl_assertions = sum(1 for t in tasks if "evaluation_criteria" in t and
                            t["evaluation_criteria"].get("nl_assertions"))

    print(f"Total tasks: {total}")
    print(f"With ticket field: {with_ticket}/{total} ({100*with_ticket/total:.1f}%)")
    print(f"With annotations: {with_annotations}/{total} ({100*with_annotations/total:.1f}%)")
    print(f"With nl_assertions: {with_nl_assertions}/{total} ({100*with_nl_assertions/total:.1f}%)")

    # Sample task IDs
    print(f"\nSample task IDs:")
    for task in tasks[:5]:
        print(f"  - {task.get('id', 'unknown')}")

    if len(tasks) > 5:
        print(f"  ... and {len(tasks) - 5} more")

    print("=" * 60)


def validate_file_location(file_path: str, result: ValidationResult):
    """Validate that the file is in the correct location."""
    file_path_obj = Path(file_path).resolve()

    print("\nValidating file location...")

    # Check if file is in tau2-bench/data/clinical/
    path_parts = file_path_obj.parts
    expected_path_segments = ["tau2-bench", "data", "clinical"]

    # Check if the path contains expected segments
    path_str = str(file_path_obj)
    if all(seg in path_str for seg in expected_path_segments):
        print(f"✓ File is in the correct location: {file_path_obj}")

        # Also check parent directory structure
        if file_path_obj.parent.name == "clinical":
            print(f"✓ Parent directory is 'clinical' as expected")
            return

    result.add_warning(
        f"File may not be in the standard tau2-bench structure. "
        f"Expected path contains: tau2-bench/data/clinical/"
    )


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate tau2-bench clinical tasks.json file"
    )
    parser.add_argument(
        "--tasks",
        default="C:\\Users\\方正\\tau2-bench\\data\\clinical\\tasks.json",
        help="Path to tasks.json file to validate"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("TAU2-BENCH CLINICAL TASKS VALIDATION")
    print("=" * 60)
    print(f"Validating: {args.tasks}")
    print()

    result = ValidationResult()

    # Validate file location
    validate_file_location(args.tasks, result)

    # Validate JSON format and load data
    tasks = validate_json_format(args.tasks, result)

    if not tasks:
        result.print_summary()
        return 1 if not result.passed else 0

    # Validate each task
    print("\nValidating task structure...")
    for i, task in enumerate(tasks):
        validate_task_structure(task, result, i)
        validate_field_mappings(task, result, i)
        validate_data_consistency(task, result, i)

    # Print statistics
    print_statistics(tasks)

    # Print summary
    result.print_summary()

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
