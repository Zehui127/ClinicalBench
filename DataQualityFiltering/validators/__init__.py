#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validators for Clinical Tasks
临床任务验证器

Schema and quality validation for clinical tasks.
"""

from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod


class BaseValidator(ABC):
    """Abstract base class for validators."""

    @abstractmethod
    def validate(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a clinical task.

        Args:
            task: Task dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass


class SchemaValidator(BaseValidator):
    """
    Schema validator for clinical tasks.
    架构验证器

    Validates clinical tasks against schema requirements.
    """

    # Required field definitions
    REQUIRED_FIELDS = ["id", "description"]
    OPTIONAL_FIELDS = [
        "department", "difficulty", "clinical_scenario",
        "tool_call_requirements", "expected_outcome", "metadata"
    ]

    # Clinical scenario required fields
    SCENARIO_REQUIRED_FIELDS = ["patient_info"]
    SCENARIO_OPTIONAL_FIELDS = [
        "diagnosis", "vital_signs", "lab_results",
        "medications", "comorbidities", "history"
    ]

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the schema validator.

        Args:
            strict_mode: Enable strict validation
        """
        self.strict_mode = strict_mode

    def validate(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate task schema.

        Args:
            task: Task dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in task or not task[field]:
                errors.append(f"Missing required field: {field}")

        # Validate clinical scenario if present
        if "clinical_scenario" in task:
            scenario_errors = self._validate_scenario(task["clinical_scenario"])
            errors.extend(scenario_errors)

        # Validate tool_call_requirements if present
        if "tool_call_requirements" in task:
            tool_errors = self._validate_tool_requirements(task["tool_call_requirements"])
            errors.extend(tool_errors)

        # Validate data types
        type_errors = self._validate_types(task)
        errors.extend(type_errors)

        return len(errors) == 0, errors

    def _validate_scenario(self, scenario: Dict[str, Any]) -> List[str]:
        """Validate clinical scenario structure."""
        errors = []

        if not isinstance(scenario, dict):
            errors.append("clinical_scenario must be a dictionary")
            return errors

        # Check required scenario fields
        for field in self.SCENARIO_REQUIRED_FIELDS:
            if field not in scenario:
                errors.append(f"Missing scenario field: {field}")

        # Validate patient_info
        if "patient_info" in scenario:
            patient_info = scenario["patient_info"]
            if not isinstance(patient_info, dict):
                errors.append("patient_info must be a dictionary")
            else:
                # Check for at least age or gender
                if not patient_info.get("age") and not patient_info.get("gender"):
                    errors.append("patient_info must contain age or gender")

        return errors

    def _validate_tool_requirements(self, tool_reqs: Any) -> List[str]:
        """Validate tool_call_requirements structure."""
        errors = []

        if not isinstance(tool_reqs, dict):
            errors.append("tool_call_requirements must be a dictionary")
            return errors

        # Check required_tools
        if "required_tools" in tool_reqs:
            tools = tool_reqs["required_tools"]
            if not isinstance(tools, list):
                errors.append("required_tools must be a list")

        # Check optional_tools
        if "optional_tools" in tool_reqs:
            tools = tool_reqs["optional_tools"]
            if not isinstance(tools, list):
                errors.append("optional_tools must be a list")

        return errors

    def _validate_types(self, task: Dict[str, Any]) -> List[str]:
        """Validate data types for fields."""
        errors = []

        # description must be string
        if "description" in task and task["description"]:
            if not isinstance(task["description"], str):
                errors.append("description must be a string")

        # difficulty must be one of the allowed values
        if "difficulty" in task:
            valid_difficulties = ["easy", "moderate", "hard"]
            if task["difficulty"] not in valid_difficulties:
                errors.append(
                    f"difficulty must be one of {valid_difficulties}, "
                    f"got '{task['difficulty']}'"
                )

        return errors


class QualityValidator(BaseValidator):
    """
    Quality validator for clinical tasks.
    质量验证器

    Validates clinical tasks against quality criteria.
    """

    def __init__(
        self,
        min_quality_score: float = 3.5,
        min_tool_count: int = 1,
        max_tool_count: int = 8,
        min_content_length: int = 50
    ):
        """
        Initialize the quality validator.

        Args:
            min_quality_score: Minimum quality score
            min_tool_count: Minimum number of tools
            max_tool_count: Maximum number of tools
            min_content_length: Minimum content length
        """
        self.min_quality_score = min_quality_score
        self.min_tool_count = min_tool_count
        self.max_tool_count = max_tool_count
        self.min_content_length = min_content_length

    def validate(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate task quality.

        Args:
            task: Task dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Calculate quality score
        quality_score = self._calculate_quality_score(task)

        if quality_score < self.min_quality_score:
            errors.append(
                f"Quality score {quality_score:.2f} below minimum "
                f"{self.min_quality_score}"
            )

        # Validate tool count
        tool_count = self._get_tool_count(task)
        if tool_count < self.min_tool_count:
            errors.append(
                f"Tool count {tool_count} below minimum {self.min_tool_count}"
            )

        if tool_count > self.max_tool_count:
            errors.append(
                f"Tool count {tool_count} above maximum {self.max_tool_count}"
            )

        # Validate content length
        content_length = self._get_content_length(task)
        if content_length < self.min_content_length:
            errors.append(
                f"Content length {content_length} below minimum "
                f"{self.min_content_length}"
            )

        return len(errors) == 0, errors

    def _calculate_quality_score(self, task: Dict[str, Any]) -> float:
        """Calculate quality score for the task."""
        score = 0.0

        # Tool count contribution (0-60%)
        tool_count = self._get_tool_count(task)
        tool_score = min(3.0, tool_count * 0.6)

        # Content length contribution (0-40%)
        content_length = self._get_content_length(task)
        content_score = min(2.0, content_length * self._content_length_weight())

        score = tool_score + content_score

        return min(5.0, score)

    def _get_tool_count(self, task: Dict[str, Any]) -> int:
        """Get number of required tools."""
        return len(
            task.get("tool_call_requirements", {})
            .get("required_tools", [])
        )

    def _get_content_length(self, task: Dict[str, Any]) -> int:
        """Get content length."""
        content = (
            str(task.get("clinical_scenario", "")) +
            str(task.get("description", ""))
        )
        return len(content)

    def _content_length_weight(self) -> float:
        """Calculate weight for content length."""
        return 0.02


class DepartmentValidator(BaseValidator):
    """
    Department validator for clinical tasks.
    科室验证器

    Validates task department classification.
    """

    VALID_DEPARTMENTS = [
        "cardiology",
        "nephrology",
        "gastroenterology",
        "neurology",
        "oncology",
        "pediatrics",
        "general_practice",
        "internal_medicine",
    ]

    # Department keyword mappings
    DEPARTMENT_KEYWORDS = {
        "cardiology": {
            "english": ["cardio", "heart", "hypertension", "chest_pain",
                       "mi", "myocardial", "coronary", "arrhythmia"],
            "chinese": ["心脏", "心梗", "心电图", "血压"],
        },
        "nephrology": {
            "english": ["nephro", "renal", "kidney", "ckd", "egfr",
                       "dialysis", "albuminuria"],
            "chinese": ["肾", "肾病", "肾功能"],
        },
        "gastroenterology": {
            "english": ["gastro", "stomach", "ulcer", "digestive",
                       "liver", "endoscopy"],
            "chinese": ["胃", "消化", "溃疡"],
        },
        "neurology": {
            "english": ["neuro", "brain", "stroke", "seizure", "headache"],
            "chinese": ["神经", "脑", "中风"],
        },
        "oncology": {
            "english": ["onco", "cancer", "tumor", "chemotherapy"],
            "chinese": ["肿瘤", "癌症"],
        },
        "pediatrics": {
            "english": ["ped", "child", "infant", "newborn"],
            "chinese": ["儿科", "儿童"],
        },
    }

    def __init__(self, allow_auto_detect: bool = True):
        """
        Initialize the department validator.

        Args:
            allow_auto_detect: Allow automatic department detection
        """
        self.allow_auto_detect = allow_auto_detect

    def validate(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate task department.

        Args:
            task: Task dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Get department
        department = task.get("department", "")

        if not department:
            if self.allow_auto_detect:
                # Auto-detect department
                department = self.detect_department(task)
                if department != "general_practice":
                    # Successfully detected department
                    return True, []
                else:
                    errors.append("Could not detect department")
            else:
                errors.append("Missing department field")
        elif department not in self.VALID_DEPARTMENTS:
            errors.append(
                f"Invalid department '{department}'. "
                f"Valid: {', '.join(self.VALID_DEPARTMENTS)}"
            )

        return len(errors) == 0, errors

    def detect_department(self, task: Dict[str, Any]) -> str:
        """
        Auto-detect department from task content.

        Args:
            task: Task dictionary

        Returns:
            Detected department name
        """
        # Combine all text fields
        text = (
            str(task.get("id", "")) +
            str(task.get("task_id", "")) +
            str(task.get("description", "")) +
            str(task.get("diagnosis", "")) +
            str(task.get("clinical_scenario", {}).get("diagnosis", ""))
        ).lower()

        # Check each department's keywords
        for dept, keywords in self.DEPARTMENT_KEYWORDS.items():
            for keyword_list in [keywords["english"], keywords["chinese"]]:
                for keyword in keyword_list:
                    if keyword.lower() in text:
                        return dept

        return "general_practice"


class ValidatorPipeline:
    """
    Pipeline for running multiple validators.
    验证器管道

    Runs multiple validators in sequence.
    """

    def __init__(self, validators: Optional[List[BaseValidator]] = None):
        """
        Initialize the validator pipeline.

        Args:
            validators: List of validators to run
        """
        self.validators = validators or [
            SchemaValidator(),
            QualityValidator(),
            DepartmentValidator(),
        ]

    def validate(self, task: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Run all validators on a task.

        Args:
            task: Task dictionary

        Returns:
            Tuple of (is_valid, validation_report)
        """
        all_errors = {}
        all_valid = True

        for validator in self.validators:
            is_valid, errors = validator.validate(task)

            validator_name = validator.__class__.__name__

            all_errors[validator_name] = {
                "valid": is_valid,
                "errors": errors
            }

            if not is_valid:
                all_valid = False

        return all_valid, {
            "overall_valid": all_valid,
            "validator_results": all_errors,
        }

    def validate_batch(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate multiple tasks.

        Args:
            tasks: List of task dictionaries

        Returns:
            List of validation reports
        """
        reports = []

        for task in tasks:
            is_valid, report = self.validate(task)
            reports.append(report)

        return reports


# Import medical dialogue validator
from .medical_dialogue_validator import (
    MedicalDialogueValidator,
    MedicalDialoguePipeline,
)


# Export all validators
__all__ = [
    "BaseValidator",
    "SchemaValidator",
    "QualityValidator",
    "DepartmentValidator",
    "ValidatorPipeline",
    "MedicalDialogueValidator",
    "MedicalDialoguePipeline",
]
