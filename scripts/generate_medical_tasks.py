#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Multi-Turn Medical Consultation Tasks

Usage:
    # Generate 50 balanced tasks
    python scripts/generate_medical_tasks.py --n 50 --output tasks/output.json

    # Specific task type and difficulty
    python scripts/generate_medical_tasks.py --n 20 --task-type diagnostic_uncertainty --difficulty L2

    # Specific disease
    python scripts/generate_medical_tasks.py --n 5 --disease "type 2 diabetes"

    # Quick test
    python scripts/generate_medical_tasks.py --n 3 --output test_tasks.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser(
        description="Generate multi-turn medical consultation tasks using v2.7 medical suite"
    )
    parser.add_argument(
        "--n", type=int, default=50,
        help="Number of tasks to generate (default: 50)"
    )
    parser.add_argument(
        "--task-type", type=str, default=None,
        choices=[
            "diagnostic_uncertainty", "conflicting_evidence",
            "treatment_tradeoff", "patient_non_compliance",
            "drug_safety_risk", "emergency_triage",
        ],
        help="Restrict to a specific task type (default: all types)"
    )
    parser.add_argument(
        "--difficulty", type=str, default=None,
        choices=["L1", "L2", "L3"],
        help="Restrict to a specific difficulty (default: all levels)"
    )
    parser.add_argument(
        "--disease", type=str, default=None,
        help="Target a specific disease (e.g., 'type 2 diabetes')"
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output JSON file path (default: auto-generated)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--print-sample", action="store_true",
        help="Print a sample task to stdout"
    )

    args = parser.parse_args()

    # Auto output path
    if args.output is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        args.output = f"tasks/medical_tasks_{timestamp}.json"

    print(f"\n{'='*60}")
    print(f"  Medical Task Generator (v2.7)")
    print(f"{'='*60}")
    print(f"  Count:        {args.n}")
    print(f"  Task type:    {args.task_type or 'all types'}")
    print(f"  Difficulty:   {args.difficulty or 'all levels'}")
    print(f"  Disease:      {args.disease or 'auto-selected'}")
    print(f"  Output:       {args.output}")
    print(f"  Seed:         {args.seed}")
    print(f"{'='*60}\n")

    # Initialize
    print("  Loading clinical knowledge base...")
    from medical_task_suite.clinical_knowledge.accessor import ClinicalKnowledgeBase
    kb = ClinicalKnowledgeBase.get_instance()
    print(f"  KB loaded: {len(kb.get_covered_diseases())} diseases\n")

    from medical_task_suite.generation.v2.task_generation import MedicalTaskGenerator
    gen = MedicalTaskGenerator(kb)

    # Generate
    print(f"  Generating {args.n} tasks...")
    start_time = time.time()

    task_types = [args.task_type] if args.task_type else None
    difficulties = [args.difficulty] if args.difficulty else None

    if args.disease:
        # Generate for specific disease
        tasks = []
        for i in range(args.n):
            tt = task_types[0] if task_types else [
                "diagnostic_uncertainty", "conflicting_evidence",
                "treatment_tradeoff", "patient_non_compliance",
                "drug_safety_risk", "emergency_triage",
            ][i % 6]
            diff = difficulties[0] if difficulties else ["L1", "L2", "L3"][i % 3]
            try:
                task = gen.generate_task(tt, diff, target_disease=args.disease, seed=args.seed + i)
                tasks.append(task)
            except Exception as e:
                print(f"  [WARN] Task {i+1} failed: {e}")
    else:
        tasks = gen.generate_batch(
            n=args.n,
            task_types=task_types,
            difficulties=difficulties,
            output_path=args.output,
            seed=args.seed,
        )

    elapsed = time.time() - start_time

    # Save if not already saved by generate_batch
    if args.disease or not Path(args.output).exists():
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

    # Statistics
    print(f"\n  Generation complete!")
    print(f"  Tasks generated: {len(tasks)}")
    print(f"  Time: {elapsed:.1f}s ({elapsed/max(1,len(tasks)):.2f}s/task)")
    print(f"  Output: {args.output}")

    # Task type distribution
    type_dist = {}
    disease_dist = {}
    for t in tasks:
        tt = t.get("task_type", "unknown")
        type_dist[tt] = type_dist.get(tt, 0) + 1
        dis = t.get("medical_persona", {}).get("diagnosis", {}).get("primary", "unknown")
        disease_dist[dis] = disease_dist.get(dis, 0) + 1

    print(f"\n  Task type distribution:")
    for tt, count in sorted(type_dist.items(), key=lambda x: -x[1]):
        print(f"    {tt}: {count}")

    print(f"\n  Disease distribution ({len(disease_dist)} unique):")
    for dis, count in sorted(disease_dist.items(), key=lambda x: -x[1])[:10]:
        print(f"    {dis}: {count}")

    # Print sample
    if args.print_sample and tasks:
        print(f"\n{'='*60}")
        print(f"  Sample Task:")
        print(f"{'='*60}")
        print(json.dumps(tasks[0], indent=2, ensure_ascii=False)[:3000])
        if len(json.dumps(tasks[0], indent=2, ensure_ascii=False)) > 3000:
            print("  ... (truncated)")

    print(f"\n{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
