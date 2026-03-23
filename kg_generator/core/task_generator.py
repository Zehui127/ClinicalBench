#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成更多 PrimeKG 任务（简化版）
"""

import sys
import io
import random
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from primekg_random_walk import PrimeKGRandomWalkPipeline

def main():
    print("="*70)
    print(" Generate More PrimeKG Tasks")
    print("="*70)

    # Initialize
    print("\n[1/3] Initializing...")
    pipeline = PrimeKGRandomWalkPipeline(use_cache=True)

    # Search symptoms
    print("\n[2/3] Searching symptoms...")
    symptom_keywords = [
        "pain", "fever", "nausea", "hypertension", "diabetes",
        "headache", "cough", "fatigue"
    ]

    output_dir = Path("data/primekg_tasks/batch")
    output_dir.mkdir(parents=True, exist_ok=True)

    task_count = 0
    max_tasks = 15

    # Generate
    print("\n[3/3] Generating tasks...")
    for keyword in symptom_keywords[:max_tasks]:
        try:
            results = pipeline.real_kg.search_nodes(
                keyword,
                node_type="effect/phenotype",
                limit=1
            )

            if not results:
                continue

            symptom_name = results[0]['name']
            walk_type = random.choice(["short", "medium"])

            task = pipeline.generate_consultation_task(
                symptom_keyword=symptom_name,
                walk_type=walk_type
            )

            # Save
            output_file = output_dir / f"{task.task_id}.json"
            pipeline.export_to_tau2(task, str(output_file))

            task_count += 1
            print(f"  [{task_count:2d}] {task.task_id}")

            if task_count >= max_tasks:
                break

        except Exception as e:
            print(f"  Skip {keyword}: {str(e)[:50]}")
            continue

    print(f"\nGenerated: {task_count} tasks")
    print(f"Location: {output_dir}")

    print("\n" + "="*70)
    print(" Complete!")
    print("="*70)

    print(f"\nNext steps:")
    print(f"  1. Convert to tau2: python primekg_to_tau2.py")
    print(f"  2. Test tasks: python test_primekg_tasks.py")

if __name__ == "__main__":
    main()
