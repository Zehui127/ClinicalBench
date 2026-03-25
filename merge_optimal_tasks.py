#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge the best features from both task files:
- tasks_with_agent_workflow.json: agent workflow, environment, tool evaluation
- tasks_optimized.json: quality scoring, conversion metadata, weighted checks

Creates an optimal version with all advantages.
"""

import json
from pathlib import Path
from typing import Dict, Any
from copy import deepcopy


def merge_tasks(
    workflow_task: Dict[str, Any],
    optimized_task: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge workflow task and optimized task into one optimal task.

    Priority:
    1. Core fields (id, description, user_scenario, ticket, initial_state) → from either (identical)
    2. evaluation_criteria → Take from optimized (has weight field)
    3. metadata → Take from optimized, add environment info from workflow
    4. agent workflow fields → Only from workflow (expected_agent_workflow, environment, tool_evaluation_criteria)
    5. optimization fields → Only from optimized (conversion_metadata, original_task_id)
    """

    merged = {}

    # 1. Core fields (should be identical in both)
    for field in ['id', 'description', 'user_scenario', 'ticket', 'initial_state']:
        merged[field] = workflow_task.get(field) or optimized_task.get(field)

    # 2. Evaluation criteria - prefer optimized (has weight field)
    if 'evaluation_criteria' in optimized_task:
        merged['evaluation_criteria'] = optimized_task['evaluation_criteria']
    else:
        merged['evaluation_criteria'] = workflow_task.get('evaluation_criteria', {})

    # 3. Metadata - merge both
    merged['metadata'] = {}

    # Base metadata from optimized (has quality info)
    if 'metadata' in optimized_task:
        merged['metadata'].update(optimized_task['metadata'])

    # Environment info from workflow
    if 'metadata' in workflow_task:
        # Keep version from optimized but note workflow features
        if 'has_agent_workflow' in workflow_task['metadata']:
            merged['metadata']['has_agent_workflow'] = workflow_task['metadata']['has_agent_workflow']
        if 'version' not in merged['metadata']:
            merged['metadata']['version'] = workflow_task['metadata'].get('version', 'merged_v1')

    # 4. Difficulty and patient behavior
    merged['difficulty'] = workflow_task.get('difficulty') or optimized_task.get('difficulty')
    merged['patient_behavior'] = workflow_task.get('patient_behavior') or optimized_task.get('patient_behavior')

    # 5. Agent workflow features (only from workflow)
    if 'expected_agent_workflow' in workflow_task:
        merged['expected_agent_workflow'] = workflow_task['expected_agent_workflow']

    if 'environment' in workflow_task:
        merged['environment'] = workflow_task['environment']

    if 'tool_evaluation_criteria' in workflow_task:
        merged['tool_evaluation_criteria'] = workflow_task['tool_evaluation_criteria']

    # 6. Optimization features (only from optimized)
    if 'conversion_metadata' in optimized_task:
        merged['conversion_metadata'] = optimized_task['conversion_metadata']

    if 'original_task_id' in optimized_task:
        merged['original_task_id'] = optimized_task['original_task_id']

    # 7. Add merge metadata
    merged['merge_metadata'] = {
        'merged_from': ['workflow', 'optimized'],
        'merge_version': '1.0',
        'merge_timestamp': '2026-03-25',
        'features_included': {
            'agent_workflow': bool('expected_agent_workflow' in workflow_task),
            'environment_config': bool('environment' in workflow_task),
            'tool_evaluation': bool('tool_evaluation_criteria' in workflow_task),
            'quality_scoring': bool('conversion_metadata' in optimized_task),
            'weighted_checks': any(
                'weight' in check.get('', {})
                for check in optimized_task.get('evaluation_criteria', {}).get('communication_checks', [])
            ),
            'traceability': bool('original_task_id' in optimized_task)
        }
    }

    return merged


