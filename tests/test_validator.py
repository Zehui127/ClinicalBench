#!/usr/bin/env python3
"""
Test the Medical Dialogue Data Validator with example datasets.

This script demonstrates the validator's capabilities by testing it
against both valid and invalid medical dialogue datasets.
"""

import json
from pathlib import Path
from data_validator import MedicalDialogueValidator, ValidationLevel, ValidationResult


def create_chinese_medical_task(task_id: str) -> dict:
    """Create a valid Chinese medical consultation task."""
    return {
        "id": task_id,
        "description": {
            "purpose": "临床咨询 - 高血压患者",
            "relevant_policies": None,
            "notes": "多轮心脏科咨询"
        },
        "user_scenario": {
            "persona": "45岁高血压患者",
            "instructions": {
                "domain": "cardiology",
                "reason_for_call": "血压控制不佳",
                "known_info": "患者服用降压药但血压仍偏高",
                "unknown_info": None,
                "task_instructions": """您是一名寻求医疗建议的患者。

患者: 我有高血压，一直在吃降压药，但最近血压还是偏高。
医生: 您服用的是什么降压药？剂量多少？
患者: 我吃的是氨氯地平，每天一次，每次5毫克。
医生: 血压一般是多少？
患者: 早上起床量大约150/95，有时候更高一些。
医生: 有没有头痛、头晕或者其他不舒服的感觉？
患者: 偶尔会有点头晕，特别是站起来的时候。"""
            }
        },
        "ticket": "我有高血压，一直在吃降压药，但最近血压还是偏高。我吃的是氨氯地平，每天一次，每次5毫克。早上起床量大约150/95，偶尔会有点头晕。",
        "initial_state": {
            "initialization_actions": [
                {
                    "env_type": "user",
                    "func_name": "set_user_info",
                    "arguments": {
                        "name": "张伟",
                        "age": 45,
                        "gender": "male"
                    }
                }
            ]
        },
        "evaluation_criteria": {
            "actions": [
                {
                    "action_id": "assess_cardiovascular_risk",
                    "requestor": "assistant",
                    "name": "assess_cardiovascular_risk",
                    "arguments": {}
                }
            ],
            "communication_checks": [
                {
                    "check_id": "empathetic_response",
                    "criteria": "回应应表现出同理心和专业性"
                }
            ]
        }
    }


def create_valid_medical_task(task_id: str) -> dict:
    """Create a valid medical consultation task."""
    return {
        "id": task_id,
        "description": {
            "purpose": "Clinical consultation - patient with chest pain",
            "relevant_policies": None,
            "notes": "Multi-turn cardiac consultation"
        },
        "user_scenario": {
            "persona": "45-year-old patient with chest pain",
            "instructions": {
                "domain": "cardiology",
                "reason_for_call": "chest pain",
                "known_info": "Patient experiences chest pain during exercise",
                "unknown_info": None,
                "task_instructions": """You are a patient seeking medical advice.

Patient: I've been having chest pain when I exercise for the past week.
Physician: Can you describe the pain? Is it sharp or dull?
Patient: It's more like a pressure, right in the center of my chest.
Physician: Does the pain radiate to your arm or jaw?
Patient: Sometimes I feel it in my left shoulder.
Physician: Any shortness of breath or sweating?
Patient: A little bit of shortness when I climb stairs."""
            }
        },
        "ticket": "I've been having chest pain when I exercise for the past week. It's a pressure in the center of my chest and sometimes radiates to my left shoulder.",
        "initial_state": {
            "initialization_actions": [
                {
                    "env_type": "user",
                    "func_name": "set_user_info",
                    "arguments": {
                        "name": "Jane Smith",
                        "age": 45,
                        "gender": "female"
                    }
                }
            ]
        },
        "evaluation_criteria": {
            "actions": [
                {
                    "action_id": "assess_cardiovascular_risk",
                    "requestor": "assistant",
                    "name": "assess_cardiovascular_risk",
                    "arguments": {}
                }
            ],
            "communication_checks": [
                {
                    "check_id": "empathetic_response",
                    "criteria": "Response should show empathy and professionalism"
                }
            ]
        }
    }


