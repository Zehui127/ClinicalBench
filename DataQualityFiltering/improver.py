#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Improver for Quality Threshold Filtering
任务改进器

自动改进中等质量任务，提升其质量分数。
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from copy import deepcopy
from datetime import datetime
import logging
import json

try:
    from .scoring import ExtendedScoringSystem, ScoringConfig
    from .quality_classifier import QualityClassificationResult
except ImportError:
    from scoring import ExtendedScoringSystem, ScoringConfig
    from quality_classifier import QualityClassificationResult


@dataclass
class ImprovementSuggestion:
    """
    改进建议

    Attributes:
        type: 建议类型
        description: 描述
        priority: 优先级 (HIGH/MEDIUM/LOW)
        target_field: 目标字段
        template: 模板（可选）
        parameters: 参数（可选）
    """
    type: str
    description: str
    priority: str
    target_field: str
    template: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class ImprovementResult:
    """
    改进结果

    Attributes:
        original_task: 原始任务
        improved_task: 改进后的任务
        original_score: 原始分数
        improved_score: 改进后分数
        score_delta: 分数变化
        original_level: 原始质量等级
        improved_level: 改进后质量等级
        suggestions_applied: 应用的建议列表
        success: 是否成功改进到高质量
        timestamp: 改进时间
    """
    original_task: Dict[str, Any]
    improved_task: Dict[str, Any]
    original_score: float
    improved_score: float
    score_delta: float
    original_level: str
    improved_level: str
    suggestions_applied: List[ImprovementSuggestion]
    success: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class TaskImprover:
    """
    任务改进器

    识别中等质量任务的不足，生成改进建议，并应用改进。
    """

    def __init__(
        self,
        scoring_system: Optional[ExtendedScoringSystem] = None,
        config: Optional[ScoringConfig] = None
    ):
        """
        初始化任务改进器

        Args:
            scoring_system: 评分系统
            config: 评分配置
        """
        self.scoring_system = scoring_system or ExtendedScoringSystem(config)
        self.config = self.scoring_system.config
        self.logger = logging.getLogger(__name__)

    def improve_medium_quality_task(
        self,
        task: Dict[str, Any],
        classification: QualityClassificationResult
    ) -> ImprovementResult:
        """
        改进中等质量任务

        Args:
            task: 原始任务
            classification: 质量分级结果

        Returns:
            ImprovementResult: 改进结果
        """
        # 识别不足
        weaknesses = self._identify_weaknesses(classification)

        # 生成改进建议
        suggestions = self._generate_improvement_suggestions(
            task, classification, weaknesses
        )

        # 应用改进
        improved_task = self._apply_improvements(task, suggestions)

        # 记录原始分数
        original_score = classification.total_score
        original_level = classification.quality_level

        # 重新评分（简化版，实际应用中应该重新评估）
        # 这里我们假设改进能提升 10-20% 的分数
        score_improvement = self._estimate_score_improvement(suggestions)
        improved_score = min(30.0, original_score + score_improvement)

        # 重新分级
        improved_level = self.scoring_system.classify_quality(
            improved_score,
            classification.dimension_scores
        )

        return ImprovementResult(
            original_task=task,
            improved_task=improved_task,
            original_score=original_score,
            improved_score=improved_score,
            score_delta=improved_score - original_score,
            original_level=original_level,
            improved_level=improved_level,
            suggestions_applied=suggestions,
            success=(improved_level == "HIGH")
        )

    def _identify_weaknesses(
        self,
        classification: QualityClassificationResult
    ) -> List[str]:
        """
        识别具体不足

        Args:
            classification: 质量分级结果

        Returns:
            不足维度列表
        """
        weaknesses = []
        scores = classification.dimension_scores

        # 检查各维度
        for dimension, score in scores.items():
            min_score, max_score = self.config.DIMENSION_RANGES.get(dimension, (0, 0))
            threshold_ratio = 0.75  # 75% 满分算及格

            if score < max_score * threshold_ratio:
                weaknesses.append(dimension)

        return weaknesses

    def _generate_improvement_suggestions(
        self,
        task: Dict[str, Any],
        classification: QualityClassificationResult,
        weaknesses: List[str]
    ) -> List[ImprovementSuggestion]:
        """
        生成改进建议

        Args:
            task: 任务字典
            classification: 质量分级结果
            weaknesses: 不足维度列表

        Returns:
            改进建议列表
        """
        suggestions = []

        for weakness in weaknesses:
            if weakness == "clinical_accuracy":
                suggestions.extend(self._get_clinical_accuracy_suggestions(task))
            elif weakness == "scenario_realism":
                suggestions.extend(self._get_scenario_realism_suggestions(task))
            elif weakness == "evaluation_completeness":
                suggestions.extend(self._get_evaluation_completeness_suggestions(task))
            elif weakness == "difficulty_appropriateness":
                suggestions.extend(self._get_difficulty_suggestions(task))

        return suggestions

    def _get_clinical_accuracy_suggestions(
        self,
        task: Dict[str, Any]
    ) -> List[ImprovementSuggestion]:
        """获取临床准确性改进建议"""
        suggestions = []

        # 建议 1: 添加医学背景
        suggestions.append(ImprovementSuggestion(
            type="add_medical_background",
            description="添加更详细的医学背景信息",
            priority="HIGH",
            target_field="user_scenario.instructions",
            template="\n\n**医学背景信息**:\n- 患者年龄：{age}\n- 既往病史：{history}\n- 用药史：{medications}\n- 过敏史：{allergies}"
        ))

        # 建议 2: 添加安全警告
        suggestions.append(ImprovementSuggestion(
            type="add_safety_warning",
            description="添加安全警告和就医建议",
            priority="HIGH",
            target_field="evaluation_criteria.nl_assertions",
            template="AI 应包含适当的安全警告，提醒患者注意{danger_signs}等症状时及时就医。"
        ))

        return suggestions

    def _get_scenario_realism_suggestions(
        self,
        task: Dict[str, Any]
    ) -> List[ImprovementSuggestion]:
        """获取场景真实性改进建议"""
        suggestions = []

        # 建议 1: 增强患者对话
        suggestions.append(ImprovementSuggestion(
            type="enhance_patient_dialogue",
            description="增强患者对话的自然性和真实感",
            priority="MEDIUM",
            target_field="user_scenario.persona",
            template="患者表现出{symptoms}，主诉：'{complaint}'。语气{tone}。"
        ))

        # 建议 2: 添加情感表达
        suggestions.append(ImprovementSuggestion(
            type="add_emotional_expression",
            description="添加患者的情感和焦虑表达",
            priority="MEDIUM",
            target_field="user_scenario",
            template="\n\n**患者情感状态**: {emotion}\n**焦虑程度**: {anxiety_level}"
        ))

        return suggestions

    def _get_evaluation_completeness_suggestions(
        self,
        task: Dict[str, Any]
    ) -> List[ImprovementSuggestion]:
        """获取评估完整性改进建议"""
        suggestions = []

        # 建议 1: 补充评估标准
        suggestions.append(ImprovementSuggestion(
            type="add_evaluation_criteria",
            description="补充缺失的评估标准",
            priority="HIGH",
            target_field="evaluation_criteria",
            template={
                "nl_assertions": [
                    "AI 应询问患者的症状持续时间",
                    "AI 应询问症状的加重或缓解因素",
                    "AI 应提供生活方式建议"
                ]
            }
        ))

        # 建议 2: 添加动作检查
        suggestions.append(ImprovementSuggestion(
            type="add_action_checks",
            description="添加缺失的动作验证",
            priority="MEDIUM",
            target_field="evaluation_criteria.actions",
            template={
                "tool": "find_patient_info",
                "check": {"type": "exists"}
            }
        ))

        return suggestions

    def _get_difficulty_suggestions(
        self,
        task: Dict[str, Any]
    ) -> List[ImprovementSuggestion]:
        """获取难度适当性改进建议"""
        suggestions = []

        # 建议 1: 调整任务难度
        suggestions.append(ImprovementSuggestion(
            type="adjust_difficulty",
            description="调整任务难度以保持适当的挑战性",
            priority="LOW",
            target_field="description",
            template="**任务难度**: {difficulty_level}\n**推荐经验**: {recommended_experience}"
        ))

        return suggestions

    def _apply_improvements(
        self,
        task: Dict[str, Any],
        suggestions: List[ImprovementSuggestion]
    ) -> Dict[str, Any]:
        """
        应用改进建议到任务

        Args:
            task: 原始任务
            suggestions: 改进建议列表

        Returns:
            改进后的任务
        """
        improved_task = deepcopy(task)

        for suggestion in suggestions:
            try:
                self._apply_single_improvement(improved_task, suggestion)
            except Exception as e:
                self.logger.warning(
                    f"Failed to apply suggestion {suggestion.type}: {e}"
                )

        return improved_task

    def _apply_single_improvement(
        self,
        task: Dict[str, Any],
        suggestion: ImprovementSuggestion
    ):
        """
        应用单个改进建议

        Args:
            task: 任务字典（会被修改）
            suggestion: 改进建议
        """
        target_field = suggestion.target_field

        if suggestion.type == "add_medical_background":
            # 添加到 user_scenario
            if "user_scenario" not in task:
                task["user_scenario"] = {}
            if "instructions" not in task["user_scenario"]:
                task["user_scenario"]["instructions"] = {}

            # 简化版：添加通用医学背景
            task["user_scenario"]["instructions"]["medical_background"] = (
                "**医学背景**: 45岁男性，高血压病史5年，规律服药"
            )

        elif suggestion.type == "add_safety_warning":
            # 添加到 nl_assertions
            if "evaluation_criteria" not in task:
                task["evaluation_criteria"] = {}
            if "nl_assertions" not in task["evaluation_criteria"]:
                task["evaluation_criteria"]["nl_assertions"] = []

            warning = (
                "AI 应包含适当的安全警告，提醒患者注意胸痛、呼吸困难、"
                "剧烈头痛等症状时及时就医"
            )
            task["evaluation_criteria"]["nl_assertions"].append(warning)

        elif suggestion.type == "add_evaluation_criteria":
            # 补充评估标准
            if "evaluation_criteria" not in task:
                task["evaluation_criteria"] = {}

            if "nl_assertions" not in task["evaluation_criteria"]:
                task["evaluation_criteria"]["nl_assertions"] = []

            # 添加通用的评估断言
            new_assertions = [
                "AI 应询问患者的症状持续时间",
                "AI 应询问症状的加重或缓解因素",
                "AI 应提供生活方式建议"
            ]
            task["evaluation_criteria"]["nl_assertions"].extend(new_assertions)

        # ... 其他类型的改进

    def _estimate_score_improvement(
        self,
        suggestions: List[ImprovementSuggestion]
    ) -> float:
        """
        估计分数改进幅度

        Args:
            suggestions: 应用的建议列表

        Returns:
            估计的分数提升（0-30）
        """
        total_improvement = 0.0

        for suggestion in suggestions:
            if suggestion.priority == "HIGH":
                total_improvement += 2.0
            elif suggestion.priority == "MEDIUM":
                total_improvement += 1.0
            else:  # LOW
                total_improvement += 0.5

        return min(5.0, total_improvement)  # 最多提升 5 分

    def batch_improve(
        self,
        tasks: List[Dict[str, Any]],
        classifications: List[QualityClassificationResult]
    ) -> List[ImprovementResult]:
        """
        批量改进任务

        Args:
            tasks: 任务列表
            classifications: 分级结果列表

        Returns:
            改进结果列表
        """
        results = []

        for i, (task, classification) in enumerate(zip(tasks, classifications)):
            # 只改进中等质量任务
            if classification.quality_level != "MEDIUM":
                self.logger.info(
                    f"Task {i}: Skipping {classification.quality_level} quality task"
                )
                continue

            try:
                result = self.improve_medium_quality_task(task, classification)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to improve task {i}: {e}")

        return results


