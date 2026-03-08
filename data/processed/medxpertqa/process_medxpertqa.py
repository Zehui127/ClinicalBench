#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedXpertQA Processor - Converts to Tau2-Bench Format (MedAgentBench compatible)
Processes medxpertqa_text_input.jsonl into tasks.json and db.json
"""

import json
import sys
from pathlib import Path

# Fixed paths (no environment variables)
INPUT_FILE = r"C:\Users\方正\tau2-bench\data\raw\MedXpertQA\eval\data\medxpertqa\input\medxpertqa_text_input.jsonl"
OUTPUT_DIR = r"C:\Users\方正\tau2-bench\data\processed\medxpertqa"
TASKS_OUTPUT = Path(OUTPUT_DIR) / "tasks.json"
DB_OUTPUT = Path(OUTPUT_DIR) / "db.json"


def process_jsonl_file(file_path: str) -> list:
    """Process the JSONL file and return list of QA entries."""
    print(f"Reading: {file_path}")
    entries = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
                if line_num % 100 == 0:
                    print(f"  Processed {line_num} lines...")
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line {line_num}: {e}")

    print(f"Total entries loaded: {len(entries)}")
    return entries


def get_answer_text(entry: dict) -> str:
    """Extract the answer text from options based on label."""
    label = entry.get("label", [])
    options = entry.get("options", [])

    if not label or not options:
        return "Not found"

    # Get the correct letter (label is an array like ["E"])
    correct_letter = label[0] if label else ""

    # Find the corresponding option
    for opt in options:
        if opt.get("letter") == correct_letter:
            return opt.get("content", "Not found")

    return "Not found"


def convert_to_tasks_json(entries: list) -> list:
    """Convert entries to tasks.json format (MedAgentBench compatible)."""
    tasks = []

    for idx, entry in enumerate(entries, 1):
        task_id = f"medxpertqa_{idx:03d}"

        # Extract fields
        question = entry.get("question", "")
        medical_task = entry.get("medical_task", "Diagnosis")
        body_system = entry.get("body_system", "General")
        question_type = entry.get("question_type", "Reasoning")

        # Build ticket (question with fallback text)
        ticket = question
        if not ticket.endswith("Not found"):
            ticket = f"{ticket} If the answer does not exist, the answer should be 'Not found'"

        # Build known_info from metadata
        known_info_parts = []
        if medical_task:
            known_info_parts.append(f"Task Type: {medical_task}")
        if body_system:
            known_info_parts.append(f"Body System: {body_system}")
        if question_type:
            known_info_parts.append(f"Question Type: {question_type}")
        known_info = ", ".join(known_info_parts) if known_info_parts else None

        # Build notes
        notes_parts = []
        if medical_task:
            notes_parts.append(f"Task: {medical_task}")
        if body_system:
            notes_parts.append(f"System: {body_system}")
        notes = ", ".join(notes_parts) if notes_parts else None

        # Create task object (EXACT MedAgentBench format)
        task = {
            "id": task_id,
            "description": {
                "purpose": "Medical knowledge QA",
                "relevant_policies": None,
                "notes": notes
            },
            "user_scenario": {
                "persona": None,
                "instructions": {
                    "task_instructions": ticket,
                    "domain": "clinical",
                    "reason_for_call": "Medical consultation",
                    "known_info": known_info,
                    "unknown_info": None
                }
            },
            "ticket": ticket,
            "initial_state": None,
            "evaluation_criteria": None,
            "annotations": None
        }
        tasks.append(task)

    return tasks


def convert_to_db_json(entries: list) -> dict:
    """Convert entries to db.json format (MedAgentBench compatible)."""
    qa_pairs = {}

    for idx, entry in enumerate(entries, 1):
        task_id = f"medxpertqa_{idx:03d}"

        # Extract fields
        question = entry.get("question", "")
        answer = get_answer_text(entry)
        medical_task = entry.get("medical_task", None)
        body_system = entry.get("body_system", None)
        question_type = entry.get("question_type", None)

        # Create QA pair entry (EXACT MedAgentBench format)
        qa_pair = {
            "id": f"qa_{task_id}",
            "question": question,
            "answer": answer,
            "task_id": task_id
        }

        # Add optional metadata fields only if they exist
        if medical_task:
            qa_pair["medical_task"] = medical_task
        if body_system:
            qa_pair["body_system"] = body_system
        if question_type:
            qa_pair["question_type"] = question_type

        qa_pairs[task_id] = qa_pair

    return {"qa_pairs": qa_pairs}


def main():
    """Main processing function."""
    print("=" * 60)
    print("MedXpertQA Processor")
    print("=" * 60)
    print()

    # Step 1: Read input file
    print("Step 1: Reading JSONL file...")
    entries = process_jsonl_file(INPUT_FILE)

    if not entries:
        print("ERROR: No entries found in input file!")
        return 1

    print()

    # Step 2: Generate tasks.json
    print("Step 2: Generating tasks.json...")
    tasks = convert_to_tasks_json(entries)
    print(f"  Created {len(tasks)} tasks")

    # Step 3: Generate db.json
    print("Step 3: Generating db.json...")
    db_data = convert_to_db_json(entries)
    qa_count = len(db_data["qa_pairs"])
    print(f"  Created {qa_count} QA pairs")

    # Step 4: Create output directory
    print("Step 4: Creating output directory...")
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    print(f"  Output directory: {OUTPUT_DIR}")

    # Step 5: Write files
    print("Step 5: Writing output files...")

    # Write tasks.json
    with open(TASKS_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    print(f"  Created: {TASKS_OUTPUT}")

    # Write db.json
    with open(DB_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, indent=2, ensure_ascii=False)
    print(f"  Created: {DB_OUTPUT}")

    print()
    print("=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print()
    print(f"Output files:")
    print(f"  Tasks:  {TASKS_OUTPUT}")
    print(f"  DB:     {DB_OUTPUT}")
    print()
    print(f"Summary:")
    print(f"  - Total tasks:   {len(tasks)}")
    print(f"  - Total QA pairs: {qa_count}")
    print()

    # Show samples
    print("=" * 60)
    print("Sample Data (First 2 Entries)")
    print("=" * 60)
    print()

    print("Sample Task (from tasks.json):")
    print(json.dumps(tasks[0], indent=2, ensure_ascii=False))
    print()

    print("Sample QA Pair (from db.json):")
    first_qa_id = list(db_data["qa_pairs"].keys())[0]
    print(json.dumps(db_data["qa_pairs"][first_qa_id], indent=2, ensure_ascii=False))
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
