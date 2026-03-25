#!/usr/bin/env python3
"""
Enrich Cardiology Clinical Data Script

使用 ClinicalDataEnricher 改进心脏科任务数据的质量

Usage:
    python enrich_cardiology_data.py --input data/tau2/domains/clinical/cardiology/tasks.json
                                     --output data/tau2/domains/clinical/cardiology/tasks_enriched.json
                                     --level moderate
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from UniClinicalDataEngine.generators.clinical_enricher import ClinicalDataEnricher


def load_tasks(input_path: str) -> list:
    """Load tasks from JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_tasks(tasks: list, output_path: str):
    """Save tasks to JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(tasks)} enriched tasks to {output_path}")


def analyze_tasks(tasks: list) -> dict:
    """Analyze task quality metrics."""
    total = len(tasks)

    # Count placeholder usage
    placeholder_count = 0
    for task in tasks:
        instructions = task.get('user_scenario', {}).get('instructions', {}).get('task_instructions', '')
        if 'timeframe' in instructions or '{' in instructions:
            placeholder_count += 1

    # Count rich vs poor info
    rich_info = 0
    poor_info = 0
    for task in tasks:
        known_info = task.get('user_scenario', {}).get('instructions', {}).get('known_info', '')
        if len(known_info) > 100:
            rich_info += 1
        else:
            poor_info += 1

    # Count scenario types
    scenario_types = {}
    for task in tasks:
        scenario = task.get('user_scenario', {}).get('instructions', {}).get('enriched_scenario_type', 'unknown')
        scenario_types[scenario] = scenario_types.get(scenario, 0) + 1

    return {
        'total_tasks': total,
        'placeholder_usage': placeholder_count,
        'rich_info': rich_info,
        'poor_info': poor_info,
        'scenario_types': scenario_types,
    }


def print_comparison(before: dict, after: dict):
    """Print before/after comparison."""
    print("\n" + "="*70)
    print(" QUALITY IMPROVEMENT SUMMARY")
    print("="*70)

    print(f"\nTotal Tasks: {before['total_tasks']} → {after['total_tasks']}")

    print(f"\nPlaceholder Usage:")
    before_pct = before['placeholder_usage'] / before['total_tasks'] * 100
    after_pct = after['placeholder_usage'] / after['total_tasks'] * 100 if after['total_tasks'] > 0 else 0
    print(f"  Before: {before['placeholder_usage']}/{before['total_tasks']} ({before_pct:.1f}%)")
    print(f"  After:  {after['placeholder_usage']}/{after['total_tasks']} ({after_pct:.1f}%)")
    improvement = before_pct - after_pct
    print(f"  Improvement: -{improvement:.1f}%" if improvement > 0 else "  Improvement: 0%")

    print(f"\nClinical Information Richness:")
    before_rich_pct = before['rich_info'] / before['total_tasks'] * 100
    after_rich_pct = after['rich_info'] / after['total_tasks'] * 100 if after['total_tasks'] > 0 else 0
    print(f"  Before: {before['rich_info']} rich ({before_rich_pct:.1f}%)")
    print(f"  After:  {after['rich_info']} rich ({after_rich_pct:.1f}%)")
    improvement = after_rich_pct - before_rich_pct
    print(f"  Improvement: +{improvement:.1f}%" if improvement > 0 else "  Improvement: 0%")

    print(f"\nScenario Type Distribution:")
    print("  Before: Not available")
    print("  After:")
    for scenario, count in sorted(after['scenario_types'].items(), key=lambda x: -x[1])[:5]:
        pct = count / after['total_tasks'] * 100
        print(f"    - {scenario}: {count} ({pct:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Enrich cardiology clinical tasks with detailed medical information"
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/tau2/domains/clinical/cardiology/tasks.json',
        help='Input tasks JSON file path'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/tau2/domains/clinical/cardiology/tasks_enriched.json',
        help='Output enriched tasks JSON file path'
    )
    parser.add_argument(
        '--level',
        type=str,
        choices=['basic', 'moderate', 'comprehensive'],
        default='moderate',
        help='Enrichment level (default: moderate)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of tasks to process (for testing)'
    )
    parser.add_argument(
        '--include-vitals',
        action='store_true',
        help='Include vital signs in enrichment'
    )
    parser.add_argument(
        '--include-labs',
        action='store_true',
        help='Include lab results in enrichment'
    )
    parser.add_argument(
        '--include-imaging',
        action='store_true',
        help='Include imaging results in enrichment'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create backup of original file'
    )

    args = parser.parse_args()

    print("="*70)
    print(" CARDIOLOGY DATA ENRICHMENT")
    print("="*70)
    print(f"\nInput:  {args.input}")
    print(f"Output: {args.output}")
    print(f"Level:  {args.level}")
    print(f"Limit:  {args.limit or 'All'}")

    # Load original tasks
    print("\nLoading original tasks...")
    original_tasks = load_tasks(args.input)
    print(f"Loaded {len(original_tasks)} tasks")

    # Analyze before
    print("\nAnalyzing original tasks...")
    before_stats = analyze_tasks(original_tasks)
    print(f"  Placeholder usage: {before_stats['placeholder_usage']}/{before_stats['total_tasks']}")
    print(f"  Rich clinical info: {before_stats['rich_info']}/{before_stats['total_tasks']}")
    print(f"  Poor clinical info: {before_stats['poor_info']}/{before_stats['total_tasks']}")

    # Create backup if requested
    if args.backup:
        backup_path = Path(args.input).with_suffix('.json.backup')
        save_tasks(original_tasks, backup_path)
        print(f"\nBackup created: {backup_path}")

    # Limit tasks if specified
    tasks_to_process = original_tasks[:args.limit] if args.limit else original_tasks
    if args.limit:
        print(f"\nProcessing first {args.limit} tasks only...")

    # Configure enricher
    config = {
        'enrichment_level': args.level,
        'include_vitals': args.include_vitals,
        'include_lab_results': args.include_labs,
        'include_imaging': args.include_imaging,
    }

    print(f"\nEnricher Configuration:")
    print(f"  Enrichment level: {config['enrichment_level']}")
    print(f"  Include vitals: {config['include_vitals']}")
    print(f"  Include labs: {config['include_lab_results']}")
    print(f"  Include imaging: {config['include_imaging']}")

    # Enrich tasks
    print("\nEnriching tasks...")
    enricher = ClinicalDataEnricher(config)

    enriched_tasks = []
    for i, task in enumerate(tasks_to_process, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(tasks_to_process)} tasks...")

        try:
            enriched = enricher.enrich_task(task)
            enriched_tasks.append(enriched)
        except Exception as e:
            print(f"  Error enriching task {task.get('id', 'unknown')}: {e}")
            # Keep original task if enrichment fails
            enriched_tasks.append(task)

    print(f"  Enriched {len(enriched_tasks)} tasks")

    # If we limited, append remaining tasks
    if args.limit and len(original_tasks) > args.limit:
        print(f"\nAppending remaining {len(original_tasks) - args.limit} tasks without enrichment...")
        enriched_tasks.extend(original_tasks[args.limit:])

    # Analyze after
    print("\nAnalyzing enriched tasks...")
    after_stats = analyze_tasks(enriched_tasks)

    # Print comparison
    print_comparison(before_stats, after_stats)

    # Save enriched tasks
    print(f"\nSaving enriched tasks to {args.output}...")
    save_tasks(enriched_tasks, args.output)

    # Show sample
    print("\n" + "="*70)
    print(" SAMPLE ENRICHED TASK")
    print("="*70)
    if enriched_tasks:
        sample = enriched_tasks[0]
        print(f"\nTask ID: {sample.get('id')}")
        print(f"\nOriginal ticket: {sample.get('ticket', '')[:80]}...")

        known_info = sample.get('user_scenario', {}).get('instructions', {}).get('known_info', '')
        print(f"\nEnriched known_info: {known_info[:200]}...")

        scenario = sample.get('user_scenario', {}).get('instructions', {}).get('enriched_scenario_type', 'N/A')
        print(f"\nDetected scenario type: {scenario}")

    print("\n" + "="*70)
    print(" ENRICHMENT COMPLETE")
    print("="*70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
