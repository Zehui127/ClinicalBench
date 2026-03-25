"""
Medical Task Suite - 13 Core Modules + Advanced Features

This package implements 13 core medical capability modules for comprehensive
medical agent evaluation, plus advanced features for production deployment.

Core Modules (13):
1. Lab Test Inquiry (检验检查调阅)
2. Hallucination-Free Diagnosis (无幻觉诊断)
3. Medication Guidance (用药指导)
4. Differential Diagnosis (鉴别诊断)
5. Visit Instructions (就诊事项告知)
6. Structured EMR (结构化病历生成)
7. History Verification (病史核实)
8. Lab Analysis (检验指标分析)
9. TCM Cognitive (中医药认知)
10. Cutting Edge Treatment (前沿治疗掌握)
11. Insurance Guidance (医保政策指导)
12. Multimodal Understanding (多模态感知)
13. Emergency Handling (紧急情况处置)

Advanced Features:
- Temporal Consistency Verification (时序一致性校验)
- Execution Chain Annotation (执行链标注)
- Adversarial Test Suite (对抗性测试集)
- Cross-Session Memory (跨会话记忆)
"""

from .base_module import (
    BaseModule, ModuleConfig, ModuleElement,
    RedLineRule, SeverityLevel, DifficultyLevel, PatientBehavior
)

# Phase 2 Modules (Implemented)
from .lab_test_inquiry import LabTestInquiry, create_lab_test_inquiry_module
from .hallucination_free_diag import HallucinationFreeDiagnosis, create_hallucination_free_diagnosis_module
from .medication_guidance import MedicationGuidance, create_medication_guidance_module
from .differential_diag import DifferentialDiagnosis, create_differential_diagnosis_module
from .visit_instructions import VisitInstructions, create_visit_instructions_module
from .structured_emr import StructuredEMR, create_structured_emr_module

# Phase 3 Modules (Implemented)
from .history_verification import HistoryVerification, create_history_verification_module
from .lab_analysis import LabAnalysis, create_lab_analysis_module
from .tcm_cognitive import TCMCognitive, create_tcm_cognitive_module
from .cutting_edge_tx import CuttingEdgeTreatment, create_cutting_edge_treatment_module
from .insurance_guidance import InsuranceGuidance, create_insurance_guidance_module
from .emergency_handling import EmergencyHandling, create_emergency_handling_module

# Phase 4 Modules (Implemented)
from .multimodal_understanding import MultimodalUnderstanding, create_multimodal_understanding_module

__all__ = [
    # Base classes
    'BaseModule', 'ModuleConfig', 'ModuleElement',
    'RedLineRule', 'SeverityLevel', 'DifficultyLevel', 'PatientBehavior',

    # Implemented modules (Phase 2)
    'LabTestInquiry', 'create_lab_test_inquiry_module',
    'HallucinationFreeDiagnosis', 'create_hallucination_free_diagnosis_module',
    'MedicationGuidance', 'create_medication_guidance_module',
    'DifferentialDiagnosis', 'create_differential_diagnosis_module',
    'VisitInstructions', 'create_visit_instructions_module',
    'StructuredEMR', 'create_structured_emr_module',

    # Implemented modules (Phase 3)
    'HistoryVerification', 'create_history_verification_module',
    'LabAnalysis', 'create_lab_analysis_module',
    'TCMCognitive', 'create_tcm_cognitive_module',
    'CuttingEdgeTreatment', 'create_cutting_edge_treatment_module',
    'InsuranceGuidance', 'create_insurance_guidance_module',
    'EmergencyHandling', 'create_emergency_handling_module',

    # Implemented modules (Phase 4)
    'MultimodalUnderstanding', 'create_multimodal_understanding_module',
]

# Module registry for easy access
MODULE_REGISTRY = {
    'module_01': {
        'class': LabTestInquiry,
        'factory': create_lab_test_inquiry_module,
        'name': '检验检查调阅能力',
        'priority': 'P0'
    },
    'module_02': {
        'class': HallucinationFreeDiagnosis,
        'factory': create_hallucination_free_diagnosis_module,
        'name': '无幻觉诊断能力',
        'priority': 'P0'
    },
    'module_03': {
        'class': MedicationGuidance,
        'factory': create_medication_guidance_module,
        'name': '用药指导能力',
        'priority': 'P0'
    },
    'module_04': {
        'class': DifferentialDiagnosis,
        'factory': create_differential_diagnosis_module,
        'name': '鉴别诊断能力',
        'priority': 'P0'
    },
    'module_05': {
        'class': VisitInstructions,
        'factory': create_visit_instructions_module,
        'name': '就诊事项告知能力',
        'priority': 'P1'
    },
    'module_06': {
        'class': StructuredEMR,
        'factory': create_structured_emr_module,
        'name': '结构化病历生成能力',
        'priority': 'P1'
    },
    'module_07': {
        'class': HistoryVerification,
        'factory': create_history_verification_module,
        'name': '病史核实能力',
        'priority': 'P1'
    },
    'module_08': {
        'class': LabAnalysis,
        'factory': create_lab_analysis_module,
        'name': '检验指标分析能力',
        'priority': 'P1'
    },
    'module_09': {
        'class': TCMCognitive,
        'factory': create_tcm_cognitive_module,
        'name': '中医药认知能力',
        'priority': 'P2'
    },
    'module_10': {
        'class': CuttingEdgeTreatment,
        'factory': create_cutting_edge_treatment_module,
        'name': '前沿治疗掌握能力',
        'priority': 'P2'
    },
    'module_11': {
        'class': InsuranceGuidance,
        'factory': create_insurance_guidance_module,
        'name': '医保政策指导能力',
        'priority': 'P2'
    },
    'module_13': {
        'class': EmergencyHandling,
        'factory': create_emergency_handling_module,
        'name': '紧急情况识别与处置能力',
        'priority': 'P0'
    },
    'module_12': {
        'class': MultimodalUnderstanding,
        'factory': create_multimodal_understanding_module,
        'name': '多模态感知与理解能力',
        'priority': 'P3'
    },
}
