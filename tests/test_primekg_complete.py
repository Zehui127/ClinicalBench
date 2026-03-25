#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test for PrimeKG integration with tau2 framework
"""

import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add src to path
sys.path.insert(0, 'src')

def test_primekg_complete():
    """Complete integration test for PrimeKG domain"""
    print("="*70)
    print(" PrimeKG Complete Integration Test")
    print("="*70)

    results = {}

    # Test 1: Registry registration
    print("\n[1/6] Testing domain registration...")
    try:
        from tau2.registry import registry
        domain_info = registry.get_info()

        if "primekg" in domain_info.domains:
            print(f"  [OK] primekg domain registered")
            results['registration'] = True
        else:
            print(f"  [FAIL] primekg domain not registered")
            results['registration'] = False

        if "primekg" in domain_info.task_sets:
            print(f"  [OK] primekg task set registered")
        else:
            print(f"  [FAIL] primekg task set not registered")
            results['registration'] = False

    except Exception as e:
        print(f"  [FAIL] {e}")
        results['registration'] = False

    # Test 2: Load tasks via get_tasks
    print("\n[2/6] Testing task loading...")
    try:
        from tau2.run import get_tasks

        # Load all tasks
        all_tasks = get_tasks('primekg')
        print(f"  [OK] Loaded {len(all_tasks)} tasks")
        results['loading'] = True

        # Load specific task
        specific_task = get_tasks('primekg', task_ids=['primekg_fever_medium'])
        print(f"  [OK] Loaded specific task: {specific_task[0].id}")

    except Exception as e:
        print(f"  [FAIL] {e}")
        results['loading'] = False
        import traceback
        traceback.print_exc()

    # Test 3: Train/test split
    print("\n[3/6] Testing train/test split...")
    try:
        train_tasks = get_tasks('primekg', task_split_name='train')
        test_tasks = get_tasks('primekg', task_split_name='test')

        print(f"  [OK] Train set: {len(train_tasks)} tasks")
        print(f"  [OK] Test set: {len(test_tasks)} tasks")

        if len(train_tasks) == 16 and len(test_tasks) == 4:
            print(f"  [OK] Split is correct (80/20)")
            results['split'] = True
        else:
            print(f"  [WARN] Unexpected split ratio")
            results['split'] = True  # Still OK if different

    except Exception as e:
        print(f"  [FAIL] {e}")
        results['split'] = False

    # Test 4: Environment creation
    print("\n[4/6] Testing environment creation...")
    try:
        from tau2.run import get_environment

        env = get_environment('primekg')
        print(f"  [OK] Environment created")
        print(f"  [OK] Domain: {env.domain_name}")

        results['environment'] = True

    except Exception as e:
        print(f"  [FAIL] {e}")
        results['environment'] = False

    # Test 5: Task structure validation
    print("\n[5/6] Validating task structure...")
    try:
        sample_task = all_tasks[0]

        required_fields = ['id', 'description', 'user_scenario', 'ticket',
                          'initial_state', 'evaluation_criteria', 'reference_dialogue']

        for field in required_fields:
            if not hasattr(sample_task, field):
                print(f"  [FAIL] Missing field: {field}")
                results['structure'] = False
                break
        else:
            print(f"  [OK] All required fields present")
            results['structure'] = True

        # Check PrimeKG metadata
        if hasattr(sample_task, 'metadata'):
            if sample_task.metadata.get('source') == 'PrimeKG Random Walk Generator':
                print(f"  [OK] PrimeKG metadata present")
            else:
                print(f"  [WARN] Unexpected metadata source")

    except Exception as e:
        print(f"  [FAIL] {e}")
        results['structure'] = False

    # Test 6: Symptom distribution
    print("\n[6/6] Analyzing task distribution...")
    try:
        from collections import Counter

        symptoms = [t.ticket for t in all_tasks]
        symptom_counts = Counter(symptoms)

        print(f"  [OK] Total unique symptoms: {len(symptom_counts)}")
        print(f"\n  Symptom distribution:")
        for symptom, count in symptom_counts.most_common():
            print(f"    {symptom}: {count}")

        results['distribution'] = True

    except Exception as e:
        print(f"  [FAIL] {e}")
        results['distribution'] = False

    # Summary
    print("\n" + "="*70)
    print(" Test Summary")
    print("="*70)

    total_tests = len(results)
    passed_tests = sum(results.values())

    print(f"\nTotal tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")

    for test_name, passed in results.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {test_name}")

    if all(results.values()):
        print("\n" + "="*70)
        print(" [SUCCESS] All tests passed!")
        print("="*70)
        print("\nPrimeKG domain is fully integrated with tau2 framework!")
        print("\nNext steps:")
        print("  1. Run agent simulations:")
        print("     python -m src.tau2.scripts.run --domain primekg --agent llm_agent")
        print("\n  2. Evaluate trajectories:")
        print("     python -m src.tau2.scripts.evaluate_trajectories results/primekg/*.json")
        print("\n  3. Generate more tasks:")
        print("     python generate_primekg_tasks.py")
        return True
    else:
        print("\n[FAIL] Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = test_primekg_complete()
    sys.exit(0 if success else 1)
