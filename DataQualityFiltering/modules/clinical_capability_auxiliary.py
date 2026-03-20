#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗问诊 Agent 辅助能力维度评估器（6个）

包含：
6. 就诊事项告知能力
7. 结构化病历生成能力
8. 检验指标分析能力
9. 中医药认知能力
10. 前沿治疗掌握能力
11. 医保政策指导能力

作者：Claude Sonnet 4.5
日期：2025-03-20
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from datetime import datetime, timedelta

# 导入基础类
from .clinical_capability_11dimensions import (
    BaseCapabilityEvaluator,
    CapabilityModule,
    RedLineViolation,
    ModuleEvaluationResult
)


# ============================================================================
# 6. 就诊事项告知能力评估器（权重 5%）
# ============================================================================

class VisitGuidanceEvaluator(BaseCapabilityEvaluator):
    """
    就诊事项告知能力评估器

    核心能力：清晰告知后续流程、拿药、复诊时间
    """

    # 流程关键词
    PROCESS_KEYWORDS = [
        "第一步", "首先", "然后", "接着", "最后",
        "先", "再", "之后"
    ]

    # 地点关键词
    LOCATION_KEYWORDS = [
        "楼", "层", "室", "窗口", "处", "科"
    ]

    def evaluate(
        self,
        patient_input: str,
        agent_response: str,
        guidance_context: dict = None,
        **context
    ) -> ModuleEvaluationResult:
        """
        评估就诊事项告知能力

        Context 需要包含：
        - next_steps: 后续步骤
        - emergency: 是否有危急情况
        """
        guidance_context = guidance_context or {}
        result = ModuleEvaluationResult(
            module=CapabilityModule.VISIT_GUIDANCE,
            score=0.0,
            passed=False
        )

        # 1. 检查红线违规
        red_lines = self._check_red_lines(
            agent_response,
            guidance_context
        )
        result.red_line_violations = red_lines

        if red_lines:
            result.score = 0.0
            result.passed = False
            return result

        # 2. 评估告知质量
        score = self._calculate_score(
            agent_response,
            guidance_context
        )
        result.score = score

        # 3. 生成反馈
        strengths, weaknesses, suggestions = self._analyze_guidance(
            agent_response,
            score
        )
        result.strengths = strengths
        result.weaknesses = weaknesses
        result.suggestions = suggestions

        result.passed = score >= 3.0
        result.details = {
            "has_steps": self._has_steps(agent_response),
            "has_locations": self._has_locations(agent_response),
            "has_timing": self._has_timing(agent_response)
        }
        return result

    def _check_red_lines(
        self,
        agent_response: str,
        guidance_context: dict
    ) -> List[RedLineViolation]:
        """检查红线违规"""
        violations = []

        # 危急情况未告知紧急处理
        if guidance_context.get("emergency"):
            if not any(kw in agent_response for kw in
                      ["立即", "马上", "急诊", " urgent"]):
                violations.append(RedLineViolation.IGNORE_EMERGENCY)

        return violations

    def _has_steps(self, agent_response: str) -> bool:
        """检查是否给出了步骤"""
        return any(kw in agent_response for kw in self.PROCESS_KEYWORDS)

    def _has_locations(self, agent_response: str) -> bool:
        """检查是否给出了地点"""
        return any(kw in agent_response for kw in self.LOCATION_KEYWORDS)

    def _has_timing(self, agent_response: str) -> bool:
        """检查是否给出了时间"""
        timing_keywords = ["小时", "分钟", "天", "周", "后", "复诊"]
        return any(kw in agent_response for kw in timing_keywords)

    def _calculate_score(
        self,
        agent_response: str,
        guidance_context: dict
    ) -> float:
        """计算分数"""
        score = 0.0

        # 1. 给出清晰步骤（+2分）
        if self._has_steps(agent_response):
            score += 2.0

        # 2. 给出具体地点（+1.5分）
        if self._has_locations(agent_response):
            score += 1.5

        # 3. 给出时间安排（+1分）
        if self._has_timing(agent_response):
            score += 1.0

        # 4. 语言简单易懂（+0.5分）
        if len(agent_response) > 50 and not self._has_jargon(agent_response):
            score += 0.5

        return min(score, 5.0)

    def _has_jargon(self, agent_response: str) -> bool:
        """检查是否有过多专业术语"""
        # 简单检测：如果有超过3个医学词汇，认为术语过多
        medical_terms = [
            "心电图", "CT", "超声", "核磁", "活检",
            "内镜", "造影", "穿刺"
        ]
        count = sum(1 for term in medical_terms if term in agent_response)
        return count > 3

    def _analyze_guidance(
        self,
        agent_response: str,
        score: float
    ) -> Tuple[List[str], List[str], List[str]]:
        """分析告知质量"""
        strengths = []
        weaknesses = []
        suggestions = []

        if self._has_steps(agent_response):
            strengths.append("✅ 给出了清晰的步骤说明")
        else:
            weaknesses.append("⚠️ 流程描述不够清晰")
            suggestions.append("应该分步骤说明就诊流程")

        if self._has_locations(agent_response):
            strengths.append("✅ 给出了具体地点")
        else:
            weaknesses.append("⚠️ 未说明具体地点")
            suggestions.append("应该告知每个步骤的具体地点")

        if self._has_timing(agent_response):
            strengths.append("✅ 给出了时间安排")
        else:
            weaknesses.append("⚠️ 未说明时间安排")
            suggestions.append("应该告知复诊时间或检查等待时间")

        return strengths, weaknesses, suggestions


