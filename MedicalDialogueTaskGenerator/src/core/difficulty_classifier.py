"""
难度分类器
Medical Dialogue Task Generator - Difficulty Classifier

This module classifies the difficulty level of medical dialogue tasks.
"""

import random
from typing import Dict, Optional

from ..models.data_models import (
    DifficultyLevel,
    RawDialogueData,
    ScenarioType
)


class DifficultyClassifier:
    """难度级别分类器"""

    # 场景类型基础复杂度分数
    SCENARIO_COMPLEXITY = {
        ScenarioType.INFORMATION_QUERY: 1,
        ScenarioType.LIFESTYLE_ADVICE: 2,
        ScenarioType.FOLLOW_UP: 3,
        ScenarioType.SYMPTOM_ANALYSIS: 4,
        ScenarioType.SECOND_OPINION: 5,
        ScenarioType.CHRONIC_MANAGEMENT: 5,
        ScenarioType.MEDICATION_CONSULTATION: 6,
        ScenarioType.EMERGENCY_CONCERN: 7
    }

    # 复杂度阈值
    THRESHOLDS = {
        DifficultyLevel.L1: (0, 3),
        DifficultyLevel.L2: (4, 7),
        DifficultyLevel.L3: (8, 10)
    }

    # 复杂度计算权重
    WEIGHTS = {
        "question_length": 0.1,        # 问题长度权重
        "multiple_questions": 1.0,     # 多问题加分
        "medication_related": 1.0,     # 涉及药物加分
        "symptom_description": 1.0,    # 有症状描述加分
        "emotional_keywords": 1.5,     # 情绪关键词加分
        "chronic_disease": 0.5         # 慢性病加分
    }

    # 情绪关键词
    EMOTIONAL_KEYWORDS = [
        "担心", "害怕", "恐惧", "焦虑", "紧张",
        "生气", "愤怒", "痛苦", "难受",
        "救命", "受不了", "撑不住", "快不行了"
    ]

    # 慢性病关键词
    CHRONIC_DISEASE_KEYWORDS = [
        "高血压", "糖尿病", "心脏病", "冠心病",
        "慢性", "长期", "一直", "多年"
    ]

    def __init__(self, config: Optional[Dict] = None):
        """初始化难度分类器

        Args:
            config: 可选的配置字典，可包含：
                - difficulty_distribution: 难度分布 {L1: 0.4, L2: 0.4, L3: 0.2}
                - complexity_weights: 复杂度权重配置
                - scenario_complexity: 场景复杂度配置
        """
        self.config = config or {}

        # 加载配置
        self.difficulty_distribution = self.config.get(
            "difficulty_distribution",
            {DifficultyLevel.L1: 0.4, DifficultyLevel.L2: 0.4, DifficultyLevel.L3: 0.2}
        )

        # 合并权重配置
        custom_weights = self.config.get("complexity_weights", {})
        self.WEIGHTS.update(custom_weights)

        # 合并场景复杂度配置
        custom_complexity = self.config.get("scenario_complexity", {})
        for scenario, score in custom_complexity.items():
            try:
                scenario_enum = ScenarioType(scenario)
                self.SCENARIO_COMPLEXITY[scenario_enum] = score
            except ValueError:
                pass

    def classify(self, raw_data: RawDialogueData, scenario_type: str) -> str:
        """确定任务难度级别

        Args:
            raw_data: 原始对话数据
            scenario_type: 场景类型

        Returns:
            难度级别字符串 (L1, L2, L3)
        """
        # 1. 计算基础复杂度分数
        base_score = self._calculate_complexity_score(raw_data, scenario_type)

        # 2. 根据分数确定难度级别
        difficulty = self._score_to_difficulty(base_score)

        # 3. 可选：根据配置的分布进行调整
        # 这里可以实现一个随机调整机制，确保最终难度分布符合配置
        adjusted_difficulty = self._adjust_by_distribution(difficulty)

        return adjusted_difficulty

    def _calculate_complexity_score(self, raw_data: RawDialogueData, scenario_type: str) -> int:
        """计算复杂度分数（0-10）

        Args:
            raw_data: 原始对话数据
            scenario_type: 场景类型

        Returns:
            复杂度分数 (0-10)
        """
        score = 0

        # 1. 场景类型基础分
        try:
            scenario_enum = ScenarioType(scenario_type)
            score += self.SCENARIO_COMPLEXITY.get(scenario_enum, 3)
        except ValueError:
            score += 3  # 默认分数

        # 2. 问题长度（更复杂的问题通常分数更高）
        text_length = len(raw_data.ticket)
        if text_length > 50:
            score += int((text_length - 50) * self.WEIGHTS["question_length"])

        # 3. 是否包含多个问题
        question_count = raw_data.ticket.count('？') + raw_data.ticket.count('?')
        if question_count > 1:
            score += self.WEIGHTS["multiple_questions"]

        # 4. 是否涉及药物
        if any(kw in raw_data.ticket for kw in ['药', '治疗', '吃', '服用']):
            score += self.WEIGHTS["medication_related"]

        # 5. 是否有症状描述
        if any(kw in raw_data.ticket for kw in ['痛', '难受', '不舒服', '症状']):
            score += self.WEIGHTS["symptom_description"]

        # 6. 是否有情绪关键词
        if any(kw in raw_data.ticket for kw in self.EMOTIONAL_KEYWORDS):
            score += self.WEIGHTS["emotional_keywords"]

        # 7. 是否涉及慢性病
        if any(kw in raw_data.ticket for kw in self.CHRONIC_DISEASE_KEYWORDS):
            score += self.WEIGHTS["chronic_disease"]

        # 8. 检查known_info中的额外信息
        if len(raw_data.known_info) > 100:
            score += 0.5  # 信息量较大

        # 限制分数在0-10范围内
        return min(max(int(score), 0), 10)

    def _score_to_difficulty(self, score: int) -> str:
        """将复杂度分数转换为难度级别

        Args:
            score: 复杂度分数

        Returns:
            难度级别字符串
        """
        if score <= self.THRESHOLDS[DifficultyLevel.L1][1]:
            return DifficultyLevel.L1.value
        elif score <= self.THRESHOLDS[DifficultyLevel.L2][1]:
            return DifficultyLevel.L2.value
        else:
            return DifficultyLevel.L3.value

    def _adjust_by_distribution(self, initial_difficulty: str) -> str:
        """根据配置的分布调整难度级别

        这是一个可选的调整机制，可以确保生成的任务难度分布符合配置。
        简单实现：基于随机概率和初始难度进行微调

        Args:
            initial_difficulty: 初始难度级别

        Returns:
            调整后的难度级别
        """
        # 这里可以实现更复杂的分布调整逻辑
        # 目前简单返回初始难度
        # 实际使用时，可以维护一个计数器，跟踪已生成的难度分布

        # 示例：有10%的概率向上或向下调整一级
        # if random.random() < 0.1:
        #     if initial_difficulty == DifficultyLevel.L1.value:
        #         return DifficultyLevel.L2.value
        #     elif initial_difficulty == DifficultyLevel.L3.value:
        #         return DifficultyLevel.L2.value

        return initial_difficulty

    def get_difficulty_metadata(self, difficulty: str) -> Dict:
        """获取难度级别的元数据

        Args:
            difficulty: 难度级别字符串

        Returns:
            包含难度级别相关信息的字典
        """
        metadata = {
            "difficulty_level": difficulty,
            "version": "realistic_v3",
            "realistic_scenario": True
        }

        if difficulty == DifficultyLevel.L1.value:
            metadata.update({
                "description": "基础难度：患者配合，信息完整",
                "expected_cooperation": "good",
                "expected_behaviors": [],
                "expected_rounds": "1-2"
            })
        elif difficulty == DifficultyLevel.L2.value:
            metadata.update({
                "description": "中等难度：信息隐瞒，需要主动追问",
                "expected_cooperation": "partial",
                "expected_behaviors": ["withholding", "low_knowledge"],
                "expected_rounds": "3-5"
            })
        elif difficulty == DifficultyLevel.L3.value:
            metadata.update({
                "description": "高难度：多重问题，矛盾信息，情绪干扰",
                "expected_cooperation": "poor",
                "expected_behaviors": ["withholding", "contradicting", "emotional"],
                "expected_rounds": "4-6"
            })

        return metadata

    def classify_batch(self, raw_data_list: list, scenario_types: list) -> list:
        """批量分类难度级别

        Args:
            raw_data_list: 原始对话数据列表
            scenario_types: 场景类型列表

        Returns:
            难度级别列表
        """
        return [
            self.classify(raw_data, scenario_type)
            for raw_data, scenario_type in zip(raw_data_list, scenario_types)
        ]
