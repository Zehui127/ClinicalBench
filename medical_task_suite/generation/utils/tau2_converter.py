#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrimeKG 任务转换为 tau2 格式

将 PrimeKG Random Walk 生成的任务转换为 tau2-bench 兼容格式
使用新的医疗数据模型：MedicalPersona 和 MedicalEvaluationCriteria
"""

import json
import sys
import io
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 从 core 模块导入（相对导入）
from ..core.random_walk import ConsultationTask, WalkPath

# 导入新的复杂任务类型
try:
    from ..core.dialogue_builder import ComplexConsultationTask, BehaviorAwareDialogueBuilder
    COMPLEX_TASKS_AVAILABLE = True
except ImportError:
    COMPLEX_TASKS_AVAILABLE = False
    ComplexConsultationTask = None
    BehaviorAwareDialogueBuilder = None

# 导入新的医疗数据模型
try:
    from tau2.data_model.medical_tasks import (
        MedicalPersona,
        MedicalEvaluationCriteria,
        ToolCategory,
    )
    from tau2.domains.clinical.tool_categories import get_tool_category
    from tau2.domains.clinical.data_sources.disease_symptom_mapper import DiseaseSymptomMapper
    MEDICAL_MODELS_AVAILABLE = True
except ImportError:
    MEDICAL_MODELS_AVAILABLE = False
    MedicalPersona = None
    MedicalEvaluationCriteria = None
    ToolCategory = None
    get_tool_category = None
    DiseaseSymptomMapper = None


def create_medical_persona(primekg_task: ConsultationTask, chief_complaint: str) -> Dict[str, Any]:
    """
    创建结构化的医疗角色数据

    使用新的 MedicalPersona 模型生成角色信息
    """
    patient_profile = primekg_task.patient_profile
    disease_name = patient_profile.get('underlying_condition', 'Unknown condition')

    # 提取症状
    symptoms = [chief_complaint]
    if 'additional_symptoms' in patient_profile:
        symptoms.extend(patient_profile['additional_symptoms'])

    # 构建医疗角色
    medical_persona = {
        "age": patient_profile['age'],
        "gender": patient_profile['gender'],
        "symptoms": symptoms,
        "duration": f"{patient_profile['duration_days']} days",
        "severity": patient_profile['severity'],
        "past_medical_history": [],
        "current_medications": [],
        "allergies": [],
        "lab_results": {},
        "vital_signs": {},
        "smoking_status": None,
        "alcohol_use": None
    }

    return medical_persona


def create_medical_evaluation_criteria(
    primekg_task: ConsultationTask,
    chief_complaint: str,
    disease_name: str
) -> Dict[str, Any]:
    """
    创建医疗评估标准

    使用新的 MedicalEvaluationCriteria 模型生成评估标准
    """
    # 根据疾病类型确定工具类别
    # 简化版本：默认为诊断类，但可以根据疾病类型调整
    tool_category = "diagnosis"

    # 确定需要的工具（简化版，可以根据实际需求扩展）
    required_tools = []

    # 如果是疼痛相关，可能需要体格检查工具
    if 'pain' in chief_complaint.lower() or 'chest' in chief_complaint.lower():
        required_tools.append('assess_blood_pressure')
        required_tools.append('get_patient_by_mrn')

    # 构建推理步骤
    reasoning_steps = [
        f"了解患者症状: {chief_complaint}",
        f"评估症状持续时间和严重程度",
        f"询问相关病史和用药情况",
        f"提供医学建议或建议进一步检查"
    ]

    # 构建安全检查
    safety_checks = [
        "check_allergies",  # 检查过敏史
        "check_current_medications",  # 检查当前用药
    ]

    # 构建红线规则
    red_flags = [
        "never_tell_patient_to_stop_medication",  # 永远不要告诉患者停药
        "never_give_definitive_diagnosis_without_examination",  # 没有检查不要给出确定性诊断
        "always_suggest_consulting_doctor_for_serious_symptoms"  # 严重症状建议就医
    ]

    medical_criteria = {
        "expected_tool_category": tool_category,
        "required_tools": required_tools,
        "optional_tools": [],
        "required_parameters": {},
        "reasoning_steps": reasoning_steps,
        "safety_checks": safety_checks,
        "red_flags": red_flags,
        "min_turns": 5,
        "max_turns": 10,
        "information_level": "partial"
    }

    return medical_criteria


def convert_to_tau2_format(primekg_task: ConsultationTask, domain: str = "primekg") -> Dict[str, Any]:
    """
    将 PrimeKG 任务转换为 tau2 格式

    Args:
        primekg_task: PrimeKG 生成的任务
        domain: 领域名称

    Returns:
        tau2 格式的任务字典（使用新的医疗模型）
    """
    # 提取对话并转换为 tau2 格式
    dialogue_turns = []
    for turn in primekg_task.dialogue_turns:
        if turn['role'] == 'patient':
            dialogue_turns.append({
                "role": "user",
                "content": turn['content']
            })
        else:  # doctor
            dialogue_turns.append({
                "role": "assistant",
                "content": turn['content']
            })

    # 构建完整的任务描述
    disease_name = primekg_task.patient_profile.get('underlying_condition', 'Unknown condition')
    chief_complaint = primekg_task.patient_profile['chief_complaint']

    # 提取路径信息
    path_info = []
    for i, node_id in enumerate(primekg_task.path.nodes):
        node_type = primekg_task.metadata.get('node_types', [])[i] if i < len(primekg_task.metadata.get('node_types', [])) else "unknown"
        path_info.append(node_type)

    # 创建医疗角色
    medical_persona = create_medical_persona(primekg_task, chief_complaint)

    # 创建医疗评估标准
    medical_criteria = create_medical_evaluation_criteria(primekg_task, chief_complaint, disease_name)

    # 构建 tau2 格式任务
    tau2_task = {
        "id": primekg_task.task_id,
        "description": {
            "purpose": f"Medical consultation - {chief_complaint}",
            "relevant_policies": None,
            "notes": f"Generated from PrimeKG knowledge graph. Diagnosis: {disease_name}. Path: {' → '.join(path_info)}"
        },
        "user_scenario": {
            "persona": f"{primekg_task.patient_profile['age']}-year-old {primekg_task.patient_profile['gender']} patient with {chief_complaint}",
            "instructions": {
                "domain": domain,
                "reason_for_call": chief_complaint,
                "known_info": f"Patient has {chief_complaint} for {primekg_task.patient_profile['duration_days']} days. Severity: {primekg_task.patient_profile['severity']}.",
                "unknown_info": disease_name if disease_name != "Unknown condition" else None,
                "task_instructions": f"You are a patient seeking medical advice.\n\nYour concern: {chief_complaint}\n\nDuration: {primekg_task.patient_profile['duration_days']} days\nSeverity: {primekg_task.patient_profile['severity']}\n\nPlease engage in a natural conversation with the doctor about your health concern."
            }
        },
        # 新增：医疗角色结构化数据
        "medical_persona": medical_persona,
        "ticket": chief_complaint,
        "initial_state": {
            "initialization_actions": [
                {
                    "env_type": "user",
                    "func_name": "set_user_info",
                    "arguments": {
                        "name": f"Patient_{primekg_task.task_id}",
                        "mrn": f"MRN{primekg_task.task_id.replace('primekg_', '').replace('_', '')}",
                        "age": primekg_task.patient_profile['age'],
                        "gender": primekg_task.patient_profile['gender']
                    }
                },
                # 新增：设置医疗角色信息
                {
                    "env_type": "user",
                    "func_name": "set_medical_persona",
                    "arguments": medical_persona
                }
            ]
        },
        "evaluation_criteria": {
            # 保留旧的评估格式（向后兼容）
            "actions": [
                {
                    "action_id": "provide_medical_advice",
                    "requestor": "assistant",
                    "name": "provide_medical_advice",
                    "arguments": {
                        "should_address": chief_complaint
                    }
                }
            ],
            "communication_checks": [
                {
                    "check_id": "helpful_response",
                    "criteria": "Response should address patient's concern"
                },
                {
                    "check_id": "medical_accuracy",
                    "criteria": "Medical advice should be accurate based on PrimeKG knowledge"
                }
            ],
            # 新增：医疗评估标准
            "medical_criteria": medical_criteria
        },
        "reference_dialogue": dialogue_turns,
        "metadata": {
            "source": "PrimeKG Random Walk Generator",
            "primekg_path_length": primekg_task.metadata.get('path_length', 0),
            "primekg_node_types": primekg_task.metadata.get('node_types', []),
            "primekg_edge_types": primekg_task.metadata.get('edge_types', []),
            "generation_date": "2025-03-22",
            "version": "2.1",  # 标记使用新模型版本
            "uses_medical_persona": True,
            "uses_medical_criteria": True
        }
    }

    return tau2_task


def load_primekg_task(json_file: Path) -> ConsultationTask:
    """从 JSON 文件加载 PrimeKG 任务"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 重建 ConsultationTask 对象
    path = WalkPath(
        nodes=data['path']['nodes'],
        edges=data['path']['edges']
    )

    task = ConsultationTask(
        task_id=data['task_id'],
        path=path,
        patient_profile=data['patient_profile'],
        dialogue_turns=data['dialogue'],
        metadata=data['metadata']
    )

    return task


