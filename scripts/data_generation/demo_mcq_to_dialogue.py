#!/usr/bin/env python3
"""
MCQ to Dialogue Converter Demonstration

This script demonstrates the conversion of medical multiple-choice questions
into clinical consultation dialogue data compatible with tau2 format.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import directly from files to avoid package import issues
sys.path.insert(0, str(project_root / "UniClinicalDataEngine" / "generators"))
from mcq_converter import MCQToDialogueConverter
from base_generator import DialogueTurn


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_before_after(mcq_task: dict, tau2_task: dict, index: int):
    """Print before and after comparison."""
    print(f"\n--- EXAMPLE {index + 1}: {mcq_task.get('id', 'Unknown')} ---\n")

    # BEFORE: Original MCQ
    print("BEFORE (Original MCQ Format):")
    print("-" * 40)
    print(f"Task ID: {mcq_task.get('id', 'N/A')}")
    print(f"Purpose: {mcq_task.get('description', {}).get('purpose', 'N/A')}")
    print(f"Notes: {mcq_task.get('description', {}).get('notes', 'N/A')}")

    instructions = mcq_task.get('user_scenario', {}).get('instructions', {}).get('task_instructions', '')
    # Truncate very long instructions
    if len(instructions) > 600:
        instructions = instructions[:600] + "..."

    print(f"\nQuestion:\n{instructions}")

    # AFTER: Tau2 Consultation Dialogue
    print("\n\nAFTER (Tau2 Consultation Format):")
    print("-" * 40)
    print(f"Task ID: {tau2_task.get('id', 'N/A')}")
    print(f"Department: {tau2_task.get('description', {}).get('notes', 'N/A')}")

    # Print dialogue
    dialogue_text = tau2_task.get('user_scenario', {}).get('instructions', {}).get('dialogue', '')
    if dialogue_text:
        print("\nConsultation Dialogue:")
        print(dialogue_text[:800])
        if len(dialogue_text) > 800:
            print("...")

    # Print patient info
    print("\n\nPatient Profile:")
    print("-" * 40)
    init_actions = tau2_task.get('initial_state', {}).get('initialization_actions', [])
    if init_actions:
        patient_info = init_actions[0].get('arguments', {})
        print(f"  Name: {patient_info.get('name', 'N/A')}")
        print(f"  Age: {patient_info.get('age', 'N/A')}")
        print(f"  Gender: {patient_info.get('gender', 'N/A')}")
        print(f"  MRN: {patient_info.get('mrn', 'N/A')}")

    # Print known info
    known_info = tau2_task.get('user_scenario', {}).get('instructions', {}).get('known_info', '')
    if known_info:
        print(f"\n  Known Info: {known_info}")

    # Print ticket
    ticket = tau2_task.get('ticket', '')
    if ticket:
        print(f"\n  Chief Complaint: {ticket}")

    # Print expected tools
    eval_criteria = tau2_task.get('evaluation_criteria')
    if eval_criteria and eval_criteria.get('actions'):
        print(f"\n  Expected Tools: {[a.get('name') for a in eval_criteria['actions']]}")


def main():
    """Main demonstration function."""
    print_section("MCQ TO DIALOGUE CONVERTER DEMONSTRATION")

    # Load the medxpertqa dataset
    print("Loading medxpertqa dataset...")
    input_file = project_root / "data" / "processed" / "medxpertqa" / "tasks.json"

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return

    with open(input_file, 'r', encoding='utf-8-sig') as f:
        mcq_tasks = json.load(f)

    print(f"Loaded {len(mcq_tasks)} tasks")

    # Find examples from different departments
    print("\nFinding examples from different clinical departments...")

    examples = {
        'nervous': None,      # Neurology
        'cardiovascular': None,  # Cardiology
        'digestive': None,    # Gastroenterology
    }

    for task in mcq_tasks:
        notes = task.get('description', {}).get('notes', '').lower()

        if 'nervous' in notes and not examples['nervous']:
            examples['nervous'] = task
        elif 'cardiovascular' in notes and not examples['cardiovascular']:
            examples['cardiovascular'] = task
        elif 'digestive' in notes and not examples['digestive']:
            examples['digestive'] = task

        if all(examples.values()):
            break

    # Initialize converter
    print("\nInitializing MCQ to Dialogue Converter...")
    converter_config = {
        'dialogue_style': 'auto',
        'num_turns': 6,
        'include_rationales': False,
    }
    converter = MCQToDialogueConverter(converter_config)

    # Convert examples
    print("Converting examples to consultation dialogues...")

    results = []
    for system, task in examples.items():
        if task:
            print(f"  - Converting {system} system task: {task.get('id')}")
            dialogue = converter.generate(task)
            tau2_task = converter.to_tau2_format(dialogue)
            results.append((task, tau2_task))

    # Print before/after comparisons
    print_section("BEFORE/AFTER COMPARISON")

    for i, (mcq_task, tau2_task) in enumerate(results):
        print_before_after(mcq_task, tau2_task, i)

    # Print statistics
    print_section("CONVERSION STATISTICS")

    print(f"Tasks converted: {len(results)}")
    print(f"\nDepartments covered:")
    for i, (mcq_task, tau2_task) in enumerate(results):
        dept = tau2_task.get('user_scenario', {}).get('instructions', {}).get('domain', 'Unknown')
        print(f"  - {dept.capitalize()}")

    # Save results
    print_section("SAVING RESULTS")

    output_dir = project_root / "data" / "processed" / "medxpertqa"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "dialogue_examples.json"
    tau2_results = [tau2 for _, tau2 in results]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tau2_results, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(tau2_results)} dialogue examples to: {output_file}")

    print_section("DEMONSTRATION COMPLETE")
    print("\nNext steps:")
    print("  1. Review the generated dialogues")
    print("  2. Adjust templates if needed")
    print("  3. Scale to full dataset (2,450 tasks)")
    print()


if __name__ == "__main__":
    main()
