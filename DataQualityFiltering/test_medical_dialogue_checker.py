#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Medical Dialogue Checker
医学对话检测模块测试脚本
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, parent_dir)
sys.path.insert(0, str(Path(__file__).parent))

from DataQualityFiltering.validators.medical_dialogue_validator import (
    MedicalDialogueValidator,
    MedicalDialoguePipeline,
)


def test_validator():
    """Test the MedicalDialogueValidator."""
    print("=" * 70)
    print("TEST: MedicalDialogueValidator")
    print("=" * 70)

    # Create validator
    validator = MedicalDialogueValidator(
        min_medical_keywords=2,
        min_dialogue_turns=2
    )

    print(f"[OK] Validator created")
    print(f"  - Medical keywords: {len(validator.all_keywords)}")

    # Test medical dialogue task
    medical_task = {
        "id": "test_001",
        "description": {"purpose": "高血压咨询"},
        "ticket": "医生，我最近血压有点高",
        "user_scenario": {
            "role": "医生",
            "instructions": {
                "task_instructions": "Patient: 医生，我最近血压有点高\nDoctor: 您好，请问您的血压是多少？"
            }
        },
        "evaluation_criteria": ["询问血压"]
    }

    # Test validation
    is_valid, issues = validator.validate(medical_task)
    print(f"\n[OK] Validation test:")
    print(f"  - Valid: {is_valid}")
    print(f"  - Issues: {len(issues)}")

    # Test medical score
    score = validator.calculate_medical_score(medical_task)
    print(f"\n[OK] Medical relevance score: {score:.3f}")

    # Test is_medical_dialogue
    is_medical = validator.is_medical_dialogue(medical_task)
    print(f"[OK] Is medical dialogue: {is_medical}")

    # Test non-medical task
    non_medical_task = {
        "id": "test_002",
        "description": {"purpose": "烹饪问题"},
        "ticket": "如何做蛋糕？",
        "user_scenario": {
            "role": "厨师",
            "instructions": {"task_instructions": "User: 如何做蛋糕？"}
        },
        "evaluation_criteria": []
    }

    is_medical_non = validator.is_medical_dialogue(non_medical_task)
    print(f"\n[OK] Non-medical task detected correctly: {not is_medical_non}")

    return True


def test_pipeline():
    """Test the MedicalDialoguePipeline."""
    print("\n" + "=" * 70)
    print("TEST: MedicalDialoguePipeline")
    print("=" * 70)

    # Create pipeline
    pipeline = MedicalDialoguePipeline(
        min_medical_keywords=2,
        min_dialogue_turns=2
    )

    print(f"[OK] Pipeline created")

    # Test tasks
    tasks = [
        {
            "id": "test_001",
            "description": {"purpose": "高血压咨询"},
            "ticket": "医生，我最近血压有点高",
            "user_scenario": {
                "role": "医生",
                "instructions": {
                    "task_instructions": "Patient: 医生，我最近血压有点高\nDoctor: 您好，请问您的血压是多少？"
                }
            },
            "evaluation_criteria": ["询问血压"]
        },
        {
            "id": "test_002",
            "description": {"purpose": "烹饪问题"},
            "ticket": "如何做蛋糕？",
            "user_scenario": {
                "role": "厨师",
                "instructions": {"task_instructions": "User: 如何做蛋糕？"}
            },
            "evaluation_criteria": []
        },
    ]

    # Validate tasks
    summary = pipeline.validate_tasks(tasks)

    print(f"\n[OK] Batch validation:")
    print(f"  - Total tasks: {summary['total_tasks']}")
    print(f"  - Valid tasks: {summary['valid_tasks']}")
    print(f"  - Invalid tasks: {summary['invalid_tasks']}")
    print(f"  - Validity rate: {summary['validity_rate']:.2%}")
    print(f"  - Avg medical score: {summary['avg_medical_score']:.3f}")

    return True


def test_filter():
    """Test filtering valid and invalid dialogues."""
    print("\n" + "=" * 70)
    print("TEST: Filter Valid/Invalid Dialogues")
    print("=" * 70)

    pipeline = MedicalDialoguePipeline()

    tasks = [
        {
            "id": "medical_001",
            "description": {"purpose": "医疗咨询"},
            "ticket": "医生，我头痛",
            "user_scenario": {
                "role": "医生",
                "instructions": {
                    "task_instructions": "Patient: 医生，我头痛\nDoctor: 请描述症状"
                }
            },
            "evaluation_criteria": ["询问症状"]
        },
        {
            "id": "non_medical_001",
            "description": {"purpose": "非医疗"},
            "ticket": "如何编程？",
            "user_scenario": {
                "role": "程序员",
                "instructions": {"task_instructions": "User: 如何编程？"}
            },
            "evaluation_criteria": []
        },
    ]

    valid, invalid = pipeline.filter_valid_dialogues(tasks)

    print(f"[OK] Filtering complete:")
    print(f"  - Valid tasks: {len(valid)}")
    print(f"  - Invalid tasks: {len(invalid)}")

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("MEDICAL DIALOGUE CHECKER - TEST SUITE")
    print("=" * 70 + "\n")

    tests = [
        ("Validator", test_validator),
        ("Pipeline", test_pipeline),
        ("Filter", test_filter),
    ]

    results = {}
    for name, test_func in tests:
        try:
            success = test_func()
            results[name] = "PASSED" if success else "FAILED"
        except Exception as e:
            results[name] = f"ERROR: {e}"
            import traceback
            traceback.print_exc()

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for name, result in results.items():
        status = "[OK]" if result == "PASSED" else "[FAIL]"
        print(f"{status} {name}: {result}")

    all_passed = all(r == "PASSED" for r in results.values())
    print("\n" + "=" * 70)
    if all_passed:
        print("ALL TESTS PASSED [OK]")
    else:
        print("SOME TESTS FAILED [FAIL]")
    print("=" * 70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