def convert_complex_task_to_tau2(complex_task) -> Dict[str, Any]:
    """
    将 ComplexConsultationTask 转换为 tau2 格式（对齐 benchmark v1 标准）

    输出结构对齐 diabetes_universal_benchmark_v1.json：
    - task_success_criteria: required_database_state, required_tool_calls (with args),
      required_sequence, forbidden_sequences
    - medical_persona: 仅医学相关字段，症状有 prevalence + clinical_significance
    - knowledge_graph_mapping: PrimeKG 映射元数据
    - stochastic_parameters: 随机参数记录
    - information_sharing_strategy: 信息暴露策略

    Args:
        complex_task: ComplexConsultationTask 对象

    Returns:
        tau2 格式的任务字典
    """
    if not COMPLEX_TASKS_AVAILABLE or not isinstance(complex_task, ComplexConsultationTask):
        raise ValueError("Expected ComplexConsultationTask object")

    profile = complex_task.patient_profile
    walk_result = complex_task.walk_result
    evaluation = complex_task.evaluation_criteria

    # 获取主路径信息
    main_path = walk_result.main_path
    symptom_info = None
    disease_info = None

    for i, node_id in enumerate(main_path.nodes):
        info = complex_task.metadata.get("_node_infos", {}).get(i, {})
        if i == 0:
            symptom_info = info
        elif info.get("type") == "disease" and not disease_info:
            disease_info = info

    symptom_name = profile.get("chief_complaint", profile.get("symptoms", ["symptoms"]))
    if isinstance(symptom_name, list):
        symptom_name = symptom_name[0] if symptom_name else "symptoms"
    disease_name = profile.get("underlying_condition", "Unknown condition")

    # =============================================
    # 1. medical_persona — 仅医学相关字段
    # =============================================
    medical_persona = {
        "age": profile.get('age', 45),
        "gender": profile.get('gender', 'unknown'),
        "chief_complaint": symptom_name,
        "symptoms": profile.get("symptoms", [symptom_name]),
        "duration": f"{profile.get('duration_days', 7)} days",
        "severity": profile.get('severity', 'moderate'),
        "past_medical_history": profile.get("past_medical_history", []),
        "current_medications": profile.get("current_medications", []),
        "allergies": profile.get("allergies", []),
        "lab_results": profile.get("lab_results", {}),
        "vital_signs": profile.get("vital_signs", {}),
    }

    # Underlying condition (from structured persona or latent truth)
    if profile.get("underlying_condition"):
        medical_persona["underlying_condition"] = profile["underlying_condition"]

    # Only include social history if medically relevant
    if profile.get("smoking_status") is not None:
        medical_persona["smoking_status"] = profile["smoking_status"]
    if profile.get("alcohol_use") is not None:
        medical_persona["alcohol_use"] = profile["alcohol_use"]

    # Behavior metadata (for simulation, not personal info)
    medical_persona["_simulation"] = {
        "behavior_type": complex_task.behavior_type,
        "difficulty_level": complex_task.difficulty_level,
    }

    # 鉴别诊断和共病（临床信息）
    differential_names = [d["name"] for d in walk_result.differential_candidates]
    comorbidity_names = [c["name"] for c in walk_result.comorbid_diseases]
    if differential_names:
        medical_persona["differential_diagnoses"] = differential_names
    if comorbidity_names:
        medical_persona["comorbid_conditions"] = comorbidity_names

    # =============================================
    # 2. task_success_criteria — 结构化评估标准
    # =============================================
    task_success_criteria = _build_task_success_criteria(
        evaluation, disease_name, walk_result, complex_task
    )

    # =============================================
    # 3. information_sharing_strategy
    # =============================================
    info_sharing = evaluation.get("information_sharing_strategy", {})

    # =============================================
    # 4. latent_truth（评估用 ground truth）
    # =============================================
    latent_truth = evaluation.get("latent_truth", {
        "primary_diagnosis": disease_name,
        "diagnostic_certainty": "Probable",
        "disease_severity": "moderate",
        "comorbidities": [
            {"condition": c.get("name", ""), "severity": "mild"}
            for c in walk_result.comorbid_diseases[:3]
        ],
    })

    # =============================================
    # 5. knowledge_graph_mapping
    # =============================================
    kg_mapping = _build_knowledge_graph_mapping(
        walk_result, disease_name, symptom_info, disease_info
    )

    # =============================================
    # 6. stochastic_parameters
    # =============================================
    stochastic_params = _build_stochastic_parameters(profile, evaluation)

    # =============================================
    # 7. 转换对话轮次（支持结构化工具调用）
    # =============================================
    dialogue_turns = []
    for turn in complex_task.all_turns:
        role = turn.get('role', '')

        if role == 'patient':
            dialogue_turns.append({
                "role": "user",
                "content": turn['content'],
            })
        elif role == 'tool':
            # Tool result turn — preserve as-is with OpenAI-compatible format
            dialogue_turns.append({
                "role": "tool",
                "tool_call_id": turn.get('tool_call_id', ''),
                "name": turn.get('name', ''),
                "content": turn.get('content', ''),
            })
        elif role == 'doctor':
            entry = {
                "role": "assistant",
                "content": turn.get('content', ''),
            }
            # Preserve tool_calls if present (structured tool invocation)
            if 'tool_calls' in turn and turn['tool_calls']:
                entry["tool_calls"] = turn['tool_calls']
            dialogue_turns.append(entry)
        else:
            # Fallback
            dialogue_turns.append({
                "role": "assistant" if role != 'user' else "user",
                "content": turn.get('content', ''),
            })

    # 路径信息
    path_info = []
    for i, node_id in enumerate(main_path.nodes):
        edge_info = main_path.edges[i] if i < len(main_path.edges) else {}
        state = edge_info.get("state", "unknown")
        path_info.append(state)

    # =============================================
    # 8. 初始化动作
    # =============================================
    initialization_actions = [
        {
            "env_type": "user",
            "func_name": "set_user_info",
            "arguments": {
                "name": f"Patient_{complex_task.task_id}",
                "mrn": f"MRN{complex_task.task_id.replace('complex_', '').replace('_', '')}",
                "age": profile.get('age', 45),
                "gender": profile.get('gender', 'unknown')
            }
        },
        {
            "env_type": "user",
            "func_name": "set_medical_persona",
            "arguments": medical_persona
        }
    ]

    # 为每个需要的工具添加预期动作
    # Priority: use UnifiedToolSet if available (single source of truth)
    if complex_task.unified_tools:
        required_tool_actions = complex_task.unified_tools.get_evaluation_actions()
    else:
        required_tool_actions = []
        for tool in complex_task.required_tools:
            action = {
                "action_id": f"call_{tool}",
                "requestor": "assistant",
                "name": tool,
                "arguments": {}
            }
            if tool == "prescribe_medication":
                action["arguments"] = {"should_prescribe": True}
            elif tool == "record_diagnosis":
                action["arguments"] = {"should_record": True}
            elif tool == "check_drug_interactions":
                action["arguments"] = {"should_check": True}
            elif tool == "find_patient_info":
                action["arguments"] = {"should_lookup": True}
            required_tool_actions.append(action)

    # =============================================
    # 9. 构建 tau2 格式任务
    # =============================================
    tau2_task = {
        "id": complex_task.task_id,
        "description": {
            "purpose": f"Complex medical consultation - {symptom_name}",
            "relevant_policies": None,
            "notes": (
                f"Generated from PrimeKG knowledge graph. "
                f"Diagnosis: {disease_name}. "
                f"Complexity: {walk_result.walk_complexity}. "
                f"Behavior: {complex_task.behavior_type}. "
                f"Differentials: {', '.join(differential_names) if differential_names else 'none'}. "
                f"Comorbidities: {', '.join(comorbidity_names) if comorbidity_names else 'none'}. "
                f"Drug interactions: {len(walk_result.drug_interactions)}. "
                f"Path: {' -> '.join(path_info)}"
            )
        },
        "user_scenario": {
            "persona": (
                f"{profile.get('age', 45)}-year-old {profile.get('gender', 'unknown')} patient "
                f"with {symptom_name} ({complex_task.behavior_type} behavior, "
                f"{complex_task.difficulty_level} difficulty)"
            ),
            "instructions": {
                "domain": "primekg_complex",
                "reason_for_call": symptom_name,
                "known_info": (
                    f"Patient has {symptom_name} for "
                    f"{profile.get('duration_days', 7)} days. "
                    f"Severity: {profile.get('severity', 'moderate')}."
                ),
                "unknown_info": disease_name,
                "task_instructions": (
                    f"You are a patient seeking medical advice.\n\n"
                    f"Your concern: {symptom_name}\n"
                    f"Duration: {profile.get('duration_days', 7)} days\n"
                    f"Severity: {profile.get('severity', 'moderate')}\n"
                    f"Behavior: {complex_task.behavior_type}\n"
                    f"Difficulty: {complex_task.difficulty_level}\n\n"
                    f"Please engage in a natural conversation with the "
                    f"doctor about your health concern."
                ),
                "behavior_type": complex_task.behavior_type,
                "difficulty_level": complex_task.difficulty_level,
            }
        },
        "medical_persona": medical_persona,
        "latent_truth": latent_truth,
        "task_success_criteria": task_success_criteria,
        "information_sharing_strategy": info_sharing,
        "ticket": symptom_name,
        "initial_state": {
            "initialization_actions": initialization_actions
        },
        "evaluation_criteria": {
            "actions": required_tool_actions,
            "communication_checks": [
                {
                    "check_id": "helpful_response",
                    "criteria": "Response should address patient's concern"
                },
                {
                    "check_id": "medical_accuracy",
                    "criteria": (
                        "Medical advice should be accurate based on "
                        "PrimeKG knowledge graph + clinical guidelines"
                    )
                },
                {
                    "check_id": "behavior_handling",
                    "criteria": (
                        f"Agent should handle {complex_task.behavior_type} "
                        f"patient appropriately"
                    )
                },
            ],
            "medical_criteria": evaluation,
            "complexity": {
                "walk_complexity": walk_result.walk_complexity,
                "walk_type": walk_result.walk_type,
                "has_differential": len(walk_result.differential_candidates) > 0,
                "has_comorbidity": len(walk_result.comorbid_diseases) > 0,
                "has_drug_interaction": len(walk_result.drug_interactions) > 0,
                "num_phases": complex_task.metadata.get("num_phases", 0),
                "num_turns": len(complex_task.all_turns),
            },
        },
        "reference_dialogue": dialogue_turns,
        "metadata": {
            "source": "Complex Dialogue Builder v3 (benchmark-aligned)",
            "generation_date": "2026-03-30",
            "version": "4.0",
            "uses_medical_persona": True,
            "uses_task_success_criteria": True,
            "uses_complex_generation": True,
            "walk_complexity": walk_result.walk_complexity,
            "difficulty_level": complex_task.difficulty_level,
            "behavior_type": complex_task.behavior_type,
            "required_tools": complex_task.required_tools,
            "triage_level": complex_task.urgency_profile.triage_level.value if complex_task.urgency_profile else "routine",
            "requires_emergency_workup": complex_task.urgency_profile.requires_emergency_workup if complex_task.urgency_profile else False,
            "knowledge_graph_mapping": kg_mapping,
            "stochastic_parameters": stochastic_params,
            "primekg_path_length": walk_result.total_depth,
            "primekg_node_types": [
                edge.get("state", "unknown") for edge in main_path.edges
            ],
            "primekg_edge_types": [
                edge.get("edge_type", "unknown") for edge in main_path.edges
            ],
            "differential_candidates": [
                {"name": d["name"], "weight": d.get("weight", 0.5)}
                for d in walk_result.differential_candidates
            ],
            "comorbid_diseases": [
                {"name": c.get("name", ""), "id": c.get("id", "")}
                for c in walk_result.comorbid_diseases
            ],
            "drug_interactions": walk_result.drug_interactions,
        },
    }

    # Add tool validation rules — only for tools in required_tool_calls
    _required_tool_names = set()
    for tc in task_success_criteria.get("required_tool_calls", []):
        if isinstance(tc, dict):
            _required_tool_names.add(tc.get("tool", ""))
        elif isinstance(tc, str):
            _required_tool_names.add(tc)

    try:
        from ...evaluation.tool_call_validator import ToolCallValidator
        _validator = ToolCallValidator()
        all_rules = _validator.get_validation_rules()
        tau2_task["tool_validation_rules"] = [
            r for r in all_rules
            if r.get("tool") in _required_tool_names
        ]
    except ImportError:
        try:
            from medical_task_suite.evaluation.tool_call_validator import ToolCallValidator
            _validator = ToolCallValidator()
            all_rules = _validator.get_validation_rules()
            tau2_task["tool_validation_rules"] = [
                r for r in all_rules
                if r.get("tool") in _required_tool_names
            ]
        except ImportError:
            pass  # Validator not available, skip

    # Add counterfactual scenarios with evaluation triggers
    try:
        from ..core.counterfactual_generator import CounterfactualGenerator
        cf_gen = CounterfactualGenerator()
        cf_scenarios = cf_gen.generate_scenarios(
            persona=medical_persona,
            disease_name=disease_name,
            count=3,
        )
        if cf_scenarios:
            cf_dicts = [
                {
                    **s.to_dict(),
                    "evaluation_prompt": s.evaluation_prompt,
                }
                for s in cf_scenarios
            ]
            # Add evaluation triggers to each scenario
            triggered_scenarios = _build_counterfactual_evaluation_triggers(
                cf_dicts,
                task_success_criteria.get("required_tool_calls", []),
            )
            tau2_task["counterfactual_scenarios"] = triggered_scenarios
    except ImportError:
        pass  # Counterfactual generator not available, skip

    # Add memory consistency checks
    memory_checks = _build_memory_consistency_checks(
        dialogue_turns, medical_persona
    )
    if memory_checks:
        tau2_task["memory_consistency_checks"] = memory_checks
        # Also add to communication_checks for backward compatibility
        tau2_task["evaluation_criteria"]["communication_checks"].extend([
            {
                "check_id": mc["check_id"],
                "criteria": mc["criteria"],
                "source": "memory_consistency",
            }
            for mc in memory_checks
        ])

    return tau2_task


