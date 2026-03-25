#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test PrimeKG tasks integration with tau2 framework
"""

import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def test_primekg_tasks():
    """Test that PrimeKG tasks can be loaded and used in tau2 framework"""
    print("="*70)
    print(" PrimeKG Tasks Integration Test")
    print("="*70)

    # Test 1: Load tasks.json
    print("\n[1/4] Loading tasks.json...")
    tasks_file = Path("data/tau2/domains/clinical/primekg/tasks.json")
    if not tasks_file.exists():
        print(f"  [FAIL] File not found: {tasks_file}")
        return False

    import json
    with open(tasks_file, 'r', encoding='utf-8') as f:
        tasks_data = json.load(f)

    print(f"  [OK] Loaded {len(tasks_data)} tasks")

    # Test 2: Validate task structure
    print("\n[2/4] Validating task structure...")
    required_fields = ['id', 'description', 'user_scenario', 'ticket', 'initial_state',
                      'evaluation_criteria', 'reference_dialogue', 'metadata']

    for i, task in enumerate(tasks_data):
        for field in required_fields:
            if field not in task:
                print(f"  [FAIL] Task {task['id']} missing field: {field}")
                return False
        print(f"  [OK] Task {i+1}/{len(tasks_data)}: {task['id']}")

    # Test 3: Check metadata
    print("\n[3/4] Checking PrimeKG metadata...")
    for task in tasks_data:
        metadata = task.get('metadata', {})
        if 'source' not in metadata:
            print(f"  [FAIL] Task {task['id']} missing metadata.source")
            return False
        if metadata.get('source') != 'PrimeKG Random Walk Generator':
            print(f"  [WARN] Task {task['id']} has unexpected source: {metadata.get('source')}")

        if 'primekg_path_length' not in metadata:
            print(f"  [FAIL] Task {task['id']} missing primekg_path_length")
            return False

    print(f"  [OK] All tasks have valid PrimeKG metadata")

    # Test 4: Test tau2 loading (if available)
    print("\n[4/4] Testing tau2 framework loading...")
    try:
        from tau2.run import get_tasks

        # Try loading a few PrimeKG tasks
        sample_task_ids = [t['id'] for t in tasks_data[:3]]
        loaded_tasks = get_tasks("primekg", task_ids=sample_task_ids)

        if len(loaded_tasks) != len(sample_task_ids):
            print(f"  [WARN] Expected {len(sample_task_ids)} tasks, got {len(loaded_tasks)}")
        else:
            print(f"  [OK] Successfully loaded {len(loaded_tasks)} tasks via tau2 framework")

        # Display first task details
        if loaded_tasks:
            first_task = loaded_tasks[0]
            print(f"\n  Sample task: {first_task.id}")
            print(f"  Domain: clinical/primekg")
            print(f"  Ticket: {first_task.ticket}")

    except ImportError as e:
        print(f"  [SKIP] Could not import tau2 framework: {e}")
        print(f"  [INFO] This is OK if tau2 is not in the Python path")
    except Exception as e:
        print(f"  [FAIL] Error loading via tau2 framework: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("\n" + "="*70)
    print(" Test Summary")
    print("="*70)
    print(f"Total tasks: {len(tasks_data)}")
    print(f"Structure validation: PASSED")
    print(f"Metadata validation: PASSED")

    # Symptom distribution
    from collections import Counter
    symptoms = [t['user_scenario']['instructions']['reason_for_call'] for t in tasks_data]
    symptom_counts = Counter(symptoms)

    print(f"\nSymptom distribution:")
    for symptom, count in symptom_counts.most_common():
        print(f"  {symptom}: {count}")

    print("\n" + "="*70)
    print(" [SUCCESS] All tests passed!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Run agent simulations on these tasks")
    print("  2. Evaluate agent performance")
    print("  3. Generate more tasks if needed")

    return True


if __name__ == "__main__":
    success = test_primekg_tasks()
    sys.exit(0 if success else 1)
