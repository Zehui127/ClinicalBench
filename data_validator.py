#!/usr/bin/env python3
"""
Medical Consultation Dialogue Dataset Validator

This module validates whether a dataset conforms to medical consultation
multi-turn dialogue standards for tau2-bench format.

Author: Claude Sonnet 4.5
Date: 2025-03-14
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re


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
        return [i for i in self.issues if i.level == ValidationLevel.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]

    @property
    def infos(self) -> List[ValidationIssue]:
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


class MedicalDialogueValidator:
    """Validates medical consultation dialogue datasets."""

    # Medical domain keywords (English + Chinese)
    MEDICAL_KEYWORDS = [
        # English keywords
        "pain", "fever", "headache", "nausea", "vomiting", "cough",
        "doctor", "physician", "patient", "symptom", "diagnosis",
        "treatment", "medication", "prescription", "therapy",
        "blood pressure", "heart rate", "temperature", "examination",
        "medical", "clinical", "health", "disease", "condition",
        # Chinese keywords - 症状
        "疼痛", "发烧", "头痛", "恶心", "呕吐", "咳嗽",
        "头晕", "乏力", "失眠", "腹泻", "便秘", "胸闷",
        "气短", "心悸", "水肿", "麻木", "瘙痒",
        # 中文关键词 - 医学名词
        "医生", "患者", "症状", "诊断", "治疗",
        "药物", "药品", "处方", "疗法", "手术",
        "血压", "心率", "体温", "检查", "化验",
        "医学", "临床", "健康", "疾病", "病情", "病症",
        # 中文关键词 - 科室
        "内科", "外科", "妇科", "儿科", "肿瘤科",
        "神经科", "心脏科", "消化科", "内分泌", "肾病",
        "男科", "妇产科", "骨科", "眼科", "耳鼻喉",
        # 中文关键词 - 其他
        "高血压", "糖尿病", "感冒", "炎症", "过敏",
        "肿瘤", "癌症", "感染", "病毒", "细菌",
        "住院", "门诊", "复查", "预约", "挂号"
    ]

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

    # Multi-turn indicators (English + Chinese)
    MULTI_TURN_INDICATORS = [
        # English indicators
        "follow-up", "follow up", "additional", "more information",
        "clarification", "also", "another question", "further",
        # Chinese indicators
        "随访", "复查", "补充", "更多信息",
        "澄清", "还有", "另外", "进一步", "另外想问"
    ]

    # Dialogue markers (English + Chinese)
    DIALOGUE_MARKERS = [
        # English markers
        "patient:", "doctor:", "physician:", "assistant:", "user:", "clinician:",
        # Chinese markers
        "患者:", "医生:", "医师:", "助理:", "用户:", "临床医生:"
    ]

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the validator.

        Args:
            strict_mode: If True, treats warnings as errors
        """
        self.strict_mode = strict_mode
        self.stats = defaultdict(int)

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
        stats = self._calculate_statistics(tasks, issues)

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
        """Validate a single task."""
        issues = []
        task_id = task.get("id", f"task_{idx}")

        # 1. Check required fields
        required_fields = ["id", "description", "user_scenario", "ticket", "evaluation_criteria"]
        for field in required_fields:
            if field not in task:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="structure",
                    message=f"Missing required field: '{field}'",
                    task_id=task_id,
                    suggestion=f"Add '{field}' field to the task"
                ))

        # 2. Validate ticket content
        ticket = task.get("ticket", "")
        if ticket:
            self._validate_ticket_content(ticket, task_id, issues)

        # 3. Check for multi-turn structure
        self._validate_multi_turn_structure(task, task_id, issues)

        # 4. Validate medical content
        self._validate_medical_content(task, task_id, issues)

        # 5. Validate evaluation criteria
        self._validate_evaluation_criteria(task, task_id, issues)

        # 6. Check user_scenario
        user_scenario = task.get("user_scenario", {})
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
        has_medical_keywords = any(
            keyword.lower() in ticket.lower()
            for keyword in self.MEDICAL_KEYWORDS
        )

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

    def _validate_multi_turn_structure(self, task: Dict[str, Any], task_id: str, issues: List[ValidationIssue]) -> None:
        """Validate multi-turn dialogue structure."""
        user_scenario = task.get("user_scenario", {})
        if not isinstance(user_scenario, dict):
            return

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
            return

        # Check for dialogue pattern
        has_dialogue_structure = any(
            indicator.lower() in task_instructions.lower()
            for indicator in self.DIALOGUE_MARKERS
        )

        if has_dialogue_structure:
            # Count turns
            lines = task_instructions.split('\n')
            dialogue_lines = [
                line for line in lines
                if any(indicator in line.lower() for indicator in self.DIALOGUE_MARKERS)
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
            else:
                self.stats["multi_turn_tasks"] += 1
        else:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="multi_turn",
                message="task_instructions doesn't contain clear dialogue structure",
                task_id=task_id,
                suggestion="Use 'Patient:', 'Doctor:', or similar markers (including Chinese: '患者:', '医生:') to structure dialogue"
            ))

    def _validate_medical_content(self, task: Dict[str, Any], task_id: str, issues: List[ValidationIssue]) -> None:
        """Validate medical content quality."""
        ticket = task.get("ticket", "")
        description = task.get("description", {})

        # Check description purpose
        purpose = description.get("purpose", "") if isinstance(description, dict) else ""
        medical_terms_in_purpose = sum(
            1 for keyword in self.MEDICAL_KEYWORDS
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

        # Check for safety-related content
        safety_keywords = ["emergency", "urgent", "severe", "chest pain", "difficulty breathing"]
        has_safety_concern = any(
            keyword in ticket.lower()
            for keyword in safety_keywords
        )

        if has_safety_concern:
            self.stats["safety_related_tasks"] += 1

    def _validate_evaluation_criteria(self, task: Dict[str, Any], task_id: str, issues: List[ValidationIssue]) -> None:
        """Validate evaluation criteria."""
        eval_criteria = task.get("evaluation_criteria")

        if not eval_criteria:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="evaluation",
                message="Missing evaluation_criteria",
                task_id=task_id,
                suggestion="Add evaluation criteria to assess model performance"
            ))
            return

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

        if has_actions and isinstance(has_actions, list):
            self.stats["total_evaluation_actions"] += len(has_actions)

    def _calculate_statistics(self, tasks: List[Dict], issues: List[ValidationIssue]) -> Dict[str, Any]:
        """Calculate dataset statistics."""
        stats = dict(self.stats)

        # Count tasks by category
        stats["tasks_with_errors"] = len(set(i.task_id for i in issues if i.level == ValidationLevel.ERROR))
        stats["tasks_with_warnings"] = len(set(i.task_id for i in issues if i.level == ValidationLevel.WARNING))

        # Average ticket length
        ticket_lengths = [
            len(task.get("ticket", ""))
            for task in tasks
            if task.get("ticket")
        ]
        if ticket_lengths:
            stats["avg_ticket_length"] = sum(ticket_lengths) / len(ticket_lengths)
            stats["min_ticket_length"] = min(ticket_lengths)
            stats["max_ticket_length"] = max(ticket_lengths)

        # Medical domain distribution
        domains = {}
        for task in tasks:
            domain = task.get("user_scenario", {}).get("instructions", {}).get("domain", "unknown")
            domains[domain] = domains.get(domain, 0) + 1
        stats["domain_distribution"] = domains

        return stats