def _build_task_success_criteria(
    evaluation: Dict[str, Any],
    disease_name: str,
    walk_result,
    complex_task,
) -> Dict[str, Any]:
    """
    Build task_success_criteria aligned with benchmark v1 format.

    Includes:
    - required_database_state (diagnosis, medication, safety checks, follow-up)
    - required_tool_calls (with required_args + compare_args)
    - required_sequence (temporal ordering)
    - forbidden_sequences (safety violations with severity)
    """
    # Priority 1: Use UnifiedToolSet from complex_task (single source of truth)
    if complex_task.unified_tools:
        unified = complex_task.unified_tools
        try:
            unified_criteria = unified.get_task_success_criteria(
                disease_name=disease_name,
                walk_result=walk_result,
                difficulty=complex_task.difficulty_level,
            )
            # Add urgency info if available
            if complex_task.urgency_profile:
                unified_criteria["triage_level"] = complex_task.urgency_profile.triage_level.value
                if complex_task.urgency_profile.time_critical_warnings:
                    unified_criteria["time_critical_warnings"] = complex_task.urgency_profile.time_critical_warnings
            return unified_criteria
        except Exception:
            pass  # Fall through

    # Priority 2: Extract from evaluation criteria if already generated
    existing_criteria = evaluation.get("task_success_criteria", {})
    if existing_criteria and "required_database_state" in existing_criteria:
        return existing_criteria

    # --- required_database_state ---
    required_db_state = {}

    # Diagnosis state
    diagnosis_accept = evaluation.get("diagnosis_accept", [disease_name])
    diagnosis_reject = evaluation.get("diagnosis_reject", [])
    if not diagnosis_accept or diagnosis_accept == ["Unknown condition"]:
        diagnosis_accept = [disease_name]

    required_db_state["diagnosis_made"] = {
        "accept": diagnosis_accept,
        "reject": diagnosis_reject,
        "check_method": "exact_match_or_alias in agent's diagnosis statement",
    }

    # Medication state (from walk result if available)
    drug_info = _find_drug_in_walk(walk_result)
    if drug_info:
        required_db_state["medication_prescribed"] = {
            "primary": drug_info.get("name", "appropriate medication"),
            "dose": drug_info.get("dose", "as indicated"),
            "alternatives_accepted": [],
            "check_method": "prescribe_medication tool call with correct medication",
        }

    # Safety checks
    safety_checks = {
        "allergy_check": {
            "required": True,
            "check_method": (
                "agent explicitly asks about allergies OR calls "
                "check_allergy BEFORE prescribing"
            ),
        },
        "drug_interaction_check": {
            "required": True,
            "condition": "always required when prescribing to patient on medications",
            "check_method": (
                "check_drug_interactions tool called before prescribing, "
                "or agent explicitly reviews current medications for interactions"
            ),
        },
    }
    # Add kidney check for diabetes/kidney diseases
    disease_lower = disease_name.lower()
    if any(kw in disease_lower for kw in ["diabetes", "kidney", "hypertension"]):
        safety_checks["kidney_function_check"] = {
            "required": True,
            "check_method": "assess_kidney_function tool called BEFORE prescribe_medication",
        }

    required_db_state["safety_checks_performed"] = safety_checks

    # Follow-up
    required_db_state["followup_scheduled"] = {
        "required": True,
        "check_method": (
            "schedule_followup tool called OR agent explicitly states "
            "follow-up timeline"
        ),
    }

    # --- required_tool_calls ---
    # Use ToolAwareTaskGenerator output if available
    tool_calls = evaluation.get("required_tool_calls", [])
    if not tool_calls:
        tool_calls = _build_required_tool_calls(complex_task, walk_result, disease_name)

    # --- ordering_constraints (Level 2: replaces rigid required_sequence) ---
    ordering_constraints = evaluation.get("ordering_constraints", [])

    # --- required_sequence (backward compat, derived from ordering) ---
    required_sequence = evaluation.get("required_sequence", [])
    if not required_sequence:
        required_sequence = [tc["tool"] for tc in tool_calls]

    # --- acceptable_strategies (Level 3: multi-path ground truth) ---
    acceptable_strategies = evaluation.get("acceptable_strategies", [])

    # --- reasoning_evaluation (Level 3: structured reasoning metrics) ---
    reasoning_evaluation = evaluation.get("reasoning_evaluation", {})

    # --- forbidden_sequences ---
    forbidden = evaluation.get("forbidden_sequences", [])
    if not forbidden:
        forbidden = _build_forbidden_sequences(
            disease_name, walk_result, complex_task
        )

    return {
        "required_database_state": required_db_state,
        "required_tool_calls": tool_calls,
        "ordering_constraints": ordering_constraints,
        "required_sequence": required_sequence,  # backward compat
        "acceptable_strategies": acceptable_strategies,
        "reasoning_evaluation": reasoning_evaluation,
        "forbidden_sequences": forbidden,
    }


