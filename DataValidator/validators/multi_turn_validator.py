#!/usr/bin/env python3
"""
Multi-turn Dialogue Validator - Validates multi-turn conversation structure.
"""

from typing import Dict, List, Any, Optional
from ..models import ValidationIssue, ValidationLevel


class MultiTurnValidator:
    """Validates multi-turn dialogue structure."""

    # Multi-turn indicators (English + Chinese)
    MULTI_TURN_INDICATORS = [
        # English indicators
        "follow-up", "follow up", "additional", "more information",
        "clarification", "also", "another question", "further",
        # Chinese indicators
        "随访", "复查", "补充", "更多信息",
        "澄清", "还有", "另外", "进一步", "另外想问"
    ]

    # Dialogue markers
    DIALOGUE_MARKERS = [
        # English markers
        "patient:", "doctor:", "physician:", "assistant:", "user:", "clinician:",
        # Chinese markers
        "患者:", "医生:", "医师:", "助理:", "用户:", "临床医生:"
    ]

    def count_turns(self, task: Dict[str, Any]) -> int:
        """
        Count the number of turns in a task.

        Args:
            task: Task dictionary

        Returns:
            Number of dialogue turns detected
        """
        user_scenario = task.get("user_scenario", {})
        if not isinstance(user_scenario, dict):
            return 0

        instructions = user_scenario.get("instructions", {})
        task_instructions = instructions.get("task_instructions", "")

        if not task_instructions:
            return 0

        # Count dialogue lines
        lines = task_instructions.split('\n')
        dialogue_lines = [
            line for line in lines
            if any(marker in line.lower() for marker in self.DIALOGUE_MARKERS)
        ]

        return len(dialogue_lines)

    def has_multi_turn_indicators(self, text: str) -> bool:
        """Check if text contains multi-turn indicators."""
        return any(
            indicator.lower() in text.lower()
            for indicator in self.MULTI_TURN_INDICATORS
        )

    def validate_turn_count(self, task: Dict[str, Any], task_idx: int, min_turns: int = 4) -> List[ValidationIssue]:
        """
        Validate turn count meets minimum requirement.

        Args:
            task: Task dictionary
            task_idx: Index of the task
            min_turns: Minimum required turns

        Returns:
            List of validation issues
        """
        issues = []
        task_id = task.get("id", f"task_{task_idx}")

        num_turns = self.count_turns(task)

        if num_turns > 0 and num_turns < min_turns:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="multi_turn",
                message=f"Few dialogue turns detected ({num_turns} lines, minimum {min_turns} recommended)",
                task_id=task_id,
                suggestion=f"Consider adding more dialogue turns for comprehensive evaluation (aim for at least {min_turns})"
            ))

        return issues

    def get_turn_statistics(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate turn statistics across all tasks.

        Args:
            tasks: List of task dictionaries

        Returns:
            Dictionary with turn statistics
        """
        turn_counts = []

        for task in tasks:
            turns = self.count_turns(task)
            if turns > 0:
                turn_counts.append(turns)

        if not turn_counts:
            return {
                "total_multi_turn_tasks": 0,
                "avg_turns": 0,
                "max_turns": 0,
                "min_turns": 0,
            }

        return {
            "total_multi_turn_tasks": len(turn_counts),
            "avg_turns": sum(turn_counts) / len(turn_counts),
            "max_turns": max(turn_counts),
            "min_turns": min(turn_counts),
        }
