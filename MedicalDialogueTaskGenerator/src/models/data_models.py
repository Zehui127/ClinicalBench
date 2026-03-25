"""
医学对话任务数据模型
Medical Dialogue Task Generator - Data Models

This module defines the core data structures for the medical dialogue task generator.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import json


class DifficultyLevel(Enum):
    """难度级别枚举"""
    L1 = "L1"  # 基础难度
    L2 = "L2"  # 中等难度
    L3 = "L3"  # 高难度


class ScenarioType(Enum):
    """场景类型枚举"""
    INFORMATION_QUERY = "INFORMATION_QUERY"
    SYMPTOM_ANALYSIS = "SYMPTOM_ANALYSIS"
    CHRONIC_MANAGEMENT = "CHRONIC_MANAGEMENT"
    MEDICATION_CONSULTATION = "MEDICATION_CONSULTATION"
    LIFESTYLE_ADVICE = "LIFESTYLE_ADVICE"
    EMERGENCY_CONCERN = "EMERGENCY_CONCERN"
    FOLLOW_UP = "FOLLOW_UP"
    SECOND_OPINION = "SECOND_OPINION"


class CooperationLevel(Enum):
    """患者配合度枚举"""
    GOOD = "good"
    PARTIAL = "partial"
    POOR = "poor"


class InformationQuality(Enum):
    """信息质量枚举"""
    GOOD = "good"
    MEDIUM = "medium"
    POOR = "poor"


class BehaviorType(Enum):
    """患者行为类型枚举"""
    WITHHOLDING = "withholding"
    LYING = "lying"
    CONTRADICTING = "contradicting"
    EMOTIONAL = "emotional"
    POOR_MEMORY = "poor_memory"
    LOW_KNOWLEDGE = "low_knowledge"


class EmotionalState(Enum):
    """情绪状态类型"""
    ANXIOUS = "anxious"
    FEARFUL = "fearful"
    ANGRY = "angry"
    PANICKED = "panicked"
    CALM = "calm"


class ContradictionType(Enum):
    """矛盾类型枚举"""
    PATIENT_VS_RECORD = "patient_vs_record"
    TIMELINE_INCONSISTENCY = "timeline_inconsistency"
    STATEMENT_CONTRADICTION = "statement_contradiction"


# ==================== 输入数据模型 ====================

@dataclass
class RawDialogueData:
    """原始医患对话数据"""
    id: str
    ticket: str  # 患者主诉
    known_info: str  # 患者提供的信息
    department_cn: str  # 科室
    source: str  # 数据来源
    original_title: str  # 原始标题
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "ticket": self.ticket,
            "known_info": self.known_info,
            "department_cn": self.department_cn,
            "source": self.source,
            "original_title": self.original_title,
            "metadata": self.metadata
        }


# ==================== 任务描述模型 ====================

@dataclass
class TaskDescription:
    """任务描述"""
    purpose: str
    relevant_policies: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "purpose": self.purpose,
            "relevant_policies": self.relevant_policies,
            "notes": self.notes
        }


@dataclass
class UserInstructions:
    """用户指令"""
    domain: str
    reason_for_call: str
    known_info: str
    unknown_info: Optional[str] = None
    task_instructions: str = ""
    original_known_info: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "reason_for_call": self.reason_for_call,
            "known_info": self.known_info,
            "unknown_info": self.unknown_info,
            "task_instructions": self.task_instructions,
            "original_known_info": self.original_known_info
        }


@dataclass
class UserScenario:
    """用户场景"""
    persona: str
    instructions: UserInstructions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona": self.persona,
            "instructions": self.instructions.to_dict() if isinstance(self.instructions, UserInstructions) else self.instructions
        }


@dataclass
class InitializationAction:
    """初始化动作"""
    env_type: str
    func_name: str
    arguments: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "env_type": self.env_type,
            "func_name": self.func_name,
            "arguments": self.arguments
        }


@dataclass
class InitialState:
    """初始状态"""
    initialization_actions: List[InitializationAction]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "initialization_actions": [
                action.to_dict() if isinstance(action, InitializationAction) else action
                for action in self.initialization_actions
            ]
        }


# ==================== 评估标准模型 ====================

@dataclass
class Action:
    """动作"""
    action_id: str
    requestor: str
    name: str
    arguments: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "requestor": self.requestor,
            "name": self.name,
            "arguments": self.arguments
        }


@dataclass
class CommunicationCheck:
    """通信检查"""
    check_id: str
    criteria: str
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "check_id": self.check_id,
            "criteria": self.criteria
        }
        if self.weight != 1.0:
            result["weight"] = self.weight
        return result


@dataclass
class EvaluationCriteria:
    """评估标准"""
    actions: List[Action]
    communication_checks: List[CommunicationCheck]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actions": [
                action.to_dict() if isinstance(action, Action) else action
                for action in self.actions
            ],
            "communication_checks": [
                check.to_dict() if isinstance(check, CommunicationCheck) else check
                for check in self.communication_checks
            ]
        }


# ==================== 患者行为模型 ====================

@dataclass
class PatientBehavior:
    """患者行为"""
    cooperation: str  # good, partial, poor
    behaviors: List[str]  # 行为类型列表
    information_quality: str  # good, medium, poor
    withholding: Optional[List[str]] = None  # 隐藏的信息类型
    contradictions: Optional[List[Dict[str, str]]] = None  # 矛盾类型列表
    emotional_state: Optional[Dict[str, Any]] = None  # 情绪状态
    knowledge_gaps: Optional[List[str]] = None  # 知识缺口
    memory_issues: Optional[List[str]] = None  # 记忆问题

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "cooperation": self.cooperation,
            "behaviors": self.behaviors,
            "information_quality": self.information_quality
        }
        if self.withholding:
            result["withholding"] = self.withholding
        if self.contradictions:
            result["contradictions"] = self.contradictions
        if self.emotional_state:
            result["emotional_state"] = self.emotional_state
        if self.knowledge_gaps:
            result["knowledge_gaps"] = self.knowledge_gaps
        if self.memory_issues:
            result["memory_issues"] = self.memory_issues
        return result


# ==================== 系统记录模型 ====================

@dataclass
class MedicationRecord:
    """用药记录"""
    name: str
    dose: str
    frequency: str
    start_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dose": self.dose,
            "frequency": self.frequency,
            "start_date": self.start_date
        }


@dataclass
class SystemRecords:
    """系统记录"""
    medications: Optional[List[MedicationRecord]] = None
    allergies: Optional[List[str]] = None
    conditions: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.medications:
            result["medications"] = [
                med.to_dict() if isinstance(med, MedicationRecord) else med
                for med in self.medications
            ]
        if self.allergies:
            result["allergies"] = self.allergies
        if self.conditions:
            result["conditions"] = self.conditions
        return result


# ==================== 对话流程模型 ====================

@dataclass
class ProgressiveDisclosure:
    """渐进式信息披露"""
    description: str
    rounds_until_truth: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "rounds_until_truth": self.rounds_until_truth
        }


@dataclass
class ConversationFlow:
    """对话流程"""
    expected_rounds: str
    unfolding_pattern: str
    progressive_disclosure: Optional[ProgressiveDisclosure] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "expected_rounds": self.expected_rounds,
            "unfolding_pattern": self.unfolding_pattern
        }
        if self.progressive_disclosure:
            result["progressive_disclosure"] = self.progressive_disclosure.to_dict()
        return result


# ==================== 问诊策略模型 ====================

@dataclass
class InquiryQuestion:
    """问诊问题"""
    question: str
    critical: bool = False
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "question": self.question
        }
        if self.critical:
            result["critical"] = True
        if self.reason:
            result["reason"] = self.reason
        return result


@dataclass
class InquiryChain:
    """问诊链"""
    purpose: str
    mandatory: bool
    questions: List[InquiryQuestion]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "purpose": self.purpose,
            "mandatory": self.mandatory,
            "questions": [
                q.to_dict() if isinstance(q, InquiryQuestion) else q
                for q in self.questions
            ]
        }


@dataclass
class InquiryStrategy:
    """问诊策略"""
    primary_diagnoses_to_rule_out: Optional[List[str]] = None
    inquiry_chains: Optional[List[InquiryChain]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.primary_diagnoses_to_rule_out:
            result["primary_diagnoses_to_rule_out"] = self.primary_diagnoses_to_rule_out
        if self.inquiry_chains:
            result["inquiry_chains"] = [
                chain.to_dict() if isinstance(chain, InquiryChain) else chain
                for chain in self.inquiry_chains
            ]
        return result


# ==================== 体检要求模型 ====================

@dataclass
class MandatoryCheck:
    """ mandatory检查 """
    check_type: str
    importance: str
    items: List[str]
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_type": self.check_type,
            "importance": self.importance,
            "items": self.items,
            "reason": self.reason
        }


@dataclass
class PhysicalExaminationRequirements:
    """体检要求"""
    mandatory_checks: List[MandatoryCheck]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mandatory_checks": [
                check.to_dict() if isinstance(check, MandatoryCheck) else check
                for check in self.mandatory_checks
            ]
        }


# ==================== 红线测试模型 ====================

@dataclass
class RedLineTest:
    """红线测试"""
    type: str
    trigger: str
    correct_behavior: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "trigger": self.trigger,
            "correct_behavior": self.correct_behavior
        }


# ==================== 患者画像模型 ====================

@dataclass
class Demographics:
    """人口统计信息"""
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    education: Optional[str] = None
    income_level: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "age": self.age,
            "gender": self.gender,
            "occupation": self.occupation,
            "education": self.education,
            "income_level": self.income_level
        }


@dataclass
class EmotionalSource:
    """情绪来源"""
    type: str
    description: str
    common_triggers: List[str]
    impact: str
    patient_statements: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "description": self.description,
            "common_triggers": self.common_triggers,
            "impact": self.impact,
            "patient_statements": self.patient_statements
        }


@dataclass
class EmotionalProfile:
    """情绪画像"""
    primary: str
    intensity: str
    sources: List[EmotionalSource]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary": self.primary,
            "intensity": self.intensity,
            "sources": [
                source.to_dict() if isinstance(source, EmotionalSource) else source
                for source in self.sources
            ]
        }


@dataclass
class SocialContext:
    """社会背景"""
    family_support: Optional[str] = None
    family_situation: Optional[str] = None
    caregiver_availability: Optional[str] = None
    social_support: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family_support": self.family_support,
            "family_situation": self.family_situation,
            "caregiver_availability": self.caregiver_availability,
            "social_support": self.social_support
        }


@dataclass
class HealthLiteracy:
    """健康素养"""
    level: str
    misconceptions: Optional[List[str]] = None
    information_sources: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "level": self.level
        }
        if self.misconceptions:
            result["misconceptions"] = self.misconceptions
        if self.information_sources:
            result["information_sources"] = self.information_sources
        return result


@dataclass
class PatientProfile:
    """患者画像"""
    demographics: Optional[Demographics] = None
    emotional_state: Optional[EmotionalProfile] = None
    social_context: Optional[SocialContext] = None
    health_literacy: Optional[HealthLiteracy] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.demographics:
            result["demographics"] = self.demographics.to_dict()
        if self.emotional_state:
            result["emotional_state"] = self.emotional_state.to_dict()
        if self.social_context:
            result["social_context"] = self.social_context.to_dict()
        if self.health_literacy:
            result["health_literacy"] = self.health_literacy.to_dict()
        return result


# ==================== 矛盾场景模型 ====================

@dataclass
class WithholdingBehavior:
    """隐瞒行为"""
    items: List[str]
    reasoning: str
    will_reveal_when: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": self.items,
            "reasoning": self.reasoning,
            "will_reveal_when": self.will_reveal_when
        }


@dataclass
class PatientBehaviorInScenario:
    """场景中的患者行为"""
    withholding: WithholdingBehavior

    def to_dict(self) -> Dict[str, Any]:
        return {
            "withholding": self.withholding.to_dict()
        }


@dataclass
class MustDoAction:
    """必须做的动作"""
    action: str
    criticality: str
    points: float
    failure_consequence: Optional[str] = None
    reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "action": self.action,
            "criticality": self.criticality,
            "points": self.points
        }
        if self.failure_consequence:
            result["failure_consequence"] = self.failure_consequence
        if self.reasoning:
            result["reasoning"] = self.reasoning
        return result


@dataclass
class MustNotDoAction:
    """不能做的动作"""
    action: str
    reason: str
    correct_approach: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "reason": self.reason,
            "correct_approach": self.correct_approach
        }


@dataclass
class ScoringBreakdown:
    """评分明细"""
    asks_medication: Optional[float] = None
    identifies_drug_issue: Optional[float] = None
    appropriate_recommendation: Optional[float] = None
    avoids_oversimplification: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.asks_medication is not None:
            result["asks_medication"] = self.asks_medication
        if self.identifies_drug_issue is not None:
            result["identifies_drug_issue"] = self.identifies_drug_issue
        if self.appropriate_recommendation is not None:
            result["appropriate_recommendation"] = self.appropriate_recommendation
        if self.avoids_oversimplification is not None:
            result["avoids_oversimplification"] = self.avoids_oversimplification
        return result


@dataclass
class Scoring:
    """评分"""
    points_available: float
    breakdown: Optional[ScoringBreakdown] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "points_available": self.points_available
        }
        if self.breakdown:
            result["breakdown"] = self.breakdown.to_dict()
        return result


@dataclass
class AgentEvaluationCriteria:
    """Agent评估标准"""
    must_do: List[MustDoAction]
    must_not_do: List[MustNotDoAction]
    scoring: Optional[Scoring] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "must_do": [
                action.to_dict() if isinstance(action, MustDoAction) else action
                for action in self.must_do
            ],
            "must_not_do": [
                action.to_dict() if isinstance(action, MustNotDoAction) else action
                for action in self.must_not_do
            ]
        }
        if self.scoring:
            result["scoring"] = self.scoring.to_dict()
        return result


@dataclass
class ContradictionScenario:
    """矛盾场景"""
    scenario_id: str
    design_purpose: str
    system_records: SystemRecords
    patient_behavior: PatientBehaviorInScenario
    agent_evaluation_criteria: AgentEvaluationCriteria

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "design_purpose": self.design_purpose,
            "system_records": self.system_records.to_dict(),
            "patient_behavior": self.patient_behavior.to_dict(),
            "agent_evaluation_criteria": self.agent_evaluation_criteria.to_dict()
        }


# ==================== 任务元数据模型 ====================

@dataclass
class TaskMetadata:
    """任务元数据"""
    source: str
    department_cn: str
    original_title: str
    scenario_type: str
    scenario_name: str
    scenario_confidence: int
    inquiry_requirements: Dict[str, Any]
    safety_rules: List[Dict[str, Any]]
    realistic_scenario: bool = True
    difficulty_level: str = "L1"
    version: str = "realistic_v3"
    patient_tags: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "source": self.source,
            "department_cn": self.department_cn,
            "original_title": self.original_title,
            "scenario_type": self.scenario_type,
            "scenario_name": self.scenario_name,
            "scenario_confidence": self.scenario_confidence,
            "inquiry_requirements": self.inquiry_requirements,
            "safety_rules": self.safety_rules,
            "realistic_scenario": self.realistic_scenario,
            "difficulty_level": self.difficulty_level,
            "version": self.version
        }
        if self.patient_tags:
            result["patient_tags"] = self.patient_tags
        return result


# ==================== 主任务模型 ====================

@dataclass
class MedicalDialogueTask:
    """医学对话评估任务"""
    id: str
    description: TaskDescription
    user_scenario: UserScenario
    ticket: str
    initial_state: InitialState
    evaluation_criteria: EvaluationCriteria
    metadata: TaskMetadata
    difficulty: str
    patient_behavior: PatientBehavior

    # 可选字段（L2+）
    system_records: Optional[SystemRecords] = None
    conversation_flow: Optional[ConversationFlow] = None
    inquiry_strategy: Optional[InquiryStrategy] = None
    physical_examination_requirements: Optional[PhysicalExaminationRequirements] = None
    physical_examination_findings: Optional[Dict[str, Any]] = None
    inquiry_approaches: Optional[Dict[str, Any]] = None

    # 可选字段（L3）
    red_line_tests: Optional[List[RedLineTest]] = None
    patient_profile: Optional[PatientProfile] = None
    contradiction_scenarios: Optional[List[ContradictionScenario]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（与tau2格式完全兼容）"""
        result = {
            "id": self.id,
            "description": self.description.to_dict() if isinstance(self.description, TaskDescription) else self.description,
            "user_scenario": self.user_scenario.to_dict() if isinstance(self.user_scenario, UserScenario) else self.user_scenario,
            "ticket": self.ticket,
            "initial_state": self.initial_state.to_dict() if isinstance(self.initial_state, InitialState) else self.initial_state,
            "evaluation_criteria": self.evaluation_criteria.to_dict() if isinstance(self.evaluation_criteria, EvaluationCriteria) else self.evaluation_criteria,
            "metadata": self.metadata.to_dict() if isinstance(self.metadata, TaskMetadata) else self.metadata,
            "difficulty": self.difficulty,
            "patient_behavior": self.patient_behavior.to_dict() if isinstance(self.patient_behavior, PatientBehavior) else self.patient_behavior
        }

        # 添加可选字段（L2+）
        if self.system_records:
            result["system_records"] = self.system_records.to_dict() if isinstance(self.system_records, SystemRecords) else self.system_records
        if self.conversation_flow:
            result["conversation_flow"] = self.conversation_flow.to_dict() if isinstance(self.conversation_flow, ConversationFlow) else self.conversation_flow
        if self.inquiry_strategy:
            result["inquiry_strategy"] = self.inquiry_strategy.to_dict() if isinstance(self.inquiry_strategy, InquiryStrategy) else self.inquiry_strategy
        if self.physical_examination_requirements:
            result["physical_examination_requirements"] = self.physical_examination_requirements.to_dict() if isinstance(self.physical_examination_requirements, PhysicalExaminationRequirements) else self.physical_examination_requirements
        if self.physical_examination_findings:
            result["physical_examination_findings"] = self.physical_examination_findings
        if self.inquiry_approaches:
            result["inquiry_approaches"] = self.inquiry_approaches

        # 添加可选字段（L3）
        if self.red_line_tests:
            result["red_line_tests"] = [
                test.to_dict() if isinstance(test, RedLineTest) else test
                for test in self.red_line_tests
            ]
        if self.patient_profile:
            result["patient_profile"] = self.patient_profile.to_dict() if isinstance(self.patient_profile, PatientProfile) else self.patient_profile
        if self.contradiction_scenarios:
            result["contradiction_scenarios"] = [
                scenario.to_dict() if isinstance(scenario, ContradictionScenario) else scenario
                for scenario in self.contradiction_scenarios
            ]

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MedicalDialogueTask':
        """从字典创建实例"""
        # 这里简化处理，实际使用时需要更完整的反序列化逻辑
        return cls(**data)
