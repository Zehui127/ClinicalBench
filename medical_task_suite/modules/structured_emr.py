"""
Module 6: Structured EMR (结构化病历生成能力)

This module tests the medical agent's ability to:
1. Organize patient information systematically
2. Repeat key information for verification
3. Clarify contradictions in patient's statements
"""

from typing import Dict, List, Any, Optional
from .base_module import (
    BaseModule, ModuleConfig, ModuleElement, RedLineRule,
    SeverityLevel, DifficultyLevel, PatientBehavior
)


class StructuredEMR(BaseModule):
    """
    Structured EMR Module - 结构化病历生成能力

    Tests whether the medical agent:
    - Systematically organizes patient information
    - Repeats key information for confirmation
    - Identifies and clarifies contradictions
    """

    def __init__(self, config: Optional[ModuleConfig] = None):
        """Initialize the Structured EMR module."""
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    def _create_default_config(self) -> ModuleConfig:
        """Create default module configuration."""
        red_line_rules = [
            RedLineRule(
                rule_id="copy_conflicting_info",
                name="照抄矛盾信息",
                description="直接照抄患者的混乱或矛盾表述，不进行澄清整理",
                severity=SeverityLevel.HIGH,
                trigger_conditions=[
                    "generating_emr",
                    "conflicting_info_present"
                ],
                detection_patterns=[
                    {
                        "keywords": [],
                        "context_requirements": ["no_clarification_attempt", "direct_copy_of_patient_words"]
                    }
                ],
                remediation="必须整理患者信息，发现并澄清矛盾，标注不确定的内容"
            )
        ]

        elements = [
            ModuleElement(
                element_id="organize_information",
                name="信息整理",
                description="系统整理患者提供的零散信息",
                difficulty_levels={
                    "L1": {
                        "scenario": "信息相对完整",
                        "patient_behavior": "cooperative",
                        "evaluation_points": ["分类整理", "按时间顺序", "突出关键"]
                    },
                    "L2": {
                        "scenario": "信息混乱",
                        "patient_behavior": "forgetful",
                        "evaluation_points": ["梳理逻辑", "归类整理", "标记缺失"]
                    },
                    "L3": {
                        "scenario": "信息矛盾",
                        "patient_behavior": "concealing",
                        "evaluation_points": ["发现矛盾", "澄清问题", "标注不确定"]
                    }
                },
                evaluation_criteria={"check_id": "information_organization", "weight": 1.5},
                red_line_triggers=["照抄患者混乱表述", "不整理就生成病历"]
            ),
            ModuleElement(
                element_id="repeat_key_info",
                name="关键信息复述",
                description="向患者复述关键信息确认准确性",
                difficulty_levels={
                    "L1": {
                        "scenario": "信息清楚",
                        "patient_behavior": "cooperative",
                        "evaluation_points": ["复述关键信息", "确认准确性", "给患者纠正机会"]
                    },
                    "L2": {
                        "scenario": "信息复杂",
                        "patient_behavior": "forgetful",
                        "evaluation_points": ["分项复述", "逐项确认", "询问补充"]
                    },
                    "L3": {
                        "scenario": "患者表述矛盾",
                        "patient_behavior": "concealing",
                        "evaluation_points": ["指出矛盾", "要求澄清", "不擅自决定"]
                    }
                },
                evaluation_criteria={"check_id": "key_info_repetition", "weight": 1.4},
                red_line_triggers=["不复述关键信息", "不确认就直接记录"]
            ),
            ModuleElement(
                element_id="clarify_contradictions",
                name="澄清矛盾",
                description="发现并澄清患者表述中的矛盾",
                difficulty_levels={
                    "L1": {
                        "scenario": "明显矛盾",
                        "patient_behavior": "cooperative",
                        "evaluation_points": ["发现矛盾", "指出问题", "要求澄清"]
                    },
                    "L2": {
                        "scenario": "隐含矛盾",
                        "patient_behavior": "forgetful",
                        "evaluation_points": ["识别矛盾", "温和询问", "帮助回忆"]
                    },
                    "L3": {
                        "scenario": "患者坚持矛盾表述",
                        "patient_behavior": "concealing",
                        "evaluation_points": ["坚持澄清", "标记矛盾", "不盲目记录"]
                    }
                },
                evaluation_criteria={"check_id": "contradiction_clarification", "weight": 1.6},
                red_line_triggers=["忽视矛盾信息", "把矛盾信息都记下来"]
            )
        ]

        patient_behaviors = {
            "cooperative": PatientBehavior(
                behavior_type="cooperative",
                difficulty_level="L1",
                description="信息相对完整，逻辑较清晰，配合澄清",
                triggers=["医生总结信息", "医生询问细节"],
                responses={
                    "summary": ["我对的，就是这样", "没什么问题"],
                    "clarification": ["没错，就是这样"]
                },
                expected_agent_responses=["系统性问诊", "建议必要的检查", "给出明确治疗建议"]
            ),
            "forgetful": PatientBehavior(
                behavior_type="forgetful",
                difficulty_level="L2",
                description="表述混乱，时间顺序错，丢三落四",
                triggers=["医生总结信息", "医生询问时间"],
                responses={
                    "summary": ["我先说了什么来着", "好像是这样的", "我搞混了"],
                    "clarification": ["我不太确定", "大概是吧"]
                },
                expected_agent_responses=["梳理逻辑", "帮助回忆", "分项确认"]
            ),
            "concealing": PatientBehavior(
                behavior_type="concealing",
                difficulty_level="L3",
                description="前后矛盾，刻意隐瞒，误导医生",
                triggers=["医生指出矛盾", "医生澄清信息"],
                responses={
                    "summary": ["我刚才不是说过了吗", "就是对你听到的"],
                    "clarification": ["我没那么说过", "你记错了"]
                },
                expected_agent_responses=["发现矛盾", "指出问题", "要求澄清"]
            )
        }

        return ModuleConfig(
            module_id="module_06",
            module_name="结构化病历生成能力",
            description="测试医疗代理整理患者信息、生成结构化病历的能力",
            elements=elements,
            difficulty_distribution={"L1": 0.35, "L2": 0.40, "L3": 0.25},
            red_line_rules=red_line_rules,
            patient_behaviors=patient_behaviors,
            metadata={
                "priority": "P1",
                "coverage_weight": 1.3,
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
            {"check_id": "check_organization", "description": "检查信息是否整理", "severity": "high"}
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


def create_structured_emr_module() -> StructuredEMR:
    """Factory function."""
    return StructuredEMR()
