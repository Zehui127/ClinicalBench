#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick start script for PrimeKG integration test
Run this to verify PrimeKG tasks are working correctly
"""

import sys
sys.path.insert(0, 'src')

def main():
    print("\n" + "="*70)
    print(" PrimeKG Quick Start Test")
    print("="*70)

    # Test 1: Import and load tasks
    print("\n[1/3] Loading PrimeKG tasks...")
    try:
        from tau2.run import get_tasks
        tasks = get_tasks('primekg')
        print(f"  [OK] Loaded {len(tasks)} tasks")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

    # Test 2: Display sample task
    print("\n[2/3] Displaying sample task...")
    try:
        sample_task = tasks[0]
        print(f"  Task ID: {sample_task.id}")
        print(f"  Ticket: {sample_task.ticket}")
        print(f"  Purpose: {sample_task.description.purpose}")
        print(f"  Patient: {sample_task.user_scenario.persona}")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

    # Test 3: Test train/test split
    print("\n[3/3] Testing train/test split...")
    try:
        train_tasks = get_tasks('primekg', task_split_name='train')
        test_tasks = get_tasks('primekg', task_split_name='test')
        print(f"  [OK] Train: {len(train_tasks)} tasks")
        print(f"  [OK] Test: {len(test_tasks)} tasks")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

    # Success!
    print("\n" + "="*70)
    print(" [SUCCESS] PrimeKG is ready to use!")
    print("="*70)
    print("\nQuick usage examples:")
    print("\n1. Load all tasks:")
    print("   from tau2.run import get_tasks")
    print("   tasks = get_tasks('primekg')")
    print("\n2. Load training set:")
    print("   train = get_tasks('primekg', task_split_name='train')")
    print("\n3. Load specific task:")
    print("   task = get_tasks('primekg', task_ids=['primekg_fever_medium'])")
    print("\nFor more information, see: PRIMEKG_INTEGRATION_COMPLETE.md")
    print()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
