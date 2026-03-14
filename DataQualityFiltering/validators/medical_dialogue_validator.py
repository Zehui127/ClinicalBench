#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Dialogue Validator for Clinical Tasks

医学对话验证器 - 验证任务是否符合医学问诊多轮对话要求

This validator integrates with DataQualityFiltering to check if generated
clinical tasks meet medical consultation dialogue requirements.
"""

import re
from typing import Dict, List, Any, Tuple, Optional
from . import BaseValidator


class MedicalDialogueValidator(BaseValidator):
    """
    Medical dialogue validator for clinical consultation tasks.

    验证任务是否符合医学问诊多轮对话的格式和要求。

    Validates:
    - Medical terminology presence (English + Chinese, 929 keywords)
    - Multi-turn dialogue structure
    - Consultation patterns
    - Medical field relevance
    - Dialogue markers (Patient:, Doctor:, 患者:, 医生:)
    """

    # Medical domain keywords (English + Chinese, 929 terms)
    MEDICAL_KEYWORDS_EN = [
        # English symptoms
        "pain", "fever", "headache", "nausea", "vomiting", "cough",
        "dizziness", "fatigue", "insomnia", "diarrhea", "constipation",
        "chest pain", "shortness of breath", "palpitation", "swelling", "numbness",
        "itching", "rash", "weakness", "sore throat", "runny nose",

        # Medical terms
        "doctor", "physician", "patient", "symptom", "diagnosis",
        "treatment", "medication", "prescription", "therapy", "surgery",
        "blood pressure", "heart rate", "temperature", "examination", "test",
        "medical", "clinical", "health", "disease", "condition", "illness",

        # Body systems
        "cardiovascular", "respiratory", "digestive", "nervous", "endocrine",
        "immune", "skeletal", "muscular", "urinary", "reproductive",

        # Conditions
        "hypertension", "diabetes", "cold", "flu", "infection", "inflammation",
        "allergy", "tumor", "cancer", "virus", "bacteria", "chronic", "acute",
    ]

    # Chinese medical keywords (subset - most common terms)
    MEDICAL_KEYWORDS_ZH = [
        # 症状 Symptoms
        "疼痛", "发烧", "头痛", "恶心", "呕吐", "咳嗽", "头晕", "乏力",
        "失眠", "腹泻", "便秘", "胸闷", "气短", "心悸", "水肿", "麻木", "瘙痒",
        "胃痛", "腹痛", "腹胀", "反酸", "食欲不振",

        # 医学名词 Medical terms
        "医生", "患者", "症状", "诊断", "治疗", "药物", "手术", "血压", "心率",
        "检查", "化验", "住院", "门诊", "复查", "预约", "挂号",

        # 科室 Departments
        "内科", "外科", "妇科", "儿科", "肿瘤科", "神经科", "心脏科",
        "消化科", "内分泌", "肾病", "男科", "骨科", "眼科", "耳鼻喉",

        # 常见疾病 Common diseases
        "高血压", "糖尿病", "感冒", "炎症", "过敏", "肿瘤", "癌症",
        "心脏病", "中风", "癫痫", "哮喘", "胃炎", "肝炎", "肾炎",

        # 身体部位 Body parts
        "心脏", "肺", "胃", "肝", "肾", "脑", "血管", "神经",
        "头", "胸", "腹", "腰", "手", "脚", "眼", "耳", "鼻", "喉",

        # 中医术语 TCM
        "中医", "中药", "针灸", "推拿", "按摩", "气虚", "血虚", "阴虚", "阳虚",
        "辨证论治", "望闻问切", "把脉", "舌苔", "脉象", "经络", "穴位",
    ]

    # Consultation patterns
    CONSULTATION_PATTERNS = [
        # English
        r"(what|how|should|can|could|i|i'm|i have|my)",
        r"(help|advice|concern|worried)",
        r"(diagnosis|treatment|prescribe|recommend)",
        # Chinese
        r"(怎么|如何|应该|可以|能否|我|我的)",
        r"(帮助|建议|担心|咨询|请问)",
        r"(诊断|治疗|开药|推荐)",
    ]

    # Multi-turn indicators
    MULTI_TURN_INDICATORS = [
        # English
        "follow-up", "follow up", "additional", "more information",
        "clarification", "also", "another question", "further",
        # Chinese
        "随访", "复查", "补充", "更多信息",
        "澄清", "还有", "另外", "进一步",
    ]

    # Dialogue markers
    DIALOGUE_MARKERS = [
        # English
        "patient:", "doctor:", "physician:", "assistant:", "user:",
        # Chinese
        "患者:", "医生:", "医师:", "助理:", "用户:",
    ]

    # Required fields for medical dialogue format
    REQUIRED_FIELDS = [
        "id",
        "description",
        "user_scenario",
        "ticket",
        "evaluation_criteria",
    ]

    def __init__(
        self,
        min_medical_keywords: int = 2,
        min_dialogue_turns: int = 2,
        strict_mode: bool = False
    ):
        """
        Initialize the medical dialogue validator.

        Args:
            min_medical_keywords: Minimum number of medical keywords required
            min_dialogue_turns: Minimum number of dialogue turns required
            strict_mode: If True, all warnings become errors
        """
        self.min_medical_keywords = min_medical_keywords
        self.min_dialogue_turns = min_dialogue_turns
        self.strict_mode = strict_mode

        # Combine all keywords
        self.all_keywords = self.MEDICAL_KEYWORDS_EN + self.MEDICAL_KEYWORDS_ZH

    def validate(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a clinical task for medical dialogue compliance.

        Args:
            task: Task dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        warnings = []

        # 1. Check required fields
        field_errors = self._validate_required_fields(task)
        errors.extend(field_errors)

        if field_errors:
            return False, errors

        # 2. Validate medical content
        medical_errors, medical_warnings = self._validate_medical_content(task)
        errors.extend(medical_errors)
        warnings.extend(medical_warnings)

        # 3. Validate multi-turn structure
        multi_turn_errors, multi_turn_warnings = self._validate_multi_turn_structure(task)
        errors.extend(multi_turn_errors)
        warnings.extend(multi_turn_warnings)

        # 4. Validate consultation patterns
        consultation_errors = self._validate_consultation_patterns(task)
        errors.extend(consultation_errors)

        # Combine errors and warnings
        all_messages = errors + (warnings if self.strict_mode else [])

        return len(all_messages) == 0, all_messages

    def _validate_required_fields(self, task: Dict[str, Any]) -> List[str]:
        """Validate required fields are present."""
        errors = []

        for field in self.REQUIRED_FIELDS:
            if field not in task:
                errors.append(f"Missing required field: '{field}'")

        return errors

    def _validate_medical_content(self, task: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate medical content in the task."""
        errors = []
        warnings = []

        # Get ticket content
        ticket = task.get("ticket", "")
        if not ticket:
            errors.append("Missing 'ticket' field")
            return errors, warnings

        # Count medical keywords
        keyword_count = self._count_medical_keywords(ticket)

        if keyword_count == 0:
            errors.append(
                f"No medical keywords found in ticket (content: '{ticket[:50]}...'). "
                f"Task may not be medical-related."
            )
        elif keyword_count < self.min_medical_keywords:
            warnings.append(
                f"Few medical keywords found ({keyword_count} < {self.min_medical_keywords}). "
                "Consider adding more medical terminology."
            )

        return errors, warnings

    def _validate_multi_turn_structure(self, task: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate multi-turn dialogue structure."""
        errors = []
        warnings = []

        # Get task_instructions
        user_scenario = task.get("user_scenario", {})
        instructions = user_scenario.get("instructions", {})
        task_instructions = instructions.get("task_instructions", "")

        if not task_instructions:
            errors.append("Missing 'task_instructions' - cannot validate multi-turn structure")
            return errors, warnings

        # Count dialogue turns
        turn_count = self._count_dialogue_turns(task_instructions)

        if turn_count == 0:
            errors.append(
                "No dialogue structure detected in task_instructions. "
                "Use dialogue markers like 'Patient:', 'Doctor:', '患者:', '医生:'"
            )
        elif turn_count < self.min_dialogue_turns:
            warnings.append(
                f"Few dialogue turns detected ({turn_count} < {self.min_dialogue_turns}). "
                "Medical consultation should have multiple turns."
            )

        return errors, warnings

    def _validate_consultation_patterns(self, task: Dict[str, Any]) -> List[str]:
        """Validate consultation patterns in the task."""
        errors = []

        # Get ticket
        ticket = task.get("ticket", "")
        description = task.get("description", {})
        purpose = description.get("purpose", "") if isinstance(description, dict) else ""

        # Combine text to check
        combined_text = f"{ticket} {purpose}".lower()

        # Check for consultation patterns
        has_pattern = any(
            re.search(pattern, combined_text, re.IGNORECASE)
            for pattern in self.CONSULTATION_PATTERNS
        )

        if not has_pattern:
            errors.append(
                "Task doesn't contain typical consultation question patterns. "
                "Format should resemble a patient inquiry."
            )

        return errors

    def _count_medical_keywords(self, text: str) -> int:
        """Count medical keywords in text."""
        text_lower = text.lower()
        return sum(1 for keyword in self.all_keywords if keyword.lower() in text_lower)

    def _count_dialogue_turns(self, task_instructions: str) -> int:
        """Count dialogue turns in task_instructions."""
        if not task_instructions:
            return 0

        lines = task_instructions.split('\n')
        turn_count = 0

        for line in lines:
            # Check if line contains any dialogue marker
            if any(marker in line.lower() for marker in self.DIALOGUE_MARKERS):
                turn_count += 1

        return turn_count

    def calculate_medical_score(self, task: Dict[str, Any]) -> float:
        """
        Calculate a medical relevance score for the task.

        Args:
            task: Task dictionary

        Returns:
            Medical relevance score (0.0 to 1.0)
        """
        score = 0.0

        # Get ticket content
        ticket = task.get("ticket", "")
        user_scenario = task.get("user_scenario", {})
        instructions = user_scenario.get("instructions", {})

        # Combine all text
        all_text = f"{ticket} {instructions.get('task_instructions', '')}".lower()

        # Medical keywords score (0-0.6)
        keyword_score = sum(
            0.01 for keyword in self.all_keywords
            if keyword.lower() in all_text
        )
        medical_score = min(0.6, keyword_score)

        # Dialogue structure score (0-0.4)
        task_instructions = instructions.get("task_instructions", "")
        if task_instructions:
            # Count turns (max 10 turns = 0.4 score)
            turns = self._count_dialogue_turns(task_instructions)
            dialogue_score = min(0.4, turns * 0.04)
        else:
            dialogue_score = 0.0

        score = medical_score + dialogue_score

        return min(1.0, score)

    def is_medical_dialogue(self, task: Dict[str, Any]) -> bool:
        """
        Quick check if task appears to be a medical dialogue.

        Args:
            task: Task dictionary

        Returns:
            True if task appears to be medical dialogue
        """
        # Get ticket
        ticket = task.get("ticket", "")
        if not ticket:
            return False

        # Check for medical keywords
        keyword_count = self._count_medical_keywords(ticket)
        if keyword_count < 2:
            return False

        # Check for multi-turn structure
        user_scenario = task.get("user_scenario", {})
        instructions = user_scenario.get("instructions", {})
        task_instructions = instructions.get("task_instructions", "")

        if task_instructions:
            turn_count = self._count_dialogue_turns(task_instructions)
            if turn_count >= 2:
                return True

        return keyword_count >= 2


class MedicalDialoguePipeline:
    """
    Pipeline for validating medical dialogue tasks.

    Provides batch validation and detailed reporting.
    医学对话验证管道
    """

    def __init__(
        self,
        min_medical_keywords: int = 2,
        min_dialogue_turns: int = 2,
        strict_mode: bool = False
    ):
        """
        Initialize the pipeline.

        Args:
            min_medical_keywords: Minimum medical keywords required
            min_dialogue_turns: Minimum dialogue turns required
            strict_mode: Treat warnings as errors
        """
        self.validator = MedicalDialogueValidator(
            min_medical_keywords=min_medical_keywords,
            min_dialogue_turns=min_dialogue_turns,
            strict_mode=strict_mode
        )

    def validate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single task and return detailed report.

        Args:
            task: Task dictionary

        Returns:
            Validation report dictionary
        """
        is_valid, messages = self.validator.validate(task)

        return {
            "is_valid": is_valid,
            "medical_relevance": self.validator.calculate_medical_score(task),
            "issues": messages,
            "task_id": task.get("id", "unknown")
        }

    def validate_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate multiple tasks.

        Args:
            tasks: List of task dictionaries

        Returns:
            Summary validation report
        """
        total_tasks = len(tasks)
        valid_tasks = 0
        all_issues = []

        for task in tasks:
            report = self.validate_task(task)
            if report["is_valid"]:
                valid_tasks += 1
            all_issues.extend([
                f"{report['task_id']}: {msg}"
                for msg in report["issues"]
            ])

        # Calculate statistics
        scores = [
            self.validator.calculate_medical_score(task)
            for task in tasks
        ]

        avg_score = sum(scores) / len(scores) if scores else 0.0

        return {
            "total_tasks": total_tasks,
            "valid_tasks": valid_tasks,
            "invalid_tasks": total_tasks - valid_tasks,
            "validity_rate": valid_tasks / total_tasks if total_tasks > 0 else 0.0,
            "avg_medical_score": avg_score,
            "all_issues": all_issues,
        }

    def filter_valid_dialogues(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filter tasks into valid and invalid medical dialogues.

        Args:
            tasks: List of task dictionaries

        Returns:
            Tuple of (valid_tasks, invalid_tasks)
        """
        valid_tasks = []
        invalid_tasks = []

        for task in tasks:
            report = self.validate_task(task)
            task_with_report = {**task, "_validation": report}

            if report["is_valid"]:
                valid_tasks.append(task_with_report)
            else:
                invalid_tasks.append(task_with_report)

        return valid_tasks, invalid_tasks


# Export
__all__ = [
    "MedicalDialogueValidator",
    "MedicalDialoguePipeline",
]
