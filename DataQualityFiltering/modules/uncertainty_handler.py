#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uncertainty Handler Module
不确定性处理模块 - 为任务添加信息缺失、模糊性和矛盾信息

功能：
1. 添加模糊信息
2. 添加矛盾信息（15-20%任务）
3. 添加干扰信息
"""

import json
import random
from typing import Dict, List, Any, Optional
from pathlib import Path


class UncertaintyHandler:
    """
    不确定性处理器

    为任务添加：
    1. 模糊信息（信息缺失）
    2. 矛盾信息（在少数任务中）
    3. 干扰信息（无关症状、生活压力等）
    """

    # 模糊信息模板
    FUZZY_KNOWN_INFO_TEMPLATES = {
        "medication_uncertain": [
            "医生开了什么降压药，但我记不清名字了",
            "社区医生好像说我血压高，没当回事",
            "之前吃过一些药，但忘了什么时候停的",
            "好像是白色的药片？具体名字想不起来了",
            "药瓶子上写着什么片，我给忘了"
        ],
        "symptom_vague": [
            "最近感觉不太舒服，说不上哪里不对",
            "就是有点难受，可能也没什么大事",
            "断断续续的，有时候有有时候没有",
            "好像没什么特别的，就是不舒服",
            "说不上来，反正就是不精神"
        ],
        "duration_unclear": [
            "有一阵子了",
            "好像是从去年开始的？",
            "具体时间记不清楚了",
            "挺长时间了，记不得什么时候开始的",
            "好像有几个月了吧"
        ],
        "frequency_unclear": [
            "经常吧，具体次数没数过",
            "时不时的就会发作",
            "没什么规律，有时候有有时候没有",
            "好像一周好几次？不太确定"
        ]
    }

    # 矛盾信息模式（15-20%任务）
    CONTRADICTION_PATTERNS = {
        "diet_contradiction": {
            "round_1": "我平时很注意饮食，很少吃甜食",
            "round_2": "每天下午习惯喝两瓶可乐",
            "contradiction_type": "饮食矛盾"
        },
        "medication_contradiction": {
            "round_1": "我一直按时吃药",
            "round_2": "有时候忙起来就忘了吃",
            "contradiction_type": "用药依从性矛盾"
        },
        "symptom_contradiction": {
            "round_1": "没什么不舒服的",
            "round_2": "就是有时候会觉得胸闷",
            "contradiction_type": "症状描述矛盾"
        },
        "lifestyle_contradiction": {
            "round_1": "我每天都坚持运动",
            "round_2": "最近半年因为工作忙，基本没动过",
            "contradiction_type": "生活方式矛盾"
        },
        "family_history_contradiction": {
            "round_1": "家里没人有这个病",
            "round_2": "我想起来我爸好像也有高血压",
            "contradiction_type": "家族史矛盾"
        }
    }

    # 干扰信息模板
    DISTRACTION_TEMPLATES = {
        "unrelated_symptoms": [
            "对了，我最近腿也有点疼，不知道是不是风湿",
            "我眼睛也有点花，是不是老花眼？",
            "最近老是腰酸，是不是肾不好？",
            "我胃口也不太好，是不是胃炎？",
            "最近总是忘事，是不是老年痴呆？"
        ],
        "life_stressors": [
            "最近家里事情特别多，压力大",
            "孙子刚出生，照顾小孩累得不行",
            "儿子要结婚，准备婚礼忙得很",
            "老伴最近身体也不好，我得照顾她",
            "最近失眠，睡不好觉"
        ],
        "internet_research": [
            "我在网上查说这个病要终身服药，是真的吗？",
            "朋友圈有人说这个药伤肾，我不敢吃了",
            "我看抖音上说喝这个茶能降血压，能代替药吗？",
            "邻居说吃那个保健品特别好，我也想试试",
            "网上说练气功能治这个病，是真的吗？"
        ],
        "family_concerns": [
            "我儿子特别担心，非要我来看病",
            "老伴让我问问能不能吃那个中药",
            "女儿在网上查了一堆东西，非让我问",
            "家里人都不让我吃这个药"
        ]
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化不确定性处理器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.probability_add_contradiction = self.config.get("add_contradiction", 0.15)
        self.probability_add_distraction = self.config.get("add_distraction", 0.25)

    def add_uncertainty(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        为任务添加不确定性（模糊信息）

        Args:
            task: 原始任务

        Returns:
            添加了模糊信息的任务
        """
        improved = task.copy()
        instructions = improved.get("user_scenario", {}).get("instructions", {})
        known_info = instructions.get("known_info", "")

        # 随机选择模糊类型
        uncertainty_type = random.choice(list(self.FUZZY_KNOWN_INFO_TEMPLATES.keys()))
        fuzzy_templates = self.FUZZY_KNOWN_INFO_TEMPLATES[uncertainty_type]
        fuzzy_info = random.choice(fuzzy_templates)

        # 在 known_info 中添加模糊信息
        if random.random() < 0.5:
            # 在开头添加
            new_known_info = f"{fuzzy_info}。{known_info}"
        else:
            # 在结尾添加
            new_known_info = f"{known_info}。{fuzzy_info}"

        # 更新任务
        if "user_scenario" not in improved:
            improved["user_scenario"] = {}
        if "instructions" not in improved["user_scenario"]:
            improved["user_scenario"]["instructions"] = {}

        improved["user_scenario"]["instructions"]["known_info"] = new_known_info
        improved["user_scenario"]["instructions"]["original_known_info"] = known_info

        # 添加不确定性标记
        if "uncertainty_markers" not in improved:
            improved["uncertainty_markers"] = {}
        improved["uncertainty_markers"]["has_vague_info"] = True
        improved["uncertainty_markers"]["uncertainty_type"] = uncertainty_type

        return improved

    def add_contradiction(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        为任务添加矛盾信息（15-20%任务）

        Args:
            task: 原始任务

        Returns:
            添加了矛盾信息的任务
        """
        improved = task.copy()

        # 随机选择矛盾类型
        contradiction_type = random.choice(list(self.CONTRADICTION_PATTERNS.keys()))
        contradiction = self.CONTRADICTION_PATTERNS[contradiction_type]

        # 添加多轮矛盾信息
        if "multi_turn_design" not in improved:
            improved["multi_turn_design"] = {"rounds": []}

        # 在不同轮次添加矛盾信息
        if "contradiction_info" not in improved:
            improved["contradiction_info"] = {
                "type": contradiction["contradiction_type"],
                "round_1_statement": contradiction["round_1"],
                "round_2_statement": contradiction["round_2"]
            }

        # 添加不确定性标记
        if "uncertainty_markers" not in improved:
            improved["uncertainty_markers"] = {}
        improved["uncertainty_markers"]["has_contradiction"] = True
        improved["uncertainty_markers"]["contradiction_type"] = contradiction["contradiction_type"]

        return improved

    def add_distraction(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        为任务添加干扰信息

        Args:
            task: 原始任务

        Returns:
            添加了干扰信息的任务
        """
        improved = task.copy()
        instructions = improved.get("user_scenario", {}).get("instructions", {})
        known_info = instructions.get("known_info", "")

        # 随机选择干扰类型
        distraction_type = random.choice(list(self.DISTRACTION_TEMPLATES.keys()))
        distraction_templates = self.DISTRACTION_TEMPLATES[distraction_type]
        distraction_info = random.choice(distraction_templates)

        # 在 known_info 中添加干扰信息
        new_known_info = f"{known_info}。{distraction_info}"

        # 更新任务
        if "user_scenario" not in improved:
            improved["user_scenario"] = {}
        if "instructions" not in improved["user_scenario"]:
            improved["user_scenario"]["instructions"] = {}

        improved["user_scenario"]["instructions"]["known_info"] = new_known_info
        improved["user_scenario"]["instructions"]["original_known_info"] = known_info

        # 添加复杂性标记
        if "complexity_features" not in improved:
            improved["complexity_features"] = {}
        improved["complexity_features"]["has_distraction"] = True
        improved["complexity_features"]["distraction_type"] = distraction_type

        return improved

    def generate_clarification_requirements(self, task: Dict[str, Any]) -> List[str]:
        """
        生成需要澄清的信息列表

        Args:
            task: 任务

        Returns:
            需要澄清的信息列表
        """
        required_clarifications = []
        uncertainty_markers = task.get("uncertainty_markers", {})

        if uncertainty_markers.get("has_vague_info"):
            uncertainty_type = uncertainty_markers.get("uncertainty_type", "")
            if uncertainty_type == "medication_uncertain":
                required_clarifications.append("药物名称和用法")
            elif uncertainty_type == "symptom_vague":
                required_clarifications.append("具体症状描述")
            elif uncertainty_type == "duration_unclear":
                required_clarifications.append("症状持续时间")
            elif uncertainty_type == "frequency_unclear":
                required_clarifications.append("发作频率")

        if uncertainty_markers.get("has_contradiction"):
            required_clarifications.append("矛盾信息澄清")

        return required_clarifications
