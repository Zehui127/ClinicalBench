"""Interactive CLI scoring and file-based score loading for human review."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from DataQualityFiltering.models import ReviewResult, TaskScore


SCORING_DIMENSIONS = [
    ("clinical_accuracy", "Clinical Accuracy (0-5): How clinically accurate is this scenario?"),
    ("scenario_realism", "Scenario Realism (0-5): How realistic is this patient scenario?"),
    ("evaluation_completeness", "Evaluation Completeness (0-5): How complete are the evaluation criteria?"),
    ("difficulty_appropriateness", "Difficulty Appropriateness (0-5): How appropriate is the difficulty level?"),
]


class HumanReviewer:
    """Human review interface: interactive CLI or load from file."""

    def review_interactive(self, tasks: List[Dict[str, Any]]) -> ReviewResult:
        """Interactively score tasks via the terminal.

        Args:
            tasks: List of task dicts (parsed from tasks.json).

        Returns:
            ReviewResult with human scores.
        """
        scores = []
        total = len(tasks)

        for i, task in enumerate(tasks):
            task_id = task.get("id", f"task_{i}")
            print(f"\n{'='*60}")
            print(f"Task {i+1}/{total}: {task_id}")
            print(f"{'='*60}")

            # Display task summary
            self._display_task(task)

            # Collect scores
            dim_scores = {}
            for dim_key, prompt in SCORING_DIMENSIONS:
                dim_scores[dim_key] = self._prompt_score(prompt)

            comments = input("Comments (optional, press Enter to skip): ").strip()

            scores.append(
                TaskScore(
                    task_id=task_id,
                    comments=comments if comments else None,
                    **dim_scores,
                )
            )

        return ReviewResult(reviewer_type="human", scores=scores)

    def load_scores_from_file(self, scores_path: str) -> ReviewResult:
        """Load human review scores from a JSON file.

        Expected format:
        {
            "scores": [
                {
                    "task_id": "...",
                    "clinical_accuracy": 4.0,
                    "scenario_realism": 3.5,
                    "evaluation_completeness": 4.0,
                    "difficulty_appropriateness": 3.0,
                    "comments": "optional"
                },
                ...
            ]
        }

        Args:
            scores_path: Path to the scores JSON file.

        Returns:
            ReviewResult with human scores.
        """
        with open(scores_path, "r") as f:
            data = json.load(f)

        raw_scores = data if isinstance(data, list) else data.get("scores", [])
        scores = [TaskScore.model_validate(s) for s in raw_scores]
        return ReviewResult(reviewer_type="human", scores=scores)

    def _display_task(self, task: Dict[str, Any]) -> None:
        """Display a task summary for human review."""
        desc = task.get("description", {})
        if isinstance(desc, dict):
            purpose = desc.get("purpose", "N/A")
            notes = desc.get("notes", "")
        else:
            purpose = str(desc) if desc else "N/A"
            notes = ""

        scenario = task.get("user_scenario", {})
        if isinstance(scenario, dict):
            persona = scenario.get("persona", "N/A")
            instructions = scenario.get("instructions", "N/A")
            if isinstance(instructions, dict):
                instructions = instructions.get("task_instructions", str(instructions))
        else:
            persona = "N/A"
            instructions = str(scenario)

        eval_criteria = task.get("evaluation_criteria", {})
        if isinstance(eval_criteria, dict):
            actions = eval_criteria.get("actions", [])
            nl_asserts = eval_criteria.get("nl_assertions", [])
        else:
            actions = []
            nl_asserts = []

        print(f"  Purpose: {purpose}")
        if notes:
            print(f"  Notes: {notes}")
        print(f"  Persona: {persona}")
        print(f"  Instructions: {instructions}")
        if actions:
            print(f"  Expected Actions: {len(actions)}")
        if nl_asserts:
            print(f"  NL Assertions: {nl_asserts}")

    def _prompt_score(self, prompt: str) -> float:
        """Prompt the user for a score with validation."""
        while True:
            try:
                val = float(input(f"  {prompt} "))
                if 0 <= val <= 5:
                    return val
                print("    Score must be between 0 and 5.")
            except ValueError:
                print("    Please enter a number between 0 and 5.")
