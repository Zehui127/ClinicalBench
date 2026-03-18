#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extended Scoring System for Quality Threshold Filtering
质量阈值筛选扩展评分系统

实现 0-30 分制的评分系统，支持三级质量分类。
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging


@dataclass
class ScoringConfig:
    """评分配置"""

    # 维度分数范围
    DIMENSION_RANGES: Dict[str, Tuple[int, int]] = None

    # 维度权重
    WEIGHTS: Dict[str, float] = None

    # 质量分级阈值
    HIGH_THRESHOLD: float = 27.0
    MEDIUM_THRESHOLD: float = 24.0

    # 维度最小及格线（一票否决）
    MIN_DIMENSION_SCORES: Dict[str, float] = None

    def __post_init__(self):
        if self.DIMENSION_RANGES is None:
            self.DIMENSION_RANGES = {
                "clinical_accuracy": (0, 10),
                "scenario_realism": (0, 8),
                "evaluation_completeness": (0, 7),
                "difficulty_appropriateness": (0, 5),
            }

        if self.WEIGHTS is None:
            self.WEIGHTS = {
                "clinical_accuracy": 0.33,
                "scenario_realism": 0.27,
                "evaluation_completeness": 0.23,
                "difficulty_appropriateness": 0.17,
            }

        if self.MIN_DIMENSION_SCORES is None:
            self.MIN_DIMENSION_SCORES = {
                "clinical_accuracy": 7.0,  # 临床准确性必须 ≥ 7/10
                "scenario_realism": 6.0,     # 场景真实性必须 ≥ 6/8
                "evaluation_completeness": 5.0,  # 评估完整性必须 ≥ 5/7
                "difficulty_appropriateness": 4.0,  # 难度适当性必须 ≥ 4/5
            }


class ExtendedScoringSystem:
    """
    扩展的评分系统 (0-30 分制)

    支持三级质量分类：
    - HIGH (≥27分): 保留
    - MEDIUM (24-26分): 改进后重新评估
    - LOW (<24分): 剔除
    """

    def __init__(self, config: Optional[ScoringConfig] = None):
        """
        初始化评分系统

        Args:
            config: 评分配置
        """
        self.config = config or ScoringConfig()
        self.logger = logging.getLogger(__name__)

    def normalize_dimension_score(
        self,
        dimension: str,
        original_score: float,
        original_max: float = 5.0
    ) -> float:
        """
        将原始分数（0-5 分制）转换为扩展分数

        Args:
            dimension: 维度名称
            original_score: 原始分数（0-5）
            original_max: 原始最大分数（默认 5.0）

        Returns:
            转换后的分数
        """
        if dimension not in self.config.DIMENSION_RANGES:
            self.logger.warning(f"Unknown dimension: {dimension}")
            return original_score

        min_score, max_score = self.config.DIMENSION_RANGES[dimension]

        # 线性缩放
        if original_max > 0:
            normalized = (original_score / original_max) * max_score
        else:
            normalized = original_score

        # 确保在范围内
        return max(min_score, min(max_score, normalized))

    def calculate_total_score(self, dimension_scores: Dict[str, float]) -> float:
        """
        计算总分（0-30 分制）

        Args:
            dimension_scores: 各维度分数 {
                "clinical_accuracy": float,
                "scenario_realism": float,
                "evaluation_completeness": float,
                "difficulty_appropriateness": float
            }

        Returns:
            总分（0-30）
        """
        # 直接使用各维度分数相加（已经是 0-30 分制）
        total = sum(dimension_scores.values())

        return round(total, 2)

    def classify_quality(
        self,
        total_score: float,
        dimension_scores: Optional[Dict[str, float]] = None
    ) -> str:
        """
        质量分级

        Args:
            total_score: 总分
            dimension_scores: 各维度分数（用于一票否决）

        Returns:
            质量等级: "HIGH", "MEDIUM", "LOW"
        """
        # 检查一票否决
        if dimension_scores:
            for dimension, min_score in self.config.MIN_DIMENSION_SCORES.items():
                if dimension_scores.get(dimension, 0) < min_score:
                    self.logger.info(
                        f"Dimension {dimension} below minimum: "
                        f"{dimension_scores.get(dimension, 0)} < {min_score}"
                    )
                    return "LOW"

        # 基于总分分级
        if total_score >= self.config.HIGH_THRESHOLD:
            return "HIGH"
        elif total_score >= self.config.MEDIUM_THRESHOLD:
            return "MEDIUM"
        else:
            return "LOW"

    def get_action_for_quality(self, quality_level: str) -> str:
        """
        根据质量等级获取处理动作

        Args:
            quality_level: 质量等级

        Returns:
            处理动作: "KEEP", "IMPROVE", "REJECT"
        """
        actions = {
            "HIGH": "KEEP",
            "MEDIUM": "IMPROVE",
            "LOW": "REJECT"
        }
        return actions.get(quality_level, "REJECT")

    def get_quality_reasons(
        self,
        total_score: float,
        dimension_scores: Dict[str, float],
        quality_level: str
    ) -> List[str]:
        """
        获取质量等级的原因

        Args:
            total_score: 总分
            dimension_scores: 各维度分数
            quality_level: 质量等级

        Returns:
            原因列表
        """
        reasons = []

        if quality_level == "HIGH":
            reasons.append("所有维度都达到高标准")
            reasons.append(f"总分 {total_score:.1f} ≥ {self.config.HIGH_THRESHOLD}")

        elif quality_level == "MEDIUM":
            reasons.append(f"总分 {total_score:.1f} 在中等质量范围")

            # 检查哪些维度需要改进
            for dimension, score in dimension_scores.items():
                min_score, max_score = self.config.DIMENSION_RANGES.get(dimension, (0, 0))
                threshold_ratio = 0.8  # 80% 满分算优秀

                if score < max_score * threshold_ratio:
                    reasons.append(f"{dimension}: {score:.1f}/{max_score} (可改进)")

        else:  # LOW
            reasons.append(f"总分 {total_score:.1f} < {self.config.MEDIUM_THRESHOLD}")

            # 检查严重不足的维度
            for dimension, score in dimension_scores.items():
                min_score = self.config.MIN_DIMENSION_SCORES.get(dimension, 0)
                if score < min_score:
                    reasons.append(f"{dimension}: {score:.1f} 低于最低要求 {min_score}")

        return reasons

    def convert_from_5_point_scale(
        self,
        scores_5_point: Dict[str, float]
    ) -> Dict[str, float]:
        """
        从 5 分制转换为扩展分数制

        Args:
            scores_5_point: 5 分制的分数 {
                "clinical_accuracy": float (0-5),
                "scenario_realism": float (0-5),
                "evaluation_completeness": float (0-5),
                "difficulty_appropriateness": float (0-5)
            }

        Returns:
            扩展分数制的分数
        """
        extended_scores = {}

        for dimension, score in scores_5_point.items():
            extended_scores[dimension] = self.normalize_dimension_score(
                dimension, score, original_max=5.0
            )

        return extended_scores


