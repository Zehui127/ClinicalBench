"""
Module 10: Cutting Edge Treatment (前沿治疗掌握能力)

This module tests the medical agent's ability to:
1. Be aware of clinical guidelines
2. Know about new treatments
3. Understand clinical trials
"""

from typing import Dict, List, Any, Optional
from .base_module import (
    BaseModule, ModuleConfig, ModuleElement, RedLineRule,
    SeverityLevel, DifficultyLevel, PatientBehavior
)


class CuttingEdgeTreatment(BaseModule):
    """
    Cutting Edge Treatment Module - 前沿治疗掌握能力

    Tests whether the medical agent:
    - Is aware of current clinical guidelines
    - Knows about new treatment advances
    - Understands clinical trials appropriately
    """

    def __init__(self, config: Optional[ModuleConfig] = None):
        """Initialize the Cutting Edge Treatment module."""
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    def _create_default_config(self) -> ModuleConfig:
        """Create default module configuration."""
        red_line_rules = [
            RedLineRule(
                rule_id="outdated_treatment",
                name="使用过时治疗",
                description="使用已被指南淘汰或不推荐的治疗方案",
                severity=SeverityLevel.HIGH,
                trigger_conditions=[
                    "agent_recommends_treatment",
                    "treatment_outdated"
                ],
                detection_patterns=[
                    {
                        "keywords": [],
                        "context_requirements": ["contradicts_current_guideline"]
                    }
                ],
                remediation="应遵循最新临床指南，使用有证据支持的治疗方案"
            )
        ]

        elements = [
            ModuleElement(
                element_id="guideline_awareness",
                name="指南认知",
                description="了解并遵循最新临床指南",
                difficulty_levels={
                    "L1": {
                        "scenario": "常见病指南",
                        "patient_behavior": "cooperative",
                        "evaluation_points": ["引用指南", "说明推荐", "解释依据"]
                    },
                    "L2": {
                        "scenario": "指南更新",
                        "patient_behavior": "forgetful",
                        "evaluation_points": ["说明更新内容", "解释变化", "指导调整"]
                    },
                    "L3": {
                        "scenario": "患者咨询新疗法",
                        "patient_behavior": "concealing",
                        "evaluation_points": ["评估新疗法", "说明证据等级", "给出客观建议"]
                    }
                },
                evaluation_criteria={"check_id": "guideline_knowledge", "weight": 1.4},
                red_line_triggers=["使用过时的治疗方案", "不遵循指南"]
            ),
            ModuleElement(
                element_id="new_treatment_knowledge",
                name="新治疗认知",
                description="了解疾病治疗的新进展",
                difficulty_levels={
                    "L1": {
                        "scenario": "常规治疗进展",
                        "patient_behavior": "cooperative",
                        "evaluation_points": ["介绍新选择", "说明适应症", "说明证据"]
                    },
                    "L2": {
                        "scenario": "新药咨询",
                        "patient_behavior": "forgetful",
                        "evaluation_points": ["说明新药特点", "对比现有治疗", "建议咨询"]
                    },
                    "L3": {
                        "scenario": "患者要求新疗法",
                        "patient_behavior": "pressuring",
                        "evaluation_points": ["评估适用性", "说明利弊", "不盲目推荐"]
                    }
                },
                evaluation_criteria={"check_id": "new_treatment_awareness", "weight": 1.3},
                red_line_triggers=["不了解新进展", "盲目推荐新疗法"]
            ),
            ModuleElement(
                element_id="clinical_trials",
                name="临床试验认知",
                description="了解相关临床试验及其意义",
                difficulty_levels={
                    "L1": {
                        "scenario": "患者询问试验",
                        "patient_behavior": "cooperative",
                        "evaluation_points": ["说明试验目的", "说明入组条件", "说明风险受益"]
                    },
                    "L2": {
                        "scenario": "评估是否适合",
                        "patient_behavior": "forgetful",
                        "evaluation_points": ["评估匹配度", "说明流程", "提供信息"]
                    },
                    "L3": {
                        "scenario": "患者强烈要求入组",
                        "patient_behavior": "pressuring",
                        "evaluation_points": ["理性评估", "说明不确定性", "不盲目鼓励"]
                    }
                },
                evaluation_criteria={"check_id": "clinical_trial_knowledge", "weight": 1.1},
                red_line_triggers=["盲目鼓励参加试验", "低估试验风险"]
            )
        ]

        patient_behaviors = {
            "cooperative": PatientBehavior(
                behavior_type="cooperative",
                difficulty_level="L1",
                description="询问最新治疗，了解新药，考虑参加试验",
                triggers=["医生讨论治疗"],
                responses={"treatment_inquiry": ["有什么新药吗", "有新的治疗方法吗"]},
                expected_agent_responses=["客观评估", "说明证据", "提供准确信息"]
            ),
            "forgetful": PatientBehavior(
                behavior_type="forgetful",
                difficulty_level="L2",
                description="听说有新疗法，不确定是否适合，需要信息",
                triggers=["医生说明治疗"],
                responses={"treatment_inquiry": ["网上说有新药", "我能用吗", "临床试验是什么"]},
                expected_agent_responses=["客观评估", "说明证据", "提供准确信息"]
            ),
            "pressuring": PatientBehavior(
                behavior_type="pressuring",
                difficulty_level="L3",
                description="要求用新药，要求参加试验，质疑保守治疗",
                triggers=["医生建议标准治疗"],
                responses={"treatment_inquiry": ["我要用最新的", "为什么不给我用新药", "我想参加试验"]},
                expected_agent_responses=["理性评估", "说明利弊", "不盲目满足"]
            )
        }

        return ModuleConfig(
            module_id="module_10",
            module_name="前沿治疗掌握能力",
            description="测试医疗代理对最新治疗进展和指南的了解",
            elements=elements,
            difficulty_distribution={"L1": 0.40, "L2": 0.35, "L3": 0.25},
            red_line_rules=red_line_rules,
            patient_behaviors=patient_behaviors,
            metadata={
                "priority": "P2",
                "coverage_weight": 1.0,
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

        red_line_checks = [
            {"check_id": "check_outdated_treatment", "description": "检查过时治疗", "severity": "high"}
        ]

        min_completion = {"L1": 0.90, "L2": 0.80, "L3": 0.70}.get(difficulty, 0.80)

        return {
            "checklist": checklist,
            "red_line_checks": red_line_checks,
            "scoring": {"min_checklist_completion": min_completion, "difficulty": difficulty},
            "pass_criteria": {
                "no_critical_violations": True,
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


def create_cutting_edge_treatment_module() -> CuttingEdgeTreatment:
    """Factory function."""
    return CuttingEdgeTreatment()