def main():
    """Command-line interface for the validator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate medical consultation dialogue datasets"
    )
    parser.add_argument(
        "dataset_path",
        type=str,
        help="Path to the dataset JSON file"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode (warnings become errors)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show errors and warnings, not info"
    )
    parser.add_argument(
        "--json-output",
        type=str,
        help="Save validation result to JSON file"
    )

    args = parser.parse_args()

    # Initialize validator
    validator = MedicalDialogueValidator(strict_mode=args.strict)

    # Validate dataset
    data_path = Path(args.dataset_path)
    result = validator.validate_dataset(data_path)

    # Print report
    result.print_report(verbose=not args.quiet)

    # Save JSON output if requested
    if args.json_output:
        output = {
            "is_valid": result.is_valid,
            "total_tasks": result.total_tasks,
            "errors": [
                {
                    "category": e.category,
                    "message": e.message,
                    "task_id": e.task_id,
                    "suggestion": e.suggestion
                }
                for e in result.errors
            ],
            "warnings": [
                {
                    "category": w.category,
                    "message": w.message,
                    "task_id": w.task_id,
                    "suggestion": w.suggestion
                }
                for w in result.warnings
            ],
            "stats": result.stats
        }
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Validation result saved to: {args.json_output}")

    # Exit code
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
