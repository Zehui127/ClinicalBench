#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Dimension Evaluators
医学维度的具体评估器

实现三个评估维度：
1. 临床准确性
2. 对话流畅性
3. 安全性与同理心
"""

import logging
from typing import Dict, List, Any, Optional

# 从核心模块导入
from DataQualityFiltering.core import create_llm_evaluator

# 从本模块导入
from ..prompt_templates import PromptTemplates


class ClinicalAccuracyEvaluator:
    """
    临床准确性评估器

    评估 AI 医学助手的临床准确性，包括：
    - 医学知识准确性 (30%)
    - 诊断推理合理性 (30%)
    - 治疗建议适当性 (25%)
    - 安全警告 (15%)
    """

    def __init__(
        self,
        model: str = "gpt-4-turbo",
        cache_dir: Optional[str] = None,
        use_cache: bool = True,
    ):
        """
        初始化临床准确性评估器

        Args:
            model: LLM 模型名称
            cache_dir: 缓存目录
            use_cache: 是否使用缓存
        """
        self.logger = logging.getLogger(__name__)
        self.model = model

        try:
            self.llm = create_llm_evaluator(
                model=model,
                cache_dir=cache_dir,
                use_cache=use_cache,
            )
            self.available = True
        except Exception as e:
            self.logger.warning(f"LLM 初始化失败: {e}")
            self.llm = None
            self.available = False

        # 评分权重
        self.weights = {
            "medical_knowledge": 0.30,
            "diagnostic_reasoning": 0.30,
            "treatment_appropriateness": 0.25,
            "safety_warnings": 0.15,
        }

    def evaluate(
        self,
        patient_question: str,
        ai_response: str,
        context_info: str = "",
        reference_answer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        评估临床准确性

        Args:
            patient_question: 患者问题
            ai_response: AI 助手的回答
            context_info: 额外上下文信息
            reference_answer: 参考医生回答（可选）

        Returns:
            评估结果 {
                "overall_score": float (0-5),
                "dimension_scores": {...},
                "strengths": List[str],
                "weaknesses": List[str],
                "errors": List[str],
                "comments": str,
            }
        """
        if not self.available:
            return self._unavailable_result()

        # 格式化提示词
        prompt = PromptTemplates.format_clinical_accuracy_prompt(
            patient_question=patient_question,
            ai_response=ai_response,
            context_info=context_info,
            reference_answer=reference_answer,
        )

        # 调用 LLM
        try:
            result = self.llm.evaluate(prompt)

            # 解析结果
            parsed = result.get("parsed", {})

            # 计算加权总分
            overall_score = self._calculate_weighted_score(parsed)

            return {
                "overall_score": round(overall_score, 2),
                "dimension_scores": {
                    "medical_knowledge": parsed.get("medical_knowledge", 0),
                    "diagnostic_reasoning": parsed.get("diagnostic_reasoning", 0),
                    "treatment_appropriateness": parsed.get("treatment_appropriateness", 0),
                    "safety_warnings": parsed.get("safety_warnings", 0),
                },
                "strengths": parsed.get("strengths", []),
                "weaknesses": parsed.get("weaknesses", []),
                "errors": parsed.get("errors", []),
                "comments": parsed.get("comments", ""),
                "raw_response": result.get("response", ""),
                "model": self.model,
                "cached": result.get("cached", False),
            }

        except Exception as e:
            self.logger.error(f"评估失败: {e}")
            return {
                "overall_score": 0.0,
                "error": str(e),
                "dimension_scores": {},
                "strengths": [],
                "weaknesses": [],
                "errors": [f"评估失败: {e}"],
                "comments": "",
            }

    def _calculate_weighted_score(self, parsed: Dict) -> float:
        """计算加权总分"""
        total = 0.0
        for dimension, weight in self.weights.items():
            score = parsed.get(dimension, 0)
            total += score * weight
        return total

    def _unavailable_result(self) -> Dict:
        """返回不可用时的默认结果"""
        return {
            "overall_score": 0.0,
            "error": "LLM 服务不可用",
            "dimension_scores": {},
            "strengths": [],
            "weaknesses": ["LLM 服务不可用，无法评估"],
            "errors": ["LLM 服务不可用"],
            "comments": "请检查 API 密钥配置",
        }

    def check_availability(self) -> Dict[str, bool]:
        """检查评估器可用性"""
        if not self.llm:
            return {
                "available": False,
                "api_key_configured": False,
                "api_accessible": False,
            }

        return {
            "available": self.available,
            **self.llm.check_availability(),
        }


