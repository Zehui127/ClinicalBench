#!/usr/bin/env python3
"""
Clinical Task Classifier
Classifies general_practice medical tasks into specialty domains based on keyword matching
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# Specialty keyword mappings
SPECIALTY_KEYWORDS = {
    "nephrology": [
        "kidney", "renal", "egfr", "creatinine", "dialysis", "glomerul",
        "nephrit", "proteinuria", "hematuria", "albuminuria", "bun",
        "potassium", "electrolyte", "ckd", "chronic kidney"
    ],
    "gastroenterology": [
        "gi", "gastro", "stomach", "digestive", "liver", "hepat",
        "pancreatit", "colon", "diarrhea", "constipat", "endoscop",
        "egd", "colonoscop", "cirrhos", "hepatit", "bilirubin",
        "alt", "ast", "ulcer", "gerd", "reflux", "ibs"
    ],
    "cardiology": [
        "heart", "cardiac", "ecg", "ekg", "echo", "chest pain",
        "blood pressure", "hypertension", "arrhythmia", "palpitation",
        "stent", "catheter", "coronary", "myocardial", "infarction",
        "mi", "angina", "heart failure", "pacemaker", "defibrillator"
    ],
    "neurology": [
        "brain", "neuro", "seizure", "stroke", "headache", "migraine",
        "neural", "cognitive", "dementia", "parkinson", "multiple sclerosis",
        "concussion", "spinal", "nerve", "numbness", "weakness",
        "paralysis", "ataxia", "tremor", "epilepsy"
    ],
    "endocrinology": [
        "diabetes", "thyroid", "hormone", "insulin", "glucose",
        "hba1c", "tsh", "t4", "metabolism", "cortisol", "parathyroid",
        "hyperglycemia", "hypoglycemia", "metabolic", "obesity"
    ]
}


def classify_task(description: str) -> str:
    """
    Classify a task to a specialty based on keyword matching.

    Args:
        description: Task description text

    Returns:
        Specialty name (e.g., "nephrology")
    """
    description_lower = description.lower()

    # Check each specialty's keywords
    for specialty, keywords in SPECIALTY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in description_lower:
                return specialty

    # Default to general_practice if no match
    return "general_practice"


def classify_and_split_tasks(
    input_files: List[str],
    output_dir: str
) -> Dict[str, List[dict]]:
    """
    Classify tasks from input files and split by specialty.

    Args:
        input_files: List of input JSON files with tasks
        output_dir: Output directory for classified tasks

    Returns:
        Dictionary mapping specialty names to lists of tasks
    """
    classified_tasks = {
        "nephrology": [],
        "gastroenterology": [],
        "cardiology": [],
        "neurology": [],
        "endocrinology": [],
        "general_practice": []  # Remaining tasks
    }

    # Load and classify all tasks
    for input_file in input_files:
        print(f"Processing {input_file}...")
        with open(input_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)

        for task in tasks:
            description = task.get("description", "")
            specialty = classify_task(description)
            classified_tasks[specialty].append(task)

        print(f"  Loaded {len(tasks)} tasks")

    # Print summary
    print("\n=== Classification Summary ===")
    for specialty, tasks in classified_tasks.items():
        print(f"{specialty}: {len(tasks)} tasks")

    # Save classified tasks
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for specialty, tasks in classified_tasks.items():
        if not tasks:
            print(f"\nSkipping {specialty} (no tasks)")
            continue

        # Convert task format
        tau2_tasks = []
        for i, task in enumerate(tasks):
            tau2_task = {
                "id": task.get("id", f"{specialty}_{i}"),
                "description": {
                    "purpose": f"{specialty.capitalize()} clinical task",
                    "relevant_policies": None,
                    "notes": None
                },
                "user_scenario": {
                    "persona": None,
                    "instructions": {
                        "task_instructions": task.get("description", ""),
                        "domain": "clinical",
                        "reason_for_call": f"{specialty.capitalize()} consultation",
                        "known_info": f"Clinical case requiring {specialty} evaluation",
                        "unknown_info": None
                    }
                },
                "ticket": task.get("description", ""),
                "initial_state": None,
                "evaluation_criteria": {
                    "actions": [],
                    "communicate_info": [],
                    "nl_assertions": []
                },
                "annotations": {
                    "original_format": task.get("metadata", {}).get("source", "unknown"),
                    "original_department": task.get("department", "unknown"),
                    "difficulty": task.get("difficulty", "moderate")
                }
            }
            tau2_tasks.append(tau2_task)

        # Save tasks
        domain_name = f"clinical_{specialty}"
        tasks_file = output_path / f"{domain_name}_tasks.json"
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tau2_tasks, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(tau2_tasks)} tasks to {tasks_file}")

        # Create split file (base split contains all tasks)
        split_file = output_path / f"{domain_name}_split_tasks.json"
        task_ids = [task["id"] for task in tau2_tasks]
        with open(split_file, "w", encoding="utf-8") as f:
            json.dump({"base": task_ids}, f, indent=2)

    return classified_tasks


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Classify medical tasks into clinical specialty domains"
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="Input task JSON files from UniClinicalDataEngine output"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="data/tau2/domains/classified",
        help="Output directory for classified tasks"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("CLINICAL TASK CLASSIFIER")
    print("=" * 60)

    # Classify tasks
    result = classify_and_split_tasks(args.input, args.output)

    print("\n=== Complete ===")
    print(f"Classified tasks saved to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
