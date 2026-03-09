#!/usr/bin/env python3
"""
Batch Process MedXpertQA to Tau2 Consultation Dialogues

This script converts the entire medxpertqa dataset (2,450 tasks) into
tau2-format consultation dialogues, organized by clinical department.
"""

import json
import sys
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "UniClinicalDataEngine" / "generators"))

from mcq_converter import MCQToDialogueConverter


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_progress(current: int, total: int, department: str = ""):
    """Print progress bar."""
    percent = (current / total) * 100
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = "█" * filled + "-" * (bar_length - filled)

    dept_info = f" [{department}]" if department else ""
    print(f"\r  [{bar}] {percent:.1f}% ({current}/{total}){dept_info}", end="", flush=True)


def group_tasks_by_department(tasks: List[Dict]) -> Dict[str, List[Dict]]:
    """Group tasks by their clinical department.

    Args:
        tasks: List of MCQ task dictionaries

    Returns:
        Dictionary mapping department names to task lists
    """
    from utils import parse_notes, map_to_tau2_domain

    grouped = defaultdict(list)

    for task in tasks:
        notes = task.get("description", {}).get("notes", "")
        parsed = parse_notes(notes)
        system = parsed.get("system", "other")
        department = map_to_tau2_domain(system)

        grouped[department].append(task)

    return dict(grouped)


def batch_convert_department(
    tasks: List[Dict],
    department: str,
    converter: MCQToDialogueConverter,
) -> List[Dict]:
    """Convert all tasks for a specific department.

    Args:
        tasks: List of MCQ tasks for this department
        department: Department name
        converter: MCQ to dialogue converter

    Returns:
        List of tau2-format task dictionaries
    """
    results = []

    for i, task in enumerate(tasks):
        try:
            # Convert to dialogue
            dialogue = converter.generate(task)

            # Convert to tau2 format
            tau2_task = converter.to_tau2_format(dialogue)

            # Update task ID to include department
            tau2_task["id"] = f"{department.replace('clinical_', '')}_{task.get('id', 'unknown')}"

            results.append(tau2_task)

        except Exception as e:
            print(f"\n  Error converting task {task.get('id')}: {e}")
            continue

    return results


def save_department_tasks(
    department: str,
    tasks: List[Dict],
    output_base_dir: Path,
) -> Path:
    """Save converted tasks to department directory.

    Args:
        department: Department name (e.g., "clinical_neurology")
        tasks: List of tau2-format tasks
        output_base_dir: Base output directory

    Returns:
        Path to saved file
    """
    # Create department directory
    dept_dir = output_base_dir / department
    dept_dir.mkdir(parents=True, exist_ok=True)

    # Save tasks.json
    output_file = dept_dir / "tasks.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    return output_file


def update_department_db(department: str, tasks: List[Dict], output_base_dir: Path):
    """Create/update db.json with patient information.

    Args:
        department: Department name
        tasks: List of tau2-format tasks
        output_base_dir: Base output directory
    """
    # Extract patient information from tasks
    patients = {}

    for task in tasks:
        init_actions = task.get("initial_state", {}).get("initialization_actions", [])
        if init_actions:
            patient_info = init_actions[0].get("arguments", {})
            mrn = patient_info.get("mrn")

            if mrn:
                patients[mrn] = {
                    "name": patient_info.get("name"),
                    "age": patient_info.get("age"),
                    "gender": patient_info.get("gender"),
                    "chief_complaint": task.get("ticket", ""),
                    "department": department,
                }

    # Save db.json
    dept_dir = output_base_dir / department
    db_file = dept_dir / "db.json"

    db_data = {"patients": patients}

    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(db_data, f, indent=2, ensure_ascii=False)


