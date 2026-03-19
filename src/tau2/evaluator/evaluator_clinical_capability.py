#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tau2框架集成包装器 - 临床能力评估器

将新的临床能力评估器（模块2、模块3等）集成到tau2评估框架中，与现有的ClinicalEvaluator协同工作。

作者：Claude Sonnet 4.5
日期：2025-03-20
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# 导入tau2核心组件
from tau2.data_model.message import Message
from tau2.data_model.simulation import ClinicalCheck, RewardInfo
from tau2.data_model.tasks import RewardType, Task
from tau2.evaluator.evaluator_base import EvaluatorBase

# 导入新的临床能力评估器
# 注意：需要确保模块路径正确
try:
    # 从DataQualityFiltering导入
    module_path = Path(__file__).parent.parent.parent.parent / "DataQualityFiltering" / "modules"
    if str(module_path) not in sys.path:
        sys.path.insert(0, str(module_path))

    from evaluator_no_hallucination import NoHallucinationDiagnosisEvaluator
    from evaluator_medication_guidance import MedicationGuidanceEvaluator
except ImportError as e:
    logging.warning(f"无法导入临床能力评估器：{e}")
    NoHallucinationDiagnosisEvaluator = None
    MedicationGuidanceEvaluator = None


class ClinicalCapabilityEvaluator(EvaluatorBase):
    """
    临床能力评估器 - tau2集成包装器

    这是一个适配器，将新的临床能力评估器（无幻觉诊断、用药指导等）集成到tau2框架中。

    使用方式：
    1. 独立使用：直接调用calculate_reward方法
    2. 与现有评估器协同：在ClinicalEvaluator中调用

    设计原则：
    - 保持与现有tau2评估器接口一致
    - 支持模块化评估（可选择启用哪些模块）
    - 输出符合tau2的RewardInfo格式
    - 支持缓存和批处理
    """

    # 默认启用哪些能力模块
    DEFAULT_ENABLED_MODULES = [
        "no_hallucination_diagnosis",  # 无幻觉诊断
        "medication_guidance",  # 用药指导
        # 未来可添加更多模块
    ]

    # 默认权重配置
    DEFAULT_MODULE_WEIGHTS = {
        "no_hallucination_diagnosis": 0.5,
        "medication_guidance": 0.5,
    }

    def __init__(
        self,
        model: str = "gpt-4",
        enabled_modules: Optional[list] = None,
        module_weights: Optional[dict] = None,
        use_llm_judge: bool = True,
        cache_dir: Optional[str] = None,
        pass_threshold: float = 3.0,
    ):
        """
        初始化临床能力评估器

        Args:
            model: LLM模型名称
            enabled_modules: 启用的模块列表，None表示使用默认
            module_weights: 模块权重配置，None表示使用默认
            use_llm_judge: 是否使用LLM-as-Judge进行更精确的评估
            cache_dir: 缓存目录
            pass_threshold: 通过阈值（0-5分）
        """
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.enabled_modules = enabled_modules or self.DEFAULT_ENABLED_MODULES
        self.module_weights = module_weights or self.DEFAULT_MODULE_WEIGHTS
        self.use_llm_judge = use_llm_judge
        self.pass_threshold = pass_threshold
        self.cache_dir = cache_dir

        # 初始化各模块评估器
        self.evaluators = {}
        self._init_evaluators()

    def _init_evaluators(self):
        """初始化各模块的评估器"""
        if NoHallucinationDiagnosisEvaluator and "no_hallucination_diagnosis" in self.enabled_modules:
            self.evaluators["no_hallucination_diagnosis"] = NoHallucinationDiagnosisEvaluator(
                model=self.model,
                use_llm_judge=self.use_llm_judge
            )
            self.logger.info("已初始化无幻觉诊断评估器")

        if MedicationGuidanceEvaluator and "medication_guidance" in self.enabled_modules:
            self.evaluators["medication_guidance"] = MedicationGuidanceEvaluator(
                model=self.model,
                use_llm_judge=self.use_llm_judge
            )
            self.logger.info("已初始化用药指导评估器")

    @classmethod
    def calculate_reward(
        cls,
        task: Task,
        full_trajectory: list[Message],
        model: str = "gpt-4",
        enabled_modules: Optional[list] = None,
        module_weights: Optional[dict] = None,
        use_llm_judge: bool = True,
        pass_threshold: float = 3.0,
        **kwargs,
    ) -> RewardInfo:
        """
        计算临床能力评估的奖励分数

        这是tau2框架调用的主要接口。

        Args:
            task: 任务对象，包含用户场景和评估标准
            full_trajectory: 完整的对话轨迹
            model: LLM模型名称
            enabled_modules: 启用的模块列表
            module_weights: 模块权重配置
            use_llm_judge: 是否使用LLM-as-Judge
            pass_threshold: 通过阈值
            **kwargs: 额外参数

        Returns:
            RewardInfo: 包含clinical_checks的奖励信息
        """
        # 创建实例（因为__init__不是类方法）
        evaluator = cls(
            model=model,
            enabled_modules=enabled_modules,
            module_weights=module_weights,
            use_llm_judge=use_llm_judge,
            pass_threshold=pass_threshold,
        )

        # 从轨迹中提取患者问题和AI回答
        patient_question, ai_response = evaluator._extract_dialogue(full_trajectory)

        # 从task中提取上下文信息
        context = evaluator._extract_context(task, kwargs)

        # 执行各模块的评估
        module_results = []
        overall_score = 0.0
        total_weight = 0.0
        red_line_violations = []

        for module_name, module_evaluator in evaluator.evaluators.items():
            # 获取该模块的特定上下文
            module_context = context.get(module_name, {})

            # 调用模块评估器
            try:
                if module_name == "no_hallucination_diagnosis":
                    result = module_evaluator.evaluate(
                        patient_input=patient_question,
                        agent_response=ai_response,
                        available_info=module_context,
                        trajectory=full_trajectory
                    )
                elif module_name == "medication_guidance":
                    result = module_evaluator.evaluate(
                        patient_input=patient_question,
                        agent_response=ai_response,
                        medication_context=module_context,
                        trajectory=full_trajectory
                    )
                else:
                    result = {"overall_score": 0.0, "passed": False}

                module_results.append(result)

                # 记录红线违规
                if result.get("red_line_violations"):
                    red_line_violations.extend([
                        f"{module_name}: {v}"
                        for v in result["red_line_violations"]
                    ])

                # 计算加权分数（仅当没有红线违规时）
                if not result.get("red_line_violations"):
                    weight = evaluator.module_weights.get(module_name, 1.0)
                    overall_score += result["overall_score"] * weight
                    total_weight += weight

            except Exception as e:
                evaluator.logger.error(f"模块{module_name}评估失败：{e}")
                module_results.append({
                    "module": module_name,
                    "overall_score": 0.0,
                    "passed": False,
                    "error": str(e)
                })

        # 计算总分
        if total_weight > 0:
            overall_score = overall_score / total_weight
        else:
            overall_score = 0.0

        # 判断是否通过（如果有红线违规，直接不通过）
        passed = overall_score >= evaluator.pass_threshold and len(red_line_violations) == 0

        # 计算奖励分数（归一化到0-1）
        reward = overall_score / 5.0

        # 构建ClinicalCheck对象
        clinical_check = ClinicalCheck(
            overall_score=round(overall_score, 2),
            dimension_scores={
                result["module"]: result.get("dimension_scores", {})
                for result in module_results
            },
            met=passed,
            reward=round(reward, 3),
            strengths=sum([result.get("strengths", []) for result in module_results], []),
            weaknesses=sum([result.get("weaknesses", []) for result in module_results], []),
            suggestions=sum([result.get("suggestions", []) for result in module_results], []),
            comments=evaluator._generate_comments(
                overall_score, passed, module_results, red_line_violations
            ),
        )

        # 构建RewardInfo
        reward_info = RewardInfo(
            reward=reward,
            clinical_checks=[clinical_check],
            reward_basis=[RewardType.CLINICAL],
            reward_breakdown={RewardType.CLINICAL: reward},
            info={
                "model": model,
                "enabled_modules": evaluator.enabled_modules,
                "module_weights": evaluator.module_weights,
                "module_results": module_results,
                "red_line_violations": red_line_violations,
            },
        )

        return reward_info

    def _extract_dialogue(
        self, full_trajectory: list[Message]
    ) -> tuple[str, str]:
        """
        从对话轨迹中提取患者问题和AI回答

        Args:
            full_trajectory: 完整的对话轨迹

        Returns:
            (patient_question, ai_response) 元组
        """
        patient_question = ""
        ai_response = ""

        # 找到最后一条用户消息作为患者问题
        for msg in reversed(full_trajectory):
            if msg.role == "user":
                patient_question = msg.content or ""
                break

        # 找到最后一条助手消息作为AI回答
        for msg in reversed(full_trajectory):
            if msg.role == "assistant":
                # 如果有工具调用，也包含在回答中
                if msg.tool_calls:
                    tool_info = "\n".join([
                        f"工具调用: {call.function.name}({call.function.arguments})"
                        for call in msg.tool_calls
                    ])
                    ai_response = (msg.content or "") + "\n" + tool_info
                else:
                    ai_response = msg.content or ""
                break

        return patient_question, ai_response

    def _extract_context(
        self, task: Task, kwargs: dict
    ) -> dict:
        """
        从任务中提取上下文信息，为各模块提供所需的数据

        Args:
            task: 任务对象
            kwargs: 额外参数

        Returns:
            各模块的上下文信息字典
        """
        context = {}

        # 基础信息（所有模块通用）
        base_context = {
            "domain": getattr(task.user_scenario.instructions, 'domain', 'unknown'),
            "reason_for_call": getattr(task.user_scenario.instructions, 'reason_for_call', ''),
            "known_info": getattr(task.user_scenario.instructions, 'known_info', ''),
        }

        # 从task的initial_state中提取更多信息
        if hasattr(task, 'initial_state') and task.initial_state:
            init_actions = task.initial_state.initialization_actions or []
            for action in init_actions:
                if action.action_type == "patient_info":
                    # 患者信息（年龄、性别等）
                    base_context.update(action.parameters or {})
                elif action.action_type == "medical_records":
                    # 医疗记录（症状、检查结果等）
                    base_context.update(action.parameters or {})

        # 从kwargs中提取模块特定的上下文
        # 这允许外部传入额外的上下文信息
        context.update(kwargs.get("context", {}))

        # 为各模块分配上下文
        # 无幻觉诊断模块
        context["no_hallucination_diagnosis"] = {
            "symptoms": base_context.get("symptoms", []),
            "duration": base_context.get("duration"),
            "severity": base_context.get("severity"),
            "past_history": base_context.get("past_history", []),
            "lab_results": base_context.get("lab_results", {}),
            "information_level": base_context.get("information_level", "partial"),
            **{k: v for k, v in base_context.items() if k not in ["symptoms", "duration", "severity", "past_history", "lab_results", "information_level"]}
        }

        # 用药指导模块
        context["medication_guidance"] = {
            "allergies": base_context.get("allergies", []),
            "current_medications": base_context.get("current_medications", []),
            "proposed_medication": base_context.get("proposed_medication", ""),
            "patient_profile": base_context.get("patient_profile", {}),
            "lab_results": base_context.get("lab_results", {}),
            "scenario_type": self._classify_scenario(base_context),
        }

        return context

    def _classify_scenario(self, context: dict) -> str:
        """
        分类场景类型，用于评估器选择适当的评估策略

        Args:
            context: 基础上下文信息

        Returns:
            场景类型字符串
        """
        reason_for_call = context.get("reason_for_call", "").lower()

        if any(kw in reason_for_call for kw in ["药", "用药", "吃药", "药物"]):
            return "medication_consultation"
        elif any(kw in reason_for_call for kw in ["检查", "化验", "ct", "b超"]):
            return "test_ordering"
        elif any(kw in reason_for_call for kw in ["手术", "住院"]):
            return "procedural"
        else:
            return "general_consultation"

    def _generate_comments(
        self,
        overall_score: float,
        passed: bool,
        module_results: list,
        red_line_violations: list
    ) -> str:
        """
        生成评估评语

        Args:
            overall_score: 总分
            passed: 是否通过
            module_results: 各模块评估结果
            red_line_violations: 红线违规列表

        Returns:
            评语字符串
        """
        lines = []

        # 总体评价
        lines.append("临床能力评估结果：")
        lines.append(f"- 总分: {overall_score:.2f}/5.0 ({'通过' if passed else '未通过'})")

        # 红线违规
        if red_line_violations:
            lines.append(f"- ⛔ 红线违规: {len(red_line_violations)}项")
            for violation in red_line_violations:
                lines.append(f"  * {violation}")

        # 各模块得分
        lines.append("- 各模块得分:")
        for result in module_results:
            module_name = result.get("module", "unknown")
            score = result.get("overall_score", 0.0)
            module_passed = result.get("passed", False)
            lines.append(f"  * {module_name}: {score:.2f}/5.0 ({'通过' if module_passed else '未通过'})")

        # 优势
        strengths = sum([r.get("strengths", []) for r in module_results], [])
        if strengths:
            lines.append("- 优势:")
            for strength in strengths[:3]:  # 最多显示3条
                lines.append(f"  * {strength}")

        # 待改进
        weaknesses = sum([r.get("weaknesses", []) for r in module_results], [])
        if weaknesses:
            lines.append("- 待改进:")
            for weakness in weaknesses[:3]:
                lines.append(f"  * {weakness}")

        # 改进建议
        suggestions = sum([r.get("suggestions", []) for r in module_results], [])
        if suggestions:
            lines.append("- 建议:")
            for suggestion in suggestions[:3]:
                lines.append(f"  * {suggestion}")

        return "\n".join(lines)


