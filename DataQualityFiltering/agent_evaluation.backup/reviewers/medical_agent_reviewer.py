#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Agent Reviewer
医学 Agent 回答质量审查器

整合三个评估维度：
1. 临床准确性 (40%)
2. 对话流畅性 (35%)
3. 安全性与同理心 (25%)
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入本模块的组件
from ..evaluators.medical_dimensions import (
    ClinicalAccuracyEvaluator,
    DialogueFluencyEvaluator,
    SafetyEmpathyEvaluator,
)


class MedicalAgentReviewer:
    """
    Medical Agent 回答质量审查器

    整合三个评估维度，提供全面的 Agent 回答质量评估。

    权重分配：
    - 临床准确性: 40%
    - 对话流畅性: 35%
    - 安全性与同理心: 25%

    通过阈值: 3.5/5.0
    """

    # 评估权重
    DIMENSION_WEIGHTS = {
        "clinical_accuracy": 0.40,
        "dialogue_fluency": 0.35,
        "safety_empathy": 0.25,
    }

    # 通过阈值
    PASS_THRESHOLD = 3.5

    def __init__(
        self,
        model: str = "gpt-4-turbo",
        cache_dir: Optional[str] = None,
        use_cache: bool = True,
        pass_threshold: float = None,
    ):
        """
        初始化 Medical Agent 审查器

        Args:
            model: LLM 模型名称（默认 gpt-4-turbo）
            cache_dir: 缓存目录
            use_cache: 是否使用缓存
            pass_threshold: 通过阈值（默认 3.5）
        """
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.pass_threshold = pass_threshold or self.PASS_THRESHOLD

        # 初始化三个评估器
        self.clinical_evaluator = ClinicalAccuracyEvaluator(
            model=model,
            cache_dir=cache_dir,
            use_cache=use_cache,
        )

        self.fluency_evaluator = DialogueFluencyEvaluator(
            model=model,
            cache_dir=cache_dir,
            use_cache=use_cache,
        )

        self.safety_evaluator = SafetyEmpathyEvaluator(
            model=model,
            cache_dir=cache_dir,
            use_cache=use_cache,
        )

        # 检查可用性
        self.available = all([
            self.clinical_evaluator.available,
            self.fluency_evaluator.available,
            self.safety_evaluator.available,
        ])

        if not self.available:
            self.logger.warning("部分或全部评估器不可用")

    def review(
        self,
        patient_question: str,
        ai_response: str,
        context_info: str = "",
        reference_answer: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        审查 Agent 回答质量

        Args:
            patient_question: 患者问题
            ai_response: AI 助手的回答
            context_info: 额外上下文信息
            reference_answer: 参考医生回答（可选）
            task_id: 任务 ID（可选）

        Returns:
            审查结果 {
                "task_id": str,
                "overall_score": float (0-5),
                "pass_status": bool,
                "dimension_scores": {
                    "clinical_accuracy": float,
                    "dialogue_fluency": float,
                    "safety_empathy": float,
                },
                "dimension_details": {...},
                "strengths": List[str],
                "weaknesses": List[str],
                "errors": List[str],
                "suggestions": List[str],
                "comments": str,
                "timestamp": str,
            }
        """
        start_time = datetime.now()

        # 1. 临床准确性评估 (40%)
        self.logger.info("评估临床准确性...")
        clinical_result = self.clinical_evaluator.evaluate(
            patient_question=patient_question,
            ai_response=ai_response,
            context_info=context_info,
            reference_answer=reference_answer,
        )

        # 2. 对话流畅性评估 (35%)
        self.logger.info("评估对话流畅性...")
        fluency_result = self.fluency_evaluator.evaluate(
            patient_question=patient_question,
            ai_response=ai_response,
            context_info=context_info,
            reference_answer=reference_answer,
        )

        # 3. 安全性与同理心评估 (25%)
        self.logger.info("评估安全性与同理心...")
        safety_result = self.safety_evaluator.evaluate(
            patient_question=patient_question,
            ai_response=ai_response,
            context_info=context_info,
            reference_answer=reference_answer,
        )

        # 4. 计算总分
        clinical_score = clinical_result.get("overall_score", 0)
        fluency_score = fluency_result.get("overall_score", 0)
        safety_score = safety_result.get("overall_score", 0)

        overall_score = (
            clinical_score * self.DIMENSION_WEIGHTS["clinical_accuracy"] +
            fluency_score * self.DIMENSION_WEIGHTS["dialogue_fluency"] +
            safety_score * self.DIMENSION_WEIGHTS["safety_empathy"]
        )

        # 5. 判断是否通过
        pass_status = overall_score >= self.pass_threshold

        # 6. 整合反馈
        all_strengths = []
        all_weaknesses = []
        all_errors = []
        all_suggestions = []

        # 从各维度收集反馈
        for result in [clinical_result, fluency_result, safety_result]:
            all_strengths.extend(result.get("strengths", []))
            all_weaknesses.extend(result.get("weaknesses", []))
            all_errors.extend(result.get("errors", []))
            all_suggestions.extend(result.get("suggestions", []))

        # 7. 生成综合评论
        comments = self._generate_comments(
            overall_score,
            clinical_score,
            fluency_score,
            safety_score,
            pass_status,
        )

        # 8. 计算耗时
        elapsed_time = (datetime.now() - start_time).total_seconds()

        return {
            "task_id": task_id or "unknown",
            "overall_score": round(overall_score, 2),
            "pass_status": pass_status,
            "pass_threshold": self.pass_threshold,
            "dimension_scores": {
                "clinical_accuracy": round(clinical_score, 2),
                "dialogue_fluency": round(fluency_score, 2),
                "safety_empathy": round(safety_score, 2),
            },
            "dimension_details": {
                "clinical_accuracy": clinical_result,
                "dialogue_fluency": fluency_result,
                "safety_empathy": safety_result,
            },
            "strengths": all_strengths,
            "weaknesses": all_weaknesses,
            "errors": all_errors,
            "suggestions": all_suggestions,
            "comments": comments,
            "model": self.model,
            "timestamp": datetime.now().isoformat(),
            "evaluation_time_seconds": round(elapsed_time, 2),
            "cached": (
                clinical_result.get("cached", False) or
                fluency_result.get("cached", False) or
                safety_result.get("cached", False)
            ),
        }

    def review_batch(
        self,
        items: List[Dict[str, Any]],
        show_progress: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        批量审查

        Args:
            items: 项目列表，每个项目包含 {
                "task_id": str,
                "patient_question": str,
                "ai_response": str,
                "context_info": str (optional),
                "reference_answer": str (optional),
            }
            show_progress: 是否显示进度

        Returns:
            审查结果列表
        """
        results = []

        for idx, item in enumerate(items, 1):
            if show_progress:
                self.logger.info(f"审查 {idx}/{len(items)}: {item.get('task_id', 'unknown')}")

            result = self.review(
                patient_question=item["patient_question"],
                ai_response=item["ai_response"],
                context_info=item.get("context_info", ""),
                reference_answer=item.get("reference_answer"),
                task_id=item.get("task_id"),
            )

            results.append(result)

        return results

    def _generate_comments(
        self,
        overall_score: float,
        clinical_score: float,
        fluency_score: float,
        safety_score: float,
        pass_status: bool,
    ) -> str:
        """生成综合评论"""
        comments = []

        # 总体评价
        if overall_score >= 4.5:
            comments.append("✅ 优秀的医学助手回答，各方面表现突出。")
        elif overall_score >= 4.0:
            comments.append("✅ 良好的医学助手回答，达到高质量标准。")
        elif overall_score >= 3.5:
            comments.append("✓ 达到基本要求，有改进空间。")
        elif overall_score >= 3.0:
            comments.append("⚠️  低于理想标准，需要明显改进。")
        elif overall_score >= 2.0:
            comments.append("❌ 存在明显问题，不建议用于实际应用。")
        else:
            comments.append("❌ 严重不达标，存在重大缺陷。")

        # 各维度评价
        comments.append(f"\n**临床准确性**: {clinical_score:.1f}/5.0")
        if clinical_score < 3.0:
            comments.append("  - 需要提升医学知识和诊断推理能力")

        comments.append(f"\n**对话流畅性**: {fluency_score:.1f}/5.0")
        if fluency_score < 3.0:
            comments.append("  - 需要改善对话连贯性和问题理解")

        comments.append(f"\n**安全性与同理心**: {safety_score:.1f}/5.0")
        if safety_score < 3.0:
            comments.append("  - 需要加强安全警告和同理心表达")

        return "\n".join(comments)

    def check_availability(self) -> Dict[str, Any]:
        """
        检查所有评估器的可用性

        Returns:
            各评估器状态 {
                "overall_available": bool,
                "clinical_accuracy": {...},
                "dialogue_fluency": {...},
                "safety_empathy": {...},
            }
        """
        return {
            "overall_available": self.available,
            "model": self.model,
            "evaluators": {
                "clinical_accuracy": self.clinical_evaluator.check_availability(),
                "dialogue_fluency": self.fluency_evaluator.check_availability(),
                "safety_empathy": self.safety_evaluator.check_availability(),
            },
        }

    def get_statistics(
        self,
        reviews: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        统计批量审查结果

        Args:
            reviews: 审查结果列表

        Returns:
            统计信息 {
                "total_reviews": int,
                "passed": int,
                "failed": int,
                "pass_rate": float,
                "average_scores": {...},
                "score_distribution": {...},
            }
        """
        if not reviews:
            return {}

        total = len(reviews)
        passed = sum(1 for r in reviews if r.get("pass_status", False))
        failed = total - passed

        # 计算平均分
        overall_scores = [r.get("overall_score", 0) for r in reviews]
        clinical_scores = [r.get("dimension_scores", {}).get("clinical_accuracy", 0) for r in reviews]
        fluency_scores = [r.get("dimension_scores", {}).get("dialogue_fluency", 0) for r in reviews]
        safety_scores = [r.get("dimension_scores", {}).get("safety_empathy", 0) for r in reviews]

        # 分数分布
        score_ranges = {
            "excellent": sum(1 for s in overall_scores if s >= 4.5),
            "good": sum(1 for s in overall_scores if 4.0 <= s < 4.5),
            "satisfactory": sum(1 for s in overall_scores if 3.5 <= s < 4.0),
            "needs_improvement": sum(1 for s in overall_scores if 3.0 <= s < 3.5),
            "poor": sum(1 for s in overall_scores if s < 3.0),
        }

        return {
            "total_reviews": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
            "average_scores": {
                "overall": round(sum(overall_scores) / total, 2) if total > 0 else 0,
                "clinical_accuracy": round(sum(clinical_scores) / total, 2) if total > 0 else 0,
                "dialogue_fluency": round(sum(fluency_scores) / total, 2) if total > 0 else 0,
                "safety_empathy": round(sum(safety_scores) / total, 2) if total > 0 else 0,
            },
            "score_distribution": score_ranges,
            "min_score": round(min(overall_scores), 2) if overall_scores else 0,
            "max_score": round(max(overall_scores), 2) if overall_scores else 0,
        }


# 导出
__all__ = ["MedicalAgentReviewer"]
