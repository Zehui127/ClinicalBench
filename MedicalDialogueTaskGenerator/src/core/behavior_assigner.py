"""
患者行为分配器
Medical Dialogue Task Generator - Behavior Assigner

This module assigns patient behaviors based on difficulty level.
"""

import random
from typing import Dict, List, Optional, Any

from ..models.data_models import (
    DifficultyLevel,
    RawDialogueData,
    PatientBehavior,
    BehaviorType,
    EmotionalState
)


class BehaviorAssigner:
    """患者行为分配器"""

    # 可隐瞒的信息类型
    WITHHOLDING_ITEMS = [
        "current_medications",
        "allergies",
        "duration",
        "severity",
        "past_medical_history",
        "family_history"
    ]

    # 知识缺口类型
    KNOWLEDGE_GAPS = [
        "网络搜索误解",
        "听信偏方",
        "对疾病机制误解",
        "对治疗目的不理解"
    ]

    # 记忆问题类型
    MEMORY_ISSUES = [
        "记不住时间",
        "混淆检查结果",
        "忘记药物名称"
    ]

    # 情绪状态配置
    EMOTIONAL_STATES = {
        "anxious": {
            "name": "焦虑",
            "triggers": ["新发症状", "检查等待", "担心严重疾病"],
            "statements": ["我很担心", "会不会严重", "这要紧吗"]
        },
        "fearful": {
            "name": "恐惧",
            "triggers": ["以往就医创伤", "亲人因病去世", "误诊经历"],
            "statements": ["我邻居就是...", "我怕检查出来..."]
        },
        "angry": {
            "name": "愤怒",
            "triggers": ["以往误诊经历", "对医疗系统不信任"],
            "statements": ["你们都是...", "上次医生说..."]
        },
        "panicked": {
            "name": "恐慌",
            "triggers": ["急性症状", "严重不适"],
            "statements": ["救命啊", "我快不行了"]
        }
    }

    # 矛盾类型
    CONTRADICTION_TYPES = [
        {
            "type": "patient_vs_record",
            "example": "患者陈述与系统记录矛盾"
        },
        {
            "type": "timeline_inconsistency",
            "example": "时间线前后不一致"
        },
        {
            "type": "statement_contradiction",
            "example": "前后陈述互相矛盾"
        }
    ]

    def __init__(self, config: Optional[Dict] = None):
        """初始化行为分配器

        Args:
            config: 可选的配置字典
        """
        self.config = config or {}
        self.random_seed = self.config.get("random_seed", None)
        if self.random_seed is not None:
            random.seed(self.random_seed)

    def assign(self, difficulty: str, raw_data: RawDialogueData) -> PatientBehavior:
        """分配患者行为

        Args:
            difficulty: 难度级别
            raw_data: 原始对话数据

        Returns:
            患者行为对象
        """
        if difficulty == DifficultyLevel.L1.value:
            return self._assign_l1_behavior()
        elif difficulty == DifficultyLevel.L2.value:
            return self._assign_l2_behavior(raw_data)
        else:  # L3
            return self._assign_l3_behavior(raw_data)

    def _assign_l1_behavior(self) -> PatientBehavior:
        """L1行为：完全配合

        Returns:
            患者行为对象
        """
        return PatientBehavior(
            cooperation="good",
            behaviors=[],
            information_quality="good"
        )

    def _assign_l2_behavior(self, raw_data: RawDialogueData) -> PatientBehavior:
        """L2行为：部分配合，信息隐瞒

        Args:
            raw_data: 原始对话数据

        Returns:
            患者行为对象
        """
        behaviors = []

        # 必须有withholding
        behaviors.append(BehaviorType.WITHHOLDING.value)

        # 随机添加low_knowledge
        if random.random() > 0.3:
            behaviors.append(BehaviorType.LOW_KNOWLEDGE.value)

        # 选择要隐瞒的信息（2-3个）
        withholding_count = random.randint(2, 3)
        withholding_items = random.sample(self.WITHHOLDING_ITEMS, withholding_count)

        # 如果有low_knowledge，选择知识缺口
        knowledge_gaps = None
        if BehaviorType.LOW_KNOWLEDGE.value in behaviors:
            knowledge_gaps = random.sample(self.KNOWLEDGE_GAPS, random.randint(1, 2))

        return PatientBehavior(
            cooperation="partial",
            behaviors=behaviors,
            information_quality="medium",
            withholding=withholding_items,
            knowledge_gaps=knowledge_gaps
        )

    def _assign_l3_behavior(self, raw_data: RawDialogueData) -> PatientBehavior:
        """L3行为：不配合，多种问题

        Args:
            raw_data: 原始对话数据

        Returns:
            患者行为对象
        """
        behaviors = [
            BehaviorType.WITHHOLDING.value,
            BehaviorType.CONTRADICTING.value,
            BehaviorType.EMOTIONAL.value
        ]

        # 随机添加其他行为
        if random.random() > 0.5:
            behaviors.append(BehaviorType.LYING.value)
        if random.random() > 0.5:
            behaviors.append(BehaviorType.POOR_MEMORY.value)
        if random.random() > 0.3:
            behaviors.append(BehaviorType.LOW_KNOWLEDGE.value)

        # 选择要隐瞒的信息（3-4个）
        withholding_count = random.randint(3, 4)
        withholding_items = random.sample(self.WITHHOLDING_ITEMS, withholding_count)

        # 配置矛盾类型（1-2个）
        contradiction_count = random.randint(1, 2)
        contradictions = random.sample(self.CONTRADICTION_TYPES, contradiction_count)

        # 选择情绪状态
        emotional_state = self._select_emotional_state(raw_data)

        # 配置知识缺口（如果有low_knowledge）
        knowledge_gaps = None
        if BehaviorType.LOW_KNOWLEDGE.value in behaviors:
            knowledge_gaps = random.sample(self.KNOWLEDGE_GAPS, random.randint(1, 2))

        # 配置记忆问题（如果有poor_memory）
        memory_issues = None
        if BehaviorType.POOR_MEMORY.value in behaviors:
            memory_issues = random.sample(self.MEMORY_ISSUES, random.randint(1, 2))

        return PatientBehavior(
            cooperation="poor",
            behaviors=behaviors,
            information_quality="poor",
            withholding=withholding_items,
            contradictions=contradictions,
            emotional_state=emotional_state,
            knowledge_gaps=knowledge_gaps,
            memory_issues=memory_issues
        )

    def _select_emotional_state(self, raw_data: RawDialogueData) -> Dict[str, Any]:
        """选择情绪状态

        Args:
            raw_data: 原始对话数据

        Returns:
            情绪状态字典
        """
        # 分析文本中的情绪关键词
        ticket = raw_data.ticket.lower()

        # 根据关键词选择情绪
        if any(kw in ticket for kw in ["担心", "焦虑", "害怕"]):
            emotion_type = "anxious"
        elif any(kw in ticket for kw in ["痛苦", "恐惧", "邻居"]):
            emotion_type = "fearful"
        elif any(kw in ticket for kw in ["生气", "愤怒", "不信任"]):
            emotion_type = "angry"
        elif any(kw in ticket for kw in ["救命", "受不了", "快不行"]):
            emotion_type = "panicked"
        else:
            # 随机选择
            emotion_type = random.choice(list(self.EMOTIONAL_STATES.keys()))

        emotion_config = self.EMOTIONAL_STATES[emotion_type]

        # 确定强度
        intensity = "medium" if random.random() > 0.5 else "high"

        return {
            "type": emotion_type,
            "intensity": intensity,
            "triggers": random.choice(emotion_config["triggers"])
        }

    def generate_system_records(self, difficulty: str, patient_behavior: PatientBehavior) -> Optional[Dict]:
        """生成系统记录

        Args:
            difficulty: 难度级别
            patient_behavior: 患者行为

        Returns:
            系统记录字典或None
        """
        if difficulty == DifficultyLevel.L1.value:
            return None

        # L2和L3需要系统记录
        records = {}

        # 如果有withholding行为，添加用药记录
        if hasattr(patient_behavior, "withholding") and patient_behavior.withholding:
            if "current_medications" in patient_behavior.withholding:
                records["medications"] = [
                    {
                        "name": "阿司匹林",
                        "dose": "100mg",
                        "frequency": "qd",
                        "start_date": "2024-01-15"
                    }
                ]

            if "allergies" in patient_behavior.withholding:
                records["allergies"] = ["青霉素"]

        return records if records else None

    def generate_conversation_flow(self, difficulty: str, patient_behavior: PatientBehavior) -> Optional[Dict]:
        """生成对话流程配置

        Args:
            difficulty: 难度级别
            patient_behavior: 患者行为

        Returns:
            对话流程字典或None
        """
        if difficulty == DifficultyLevel.L1.value:
            return None

        # L2和L3需要对话流程配置
        if difficulty == DifficultyLevel.L2.value:
            expected_rounds = "3-5"
            rounds_until_truth = 3
        else:  # L3
            expected_rounds = "4-6"
            rounds_until_truth = random.randint(4, 6)

        return {
            "expected_rounds": expected_rounds,
            "unfolding_pattern": "progressive_disclosure",
            "progressive_disclosure": {
                "description": "信息逐渐揭露，Agent需要主动追问",
                "rounds_until_truth": rounds_until_truth
            }
        }

    def assign_batch(self, difficulty_list: List[str], raw_data_list: List[RawDialogueData]) -> List[PatientBehavior]:
        """批量分配患者行为

        Args:
            difficulty_list: 难度级别列表
            raw_data_list: 原始对话数据列表

        Returns:
            患者行为列表
        """
        return [
            self.assign(difficulty, raw_data)
            for difficulty, raw_data in zip(difficulty_list, raw_data_list)
        ]