def create_invalid_task_missing_fields(task_id: str) -> dict:
    """Create a task with missing required fields."""
    return {
        "id": task_id,
        "description": {
            "purpose": "Incomplete task"
        }
        # Missing: user_scenario, ticket, evaluation_criteria
    }


def create_non_medical_task(task_id: str) -> dict:
    """Create a task that's not medical-related."""
    return {
        "id": task_id,
        "description": {
            "purpose": "Technical support consultation"
        },
        "user_scenario": {
            "persona": "Computer user",
            "instructions": {
                "domain": "technical_support",
                "reason_for_call": "computer not working",
                "known_info": "Computer won't turn on",
                "unknown_info": None,
                "task_instructions": "User: My computer won't turn on"
            }
        },
        "ticket": "My computer is broken and I need help fixing it",
        "initial_state": {
            "initialization_actions": []
        },
        "evaluation_criteria": {
            "actions": []
        }
    }


def create_single_turn_task(task_id: str) -> dict:
    """Create a single-turn task (lacks multi-turn structure)."""
    return {
        "id": task_id,
        "description": {
            "purpose": "Simple medical question"
        },
        "user_scenario": {
            "persona": "Patient with a question",
            "instructions": {
                "domain": "general",
                "reason_for_call": "medication question",
                "known_info": "Patient wants to know about medication",
                "unknown_info": None,
                "task_instructions": "Single question only"
            }
        },
        "ticket": "Can I take ibuprofen with food?",
        "initial_state": {
            "initialization_actions": []
        },
        "evaluation_criteria": {
            "actions": [
                {
                    "action_id": "provide_medical_advice",
                    "requestor": "assistant",
                    "name": "provide_medical_advice",
                    "arguments": {}
                }
            ]
        }
    }


