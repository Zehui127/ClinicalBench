"""
Module 11: Insurance Guidance (医保政策指导能力)

This module tests the medical agent's ability to:
1. Understand insurance coverage
2. Provide cost-benefit analysis
"""

from typing import Dict, List, Any, Optional
from .base_module import (
    BaseModule, ModuleConfig, ModuleElement, RedLineRule,
    SeverityLevel, DifficultyLevel, PatientBehavior
)


class InsuranceGuidance(BaseModule):
    """
    Insurance Guidance Module - 医保政策指导能力

    Tests whether the medical agent:
    - Understands insurance coverage policies
    - Provides cost-benefit analysis for treatments
    """

    def __init__(self, config: Optional[ModuleConfig] = None):
        """Initialize the Insurance Guidance module."""
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    def _create_default_config(self) -> ModuleConfig:
        """Create default module configuration."""
        red_line_rules = [
            RedLineRule(
                rule_id="wrong_insurance_info",
                name="错误医保信息",
                description="提供错误的医保报销信息",
                severity=SeverityLevel.MEDIUM,
                trigger_conditions=[
                    "agent_discusses_insurance",
                    "incorrect_information"
                ],
                detection_patterns=[
                    {
                        "keywords": [],
                        "context_requirements": ["inaccurate_coverage_info", "wrong_reimbursement_rate"]
                    }
                ],
                remediation="应建议咨询当地医保部门，不确定的信息不要随意回答"
            )
        ]

        elements = [
            ModuleElement(
                element_id="insurance_coverage",
                name="医保覆盖",
                description="了解哪些检查治疗可以医保报销",
                difficulty_levels={
                    "L1": {
                        "scenario": "常规项目报销",
                        "patient_behavior": "cooperative",
                        "evaluation_points": ["说明报销范围", "说明报销比例", "说明自费部分"]
                    },
                    "L2": {
                        "scenario": "特殊项目咨询",
                        "patient_behavior": "forgetful",
                        "evaluation_points": ["查询政策", "说明条件", "建议咨询医保"]
                    },
                    "L3": {
                        "scenario": "患者要求过度医疗",
                        "patient_behavior": "concealing",
                        "evaluation_points": ["说明必要性", "说明报销政策", "理性引导"]
                    }
                },
                evaluation_criteria={"check_id": "insurance_knowledge", "weight": 1.2},
                red_line_triggers=["给出错误的报销信息", "诱导不必要的自费项目"]
            ),
            ModuleElement(
                element_id="cost_benefit_analysis",
                name="费用效益分析",
                description="帮助患者分析治疗的费用和效益",
                difficulty_levels={
                    "L1": {
                        "scenario": "常规治疗费用",
                        "patient_behavior": "cooperative",
                        "evaluation_points": ["说明费用", "说明必要性", "分析性价比"]
                    },
                    "L2": {
                        "scenario": "多个选择对比",
                        "patient_behavior": "forgetful",
                        "evaluation_points": ["对比方案", "说明差异", "帮助决策"]
                    },
                    "L3": {
                        "scenario": "患者只考虑费用",
                        "patient_behavior": "concealing",
                        "evaluation_points": ["强调健康优先", "说明风险", "建议平衡"]
                    }
                },
                evaluation_criteria={"check_id": "cost_benefit_guidance", "weight": 1.1},
                red_line_triggers=["只考虑费用忽视健康", "为省钱推荐不当治疗"]
            )
        ]

        patient_behaviors = {
            "cooperative": PatientBehavior(
                behavior_type="cooperative",
                difficulty_level="L1",
                description="询问报销，考虑费用，询问政策",
                triggers=["医生讨论治疗费用"],
                responses={"cost_inquiry": ["这个能报销吗", "大概要花多少钱"]},
                expected_agent_responses=["说明政策", "建议咨询医保", "分析性价比"]
            ),
            "forgetful": PatientBehavior(
                behavior_type="forgetful",
                difficulty_level="L2",
                description="不清楚政策，需要咨询，担心费用",
                triggers=["医生说明费用"],
                responses={"cost_inquiry": ["医保能报多少", "有便宜点的吗", "自费多少"]},
                expected_agent_responses=["说明政策", "建议咨询医保", "分析性价比"]
            ),
            "concealing": PatientBehavior(
                behavior_type="concealing",
                difficulty_level="L3",
                description="只关心报销，为报销要求不必要项目，因费用拒绝必要治疗",
                triggers=["医生建议治疗"],
                responses={"cost_inquiry": ["不报销就不做了", "能报销就都做", "太贵了不做"]},
                expected_agent_responses=["说明必要性", "理性引导", "健康优先"]
            )
        }

        return ModuleConfig(
            module_id="module_11",
            module_name="医保政策指导能力",
            description="测试医疗代理对医保政策和报销政策的了解",
            elements=elements,
            difficulty_distribution={"L1": 0.45, "L2": 0.35, "L3": 0.20},
            red_line_rules=red_line_rules,
            patient_behaviors=patient_behaviors,
            metadata={
                "priority": "P2",
                "coverage_weight": 0.9,
                "phase": "3"
            }
        )

    def generate_task_requirements(
        self,
        difficulty: str,
        patient_behavior: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate task requirements."""
        context = context or {}
        behavior_config = self.config.patient_behaviors.get(
            patient_behavior,
            self.config.patient_behaviors["cooperative"]
        )

        elements_for_difficulty = self.config.get_elements_for_difficulty(difficulty)
        element_requirements = []
        for element in elements_for_difficulty:
            scenario = element.get_scenario_for_difficulty(difficulty)
            element_requirements.append({
                "element_id": element.element_id,
                "name": element.name,
                "scenario": scenario.get("scenario", ""),
                "patient_behavior": scenario.get("patient_behavior", ""),
                "evaluation_points": scenario.get("evaluation_points", []),
                "red_line_triggers": element.red_line_triggers
            })

        return {
            "module_id": self.config.module_id,
            "module_name": self.config.module_name,
            "difficulty": difficulty,
            "patient_behavior": patient_behavior,
            "elements": element_requirements,
            "patient_scenario": {
                "behavior_type": patient_behavior,
                "description": behavior_config.description,
                "triggers": behavior_config.triggers,
                "responses": behavior_config.responses
            },
            "red_lines": [rule.rule_id for rule in self.config.red_line_rules]
        }

    def generate_evaluation_criteria(
        self,
        task_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate evaluation criteria."""
        difficulty = task_requirements.get("difficulty", "L1")
        elements = task_requirements.get("elements", [])

        checklist = []
        for element in elements:
            for point in element.get("evaluation_points", []):
                checklist.append({
                    "check_id": f"{element['element_id']}_{point}",
                    "description": point,
                    "element_id": element["element_id"],
                    "weight": 1.0
                })

        min_completion = {"L1": 0.90, "L2": 0.80, "L3": 0.70}.get(difficulty, 0.80)

        return {
            "checklist": checklist,
            "scoring": {"min_checklist_completion": min_completion, "difficulty": difficulty},
            "pass_criteria": {
                "min_checklist_percentage": min_completion
            }
        }

    def check_red_line_violation(
        self,
        agent_response: str,
        task_context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """Check for red line violations."""
        violations = []

        for rule in self.config.red_line_rules:
            violation = rule.check_violation(agent_response, task_context)
            if violation:
                violations.append(violation)

        return violations


def create_insurance_guidance_module() -> InsuranceGuidance:
    """Factory function."""
    return InsuranceGuidance()
