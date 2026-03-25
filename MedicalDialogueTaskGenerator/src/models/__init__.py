"""
数据模型包初始化
Medical Dialogue Task Generator - Models Package
"""

from .data_models import (
    # 枚举类型
    DifficultyLevel,
    ScenarioType,
    CooperationLevel,
    InformationQuality,
    BehaviorType,
    EmotionalState,
    ContradictionType,

    # 输入数据模型
    RawDialogueData,

    # 任务描述模型
    TaskDescription,
    UserInstructions,
    UserScenario,
    InitializationAction,
    InitialState,

    # 评估标准模型
    Action,
    CommunicationCheck,
    EvaluationCriteria,

    # 患者行为模型
    PatientBehavior,

    # 系统记录模型
    MedicationRecord,
    SystemRecords,

    # 对话流程模型
    ProgressiveDisclosure,
    ConversationFlow,

    # 问诊策略模型
    InquiryQuestion,
    InquiryChain,
    InquiryStrategy,

    # 体检要求模型
    MandatoryCheck,
    PhysicalExaminationRequirements,

    # 红线测试模型
    RedLineTest,

    # 患者画像模型
    Demographics,
    EmotionalSource,
    EmotionalProfile,
    SocialContext,
    HealthLiteracy,
    PatientProfile,

    # 矛盾场景模型
    WithholdingBehavior,
    PatientBehaviorInScenario,
    MustDoAction,
    MustNotDoAction,
    ScoringBreakdown,
    Scoring,
    AgentEvaluationCriteria,
    ContradictionScenario,

    # 任务元数据模型
    TaskMetadata,

    # 主任务模型
    MedicalDialogueTask,
)

__all__ = [
    # 枚举类型
    "DifficultyLevel",
    "ScenarioType",
    "CooperationLevel",
    "InformationQuality",
    "BehaviorType",
    "EmotionalState",
    "ContradictionType",

    # 输入数据模型
    "RawDialogueData",

    # 任务描述模型
    "TaskDescription",
    "UserInstructions",
    "UserScenario",
    "InitializationAction",
    "InitialState",

    # 评估标准模型
    "Action",
    "CommunicationCheck",
    "EvaluationCriteria",

    # 患者行为模型
    "PatientBehavior",

    # 系统记录模型
    "MedicationRecord",
    "SystemRecords",

    # 对话流程模型
    "ProgressiveDisclosure",
    "ConversationFlow",

    # 问诊策略模型
    "InquiryQuestion",
    "InquiryChain",
    "InquiryStrategy",

    # 体检要求模型
    "MandatoryCheck",
    "PhysicalExaminationRequirements",

    # 红线测试模型
    "RedLineTest",

    # 患者画像模型
    "Demographics",
    "EmotionalSource",
    "EmotionalProfile",
    "SocialContext",
    "HealthLiteracy",
    "PatientProfile",

    # 矛盾场景模型
    "WithholdingBehavior",
    "PatientBehaviorInScenario",
    "MustDoAction",
    "MustNotDoAction",
    "ScoringBreakdown",
    "Scoring",
    "AgentEvaluationCriteria",
    "ContradictionScenario",

    # 任务元数据模型
    "TaskMetadata",

    # 主任务模型
    "MedicalDialogueTask",
]
