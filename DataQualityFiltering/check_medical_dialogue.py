#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Tool for Medical Dialogue Detection
医学问诊多轮对话检测工具

Command-line interface for checking if generated tasks meet medical
consultation dialogue requirements.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, parent_dir)
sys.path.insert(0, str(Path(__file__).parent))

from DataQualityFiltering.validators.medical_dialogue_validator import (
    MedicalDialogueValidator,
    MedicalDialoguePipeline,
)


# Define simple reviewer class inline to avoid import issues
class SimpleMedicalDialogueReviewer:
    """Simple reviewer wrapper around validator."""

    def __init__(
        self,
        min_medical_keywords: int = 2,
        min_dialogue_turns: int = 2,
        strict_mode: bool = False
    ):
        self.validator = MedicalDialogueValidator(
            min_medical_keywords=min_medical_keywords,
            min_dialogue_turns=min_dialogue_turns,
            strict_mode=strict_mode
        )

    def review(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Review task using validator."""
        is_valid, issues = self.validator.validate(task)
        medical_score = self.validator.calculate_medical_score(task)

        return {
            "task_id": task.get("id", task.get("task_id", "")),
            "pass_status": is_valid and medical_score >= 0.2,  # Lower threshold for testing
            "validation_issues": issues,
            "medical_relevance": medical_score,
            "is_medical_dialogue": self.validator.is_medical_dialogue(task),
        }


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    return logging.getLogger(__name__)


def load_tasks(input_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from JSON file.

    Args:
        input_path: Path to input JSON file

    Returns:
        List of task dictionaries
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle different formats
    if isinstance(data, dict):
        tasks = data.get("tasks", data.get("data", [data]))
    elif isinstance(data, list):
        tasks = data
    else:
        raise ValueError(f"Unexpected data format: {type(data)}")

    return tasks


def check_single_task(
    task: Dict[str, Any],
    validator: MedicalDialogueValidator,
    reviewer: SimpleMedicalDialogueReviewer,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Check a single task for medical dialogue compliance.

    Args:
        task: Task dictionary
        validator: Medical dialogue validator
        reviewer: Medical dialogue reviewer
        logger: Logger instance

    Returns:
        Check result dictionary
    """
    task_id = task.get("id", task.get("task_id", "unknown"))

    logger.info(f"Checking task: {task_id}")

    result = {
        "task_id": task_id,
        "timestamp": datetime.now().isoformat(),
    }

    # 1. Quick check: Is this a medical dialogue?
    is_medical = validator.is_medical_dialogue(task)
    result["is_medical_dialogue"] = is_medical

    if not is_medical:
        logger.warning(f"Task '{task_id}' is NOT a medical dialogue")
        result["validation_passed"] = False
        result["review_passed"] = False
        result["overall_passed"] = False
        result["reason"] = "Task does not appear to be a medical dialogue"
        result["medical_relevance_score"] = 0.0
        return result

    logger.info(f"Task '{task_id}' appears to be a medical dialogue")

    # 2. Validate structure
    is_valid, validation_issues = validator.validate(task)
    result["validation_passed"] = is_valid
    result["validation_issues"] = validation_issues

    # 3. Review quality
    review = reviewer.review(task)
    result["review_passed"] = review["pass_status"]
    result["review"] = review

    # 4. Medical relevance score
    medical_score = validator.calculate_medical_score(task)
    result["medical_relevance_score"] = round(medical_score, 3)

    # 5. Overall assessment
    result["overall_passed"] = is_valid and review["pass_status"]

    if result["overall_passed"]:
        logger.info(f"Task '{task_id}' PASSED all checks")
    else:
        logger.warning(f"Task '{task_id}' FAILED some checks")

    return result


def check_batch_tasks(
    tasks: List[Dict[str, Any]],
    validator: MedicalDialogueValidator,
    reviewer: SimpleMedicalDialogueReviewer,
    pipeline: MedicalDialoguePipeline,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Check multiple tasks for medical dialogue compliance.

    Args:
        tasks: List of task dictionaries
        validator: Medical dialogue validator
        reviewer: Medical dialogue reviewer
        pipeline: Medical dialogue pipeline
        logger: Logger instance

    Returns:
        Batch check result dictionary
    """
    logger.info("=" * 70)
    logger.info("MEDICAL DIALOGUE BATCH CHECK")
    logger.info("=" * 70)
    logger.info(f"Total tasks to check: {len(tasks)}")

    results = []
    medical_dialogue_count = 0
    passed_count = 0

    for idx, task in enumerate(tasks, 1):
        task_id = task.get("id", task.get("task_id", f"task_{idx}"))

        logger.info(f"\n[{idx}/{len(tasks)}] Checking task: {task_id}")

        result = check_single_task(task, validator, reviewer, logger)
        results.append(result)

        if result["is_medical_dialogue"]:
            medical_dialogue_count += 1

        if result["overall_passed"]:
            passed_count += 1

    # Calculate statistics
    total_tasks = len(tasks)
    non_medical_count = total_tasks - medical_dialogue_count
    failed_count = medical_dialogue_count - passed_count

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_tasks": total_tasks,
        "medical_dialogues": medical_dialogue_count,
        "non_medical_tasks": non_medical_count,
        "passed_tasks": passed_count,
        "failed_tasks": failed_count,
        "pass_rate": round((passed_count / medical_dialogue_count * 100) if medical_dialogue_count > 0 else 0, 2),
        "results": results,
    }

    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("BATCH CHECK SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total tasks:          {total_tasks}")
    logger.info(f"Medical dialogues:    {medical_dialogue_count}")
    logger.info(f"Non-medical tasks:    {non_medical_count}")
    logger.info(f"Passed checks:        {passed_count}")
    logger.info(f"Failed checks:        {failed_count}")
    logger.info(f"Pass rate:            {summary['pass_rate']}%")
    logger.info("=" * 70)

    return summary


def save_results(
    results: Dict[str, Any],
    output_path: str,
    format: str = "json"
) -> None:
    """
    Save check results to file.

    Args:
        results: Results dictionary
        output_path: Path to output file
        format: Output format (json or markdown)
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if format == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    elif format == "markdown":
        with open(output_path, "w", encoding="utf-8") as f:
            write_markdown_report(results, f)
    else:
        raise ValueError(f"Unsupported format: {format}")


def write_markdown_report(results: Dict[str, Any], file) -> None:
    """
    Write results as markdown report.

    Args:
        results: Results dictionary
        file: File object to write to
    """
    file.write("# Medical Dialogue Check Report\n\n")
    file.write(f"**Generated:** {results['timestamp']}\n\n")

    file.write("## Summary\n\n")
    file.write(f"- **Total Tasks:** {results['total_tasks']}\n")
    file.write(f"- **Medical Dialogues:** {results['medical_dialogues']}\n")
    file.write(f"- **Non-Medical Tasks:** {results['non_medical_tasks']}\n")
    file.write(f"- **Passed Checks:** {results['passed_tasks']}\n")
    file.write(f"- **Failed Checks:** {results['failed_tasks']}\n")
    file.write(f"- **Pass Rate:** {results['pass_rate']}%\n\n")

    file.write("## Results\n\n")

    for result in results["results"]:
        task_id = result["task_id"]
        file.write(f"### Task: {task_id}\n\n")

        if result["is_medical_dialogue"]:
            file.write(f"- **Medical Dialogue:** Yes\n")
            file.write(f"- **Medical Relevance:** {result['medical_relevance_score']:.3f}\n")
            file.write(f"- **Validation:** {'PASSED' if result['validation_passed'] else 'FAILED'}\n")
            file.write(f"- **Review:** {'PASSED' if result['review_passed'] else 'FAILED'}\n")
            file.write(f"- **Overall:** {'PASSED' if result['overall_passed'] else 'FAILED'}\n")

            if result.get("validation_issues"):
                file.write(f"\n**Issues:**\n")
                for issue in result["validation_issues"]:
                    file.write(f"  - {issue}\n")

            if result.get("review"):
                review = result["review"]
                file.write(f"\n**Scores:**\n")
                for dim, score in review.get("dimension_scores", {}).items():
                    file.write(f"  - {dim}: {score}/5.0\n")

                if review.get("comments"):
                    file.write(f"\n**Comments:**\n")
                    for comment in review["comments"]:
                        file.write(f"  - {comment}\n")
        else:
            file.write(f"- **Medical Dialogue:** No\n")
            file.write(f"- **Reason:** {result.get('reason', 'Unknown')}\n")

        file.write("\n---\n\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Check if generated tasks meet medical consultation dialogue requirements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check a single task file
  python check_medical_dialogue.py tasks.json

  # Check with custom thresholds
  python check_medical_dialogue.py tasks.json --min-keywords 3 --min-turns 3

  # Save results to custom location
  python check_medical_dialogue.py tasks.json -o results/check_report.json

  # Generate markdown report
  python check_medical_dialogue.py tasks.json --format markdown -o report.md

  # Enable verbose logging
  python check_medical_dialogue.py tasks.json --verbose
        """
    )

    parser.add_argument(
        "input",
        help="Path to input JSON file containing tasks"
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Path to output file (default: auto-generated in ./outputs)"
    )

    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format (default: json)"
    )

    parser.add_argument(
        "--min-keywords",
        type=int,
        default=2,
        help="Minimum number of medical keywords required (default: 2)"
    )

    parser.add_argument(
        "--min-turns",
        type=int,
        default=2,
        help="Minimum number of dialogue turns required (default: 2)"
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode (treat warnings as errors)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.verbose)

    try:
        # Load tasks
        logger.info(f"Loading tasks from: {args.input}")
        tasks = load_tasks(args.input)
        logger.info(f"Loaded {len(tasks)} tasks")

        # Initialize components
        validator = MedicalDialogueValidator(
            min_medical_keywords=args.min_keywords,
            min_dialogue_turns=args.min_turns,
            strict_mode=args.strict
        )

        reviewer = SimpleMedicalDialogueReviewer(
            min_medical_keywords=args.min_keywords,
            min_dialogue_turns=args.min_turns,
            strict_mode=args.strict
        )

        pipeline = MedicalDialoguePipeline(
            min_medical_keywords=args.min_keywords,
            min_dialogue_turns=args.min_turns,
            strict_mode=args.strict
        )

        # Run batch check
        results = check_batch_tasks(tasks, validator, reviewer, pipeline, logger)

        # Determine output path
        if args.output:
            output_path = args.output
        else:
            os.makedirs("./outputs", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = "md" if args.format == "markdown" else "json"
            output_path = f"./outputs/medical_dialogue_check_{timestamp}.{ext}"

        # Save results
        logger.info(f"\nSaving results to: {output_path}")
        save_results(results, output_path, args.format)

        logger.info("\nCheck completed successfully!")

        # Return exit code based on results
        return 0 if results["pass_rate"] >= 80 else 1

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
