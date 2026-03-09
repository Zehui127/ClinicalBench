#!/usr/bin/env python3
"""
Tau2 Validation Script for Generated Clinical Dialogues

This script validates the generated consultation dialogues against tau2 requirements
and runs a simple compatibility test.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# Add tau2 to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tau2.registry import registry


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def load_generated_tasks(department: str) -> List[Dict]:
    """Load generated tau2 tasks for a department.

    Args:
        department: Department name (e.g., "clinical_neurology")

    Returns:
        List of tau2 task dictionaries
    """
    tasks_file = Path("data/tau2/domains") / department / "tasks.json"

    if not tasks_file.exists():
        return []

    with open(tasks_file, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_task_structure(task: Dict) -> tuple[bool, List[str]]:
    """Validate a single tau2 task structure.

    Args:
        task: Tau2 task dictionary

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Required top-level fields
    required_fields = ["id", "description", "user_scenario", "ticket", "initial_state"]
    for field in required_fields:
        if field not in task:
            errors.append(f"Missing required field: {field}")

    # Validate description
    if "description" in task:
        desc = task["description"]
        if not isinstance(desc, dict):
            errors.append("description must be a dictionary")
        elif "purpose" not in desc:
            errors.append("description must have 'purpose' field")

    # Validate user_scenario
    if "user_scenario" in task:
        scenario = task["user_scenario"]
        if not isinstance(scenario, dict):
            errors.append("user_scenario must be a dictionary")
        else:
            if "instructions" not in scenario:
                errors.append("user_scenario must have 'instructions' field")
            else:
                instructions = scenario["instructions"]
                if not isinstance(instructions, dict):
                    errors.append("instructions must be a dictionary")
                elif "domain" not in instructions:
                    errors.append("instructions must have 'domain' field")

    # Validate initial_state
    if "initial_state" in task:
        init_state = task["initial_state"]
        if init_state is not None and not isinstance(init_state, dict):
            errors.append("initial_state must be a dictionary or null")

    return (len(errors) == 0, errors)


def validate_dialogue_content(task: Dict) -> tuple[bool, List[str]]:
    """Validate the dialogue content for medical plausibility.

    Args:
        task: Tau2 task dictionary

    Returns:
        Tuple of (is_valid, list_of_warnings)
    """
    warnings = []

    # Get dialogue
    instructions = task.get("user_scenario", {}).get("instructions", {})
    dialogue = instructions.get("dialogue", "")

    if not dialogue:
        warnings.append("No dialogue content found")
        return (True, warnings)

    # Check for dialogue turns
    if "Patient:" not in dialogue or "Clinician:" not in dialogue:
        warnings.append("Dialogue may be missing patient or clinician turns")

    # Check patient profile
    init_actions = task.get("initial_state", {}).get("initialization_actions", [])
    if init_actions:
        patient_info = init_actions[0].get("arguments", {})
        age = patient_info.get("age")
        gender = patient_info.get("gender")

        if not age:
            warnings.append("Patient age is missing")
        if not gender:
            warnings.append("Patient gender is missing")

        # Check for chief complaint
        chief_complaint = task.get("ticket", "")
        if not chief_complaint:
            warnings.append("No chief complaint (ticket) specified")

    return (True, warnings)


def check_tau2_compatibility(department: str, tasks: List[Dict]) -> Dict[str, Any]:
    """Check if tasks are compatible with tau2 framework.

    Args:
        department: Department name
        tasks: List of tau2 tasks

    Returns:
        Dictionary with validation results
    """
    results = {
        "department": department,
        "total_tasks": len(tasks),
        "structure_valid": 0,
        "structure_invalid": 0,
        "content_warnings": 0,
        "errors": [],
        "task_details": [],
    }

    for task in tasks:
        task_id = task.get("id", "unknown")

        # Validate structure
        is_valid, errors = validate_task_structure(task)

        if is_valid:
            results["structure_valid"] += 1
        else:
            results["structure_invalid"] += 1
            results["errors"].append(f"{task_id}: {', '.join(errors[:3])}")

        # Validate content
        is_valid, warnings = validate_dialogue_content(task)
        results["content_warnings"] += len(warnings)

        results["task_details"].append({
            "id": task_id,
            "valid": is_valid,
            "error_count": len(errors),
            "warning_count": len(warnings),
        })

    return results


def run_tau2_domain_check():
    """Run tau2 domain registration check."""
    print_header("TAU2 DOMAIN REGISTRATION CHECK")

    registered_domains = registry.get_info().domains

    print("Registered domains in tau2:")
    for domain in registered_domains:
        if "clinical" in domain:
            print(f"  [OK] {domain}")
        else:
            print(f"      {domain}")

    # Check our generated departments
    clinical_departments = [
        "clinical_neurology",
        "clinical_cardiology",
        "clinical_gastroenterology",
        "clinical_nephrology",
        "clinical_endocrinology",
    ]

    print("\nGenerated departments:")
    all_registered = True
    for dept in clinical_departments:
        if dept in registered_domains:
            print(f"  [OK] {dept} - REGISTERED")
        else:
            print(f"  [FAIL] {dept} - NOT REGISTERED")
            all_registered = False

    return all_registered