def run_validation_tests():
    """Run validation tests on various datasets."""
    print("\n" + "=" * 80)
    print("  MEDICAL DIALOGUE VALIDATOR - TEST SUITE")
    print("=" * 80 + "\n")

    validator = MedicalDialogueValidator(strict_mode=False)

    # Test 1: Valid medical dialogue dataset
    print("Test 1: Valid Multi-turn Medical Dialogue Dataset")
    print("-" * 80)
    valid_dataset = [
        create_valid_medical_task(f"valid_task_{i}")
        for i in range(1, 6)
    ]

    test_file_1 = Path("test_valid_dataset.json")
    with open(test_file_1, "w", encoding="utf-8") as f:
        json.dump(valid_dataset, f, indent=2, ensure_ascii=False)

    result_1 = validator.validate_dataset(test_file_1)
    result_1.print_report()

    # Clean up
    test_file_1.unlink()

    # Test 2: Dataset with missing fields
    print("\nTest 2: Dataset with Missing Required Fields")
    print("-" * 80)
    invalid_dataset = [
        create_invalid_task_missing_fields(f"invalid_task_{i}")
        for i in range(1, 4)
    ]

    test_file_2 = Path("test_invalid_dataset.json")
    with open(test_file_2, "w", encoding="utf-8") as f:
        json.dump(invalid_dataset, f, indent=2, ensure_ascii=False)

    result_2 = validator.validate_dataset(test_file_2)
    result_2.print_report()

    # Clean up
    test_file_2.unlink()

    # Test 3: Chinese medical dataset
    print("\nTest 3: Chinese Medical Consultation Dataset (Bilingual Support)")
    print("-" * 80)
    chinese_dataset = [
        create_chinese_medical_task(f"chinese_task_{i}")
        for i in range(1, 6)
    ]

    test_file_3 = Path("test_chinese_dataset.json")
    with open(test_file_3, "w", encoding="utf-8") as f:
        json.dump(chinese_dataset, f, indent=2, ensure_ascii=False)

    result_3 = validator.validate_dataset(test_file_3)
    result_3.print_report()

    # Clean up
    test_file_3.unlink()

    # Test 4: Non-medical dataset
    print("\nTest 4: Non-Medical Dataset (Should Have Warnings)")
    print("-" * 80)
    non_medical_dataset = [
        create_non_medical_task(f"tech_task_{i}")
        for i in range(1, 4)
    ]

    test_file_4 = Path("test_non_medical_dataset.json")
    with open(test_file_4, "w", encoding="utf-8") as f:
        json.dump(non_medical_dataset, f, indent=2, ensure_ascii=False)

    result_4 = validator.validate_dataset(test_file_4)
    result_4.print_report()

    # Clean up
    test_file_4.unlink()

    # Test 5: Mixed quality dataset
    print("\nTest 5: Mixed Quality Dataset (Valid + Invalid + Single-turn)")
    print("-" * 80)
    mixed_dataset = [
        create_valid_medical_task(f"mixed_valid_{i}") for i in range(1, 4)
    ] + [
        create_single_turn_task(f"mixed_single_{i}") for i in range(1, 4)
    ] + [
        create_invalid_task_missing_fields(f"mixed_invalid_{i}") for i in range(1, 3)
    ]

    test_file_5 = Path("test_mixed_dataset.json")
    with open(test_file_5, "w", encoding="utf-8") as f:
        json.dump(mixed_dataset, f, indent=2, ensure_ascii=False)

    result_5 = validator.validate_dataset(test_file_5)
    result_5.print_report()

    # Clean up
    test_file_5.unlink()

    # Test 6: Validate actual threadmed_qa dataset
    print("\nTest 6: Actual ThReadMed-QA Dataset")
    print("-" * 80)
    threadmed_file = Path("data/tau2/domains/clinical/threadmed_qa/tasks.json")

    if threadmed_file.exists():
        result_6 = validator.validate_dataset(threadmed_file)
        result_6.print_report()
    else:
        print(f"File not found: {threadmed_file}")
        result_6 = None

    # Test 7: Validate Chinese MedDialog dataset
    print("\nTest 7: Chinese MedDialog Dataset (Bilingual Support)")
    print("-" * 80)
    chinese_file = Path("data/tau2/domains/clinical/chinese_internal_medicine/tasks.json")

    if chinese_file.exists():
        result_7 = validator.validate_dataset(chinese_file)
        result_7.print_report()
    else:
        print(f"File not found: {chinese_file}")
        result_7 = None

    # Summary
    print("\n" + "=" * 80)
    print("  TEST SUMMARY")
    print("=" * 80)
    print(f"\nTests completed:")
    print(f"  Test 1 (Valid Medical): {'[PASS]' if result_1.is_valid else '[FAIL]'}")
    print(f"  Test 2 (Missing Fields): {'[Expected FAIL]' if not result_2.is_valid else '[Unexpected]'}")
    print(f"  Test 3 (Chinese Medical): {'[PASS]' if result_3.is_valid else '[FAIL]'} (Bilingual)")
    print(f"  Test 4 (Non-Medical): {'[Has Warnings]' if result_4.warnings else '[No Warnings]'}")
    print(f"  Test 5 (Mixed): {'[Has Issues]' if result_5.errors or result_5.warnings else '[No Issues]'}")

    if result_6:
        print(f"  Test 6 (ThReadMed-QA): {'[Valid]' if result_6.is_valid else '[Has Issues]'} ({result_6.total_tasks} tasks)")
    if result_7:
        print(f"  Test 7 (Chinese MedDialog): {'[Valid]' if result_7.is_valid else '[Has Issues]'} ({result_7.total_tasks} tasks)")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    run_validation_tests()
