#!/usr/bin/env python3
"""
Structure Validator - Validates required fields and data structure.
"""

import re
from typing import Dict, List, Any
from ..models import ValidationIssue, ValidationLevel


class StructureValidator:
    """Validates the structure and required fields of medical dialogue tasks."""

    # Required fields for tau2-bench format
    REQUIRED_FIELDS = [
        "id",
        "description",
        "user_scenario",
        "ticket",
        "evaluation_criteria",
    ]

    # Dialogue markers for multi-turn detection
    DIALOGUE_MARKERS = [
        # English markers
        "patient:", "doctor:", "physician:", "assistant:", "user:", "clinician:",
        # Chinese markers
        "患者:", "医生:", "医师:", "助理:", "用户:", "临床医生:"
    ]

    def validate_task(self, task: Dict[str, Any], task_idx: int) -> List[ValidationIssue]:
        """
        Validate task structure.

        Args:
            task: Task dictionary to validate
            task_idx: Index of the task in the dataset

        Returns:
            List of validation issues
        """
        issues = []
        task_id = task.get("id", f"task_{task_idx}")

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in task:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="structure",
                    message=f"Missing required field: '{field}'",
                    task_id=task_id,
                    suggestion=f"Add '{field}' field to the task"
                ))

        # Validate user_scenario if present
        user_scenario = task.get("user_scenario")
        if isinstance(user_scenario, dict):
            instructions = user_scenario.get("instructions", {})
            if not instructions.get("domain"):
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="content",
                    message="Missing 'domain' in user_scenario.instructions",
                    task_id=task_id,
                    suggestion="Specify the medical domain (e.g., 'cardiology', 'neurology')"
                ))

        # Validate evaluation_criteria if present
        eval_criteria = task.get("evaluation_criteria")
        if eval_criteria:
            self._validate_evaluation_criteria(eval_criteria, task_id, issues)

        return issues

    def _validate_evaluation_criteria(
        self,
        eval_criteria: Dict[str, Any],
        task_id: str,
        issues: List[ValidationIssue]
    ) -> None:
        """Validate evaluation criteria structure."""
        if not isinstance(eval_criteria, dict):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="structure",
                message=f"evaluation_criteria must be a dict, got {type(eval_criteria).__name__}",
                task_id=task_id
            ))
            return

        # Check for actions or communication_checks
        has_actions = eval_criteria.get("actions")
        has_communication_checks = eval_criteria.get("communication_checks")

        if not has_actions and not has_communication_checks:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="evaluation",
                message="evaluation_criteria lacks 'actions' or 'communication_checks'",
                task_id=task_id,
                suggestion="Add specific actions to evaluate or communication checks"
            ))

    def check_multi_turn_structure(self, task: Dict[str, Any], task_id: str, issues: List[ValidationIssue]) -> int:
        """
        Check for multi-turn dialogue structure.

        Returns:
            Number of dialogue turns detected
        """
        user_scenario = task.get("user_scenario", {})
        if not isinstance(user_scenario, dict):
            return 0

        instructions = user_scenario.get("instructions", {})
        task_instructions = instructions.get("task_instructions", "")

        if not task_instructions:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="multi_turn",
                message="No task_instructions found - may be single-turn dialogue",
                task_id=task_id,
                suggestion="Add task_instructions to enable multi-turn evaluation"
            ))
            return 0

        # Check for dialogue pattern
        has_dialogue_structure = any(
            marker.lower() in task_instructions.lower()
            for marker in self.DIALOGUE_MARKERS
        )

        if has_dialogue_structure:
            # Count turns
            lines = task_instructions.split('\n')
            dialogue_lines = [
                line for line in lines
                if any(marker in line.lower() for marker in self.DIALOGUE_MARKERS)
            ]
            num_turns = len(dialogue_lines)

            if num_turns < 4:
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    category="multi_turn",
                    message=f"Few dialogue turns detected ({num_turns} lines)",
                    task_id=task_id,
                    suggestion="Consider adding more turns for comprehensive multi-turn evaluation"
                ))

            return num_turns
        else:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="multi_turn",
                message="task_instructions doesn't contain clear dialogue structure",
                task_id=task_id,
                suggestion="Use 'Patient:', 'Doctor:', or similar markers (including Chinese: '患者:', '医生:') to structure dialogue"
            ))
            return 0
