#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complexity Enhancer Module
复杂性增强模块 - 设计复杂的对话流，包含打断、情绪变化和嵌套问题

功能：
1. 情绪转换设计
2. 话题打断设计
3. 嵌套式问题结构
"""

import json
import random
from typing import Dict, List, Any, Optional
from pathlib import Path


class ComplexityEnhancer:
    """
    复杂性增强器

    为任务添加：
    1. 情绪转换
    2. 话题打断
    3. 嵌套式问题
    """

    # 情绪转换设计
    EMOTION_TRANSITIONS = {
        "calm_to_resistant": {
            "trigger": "医生建议长期服药或改变生活方式",
            "emotion_change": "平静 → 抗拒/焦虑",
            "patient_responses": [
                "为什么要长期吃？能不能先自己运动试试？",
                "我听邻居说这药伤肾，能不能不吃？",
                "有没有别的办法？我不想终身服药"
            ],
            "expected_doctor_response": "耐心解释、提供依据、强调重要性"
        },
        "anxious_to_calm": {
            "trigger": "医生解释病情和治疗方案",
            "emotion_change": "焦虑 → 平静",
            "patient_responses": [
                "原来是这样，那我听您的",
                "只要能治好，我都配合",
                "明白了，那我按照您说的做"
            ],
            "expected_doctor_response": "清晰解释、给予安慰、建立信任"
        },
        "cooperative_to_skeptical": {
            "trigger": "医生建议进一步检查或转诊",
            "emotion_change": "配合 → 怀疑",
            "patient_responses": [
                "真的需要吗？会不会过度检查？",
                "能不能先开点药试试？",
                "我去了好多医院都没查出问题"
            ],
            "expected_doctor_response": "解释必要性、消除顾虑、提供选择"
        },
        "worried_to_hopeful": {
            "trigger": "医生提供积极的治疗前景",
            "emotion_change": "担心 → 充满希望",
            "patient_responses": [
                "真的吗？太好了！",
                "那我一定好好配合治疗",
                "听您这么说我就放心了"
            ],
            "expected_doctor_response": "鼓励支持、制定计划、增强信心"
        }
    }

    # 话题打断场景
    INTERRUPTION_SCENARIOS = {
        "mid_explanation": {
            "doctor_action": "正在解释饮食注意事项或治疗方案",
            "patient_interrupt": [
                "那个降压药是不是特别伤肾？我邻居吃了说不行",
                "对了，我这个能吃中药吗？",
                "我朋友说练那个气功能治好，是真的吗？"
            ],
            "expected_response": "先回答新问题，再自然回到原话题"
        },
        "topic_jump": {
            "doctor_action": "询问症状详情",
            "patient_interrupt": [
                "对了医生，我最近总是失眠，跟这个有关系吗？",
                "我能不能顺便问问我老伴的病？",
                "对了，我这个病会不会遗传给小孩？"
            ],
            "expected_response": "记录问题，简要回答后继续或稍后处理"
        },
        "sudden_concern": {
            "doctor_action": "正在检查或询问病史",
            "patient_interrupt": [
                "医生，我会不会变成尿毒症啊？",
                "我这个是不是要终身服药了？",
                "我是不是再也不能正常工作了？"
            ],
            "expected_response": "优先处理焦虑，安抚后继续"
        }
    }

    # 嵌套式问题设计
    NESTED_QUESTION_DESIGN = {
        "medication_concerns": {
            "primary_concern": "某种药物能否使用",
            "secondary_concerns": [
                "能不能停西药只吃中药？",
                "能不能通过食疗代替吃药？",
                "这个药会不会有依赖性？"
            ],
            "evaluation_focus": ["优先级判断", "逐个解答", "安全提示", "澄清误解"]
        },
        "lifestyle_concerns": {
            "primary_concern": "生活方式调整建议",
            "secondary_concerns": [
                "能不能完全不运动只靠药物？",
                "是不是所有好吃的都不能吃了？",
                "戒酒戒烟太难了，能不能少一点？"
            ],
            "evaluation_focus": ["现实性考虑", "循序渐进", "替代方案", "坚持策略"]
        },
        "prognosis_concerns": {
            "primary_concern": "疾病预后和并发症",
            "secondary_concerns": [
                "这个病会不会遗传给孩子？",
                "会不会影响我的工作能力？",
                "会不会影响寿命？"
            ],
            "evaluation_focus": ["科学依据", "个体化评估", "积极态度", "管理策略"]
        }
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化复杂性增强器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.probability_add_emotion_change = self.config.get("add_emotion_change", 0.35)
        self.probability_add_interruption = self.config.get("add_interruption", 0.20)
        self.probability_add_nested_questions = self.config.get("add_nested_questions", 0.40)

    def add_emotion_transition(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加情绪转换

        Args:
            task: 原始任务

        Returns:
            添加了情绪转换的任务
        """
        improved = task.copy()

        # 随机选择情绪转换类型
        transition_type = random.choice(list(self.EMOTION_TRANSITIONS.keys()))
        transition = self.EMOTION_TRANSITIONS[transition_type]

        # 在多轮设计中添加情绪转换
        if "multi_turn_design" not in improved:
            improved["multi_turn_design"] = {"rounds": []}

        # 添加情绪转换信息
        if "emotion_transitions" not in improved:
            improved["emotion_transitions"] = []

        improved["emotion_transitions"].append({
            "type": transition_type,
            "trigger": transition["trigger"],
            "emotion_change": transition["emotion_change"],
            "patient_response": random.choice(transition["patient_responses"]),
            "expected_doctor_response": transition["expected_doctor_response"]
        })

        # 添加复杂性标记
        if "complexity_features" not in improved:
            improved["complexity_features"] = {}
        improved["complexity_features"]["has_emotion_transition"] = True

        return improved

    def add_interruption(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加话题打断

        Args:
            task: 原始任务

        Returns:
            添加了话题打断的任务
        """
        improved = task.copy()

        # 随机选择打断场景
        interruption_type = random.choice(list(self.INTERRUPTION_SCENARIOS.keys()))
        interruption = self.INTERRUPTION_SCENARIOS[interruption_type]

        # 添加打断信息
        if "interruptions" not in improved:
            improved["interruptions"] = []

        improved["interruptions"].append({
            "type": interruption_type,
            "doctor_action": interruption["doctor_action"],
            "patient_interrupt": random.choice(interruption["patient_interrupt"]),
            "expected_response": interruption["expected_response"]
        })

        # 在多轮设计中添加打断轮次
        if "multi_turn_design" not in improved:
            improved["multi_turn_design"] = {"rounds": []}

        # 添加复杂性标记
        if "complexity_features" not in improved:
            improved["complexity_features"] = {}
        improved["complexity_features"]["has_interruption"] = True

        return improved

    def add_nested_questions(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加嵌套式问题

        Args:
            task: 原始任务

        Returns:
            添加了嵌套式问题的任务
        """
        improved = task.copy()

        # 随机选择嵌套问题类型
        nested_type = random.choice(list(self.NESTED_QUESTION_DESIGN.keys()))
        nested = self.NESTED_QUESTION_DESIGN[nested_type]

        # 添加嵌套问题信息
        if "nested_questions" not in improved:
            improved["nested_questions"] = []

        # 随机选择 2-3 个次要问题
        num_secondary = random.randint(2, 3)
        selected_secondary = random.sample(nested["secondary_concerns"], num_secondary)

        improved["nested_questions"].append({
            "primary_concern": nested["primary_concern"],
            "secondary_concerns": selected_secondary,
            "evaluation_focus": nested["evaluation_focus"]
        })

        # 添加复杂性标记
        if "complexity_features" not in improved:
            improved["complexity_features"] = {}
        improved["complexity_features"]["nested_question_count"] = len(selected_secondary)

        return improved

    def add_complexity(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加复杂性（组合多种增强）

        Args:
            task: 原始任务

        Returns:
            添加了复杂性的任务
        """
        improved = task.copy()

        # 随机决定添加哪些复杂性
        if random.random() < self.probability_add_emotion_change:
            improved = self.add_emotion_transition(improved)

        if random.random() < self.probability_add_interruption:
            improved = self.add_interruption(improved)

        if random.random() < self.probability_add_nested_questions:
            improved = self.add_nested_questions(improved)

        return improved