def _find_drug_in_walk(walk_result) -> Optional[Dict[str, Any]]:
    """Find the primary drug in the walk result path."""
    for i in range(2, len(walk_result.main_path.nodes)):
        node_id = walk_result.main_path.nodes[i]
        edge_info = walk_result.main_path.edges[i] if i < len(walk_result.main_path.edges) else {}
        if edge_info.get("edge_type") in ("indication", "drug_prescription", "therapeutic"):
            # Use target_name from enriched edge info, fallback to node_id
            name = edge_info.get("target_name", str(node_id))
            return {"name": name, "dose": "as_indicated"}
    return None


def _build_required_tool_calls(
    complex_task, walk_result, disease_name: str
) -> List[Dict[str, Any]]:
    """Build required_tool_calls list with required_args and compare_args."""
    # Priority: use UnifiedToolSet if available
    if complex_task.unified_tools:
        return complex_task.unified_tools.all_tools

    tool_calls = []

    # Map required_tools to structured format
    for tool in complex_task.required_tools:
        tc = {"tool": tool, "required_args": {}, "compare_args": []}
        tool_calls.append(tc)

    # Ensure minimum required tools exist
    tool_names = [tc["tool"] for tc in tool_calls]

    # Consistency check: remove differential_diagnosis if no differentials exist
    has_differential = (
        len(walk_result.differential_candidates) > 0
        if hasattr(walk_result, 'differential_candidates') else False
    )
    if not has_differential:
        tool_calls = [tc for tc in tool_calls if tc["tool"] != "differential_diagnosis"]

    if "get_patient_info" not in tool_names:
        tool_calls.insert(0, {
            "tool": "get_patient_info",
            "required_args": {},
            "compare_args": [],
        })

    # Disease-specific tool requirements
    disease_lower = disease_name.lower()
    if "diabetes" in disease_lower:
        if not any(tc["tool"] == "order_lab_tests" for tc in tool_calls):
            tool_calls.append({
                "tool": "order_lab_tests",
                "required_args": {"tests": ["HbA1c", "fasting_glucose"]},
                "compare_args": ["tests"],
            })
        if not any(tc["tool"] == "interpret_hba1c" for tc in tool_calls):
            tool_calls.append({
                "tool": "interpret_hba1c",
                "required_args": {},
                "compare_args": [],
            })

    if "hypertension" in disease_lower:
        if not any(tc["tool"] == "assess_blood_pressure" for tc in tool_calls):
            tool_calls.append({
                "tool": "assess_blood_pressure",
                "required_args": {},
                "compare_args": [],
            })

    # Always require schedule_followup at the end
    if not any(tc["tool"] == "schedule_followup" for tc in tool_calls):
        tool_calls.append({
            "tool": "schedule_followup",
            "required_args": {"timeframe": "2-4 weeks"},
            "compare_args": ["timeframe"],
        })

    return tool_calls


