#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerate all medical task files with new format

This script regenerates all medical domain task files to include:
- medical_persona: Structured medical persona data
- medical_criteria: Evaluation criteria with tool categories, reasoning steps, safety checks

Usage:
    python regenerate_all_medical_tasks.py
"""

import sys
import io
import json
import random
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        # Python < 3.7 doesn't have reconfigure
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')

# Add paths
sys.path.insert(0, 'src')
sys.path.insert(0, 'medical_task_suite/generation')

from medical_task_suite.generation import PrimeKGRandomWalkPipeline
from medical_task_suite.generation.utils.tau2_converter import convert_to_tau2_format


def generate_and_convert_tasks(
    num_tasks: int = 20,
    output_dir: str = "data/tau2/domains/clinical/primekg"
) -> list:
    """
    Generate PrimeKG tasks and convert to tau2 format with medical_persona and medical_criteria

    Args:
        num_tasks: Number of tasks to generate
        output_dir: Output directory for converted tasks

    Returns:
        List of converted tau2 tasks
    """
    print("\n" + "="*70)
    print(" Regenerate Medical Tasks with New Format")
    print("="*70)

    # Initialize PrimeKG pipeline
    print("\n[1/4] Initializing PrimeKG pipeline...")
    pipeline = PrimeKGRandomWalkPipeline(use_cache=True)
    print(f"  [OK] Pipeline initialized")

    # Search for symptoms
    print("\n[2/4] Searching for symptoms...")
    symptom_keywords = [
        "pain", "fever", "nausea", "hypertension", "diabetes",
        "headache", "cough", "fatigue", "dizziness", "weakness",
        "chest pain", "shortness of breath", "palpitations"
    ]

    # Generate tasks
    print(f"\n[3/4] Generating {num_tasks} consultation tasks...")
    consultation_tasks = []
    task_count = 0

    for keyword in symptom_keywords:
        if task_count >= num_tasks:
            break

        try:
            # Search for symptom
            results = pipeline.real_kg.search_nodes(
                keyword,
                node_type="effect/phenotype",
                limit=1
            )

            if not results:
                continue

            symptom_name = results[0]['name']

            # Generate task
            walk_type = random.choice(["short", "medium"])
            task = pipeline.generate_consultation_task(
                symptom_keyword=symptom_name,
                walk_type=walk_type
            )

            consultation_tasks.append(task)
            task_count += 1
            print(f"  [{task_count:2d}/{num_tasks}] {task.task_id}: {symptom_name[:50]}")

        except Exception as e:
            print(f"  [SKIP] {keyword}: {str(e)[:50]}")
            continue

    print(f"\n  [OK] Generated {len(consultation_tasks)} tasks")

    # Convert to tau2 format (with new medical_persona and medical_criteria)
    print(f"\n[4/4] Converting to tau2 format...")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    tau2_tasks = []
    for i, task in enumerate(consultation_tasks, 1):
        try:
            tau2_task = convert_to_tau2_format(task, domain="primekg_internal_medicine")
            tau2_tasks.append(tau2_task)

            # Verify new format
            has_medical_persona = "medical_persona" in tau2_task
            has_medical_criteria = "medical_criteria" in tau2_task.get("evaluation_criteria", {})

            status = "[OK]" if (has_medical_persona and has_medical_criteria) else "[WARN]"
            print(f"  {status} [{i}/{len(consultation_tasks)}] {tau2_task['id']}")

        except Exception as e:
            print(f"  [FAIL] {task.task_id}: {e}")

    # Save tasks
    output_file = output_path / "tasks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tau2_tasks, f, ensure_ascii=False, indent=2)

    print(f"\n  [OK] Saved {len(tau2_tasks)} tasks to {output_file}")

    # Generate train/test split
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

    split_file = output_path / "split_tasks.json"
    with open(split_file, 'w', encoding='utf-8') as f:
        json.dump(split_data, f, ensure_ascii=False, indent=2)

    print(f"  [OK] Train/test split: {len(train_tasks)} train, {len(test_tasks)} test")

    # Generate db.json
    db_data = {
        "domain": "primekg_internal_medicine",
        "description": "Medical consultation tasks generated from PrimeKG knowledge graph using Random Walk algorithm with new medical format",
        "source": "Harvard Medical School PrimeKG",
        "task_count": len(tau2_tasks),
        "metadata": {
            "primekg_version": "v2",
            "primekg_nodes": 23087,
            "primekg_edges": 617118,
            "generated_by": "PrimeKG Random Walk Generator v2.1",
            "generated_date": "2025-03-26",
            "algorithm": "Random Walk with weighted edge selection",
            "format_version": "2.1",
            "features": [
                "medical_persona: Structured patient data",
                "medical_criteria: Tool categories, reasoning steps, safety checks",
                "multi_turn: 5-10 conversation turns"
            ]
        }
    }

    db_file = output_path / "db.json"
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

    print(f"  [OK] Database info: {db_file}")

    return tau2_tasks


def verify_new_format(tau2_tasks: list):
    """Verify that tasks have the new format"""
    print("\n" + "="*70)
    print(" Verifying New Format")
    print("="*70)

    has_medical_persona = 0
    has_medical_criteria = 0
    has_set_medical_persona = 0

    for task in tau2_tasks:
        if "medical_persona" in task:
            has_medical_persona += 1

        if "medical_criteria" in task.get("evaluation_criteria", {}):
            has_medical_criteria += 1

        # Check if initialization_actions includes set_medical_persona
        init_actions = task.get("initial_state", {}).get("initialization_actions", [])
        for action in init_actions:
            if action.get("func_name") == "set_medical_persona":
                has_set_medical_persona += 1
                break

    print(f"\nMedical persona field: {has_medical_persona}/{len(tau2_tasks)} tasks")
    print(f"Medical criteria field: {has_medical_criteria}/{len(tau2_tasks)} tasks")
    print(f"Set medical persona action: {has_set_medical_persona}/{len(tau2_tasks)} tasks")

    if has_medical_persona == len(tau2_tasks) and has_medical_criteria == len(tau2_tasks):
        print(f"\n[OK] All tasks have new format!")
        return True
    else:
        print(f"\n[WARN] Some tasks missing new format fields")
        return False


def show_sample_task(tau2_tasks: list):
    """Show a sample task with new format"""
    if not tau2_tasks:
        return

    print("\n" + "="*70)
    print(" Sample Task (New Format)")
    print("="*70)

    task = tau2_tasks[0]

    print(f"\nTask ID: {task['id']}")
    print(f"\nMedical Persona:")
    print(json.dumps(task.get('medical_persona', {}), indent=2, ensure_ascii=False))

    print(f"\nMedical Criteria:")
    mc = task.get('evaluation_criteria', {}).get('medical_criteria', {})
    print(json.dumps(mc, indent=2, ensure_ascii=False))

    print(f"\nInitialization Actions:")
    for action in task.get('initial_state', {}).get('initialization_actions', []):
        print(f"  - {action.get('func_name')}")


def main():
    """Main function"""
    print("\n" + "="*70)
    print(" REGENERATE ALL MEDICAL TASKS WITH NEW FORMAT")
    print("="*70)
    print("\nThis will regenerate all medical domain tasks to include:")
    print("  - medical_persona: Structured patient data")
    print("  - medical_criteria: Tool categories, reasoning steps, safety checks")
    print("\nOutput directory: data/tau2/domains/clinical/primekg/")

    # Generate and convert tasks
    tau2_tasks = generate_and_convert_tasks(num_tasks=20)

    if not tau2_tasks:
        print("\n[FAIL] No tasks generated")
        return 1

    # Verify format
    success = verify_new_format(tau2_tasks)

    # Show sample
    show_sample_task(tau2_tasks)

    print("\n" + "="*70)
    print(" Summary")
    print("="*70)
    print(f"\nTotal tasks generated: {len(tau2_tasks)}")
    print(f"Output directory: data/tau2/domains/clinical/primekg/")
    print(f"\nFiles:")
    print(f"  - tasks.json: All tasks with new format")
    print(f"  - split_tasks.json: Train/test split")
    print(f"  - db.json: Database information")

    if success:
        print(f"\n[OK] Regeneration complete!")
        return 0
    else:
        print(f"\n[WARN] Regeneration completed with warnings")
        return 1


if __name__ == "__main__":
    sys.exit(main())
