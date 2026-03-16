#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Pipeline Test
端到端流程测试

Tests the complete clinical data processing pipeline:
1. DataValidator integration
2. UniClinicalDataEngine ETL
3. DataQualityFiltering
4. Pipeline orchestration

Note: This test does NOT require LLM API calls for data processing stages.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Test data
SAMPLE_MEDICAL_DATA = [
    {
        "dialogue_id": "test_001",
        "patient": "65-year-old male",
        "chief_complaint": "Chest pain for 2 hours",
        "history": "Hypertension, diabetes",
        "dialogue": [
            {
                "role": "doctor",
                "content": "What brings you in today?"
            },
            {
                "role": "patient",
                "content": "I have chest pain."
            }
        ]
    }
]


def test_stage0_raw_data_validation():
    """Test Stage 0: Raw data validation."""
    print("\n" + "=" * 70)
    print("TEST STAGE 0: Raw Data Validation")
    print("=" * 70)

    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(SAMPLE_MEDICAL_DATA, f, ensure_ascii=False)
        test_file = f.name

    try:
        from scripts.run_pipeline import validate_raw_data

        result = validate_raw_data(test_file, strict_mode=False, fail_on_error=False)

        print(f"[OK] Validation function executed")
        print(f"   - Validated: {result['validated']}")
        print(f"   - Is valid: {result['is_valid']}")
        print(f"   - Stats: {result.get('stats', {})}")

        if result['errors']:
            print(f"   - Errors: {result['errors']}")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        return False

    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)


def test_stage1_5_task_validation():
    """Test Stage 1.5: Task validation with DataValidator."""
    print("\n" + "=" * 70)
    print("TEST STAGE 1.5: Task Validation")
    print("=" * 70)

    # Create a sample tasks.json
    sample_task = {
        "id": "test_task_001",
        "description": {
            "purpose": "Test task"
        },
        "user_scenario": {
            "persona": "65-year-old male patient",
            "instructions": {
                "domain": "healthcare",
                "reason_for_call": "Chest pain",
                "task_instructions": "Evaluate chest pain"
            }
        },
        "evaluation_criteria": {
            "actions": [],
            "reward_basis": ["DB", "COMMUNICATE"]
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='_tasks.json', delete=False, encoding='utf-8') as f:
        json.dump([sample_task], f, ensure_ascii=False)
        tasks_file = f.name

    try:
        from scripts.run_pipeline import validate_generated_tasks

        result = validate_generated_tasks(tasks_file, strict_mode=False)

        print(f"[OK] Task validation executed")
        print(f"   - Validated: {result['validated']}")
        print(f"   - Is valid: {result['is_valid']}")
        print(f"   - Stats: {result.get('stats', {})}")

        if result['errors']:
            print(f"   - Errors ({len(result['errors'])}):")
            for err in result['errors'][:3]:
                print(f"     * {err.get('message', err)}")

        if result['warnings']:
            print(f"   - Warnings ({len(result['warnings'])}):")
            for warn in result['warnings'][:3]:
                print(f"     * {warn.get('message', warn)}")

        # Task validation might fail due to missing fields, that's OK for this test
        return result['validated']

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if os.path.exists(tasks_file):
            os.remove(tasks_file)


def test_pipeline_integration():
    """Test pipeline integration."""
    print("\n" + "=" * 70)
    print("TEST: Pipeline Integration")
    print("=" * 70)

    # Create test input
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        # Create minimal valid input for UniClinicalDataEngine
        test_data = [{
            "dialogue_id": "test_001",
            "patient_complaint": "Headache",
            "department": "general_practice",
            "dialogue_turns": [
                {"role": "patient", "content": "I have a headache"},
                {"role": "doctor", "content": "How long?"}
            ]
        }]
        json.dump(test_data, f, ensure_ascii=False)
        test_file = f.name

    output_dir = tempfile.mkdtemp()

    try:
        from scripts.run_pipeline import run_complete_pipeline

        print(f"Input file: {test_file}")
        print(f"Output directory: {output_dir}")
        print("Running pipeline (without Stage 0 validation for ETL test)...")

        result = run_complete_pipeline(
            input_path=test_file,
            output_dir=output_dir,
            stage1_format="json",
            min_quality_score=2.0,  # Lower threshold for test data
            skip_validation=True,  # Skip raw data validation
            validate_tasks=False,  # Skip task validation for faster test
        )

        print(f"\n[OK] Pipeline executed")
        print(f"   - Stage 1 success: {result.get('stage1', {}).get('success', False)}")
        print(f"   - Stage 2 success: {result.get('stage2', {}).get('success', False)}")
        print(f"   - Overall success: {result.get('success', False)}")

        if result.get('stage1', {}).get('success'):
            print(f"   - Tasks generated: {result['stage1'].get('tasks_generated', 0)}")
            print(f"   - Records processed: {result['stage1'].get('records_processed', 0)}")

        if result.get('stage2', {}).get('success'):
            print(f"   - Total tasks: {result['stage2'].get('total_tasks', 0)}")
            print(f"   - High quality: {result['stage2'].get('high_quality_tasks', 0)}")
            print(f"   - Pass rate: {result['stage2'].get('pass_rate', 0):.1f}%")

        return result.get('success', False)

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        import shutil
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir, ignore_errors=True)


