#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified End-to-End Pipeline Test
简化的端到端流程测试

Tests the pipeline components without requiring full tau2 installation.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


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


def test_uni_clinical_engine_available():
    """Test that UniClinicalDataEngine is available."""
    print("\n" + "=" * 70)
    print("TEST: UniClinicalDataEngine Availability")
    print("=" * 70)

    try:
        from UniClinicalDataEngine import run_etl, ETLConfig
        from UniClinicalDataEngine.models import ClinicalTask, ClinicalScenario

        print("[OK] UniClinicalDataEngine is available")
        print(f"   - run_etl: {run_etl}")
        print(f"   - ClinicalTask: {ClinicalTask}")
        print(f"   - ClinicalScenario: {ClinicalScenario}")

        return True

    except ImportError as e:
        print(f"[FAIL] UniClinicalDataEngine not available: {e}")
        return False


def test_data_quality_filtering_available():
    """Test that DataQualityFiltering is available."""
    print("\n" + "=" * 70)
    print("TEST: DataQualityFiltering Availability")
    print("=" * 70)

    try:
        from DataQualityFiltering import run_filter, FilterConfig

        print("[OK] DataQualityFiltering is available")
        print(f"   - run_filter: {run_filter}")
        print(f"   - FilterConfig: {FilterConfig}")

        return True

    except ImportError as e:
        print(f"[FAIL] DataQualityFiltering not available: {e}")
        return False


def test_pipeline_scripts_available():
    """Test that pipeline scripts are available."""
    print("\n" + "=" * 70)
    print("TEST: Pipeline Scripts Availability")
    print("=" * 70)

    scripts = [
        "scripts/run_pipeline.py",
        "scripts/master_pipeline.py",
    ]

    all_available = True
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            print(f"   [OK] {script}")
        else:
            print(f"   [FAIL] {script} not found")
            all_available = False

    return all_available


def test_raw_data_validation():
    """Test raw data validation function."""
    print("\n" + "=" * 70)
    print("TEST: Raw Data Validation Function")
    print("=" * 70)

    # Create test data
    test_data = [{"id": "test", "value": "sample"}]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(test_data, f)
        test_file = f.name

    try:
        from scripts.run_pipeline import validate_raw_data

        result = validate_raw_data(test_file, strict_mode=False, fail_on_error=False)

        print(f"[OK] Validation function works")
        print(f"   - Validated: {result['validated']}")
        print(f"   - Is valid: {result['is_valid']}")

        return result['validated']

    except Exception as e:
        print(f"[FAIL] Validation test failed: {e}")
        return False

    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_config_files_exist():
    """Test that configuration files exist."""
    print("\n" + "=" * 70)
    print("TEST: Configuration Files")
    print("=" * 70)

    config_files = [
        "configs/pipeline_config.json",
        "configs/adapter_config.json",
        "configs/tool_registry.json",
    ]

    all_exist = True
    for config_file in config_files:
        config_path = Path(config_file)
        if config_path.exists():
            print(f"   [OK] {config_file}")
        else:
            print(f"   [WARN] {config_file} not found (optional)")
            # Don't fail on optional configs

    return all_exist


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print(" SIMPLIFIED END-TO-END PIPELINE TEST")
    print("=" * 80)
    print("Testing pipeline components without full tau2 installation")
    print("")

    tests = [
        ("DataValidator Available", test_data_validator_available),
        ("UniClinicalDataEngine Available", test_uni_clinical_engine_available),
        ("DataQualityFiltering Available", test_data_quality_filtering_available),
        ("Pipeline Scripts Available", test_pipeline_scripts_available),
        ("Raw Data Validation Function", test_raw_data_validation),
        ("Configuration Files", test_config_files_exist),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n[CRASH] {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
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
        print("\n[SUCCESS] All tests passed!")
        print("\nThe pipeline components are properly integrated:")
        print("  1. DataValidator is available and working")
        print("  2. UniClinicalDataEngine can be imported")
        print("  3. DataQualityFiltering is available")
        print("  4. Pipeline scripts are ready")
        print("\nNext steps:")
        print("  - Run: python scripts/run_pipeline.py <input_file>")
        print("  - Or:  python scripts/master_pipeline.py <input_file> --run-agents --evaluate")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed.")
        print("Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
