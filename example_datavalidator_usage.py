#!/usr/bin/env python3
"""
Example script demonstrating how to use the DataValidator module.

This script shows various usage patterns:
- Validating a single dataset
- Validating multiple datasets
- Using the validator programmatically
- Customizing validation behavior
"""

import json
from pathlib import Path

# Import from DataValidator module
from DataValidator import MedicalDialogueValidator
from DataValidator.models import ValidationLevel


def example_1_basic_validation():
    """Example 1: Basic validation of a dataset."""
    print("\n" + "=" * 80)
    print("Example 1: Basic Validation")
    print("=" * 80)

    # Initialize validator
    validator = MedicalDialogueValidator(strict_mode=False)

    # Validate a dataset
    dataset_path = Path("data/tau2/domains/clinical/chinese_internal_medicine/tasks.json")

    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}")
        return

    result = validator.validate_dataset(dataset_path)

    # Check result
    if result.is_valid:
        print("✅ Dataset validation PASSED")
    else:
        print("❌ Dataset validation FAILED")
        print(f"   Errors: {len(result.errors)}")

    print(f"   Total tasks: {result.total_tasks}")
    print(f"   Warnings: {len(result.warnings)}")
    print(f"   Info: {len(result.infos)}")


def example_2_detailed_report():
    """Example 2: Print detailed validation report."""
    print("\n" + "=" * 80)
    print("Example 2: Detailed Report")
    print("=" * 80)

    validator = MedicalDialogueValidator()
    dataset_path = Path("data/tau2/domains/clinical/cardiology/tasks.json")

    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}")
        return

    result = validator.validate_dataset(dataset_path)

    # Print full report
    result.print_report(verbose=True)

    # Access specific statistics
    stats = result.stats
    print(f"\n📊 Key Statistics:")
    print(f"   Multi-turn tasks: {stats.get('multi_turn_tasks', 0)}")
    print(f"   Safety-related: {stats.get('safety_related_tasks', 0)}")
    print(f"   Avg ticket length: {stats.get('avg_ticket_length', 0):.1f}")


def example_3_batch_validation():
    """Example 3: Validate multiple clinical datasets."""
    print("\n" + "=" * 80)
    print("Example 3: Batch Validation")
    print("=" * 80)

    validator = MedicalDialogueValidator(strict_mode=False)

    # Define datasets to validate
    clinical_dir = Path("data/tau2/domains/clinical")

    # Find all tasks.json files
    datasets = list(clinical_dir.glob("*/tasks.json"))

    print(f"\nFound {len(datasets)} clinical datasets")

    results = {}
    for dataset_path in datasets:
        domain_name = dataset_path.parent.name
        print(f"\nValidating {domain_name}...")

        try:
            result = validator.validate_dataset(dataset_path)
            results[domain_name] = result

            status = "✅ VALID" if result.is_valid else "❌ INVALID"
            print(f"  {status}")
            print(f"  Tasks: {result.total_tasks}")
            print(f"  Issues: {len(result.issues)}")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            results[domain_name] = None

    # Summary
    print("\n" + "-" * 80)
    print("  BATCH VALIDATION SUMMARY")
    print("-" * 80)

    valid_count = sum(1 for r in results.values() if r and r.is_valid)
    print(f"  Valid datasets: {valid_count}/{len(results)}")
    print(f"  Total tasks validated: {sum(r.total_tasks for r in results.values() if r)}")


def example_4_strict_mode():
    """Example 4: Using strict mode."""
    print("\n" + "=" * 80)
    print("Example 4: Strict Mode")
    print("=" * 80)

    # Normal mode
    print("\nNormal mode:")
    validator_normal = MedicalDialogueValidator(strict_mode=False)
    dataset_path = Path("data/tau2/domains/clinical/threadmed_qa/tasks.json")

    if dataset_path.exists():
        result_normal = validator_normal.validate_dataset(dataset_path)
        print(f"  Valid: {result_normal.is_valid}")
        print(f"  Warnings: {len(result_normal.warnings)}")

    # Strict mode
    print("\nStrict mode (warnings become errors):")
    validator_strict = MedicalDialogueValidator(strict_mode=True)

    if dataset_path.exists():
        result_strict = validator_strict.validate_dataset(dataset_path)
        print(f"  Valid: {result_strict.is_valid}")
        print(f"  Errors: {len(result_strict.errors)}")


def example_5_programmatic_access():
    """Example 5: Programmatic access to validation results."""
    print("\n" + "=" * 80)
    print("Example 5: Programmatic Access")
    print("=" * 80)

    validator = MedicalDialogueValidator()
    dataset_path = Path("data/tau2/domains/clinical/neurology/tasks.json")

    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}")
        return

    result = validator.validate_dataset(dataset_path)

    # Access specific issues
    print("\n🔍 Issue Breakdown:")
    print(f"  Errors: {len(result.errors)}")
    for error in result.errors[:3]:  # Show first 3
        print(f"    - {error.category}: {error.message}")

    print(f"\n  Warnings: {len(result.warnings)}")
    for warning in result.warnings[:3]:
        print(f"    - {warning.category}: {warning.message}")

    # Access statistics
    stats = result.stats
    print(f"\n📊 Statistics:")
    print(f"  Domain: {stats.get('domain_distribution', {})}")
    print(f"  Multi-turn: {stats.get('multi_turn_tasks', 0)}")
    print(f"  Avg ticket length: {stats.get('avg_ticket_length', 0):.1f}")


def example_6_custom_validation():
    """Example 6: Validate tasks list directly."""
    print("\n" + "=" * 80)
    print("Example 6: Direct Task List Validation")
    print("=" * 80)

    # Create sample tasks
    sample_tasks = [
        {
            "id": "sample_1",
            "description": {
                "purpose": "Test task - patient with headache"
            },
            "user_scenario": {
                "persona": "Patient with headache",
                "instructions": {
                    "domain": "neurology",
                    "reason_for_call": "headache",
                    "known_info": "Has migraine",
                    "task_instructions": """Patient: I have a severe headache.
Doctor: How long have you had this headache?
Patient: For about 3 days now.
Doctor: Is the pain on one side or both?
Patient: Mostly on the right side."""
                }
            },
            "ticket": "I have a severe headache for the past 3 days, mostly on the right side.",
            "initial_state": {
                "initialization_actions": []
            },
            "evaluation_criteria": {
                "actions": [
                    {
                        "action_id": "provide_medical_advice",
                        "name": "provide_medical_advice"
                    }
                ]
            }
        },
        {
            "id": "sample_2",
            "description": {
                "purpose": "Test task - fever"
            },
            "user_scenario": {
                "persona": "Patient with fever",
                "instructions": {
                    "domain": "general",
                    "reason_for_call": "fever"
                }
            },
            "ticket": "I have a fever",
            "initial_state": {"initialization_actions": []},
            "evaluation_criteria": {"actions": []}
        }
    ]

    # Validate tasks list
    validator = MedicalDialogueValidator()
    result = validator.validate_tasks(sample_tasks)

    print(f"\nValidated {result.total_tasks} sample tasks")
    print(f"Valid: {result.is_valid}")
    print(f"Issues: {len(result.issues)}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  DataValidator Module - Usage Examples")
    print("=" * 80)

    # Run examples
    example_1_basic_validation()
    example_2_detailed_report()
    example_3_batch_validation()
    example_4_strict_mode()
    example_5_programmatic_access()
    example_6_custom_validation()

    print("\n" + "=" * 80)
    print("  Examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
