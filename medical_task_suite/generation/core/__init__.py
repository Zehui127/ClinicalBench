"""
核心模块 - KGGenerator核心功能
Core Modules - KGGenerator Core Functionality
"""

from .kg_loader import PrimeKGLoader
from .random_walk import (
    PrimeKGRandomWalkPipeline,
    ConsultationTask,
    WalkPath,
    PrimeKGAdapter,
)
from .random_walk import MultiPathWalkGenerator, MultiPathWalkResult, WalkState
from .task_generator import KGTaskGenerator

# 新增复杂任务生成组件
try:
    from .comorbidity_engine import ComorbidityEngine, ComorbidityInfo
    from .dialogue_builder import (
        BehaviorAwareDialogueBuilder,
        ComplexConsultationTask,
        DialoguePhase,
        BehaviorType,
        DifficultyLevel,
    )
    COMPLEX_GENERATION_AVAILABLE = True
except ImportError:
    COMPLEX_GENERATION_AVAILABLE = False
    ComorbidityEngine = None
    ComorbidityInfo = None
    BehaviorAwareDialogueBuilder = None
    ComplexConsultationTask = None
    DialoguePhase = None
    BehaviorType = None
    DifficultyLevel = None

# Enhanced components for structured persona, tool-aware generation, symptom mapping
try:
    from .persona_generator import (
        PersonaGenerator, StructuredMedicalPersona, SymptomSlot,
        InformationSharingStrategy, SharingMode, ClinicalSignificance,
    )
    from .tool_aware_generator import (
        ToolAwareTaskGenerator, TaskSuccessCriteria, ToolCategory,
    )
    from .symptom_mapper import EnhancedSymptomMapper, EnhancedSymptom
    ENHANCED_GENERATION_AVAILABLE = True
except ImportError:
    ENHANCED_GENERATION_AVAILABLE = False
    PersonaGenerator = None
    StructuredMedicalPersona = None
    SymptomSlot = None
    InformationSharingStrategy = None
    SharingMode = None
    ClinicalSignificance = None
    ToolAwareTaskGenerator = None
    TaskSuccessCriteria = None
    ToolCategory = None
    EnhancedSymptomMapper = None
    EnhancedSymptom = None

__all__ = [
    'PrimeKGLoader',
    'PrimeKGRandomWalkPipeline',
    'ConsultationTask',
    'WalkPath',
    'MultiPathWalkGenerator',
    'MultiPathWalkResult',
    'WalkState',
    'PrimeKGAdapter',
    'KGTaskGenerator',
    'COMPLEX_GENERATION_AVAILABLE',
    'ENHANCED_GENERATION_AVAILABLE',
    'ComorbidityEngine',
    'ComorbidityInfo',
    'BehaviorAwareDialogueBuilder',
    'ComplexConsultationTask',
    'DialoguePhase',
    'BehaviorType',
    'DifficultyLevel',
    'PersonaGenerator',
    'StructuredMedicalPersona',
    'ToolAwareTaskGenerator',
    'TaskSuccessCriteria',
    'ToolCategory',
    'EnhancedSymptomMapper',
]