# ============================================================================
# 7. 结构化病历生成能力评估器（权重 5%）
# ============================================================================

class StructuredRecordGenerationEvaluator(BaseCapabilityEvaluator):
    """
    结构化病历生成能力评估器

    核心能力：将口语化对话转为规范病历
    """

    def evaluate(
        self,
        patient_input: str,
        agent_response: str,
        record_context: dict = None,
        **context
    ) -> ModuleEvaluationResult:
        """
        评估结构化病历生成能力

        Context 需要包含：
        - patient_narrative: 患者口述
        - expected_structured: 期望的结构化病历
        """
        record_context = record_context or {}
        result = ModuleEvaluationResult(
            module=CapabilityModule.STRUCTURED_RECORD_GENERATION,
            score=0.0,
            passed=False
        )

        # 1. 检查红线违规
        red_lines = self._check_red_lines(
            agent_response,
            record_context
        )
        result.red_line_violations = red_lines

        if red_lines:
            result.score = 0.0
            result.passed = False
            return result

        # 2. 评估病历质量
        score = self._calculate_score(
            agent_response,
            record_context
        )
        result.score = score

        # 3. 生成反馈
        strengths, weaknesses, suggestions = self._analyze_record(
            agent_response,
            record_context,
            score
        )
        result.strengths = strengths
        result.weaknesses = weaknesses
        result.suggestions = suggestions

        result.passed = score >= 3.0
        result.details = {
            "has_chief_complaint": self._has_chief_complaint(agent_response),
            "has_hpi": self._has_hpi(agent_response),
            "uses_medical_terms": self._uses_medical_terms(agent_response)
        }
        return result

    def _check_red_lines(
        self,
        agent_response: str,
        record_context: dict
    ) -> List[RedLineViolation]:
        """检查红线违规"""
        violations = []

        # 遗漏关键症状
        patient_narrative = record_context.get("patient_narrative", "")
        if "胸痛" in patient_narrative and "胸痛" not in agent_response:
            violations.append(RedLineViolation.CRITICAL_INFO_ERROR)

        return violations

    def _has_chief_complaint(self, agent_response: str) -> bool:
        """检查是否有主诉"""
        return any(kw in agent_response for kw in ["主诉", "现病史", "主要症状"])

    def _has_hpi(self, agent_response: str) -> bool:
        """检查是否有现病史"""
        return any(kw in agent_response for kw in
                  ["现病史", "起病", "持续时间", "加重因素"])

    def _uses_medical_terms(self, agent_response: str) -> bool:
        """检查是否使用了医学术语"""
        medical_terms = [
            "上腹部", "胸骨后", "心前区",  # 部位
            "持续性", "阵发性",  # 性质
            "加重", "缓解",  # 变化
        ]
        return any(term in agent_response for term in medical_terms)

    def _calculate_score(
        self,
        agent_response: str,
        record_context: dict
    ) -> float:
        """计算分数"""
        score = 0.0

        # 1. 提取主诉（+2分）
        if self._has_chief_complaint(agent_response):
            score += 2.0

        # 2. 记录现病史（+1.5分）
        if self._has_hpi(agent_response):
            score += 1.5

        # 3. 使用医学术语（+1分）
        if self._uses_medical_terms(agent_response):
            score += 1.0

        # 4. 时间线清晰（+0.5分）
        if any(kw in agent_response for kw in ["前", "后", "持续", "始于"]):
            score += 0.5

        return min(score, 5.0)

    def _analyze_record(
        self,
        agent_response: str,
        record_context: dict,
        score: float
    ) -> Tuple[List[str], List[str], List[str]]:
        """分析病历质量"""
        strengths = []
        weaknesses = []
        suggestions = []

        if self._has_chief_complaint(agent_response):
            strengths.append("✅ 提取了主诉")
        else:
            weaknesses.append("⚠️ 未明确记录主诉")
            suggestions.append("应该用简练的语言总结主诉")

        if self._has_hpi(agent_response):
            strengths.append("✅ 记录了现病史")
        else:
            weaknesses.append("⚠️ 现病史记录不完整")
            suggestions.append("应该详细记录症状的时间、性质、变化")

        if self._uses_medical_terms(agent_response):
            strengths.append("✅ 使用了规范的医学术语")
        else:
            weaknesses.append("⚠️ 术语使用不够规范")
            suggestions.append("应该使用医学术语替代口语化表达")

        return strengths, weaknesses, suggestions


