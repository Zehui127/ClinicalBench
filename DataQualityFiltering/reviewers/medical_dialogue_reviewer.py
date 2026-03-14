#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Dialogue Reviewer for Clinical Tasks
医学对话审查器

Reviews clinical tasks for medical consultation dialogue quality.
"""

from typing import Dict, List, Any, Optional

try:
    from . import BaseReviewer
    from ..validators.medical_dialogue_validator import MedicalDialogueValidator
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from reviewers import BaseReviewer
    from validators.medical_dialogue_validator import MedicalDialogueValidator


class MedicalDialogueReviewer(BaseReviewer):
    """
    Medical dialogue reviewer for clinical consultation tasks.

    审查临床任务是否符合医学问诊多轮对话的质量要求。

    Reviews:
    - Medical terminology presence and accuracy
    - Multi-turn dialogue structure
    - Consultation pattern authenticity
    - Medical field relevance
    - Dialogue flow and coherence
    """

    def __init__(
        self,
        strict_mode: bool = False,
        min_medical_keywords: int = 2,
        min_dialogue_turns: int = 2
    ):
        """
        Initialize the medical dialogue reviewer.

        Args:
            strict_mode: Enable strict review criteria
            min_medical_keywords: Minimum number of medical keywords required
            min_dialogue_turns: Minimum number of dialogue turns required
        """
        self.strict_mode = strict_mode
        self.validator = MedicalDialogueValidator(
            min_medical_keywords=min_medical_keywords,
            min_dialogue_turns=min_dialogue_turns,
            strict_mode=strict_mode
        )

    def review(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review a clinical task for medical dialogue quality.

        Args:
            task: Task dictionary

        Returns:
            Review result with scores and comments
        """
        review = {
            "task_id": task.get("id", task.get("task_id", "")),
            "overall_score": 0.0,
            "dimension_scores": {},
            "is_medical_dialogue": False,
            "comments": [],
            "recommendations": [],
            "pass_status": False,
        }

        # 1. Check if task is medical dialogue
        is_medical = self.validator.is_medical_dialogue(task)
        review["is_medical_dialogue"] = is_medical

        if not is_medical:
            review["comments"].append("Task does not appear to be a medical dialogue")
            review["recommendations"].append(
                "Ensure task contains medical terminology and dialogue structure"
            )
            return review

        # 2. Validate medical dialogue structure
        is_valid, issues = self.validator.validate(task)
        review["validation_passed"] = is_valid
        review["validation_issues"] = issues

        # 3. Score each dimension
        review["dimension_scores"]["medical_relevance"] = self._score_medical_relevance(task)
        review["dimension_scores"]["dialogue_structure"] = self._score_dialogue_structure(task)
        review["dimension_scores"]["consultation_quality"] = self._score_consultation_quality(task)
        review["dimension_scores"]["clinical_authenticity"] = self._score_clinical_authenticity(task)

        # 4. Calculate overall score
        dimension_scores = list(review["dimension_scores"].values())
        review["overall_score"] = round(sum(dimension_scores) / len(dimension_scores), 2)

        # 5. Generate comments and recommendations
        review["comments"] = self._generate_comments(task, review)
        review["recommendations"] = self._generate_recommendations(task, review)

        # 6. Determine pass status
        review["pass_status"] = (
            is_valid and
            review["overall_score"] >= 3.5 and
            all(score >= 3.0 for score in review["dimension_scores"].values())
        )

        return review

    def _score_medical_relevance(self, task: Dict[str, Any]) -> float:
        """
        Score medical relevance of the task.

        Args:
            task: Task dictionary

        Returns:
            Medical relevance score (0-5)
        """
        # Use validator's medical score calculation
        medical_score = self.validator.calculate_medical_score(task)

        # Convert to 0-5 scale
        return round(medical_score * 5, 2)

    def _score_dialogue_structure(self, task: Dict[str, Any]) -> float:
        """
        Score dialogue structure quality.

        Args:
            task: Task dictionary

        Returns:
            Dialogue structure score (0-5)
        """
        score = 3.0  # Base score

        user_scenario = task.get("user_scenario", {})
        instructions = user_scenario.get("instructions", {})
        task_instructions = instructions.get("task_instructions", "")

        if not task_instructions:
            return 1.0

        # Count dialogue turns
        turn_count = self.validator._count_dialogue_turns(task_instructions)

        # More turns = better structure (max 10 turns for full score)
        turn_score = min(2.0, turn_count * 0.2)

        # Check for dialogue markers
        has_markers = any(
            marker.lower() in task_instructions.lower()
            for marker in self.validator.DIALOGUE_MARKERS
        )
        if has_markers:
            score += 1.0

        # Check for proper turn alternation
        lines = task_instructions.split('\n')
        patient_turns = sum(
            1 for line in lines
            if any(m in line.lower() for m in ["patient:", "患者:"])
        )
        doctor_turns = sum(
            1 for line in lines
            if any(m in line.lower() for m in ["doctor:", "医生:", "physician:"])
        )

        if patient_turns >= 2 and doctor_turns >= 2:
            score += 1.0
        elif patient_turns >= 1 and doctor_turns >= 1:
            score += 0.5

        return min(5.0, score + turn_score)

    def _score_consultation_quality(self, task: Dict[str, Any]) -> float:
        """
        Score consultation question quality.

        Args:
            task: Task dictionary

        Returns:
            Consultation quality score (0-5)
        """
        score = 3.0  # Base score

        ticket = task.get("ticket", "")
        description = task.get("description", {})
        purpose = description.get("purpose", "") if isinstance(description, dict) else ""

        # Check for consultation patterns
        has_question_pattern = any(
            pattern in ticket.lower() or pattern in purpose.lower()
            for pattern in [
                "what", "how", "should", "can", "could",
                "怎么", "如何", "应该", "可以",
                "help", "advice", "concern", "worried",
                "帮助", "建议", "担心", "咨询", "请问"
            ]
        )

        if has_question_pattern:
            score += 1.0

        # Check for medical context
        has_medical_context = (
            self.validator._count_medical_keywords(ticket) >= 2 or
            self.validator._count_medical_keywords(purpose) >= 2
        )

        if has_medical_context:
            score += 1.0

        return min(5.0, score)

    def _score_clinical_authenticity(self, task: Dict[str, Any]) -> float:
        """
        Score clinical authenticity of the dialogue.

        Args:
            task: Task dictionary

        Returns:
            Clinical authenticity score (0-5)
        """
        score = 3.0  # Base score

        ticket = task.get("ticket", "")
        user_scenario = task.get("user_scenario", {})
        instructions = user_scenario.get("instructions", {})
        task_instructions = instructions.get("task_instructions", "")

        # Check for specific clinical details
        clinical_indicators = [
            "symptom", "diagnosis", "treatment", "medication", "prescription",
            "血压", "诊断", "治疗", "药物", "处方", "症状",
            "examination", "test", "lab", "x-ray", "mri",
            "检查", "化验", "心电图", "CT"
        ]

        has_clinical_details = any(
            indicator in ticket.lower() or indicator in task_instructions.lower()
            for indicator in clinical_indicators
        )

        if has_clinical_details:
            score += 1.0

        # Check for patient-doctor interaction flow
        has_interaction_flow = any(
            phrase in task_instructions.lower()
            for phrase in [
                "follow-up", "ask about", "need to know",
                "随访", "询问", "需要了解", "请描述"
            ]
        )

        if has_interaction_flow:
            score += 1.0

        return min(5.0, score)

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
            comments.append("Excellent medical dialogue quality")
        elif overall >= 3.5:
            comments.append("Good medical dialogue quality")
        elif overall >= 2.5:
            comments.append("Fair medical dialogue quality - needs improvement")
        else:
            comments.append("Poor medical dialogue quality - significant issues")

        # Validation status
        if not review.get("validation_passed", False):
            comments.append("Validation failed: " + "; ".join(review.get("validation_issues", [])))

        # Dimension-specific comments
        scores = review.get("dimension_scores", {})
        for dimension, score in scores.items():
            if score < 3.0:
                comments.append(f"Low score in {dimension}: {score}/5.0")
            elif score >= 4.5:
                comments.append(f"Excellent {dimension}: {score}/5.0")

        return comments

    def _generate_recommendations(
        self,
        task: Dict[str, Any],
        review: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []

        scores = review.get("dimension_scores", {})

        # Medical relevance recommendations
        if scores.get("medical_relevance", 5) < 3.0:
            recommendations.append(
                "Improve medical relevance: Add more medical terminology "
                "and ensure the task is clearly medical-related"
            )

        # Dialogue structure recommendations
        if scores.get("dialogue_structure", 5) < 3.0:
            recommendations.append(
                "Enhance dialogue structure: Ensure proper dialogue markers "
                "(Patient:, Doctor:, 患者:, 医生:) and multiple turns"
            )

        # Consultation quality recommendations
        if scores.get("consultation_quality", 5) < 3.0:
            recommendations.append(
                "Improve consultation quality: Format the ticket as a "
                "patient inquiry with clear questions"
            )

        # Clinical authenticity recommendations
        if scores.get("clinical_authenticity", 5) < 3.0:
            recommendations.append(
                "Enhance clinical authenticity: Add specific clinical details, "
                "examination findings, or treatment discussions"
            )

        return recommendations


class BatchMedicalDialogueReviewer:
    """
    Batch reviewer for medical dialogue tasks.
    批量医学对话审查器

    Reviews multiple tasks for medical dialogue quality.
    """

    def __init__(
        self,
        strict_mode: bool = False,
        min_medical_keywords: int = 2,
        min_dialogue_turns: int = 2
    ):
        """
        Initialize the batch reviewer.

        Args:
            strict_mode: Enable strict review criteria
            min_medical_keywords: Minimum medical keywords required
            min_dialogue_turns: Minimum dialogue turns required
        """
        self.reviewer = MedicalDialogueReviewer(
            strict_mode=strict_mode,
            min_medical_keywords=min_medical_keywords,
            min_dialogue_turns=min_dialogue_turns
        )

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
        medical_dialogues = sum(1 for r in reviews if r.get("is_medical_dialogue", False))

        overall_scores = [r.get("overall_score", 0) for r in reviews]
        avg_score = sum(overall_scores) / total_reviews if total_reviews > 0 else 0

        dimension_scores = {}
        for dimension in ["medical_relevance", "dialogue_structure",
                          "consultation_quality", "clinical_authenticity"]:
            scores = [
                r.get("dimension_scores", {}).get(dimension, 0)
                for r in reviews
            ]
            if scores:
                dimension_scores[dimension] = sum(scores) / len(scores)

        return {
            "total_reviews": total_reviews,
            "medical_dialogues": medical_dialogues,
            "non_medical_tasks": total_reviews - medical_dialogues,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total_reviews * 100) if total_reviews > 0 else 0,
            "average_score": round(avg_score, 2),
            "dimension_averages": dimension_scores,
        }


# Export
__all__ = [
    "MedicalDialogueReviewer",
    "BatchMedicalDialogueReviewer",
]