def test_scoring_system():
    """测试评分系统"""
    config = ScoringConfig()
    scoring_system = ExtendedScoringSystem(config)

    # 测试用例 1: 高质量任务
    print("=" * 60)
    print("测试用例 1: 高质量任务")
    print("=" * 60)

    scores_5_point = {
        "clinical_accuracy": 4.5,
        "scenario_realism": 4.2,
        "evaluation_completeness": 4.8,
        "difficulty_appropriateness": 4.0
    }

    extended_scores = scoring_system.convert_from_5_point_scale(scores_5_point)
    total_score = scoring_system.calculate_total_score(extended_scores)
    quality_level = scoring_system.classify_quality(total_score, extended_scores)

    print(f"原始分数 (5分制): {scores_5_point}")
    print(f"扩展分数: {extended_scores}")
    print(f"总分: {total_score}/30")
    print(f"质量等级: {quality_level}")
    print(f"处理动作: {scoring_system.get_action_for_quality(quality_level)}")
    print(f"原因: {scoring_system.get_quality_reasons(total_score, extended_scores, quality_level)}")

    # 测试用例 2: 中等质量任务
    print("\n" + "=" * 60)
    print("测试用例 2: 中等质量任务")
    print("=" * 60)

    scores_5_point = {
        "clinical_accuracy": 3.8,
        "scenario_realism": 3.5,
        "evaluation_completeness": 3.2,
        "difficulty_appropriateness": 3.0
    }

    extended_scores = scoring_system.convert_from_5_point_scale(scores_5_point)
    total_score = scoring_system.calculate_total_score(extended_scores)
    quality_level = scoring_system.classify_quality(total_score, extended_scores)

    print(f"原始分数 (5分制): {scores_5_point}")
    print(f"扩展分数: {extended_scores}")
    print(f"总分: {total_score}/30")
    print(f"质量等级: {quality_level}")
    print(f"处理动作: {scoring_system.get_action_for_quality(quality_level)}")
    print(f"原因: {scoring_system.get_quality_reasons(total_score, extended_scores, quality_level)}")

    # 测试用例 3: 低质量任务
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
    total_score = scoring_system.calculate_total_score(extended_scores)
    quality_level = scoring_system.classify_quality(total_score, extended_scores)

    print(f"原始分数 (5分制): {scores_5_point}")
    print(f"扩展分数: {extended_scores}")
    print(f"总分: {total_score}/30")
    print(f"质量等级: {quality_level}")
    print(f"处理动作: {scoring_system.get_action_for_quality(quality_level)}")
    print(f"原因: {scoring_system.get_quality_reasons(total_score, extended_scores, quality_level)}")


if __name__ == "__main__":
    test_scoring_system()
