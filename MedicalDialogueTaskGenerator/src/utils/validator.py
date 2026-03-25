"""
任务验证器
Medical Dialogue Task Generator - Task Validator

This module validates generated tasks for format and logical consistency.
"""

from typing import List, Dict, Any, Optional
import re

from ..models.data_models import MedicalDialogueTask, PatientBehavior


class TaskValidator:
    """任务验证器"""

    # 有效的场景类型
    VALID_SCENARIO_TYPES = {
        "INFORMATION_QUERY", "SYMPTOM_ANALYSIS", "CHRONIC_MANAGEMENT",
        "MEDICATION_CONSULTATION", "LIFESTYLE_ADVICE", "EMERGENCY_CONCERN",
        "FOLLOW_UP", "SECOND_OPINION"
    }

    # 有效的难度级别
    VALID_DIFFICULTY_LEVELS = {"L1", "L2", "L3"}

    # 有效的配合度
    VALID_COOPERATION_LEVELS = {"good", "partial", "poor"}

    # 有效的信息质量
    VALID_INFORMATION_QUALITY = {"good", "medium", "poor"}

    # 有效的行为类型
    VALID_BEHAVIORS = {
        "withholding", "lying", "contradicting", "emotional",
        "poor_memory", "low_knowledge"
    }

    # 有效的情绪状态
    VALID_EMOTIONAL_TYPES = {"anxious", "fearful", "angry", "panicked", "calm"}

    # 有效的强度级别
    VALID_INTENSITY_LEVELS = {"low", "medium", "high"}

    def __init__(self):
        """初始化验证器"""
        self.errors = []
        self.warnings = []

    def validate(self, task: MedicalDialogueTask) -> bool:
        """验证任务格式和逻辑

        Args:
            task: 要验证的任务

        Returns:
            是否验证通过
        """
        self.errors = []
        self.warnings = []

        checks = [
            self._validate_required_fields(task),
            self._validate_difficulty_consistency(task),
            self._validate_behavior_consistency(task),
            self._validate_evaluation_criteria(task),
            self._validate_scenario_type(task),
            self._validate_metadata(task)
        ]

        return all(checks)

    def get_errors(self) -> List[str]:
        """获取错误列表

        Returns:
            错误列表
        """
        return self.errors

    def get_warnings(self) -> List[str]:
        """获取警告列表

        Returns:
            警告列表
        """
        return self.warnings

    def _add_error(self, error: str):
        """添加错误

        Args:
            error: 错误信息
        """
        self.errors.append(error)

    def _add_warning(self, warning: str):
        """添加警告

        Args:
            warning: 警告信息
        """
        self.warnings.append(warning)

    def _validate_required_fields(self, task: MedicalDialogueTask) -> bool:
        """验证必需字段

        Args:
            task: 要验证的任务

        Returns:
            是否通过验证
        """
        required_fields = [
            "id", "description", "user_scenario", "ticket",
            "initial_state", "evaluation_criteria", "metadata",
            "difficulty", "patient_behavior"
        ]

        valid = True
        for field in required_fields:
            if not hasattr(task, field):
                self._add_error(f"Missing required field: {field}")
                valid = False

        return valid

    def _validate_difficulty_consistency(self, task: MedicalDialogueTask) -> bool:
        """验证难度级别一致性

        Args:
            task: 要验证的任务

        Returns:
            是否通过验证
        """
        difficulty = task.difficulty

        # 验证难度级别值
        if difficulty not in self.VALID_DIFFICULTY_LEVELS:
            self._add_error(f"Invalid difficulty level: {difficulty}")
            return False

        # 验证元数据中的难度级别
        metadata_difficulty = task.metadata.difficulty_level if hasattr(task.metadata, 'difficulty_level') else None
        if metadata_difficulty and metadata_difficulty != difficulty:
            self._add_error(f"Difficulty mismatch: task.difficulty={difficulty}, metadata.difficulty_level={metadata_difficulty}")
            return False

        # 验证难度与行为的一致性
        if difficulty == "L1":
            if task.patient_behavior.cooperation != "good":
                self._add_error(f"L1 task should have cooperation='good', got '{task.patient_behavior.cooperation}'")
                return False
            if len(task.patient_behavior.behaviors) > 0:
                self._add_error(f"L1 task should have no behaviors, got {task.patient_behavior.behaviors}")
                return False
            if task.red_line_tests is not None:
                self._add_error("L1 task should not have red_line_tests")
                return False

        elif difficulty == "L2":
            if task.patient_behavior.cooperation not in ["partial", "poor"]:
                self._add_error(f"L2 task should have cooperation in ['partial', 'poor'], got '{task.patient_behavior.cooperation}'")
                return False
            if len(task.patient_behavior.behaviors) == 0:
                self._add_error("L2 task should have at least one behavior")
                return False
            if "contradicting" in task.patient_behavior.behaviors:
                self._add_error("L2 task should not have contradicting behavior")
                return False
            if task.conversation_flow is None:
                self._add_warning("L2 task should have conversation_flow")

        elif difficulty == "L3":
            if task.patient_behavior.cooperation != "poor":
                self._add_error(f"L3 task should have cooperation='poor', got '{task.patient_behavior.cooperation}'")
                return False
            if len(task.patient_behavior.behaviors) < 3:
                self._add_error(f"L3 task should have at least 3 behaviors, got {len(task.patient_behavior.behaviors)}")
                return False
            if task.red_line_tests is None or len(task.red_line_tests) == 0:
                self._add_error("L3 task should have red_line_tests")
                return False
            if task.conversation_flow is None:
                self._add_error("L3 task should have conversation_flow")
                return False

        return True

    def _validate_behavior_consistency(self, task: MedicalDialogueTask) -> bool:
        """验证行为一致性

        Args:
            task: 要验证的任务

        Returns:
            是否通过验证
        """
        valid = True
        behaviors = task.patient_behavior.behaviors if task.patient_behavior.behaviors else []

        # 验证行为类型
        for behavior in behaviors:
            if behavior not in self.VALID_BEHAVIORS:
                self._add_error(f"Invalid behavior type: {behavior}")
                valid = False

        # 验证情绪行为
        if "emotional" in behaviors:
            if not hasattr(task.patient_behavior, "emotional_state") or not task.patient_behavior.emotional_state:
                self._add_error("emotional behavior requires emotional_state field")
                valid = False
            else:
                emotional_state = task.patient_behavior.emotional_state
                if isinstance(emotional_state, dict):
                    emotion_type = emotional_state.get("type")
                    if emotion_type and emotion_type not in self.VALID_EMOTIONAL_TYPES:
                        self._add_error(f"Invalid emotional_state type: {emotion_type}")
                        valid = False

                    intensity = emotional_state.get("intensity")
                    if intensity and intensity not in self.VALID_INTENSITY_LEVELS:
                        self._add_error(f"Invalid emotional_state intensity: {intensity}")
                        valid = False

        # 验证矛盾行为
        if "contradicting" in behaviors:
            if not hasattr(task.patient_behavior, "contradictions") or not task.patient_behavior.contradictions:
                self._add_error("contradicting behavior requires contradictions field")
                valid = False

        # 验证信息质量与配合度的一致性
        cooperation = task.patient_behavior.cooperation
        info_quality = task.patient_behavior.information_quality

        quality_mapping = {
            "good": "good",
            "partial": "medium",
            "poor": "poor"
        }

        expected_quality = quality_mapping.get(cooperation)
        if expected_quality and info_quality != expected_quality:
            self._add_warning(f"information_quality '{info_quality}' may not match cooperation '{cooperation}'")

        return valid

    def _validate_evaluation_criteria(self, task: MedicalDialogueTask) -> bool:
        """验证评估标准

        Args:
            task: 要验证的任务

        Returns:
            是否通过验证
        """
        criteria = task.evaluation_criteria
        valid = True

        # 验证actions
        if not criteria.actions or len(criteria.actions) == 0:
            self._add_error("evaluation_criteria must have at least one action")
            valid = False
        else:
            for action in criteria.actions:
                if hasattr(action, "arguments") and "should_address" not in action.arguments:
                    self._add_error("Action must have 'should_address' in arguments")
                    valid = False

        # 验证communication_checks
        if not criteria.communication_checks or len(criteria.communication_checks) == 0:
            self._add_error("evaluation_criteria must have at least one communication_check")
            valid = False

        return valid

    def _validate_scenario_type(self, task: MedicalDialogueTask) -> bool:
        """验证场景类型

        Args:
            task: 要验证的任务

        Returns:
            是否通过验证
        """
        scenario_type = task.metadata.scenario_type if hasattr(task.metadata, "scenario_type") else None

        if not scenario_type:
            self._add_error("metadata must have scenario_type")
            return False

        if scenario_type not in self.VALID_SCENARIO_TYPES:
            self._add_error(f"Invalid scenario_type: {scenario_type}")
            return False

        return True

    def _validate_metadata(self, task: MedicalDialogueTask) -> bool:
        """验证元数据

        Args:
            task: 要验证的任务

        Returns:
            是否通过验证
        """
        metadata = task.metadata
        valid = True

        # 验证必需字段
        required_metadata_fields = [
            "source", "department_cn", "original_title",
            "scenario_type", "scenario_name", "scenario_confidence",
            "inquiry_requirements", "safety_rules"
        ]

        for field in required_metadata_fields:
            if not hasattr(metadata, field):
                self._add_error(f"metadata missing required field: {field}")
                valid = False

        # 验证inquiry_requirements
        if hasattr(metadata, "inquiry_requirements") and metadata.inquiry_requirements:
            inquiry_req = metadata.inquiry_requirements
            if isinstance(inquiry_req, dict):
                # 验证至少有一个类别
                if len(inquiry_req) == 0:
                    self._add_error("inquiry_requirements must have at least one category")
                    valid = False

        # 验证safety_rules
        if hasattr(metadata, "safety_rules") and metadata.safety_rules:
            safety_rules = metadata.safety_rules
            if isinstance(safety_rules, list):
                # 验证至少有一个安全规则
                if len(safety_rules) == 0:
                    self._add_warning("safety_rules is empty")

        return valid


