#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedXpertQA Validation Script

Validates that processed files match tau2-bench format requirements:
- tasks.json: Pure questions without answers
- db.json: Complete QA pair database
- policy.md: Clinical policy document
- Data consistency between files

Usage:
    python medxpertqa_validate.py --data-dir <path_to_medxpertqa_directory>
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ValidationResult:
    """Container for validation results."""
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = True
        self.stats = {}

    def add_error(self, message: str, context: str = ""):
        """Add an error message."""
        prefix = f"[{context}] " if context else ""
        self.errors.append(f"{prefix}{message}")
        self.passed = False

    def add_warning(self, message: str, context: str = ""):
        """Add a warning message."""
        prefix = f"[{context}] " if context else ""
        self.warnings.append(f"{prefix}{message}")

    def add_stat(self, key: str, value: Any):
        """Add a statistic."""
        self.stats[key] = value


def validate_json_file(file_path: Path, result: ValidationResult, context: str = "") -> Optional[Dict]:
    """Validate that a file exists and is valid JSON."""
    if not file_path.exists():
        result.add_error(f"File not found: {file_path}", context)
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON format: {e}", context)
        return None
    except Exception as e:
        result.add_error(f"Error reading file: {e}", context)
        return None


def validate_tasks_json(data: Dict, result: ValidationResult) -> Tuple[List[str], List[Dict]]:
    """Validate tasks.json structure and content."""
    context = "tasks.json"

    # Check if it's an array
    if not isinstance(data, list):
        result.add_error("Root element must be an array", context)
        return [], []

    if len(data) == 0:
        result.add_error("No tasks found", context)
        return [], []

    result.add_stat("total_tasks", len(data))

    # Track task IDs and check for duplicates
    task_ids = []
    task_id_set = set()
    duplicate_ids = set()
    tasks_with_answers = []

    # Required fields
    required_fields = ["id", "description", "user_scenario", "ticket"]
    optional_fields = ["initial_state", "evaluation_criteria", "annotations"]

    for i, task in enumerate(data):
        task_id = task.get("id", f"index_{i}")

        # Check for duplicates
        if task_id in task_id_set:
            duplicate_ids.add(task_id)
        task_id_set.add(task_id)
        task_ids.append(task_id)

        # Check required fields
        for field in required_fields:
            if field not in task:
                result.add_error(f"Task '{task_id}' missing required field: '{field}'", context)

        # Check that evaluation_criteria and annotations are null/empty (no answers)
        if task.get("evaluation_criteria") is not None:
            # Check if it contains actual criteria (not just null/empty)
            ec = task.get("evaluation_criteria")
            if ec and isinstance(ec, dict):
                # If it has meaningful content, that's a problem
                if any(v for v in ec.values() if v not in [None, [], {}]):
                    result.add_error(f"Task '{task_id}' has non-empty evaluation_criteria (should be null for pure questions)", context)

        if task.get("annotations") is not None:
            ann = task.get("annotations")
            if ann and isinstance(ann, dict):
                if any(v for v in ann.values() if v not in [None, [], {}]):
                    tasks_with_answers.append(task_id)
                    result.add_error(f"Task '{task_id}' has non-empty annotations (may contain answers)", context)

        # Validate description
        if "description" in task:
            desc = task["description"]
            if not isinstance(desc, dict):
                result.add_error(f"Task '{task_id}' description must be an object", context)
            else:
                if "purpose" not in desc:
                    result.add_warning(f"Task '{task_id}' description missing 'purpose'", context)

        # Validate user_scenario
        if "user_scenario" in task:
            us = task["user_scenario"]
            if not isinstance(us, dict):
                result.add_error(f"Task '{task_id}' user_scenario must be an object", context)
            else:
                if "instructions" not in us:
                    result.add_error(f"Task '{task_id}' user_scenario missing 'instructions'", context)
                else:
                    instructions = us["instructions"]
                    if not isinstance(instructions, dict):
                        result.add_error(f"Task '{task_id}' instructions must be an object", context)
                    else:
                        if "domain" not in instructions:
                            result.add_warning(f"Task '{task_id}' instructions missing 'domain'", context)

        # Validate ticket (question text)
        if "ticket" in task:
            ticket = task["ticket"]
            if not isinstance(ticket, str) or len(ticket.strip()) == 0:
                result.add_error(f"Task '{task_id}' ticket must be a non-empty string", context)

    # Check for duplicate IDs
    if duplicate_ids:
        result.add_error(f"Found duplicate task IDs: {', '.join(sorted(duplicate_ids))}", context)

    # Check for tasks with answers
    if tasks_with_answers:
        result.add_error(f"Found {len(tasks_with_answers)} tasks with non-empty annotations (possible answers)", context)

    result.add_stat("unique_tasks", len(task_id_set))

    return task_ids, data