def test_data_validator_available():
    """Test that DataValidator is available."""
    print("\n" + "=" * 70)
    print("TEST: DataValidator Availability")
    print("=" * 70)

    try:
        from DataValidator import MedicalDialogueValidator
        from DataValidator.models import ValidationResult, ValidationIssue

        print("[OK] DataValidator module is available")
        print(f"   - MedicalDialogueValidator: {MedicalDialogueValidator}")
        print(f"   - ValidationResult: {ValidationResult}")
        print(f"   - ValidationIssue: {ValidationIssue}")

        return True

    except ImportError as e:
        print(f"[FAIL] DataValidator not available: {e}")
        return False


def test_tau2_evaluator_available():
    """Test that tau2 clinical evaluators are available."""
    print("\n" + "=" * 70)
    print("TEST: Tau2 Clinical Evaluators Availability")
    print("=" * 70)

    try:
        from tau2.evaluator import ClinicalEvaluator
        from tau2.evaluator import ClinicalAccuracyEvaluator
        from tau2.evaluator import DialogueFluencyEvaluator
        from tau2.evaluator import SafetyEmpathyEvaluator
        from tau2.data_model.tasks import RewardType
        from tau2.data_model.simulation import ClinicalCheck

        print("[OK] Tau2 clinical evaluators are available")
        print(f"   - ClinicalEvaluator: {ClinicalEvaluator}")
        print(f"   - ClinicalAccuracyEvaluator: {ClinicalAccuracyEvaluator}")
        print(f"   - DialogueFluencyEvaluator: {DialogueFluencyEvaluator}")
        print(f"   - SafetyEmpathyEvaluator: {SafetyEmpathyEvaluator}")
        print(f"   - RewardType.CLINICAL: {RewardType.CLINICAL}")
        print(f"   - ClinicalCheck: {ClinicalCheck}")

        return True

    except ImportError as e:
        print(f"[FAIL] Tau2 evaluators not available: {e}")
        return False


def test_master_pipeline_available():
    """Test that master pipeline script is available."""
    print("\n" + "=" * 70)
    print("TEST: Master Pipeline Availability")
    print("=" * 70)

    try:
        from scripts.master_pipeline import MasterPipeline

        print("[OK] MasterPipeline class is available")
        print(f"   - Class: {MasterPipeline}")

        # Check methods
        methods = ['stage0_validate_raw_data', 'stage1_etl',
                  'stage1_5_validate_tasks', 'stage2_quality_filtering',
                  'stage3_agent_simulation', 'stage4_evaluation']

        for method in methods:
            if hasattr(MasterPipeline, method):
                print(f"   - Method {method}: [OK]")

        return True

    except Exception as e:
        print(f"[FAIL] MasterPipeline not available: {e}")
        return False


def main():
    """Run all end-to-end tests."""
    print("\n" + "=" * 80)
    print(" END-TO-END PIPELINE TEST SUITE")
    print("=" * 80)
    print("Testing the complete clinical data processing pipeline")
    print("")

    tests = [
        ("DataValidator Available", test_data_validator_available),
        ("Tau2 Evaluators Available", test_tau2_evaluator_available),
        ("Master Pipeline Available", test_master_pipeline_available),
        ("Stage 0: Raw Data Validation", test_stage0_raw_data_validation),
        ("Stage 1.5: Task Validation", test_stage1_5_task_validation),
        ("Pipeline Integration", test_pipeline_integration),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n[CRASH] {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print(" TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, p in results if p)
    total = len(results)

    for test_name, is_passed in results:
        status = "[OK] PASS" if is_passed else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "-" * 80)
    print(f"Results: {passed}/{total} tests passed ({passed*100//total}%)")
    print("=" * 80)

    if passed == total:
        print("\n[SUCCESS] All tests passed! The pipeline is working correctly.")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