class DialogueFluencyEvaluator:
    """
    对话流畅性评估器

    评估 AI 医学助手的对话质量，包括：
    - 对话连贯性 (20%)
    - 问题理解准确性 (20%)
    - 回复相关性 (20%)
    - 自然语言表达 (20%)
    - 信息收集完整性 (20%)
    """

    def __init__(
        self,
        model: str = "gpt-4-turbo",
        cache_dir: Optional[str] = None,
        use_cache: bool = True,
    ):
        """初始化对话流畅性评估器"""
        self.logger = logging.getLogger(__name__)
        self.model = model

        try:
            self.llm = create_llm_evaluator(
                model=model,
                cache_dir=cache_dir,
                use_cache=use_cache,
            )
            self.available = True
        except Exception as e:
            self.logger.warning(f"LLM 初始化失败: {e}")
            self.llm = None
            self.available = False

        # 评分权重
        self.weights = {
            "coherence": 0.20,
            "question_understanding": 0.20,
            "response_relevance": 0.20,
            "natural_expression": 0.20,
            "information_gathering": 0.20,
        }

    def evaluate(
        self,
        patient_question: str,
        ai_response: str,
        context_info: str = "",
        reference_answer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """评估对话流畅性"""
        if not self.available:
            return self._unavailable_result()

        # 格式化提示词
        prompt = PromptTemplates.format_dialogue_fluency_prompt(
            patient_question=patient_question,
            ai_response=ai_response,
            context_info=context_info,
            reference_answer=reference_answer,
        )

        # 调用 LLM
        try:
            result = self.llm.evaluate(prompt)
            parsed = result.get("parsed", {})

            # 计算加权总分
            overall_score = self._calculate_weighted_score(parsed)

            return {
                "overall_score": round(overall_score, 2),
                "dimension_scores": {
                    "coherence": parsed.get("coherence", 0),
                    "question_understanding": parsed.get("question_understanding", 0),
                    "response_relevance": parsed.get("response_relevance", 0),
                    "natural_expression": parsed.get("natural_expression", 0),
                    "information_gathering": parsed.get("information_gathering", 0),
                },
                "strengths": parsed.get("strengths", []),
                "weaknesses": parsed.get("weaknesses", []),
                "suggestions": parsed.get("suggestions", []),
                "comments": parsed.get("comments", ""),
                "raw_response": result.get("response", ""),
                "model": self.model,
                "cached": result.get("cached", False),
            }

        except Exception as e:
            self.logger.error(f"评估失败: {e}")
            return {
                "overall_score": 0.0,
                "error": str(e),
                "dimension_scores": {},
                "strengths": [],
                "weaknesses": [],
                "suggestions": [],
                "comments": f"评估失败: {e}",
            }

    def _calculate_weighted_score(self, parsed: Dict) -> float:
        """计算加权总分"""
        total = 0.0
        for dimension, weight in self.weights.items():
            score = parsed.get(dimension, 0)
            total += score * weight
        return total

    def _unavailable_result(self) -> Dict:
        """返回不可用时的默认结果"""
        return {
            "overall_score": 0.0,
            "error": "LLM 服务不可用",
            "dimension_scores": {},
            "strengths": [],
            "weaknesses": ["LLM 服务不可用，无法评估"],
            "suggestions": [],
            "comments": "请检查 API 密钥配置",
        }

    def check_availability(self) -> Dict[str, bool]:
        """检查评估器可用性"""
        if not self.llm:
            return {
                "available": False,
                "api_key_configured": False,
                "api_accessible": False,
            }

        return {
            "available": self.available,
            **self.llm.check_availability(),
        }


class SafetyEmpathyEvaluator:
    """
    安全性与同理心评估器

    评估 AI 医学助手的安全性和同理心，包括：
    - 安全警告提供 (20%)
    - 同理心表达 (20%)
    - 专业语气 (20%)
    - 紧急情况识别 (20%)
    - 转诊建议 (20%)
    """

    def __init__(
        self,
        model: str = "gpt-4-turbo",
        cache_dir: Optional[str] = None,
        use_cache: bool = True,
    ):
        """初始化安全性与同理心评估器"""
        self.logger = logging.getLogger(__name__)
        self.model = model

        try:
            self.llm = create_llm_evaluator(
                model=model,
                cache_dir=cache_dir,
                use_cache=use_cache,
            )
            self.available = True
        except Exception as e:
            self.logger.warning(f"LLM 初始化失败: {e}")
            self.llm = None
            self.available = False

        # 评分权重
        self.weights = {
            "safety_warnings": 0.20,
            "empathy": 0.20,
            "professional_tone": 0.20,
            "emergency_recognition": 0.20,
            "referral_suggestions": 0.20,
        }

    def evaluate(
        self,
        patient_question: str,
        ai_response: str,
        context_info: str = "",
        reference_answer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """评估安全性与同理心"""
        if not self.available:
            return self._unavailable_result()

        # 格式化提示词
        prompt = PromptTemplates.format_safety_empathy_prompt(
            patient_question=patient_question,
            ai_response=ai_response,
            context_info=context_info,
            reference_answer=reference_answer,
        )

        # 调用 LLM
        try:
            result = self.llm.evaluate(prompt)
            parsed = result.get("parsed", {})

            # 计算加权总分
            overall_score = self._calculate_weighted_score(parsed)

            return {
                "overall_score": round(overall_score, 2),
                "dimension_scores": {
                    "safety_warnings": parsed.get("safety_warnings", 0),
                    "empathy": parsed.get("empathy", 0),
                    "professional_tone": parsed.get("professional_tone", 0),
                    "emergency_recognition": parsed.get("emergency_recognition", 0),
                    "referral_suggestions": parsed.get("referral_suggestions", 0),
                },
                "strengths": parsed.get("strengths", []),
                "weaknesses": parsed.get("weaknesses", []),
                "ethical_concerns": parsed.get("ethical_concerns", []),
                "suggestions": parsed.get("suggestions", []),
                "comments": parsed.get("comments", ""),
                "raw_response": result.get("response", ""),
                "model": self.model,
                "cached": result.get("cached", False),
            }

        except Exception as e:
            self.logger.error(f"评估失败: {e}")
            return {
                "overall_score": 0.0,
                "error": str(e),
                "dimension_scores": {},
                "strengths": [],
                "weaknesses": [],
                "ethical_concerns": [],
                "suggestions": [],
                "comments": f"评估失败: {e}",
            }

    def _calculate_weighted_score(self, parsed: Dict) -> float:
        """计算加权总分"""
        total = 0.0
        for dimension, weight in self.weights.items():
            score = parsed.get(dimension, 0)
            total += score * weight
        return total

    def _unavailable_result(self) -> Dict:
        """返回不可用时的默认结果"""
        return {
            "overall_score": 0.0,
            "error": "LLM 服务不可用",
            "dimension_scores": {},
            "strengths": [],
            "weaknesses": [],
            "ethical_concerns": [],
            "suggestions": [],
            "comments": "请检查 API 密钥配置",
        }

    def check_availability(self) -> Dict[str, bool]:
        """检查评估器可用性"""
        if not self.llm:
            return {
                "available": False,
                "api_key_configured": False,
                "api_accessible": False,
            }

        return {
            "available": self.available,
            **self.llm.check_availability(),
        }


# 导出
__all__ = [
    "ClinicalAccuracyEvaluator",
    "DialogueFluencyEvaluator",
    "SafetyEmpathyEvaluator",
]