def generate_optimal_version(
    workflow_file: Path,
    optimized_file: Path,
    output_file: Path
):
    """Generate the optimal merged version."""

    print("=" * 70)
    print("MERGING OPTIMAL FEATURES FROM BOTH FILES")
    print("=" * 70)
    print()

    # Load files
    print(f"Loading: {workflow_file.name}")
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflow_tasks = json.load(f)

    print(f"Loading: {optimized_file.name}")
    with open(optimized_file, 'r', encoding='utf-8') as f:
        optimized_tasks = json.load(f)

    print(f"Workflow tasks: {len(workflow_tasks)}")
    print(f"Optimized tasks: {len(optimized_tasks)}")
    print()

    # Verify they match
    if len(workflow_tasks) != len(optimized_tasks):
        print("WARNING: Task counts don't match!")
        print(f"  Workflow: {len(workflow_tasks)}")
        print(f"  Optimized: {len(optimized_tasks)}")
        print()

    # Merge tasks
    print("Merging tasks...")
    merged_tasks = []

    for i in range(max(len(workflow_tasks), len(optimized_tasks))):
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i + 1}/{max(len(workflow_tasks), len(optimized_tasks))}")

        workflow_task = workflow_tasks[i] if i < len(workflow_tasks) else {}
        optimized_task = optimized_tasks[i] if i < len(optimized_tasks) else {}

        merged_task = merge_tasks(workflow_task, optimized_task)
        merged_tasks.append(merged_task)

    print(f"  Completed: {len(merged_tasks)} tasks")
    print()

    # Write output
    print(f"Writing: {output_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_tasks, f, ensure_ascii=False, indent=2)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)

    # Analyze features
    print()
    print("=" * 70)
    print("MERGE ANALYSIS")
    print("=" * 70)

    sample = merged_tasks[0]
    features = sample.get('merge_metadata', {}).get('features_included', {})

    print("\\nFeatures included:")
    for feature, present in features.items():
        status = "[YES]" if present else "[NO]"
        print(f"  {status} {feature}")

    print(f"\\nFile statistics:")
    print(f"  Total tasks: {len(merged_tasks)}")
    print(f"  File size: {file_size_mb:.2f} MB")

    # Check for environment features
    has_env = sum(1 for t in merged_tasks if 'environment' in t)
    has_workflow = sum(1 for t in merged_tasks if 'expected_agent_workflow' in t)
    has_quality = sum(1 for t in merged_tasks if 'conversion_metadata' in t)

    print(f"\\nTask coverage:")
    print(f"  With environment config: {has_env}/{len(merged_tasks)} ({100*has_env/len(merged_tasks):.1f}%)")
    print(f"  With agent workflow: {has_workflow}/{len(merged_tasks)} ({100*has_workflow/len(merged_tasks):.1f}%)")
    print(f"  With quality scoring: {has_quality}/{len(merged_tasks)} ({100*has_quality/len(merged_tasks):.1f}%)")

    print()
    print("=" * 70)
    print("MERGE COMPLETE!")
    print("=" * 70)
    print()
    print("Output file:", output_file)
    print()
    print("Advantages of merged version:")
    print("  [+] Agent workflow guidance (from workflow)")
    print("  [+] Environment and tool configuration (from workflow)")
    print("  [+] Tool evaluation criteria (from workflow)")
    print("  [+] Quality scoring system (from optimized)")
    print("  [+] Weighted evaluation checks (from optimized)")
    print("  [+] Full traceability (from optimized)")
    print()

    return merged_tasks


def main():
    """Main function."""
    base_dir = Path("data/tau2/domains/clinical/chinese_internal_medicine")

    workflow_file = base_dir / "tasks_with_agent_workflow.json"
    optimized_file = base_dir / "tasks_optimized.json"
    output_file = base_dir / "tasks_optimal_complete.json"

    try:
        generate_optimal_version(workflow_file, optimized_file, output_file)
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