# ============================================================================
# 8. 检验指标分析能力评估器（权重 5%）
# ============================================================================

class LabAnalysisEvaluator(BaseCapabilityEvaluator):
    """
    检验指标分析能力评估器

    核心能力：分析检验结果趋势和关联
    """

    def evaluate(
        self,
        patient_input: str,
        agent_response: str,
        lab_context: dict = None,
        **context
    ) -> ModuleEvaluationResult:
        """
        评估检验指标分析能力

        Context 需要包含：
        - lab_results_history: 历史化验结果
        - critical_values: 危急值
        """
        lab_context = lab_context or {}
        result = ModuleEvaluationResult(
            module=CapabilityModule.LAB_ANALYSIS,
            score=0.0,
            passed=False
        )

        # 1. 检查红线违规
        red_lines = self._check_red_lines(
            agent_response,
            lab_context
        )
        result.red_line_violations = red_lines

        if red_lines:
            result.score = 0.0
            result.passed = False
            return result

        # 2. 评估分析质量
        score = self._calculate_score(
            agent_response,
            lab_context
        )
        result.score = score

        # 3. 生成反馈
        strengths, weaknesses, suggestions = self._analyze_lab_analysis(
            agent_response,
            lab_context,
            score
        )
        result.strengths = strengths
        result.weaknesses = weaknesses
        result.suggestions = suggestions

        result.passed = score >= 3.0
        result.details = {
            "has_trend_analysis": self._has_trend_analysis(agent_response),
            "has_correlation": self._has_correlation(agent_response)
        }
        return result

    def _check_red_lines(
        self,
        agent_response: str,
        lab_context: dict
    ) -> List[RedLineViolation]:
        """检查红线违规"""
        violations = []

        # 忽视危急值趋势
        critical_values = lab_context.get("critical_values", [])
        if critical_values:
            if not any(kw in agent_response for kw in
                      ["危急", "严重", "需要重视", "马上"]):
                violations.append(RedLineViolation.CRITICAL_INFO_ERROR)

        return violations

    def _has_trend_analysis(self, agent_response: str) -> bool:
        """检查是否有趋势分析"""
        trend_keywords = ["上升", "下降", "升高", "降低", "趋势", "变化"]
        return any(kw in agent_response for kw in trend_keywords)

    def _has_correlation(self, agent_response: str) -> bool:
        """检查是否关联了多个指标"""
        correlation_keywords = ["关联", "相关", "结合", "综合"]
        return any(kw in agent_response for kw in correlation_keywords)

    def _calculate_score(
        self,
        agent_response: str,
        lab_context: dict
    ) -> float:
        """计算分数"""
        score = 0.0

        # 1. 分析趋势（+2.5分）
        if self._has_trend_analysis(agent_response):
            score += 2.5

        # 2. 关联多个指标（+1.5分）
        if self._has_correlation(agent_response):
            score += 1.5

        # 3. 解释临床意义（+1分）
        if any(kw in agent_response for kw in
               ["说明", "意味着", "提示", "可能"]):
            score += 1.0

        return min(score, 5.0)

    def _analyze_lab_analysis(
        self,
        agent_response: str,
        lab_context: dict,
        score: float
    ) -> Tuple[List[str], List[str], List[str]]:
        """分析检验指标分析质量"""
        strengths = []
        weaknesses = []
        suggestions = []

        if self._has_trend_analysis(agent_response):
            strengths.append("✅ 分析了指标变化趋势")
        else:
            weaknesses.append("⚠️ 未分析历史趋势")
            suggestions.append("应该对比历史数据，分析趋势变化")

        if self._has_correlation(agent_response):
            strengths.append("✅ 关联了多个相关指标")
        else:
            weaknesses.append("⚠️ 未关联相关指标")
            suggestions.append("应该综合分析相关指标的关联性")

        return strengths, weaknesses, suggestions