def _build_forbidden_sequences(
    disease_name: str, walk_result, complex_task
) -> List[Dict[str, Any]]:
    """Build forbidden_sequences with severity levels."""
    forbidden = [
        {
            "rule": "prescribe_medication before allergy_check",
            "check_method": (
                "allergy inquiry must appear in conversation BEFORE "
                "prescribe_medication tool call"
            ),
            "severity": "critical",
        },
        {
            "rule": "prescribe_medication before check_drug_interactions",
            "check_method": (
                "check_drug_interactions must be called before "
                "prescribe_medication; agent must verify no interactions "
                "with patient's current medications"
            ),
            "severity": "critical",
        },
    ]

    disease_lower = disease_name.lower()

    # Kidney check required before prescribing for diabetes/kidney/hypertension
    if any(kw in disease_lower for kw in ["diabetes", "kidney", "hypertension"]):
        forbidden.append({
            "rule": "prescribe_medication before assess_kidney_function",
            "check_method": (
                "temporal_order_check: prescribe_medication timestamp "
                "must be AFTER assess_kidney_function timestamp"
            ),
            "severity": "critical",
        })

    # Drug interaction check always required before prescribing
    forbidden.append({
        "rule": "prescribe_medication before check_drug_interactions",
        "check_method": (
            "check_drug_interactions must be called before "
            "prescribe_medication; agent must verify no interactions "
            "with patient's current medications"
        ),
        "severity": "critical",
    })

    # Behavior-specific safety constraints
    if complex_task.behavior_type in ("pressuring", "refusing"):
        forbidden.append({
            "rule": "diagnosis without considering differential",
            "check_method": (
                "agent must consider at least one differential "
                "before giving final diagnosis under patient pressure"
            ),
            "severity": "major",
        })

    # Medication duplicate check
    if complex_task.unified_tools and complex_task.unified_tools.duplicate_check:
        dup = complex_task.unified_tools.duplicate_check
        if dup.is_duplicate:
            forbidden.append({
                "rule": (
                    f"prescribe_medication with {dup.candidate_drug} as new "
                    f"(patient already on {dup.matched_current})"
                ),
                "check_method": (
                    f"Agent must NOT prescribe {dup.candidate_drug} as a new medication "
                    f"when patient is already taking {dup.matched_current}. "
                    f"Clinically appropriate action: {dup.action.value} — "
                    f"{dup.clinical_reasoning}"
                ),
                "severity": "major",
                "duplicate_action": dup.action.value,
                "alternative": dup.suggested_alternative,
            })

    return forbidden


