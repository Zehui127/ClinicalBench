#!/usr/bin/env python3
"""
Data Models for Medical Dialogue Validation

Defines the core data structures used throughout the validation process.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "ERROR"      # Critical issues that prevent dataset usage
    WARNING = "WARNING"  # Issues that should be addressed but don't block usage
    INFO = "INFO"        # Informational messages


@dataclass
class ValidationIssue:
    """Represents a validation issue found in the dataset."""
    level: ValidationLevel
    category: str  # e.g., "structure", "content", "medical", "multi_turn"
    message: str
    task_id: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """Format the issue for display."""
        prefix = f"[{self.level.value}]"
        task_info = f" (Task: {self.task_id})" if self.task_id else ""
        suggestion = f"\n  Suggestion: {self.suggestion}" if self.suggestion else ""
        return f"{prefix} {self.category}: {self.message}{task_info}{suggestion}"


@dataclass
class ValidationResult:
    """Results of dataset validation."""
    is_valid: bool
    total_tasks: int
    issues: List[ValidationIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get all ERROR level issues."""
        return [i for i in self.issues if i.level == ValidationLevel.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get all WARNING level issues."""
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]

    @property
    def infos(self) -> List[ValidationIssue]:
        """Get all INFO level issues."""
        return [i for i in self.issues if i.level == ValidationLevel.INFO]

    def print_report(self, verbose: bool = True) -> None:
        """Print a formatted validation report."""
        print("\n" + "=" * 80)
        print("  MEDICAL CONSULTATION DIALOGUE DATASET VALIDATION REPORT")
        print("=" * 80)

        # Overall status
        status = "[VALID]" if self.is_valid else "[INVALID]"
        print(f"\nOverall Status: {status}")
        print(f"Total Tasks: {self.total_tasks}")
        print(f"Issues Found: {len(self.issues)}")
        print(f"  - Errors: {len(self.errors)}")
        print(f"  - Warnings: {len(self.warnings)}")
        print(f"  - Info: {len(self.infos)}")

        # Statistics
        if self.stats:
            print("\n" + "-" * 80)
            print("  DATASET STATISTICS")
            print("-" * 80)
            for key, value in self.stats.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                else:
                    print(f"  {key}: {value}")

        # Issues by level
        if self.issues and verbose:
            for level in [ValidationLevel.ERROR, ValidationLevel.WARNING, ValidationLevel.INFO]:
                level_issues = [i for i in self.issues if i.level == level]
                if level_issues:
                    print(f"\n{level.value}s ({len(level_issues)}):")
                    for issue in level_issues[:20]:  # Limit to 20 per level
                        print(f"  {issue}")
                    if len(level_issues) > 20:
                        print(f"  ... and {len(level_issues) - 20} more {level.value.lower()}s")

        print("\n" + "=" * 80 + "\n")

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "total_tasks": self.total_tasks,
            "errors": [
                {
                    "category": e.category,
                    "message": e.message,
                    "task_id": e.task_id,
                    "suggestion": e.suggestion
                }
                for e in self.errors
            ],
            "warnings": [
                {
                    "category": w.category,
                    "message": w.message,
                    "task_id": w.task_id,
                    "suggestion": w.suggestion
                }
                for w in self.warnings
            ],
            "infos": [
                {
                    "category": i.category,
                    "message": i.message,
                    "task_id": i.task_id,
                    "suggestion": i.suggestion
                }
                for i in self.infos
            ],
            "stats": self.stats
        }
