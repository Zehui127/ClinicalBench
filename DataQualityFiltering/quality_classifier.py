#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Classifier for Quality Threshold Filtering
质量分级器

对任务进行三级质量分类：HIGH (≥27), MEDIUM (24-26), LOW (<24)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

try:
    from .scoring import ExtendedScoringSystem, ScoringConfig
except ImportError:
    from scoring import ExtendedScoringSystem, ScoringConfig


@dataclass
class QualityClassificationResult:
    """
    质量分级结果

    Attributes:
        task_id: 任务 ID
        total_score: 总分（0-30）
        quality_level: 质量等级 (HIGH/MEDIUM/LOW)
        dimension_scores: 各维度分数
        action: 处理动作 (KEEP/IMPROVE/REJECT)
        reasons: 分级原因列表
        suggestions: 改进建议列表
        timestamp: 评估时间戳
    """
    task_id: str
    total_score: float
    quality_level: str
    dimension_scores: Dict[str, float]
    action: str
    reasons: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class QualityClassifier:
    """
    质量分级器

    根据扩展评分系统对任务进行三级质量分类。
    """

    def __init__(
        self,
        scoring_system: Optional[ExtendedScoringSystem] = None,
        config: Optional[ScoringConfig] = None
    ):
        """
        初始化质量分级器

        Args:
            scoring_system: 评分系统
            config: 评分配置
        """
        self.scoring_system = scoring_system or ExtendedScoringSystem(config)
        self.config = self.scoring_system.config
        self.logger = logging.getLogger(__name__)

    def classify(
        self,
        task: Dict[str, Any],
        dimension_scores: Dict[str, float],
        original_scores: Optional[Dict[str, float]] = None
    ) -> QualityClassificationResult:
        """
        对任务进行质量分级

        Args:
            task: 任务字典
            dimension_scores: 扩展分数制的各维度分数 (0-10, 0-8, 0-7, 0-5)
            original_scores: 原始 5 分制的分数（可选，用于生成建议）

        Returns:
            QualityClassificationResult: 分级结果
        """
        # 计算总分
        total_score = self.scoring_system.calculate_total_score(dimension_scores)

        # 质量分级
        quality_level = self.scoring_system.classify_quality(
            total_score, dimension_scores
        )

        # 获取处理动作
        action = self.scoring_system.get_action_for_quality(quality_level)

        # 获取分级原因
        reasons = self.scoring_system.get_quality_reasons(
            total_score, dimension_scores, quality_level
        )

        # 生成改进建议
        suggestions = self._generate_suggestions(
            quality_level, dimension_scores, original_scores
        )

        # 获取任务 ID
        task_id = task.get("id") or task.get("task_id", "unknown")

        return QualityClassificationResult(
            task_id=task_id,
            total_score=total_score,
            quality_level=quality_level,
            dimension_scores=dimension_scores,
            action=action,
            reasons=reasons,
            suggestions=suggestions
        )

    def _generate_suggestions(
        self,
        quality_level: str,
        dimension_scores: Dict[str, float],
        original_scores: Optional[Dict[str, float]] = None
    ) -> List[str]:
        """
        生成改进建议

        Args:
            quality_level: 质量等级
            dimension_scores: 扩展分数制的各维度分数
            original_scores: 原始 5 分制的分数

        Returns:
            改进建议列表
        """
        suggestions = []

        if quality_level == "HIGH":
            suggestions.append("任务质量优秀，建议保留")
            return suggestions

        # 检查需要改进的维度
        for dimension, score in dimension_scores.items():
            min_score, max_score = self.config.DIMENSION_RANGES.get(dimension, (0, 0))
            threshold_ratio = 0.75  # 75% 满分算及格

            if score < max_score * threshold_ratio:
                suggestion = self._get_dimension_suggestion(dimension, score, max_score)
                if suggestion:
                    suggestions.append(suggestion)

        # 如果没有具体建议，添加通用建议
        if not suggestions:
            suggestions.append("建议请医学专家审核任务内容")

        return suggestions

    def _get_dimension_suggestion(
        self,
        dimension: str,
        score: float,
        max_score: float
    ) -> Optional[str]:
        """
        获取特定维度的改进建议

        Args:
            dimension: 维度名称
            score: 当前分数
            max_score: 满分

        Returns:
            改进建议
        """
        dimension_suggestions = {
            "clinical_accuracy": {
                "prefix": "临床准确性",
                "suggestions": [
                    "添加更详细的医学背景信息",
                    "补充完整的诊断和治疗方案",
                    "确保医学术语使用准确",
                    "添加药物相互作用说明",
                    "包含安全警告和禁忌症"
                ]
            },
            "scenario_realism": {
                "prefix": "场景真实性",
                "suggestions": [
                    "增强患者对话的自然性",
                    "添加真实患者的表达习惯",
                    "补充合理的患者提问",
                    "完善临床场景的时间线",
                    "增加患者的情感表达"
                ]
            },
            "evaluation_completeness": {
                "prefix": "评估完整性",
                "suggestions": [
                    "补充评估标准中的缺失项",
                    "添加更详细的验证条件",
                    "完善动作检查列表",
                    "增加自然语言断言",
                    "补充环境断言条件"
                ]
            },
            "difficulty_appropriateness": {
                "prefix": "难度适当性",
                "suggestions": [
                    "调整任务难度级别",
                    "平衡信息复杂度",
                    "确保任务有明确的目标",
                    "避免过于简单或复杂",
                    "添加适当的挑战性"
                ]
            }
        }

        if dimension not in dimension_suggestions:
            return None

        info = dimension_suggestions[dimension]
        score_ratio = score / max_score if max_score > 0 else 0

        if score_ratio < 0.5:
            # 严重不足
            return f"{info['prefix']}：{info['suggestions'][0]}，{info['suggestions'][1]}"
        elif score_ratio < 0.75:
            # 有改进空间
            return f"{info['prefix']}：{info['suggestions'][0]}"
        else:
            # 尚可
            return None

    def batch_classify(
        self,
        tasks: List[Dict[str, Any]],
        scores_list: List[Dict[str, float]],
        original_scores_list: Optional[List[Dict[str, float]]] = None
    ) -> List[QualityClassificationResult]:
        """
        批量分级

        Args:
            tasks: 任务列表
            scores_list: 扩展分数列表
            original_scores_list: 原始分数列表（可选）

        Returns:
            分级结果列表
        """
        results = []

        for i, task in enumerate(tasks):
            scores = scores_list[i] if i < len(scores_list) else {}
            original_scores = (
                original_scores_list[i] if original_scores_list and i < len(original_scores_list) else None
            )

            try:
                result = self.classify(task, scores, original_scores)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error classifying task {i}: {e}")
                # 创建一个默认的 LOW 分级结果
                results.append(QualityClassificationResult(
                    task_id=task.get("id", f"task_{i}"),
                    total_score=0.0,
                    quality_level="LOW",
                    dimension_scores={},
                    action="REJECT",
                    reasons=[f"评估失败: {str(e)}"],
                    suggestions=["请检查任务格式"]
                ))

        return results

    def generate_statistics(
        self,
        results: List[QualityClassificationResult]
    ) -> Dict[str, Any]:
        """
        生成分级统计信息

        Args:
            results: 分级结果列表

        Returns:
            统计信息字典
        """
        total = len(results)

        if total == 0:
            return {
                "total_tasks": 0,
                "high_quality": 0,
                "medium_quality": 0,
                "low_quality": 0,
                "keep": 0,
                "improve": 0,
                "reject": 0,
                "average_score": 0.0,
                "score_distribution": {}
            }

        # 统计各等级数量
        high_count = sum(1 for r in results if r.quality_level == "HIGH")
        medium_count = sum(1 for r in results if r.quality_level == "MEDIUM")
        low_count = sum(1 for r in results if r.quality_level == "LOW")

        # 统计各动作数量
        keep_count = sum(1 for r in results if r.action == "KEEP")
        improve_count = sum(1 for r in results if r.action == "IMPROVE")
        reject_count = sum(1 for r in results if r.action == "REJECT")

        # 计算平均分
        avg_score = sum(r.total_score for r in results) / total

        # 分数分布
        score_ranges = {
            "0-10": 0,
            "10-15": 0,
            "15-20": 0,
            "20-24": 0,
            "24-27": 0,
            "27-30": 0
        }

        for result in results:
            score = result.total_score
            if score < 10:
                score_ranges["0-10"] += 1
            elif score < 15:
                score_ranges["10-15"] += 1
            elif score < 20:
                score_ranges["15-20"] += 1
            elif score < 24:
                score_ranges["20-24"] += 1
            elif score < 27:
                score_ranges["24-27"] += 1
            else:
                score_ranges["27-30"] += 1

        return {
            "total_tasks": total,
            "high_quality": high_count,
            "medium_quality": medium_count,
            "low_quality": low_count,
            "keep": keep_count,
            "improve": improve_count,
            "reject": reject_count,
            "average_score": round(avg_score, 2),
            "score_distribution": score_ranges,
            "pass_rate": round((keep_count + improve_count) / total * 100, 2)
        }


