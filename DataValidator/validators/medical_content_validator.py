#!/usr/bin/env python3
"""
Medical Content Validator - Validates medical terminology and consultation patterns.
"""

import re
from typing import Dict, List, Any
from ..models import ValidationIssue, ValidationLevel
from ..keywords import MedicalKeywords


class MedicalContentValidator:
    """Validates medical content and terminology."""

    # Consultation patterns (English + Chinese)
    CONSULTATION_PATTERNS = [
        # English patterns
        r"(what|how|should|can|could|i|i'm|i have|my)",
        r"(help|advice|concern|worried)",
        r"(diagnosis|treatment|prescribe|recommend)",
        # Chinese patterns
        r"(怎么|如何|应该|可以|能否|我|我的)",
        r"(帮助|建议|担心|咨询|请问)",
        r"(诊断|治疗|开药|推荐)"
    ]

    # Safety-related keywords
    SAFETY_KEYWORDS = [
        "emergency", "urgent", "severe", "chest pain", "difficulty breathing",
        "癫痫", "抽搐", "昏迷", "呼吸困難", "休克", "中毒",
        "heart attack", "stroke", "bleeding"
    ]

    def __init__(self):
        """Initialize with medical keywords."""
        self.medical_keywords = set(MedicalKeywords.get_all_keywords())

    def validate_task(self, task: Dict[str, Any], task_idx: int) -> List[ValidationIssue]:
        """
        Validate medical content.

        Args:
            task: Task dictionary to validate
            task_idx: Index of the task in the dataset

        Returns:
            List of validation issues
        """
        issues = []
        task_id = task.get("id", f"task_{task_idx}")

        # Validate ticket content
        ticket = task.get("ticket", "")
        if ticket:
            self._validate_ticket_content(ticket, task_id, issues)

        # Validate description
        description = task.get("description", {})
        if isinstance(description, dict):
            self._validate_description(description, task_id, issues)

        return issues

    def _validate_ticket_content(self, ticket: str, task_id: str, issues: List[ValidationIssue]) -> None:
        """Validate that the ticket represents a medical consultation."""
        if not isinstance(ticket, str):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="content",
                message=f"'ticket' must be a string, got {type(ticket).__name__}",
                task_id=task_id,
                suggestion="Ensure ticket is a string"
            ))
            return

        # Check minimum length
        if len(ticket.strip()) < 10:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="content",
                message="Ticket content is too short (< 10 characters)",
                task_id=task_id,
                suggestion="Provide a more detailed patient inquiry"
            ))

        # Check for medical keywords
        has_medical_keywords = self._check_medical_keywords(ticket)

        if not has_medical_keywords:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="medical",
                message="Ticket may not be medical-related (no medical keywords found)",
                task_id=task_id,
                suggestion="Ensure content describes a health-related concern"
            ))

        # Check for consultation patterns
        has_consultation_pattern = any(
            re.search(pattern, ticket, re.IGNORECASE)
            for pattern in self.CONSULTATION_PATTERNS
        )

        if not has_consultation_pattern:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="content",
                message="Ticket lacks typical consultation question patterns",
                task_id=task_id,
                suggestion="Consider framing as a patient inquiry"
            ))

        # Check for safety concerns
        has_safety_concern = any(
            keyword.lower() in ticket.lower()
            for keyword in self.SAFETY_KEYWORDS
        )

        if has_safety_concern:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="safety",
                message="Ticket may indicate urgent or emergency condition",
                task_id=task_id,
                suggestion="Ensure appropriate urgency assessment is included"
            ))

    def _validate_description(self, description: Dict[str, Any], task_id: str, issues: List[ValidationIssue]) -> None:
        """Validate description quality."""
        purpose = description.get("purpose", "")

        # Check for medical terms in purpose
        if purpose:
            medical_terms_in_purpose = sum(
                1 for keyword in self.medical_keywords
                if keyword.lower() in purpose.lower()
            )

            if medical_terms_in_purpose < 2:
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    category="medical",
                    message="Description purpose may lack specific medical context",
                    task_id=task_id,
                    suggestion="Include relevant medical terms in the description"
                ))

    def _check_medical_keywords(self, text: str) -> bool:
        """Check if text contains medical keywords."""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.medical_keywords)

    def is_safety_related(self, ticket: str) -> bool:
        """Check if ticket mentions safety concerns."""
        return any(
            keyword.lower() in ticket.lower()
            for keyword in self.SAFETY_KEYWORDS
        )
