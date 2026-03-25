"""
场景类型检测器
Medical Dialogue Task Generator - Scenario Detector

This module detects the scenario type from patient queries.
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum

from ..models.data_models import ScenarioType, RawDialogueData


class ScenarioDetector:
    """场景类型检测器"""

    # 场景类型关键词映射
    SCENARIO_KEYWORDS = {
        ScenarioType.INFORMATION_QUERY: [
            r"能不能", r"能不能", r"可以吗", r"可以.*吗", r"可以不可以",
            r"要不要", r"需要.*吗", r"如何", r"怎么", r"怎样",
            r"是不是", r"是否"
        ],
        ScenarioType.SYMPTOM_ANALYSIS: [
            r"原因", r"怎么回事", r"为什么", r"怎么会",
            r"是什么.*引起的", r"由于", r"因为"
        ],
        ScenarioType.CHRONIC_MANAGEMENT: [
            r"治疗", r"控制", r"管理", r"怎么治",
            r"如何治疗", r"怎么控制", r"长期", r"平时"
        ],
        ScenarioType.MEDICATION_CONSULTATION: [
            r"药", r"药物", r"吃药", r"服用",
            r"副作用", r"剂量", r"用法", r"相互作用",
            r"停药", r"换药"
        ],
        ScenarioType.LIFESTYLE_ADVICE: [
            r"饮食", r"吃.*什么", r"食物", r"营养",
            r"运动", r"锻炼", r"活动", r"生活方式",
            r"生活习惯", r"注意.*什么", r"禁忌"
        ],
        ScenarioType.EMERGENCY_CONCERN: [
            r"严重", r"危险", r"救命", r"急诊",
            r"受不了", r"撑不住", r"快要.*了",
            r"很.*痛", r"剧烈", r"突然"
        ],
        ScenarioType.FOLLOW_UP: [
            r"复查", r"随访", r"复诊", r"检查结果"
        ],
        ScenarioType.SECOND_OPINION: [
            r"第二意见", r"别的医生", r"其他医院"
        ]
    }

    # 场景类型中文名称映射
    SCENARIO_NAMES = {
        ScenarioType.INFORMATION_QUERY: "信息查询",
        ScenarioType.SYMPTOM_ANALYSIS: "症状分析",
        ScenarioType.CHRONIC_MANAGEMENT: "慢性病管理",
        ScenarioType.MEDICATION_CONSULTATION: "药物咨询",
        ScenarioType.LIFESTYLE_ADVICE: "生活方式建议",
        ScenarioType.EMERGENCY_CONCERN: "紧急关注",
        ScenarioType.FOLLOW_UP: "随访咨询",
        ScenarioType.SECOND_OPINION: "第二意见"
    }

    def __init__(self, config: Optional[Dict] = None):
        """初始化场景检测器

        Args:
            config: 可选的配置字典
        """
        self.config = config or {}
        self._compile_patterns()

    def _compile_patterns(self):
        """编译正则表达式模式"""
        self.compiled_patterns = {}
        for scenario_type, keywords in self.SCENARIO_KEYWORDS.items():
            self.compiled_patterns[scenario_type] = [
                re.compile(pattern) for pattern in keywords
            ]

    def detect(self, raw_data: RawDialogueData) -> str:
        """检测场景类型

        Args:
            raw_data: 原始对话数据

        Returns:
            场景类型字符串
        """
        ticket = raw_data.ticket.lower()
        known_info = raw_data.known_info.lower()

        # 合并主诉和已知信息进行检测
        text = f"{ticket} {known_info}"

        # 检测每种场景类型的关键词
        scores = {}
        for scenario_type, patterns in self.compiled_patterns.items():
            score = 0
            for pattern in patterns:
                matches = pattern.findall(text)
                score += len(matches)
            if score > 0:
                scores[scenario_type] = score

        # 如果有匹配结果，返回得分最高的场景类型
        if scores:
            best_scenario = max(scores.items(), key=lambda x: x[1])[0]
            return best_scenario.value

        # 默认返回信息查询
        return ScenarioType.INFORMATION_QUERY.value

    def detect_with_confidence(self, raw_data: RawDialogueData) -> Tuple[str, int]:
        """检测场景类型并返回置信度

        Args:
            raw_data: 原始对话数据

        Returns:
            (场景类型, 置信度) 置信度范围0-3
        """
        ticket = raw_data.ticket.lower()
        known_info = raw_data.known_info.lower()
        text = f"{ticket} {known_info}"

        # 检测每种场景类型的关键词
        scores = {}
        for scenario_type, patterns in self.compiled_patterns.items():
            score = 0
            for pattern in patterns:
                matches = pattern.findall(text)
                score += len(matches)
            if score > 0:
                scores[scenario_type] = score

        if not scores:
            return (ScenarioType.INFORMATION_QUERY.value, 0)

        # 获取最高分
        best_scenario, best_score = max(scores.items(), key=lambda x: x[1])

        # 计算置信度（0-3）
        confidence = min(3, best_score)

        return (best_scenario.value, confidence)

    def get_scenario_name(self, scenario_type: str) -> str:
        """获取场景类型的中文名称

        Args:
            scenario_type: 场景类型字符串

        Returns:
            场景类型中文名称
        """
        try:
            enum_type = ScenarioType(scenario_type)
            return self.SCENARIO_NAMES.get(enum_type, "未知场景")
        except ValueError:
            return "未知场景"

    def detect_multiple(self, raw_data: RawDialogueData, top_k: int = 3) -> List[Tuple[str, float]]:
        """检测多个可能的场景类型

        Args:
            raw_data: 原始对话数据
            top_k: 返回前k个最可能的场景类型

        Returns:
            [(场景类型, 得分)] 列表，按得分降序排列
        """
        ticket = raw_data.ticket.lower()
        known_info = raw_data.known_info.lower()
        text = f"{ticket} {known_info}"

        # 检测每种场景类型的关键词
        scores = {}
        for scenario_type, patterns in self.compiled_patterns.items():
            score = 0
            for pattern in patterns:
                matches = pattern.findall(text)
                score += len(matches)
            if score > 0:
                scores[scenario_type] = score

        # 按得分降序排序
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # 返回top_k个结果
        results = [(scenario_type.value, score) for scenario_type, score in sorted_scores[:top_k]]

        # 如果没有匹配结果，返回默认场景
        if not results:
            results = [(ScenarioType.INFORMATION_QUERY.value, 0.0)]

        return results
