#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert all_tasks.json (20 tasks) to tau2 format
"""

import json
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows - must be done BEFORE any print statements
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from primekg_to_tau2 import ConsultationTask, WalkPath, convert_to_tau2_format


def load_all_tasks(all_tasks_file: Path):
    """Load tasks from all_tasks.json"""
    with open(all_tasks_file, 'r', encoding='utf-8') as f:
        tasks_data = json.load(f)

    tasks = []
    for task_data in tasks_data:
        # Reconstruct ConsultationTask
        path = WalkPath(
            nodes=task_data['path']['nodes'],
            edges=task_data['path']['edges']
        )

        task = ConsultationTask(
            task_id=task_data['task_id'],
            path=path,
            patient_profile=task_data['patient_profile'],
            dialogue_turns=task_data['dialogue'],
            metadata=task_data['metadata']
        )
        tasks.append(task)

    return tasks


def main():
    print("="*70)
    print(" Convert All PrimeKG Tasks to tau2 Format")
    print("="*70)

    # Load all tasks
    all_tasks_file = Path("data/primekg_tasks/all_tasks.json")
    print(f"\nLoading: {all_tasks_file}")

    tasks = load_all_tasks(all_tasks_file)
    print(f"Loaded: {len(tasks)} tasks")

    # Convert to tau2 format
    output_dir = Path("data/tau2/domains/clinical/primekg")
    output_dir.mkdir(parents=True, exist_ok=True)

    tau2_tasks = []
    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] Converting: {task.task_id}")
        try:
            tau2_task = convert_to_tau2_format(task, domain="primekg_internal_medicine")
            tau2_tasks.append(tau2_task)
            print(f"  [OK] Converted")
        except Exception as e:
            print(f"  [FAIL] {e}")

    # Save
    output_file = output_dir / "tasks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tau2_tasks, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*70}")
    print(f" Conversion Complete!")
    print(f"{'='*70}")
    print(f"\nOutput: {output_file}")
    print(f"Total tasks: {len(tau2_tasks)}")

    # Generate train/test split
    import random
    random.seed(42)
    random.shuffle(tau2_tasks)

    split_point = max(1, int(len(tau2_tasks) * 0.8))
    train_tasks = tau2_tasks[:split_point]
    test_tasks = tau2_tasks[split_point:]

    split_data = {
        "train": [t['id'] for t in train_tasks],
        "test": [t['id'] for t in test_tasks],
        "metadata": {
            "total_tasks": len(tau2_tasks),
            "train_size": len(train_tasks),
            "test_size": len(test_tasks),
            "split_ratio": "80/20"
        }
    }

    split_file = output_dir / "split_tasks.json"
    with open(split_file, 'w', encoding='utf-8') as f:
        json.dump(split_data, f, ensure_ascii=False, indent=2)

    print(f"\nTrain/test split:")
    print(f"  Train: {len(train_tasks)} tasks")
    print(f"  Test: {len(test_tasks)} tasks")
    print(f"  Split file: {split_file}")

    # Statistics
    print(f"\n{'='*70}")
    print(f" Task Statistics")
    print(f"{'='*70}")

    from collections import Counter
    symptoms = [t['user_scenario']['instructions']['reason_for_call'] for t in tau2_tasks]
    symptom_counts = Counter(symptoms)

    print(f"\nSymptom distribution:")
    for symptom, count in symptom_counts.most_common():
        print(f"  {symptom}: {count}")

    path_lengths = [t['metadata']['primekg_path_length'] for t in tau2_tasks]
    print(f"\nPath length: avg {sum(path_lengths)/len(path_lengths):.1f}, min {min(path_lengths)}, max {max(path_lengths)}")

    dialogue_lengths = [len(t['reference_dialogue']) for t in tau2_tasks]
    print(f"Dialogue turns: avg {sum(dialogue_lengths)/len(dialogue_lengths):.1f}, min {min(dialogue_lengths)}, max {max(dialogue_lengths)}")

    print(f"\n{'='*70}")
    print(f" Success!")
    print(f"{'='*70}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
