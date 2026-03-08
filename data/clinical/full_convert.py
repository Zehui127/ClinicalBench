#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full Conversion Script - MedAgentBench to Tau2-Bench

Run this script to convert the complete MedAgentBench test_data_v2.json
to tau2-bench tasks.json format.

Usage:
    python full_convert.py
"""

import json
import re
import sys
from pathlib import Path

# File paths - using raw strings for Windows paths
SOURCE_FILE = r"C:\Users\方正\tau2-bench\MedAgentBench\data\medagentbench\test_data_v2.json"
OUTPUT_FILE = r"C:\Users\方正\tau2-bench\data\clinical\tasks.json"

def extract_patient_info(instruction):
    """Extract patient name and DOB from instruction."""
    pattern = r"name\s+([\w\s]+?)\s+and\s+DOB\s+of\s+([\d\-]+)"
    match = re.search(pattern, instruction)
    if match:
        return f"Patient name: {match.group(1).strip()}, DOB: {match.group(2).strip()}"
    return instruction

def convert_task(source_task):
    """Convert a single task from MedAgentBench to tau2-bench format."""
    task_id = source_task.get("id", "")
    instruction = source_task.get("instruction", "")
    context = source_task.get("context", "")
    sol = source_task.get("sol", [])
    eval_mrn = source_task.get("eval_MRN", "")

    known_info = extract_patient_info(instruction)

    return {
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

def main():
    """Main conversion function."""
    print("=" * 60)
    print("MedAgentBench to Tau2-Bench Full Conversion")
    print("=" * 60)

    # Check source file exists
    if not Path(SOURCE_FILE).exists():
        print(f"Error: Source file not found: {SOURCE_FILE}")
        return 1

    # Load source data
    print(f"\nLoading source data from: {SOURCE_FILE}")
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
    except Exception as e:
        print(f"Error loading source file: {e}")
        return 1

    if not isinstance(source_data, list):
        source_data = [source_data]

    print(f"Found {len(source_data)} tasks to convert")

    # Convert all tasks
    print("Converting tasks...")
    converted_tasks = []
    for i, source_task in enumerate(source_data):
        try:
            converted_task = convert_task(source_task)
            converted_tasks.append(converted_task)
            if (i + 1) % 100 == 0:
                print(f"  Converted {i + 1}/{len(source_data)} tasks...")
        except Exception as e:
            print(f"Warning: Failed to convert task {source_task.get('id', i)}: {e}")

    print(f"Successfully converted {len(converted_tasks)} tasks")

    # Ensure output directory exists
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    print(f"\nWriting output to: {OUTPUT_FILE}")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(converted_tasks, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing output file: {e}")
        return 1

    # Verify output
    print("Verifying output...")
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        print(f"✓ Output file is valid JSON")
        print(f"✓ Total tasks in output: {len(loaded)}")
    except Exception as e:
        print(f"✗ Output verification failed: {e}")
        return 1

    print("\n" + "=" * 60)
    print("Conversion completed successfully!")
    print("=" * 60)
    print(f"\nOutput file: {OUTPUT_FILE}")
    print(f"Total tasks: {len(converted_tasks)}")
    print(f"\nSample task IDs: {[t['id'] for t in converted_tasks[:5]]}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
