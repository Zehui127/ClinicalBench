#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Performance Evaluation Subsystem
Agent 性能评估子系统

提供 Agent 在医学任务上的性能评估功能，包括：
1. 三维度评估：临床准确性、对话流畅性、安全性与同理心
2. 综合审查：整合多个评估器的结果
3. 批量评估：支持多线程批量处理
"""

# 从核心模块导入
from DataQualityFiltering.core import (
    BaseConfig,
    BaseEvaluator,
    BaseReviewer,
    EvaluatorBasedReviewer,
    LLMEvaluator,
    create_llm_evaluator,
)

# 导入 Agent 评估的主要组件
from .pipeline import AgentEvaluationPipeline

# 评估器
from .evaluators.medical_dimensions import (
    ClinicalAccuracyEvaluator,
    DialogueFluencyEvaluator,
    SafetyEmpathyEvaluator,
)

# 审查器
from .reviewers.medical_agent_reviewer import MedicalAgentReviewer

__all__ = [
    # 核心基类
    "BaseConfig",
    "BaseEvaluator",
    "BaseReviewer",
    "EvaluatorBasedReviewer",
    "LLMEvaluator",
    "create_llm_evaluator",
    # 管道
    "AgentEvaluationPipeline",
    # 评估器
    "ClinicalAccuracyEvaluator",
    "DialogueFluencyEvaluator",
    "SafetyEmpathyEvaluator",
    # 审查器
    "MedicalAgentReviewer",
]