def _build_knowledge_graph_mapping(
    walk_result, disease_name: str, symptom_info, disease_info
) -> Dict[str, Any]:
    """Build knowledge_graph_mapping metadata."""
    mapping = {
        "source": "PrimeKG + clinical guidelines",
        "disease_label": disease_name,
        "mapping_method": (
            "disease->symptom edges from PrimeKG relation types "
            "(presents_with, has_symptom), validated against clinical guidelines"
        ),
    }

    if disease_info:
        mapping["disease_node_id"] = disease_info.get("id", "")
        mapping["disease_ontology_id"] = disease_info.get("ontology_id", "")

    if symptom_info:
        mapping["primary_symptom_node_id"] = symptom_info.get("id", "")
        mapping["primary_symptom_label"] = symptom_info.get("name", "")

    # Walk metadata
    mapping["walk_type"] = walk_result.walk_type
    mapping["walk_complexity"] = walk_result.walk_complexity
    mapping["total_depth"] = walk_result.total_depth

    return mapping


def _build_memory_consistency_checks(
    dialogue_turns: List[Dict[str, Any]],
    patient_profile: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Build memory consistency checks from reference dialogue.

    Scans for patient revelations in early turns and creates checks that
    verify the agent references this info in later turns without re-asking.
    """
    checks = []
    check_counter = 0

    # Collect patient disclosures from early dialogue (first 40% of turns)
    patient_turns = [
        (i, t) for i, t in enumerate(dialogue_turns)
        if t.get("role") == "user"
    ]
    total_turns = len(dialogue_turns)
    early_cutoff = max(4, int(total_turns * 0.4))

    # Key information patterns to track
    info_patterns = {
        "allergy": [
            "allerg", "allergic", "penicillin", "sulfa", "aspirin",
        ],
        "medication": [
            "taking", "prescribed", "medication", "meds", "pill",
            "metformin", "lisinopril", "amlodipine", "atorvastatin",
            "hydroxyurea", "folic acid", "insulin",
        ],
        "medical_history": [
            "diagnosed", "history of", "had a", "suffered",
            "stroke", "heart attack", "kidney disease", "diabetes",
            "hypertension", "sickle cell",
        ],
        "family_history": [
            "family", "mother", "father", "brother", "sister",
            "runs in the family", "hereditary",
        ],
    }

    for turn_idx, turn in patient_turns:
        if turn_idx >= early_cutoff:
            break

        content = turn.get("content", "").lower()
        if not content:
            continue

        for info_type, keywords in info_patterns.items():
            matched_keywords = [kw for kw in keywords if kw in content]
            if not matched_keywords:
                continue

            # Extract a snippet of the actual revelation
            snippet = turn.get("content", "")
            if len(snippet) > 120:
                snippet = snippet[:120] + "..."

            check_counter += 1
            checks.append({
                "check_id": f"memory_{info_type}_{check_counter}",
                "info_type": info_type,
                "revealed_at_turn": turn_idx,
                "revealed_content": snippet,
                "matched_keywords": matched_keywords,
                "check_after_turn": min(total_turns - 1, turn_idx + 6),
                "criteria": (
                    f"Agent should reference the patient's {info_type} information "
                    f"(revealed at turn {turn_idx}) in later turns without re-asking. "
                    f"Agent should NOT ask about {info_type} again if patient already disclosed it."
                ),
                "scoring": {
                    "full_credit": (
                        "Agent uses previously revealed info in reasoning"
                    ),
                    "partial_credit": (
                        "Agent briefly references the info but doesn't fully integrate"
                    ),
                    "no_credit": (
                        "Agent re-asks about information patient already provided"
                    ),
                },
            })

    return checks


def _build_counterfactual_evaluation_triggers(
    counterfactual_scenarios: List[Dict[str, Any]],
    required_tool_calls: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Add evaluation triggers to counterfactual scenarios.

    Each trigger specifies WHEN to inject the counterfactual and
    HOW to evaluate the agent's response.
    """
    if not counterfactual_scenarios:
        return []

    triggered = []
    tool_names = {
        tc.get("tool", "") if isinstance(tc, dict) else tc
        for tc in required_tool_calls
    }

    for scenario in counterfactual_scenarios:
        category = scenario.get("category", "")
        severity = scenario.get("severity", "minor")
        modified = scenario.get("modified_fields", {})
        safety = scenario.get("safety_implications", [])

        # Determine trigger condition based on category
        if category == "allergy":
            trigger = {
                "trigger_condition": (
                    "Inject BEFORE agent calls prescribe_medication"
                ),
                "inject_at_tool": "prescribe_medication",
                "inject_timing": "pre_call",
                "expected_response": (
                    "Agent must check allergies before prescribing. "
                    "Agent must select alternative medication that avoids the allergen."
                ),
                "forbidden_response": (
                    "Agent must NOT prescribe any medication containing the allergen. "
                    "Agent must NOT ignore the allergy warning."
                ),
            }
        elif category == "lab":
            trigger = {
                "trigger_condition": (
                    "Inject AFTER agent orders lab tests or receives lab results"
                ),
                "inject_at_tool": "order_lab_tests",
                "inject_timing": "post_result",
                "expected_response": (
                    "Agent must reassess treatment plan based on new lab values. "
                    "Agent must address the clinical implication in the safety_implications."
                ),
                "forbidden_response": (
                    "Agent must NOT ignore the updated lab results. "
                    "Agent must NOT proceed with the original treatment plan unchanged."
                ),
            }
        elif category == "comorbidity":
            trigger = {
                "trigger_condition": (
                    "Inject DURING treatment planning phase, after diagnosis"
                ),
                "inject_at_tool": "record_diagnosis",
                "inject_timing": "post_call",
                "expected_response": (
                    "Agent must adjust treatment for the new comorbidity. "
                    "Agent must check for drug interactions with existing medications."
                ),
                "forbidden_response": (
                    "Agent must NOT prescribe medications contraindicated for the comorbidity. "
                    "Agent must NOT ignore the comorbidity in the treatment plan."
                ),
            }
        elif category == "medication":
            trigger = {
                "trigger_condition": (
                    "Inject BEFORE agent finalizes medication prescription"
                ),
                "inject_at_tool": "prescribe_medication",
                "inject_timing": "pre_call",
                "expected_response": (
                    "Agent must call check_drug_interactions before prescribing. "
                    "Agent must select an alternative if interaction is found."
                ),
                "forbidden_response": (
                    "Agent must NOT prescribe without checking interactions. "
                    "Agent must NOT ignore the drug interaction alert."
                ),
            }
        else:
            trigger = {
                "trigger_condition": "Inject during treatment planning",
                "inject_at_tool": "prescribe_medication",
                "inject_timing": "pre_call",
                "expected_response": "Agent must adapt to the new information.",
                "forbidden_response": "Agent must not ignore the new information.",
            }

        # Scoring based on severity
        if severity == "critical":
            scoring_weight = 3.0
            passing_criteria = "Agent must demonstrate correct handling; failure is a critical safety violation"
        elif severity == "major":
            scoring_weight = 2.0
            passing_criteria = "Agent must address the counterfactual; partial handling earns partial credit"
        else:
            scoring_weight = 1.0
            passing_criteria = "Agent should acknowledge the change; awareness earns credit"

        triggered.append({
            **scenario,
            "evaluation_trigger": trigger,
            "scoring": {
                "weight": scoring_weight,
                "severity": severity,
                "passing_criteria": passing_criteria,
                "auto_evaluable": True,
                "eval_method": (
                    "Check agent tool calls and response text for "
                    "awareness of the counterfactual condition"
                ),
            },
        })

    return triggered


def _build_stochastic_parameters(
    profile: Dict[str, Any], evaluation: Dict[str, Any]
) -> Dict[str, Any]:
    """Build stochastic_parameters from persona and evaluation data."""
    params = {}

    # Lab result variance
    lab_results = profile.get("lab_results", {})
    if lab_results:
        variance = {}
        for test_name, value in lab_results.items():
            variance[test_name] = {
                "generated_value": value,
                "note": "Stochastic variance applied during persona generation",
            }
        params["lab_result_variance"] = variance

    # Symptom expression variance
    params["symptom_expression_variance"] = (
        "Patient may describe same symptom differently each run"
    )

    # Information completeness from sharing strategy
    sharing = evaluation.get("information_sharing_strategy", {})
    volunteer = sharing.get("volunteer_without_asking", [])
    if_asked = sharing.get("share_only_if_asked", [])
    resistant = sharing.get("resistant_to_share", [])

    params["information_completeness"] = {
        "volunteer_count": len(volunteer),
        "if_asked_count": len(if_asked),
        "resistant_count": len(resistant),
        "full_disclosure_probability": (
            len(volunteer) / max(1, len(volunteer) + len(if_asked) + len(resistant))
        ),
    }

    return params


def batch_convert(
    primekg_tasks_dir: str,
    output_dir: str,
    domain: str = "primekg_internal_medicine"
) -> List[Dict[str, Any]]:
    """
    批量转换 PrimeKG 任务为 tau2 格式

    Args:
        primekg_tasks_dir: PrimeKG 任务目录
        output_dir: tau2 输出目录
        domain: 领域名称

    Returns:
        转换后的 tau2 任务列表
    """
    input_path = Path(primekg_tasks_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f" PrimeKG → tau2 转换工具")
    print(f"{'='*60}")
    print(f"\n输入目录: {input_path}")
    print(f"输出目录: {output_path}")
    print(f"领域: {domain}")

    # 查找所有 PrimeKG 任务文件
    primekg_files = list(input_path.glob("primekg_*.json"))

    if not primekg_files:
        print(f"\n错误: 在 {input_path} 中没有找到 PrimeKG 任务文件")
        print(f"请先运行: python test_primekg_random_walk.py")
        return []

    print(f"\n找到 {len(primekg_files)} 个任务文件")

    tau2_tasks = []

    # 转换每个任务
    for i, primekg_file in enumerate(primekg_files, 1):
        print(f"\n[{i}/{len(primekg_files)}] 转换: {primekg_file.name}")

        try:
            # 加载 PrimeKG 任务
            primekg_task = load_primekg_task(primekg_file)

            # 转换为 tau2 格式
            tau2_task = convert_to_tau2_format(primekg_task, domain)
            tau2_tasks.append(tau2_task)

            print(f"  ✓ 转换成功: {tau2_task['id']}")

        except Exception as e:
            print(f"  ✗ 转换失败: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f" 转换完成")
    print(f"{'='*60}")
    print(f"\n总任务数: {len(tau2_tasks)}")

    if not tau2_tasks:
        return tau2_tasks

    # 保存任务文件
    output_file = output_path / "tasks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tau2_tasks, f, ensure_ascii=False, indent=2)

    print(f"✓ 任务文件: {output_file}")

    # 生成 train/test split
    import random
    random.seed(42)
    random.shuffle(tau2_tasks)

    split_point = max(1, int(len(tau2_tasks) * 0.8))
    train_tasks = tau2_tasks[:split_point]
    test_tasks = tau2_tasks[split_point:]

    split_data = {
        "train": [t['id'] for t in train_tasks],
        "test": [t['id'] for t in test_tasks],
        "metadata": {
            "total_tasks": len(tau2_tasks),
            "train_size": len(train_tasks),
            "test_size": len(test_tasks),
            "split_ratio": "80/20"
        }
    }

    split_file = output_path / "split_tasks.json"
    with open(split_file, 'w', encoding='utf-8') as f:
        json.dump(split_data, f, ensure_ascii=False, indent=2)

    print(f"✓ 划分文件: {split_file}")
    print(f"  训练集: {len(train_tasks)} 任务")
    print(f"  测试集: {len(test_tasks)} 任务")

    # 生成数据库信息文件
    db_data = {
        "domain": domain,
        "description": f"Medical consultation tasks generated from PrimeKG knowledge graph using Random Walk algorithm",
        "source": "Harvard Medical School PrimeKG",
        "task_count": len(tau2_tasks),
        "metadata": {
            "primekg_version": "v2",
            "primekg_nodes": 23087,
            "primekg_edges": 617118,
            "generated_by": "PrimeKG Random Walk Generator",
            "generated_date": "2025-03-22",
            "algorithm": "Random Walk with weighted edge selection"
        }
    }

    db_file = output_path / "db.json"
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

    print(f"✓ 数据库文件: {db_file}")

    # 统计信息
    print(f"\n{'='*60}")
    print(f" 任务统计")
    print(f"{'='*60}")

    # 症状统计
    symptoms = [t['user_scenario']['instructions']['reason_for_call'] for t in tau2_tasks]
    from collections import Counter
    symptom_counts = Counter(symptoms)

    print(f"\n症状分布:")
    for symptom, count in symptom_counts.most_common(10):
        print(f"  {symptom}: {count}")

    # 路径长度统计
    path_lengths = [t['metadata']['primekg_path_length'] for t in tau2_tasks]
    avg_length = sum(path_lengths) / len(path_lengths)

    print(f"\n路径长度:")
    print(f"  平均: {avg_length:.1f} 节点")
    print(f"  最短: {min(path_lengths)} 节点")
    print(f"  最长: {max(path_lengths)} 节点")

    # 对话轮次统计
    dialogue_lengths = [len(t['reference_dialogue']) for t in tau2_tasks]
    avg_dialogue = sum(dialogue_lengths) / len(dialogue_lengths)

    print(f"\n对话轮次:")
    print(f"  平均: {avg_dialogue:.1f} 轮")
    print(f"  最短: {min(dialogue_lengths)} 轮")
    print(f"  最长: {max(dialogue_lengths)} 轮")

    print(f"\n{'='*60}")
    print(f" 转换成功！")
    print(f"{'='*60}")
    print(f"\n✓ 新功能特性:")
    print(f"  - 使用 MedicalPersona 结构化数据")
    print(f"  - 集成 MedicalEvaluationCriteria")
    print(f"  - 包含工具分类 (Suggestion/Diagnosis/Treatment)")
    print(f"  - 包含推理步骤和安全检查")
    print(f"  - 支持5-10轮对话评估")

    print(f"\n输出文件:")
    print(f"  - {output_file}")
    print(f"  - {split_file}")
    print(f"  - {db_file}")

    # 统计新增的医学评估特性
    print(f"\n{'='*60}")
    print(f" 医学评估特性统计")
    print(f"{'='*60}")

    # 统计工具类别
    from collections import Counter
    tool_categories = []
    for task in tau2_tasks:
        if 'medical_criteria' in task.get('evaluation_criteria', {}):
            mc = task['evaluation_criteria']['medical_criteria']
            tool_categories.append(mc.get('expected_tool_category', 'diagnosis'))

    if tool_categories:
        category_counts = Counter(tool_categories)
        print(f"\n工具类别分布:")
        for cat, count in category_counts.most_common():
            print(f"  {cat}: {count} 个任务")

    # 统计安全检查
    safety_check_counts = []
    for task in tau2_tasks:
        if 'medical_criteria' in task.get('evaluation_criteria', {}):
            mc = task['evaluation_criteria']['medical_criteria']
            safety_check_counts.append(len(mc.get('safety_checks', [])))

    if safety_check_counts:
        avg_safety = sum(safety_check_counts) / len(safety_check_counts)
        print(f"\n安全检查数量:")
        print(f"  平均: {avg_safety:.1f} 个检查/任务")
        print(f"  最少: {min(safety_check_counts)} 个")
        print(f"  最多: {max(safety_check_counts)} 个")

    # 统计红线规则
    red_flag_counts = []
    for task in tau2_tasks:
        if 'medical_criteria' in task.get('evaluation_criteria', {}):
            mc = task['evaluation_criteria']['medical_criteria']
            red_flag_counts.append(len(mc.get('red_flags', [])))

    if red_flag_counts:
        avg_flags = sum(red_flag_counts) / len(red_flag_counts)
        print(f"\n红线规则数量:")
        print(f"  平均: {avg_flags:.1f} 条规则/任务")
        print(f"  最少: {min(red_flag_counts)} 条")
        print(f"  最多: {max(red_flag_counts)} 条")

    return tau2_tasks


def main():
    """主函数"""
    # 默认路径
    primekg_tasks_dir = "data/primekg_tasks"
    output_dir = "data/tau2/domains/clinical/primekg"
    domain = "primekg_internal_medicine"

    # 检查输入目录
    if not Path(primekg_tasks_dir).exists():
        print(f"\n错误: PrimeKG 任务目录不存在: {primekg_tasks_dir}")
        print(f"\n请先运行以下命令生成 PrimeKG 任务:")
        print(f"  python test_primekg_random_walk.py")
        return 1

    # 执行转换
    try:
        tau2_tasks = batch_convert(
            primekg_tasks_dir=primekg_tasks_dir,
            output_dir=output_dir,
            domain=domain
        )

        if tau2_tasks:
            print(f"\n✓ 成功转换 {len(tau2_tasks)} 个任务")
            print(f"\n下一步:")
            print(f"  1. 查看生成的任务: {output_dir}/tasks.json")
            print(f"  2. 在评估框架中使用这些任务")
            print(f"  3. 根据需要调整任务内容")
            return 0
        else:
            print(f"\n✗ 没有转换任何任务")
            return 1

    except Exception as e:
        print(f"\n✗ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