# ============================================================================
# 工厂函数 - 便于创建评估器实例
# ============================================================================

def create_clinical_capability_evaluator(
    model: str = "gpt-4",
    modules: Optional[list] = None,
    **kwargs
) -> ClinicalCapabilityEvaluator:
    """
    创建临床能力评估器实例

    Args:
        model: LLM模型名称
        modules: 启用的模块列表，None表示使用默认
        **kwargs: 其他参数

    Returns:
        ClinicalCapabilityEvaluator实例
    """
    return ClinicalCapabilityEvaluator(
        model=model,
        enabled_modules=modules,
        **kwargs
    )


# ============================================================================
# 示例用法
# ============================================================================

if __name__ == "__main__":
    import json
    from tau2.data_model.message import Message
    from tau2.data_model.tasks import Task, UserScenario, StructuredUserInstructions, Description

    # 创建模拟的Task和trajectory
    task = Task(
        task_id="test_clinical_capability",
        description=Description(
            purpose="测试临床能力评估器"
        ),
        user_scenario=UserScenario(
            persona="45岁男性患者",
            instructions=StructuredUserInstructions(
                domain="internal_medicine",
                reason_for_call="患者咨询用药，头孢能否和阿司匹林一起吃",
                known_info="高血压，服用阿司匹林和氨氯地平",
                task_instructions="你是一名患者"
            )
        ),
        initial_state=None,
        evaluation_criteria=None
    )

    # 创建模拟的对话轨迹
    trajectory = [
        Message(role="user", content="医生，我因为感冒想头孢，但我平时吃阿司匹林，能一起吃吗？"),
        Message(
            role="assistant",
            content="我查到您正在服用阿司匹林。头孢和阿司匹林联用是安全的，不会产生危险的相互作用。您可以正常服用头孢治疗感冒。建议：1）按时按量服用；2）注意过敏反应；3）如有不适及时就医。"
        )
    ]

    # 执行评估
    try:
        reward_info = ClinicalCapabilityEvaluator.calculate_reward(
            task=task,
            full_trajectory=trajectory,
            model="gpt-4",
            enabled_modules=["medication_guidance"],
            use_llm_judge=False
        )

        print("评估结果：")
        print(f"奖励分数: {reward_info.reward}")
        print(f"\n临床检查:")
        for check in reward_info.clinical_checks:
            print(f"总分: {check.overall_score}")
            print(f"通过: {check.met}")
            print(f"评语:\n{check.comments}")

    except Exception as e:
        print(f"评估失败（预期，因为这是示例）：{e}")
        print("\n提示：在实际使用时，请确保：")
        print("1. DataQualityFiltering/modules目录在Python路径中")
        print("2. 已安装所需的依赖包")
        print("3. 配置了正确的LLM API")