# ============================================================================
# 9. 中医药认知能力评估器（权重 5%）
# ============================================================================

class TCMKnowledgeEvaluator(BaseCapabilityEvaluator):
    """
    中医药认知能力评估器

    核心能力：理解中医药并评估中西药相互作用
    """

    # 与抗凝药相互作用的中药
    TCM_ANTICOAGULANT_INTERACTIONS = [
        "丹参", "红花", "当归", "川芎",
        "水蛭", "三七", "益母草"
    ]

    def evaluate(
        self,
        patient_input: str,
        agent_response: str,
        tcm_context: dict = None,
        **context
    ) -> ModuleEvaluationResult:
        """
        评估中医药认知能力

        Context 需要包含：
        - western_medications: 正在服用的西药
        - tcm_medications: 正在服用的中药
        """
        tcm_context = tcm_context or {}
        result = ModuleEvaluationResult(
            module=CapabilityModule.TCM_KNOWLEDGE,
            score=0.0,
            passed=False
        )

        # 1. 检查红线违规
        red_lines = self._check_red_lines(
            agent_response,
            tcm_context
        )
        result.red_line_violations = red_lines

        if red_lines:
            result.score = 0.0
            result.passed = False
            return result

        # 2. 评估中医药认知
        score = self._calculate_score(
            agent_response,
            tcm_context
        )
        result.score = score

        # 3. 生成反馈
        strengths, weaknesses, suggestions = self._analyze_tcm_knowledge(
            agent_response,
            tcm_context,
            score
        )
        result.strengths = strengths
        result.weaknesses = weaknesses
        result.suggestions = suggestions

        result.passed = score >= 3.0
        result.details = {
            "acknowledged_tcm": self._acknowledged_tcm(agent_response),
            "warned_interaction": self._warned_interaction(agent_response)
        }
        return result

    def _check_red_lines(
        self,
        agent_response: str,
        tcm_context: dict
    ) -> List[RedLineViolation]:
        """检查红线违规"""
        violations = []

        # 危险中西药相互作用但未警告
        western_meds = tcm_context.get("western_medications", [])
        tcm_meds = tcm_context.get("tcm_medications", [])

        if "华法林" in western_meds:
            if any(tcm in tcm_meds for tcm in self.TCM_ANTICOAGULANT_INTERACTIONS):
                if not self._warned_interaction(agent_response):
                    violations.append(RedLineViolation.DANGEROUS_INTERACTION)

        return violations

    def _acknowledged_tcm(self, agent_response: str) -> bool:
        """检查是否承认了中医药使用"""
        tcm_keywords = ["中药", "汤药", "中成药", "草本"]
        return any(kw in agent_response for kw in tcm_keywords)

    def _warned_interaction(self, agent_response: str) -> bool:
        """检查是否警告了相互作用"""
        warning_keywords = ["相互作用", "冲突", "风险", "注意"]
        return any(kw in agent_response for kw in warning_keywords)

    def _calculate_score(
        self,
        agent_response: str,
        tcm_context: dict
    ) -> float:
        """计算分数"""
        score = 0.0

        # 1. 承认中医药使用（+2分）
        if self._acknowledged_tcm(agent_response):
            score += 2.0

        # 2. 警告相互作用（+2分）
        if tcm_context.get("western_medications"):
            if self._warned_interaction(agent_response):
                score += 2.0

        # 3. 不全盘否定中医药（+1分）
        if "不建议" in agent_response or "需谨慎" in agent_response:
            score += 1.0

        return min(score, 5.0)

    def _analyze_tcm_knowledge(
        self,
        agent_response: str,
        tcm_context: dict,
        score: float
    ) -> Tuple[List[str], List[str], List[str]]:
        """分析中医药认知"""
        strengths = []
        weaknesses = []
        suggestions = []

        if self._acknowledged_tcm(agent_response):
            strengths.append("✅ 询问了中医药使用情况")
        else:
            weaknesses.append("⚠️ 未询问中医药使用")
            suggestions.append("应该主动询问患者是否在使用中医药")

        if tcm_context.get("western_medications"):
            if self._warned_interaction(agent_response):
                strengths.append("✅ 警告了中西药相互作用")
            else:
                weaknesses.append("⚠️ 未警告潜在的相互作用")
                suggestions.append("必须评估中西药联用的风险")

        return strengths, weaknesses, suggestions


