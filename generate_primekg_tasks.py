#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成更多 PrimeKG 任务（已迁移到 medical_task_suite/generation/）

注意：此脚本现在使用 medical_task_suite/generation/ 模块
推荐直接使用：from medical_task_suite.generation import PrimeKGRandomWalkPipeline
"""

import sys
import io
import random
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 从 medical_task_suite 导入（推荐方式）
sys.path.insert(0, str(Path(__file__).parent / "medical_task_suite"))
from generation import PrimeKGRandomWalkPipeline

# 或者从旧的根目录脚本导入（向后兼容）
# from primekg_random_walk import PrimeKGRandomWalkPipeline

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

    print(f"\n📊 Generated: {task_count} tasks")
    print(f"📍 Location: {output_dir}")

    print(f"\n📖 Documentation:")
    print(f"  - medical_task_suite/generation/README.md (完整指南)")
    print(f"  - PRIMEKG_UNIFICATION.md (统一说明)")

    print(f"\n🎯 Recommended usage:")
    print(f"  from medical_task_suite.generation import PrimeKGRandomWalkPipeline")
    print(f"  pipeline = PrimeKGRandomWalkPipeline(use_cache=True)")

    print(f"\n📝 Next steps:")
    print(f"  1. Test tasks: python test_primekg_complete.py")
    print(f"  2. View documentation: cat medical_task_suite/generation/README.md")

if __name__ == "__main__":
    main()