def generate_department_policy(department: str, output_base_dir: Path):
    """Generate policy.md for a department.

    Args:
        department: Department name
        output_base_dir: Base output directory
    """
    # Department-specific policy templates
    policies = {
        "clinical_neurology": """# Clinical Neurology Domain Policy

## Overview
This domain specializes in brain and nervous system consultations.

## Clinical Guidelines
- Assess stroke risk using common risk factors
- Classify headaches by location and characteristics
- Evaluate seizure types and consciousness
- Screen for neurological red flags

## Available Tools
- `assess_stroke_risk(age, hypertension, diabetes, smoking)`: Basic stroke risk assessment
- `interpret_headache(location, severity, duration)`: Classify headache types
- `evaluate_seizure(description, consciousness)`: Determine seizure classification
- `get_patient_by_mrn(mrn)`: Find patients by MRN
""",
        "clinical_cardiology": """# Clinical Cardiology Domain Policy

## Overview
This domain specializes in heart and cardiovascular system consultations.

## Clinical Guidelines
- Assess cardiovascular risk factors
- Evaluate chest pain using typical/atypical features
- Monitor blood pressure and heart rate
- Screen for cardiac red flags

## Available Tools
- `assess_cardiovascular_risk(age, bp, cholesterol)`: Assess cardiac risk
- `interpret_ekg(ekg_data)`: Interpret EKG results
- `evaluate_blood_pressure(systolic, diastolic)`: Classify BP severity
- `get_patient_by_mrn(mrn)`: Find patients by MRN
""",
        "clinical_gastroenterology": """# Clinical Gastroenterology Domain Policy

## Overview
This domain specializes in digestive system and GI tract consultations.

## Clinical Guidelines
- Evaluate liver function tests (ALT, AST, bilirubin)
- Use APRI score for liver fibrosis assessment
- Assess anemia with gender-specific thresholds
- Screen for GI conditions based on symptoms

## Available Tools
- `get_patient_liver_function(patient_id)`: Retrieve liver function tests
- `evaluate_anemia(hemoglobin, age, gender)`: Assess anemia severity
- `assess_liver_fibrosis(alt, ast, platelets)`: Calculate APRI score
- `get_patient_by_mrn(mrn)`: Find patients by MRN
""",
        "clinical_endocrinology": """# Clinical Endocrinology Domain Policy

## Overview
This domain specializes in hormonal and metabolic consultations.

## Clinical Guidelines
- Evaluate blood glucose levels
- Assess thyroid function
- Monitor hormonal imbalances
- Screen for endocrine emergencies

## Available Tools
- `evaluate_blood_glucose(glucose_level)`: Assess glucose status
- `assess_thyroid_function(tsh, t4, t3)`: Evaluate thyroid function
- `get_patient_by_mrn(mrn)`: Find patients by MRN
""",
        "clinical_nephrology": """# Clinical Nephrology Domain Policy

## Overview
This domain specializes in kidney and renal system consultations.

## Clinical Guidelines
- Evaluate kidney function (creatinine, eGFR)
- Assess fluid and electrolyte balance
- Monitor urinary symptoms
- Screen for renal emergencies

## Available Tools
- `evaluate_kidney_function(creatinine, age)`: Calculate eGFR
- `assess_eGFR(egfr_value)`: Classify kidney disease stage
- `get_patient_by_mrn(mrn)`: Find patients by MRN
""",
    }

    # Get policy or use default
    policy = policies.get(
        department,
        f"# {department.title()}\n\n## Overview\nClinical consultations for {department}.\n\n## Available Tools\n- `get_patient_by_mrn(mrn)`: Find patients by MRN\n"
    )

    # Save policy.md
    dept_dir = output_base_dir / department
    policy_file = dept_dir / "policy.md"

    with open(policy_file, "w", encoding="utf-8") as f:
        f.write(policy)