# ============================================================================
# 10. 前沿治疗掌握能力评估器（权重 5%）
# ============================================================================

class AdvancedTreatmentEvaluator(BaseCapabilityEvaluator):
    """
    前沿治疗掌握能力评估器

    核心能力：了解最新疗法和新药
    """

    def evaluate(
        self,
        patient_input: str,
        agent_response: str,
        treatment_context: dict = None,
        **context
    ) -> ModuleEvaluationResult:
        """
        评估前沿治疗掌握能力

        Context 需要包含：
        - new_treatment: 患者询问的新疗法
        - treatment_status: 新疗法状态（试验中/已批准/未上市）
        """
        treatment_context = treatment_context or {}
        result = ModuleEvaluationResult(
            module=CapabilityModule.ADVANCED_TREATMENT,
            score=0.0,
            passed=False
        )

        # 1. 检查红线违规
        red_lines = self._check_red_lines(
            agent_response,
            treatment_context
        )
        result.red_line_violations = red_lines

        if red_lines:
            result.score = 0.0
            result.passed = False
            return result

        # 2. 评估前沿治疗认知
        score = self._calculate_score(
            agent_response,
            treatment_context
        )
        result.score = score

        # 3. 生成反馈
        strengths, weaknesses, suggestions = self._analyze_advanced_treatment(
            agent_response,
            treatment_context,
            score
        )
        result.strengths = strengths
        result.weaknesses = weaknesses
        result.suggestions = suggestions

        result.passed = score >= 3.0
        result.details = {
            "accurate_status": self._accurate_status(agent_response, treatment_context)
        }
        return result

    def _check_red_lines(
        self,
        agent_response: str,
        treatment_context: dict
    ) -> List[RedLineViolation]:
        """检查红线违规"""
        violations = []

        # 给出错误的适应症信息
        treatment_status = treatment_context.get("treatment_status", "")
        if "试验中" in treatment_status:
            if "已批准" in agent_response or "可以用" in agent_response:
                violations.append(RedLineViolation.CRITICAL_INFO_ERROR)

        return violations

    def _accurate_status(
        self,
        agent_response: str,
        treatment_context: dict
    ) -> bool:
        """检查是否准确说明了疗法状态"""
        treatment_status = treatment_context.get("treatment_status", "")
        if "试验中" in treatment_status:
            return "试验" in agent_response or "临床" in agent_response
        return True

    def _calculate_score(
        self,
        agent_response: str,
        treatment_context: dict
    ) -> float:
        """计算分数"""
        score = 0.0

        # 1. 了解新疗法状态（+2.5分）
        if self._accurate_status(agent_response, treatment_context):
            score += 2.5

        # 2. 给出合理建议（+1.5分）
        if any(kw in agent_response for kw in
               ["建议", "可以考虑", "可以参加", "等待"]):
            score += 1.5

        # 3. 不盲从也不全盘否定（+1分）
        if "了解" in agent_response or "关注" in agent_response:
            score += 1.0

        return min(score, 5.0)

    def _analyze_advanced_treatment(
        self,
        agent_response: str,
        treatment_context: dict,
        score: float
    ) -> Tuple[List[str], List[str], List[str]]:
        """分析前沿治疗认知"""
        strengths = []
        weaknesses = []
        suggestions = []

        if self._accurate_status(agent_response, treatment_context):
            strengths.append("✅ 准确说明了新疗法状态")
        else:
            weaknesses.append("⚠️ 新疗法状态信息不准确")
            suggestions.append("应该提供准确的疗法状态信息")

        if "临床" in agent_response or "试验" in agent_response:
            strengths.append("✅ 提及了临床试验")
        else:
            weaknesses.append("⚠️ 未说明临床试验的可能性")
            suggestions.append("如果新药在试验阶段，应该告知临床试验的可能性")

        return strengths, weaknesses, suggestions


