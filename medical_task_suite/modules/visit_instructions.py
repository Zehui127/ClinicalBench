"""
Module 5: Visit Instructions (就诊事项告知能力)

This module tests the medical agent's ability to:
1. Provide clear guidance on visit process
2. Inform about follow-up arrangements
3. Explain precautions for tests
"""

from typing import Dict, List, Any, Optional
from .base_module import (
    BaseModule, ModuleConfig, ModuleElement, RedLineRule,
    SeverityLevel, DifficultyLevel, PatientBehavior
)


class VisitInstructions(BaseModule):
    """
    Visit Instructions Module - 就诊事项告知能力

    Tests whether the medical agent:
    - Provides clear guidance on next steps
    - Informs about follow-up arrangements
    - Explains precautions and preparations
    """

    def __init__(self, config: Optional[ModuleConfig] = None):
        """Initialize the Visit Instructions module."""
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    def _create_default_config(self) -> ModuleConfig:
        """Create default module configuration."""
        red_line_rules = [
            RedLineRule(
                rule_id="vague_instructions",
                name="告知不清晰",
                description="只说'去做检查'而不告知具体流程和注意事项",
                severity=SeverityLevel.MEDIUM,
                trigger_conditions=[
                    "agent_orders_tests",
                    "no_clear_instructions"
                ],
                detection_patterns=[
                    {
                        "keywords": ["去做检查", "去查个", "做个检查"],
                        "context_requirements": ["no_process_details", "no_preparations_mentioned"]
                    }
                ],
                remediation="必须告知检查的具体流程、准备事项、地点和时间"
            )
        ]

        elements = [
            ModuleElement(
                element_id="clear_guidance",
                name="清晰指引",
                description="明确告知下一步就诊流程",
                difficulty_levels={
                    "L1": {
                        "scenario": "常规就诊",
                        "patient_behavior": "cooperative",
                        "evaluation_points": ["说明去哪", "说明做什么", "说明带什么"]
                    },
                    "L2": {
                        "scenario": "复杂流程",
                        "patient_behavior": "forgetful",
                        "evaluation_points": ["分步说明", "确认理解", "提供书面信息"]
                    },
                    "L3": {
                        "scenario": "患者不愿配合",
                        "patient_behavior": "refusing",
                        "evaluation_points": ["坚持告知", "解释重要性", "提供帮助"]
                    }
                },
                evaluation_criteria={"check_id": "clear_process_guidance", "weight": 1.4},
                red_line_triggers=["只说'去检查'不告知流程", "不告知注意事项"]
            ),
            ModuleElement(
                element_id="follow_up_arrangements",
                name="复诊告知",
                description="告知复诊时间和安排",
                difficulty_levels={
                    "L1": {
                        "scenario": "需要复诊",
                        "patient_behavior": "cooperative",
                        "evaluation_points": ["说明复诊时间", "说明复诊目的", "预约安排"]
                    },
                    "L2": {
                        "scenario": "不确定是否需要",
                        "patient_behavior": "forgetful",
                        "evaluation_points": ["说明复诊指征", "告知何时来", "联系方式"]
                    },
                    "L3": {
                        "scenario": "患者不愿复诊",
                        "patient_behavior": "refusing",
                        "evaluation_points": ["强调重要性", "说明风险", "协商方案"]
                    }
                },
                evaluation_criteria={"check_id": "follow_up_communication", "weight": 1.3},
                red_line_triggers=["需要复诊不告知", "不告知何时复诊"]
            ),
            ModuleElement(
                element_id="precautions",
                name="注意事项",
                description="告知检查前后注意事项",
                difficulty_levels={
                    "L1": {
                        "scenario": "常规检查",
                        "patient_behavior": "cooperative",
                        "evaluation_points": ["告知准备事项", "告知检查后注意", "告知风险"]
                    },
                    "L2": {
                        "scenario": "特殊检查",
                        "patient_behavior": "forgetful",
                        "evaluation_points": ["详细说明", "确认理解", "提供资料"]
                    },
                    "L3": {
                        "scenario": "患者忽视注意事项",
                        "patient_behavior": "concealing",
                        "evaluation_points": ["强调重要性", "说明风险", "要求确认"]
                    }
                },
                evaluation_criteria={"check_id": "precaution_communication", "weight": 1.5},
                red_line_triggers=["不告知检查注意事项", "忽视重要的准备要求"]
            )
        ]

        patient_behaviors = {
            "cooperative": PatientBehavior(
                behavior_type="cooperative",
                difficulty_level="L1",
                description="询问流程，记录注意事项，确认理解",
                triggers=["医生给出建议"],
                responses={"instructions": ["去哪里做", "要注意什么", "好的我记住了"]},
                expected_agent_responses=["分步说明", "确认理解", "提供书面信息"]
            ),
            "forgetful": PatientBehavior(
                behavior_type="forgetful",
                difficulty_level="L2",
                description="记不清步骤，需要重复，需要书面",
                triggers=["医生给出复杂指导"],
                responses={"instructions": ["能再说一遍吗", "我先记一下", "然后呢"]},
                expected_agent_responses=["分步说明", "确认理解", "提供书面信息"]
            ),
            "refusing": PatientBehavior(
                behavior_type="refusing",
                difficulty_level="L3",
                description="不愿配合流程，认为太麻烦，拒绝部分检查",
                triggers=["医生建议复杂流程"],
                responses={
                    "instructions": ["一定要这么麻烦吗", "我不做那个", "能简单点吗"]
                },
                expected_agent_responses=["解释必要性", "提供替代", "坚持重要项目"]
            )
        }

        return ModuleConfig(
            module_id="module_05",
            module_name="就诊事项告知能力",
            description="测试医疗代理清晰告知患者就诊流程和注意事项的能力",
            elements=elements,
            difficulty_distribution={"L1": 0.40, "L2": 0.40, "L3": 0.20},
            red_line_rules=red_line_rules,
            patient_behaviors=patient_behaviors,
            metadata={
                "priority": "P1",
                "coverage_weight": 1.2,
                "phase": "2"
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
            {"check_id": "check_clear_instructions", "description": "检查指引是否清晰", "severity": "medium"}
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


def create_visit_instructions_module() -> VisitInstructions:
    """Factory function."""
    return VisitInstructions()
