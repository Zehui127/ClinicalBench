"""Threshold-based task filter."""

from typing import Any, Dict, List, Tuple

from DataQualityFiltering.models import ReviewResult, TaskScore


class TaskFilter:
    """Filters tasks based on review scores and a threshold."""

    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold

    def filter(
        self,
        tasks: List[Dict[str, Any]],
        review: ReviewResult,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Filter tasks into accepted and rejected based on overall score.

        Args:
            tasks: List of task dicts.
            review: ReviewResult containing scores for the tasks.

        Returns:
            Tuple of (accepted_tasks, rejected_tasks).
        """
        score_map = review.get_score_map()

        accepted = []
        rejected = []

        for task in tasks:
            task_id = task.get("id", "")
            score = score_map.get(task_id)

            if score is None:
                # No score for this task — reject by default
                rejected.append(task)
                continue

            if score.overall_score >= self.threshold:
                accepted.append(task)
            else:
                rejected.append(task)

        return accepted, rejected