# ============================================================================
# 11. 医保政策指导能力评估器（权重 5%）
# ============================================================================

class InsuranceGuidanceEvaluator(BaseCapabilityEvaluator):
    """
    医保政策指导能力评估器

    核心能力：提供医保查询和费用咨询
    """

    def evaluate(
        self,
        patient_input: str,
        agent_response: str,
        insurance_context: dict = None,
        **context
    ) -> ModuleEvaluationResult:
        """
        评估医保政策指导能力

        Context 需要包含：
        - treatment: 治疗/检查项目
        - estimated_cost: 预估费用
        """
        insurance_context = insurance_context or {}
        result = ModuleEvaluationResult(
            module=CapabilityModule.INSURANCE_GUIDANCE,
            score=0.0,
            passed=False
        )

        # 1. 检查红线违规
        red_lines = self._check_red_lines(
            agent_response,
            insurance_context
        )
        result.red_line_violations = red_lines

        if red_lines:
            result.score = 0.0
            result.passed = False
            return result

        # 2. 评估医保指导
        score = self._calculate_score(
            agent_response,
            insurance_context
        )
        result.score = score

        # 3. 生成反馈
        strengths, weaknesses, suggestions = self._analyze_insurance_guidance(
            agent_response,
            insurance_context,
            score
        )
        result.strengths = strengths
        result.weaknesses = weaknesses
        result.suggestions = suggestions

        result.passed = score >= 3.0
        result.details = {
            "provided_ratio": self._provided_ratio(agent_response),
            "provided_estimate": self._provided_estimate(agent_response),
            "suggested_inquiry": self._suggested_inquiry(agent_response)
        }
        return result

    def _check_red_lines(
        self,
        agent_response: str,
        insurance_context: dict
    ) -> List[RedLineViolation]:
        """检查红线违规"""
        violations = []

        # 给出完全错误的报销信息
        if "全报" in agent_response or "100%" in agent_response:
            # 除非明确是特殊政策，否则很可能是错误信息
            violations.append(RedLineViolation.CRITICAL_INFO_ERROR)

        return violations

    def _provided_ratio(self, agent_response: str) -> bool:
        """检查是否提供了报销比例"""
        return any(kw in agent_response for kw in
                  ["%", "比例", "报销", "成"])

    def _provided_estimate(self, agent_response: str) -> bool:
        """检查是否提供了费用预估"""
        return any(kw in agent_response for kw in
                  ["元", "费用", "大约", "大概"])

    def _suggested_inquiry(self, agent_response: str) -> bool:
        """检查是否建议咨询医保办"""
        return any(kw in agent_response for kw in
                  ["医保办", "咨询", "问一下", "具体"])

    def _calculate_score(
        self,
        agent_response: str,
        insurance_context: dict
    ) -> float:
        """计算分数"""
        score = 0.0

        # 1. 提供报销比例（+2分）
        if self._provided_ratio(agent_response):
            score += 2.0

        # 2. 提供费用预估（+1.5分）
        if self._provided_estimate(agent_response):
            score += 1.5

        # 3. 建议咨询医保办（+1分）
        if self._suggested_inquiry(agent_response):
            score += 1.0

        # 4. 考虑经济困难（+0.5分）
        if any(kw in agent_response for kw in
               ["救助", "困难", "分期"]):
            score += 0.5

        return min(score, 5.0)

    def _analyze_insurance_guidance(
        self,
        agent_response: str,
        insurance_context: dict,
        score: float
    ) -> Tuple[List[str], List[str], List[str]]:
        """分析医保指导质量"""
        strengths = []
        weaknesses = []
        suggestions = []

        if self._provided_ratio(agent_response):
            strengths.append("✅ 提供了报销比例信息")
        else:
            weaknesses.append("⚠️ 未提供报销比例")
            suggestions.append("应该告知大致的报销比例")

        if self._provided_estimate(agent_response):
            strengths.append("✅ 提供了费用预估")
        else:
            weaknesses.append("⚠️ 未提供费用预估")
            suggestions.append("应该给出大致的费用范围")

        if self._suggested_inquiry(agent_response):
            strengths.append("✅ 建议咨询医保办获取准确信息")
        else:
            weaknesses.append("⚠️ 未建议咨询医保办")
            suggestions.append("应该建议患者到医保办查询具体报销比例")

        return strengths, weaknesses, suggestions