class LogicalConsistencyChecker:
    """逻辑一致性检查器"""

    def check(self, task: MedicalDialogueTask) -> List[str]:
        """检查逻辑一致性

        Args:
            task: 要检查的任务

        Returns:
            错误列表
        """
        errors = []

        # 检查难度与行为一致性
        errors.extend(self._check_difficulty_behavior(task))

        # 检查withholding与conversation_flow一致性
        errors.extend(self._check_withholding_flow(task))

        # 检查red_line_tests与场景类型一致性
        errors.extend(self._check_redline_scenario(task))

        return errors

    def _check_difficulty_behavior(self, task: MedicalDialogueTask) -> List[str]:
        """检查难度与行为一致性"""
        errors = []

        if task.difficulty == "L1":
            if task.patient_behavior.behaviors:
                errors.append("L1任务不应有患者行为")

        elif task.difficulty == "L2":
            if "contradicting" in (task.patient_behavior.behaviors or []):
                errors.append("L2任务不应有矛盾行为")

        return errors

    def _check_withholding_flow(self, task: MedicalDialogueTask) -> List[str]:
        """检查withholding与conversation_flow一致性"""
        errors = []

        if (hasattr(task.patient_behavior, "withholding") and
            task.patient_behavior.withholding and
            task.conversation_flow is None):
            errors.append("有withholding行为但缺少conversation_flow")

        if (task.conversation_flow and
            hasattr(task.conversation_flow, "unfolding_pattern") and
            task.conversation_flow.unfolding_pattern != "progressive_disclosure"):
            if (hasattr(task.patient_behavior, "withholding") and
                task.patient_behavior.withholding):
                errors.append("withholding行为需要progressive_disclosure模式")

        return errors

    def _check_redline_scenario(self, task: MedicalDialogueTask) -> List[str]:
        """检查red_line_tests与场景类型一致性"""
        errors = []

        if not task.red_line_tests:
            return errors

        scenario_type = task.metadata.scenario_type if hasattr(task.metadata, "scenario_type") else None

        # 检查是否需要过敏相关的红线测试
        has_ignore_allergy = any(test.type == "ignore_allergy" for test in task.red_line_tests if hasattr(test, "type"))

        if has_ignore_allergy and scenario_type not in ["MEDICATION_CONSULTATION", "INFORMATION_QUERY", "CHRONIC_MANAGEMENT"]:
            errors.append(f"ignore_allergy红线测试可能不适合场景类型: {scenario_type}")

        return errors
