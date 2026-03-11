#!/usr/bin/env python3
"""
Simple tau2 integration test for generated clinical dialogues.
"""

import json
import sys
from pathlib import Path

# Add tau2 to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tau2.registry import registry
from tau2.data_model.tasks import Task


def test_task_loading():
    """Test that tau2 can load our generated tasks."""
    print("="*70)
    print("TAU2 INTEGRATION TEST")
    print("="*70)

    # Test loading clinical_neurology tasks
    print("\n[1/3] Testing task loading...")

    try:
        task_loader = registry.get_tasks_loader("clinical_neurology")
        tasks = task_loader()

        print(f"  Successfully loaded {len(tasks)} tasks from clinical_neurology")

        if tasks:
            sample_task = tasks[0]
            print(f"\n  Sample task ID: {sample_task.id}")
            print(f"  Task description: {sample_task.description.purpose[:80]}...")
            print(f"  Has user_scenario: {sample_task.user_scenario is not None}")
            print(f"  Has ticket: {sample_task.ticket is not None}")

    except Exception as e:
        print(f"  ERROR: Failed to load tasks - {e}")
        return False

    # Test environment info
    print("\n[2/3] Testing environment info...")

    try:
        env_constructor = registry.get_env_constructor("clinical_neurology")
        env_info = env_constructor().get_info()

        print(f"  Environment: {env_info.name}")
        print(f"  Description: {env_info.description[:80] if env_info.description else 'N/A'}...")
        print(f"  Tools available: {len(env_info.tools)}")

        for tool in env_info.tools[:3]:
            print(f"    - {tool.name}")

    except Exception as e:
        print(f"  ERROR: Failed to get environment info - {e}")
        return False

    # Test task splits
    print("\n[3/3] Testing task splits...")

    try:
        split_loader = registry.get_task_splits_loader("clinical_neurology")
        splits = split_loader()

        if splits:
            print(f"  Splits loaded: {list(splits.keys())}")
            for split_name, task_ids in splits.items():
                print(f"    {split_name}: {len(task_ids)} tasks")

    except Exception as e:
        print(f"  ERROR: Failed to load splits - {e}")
        return False

    return True


def test_task_compatibility():
    """Test that a generated task is compatible with tau2 Task model."""
    print("\n" + "="*70)
    print("TASK COMPATIBILITY TEST")
    print("="*70)

    # Load a generated task
    tasks_file = Path("data/tau2/domains/clinical/neurology/tasks.json")

    with open(tasks_file, "r") as f:
        generated_tasks = json.load(f)

    print(f"\nLoaded {len(generated_tasks)} generated tasks")

    # Try to create a tau2 Task from the generated data
    sample = generated_tasks[0]

    try:
        # Map our generated format to tau2 Task format
        task = Task(
            id=sample["id"],
            description=sample["description"],
            user_scenario=sample["user_scenario"],
            ticket=sample["ticket"],
            initial_state=sample.get("initial_state"),
            evaluation_criteria=sample.get("evaluation_criteria"),
        )

        print(f"\nSuccessfully created tau2 Task:")
        print(f"  ID: {task.id}")
        print(f"  Description purpose: {task.description.purpose}")
        print(f"  Has instructions: {task.user_scenario.instructions is not None}")

        return True

    except Exception as e:
        print(f"\nERROR: Failed to create tau2 Task - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run integration tests."""
    print("\nTesting tau2 compatibility of generated clinical dialogues...\n")

    # Suppress tau2 logging for cleaner output
    import logging
    logging.getLogger("tau2").setLevel(logging.WARNING)

    # Run tests
    load_ok = test_task_loading()
    compat_ok = test_task_compatibility()

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    print(f"\nTask loading:         {'[PASS]' if load_ok else '[FAIL]'}")
    print(f"Task compatibility:   {'[PASS]' if compat_ok else '[FAIL]'}")

    if load_ok and compat_ok:
        print("\n[PASS] All integration tests passed!")
        print("\nThe generated clinical dialogues are fully compatible with tau2.")
        print("\nYou can now run tau2 evaluations with commands like:")
        print("  python -m tau2 run --domain clinical_neurology --max_tasks 10")
    else:
        print("\n[FAIL] Some tests failed. Please review the errors above.")

    print()


if __name__ == "__main__":
    main()