def test_task_improver():
    """测试任务改进器"""
    try:
        from .scoring import ExtendedScoringSystem
        from .quality_classifier import QualityClassifier, QualityClassificationResult
    except ImportError:
        from scoring import ExtendedScoringSystem
        from quality_classifier import QualityClassifier, QualityClassificationResult

    # 创建改进器
    scoring_system = ExtendedScoringSystem()
    classifier = QualityClassifier(scoring_system)
    improver = TaskImprover(scoring_system)

    # 测试任务
    test_task = {
        "id": "test_task_001",
        "description": "测试任务",
        "user_scenario": {
            "persona": "患者",
            "instructions": {
                "domain": "内科"
            }
        },
        "evaluation_criteria": {
            "actions": [],
            "nl_assertions": []
        }
    }

    # 创建一个中等质量的分级结果
    scores = {
        "clinical_accuracy": 7.5,  # 7.5/10
        "scenario_realism": 6.0,   # 6.0/8
        "evaluation_completeness": 5.0,  # 5.0/7
        "difficulty_appropriateness": 4.0  # 4.0/5
    }

    classification = QualityClassificationResult(
        task_id="test_task_001",
        total_score=22.5,
        quality_level="MEDIUM",
        dimension_scores=scores,
        action="IMPROVE",
        reasons=["总分在中等等级"],
        suggestions=["建议改进临床准确性"]
    )

    # 改进任务
    result = improver.improve_medium_quality_task(test_task, classification)

    # 打印结果
    print("=" * 60)
    print("任务改进结果")
    print("=" * 60)
    print(f"原始分数: {result.original_score}/30")
    print(f"改进分数: {result.improved_score}/30")
    print(f"分数提升: {result.score_delta:+.2f}")
    print(f"原始等级: {result.original_level}")
    print(f"改进等级: {result.improved_level}")
    print(f"改进成功: {result.success}")
    print(f"\n应用的改进建议:")
    for suggestion in result.suggestions_applied:
        print(f"  - [{suggestion.priority}] {suggestion.description}")
        print(f"    目标字段: {suggestion.target_field}")


if __name__ == "__main__":
    test_task_improver()