def validate_db_json(data: Dict, result: ValidationResult, task_ids: List[str]) -> List[str]:
    """Validate db.json structure and content."""
    context = "db.json"

    # Check structure
    if not isinstance(data, dict):
        result.add_error("Root element must be an object", context)
        return []

    if "qa_pairs" not in data:
        result.add_error("Missing 'qa_pairs' field", context)
        return []

    qa_pairs = data["qa_pairs"]
    if not isinstance(qa_pairs, dict):
        result.add_error("'qa_pairs' must be an object", context)
        return []

    result.add_stat("total_qa_pairs", len(qa_pairs))

    # Track QA pair IDs
    qa_ids = []
    qa_id_set = set()

    for qa_id, qa_data in qa_pairs.items():
        qa_ids.append(qa_id)
        if qa_id in qa_id_set:
            result.add_error(f"Duplicate QA pair ID: {qa_id}", context)
        qa_id_set.add(qa_id)

        # Validate QA pair structure
        if not isinstance(qa_data, dict):
            result.add_error(f"QA pair '{qa_id}' must be an object", context)
            continue

        # Check required fields
        required_fields = ["question", "answer", "task_id"]
        for field in required_fields:
            if field not in qa_data:
                result.add_error(f"QA pair '{qa_id}' missing field: '{field}'", context)

        # Validate question and answer are strings
        if "question" in qa_data and not isinstance(qa_data["question"], str):
            result.add_error(f"QA pair '{qa_id}' question must be a string", context)

        if "answer" in qa_data and qa_data["answer"] is not None and not isinstance(qa_data["answer"], str):
            result.add_error(f"QA pair '{qa_id}' answer must be a string or null", context)

        # Check task_id consistency
        if "task_id" in qa_data and qa_data["task_id"] != qa_id:
            result.add_warning(f"QA pair '{qa_id}' task_id '{qa_data['task_id']}' doesn't match key", context)

    # Check consistency with tasks.json
    if task_ids:
        task_set = set(task_ids)
        qa_set = set(qa_ids)

        missing_in_db = task_set - qa_set
        extra_in_db = qa_set - task_set

        if missing_in_db:
            result.add_error(f"{len(missing_in_db)} tasks in tasks.json not found in db.json: {', '.join(sorted(list(missing_in_db))[:5])}", context)

        if extra_in_db:
            result.add_warning(f"{len(extra_in_db)} QA pairs in db.json not found in tasks.json: {', '.join(sorted(list(extra_in_db))[:5])}", context)

        # Check matches
        if task_set == qa_set:
            result.add_stat("qa_task_consistency", "perfect_match")

    result.add_stat("unique_qa_pairs", len(qa_id_set))

    return qa_ids


def validate_policy_md(file_path: Path, result: ValidationResult) -> bool:
    """Validate policy.md exists and has content."""
    context = "policy.md"

    if not file_path.exists():
        result.add_warning("policy.md not found (optional file)", context)
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if len(content.strip()) == 0:
            result.add_warning("policy.md is empty", context)
        else:
            # Count lines and characters
            lines = content.split('\n')
            result.add_stat("policy_md_lines", len(lines))
            result.add_stat("policy_md_chars", len(content))
            return True
    except Exception as e:
        result.add_error(f"Error reading policy.md: {e}", context)

    return False


def validate_directory_structure(data_dir: Path, result: ValidationResult):
    """Validate that the directory structure matches expected format."""
    context = "directory_structure"

    required_files = ["tasks.json", "db.json"]
    optional_files = ["policy.md", "process_log_medxpertqa.txt", "MedXpertQA_raw_backup.zip"]

    # Check required files
    for file_name in required_files:
        file_path = data_dir / file_name
        if not file_path.exists():
            result.add_error(f"Required file not found: {file_name}", context)

    # List all files for reference
    all_files = list(data_dir.glob("*"))
    result.add_stat("total_files_in_dir", len(all_files))