def main():
    """Main batch processing function."""
    print_header("MEDXPERTQA TO TAU2 BATCH CONVERSION")

    # Configuration
    input_file = project_root / "data" / "processed" / "medxpertqa" / "tasks.json"
    output_base_dir = project_root / "data" / "tau2" / "domains"

    converter_config = {
        "dialogue_style": "auto",
        "num_turns": 6,
        "include_rationales": False,
    }

    # Check input file
    print(f"\nInput file: {input_file}")
    if not input_file.exists():
        print(f"ERROR: Input file not found!")
        return

    # Load tasks
    print("\nLoading tasks...")
    with open(input_file, "r", encoding="utf-8-sig") as f:
        all_tasks = json.load(f)

    print(f"  Loaded {len(all_tasks)} tasks")

    # Group by department
    print("\nGrouping tasks by department...")
    grouped_tasks = group_tasks_by_department(all_tasks)

    print(f"  Found {len(grouped_tasks)} departments:")
    for dept, tasks in sorted(grouped_tasks.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"    - {dept}: {len(tasks)} tasks")

    # Initialize converter
    print("\nInitializing converter...")
    converter = MCQToDialogueConverter(converter_config)

    # Process each department
    print_header("PROCESSING DEPARTMENTS")

    total_processed = 0
    total_failed = 0
    results = {}

    start_time = time.time()

    for i, (department, tasks) in enumerate(sorted(grouped_tasks.items()), 1):
        print(f"\n[{i}/{len(grouped_tasks)}] Processing {department}...")
        print(f"  Tasks to convert: {len(tasks)}")

        # Convert tasks
        dept_start = time.time()
        converted = batch_convert_department(tasks, department, converter)
        dept_time = time.time() - dept_start

        # Update statistics
        total_processed += len(converted)
        total_failed += len(tasks) - len(converted)

        # Save results
        output_file = save_department_tasks(department, converted, output_base_dir)
        update_department_db(department, converted, output_base_dir)
        generate_department_policy(department, output_base_dir)

        results[department] = {
            "input_count": len(tasks),
            "output_count": len(converted),
            "failed": len(tasks) - len(converted),
            "time": dept_time,
            "output_file": str(output_file),
        }

        print(f"  Converted: {len(converted)}/{len(tasks)}")
        print(f"  Saved to: {output_file.name}")
        print(f"  Time: {dept_time:.1f}s")

    total_time = time.time() - start_time

    # Print summary
    print_header("CONVERSION SUMMARY")

    print(f"\nTotal tasks processed: {total_processed}/{len(all_tasks)}")
    print(f"Total failed: {total_failed}")
    print(f"Success rate: {(total_processed/len(all_tasks))*100:.1f}%")
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"Average time per task: {total_time/len(all_tasks):.2f}s")

    print("\nDepartment breakdown:")
    print(f"{'Department':<25} {'Input':<8} {'Output':<8} {'Failed':<8} {'Time':<8}")
    print("-" * 65)

    for dept, stats in sorted(results.items(), key=lambda x: x[1]["output_count"], reverse=True):
        print(f"{dept:<25} {stats['input_count']:<8} {stats['output_count']:<8} {stats['failed']:<8} {stats['time']:<8.1f}")

    # Save summary report
    summary_file = output_base_dir / "conversion_summary.json"
    summary_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_input": len(all_tasks),
        "total_output": total_processed,
        "total_failed": total_failed,
        "total_time_seconds": total_time,
        "departments": results,
    }

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print(f"\nSummary report saved to: {summary_file}")

    # Create split_tasks.json for each department
    print("\nCreating split_tasks.json files...")
    for department, tasks_list in grouped_tasks.items():
        dept_dir = output_base_dir / department
        # Simple split (all in train for now)
        split_data = {"train": [f"{dept_dir.name}_{t.get('id', '')}" for t in tasks_list]}

        split_file = dept_dir / "split_tasks.json"
        with open(split_file, "w", encoding="utf-8") as f:
            json.dump(split_data, f, indent=2)

    print(f"  Created {len(results)} split_tasks.json files")

    print_header("BATCH CONVERSION COMPLETE")
    print("\nGenerated files:")
    print("  - tasks.json (converted dialogues)")
    print("  - db.json (patient database)")
    print("  - policy.md (department policies)")
    print("  - split_tasks.json (task splits)")
    print("\nReady for tau2 evaluation!")
    print()


if __name__ == "__main__":
    main()
