#!/usr/bin/env python3
"""
Core Medical Dialogue Validator

Main validator class that orchestrates all validation checks.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

from .models import ValidationResult, ValidationIssue, ValidationLevel
from .keywords import MedicalKeywords
from .validators.structure_validator import StructureValidator
from .validators.medical_content_validator import MedicalContentValidator
from .validators.multi_turn_validator import MultiTurnValidator
from .utils.statistics import calculate_dataset_statistics


class MedicalDialogueValidator:
    """
    Main validator for medical consultation dialogue datasets.

    This validator checks:
    1. Structure validation (required fields)
    2. Medical content validation (keywords detection)
    3. Multi-turn dialogue validation (conversation structure)
    4. Evaluation criteria validation

    Example:
        >>> validator = MedicalDialogueValidator(strict_mode=False)
        >>> result = validator.validate_dataset(Path("tasks.json"))
        >>> result.print_report()
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the validator.

        Args:
            strict_mode: If True, treats warnings as errors
        """
        self.strict_mode = strict_mode
        self.stats = defaultdict(int)

        # Initialize sub-validators
        self.structure_validator = StructureValidator()
        self.content_validator = MedicalContentValidator()
        self.multi_turn_validator = MultiTurnValidator()

    def validate_dataset(self, data_path: Path) -> ValidationResult:
        """
        Validate a medical consultation dialogue dataset.

        Args:
            data_path: Path to the dataset JSON file

        Returns:
            ValidationResult with all issues and statistics
        """
        issues = []

        # Load dataset
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except FileNotFoundError:
            return ValidationResult(
                is_valid=False,
                total_tasks=0,
                issues=[ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="file",
                    message=f"File not found: {data_path}",
                    suggestion="Check the file path"
                )],
                stats={}
            )
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                total_tasks=0,
                issues=[ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="format",
                    message=f"Invalid JSON format: {e}",
                    suggestion="Validate JSON syntax"
                )],
                stats={}
            )

        # Check if it's a list
        if not isinstance(tasks, list):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="structure",
                message=f"Root element must be a list, got {type(tasks).__name__}",
                suggestion="Wrap tasks in a JSON array"
            ))
            return ValidationResult(is_valid=False, total_tasks=0, issues=issues)

        # Validate each task
        for idx, task in enumerate(tasks):
            task_issues = self.validate_task(task, idx)
            issues.extend(task_issues)

        # Calculate statistics
        stats = calculate_dataset_statistics(tasks, issues)

        # Determine overall validity
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        is_valid = len(errors) == 0

        if self.strict_mode:
            warnings = [i for i in issues if i.level == ValidationLevel.WARNING]
            is_valid = is_valid and len(warnings) == 0

        return ValidationResult(
            is_valid=is_valid,
            total_tasks=len(tasks),
            issues=issues,
            stats=stats
        )

    def validate_task(self, task: Dict[str, Any], idx: int) -> List[ValidationIssue]:
        """
        Validate a single task.

        Args:
            task: Task dictionary
            idx: Index in the dataset

        Returns:
            List of validation issues
        """
        issues = []
        task_id = task.get("id", f"task_{idx}")

        # 1. Structure validation
        structure_issues = self.structure_validator.validate_task(task, idx)
        issues.extend(structure_issues)

        # 2. Multi-turn validation (only if structure is valid enough)
        if not any(i.level == ValidationLevel.ERROR for i in structure_issues):
            multi_turn_issues = self.multi_turn_validator.validate_turn_count(task, idx)
            issues.extend(multi_turn_issues)

        # 3. Medical content validation
        content_issues = self.content_validator.validate_task(task, idx)
        issues.extend(content_issues)

        return issues

    def validate_tasks(self, tasks: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate a list of tasks directly.

        Args:
            tasks: List of task dictionaries

        Returns:
            ValidationResult with all issues and statistics
        """
        issues = []

        for idx, task in enumerate(tasks):
            task_issues = self.validate_task(task, idx)
            issues.extend(task_issues)

        stats = calculate_dataset_statistics(tasks, issues)

        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            total_tasks=len(tasks),
            issues=issues,
            stats=stats
        )

    @staticmethod
    def get_keyword_info() -> Dict[str, int]:
        """Get information about loaded keywords."""
        total_keywords = len(MedicalKeywords.get_all_keywords())

        return {
            "total_keywords": total_keywords,
            "categories": 30,  # Approximate number of categories
        }