def test_quality_classifier():
    """测试质量分级器"""
    try:
        from .scoring import ExtendedScoringSystem
    except ImportError:
        from scoring import ExtendedScoringSystem

    # 创建分级器
    scoring_system = ExtendedScoringSystem()
    classifier = QualityClassifier(scoring_system)

    # 测试任务
    test_task = {
        "id": "test_task_001",
        "description": "测试任务",
        "clinical_scenario": "患者胸痛"
    }

    # 测试用例 1: 高质量
    print("=" * 60)
    print("测试用例 1: 高质量任务")
    print("=" * 60)

    scores_5_point = {
        "clinical_accuracy": 4.8,
        "scenario_realism": 4.5,
        "evaluation_completeness": 4.7,
        "difficulty_appropriateness": 4.5
    }

    extended_scores = scoring_system.convert_from_5_point_scale(scores_5_point)
    result = classifier.classify(test_task, extended_scores, scores_5_point)

    print(f"任务 ID: {result.task_id}")
    print(f"总分: {result.total_score}/30")
    print(f"质量等级: {result.quality_level}")
    print(f"处理动作: {result.action}")
    print(f"原因: {result.reasons}")
    print(f"建议: {result.suggestions}")

    # 测试用例 2: 中等质量
    print("\n" + "=" * 60)
    print("测试用例 2: 中等质量任务")
    print("=" * 60)

    scores_5_point = {
        "clinical_accuracy": 4.0,
        "scenario_realism": 3.8,
        "evaluation_completeness": 3.5,
        "difficulty_appropriateness": 3.5
    }

    extended_scores = scoring_system.convert_from_5_point_scale(scores_5_point)
    result = classifier.classify(test_task, extended_scores, scores_5_point)

    print(f"任务 ID: {result.task_id}")
    print(f"总分: {result.total_score}/30")
    print(f"质量等级: {result.quality_level}")
    print(f"处理动作: {result.action}")
    print(f"原因: {result.reasons}")
    print(f"建议: {result.suggestions}")

    # 测试用例 3: 低质量
    print("\n" + "=" * 60)
    print("测试用例 3: 低质量任务")
    print("=" * 60)

    scores_5_point = {
        "clinical_accuracy": 2.5,
        "scenario_realism": 2.8,
        "evaluation_completeness": 3.0,
        "difficulty_appropriateness": 2.5
    }

    extended_scores = scoring_system.convert_from_5_point_scale(scores_5_point)
    result = classifier.classify(test_task, extended_scores, scores_5_point)

    print(f"任务 ID: {result.task_id}")
    print(f"总分: {result.total_score}/30")
    print(f"质量等级: {result.quality_level}")
    print(f"处理动作: {result.action}")
    print(f"原因: {result.reasons}")
    print(f"建议: {result.suggestions}")


if __name__ == "__main__":
    test_quality_classifier()
