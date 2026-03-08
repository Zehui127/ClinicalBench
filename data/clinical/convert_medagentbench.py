#!/usr/bin/env python3
"""
MedAgentBench to Tau2-Bench Task Converter

This script converts MedAgentBench test_data_v2.json format to tau2-bench Task format.

Usage:
    python convert_medagentbench.py --source <source_file> --output <output_file> [--config <config_file>]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def extract_patient_info(instruction: str) -> Optional[str]:
    """
    Extract patient name and DOB from instruction using regex.

    Args:
        instruction: The task instruction text

    Returns:
        Formatted known_info string or None
    """
    # Pattern to match "name <name> and DOB of <dob>"
    pattern = r"name\s+([\w\s]+?)\s+and\s+DOB\s+of\s+([\d\-]+)"
    match = re.search(pattern, instruction)

    if match:
        name = match.group(1).strip()
        dob = match.group(2).strip()
        return f"Patient name: {name}, DOB: {dob}"

    # Alternative pattern for other instruction formats
    alt_pattern = r"patient\s+with\s+name\s+([\w\s]+?)\s+(?:and\s+DOB\s+of\s+)?([\d\-]+)?"
    alt_match = re.search(alt_pattern, instruction, re.IGNORECASE)

    if alt_match:
        name = alt_match.group(1).strip()
        dob = alt_match.group(2).strip() if alt_match.group(2) else "unknown"
        return f"Patient name: {name}, DOB: {dob}"

    return None


def convert_single_task(source_task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a single MedAgentBench task to tau2-bench Task format.

    Args:
        source_task: Source task dictionary from MedAgentBench

    Returns:
        Converted task in tau2-bench format
    """
    task_id = source_task.get("id", "")
    instruction = source_task.get("instruction", "")
    context = source_task.get("context", "")
    sol = source_task.get("sol", [])
    eval_mrn = source_task.get("eval_MRN", "")

    # Extract patient information from instruction
    known_info = extract_patient_info(instruction) or instruction

    # Build the tau2-bench task structure
    converted_task = {
        "id": task_id,
        "description": {
            "purpose": "Find patient MRN by name and date of birth",
            "relevant_policies": None,
            "notes": None
        },
        "user_scenario": {
            "persona": None,
            "instructions": {
                "task_instructions": instruction,
                "domain": "clinical",
                "reason_for_call": "Looking up patient information",
                "known_info": known_info,
                "unknown_info": context if context else None
            }
        },
        "ticket": instruction,
        "initial_state": None,
        "evaluation_criteria": {
            "actions": [],
            "communicate_info": [],
            "nl_assertions": [f"Agent should correctly identify the MRN as {eval_mrn}"] if eval_mrn else []
        },
        "annotations": {
            "expected_answer": eval_mrn,
            "expected_solution": sol,
            "source_format": "medagentbench_v2"
        }
    }

    return converted_task


def convert_tasks(source_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert all tasks from MedAgentBench format to tau2-bench format.

    Args:
        source_data: List of source tasks

    Returns:
        List of converted tasks
    """
    converted_tasks = []

    for source_task in source_data:
        try:
            converted_task = convert_single_task(source_task)
            converted_tasks.append(converted_task)
        except Exception as e:
            print(f"Warning: Failed to convert task {source_task.get('id', 'unknown')}: {e}",
                  file=sys.stderr)
            continue

    return converted_tasks


def load_config(config_path: str) -> Dict[str, Any]:
    """Load adapter configuration from JSON file."""
    if config_path and Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def main():
    """Main conversion function."""
    parser = argparse.ArgumentParser(
        description="Convert MedAgentBench test_data_v2.json to tau2-bench Task format"
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Path to source MedAgentBench JSON file"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output tau2-bench tasks.json file"
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to adapter configuration JSON file (optional)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of tasks to convert (for testing)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Load source data
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: Source file not found: {args.source}", file=sys.stderr)
        return 1

    print(f"Loading source data from: {args.source}")
    with open(source_path, 'r', encoding='utf-8') as f:
        source_data = json.load(f)

    # Ensure source_data is a list
    if isinstance(source_data, dict):
        source_data = [source_data]

    # Apply limit if specified
    if args.limit:
        source_data = source_data[:args.limit]
        print(f"Limited to {args.limit} tasks")

    print(f"Found {len(source_data)} tasks to convert")

    # Load config if provided
    config = load_config(args.config) if args.config else {}

    # Convert tasks
    print("Converting tasks...")
    converted_tasks = convert_tasks(source_data)

    print(f"Successfully converted {len(converted_tasks)} tasks")

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    print(f"Writing output to: {args.output}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(converted_tasks, f, indent=2, ensure_ascii=False)

    print("Conversion completed successfully!")

    # Display summary if verbose
    if args.verbose and converted_tasks:
        print("\n=== Sample Converted Task ===")
        print(json.dumps(converted_tasks[0], indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
