"""
DataValidator - Medical Consultation Dialogue Dataset Validator

A comprehensive validation module for medical consultation dialogue datasets
in tau2-bench format. Supports bilingual (English/Chinese) medical terminology
recognition and multi-turn dialogue validation.

Example:
    >>> from DataValidator import MedicalDialogueValidator
    >>> validator = MedicalDialogueValidator()
    >>> result = validator.validate_dataset(Path("tasks.json"))
    >>> result.print_report()
"""

from .core import MedicalDialogueValidator
from .models import ValidationIssue, ValidationResult, ValidationLevel

__version__ = "1.0.0"
__all__ = [
    "MedicalDialogueValidator",
    "ValidationIssue",
    "ValidationResult",
    "ValidationLevel",
]