def print_validation_summary(result: ValidationResult, verbose: bool = False):
    """Print validation summary."""
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    # Print statistics
    if result.stats:
        print("\n📊 STATISTICS:")
        for key, value in sorted(result.stats.items()):
            print(f"  • {key}: {value}")

    # Print errors
    print(f"\n❌ ERRORS: {len(result.errors)}")
    if result.errors:
        for error in result.errors[:20]:  # Show first 20
            print(f"  ✗ {error}")
        if len(result.errors) > 20:
            print(f"  ... and {len(result.errors) - 20} more errors")
    else:
        print("  ✓ No errors found")

    # Print warnings
    print(f"\n⚠️  WARNINGS: {len(result.warnings)}")
    if result.warnings:
        for warning in result.warnings[:20]:  # Show first 20
            print(f"  ⚠ {warning}")
        if len(result.warnings) > 20:
            print(f"  ... and {len(result.warnings) - 20} more warnings")
    else:
        print("  ✓ No warnings")

    # Final verdict
    print("\n" + "=" * 70)
    if result.passed:
        print("✅ VALIDATION PASSED")
        print("=" * 70)
        print("\nAll checks passed! The MedXpertQA dataset is properly formatted.")
    else:
        print("❌ VALIDATION FAILED")
        print("=" * 70)
        print("\nPlease fix the errors above before using this dataset.")
    print()


def compare_with_other_datasets(data_dir: Path, result: ValidationResult):
    """Compare structure with other tau2-bench datasets (airline, clinical)."""
    context = "cross_dataset_comparison"

    # Find other dataset directories
    project_root = data_dir.parent.parent  # Go up to data/
    airline_path = project_root / "tau2" / "domains" / "airline"
    clinical_path = project_root / "clinical"

    comparison_results = []

    # Check if we can compare with airline
    if airline_path.exists():
        airline_tasks = airline_path / "tasks.json"
        if airline_tasks.exists():
            try:
                with open(airline_tasks, 'r', encoding='utf-8') as f:
                    airline_data = json.load(f)
                if isinstance(airline_data, list) and len(airline_data) > 0:
                    # Compare structure
                    airline_fields = set(airline_data[0].keys())
                    comparison_results.append("airline: found for comparison")
            except:
                pass

    # Check if we can compare with clinical
    if clinical_path.exists():
        clinical_tasks = clinical_path / "tasks.json"
        if clinical_tasks.exists():
            try:
                with open(clinical_tasks, 'r', encoding='utf-8') as f:
                    clinical_data = json.load(f)
                if isinstance(clinical_data, list) and len(clinical_data) > 0:
                    clinical_fields = set(clinical_data[0].keys())
                    comparison_results.append("clinical: found for comparison")
            except:
                pass

    if comparison_results:
        result.add_stat("comparison_with_other_datasets", ", ".join(comparison_results))


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate MedXpertQA processed files against tau2-bench format"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=r"C:\Users\方正\tau2-bench\data\processed\medxpertqa",
        help="Path to MedXpertQA processed directory"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("MedXpertQA Validation Script")
    print("=" * 70)
    print(f"\nValidating: {args.data_dir}")
    print()

    result = ValidationResult()

    # Validate directory structure
    print("📁 Checking directory structure...")
    data_dir = Path(args.data_dir)
    validate_directory_structure(data_dir, result)

    # Validate tasks.json
    print("\n📄 Validating tasks.json...")
    tasks_path = data_dir / "tasks.json"
    tasks_data = validate_json_file(tasks_path, result, "tasks.json")
    task_ids = []
    if tasks_data:
        task_ids, tasks_list = validate_tasks_json(tasks_data, result)

    # Validate db.json
    print("\n📄 Validating db.json...")
    db_path = data_dir / "db.json"
    db_data = validate_json_file(db_path, result, "db.json")
    if db_data:
        validate_db_json(db_data, result, task_ids)

    # Validate policy.md
    print("\n📄 Validating policy.md...")
    policy_path = data_dir / "policy.md"
    validate_policy_md(policy_path, result)

    # Compare with other datasets
    print("\n🔄 Comparing with other tau2-bench datasets...")
    compare_with_other_datasets(data_dir, result)

    # Print summary
    print_validation_summary(result, args.verbose)

    # Sample data display
    if tasks_data and db_data and args.verbose:
        print("\n" + "=" * 70)
        print("SAMPLE DATA")
        print("=" * 70)

        if tasks_list:
            print("\n📋 Sample Task:")
            sample_task = tasks_list[0]
            print(f"  ID: {sample_task.get('id', 'N/A')}")
            print(f"  Purpose: {sample_task.get('description', {}).get('purpose', 'N/A')}")
            print(f"  Ticket (Question): {sample_task.get('ticket', 'N/A')[:100]}...")

        if db_data and "qa_pairs" in db_data:
            qa_pairs = db_data["qa_pairs"]
            if qa_pairs:
                first_id = list(qa_pairs.keys())[0]
                first_qa = qa_pairs[first_id]
                print("\n💬 Sample QA Pair:")
                print(f"  Task ID: {first_id}")
                print(f"  Question: {first_qa.get('question', 'N/A')[:100]}...")
                print(f"  Answer: {first_qa.get('answer', 'N/A')[:100]}...")
                print(f"  Domain: {first_qa.get('domain', 'N/A')}")

        print()

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