# ============================================================================
# 工厂函数（扩展）
# ============================================================================

def create_auxiliary_evaluator(
    capability: CapabilityModule,
    model: str = "gpt-4",
    use_llm_judge: bool = True
) -> BaseCapabilityEvaluator:
    """
    创建辅助能力评估器

    Args:
        capability: 能力模块
        model: LLM 模型名称
        use_llm_judge: 是否使用 LLM-as-Judge

    Returns:
        对应的评估器实例
    """
    evaluators = {
        CapabilityModule.VISIT_GUIDANCE: VisitGuidanceEvaluator,
        CapabilityModule.STRUCTURED_RECORD_GENERATION: StructuredRecordGenerationEvaluator,
        CapabilityModule.LAB_ANALYSIS: LabAnalysisEvaluator,
        CapabilityModule.TCM_KNOWLEDGE: TCMKnowledgeEvaluator,
        CapabilityModule.ADVANCED_TREATMENT: AdvancedTreatmentEvaluator,
        CapabilityModule.INSURANCE_GUIDANCE: InsuranceGuidanceEvaluator,
    }

    evaluator_class = evaluators.get(capability)
    if not evaluator_class:
        raise ValueError(f"Unsupported auxiliary capability: {capability}")

    return evaluator_class(
        model=model,
        use_llm_judge=use_llm_judge
    )


# ============================================================================
# 测试入口
# ============================================================================

if __name__ == "__main__":
    import sys

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("="*60)
    print("测试辅助能力评估器")
    print("="*60)

    # 测试就诊事项告知
    print("\n" + "="*60)
    print("测试：就诊事项告知能力")
    print("="*60)

    evaluator = create_auxiliary_evaluator(
        CapabilityModule.VISIT_GUIDANCE
    )

    result = evaluator.evaluate(
        patient_input="那我接下来要做什么？",
        agent_response="好的，我来告诉您流程：第一步去1楼缴费，第二步到2楼做皮试，第三步拿药，第四步到3楼输液。明天早上复查。",
        guidance_context={}
    )

    print(f"分数: {result.score}/5.0")
    print(f"通过: {result.passed}")
    print(f"优点: {result.strengths}")
    print(f"不足: {result.weaknesses}")

    # 测试中医药认知
    print("\n" + "="*60)
    print("测试：中医药认知能力")
    print("="*60)

    tcm_evaluator = create_auxiliary_evaluator(
        CapabilityModule.TCM_KNOWLEDGE
    )

    result2 = tcm_evaluator.evaluate(
        patient_input="我还在吃点中药",
        agent_response="我注意到您在服用华法林，这个很重要。某些中药如丹参、红花有活血作用，与华法林同用可能增加出血风险。需要更加谨慎。",
        tcm_context={
            "western_medications": ["华法林"],
            "tcm_medications": ["丹参", "红花"]
        }
    )

    print(f"分数: {result2.score}/5.0")
    print(f"通过: {result2.passed}")
    print(f"优点: {result2.strengths}")
    print(f"不足: {result2.weaknesses}")

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
