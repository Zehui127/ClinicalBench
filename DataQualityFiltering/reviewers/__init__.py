#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clinical Task Reviewers
临床任务审查器

Manual and automated reviewers for clinical task quality assessment.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseReviewer(ABC):
    """Abstract base class for task reviewers."""

    @abstractmethod
    def review(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review a clinical task.

        Args:
            task: Task dictionary

        Returns:
            Review result with scores and comments
        """
        pass


class ClinicalReviewer(BaseReviewer):
    """
    Automated clinical task reviewer.
    自动化临床任务审查器

    Reviews clinical tasks for quality and completeness.
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the reviewer.

        Args:
            strict_mode: Enable strict validation criteria
        """
        self.strict_mode = strict_mode

    def review(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review a clinical task comprehensively.

        Args:
            task: Task dictionary

        Returns:
            Review result with scores for each dimension
        """
        review = {
            "task_id": task.get("id", task.get("task_id", "")),
            "overall_score": 0.0,
            "dimension_scores": {},
            "comments": [],
            "recommendations": [],
            "pass_status": False,
        }

        # Score each dimension
        review["dimension_scores"]["clinical_accuracy"] = self._score_clinical_accuracy(task)
        review["dimension_scores"]["scenario_realism"] = self._score_scenario_realism(task)
        review["dimension_scores"]["evaluation_completeness"] = self._score_evaluation_completeness(task)
        review["dimension_scores"]["difficulty_appropriateness"] = self._score_difficulty_appropriateness(task)

        # Calculate overall score
        dimension_scores = list(review["dimension_scores"].values())
        review["overall_score"] = round(sum(dimension_scores) / len(dimension_scores), 2)

        # Generate comments and recommendations
        review["comments"] = self._generate_comments(task, review)
        review["recommendations"] = self._generate_recommendations(task, review)

        # Determine pass status
        review["pass_status"] = review["overall_score"] >= 3.5

        return review

    def _score_clinical_accuracy(self, task: Dict[str, Any]) -> float:
        """Score clinical accuracy of the task."""
        score = 3.0  # Base score

        scenario = task.get("clinical_scenario", {})

        # Check for required elements
        if scenario.get("patient_info"):
            score += 0.5

        if scenario.get("diagnosis"):
            score += 0.5

        if scenario.get("vital_signs") or scenario.get("lab_results"):
            score += 0.5

        # Check for clinical coherence
        diagnosis = scenario.get("diagnosis", "").lower()
        symptoms = scenario.get("patient_info", {}).get("symptoms", [])

        if diagnosis and symptoms:
            # Basic symptom-diagnosis matching
            score += 0.5

        return min(5.0, score)

    def _score_scenario_realism(self, task: Dict[str, Any]) -> float:
        """Score scenario realism."""
        score = 3.0  # Base score

        scenario = task.get("clinical_scenario", {})

        # Check for realistic patient details
        patient_info = scenario.get("patient_info", {})
        if patient_info.get("age") and 0 < patient_info["age"] < 120:
            score += 0.5

        if patient_info.get("gender") in ["male", "female", "M", "F"]:
            score += 0.5

        # Check for vital signs within realistic ranges
        vital_signs = scenario.get("vital_signs", {})
        if vital_signs:
            score += 0.5

        # Check for medications or lab results
        if scenario.get("medications") or scenario.get("lab_results"):
            score += 0.5

        return min(5.0, score)

    def _score_evaluation_completeness(self, task: Dict[str, Any]) -> float:
        """Score evaluation task completeness."""
        score = 0.0

        # Check for required elements
        if task.get("id") or task.get("task_id"):
            score += 1.0

        if task.get("description"):
            score += 1.0

        if task.get("clinical_scenario"):
            score += 1.0

        if task.get("tool_call_requirements"):
            tool_reqs = task["tool_call_requirements"]
            if isinstance(tool_reqs, dict):
                if tool_reqs.get("required_tools"):
                    score += 1.0
                if tool_reqs.get("optional_tools"):
                    score += 0.5
            elif isinstance(tool_reqs, list):
                if tool_reqs:
                    score += 1.0

        if task.get("expected_outcome"):
            score += 0.5

        return min(5.0, score)

    def _score_difficulty_appropriateness(self, task: Dict[str, Any]) -> float:
        """Score appropriateness of task difficulty."""
        # Count tools required
        tool_count = len(
            task.get("tool_call_requirements", {})
            .get("required_tools", [])
        )

        # Base score on tool count
        if tool_count <= 3:
            difficulty = "easy"
        elif tool_count <= 6:
            difficulty = "moderate"
        else:
            difficulty = "hard"

        # Check if difficulty matches stated difficulty
        stated_difficulty = task.get("difficulty", "").lower()

        if stated_difficulty:
            if stated_difficulty == difficulty:
                return 5.0
            elif (
                (stated_difficulty == "easy" and difficulty == "moderate") or
                (stated_difficulty == "moderate" and difficulty == "hard")
            ):
                return 4.0
            else:
                return 2.0
        else:
            # Auto-assign difficulty
            return 4.0

    def _generate_comments(
        self,
        task: Dict[str, Any],
        review: Dict[str, Any]
    ) -> List[str]:
        """Generate review comments."""
        comments = []

        # Overall score comment
        overall = review["overall_score"]
        if overall >= 4.5:
            comments.append("Excellent task quality")
        elif overall >= 3.5:
            comments.append("Good task quality")
        elif overall >= 2.5:
            comments.append("Fair task quality - needs improvement")
        else:
            comments.append("Poor task quality - significant issues")

        # Dimension-specific comments
        scores = review["dimension_scores"]
        for dimension, score in scores.items():
            if score < 3.0:
                comments.append(f"Low score in {dimension}: {score}/5.0")

        return comments

    def _generate_recommendations(
        self,
        task: Dict[str, Any],
        review: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []

        scores = review["dimension_scores"]

        # Clinical accuracy recommendations
        if scores["clinical_accuracy"] < 3.0:
            recommendations.append(
                "Improve clinical accuracy: Add more detailed patient "
                "information and ensure diagnosis matches symptoms"
            )

        # Scenario realism recommendations
        if scores["scenario_realism"] < 3.0:
            recommendations.append(
                "Enhance scenario realism: Add realistic vital signs, "
                "lab results, or medications"
            )

        # Completeness recommendations
        if scores["evaluation_completeness"] < 3.0:
            recommendations.append(
                "Improve completeness: Ensure all required fields "
                "(id, description, scenario, tools) are present"
            )

        # Difficulty recommendations
        if scores["difficulty_appropriateness"] < 3.0:
            recommendations.append(
                "Align difficulty: Ensure task difficulty matches "
                "tool complexity"
            )

        return recommendations


class BatchReviewer:
    """
    Batch reviewer for multiple tasks.
    批量审查器

    Reviews multiple tasks in batch.
    """

    def __init__(self, reviewer: Optional[BaseReviewer] = None):
        """
        Initialize the batch reviewer.

        Args:
            reviewer: Reviewer instance (uses ClinicalReviewer if not provided)
        """
        self.reviewer = reviewer or ClinicalReviewer()

    def review_batch(
        self,
        tasks: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Review multiple tasks.

        Args:
            tasks: List of task dictionaries
            show_progress: Whether to show progress updates

        Returns:
            List of review results
        """
        reviews = []

        for i, task in enumerate(tasks, 1):
            review = self.reviewer.review(task)
            reviews.append(review)

            if show_progress and (i % 10 == 0 or i == len(tasks)):
                print(f"Reviewed {i}/{len(tasks)} tasks")

        return reviews

    def get_summary_statistics(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get summary statistics from reviews.

        Args:
            reviews: List of review results

        Returns:
            Summary statistics
        """
        if not reviews:
            return {}

        total_reviews = len(reviews)
        passed = sum(1 for r in reviews if r.get("pass_status", False))
        failed = total_reviews - passed

        overall_scores = [r.get("overall_score", 0) for r in reviews]
        avg_score = sum(overall_scores) / total_reviews if total_reviews > 0 else 0

        dimension_scores = {}
        for dimension in ["clinical_accuracy", "scenario_realism",
                          "evaluation_completeness", "difficulty_appropriateness"]:
            scores = [
                r.get("dimension_scores", {}).get(dimension, 0)
                for r in reviews
            ]
            if scores:
                dimension_scores[dimension] = sum(scores) / len(scores)

        return {
            "total_reviews": total_reviews,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total_reviews * 100) if total_reviews > 0 else 0,
            "average_score": round(avg_score, 2),
            "dimension_averages": dimension_scores,
        }