def sample_dialogue_for_review(department: str, num_samples: int = 3):
    """Sample dialogues for manual review.

    Args:
        department: Department name
        num_samples: Number of samples to show
    """
    print_header(f"SAMPLE DIALOGUES - {department.upper()}")

    tasks = load_generated_tasks(department)
    if not tasks:
        print(f"No tasks found for {department}")
        return

    # Sample a few tasks
    import random
    samples = random.sample(tasks, min(num_samples, len(tasks)))

    for i, task in enumerate(samples, 1):
        print(f"\n--- Sample {i} ---")
        print(f"Task ID: {task.get('id', 'N/A')}")

        # Patient info
        init_actions = task.get("initial_state", {}).get("initialization_actions", [])
        if init_actions:
            patient = init_actions[0].get("arguments", {})
            print(f"Patient: {patient.get('name', 'N/A')}, {patient.get('age', 'N/A')}y, {patient.get('gender', 'N/A')}")

        # Chief complaint
        print(f"Complaint: {task.get('ticket', 'N/A')}")

        # Dialogue snippet
        dialogue = task.get("user_scenario", {}).get("instructions", {}).get("dialogue", "")
        if dialogue:
            # Show first 400 characters
            snippet = dialogue[:400]
            if len(dialogue) > 400:
                snippet += "..."
            print(f"\nDialogue:\n{snippet}")


def main():
    """Main validation function."""
    print_header("TAU2 VALIDATION - GENERATED CLINICAL DIALOGUES")

    # Step 1: Check tau2 domain registration
    domains_ok = run_tau2_domain_check()

    if not domains_ok:
        print("\n⚠ WARNING: Some clinical domains are not registered in tau2!")
        print("The generated tasks may not work with tau2 evaluation.\n")

    # Step 2: Validate generated tasks
    print_header("STRUCTURAL VALIDATION")

    clinical_departments = [
        "clinical_neurology",
        "clinical_cardiology",
        "clinical_gastroenterology",
        "clinical_nephrology",
        "clinical_endocrinology",
    ]

    all_results = {}
    total_valid = 0
    total_tasks = 0

    for department in clinical_departments:
        tasks = load_generated_tasks(department)
        if not tasks:
            print(f"\n[{department}]")
            print("  No tasks found - skipping")
            continue

        result = check_tau2_compatibility(department, tasks)
        all_results[department] = result

        total_tasks += result["total_tasks"]
        total_valid += result["structure_valid"]

        print(f"\n[{department}]")
        print(f"  Tasks: {result['total_tasks']}")
        print(f"  Structure valid: {result['structure_valid']}")
        print(f"  Structure invalid: {result['structure_invalid']}")

        if result["errors"]:
            print(f"  Errors (first 5):")
            for error in result["errors"][:5]:
                print(f"    - {error}")

    # Step 3: Summary
    print_header("VALIDATION SUMMARY")

    print(f"\nTotal tasks validated: {total_tasks}")
    print(f"Valid structure: {total_valid} ({(total_valid/total_tasks)*100:.1f}%)")
    print(f"Invalid structure: {total_tasks - total_valid} ({((total_tasks - total_valid)/total_tasks)*100:.1f}%)")

    print("\nDepartment breakdown:")
    print(f"{'Department':<30} {'Tasks':<10} {'Valid':<10} {'Invalid':<10}")
    print("-" * 60)

    for dept, result in all_results.items():
        print(f"{dept:<30} {result['total_tasks']:<10} {result['structure_valid']:<10} {result['structure_invalid']:<10}")

    # Step 4: Sample dialogues for review
    sample_dialogue_for_review("clinical_neurology", 2)

    # Step 5: Tau2 compatibility verdict
    print_header("TAU2 COMPATIBILITY VERDICT")

    if domains_ok and total_valid == total_tasks:
        print("\n[PASSED] All generated dialogues are compatible with tau2!")
        print("\nNext steps:")
        print("  1. Run tau2 evaluation: python -m tau2 run --domain clinical_neurology")
        print("  2. Test with an agent: python -m tau2 run --domain clinical_neurology --agent llm_agent")
        print("  3. Evaluate multiple domains")
    elif domains_ok:
        print("\n[WARNING] Some tasks have structural issues")
        print("\nRecommendations:")
        print("  1. Review and fix invalid tasks")
        print("  2. Re-run validation after fixes")
        print("  3. Test with a small subset first")
    else:
        print("\n[FAILED] Clinical domains not registered in tau2")
        print("\nRecommendations:")
        print("  1. Check tau2 domain configuration")
        print("  2. Register clinical domains if needed")
        print("  3. Ensure policy.md files are correct")

    print()


if __name__ == "__main__":
    main()
