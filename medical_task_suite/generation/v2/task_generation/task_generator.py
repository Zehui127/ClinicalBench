#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Task Generator — Convert v2.7 ScenarioSpec → tau2-bench multi-turn task JSON.

No agent interaction required. Generates complete, rich task definitions matching
benchmark quality (see benchmark_examples/diabetes_initial_v1.json).

Key quality features:
- Patient-friendly language (not clinical jargon)
- Realistic lab values from lab_reference.json
- Detailed drug info from drug_database.json
- Rich persona with socioeconomic factors, misconceptions
- Populated information tiers with 5-10 items each
- Disease-specific evaluation criteria
- Detailed task instructions for role-playing

Usage:
    from medical_task_suite.generation.v2.task_generation import MedicalTaskGenerator
    from medical_task_suite.clinical_knowledge.accessor import ClinicalKnowledgeBase

    kb = ClinicalKnowledgeBase.get_instance()
    gen = MedicalTaskGenerator(kb)

    # Single task
    task = gen.generate_task(task_type="diagnostic_uncertainty", difficulty="L2")

    # Batch
    tasks = gen.generate_batch(n=50, output_path="tasks/output.json")
"""

import json
import math
import random
import uuid
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from ..scenario_engine.scenario_generator import ScenarioGenerator
from ..scenario_engine.scenario_schema import ScenarioSpec, TASK_TYPES
from ..clinical_world.symptom_generator import SymptomGenerator, SymptomSet
from ..clinical_world.patient_language import PatientLanguageLayer, CLINICAL_TO_PATIENT


# ============================================================
# Behavior → patient cooperation style mapping
# ============================================================

BEHAVIOR_PROFILES = {
    "cooperative": {
        "cooperation_level": "good",
        "communication_style": "clear",
        "education_level": "high_school",
        "will_volunteer": True,
        "needs_empathy": False,
        "concerns": [],
    },
    "forgetful": {
        "cooperation_level": "good",
        "communication_style": "vague",
        "education_level": "elementary",
        "will_volunteer": True,
        "needs_empathy": False,
        "concerns": ["may forget to mention symptoms"],
    },
    "confused": {
        "cooperation_level": "moderate",
        "communication_style": "uncertain",
        "education_level": "elementary",
        "will_volunteer": True,
        "needs_empathy": True,
        "concerns": ["doesn't understand medical terms", "needs simple explanations"],
    },
    "concealing": {
        "cooperation_level": "poor",
        "communication_style": "evasive",
        "education_level": "high_school",
        "will_volunteer": False,
        "needs_empathy": True,
        "concerns": ["hiding symptoms", "avoiding bad news", "may deflect questions"],
    },
    "pressuring": {
        "cooperation_level": "moderate",
        "communication_style": "demanding",
        "education_level": "college",
        "will_volunteer": True,
        "needs_empathy": False,
        "concerns": ["wants quick resolution", "impatient with questions"],
    },
    "refusing": {
        "cooperation_level": "poor",
        "communication_style": "resistant",
        "education_level": "middle_school",
        "will_volunteer": False,
        "needs_empathy": True,
        "concerns": ["may refuse tests", "may refuse medications", "distrustful"],
    },
}

# Task type → tool category focus
TASK_TYPE_TOOL_FOCUS = {
    "diagnostic_uncertainty": {
        "primary_category": "diagnosis",
        "required_tool_types": ["order_lab_tests", "get_lab_results", "differential_diagnosis", "record_diagnosis"],
        "focus_description": "Systematic information gathering and differential diagnosis",
    },
    "conflicting_evidence": {
        "primary_category": "diagnosis",
        "required_tool_types": ["order_lab_tests", "get_lab_results", "differential_diagnosis", "record_diagnosis"],
        "focus_description": "Resolving conflicting clinical evidence",
    },
    "treatment_tradeoff": {
        "primary_category": "treatment",
        "required_tool_types": ["check_allergy", "check_drug_interactions", "prescribe_medication", "schedule_followup"],
        "focus_description": "Weighing treatment options with comorbidity considerations",
    },
    "patient_non_compliance": {
        "primary_category": "suggestion",
        "required_tool_types": ["health_education", "patient_education", "prescribe_medication"],
        "focus_description": "Addressing patient concerns and building treatment adherence",
    },
    "drug_safety_risk": {
        "primary_category": "treatment",
        "required_tool_types": ["check_allergy", "check_drug_interactions", "check_contraindications", "prescribe_medication"],
        "focus_description": "Safe prescribing with allergy and interaction checks",
    },
    "emergency_triage": {
        "primary_category": "diagnosis",
        "required_tool_types": ["assess_vital_signs", "order_lab_tests", "get_lab_results", "record_diagnosis"],
        "focus_description": "Rapid assessment and stabilization",
    },
}

# Common occupations by education level
OCCUPATIONS = {
    "elementary": ["factory worker", "construction worker", "cleaner", "farm worker", "delivery driver"],
    "middle_school": ["truck driver", "restaurant cook", "warehouse worker", "mechanic", "security guard"],
    "high_school": ["office clerk", "sales associate", "technician", "nurse aide", "retail manager"],
    "college": ["engineer", "teacher", "accountant", "manager", "software developer"],
}

# Education level → Chinese label
EDUCATION_LABELS = {
    "elementary": "小学",
    "middle_school": "初中",
    "high_school": "高中/中专",
    "college": "大学",
}

# Disease-specific misconception templates
DISEASE_MISCONCEPTIONS = {
    "diabetes": {
        "insulin_fears": [
            "I heard insulin is addictive — once you start, you can never stop",
            "My neighbor's aunt took insulin and got so thin, it's scary",
        ],
        "medication_concerns": [
            "Long-term diabetes medication will ruin my kidneys",
            "Western medicine has too many side effects, can I take Chinese herbs instead?",
            "Can I just control it with diet instead of medication?",
        ],
        "dietary_extremes": [
            "Does having diabetes mean I can never eat anything sweet?",
            "Are fruits completely off-limits now?",
            "Do I have to only eat whole grains and never eat rice again?",
        ],
        "prognosis_concerns": [
            "Will I go blind or lose my legs soon?",
            "How many years do I have left?",
        ],
    },
    "hypertension": {
        "medication_concerns": [
            "I feel fine, do I really need to take blood pressure medicine?",
            "Will I become dependent on blood pressure medication?",
            "I heard blood pressure medicine causes impotence",
        ],
        "lifestyle_beliefs": [
            "My blood pressure is only high because I'm stressed at work",
            "If I cut out salt completely, I won't need medication",
        ],
    },
    "heart": {
        "anxiety_fears": [
            "Am I going to have a heart attack?",
            "Will I need bypass surgery?",
            "Can I still exercise?",
        ],
        "medication_concerns": [
            "Do I have to take heart medication for the rest of my life?",
            "I heard statins damage your liver",
        ],
    },
    "copd": {
        "smoking_denial": [
            "My grandfather smoked until he was 90 and was fine",
            "I've already quit, why isn't my breathing better?",
        ],
        "inhaler_concerns": [
            "Are inhalers addictive?",
            "I don't want to use steroids",
        ],
    },
    "kidney": {
        "dialysis_fears": [
            "Will I need dialysis?",
            "How long until my kidneys fail completely?",
        ],
        "dietary_restrictions": [
            "What can I even eat anymore?",
            "Do I have to drink less water?",
        ],
    },
    "arthritis": {
        "exercise_misconception": [
            "Should I stop exercising so I don't wear out my joints?",
            "My joints hurt, shouldn't I just rest?",
        ],
        "medication_concerns": [
            "I heard arthritis painkillers damage your stomach",
            "Is there a cure for arthritis?",
        ],
    },
}


# ============================================================
# Disease Template Categories — auto-adapt by disease type
# ============================================================

DISEASE_TEMPLATES = {
    "metabolic": {
        "diseases": ["diabetes", "hyperlipidemia", "metabolic", "obesity", "thyroid"],
        "key_assessment_areas": ["blood glucose control", "organ complications", "lifestyle factors"],
        "safety_focus": ["kidney function before medication", "hypoglycemia risk", "liver function"],
        "typical_lab_conflict": "borderline HbA1c vs high fasting glucose",
        "common_complication_interactions": "may worsen fatigue, confusing with disease-related tiredness",
    },
    "cardiovascular": {
        "diseases": ["hypertension", "heart", "cardiac", "atrial", "coronary", "heart failure"],
        "key_assessment_areas": ["cardiac risk factors", "exercise tolerance", "medication interactions"],
        "safety_focus": ["bleeding risk with anticoagulants", "blood pressure control", "potassium monitoring"],
        "typical_lab_conflict": "normal troponin with angina symptoms",
        "common_complication_interactions": "may cause overlapping chest symptoms",
    },
    "pulmonary": {
        "diseases": ["copd", "asthma", "pneumonia", "pulmonary", "respiratory"],
        "key_assessment_areas": ["smoking history", "oxygenation status", "inhaler technique"],
        "safety_focus": ["oxygen saturation monitoring", "respiratory distress signs"],
        "typical_lab_conflict": "normal chest X-ray with significant dyspnea",
        "common_complication_interactions": "may worsen breathlessness",
    },
    "renal": {
        "diseases": ["kidney", "renal", "nephrolithiasis", "nephrotic"],
        "key_assessment_areas": ["GFR trajectory", "electrolyte balance", "medication dose adjustment"],
        "safety_focus": ["avoid nephrotoxic drugs", "monitor potassium", "fluid restriction"],
        "typical_lab_conflict": "stable creatinine but declining GFR",
        "common_complication_interactions": "may cause overlapping swelling/fatigue",
    },
    "rheumatologic": {
        "diseases": ["arthritis", "gout", "lupus", "rheumatoid", "osteoarthritis", "psoriasis"],
        "key_assessment_areas": ["joint involvement pattern", "inflammatory markers", "functional impact"],
        "safety_focus": ["NSAID GI risk", "immunosuppression monitoring"],
        "typical_lab_conflict": "normal uric acid during acute gout attack",
        "common_complication_interactions": "may cause overlapping joint pain",
    },
    "neurological": {
        "diseases": ["stroke", "epilepsy", "migraine", "parkinson", "multiple sclerosis"],
        "key_assessment_areas": ["neurological deficits", "seizure history", "functional decline"],
        "safety_focus": ["aspiration risk", "fall prevention", "seizure precautions"],
        "typical_lab_conflict": "normal imaging with acute neurological symptoms",
        "common_complication_interactions": "may cause overlapping confusion/weakness",
    },
    "gastrointestinal": {
        "diseases": ["cirrhosis", "gerd", "pancreat", "peptic ulcer", "hepatitis"],
        "key_assessment_areas": ["liver function", "GI bleeding risk", "nutritional status"],
        "safety_focus": ["bleeding risk", "hepatic dose adjustment", "alcohol interaction"],
        "typical_lab_conflict": "normal liver enzymes with significant liver disease",
        "common_complication_interactions": "may cause overlapping abdominal symptoms",
    },
    "hematologic": {
        "diseases": ["anemia", "sickle cell", "leukemia", "thalassemia", "coagulation"],
        "key_assessment_areas": ["bleeding history", "transfusion needs", "infection risk"],
        "safety_focus": ["infection precautions", "bleeding risk", "transfusion reactions"],
        "typical_lab_conflict": "normal hemoglobin with significant symptoms",
        "common_complication_interactions": "may cause overlapping fatigue/weakness",
    },
}

# Cross-overlapping and atypical misleading symptoms per disease category
DISEASE_MISLEADING_MAP = {
    "type 2 diabetes": {
        "cross_overlapping": [
            "unexplained weight loss (also seen in hyperthyroidism and cancer)",
            "persistent fatigue (also seen in anemia and depression)",
            "frequent infections (also seen in immunodeficiency)",
        ],
        "atypical": [
            "recurrent skin infections and slow wound healing",
            "recurrent urinary tract infections",
            "blurred vision that comes and goes",
            "tingling or numbness in hands and feet",
        ],
    },
    "hypertension": {
        "cross_overlapping": [
            "morning headache (also seen in sleep apnea and migraine)",
            "dizziness (also seen in anemia and inner ear disorders)",
        ],
        "atypical": [
            "nosebleeds without obvious cause",
            "visual changes or spots in vision",
            "ringing in the ears",
        ],
    },
    "coronary artery disease": {
        "cross_overlapping": [
            "chest discomfort (also seen in GERD and anxiety)",
            "left arm pain (also seen in cervical disc disease)",
        ],
        "atypical": [
            "jaw pain during exertion",
            "unusual fatigue with minimal activity",
            "shortness of breath when lying flat",
        ],
    },
    "copd": {
        "cross_overlapping": [
            "chronic cough (also seen in GERD and heart failure)",
            "fatigue (also seen in depression and anemia)",
        ],
        "atypical": [
            "morning headache from CO2 retention",
            "swollen ankles from right heart strain",
            "unexplained weight loss",
        ],
    },
    "chronic kidney disease": {
        "cross_overlapping": [
            "fatigue (also seen in anemia and hypothyroidism)",
            "swelling (also seen in heart failure and liver disease)",
        ],
        "atypical": [
            "persistent itching without rash",
            "metallic taste in mouth",
            "restless legs at night",
            "frequent nighttime urination",
        ],
    },
    "gout": {
        "cross_overlapping": [
            "joint pain and swelling (also seen in rheumatoid arthritis and infection)",
            "redness (also seen in cellulitis)",
        ],
        "atypical": [
            "joint pain in unusual locations (ankle, knee)",
            "attacks triggered by dietary changes",
            "kidney stones as first presentation",
        ],
    },
    "anemia": {
        "cross_overlapping": [
            "fatigue (also seen in depression and hypothyroidism)",
            "shortness of breath (also seen in COPD and heart failure)",
        ],
        "atypical": [
            "unusual cravings for ice or dirt (pica)",
            "sore tongue and mouth ulcers",
            "restless legs",
        ],
    },
    "sickle cell anemia": {
        "cross_overlapping": [
            "severe pain (also seen in acute abdomen)",
            "fatigue (also seen in many chronic conditions)",
        ],
        "atypical": [
            "sudden vision problems",
            "priapism",
            "frequent infections",
            "leg ulcers that won't heal",
        ],
    },
    "stroke": {
        "cross_overlapping": [
            "weakness on one side (also seen in migraine with aura)",
            "confusion (also seen in infection and medication effects)",
        ],
        "atypical": [
            "sudden severe headache without known cause",
            "difficulty speaking or understanding speech",
            "vision loss in one eye",
        ],
    },
    "heart failure": {
        "cross_overlapping": [
            "shortness of breath (also seen in COPD and pneumonia)",
            "swelling (also seen in kidney disease and liver disease)",
        ],
        "atypical": [
            "waking up gasping for air (paroxysmal nocturnal dyspnea)",
            "abdominal swelling and loss of appetite",
            "need to prop up with multiple pillows to sleep",
        ],
    },
}

# Symptom trigger probes — maps symptom keywords to what doctor should ask
SYMPTOM_TRIGGER_PROBES = {
    "numb": "doctor asks about sensations in hands and feet",
    "tingl": "doctor asks about unusual sensations in extremities",
    "vision": "doctor asks about any eye problems or vision changes",
    "sexual": "doctor asks about changes in sexual function",
    "stomach": "doctor asks about digestive problems",
    "breath": "doctor asks about breathing difficulties during activity",
    "sleep": "doctor asks about sleep quality",
    "swell": "doctor asks about any swelling",
    "urin": "doctor asks about urinary habits",
    "chest": "doctor asks about chest discomfort",
    "dizzy": "doctor asks about dizziness",
    "weak": "doctor asks about muscle strength",
    "itch": "doctor asks about skin symptoms",
    "cough": "doctor asks about cough and sputum",
}

# ============================================================
# Environment State Machine
# ============================================================

ENVIRONMENT_STATES = {
    "INITIAL": {
        "description": "Consultation has not started",
        "available_actions": ["greet_patient", "review_ticket"],
        "observations": ["ticket", "patient_demographics"],
    },
    "HISTORY_TAKING": {
        "description": "Doctor is gathering patient history",
        "available_actions": ["ask_patient", "ask_about_symptoms", "ask_about_history", "ask_about_medications", "ask_about_allergies", "ask_about_lifestyle"],
        "observations": ["patient_responses", "volunteer_symptoms"],
    },
    "PHYSICAL_EXAM": {
        "description": "Doctor performs or orders physical examination",
        "available_actions": ["assess_vital_signs", "perform_examination"],
        "observations": ["vital_signs", "exam_findings"],
    },
    "LAB_ORDERED": {
        "description": "Doctor has ordered lab tests, awaiting results",
        "available_actions": ["wait_for_results", "continue_history"],
        "observations": ["tests_ordered"],
    },
    "LAB_RESULTS_AVAILABLE": {
        "description": "Lab results are available for review",
        "available_actions": ["get_lab_results", "review_results", "order_additional_tests"],
        "observations": ["lab_results"],
    },
    "DIAGNOSIS_FORMING": {
        "description": "Doctor is forming differential diagnosis",
        "available_actions": ["differential_diagnosis", "order_additional_tests", "consult_specialist"],
        "observations": ["symptom_summary", "lab_summary"],
    },
    "DIAGNOSIS_MADE": {
        "description": "Doctor has recorded a diagnosis",
        "available_actions": ["record_diagnosis", "communicate_diagnosis"],
        "observations": ["diagnosis"],
    },
    "TREATMENT_PLANNING": {
        "description": "Doctor is planning treatment",
        "available_actions": ["check_allergy", "check_drug_interactions", "check_contraindications", "prescribe_medication", "health_education"],
        "observations": ["allergy_check_result", "interaction_check_result"],
    },
    "PATIENT_DISCUSSION": {
        "description": "Doctor is discussing treatment with patient",
        "available_actions": ["patient_education", "address_concerns", "negotiate_treatment"],
        "observations": ["patient_reaction", "patient_concerns"],
    },
    "PRESCRIPTION_WRITTEN": {
        "description": "Doctor has written prescription",
        "available_actions": ["schedule_followup", "provide_instructions"],
        "observations": ["prescription"],
    },
    "CONSULTATION_COMPLETE": {
        "description": "Consultation is complete",
        "available_actions": [],
        "observations": ["full_summary"],
    },
}

STATE_TRANSITIONS = [
    {"from": "INITIAL", "to": "HISTORY_TAKING", "trigger": "doctor initiates conversation"},
    {"from": "HISTORY_TAKING", "to": "PHYSICAL_EXAM", "trigger": "doctor assesses vital signs or performs exam"},
    {"from": "HISTORY_TAKING", "to": "LAB_ORDERED", "trigger": "doctor orders lab tests"},
    {"from": "PHYSICAL_EXAM", "to": "LAB_ORDERED", "trigger": "doctor orders lab tests"},
    {"from": "PHYSICAL_EXAM", "to": "DIAGNOSIS_FORMING", "trigger": "doctor begins differential diagnosis"},
    {"from": "LAB_ORDERED", "to": "LAB_RESULTS_AVAILABLE", "trigger": "lab results are ready"},
    {"from": "LAB_RESULTS_AVAILABLE", "to": "DIAGNOSIS_FORMING", "trigger": "doctor reviews results and forms diagnosis"},
    {"from": "LAB_RESULTS_AVAILABLE", "to": "LAB_ORDERED", "trigger": "doctor orders additional tests"},
    {"from": "DIAGNOSIS_FORMING", "to": "DIAGNOSIS_MADE", "trigger": "doctor records diagnosis"},
    {"from": "DIAGNOSIS_FORMING", "to": "LAB_ORDERED", "trigger": "doctor orders confirmatory tests"},
    {"from": "DIAGNOSIS_MADE", "to": "TREATMENT_PLANNING", "trigger": "doctor begins treatment planning"},
    {"from": "TREATMENT_PLANNING", "to": "PATIENT_DISCUSSION", "trigger": "doctor discusses treatment options with patient"},
    {"from": "PATIENT_DISCUSSION", "to": "PRESCRIPTION_WRITTEN", "trigger": "doctor writes prescription"},
    {"from": "PATIENT_DISCUSSION", "to": "TREATMENT_PLANNING", "trigger": "patient objects, doctor revises plan"},
    {"from": "PRESCRIPTION_WRITTEN", "to": "CONSULTATION_COMPLETE", "trigger": "doctor provides follow-up instructions"},
    {"from": "DIAGNOSIS_MADE", "to": "PATIENT_DISCUSSION", "trigger": "doctor communicates diagnosis directly to patient"},
]

# ============================================================
# Agent Capability Dimensions
# ============================================================

CAPABILITY_DIMENSIONS = {
    "information_gathering": {
        "description": "Ability to systematically collect patient history, symptoms, and relevant medical information",
        "sub_skills": ["history_taking", "symptom_probe", "hidden_symptom_discovery", "medical_history_review"],
    },
    "diagnostic_reasoning": {
        "description": "Ability to form accurate differential diagnosis based on gathered evidence",
        "sub_skills": ["differential_diagnosis", "evidence_synthesis", "lab_interpretation", "pattern_recognition"],
    },
    "treatment_planning": {
        "description": "Ability to design appropriate, individualized treatment plans",
        "sub_skills": ["medication_selection", "dose_optimization", "comorbidity_management", "guideline_adherence"],
    },
    "safety_awareness": {
        "description": "Ability to identify and avoid medical safety risks",
        "sub_skills": ["allergy_checking", "drug_interaction_check", "contraindication_awareness", "red_flag_detection"],
    },
    "communication_quality": {
        "description": "Ability to communicate effectively with patients at their level of understanding",
        "sub_skills": ["patient_friendly_language", "empathy", "misconception_correction", "shared_decision_making"],
    },
    "efficiency": {
        "description": "Ability to reach correct conclusions with minimal unnecessary actions",
        "sub_skills": ["focused_questioning", "appropriate_test_selection", "time_management", "resource_efficiency"],
    },
}

# ============================================================
# Difficulty Source Factors (structural)
# ============================================================

DIFFICULTY_FACTORS = {
    "symptom_complexity": {
        "description": "Number and overlap of presenting symptoms",
        "L1": "2-3 clear symptoms, classic presentation",
        "L2": "4-6 symptoms with some overlap, partial atypical features",
        "L3": "6+ symptoms, multiple overlapping conditions, atypical presentation",
    },
    "diagnostic_ambiguity": {
        "description": "Number of plausible differential diagnoses and ease of differentiation",
        "L1": "1-2 differentials, easily distinguished",
        "L2": "3-4 differentials, requires specific tests to differentiate",
        "L3": "5+ differentials, conflicting evidence, rare presentations",
    },
    "treatment_complexity": {
        "description": "Number of treatment options, drug interactions, and comorbidity constraints",
        "L1": "Single first-line treatment, no significant interactions",
        "L2": "Multiple options, 1-2 interactions to manage, 1 comorbidity",
        "L3": "Multiple contraindications, polypharmacy, 3+ comorbidities",
    },
    "patient_behavior_difficulty": {
        "description": "How challenging the patient behavior is for information gathering",
        "L1": "cooperative — clear communication, volunteers information",
        "L2": "forgetful/confused — needs prompting, may miss details",
        "L3": "concealing/refusing — actively resists, requires trust-building",
    },
    "information_asymmetry": {
        "description": "Gap between what patient volunteers and what doctor needs to discover",
        "L1": "Most information volunteered, minimal hidden symptoms",
        "L2": "Key symptoms in if_asked/hidden tier, progressive reveal",
        "L3": "Critical symptoms hidden/resistant, adversarial noise, misleading symptoms",
    },
    "comorbidity_burden": {
        "description": "Number and severity of coexisting conditions affecting diagnosis and treatment",
        "L1": "0-1 comorbidities, mild, not affecting primary condition",
        "L2": "1-2 comorbidities, moderate interaction with primary condition",
        "L3": "3+ comorbidities, significant interaction, undiagnosed conditions present",
    },
    "time_pressure": {
        "description": "Urgency level and consequences of delayed action",
        "L1": "No urgency, routine consultation",
        "L2": "Moderate urgency, condition may worsen without timely action",
        "L3": "High urgency, time-sensitive decisions, emergency triage needed",
    },
}

# ============================================================
# Episode Phases
# ============================================================

EPISODE_PHASES = [
    {
        "name": "intake",
        "description": "Initial greeting and chief complaint identification",
        "recommended_turns": (1, 2),
        "required_actions": ["greet_patient", "identify_chief_complaint"],
        "exit_condition": "Chief complaint clearly stated",
    },
    {
        "name": "history_taking",
        "description": "Detailed history collection: symptoms, onset, duration, severity, past history",
        "recommended_turns": (4, 8),
        "required_actions": ["ask_about_symptoms", "ask_about_history", "ask_about_medications", "ask_about_allergies"],
        "exit_condition": "All required history categories covered",
    },
    {
        "name": "examination_and_labs",
        "description": "Physical examination and laboratory testing",
        "recommended_turns": (2, 4),
        "required_actions": ["assess_vital_signs", "order_lab_tests", "get_lab_results"],
        "exit_condition": "Sufficient data collected for diagnosis",
    },
    {
        "name": "diagnosis",
        "description": "Form and record diagnosis with differential consideration",
        "recommended_turns": (2, 3),
        "required_actions": ["differential_diagnosis", "record_diagnosis"],
        "exit_condition": "Diagnosis recorded with supporting evidence",
    },
    {
        "name": "treatment",
        "description": "Plan treatment, check safety, prescribe medication",
        "recommended_turns": (2, 4),
        "required_actions": ["check_allergy", "check_drug_interactions", "prescribe_medication"],
        "exit_condition": "Safe prescription written",
    },
    {
        "name": "patient_communication",
        "description": "Explain diagnosis and treatment, address concerns, ensure understanding",
        "recommended_turns": (2, 4),
        "required_actions": ["communicate_diagnosis", "patient_education", "address_concerns"],
        "exit_condition": "Patient understands plan and concerns addressed",
    },
    {
        "name": "closure",
        "description": "Schedule follow-up and provide final instructions",
        "recommended_turns": (1, 2),
        "required_actions": ["schedule_followup"],
        "exit_condition": "Follow-up scheduled and consultation concluded",
    },
]

# ============================================================
# Formal Action Schema
# ============================================================

ACTION_SCHEMA = {
    "greet_patient": {
        "description": "Greet the patient and introduce yourself",
        "parameters": {"type": "object", "properties": {}, "required": []},
        "returns": {"type": "object", "properties": {"patient_response": {"type": "string"}}},
        "preconditions": ["state == INITIAL"],
        "postconditions": ["state transitions to HISTORY_TAKING"],
        "cost": {"turns": 1},
    },
    "ask_patient": {
        "description": "Ask the patient a question",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question to ask"},
                "category": {"type": "string", "enum": ["symptoms", "history", "medications", "allergies", "lifestyle", "family_history", "other"]},
            },
            "required": ["question"],
        },
        "returns": {
            "type": "object",
            "properties": {
                "patient_response": {"type": "string"},
                "new_information_revealed": {"type": "boolean"},
                "trust_change": {"type": "number", "description": "Change in patient trust (-1 to +1)"},
            },
        },
        "preconditions": ["state in [HISTORY_TAKING, PATIENT_DISCUSSION]"],
        "postconditions": ["turn_count += 1", "information_revealed may increase"],
        "cost": {"turns": 1},
    },
    "assess_vital_signs": {
        "description": "Measure patient vital signs",
        "parameters": {"type": "object", "properties": {"include_bmi": {"type": "boolean", "default": True}}, "required": []},
        "returns": {
            "type": "object",
            "properties": {
                "blood_pressure": {"type": "string"},
                "heart_rate": {"type": "string"},
                "oxygen_saturation": {"type": "string"},
                "temperature": {"type": "string"},
                "bmi": {"type": "string"},
            },
        },
        "preconditions": ["state in [HISTORY_TAKING, PHYSICAL_EXAM]"],
        "postconditions": ["vitals_observed = true", "state may transition to PHYSICAL_EXAM"],
        "cost": {"turns": 1},
    },
    "order_lab_tests": {
        "description": "Order laboratory tests for the patient",
        "parameters": {
            "type": "object",
            "properties": {
                "tests": {"type": "array", "items": {"type": "string"}, "description": "List of test names to order"},
                "rationale": {"type": "string", "description": "Clinical rationale for ordering"},
            },
            "required": ["tests"],
        },
        "returns": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "tests_ordered": {"type": "array"},
                "estimated_wait": {"type": "string"},
            },
        },
        "preconditions": ["state in [HISTORY_TAKING, PHYSICAL_EXAM, DIAGNOSIS_FORMING]"],
        "postconditions": ["labs_ordered = true", "state transitions to LAB_ORDERED"],
        "cost": {"turns": 1},
    },
    "get_lab_results": {
        "description": "Retrieve results of ordered lab tests",
        "parameters": {
            "type": "object",
            "properties": {"patient_id": {"type": "string", "default": "current"}},
            "required": [],
        },
        "returns": {
            "type": "object",
            "properties": {
                "results": {"type": "object", "additionalProperties": {"type": "string"}},
                "all_results_available": {"type": "boolean"},
            },
        },
        "preconditions": ["labs_ordered == true", "state in [LAB_ORDERED, LAB_RESULTS_AVAILABLE]"],
        "postconditions": ["labs_available = true", "state transitions to LAB_RESULTS_AVAILABLE"],
        "cost": {"turns": 1},
    },
    "differential_diagnosis": {
        "description": "Generate differential diagnosis based on available information",
        "parameters": {
            "type": "object",
            "properties": {
                "symptoms": {"type": "array", "items": {"type": "string"}},
                "must_consider": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["symptoms"],
        },
        "returns": {
            "type": "object",
            "properties": {
                "differentials": {"type": "array", "items": {"type": "object"}},
                "reasoning": {"type": "string"},
            },
        },
        "preconditions": ["state in [LAB_RESULTS_AVAILABLE, DIAGNOSIS_FORMING, PHYSICAL_EXAM]"],
        "postconditions": ["differential_generated = true", "state transitions to DIAGNOSIS_FORMING"],
        "cost": {"turns": 1},
    },
    "record_diagnosis": {
        "description": "Record the final diagnosis",
        "parameters": {
            "type": "object",
            "properties": {
                "diagnosis": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "evidence": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["diagnosis"],
        },
        "returns": {
            "type": "object",
            "properties": {"recorded": {"type": "boolean"}, "diagnosis_id": {"type": "string"}},
        },
        "preconditions": ["state in [DIAGNOSIS_FORMING, LAB_RESULTS_AVAILABLE]"],
        "postconditions": ["diagnosis_recorded = true", "state transitions to DIAGNOSIS_MADE"],
        "cost": {"turns": 1},
    },
    "check_allergy": {
        "description": "Check patient allergies",
        "parameters": {
            "type": "object",
            "properties": {"patient_id": {"type": "string", "default": "current"}},
            "required": [],
        },
        "returns": {
            "type": "object",
            "properties": {"allergies": {"type": "array", "items": {"type": "string"}}},
        },
        "preconditions": ["state in [TREATMENT_PLANNING, DIAGNOSIS_MADE]"],
        "postconditions": ["allergy_checked = true"],
        "cost": {"turns": 1},
    },
    "check_drug_interactions": {
        "description": "Check for drug-drug interactions",
        "parameters": {
            "type": "object",
            "properties": {"drug_list": {"type": "array", "items": {"type": "string"}}},
            "required": ["drug_list"],
        },
        "returns": {
            "type": "object",
            "properties": {
                "interactions": {"type": "array"},
                "safe_to_proceed": {"type": "boolean"},
            },
        },
        "preconditions": ["state == TREATMENT_PLANNING"],
        "postconditions": ["interaction_checked = true"],
        "cost": {"turns": 1},
    },
    "check_contraindications": {
        "description": "Check contraindications for a medication given patient conditions",
        "parameters": {
            "type": "object",
            "properties": {
                "medication": {"type": "string"},
                "conditions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["medication"],
        },
        "returns": {
            "type": "object",
            "properties": {
                "contraindications": {"type": "array"},
                "safe": {"type": "boolean"},
            },
        },
        "preconditions": ["state == TREATMENT_PLANNING"],
        "postconditions": ["contraindication_checked = true"],
        "cost": {"turns": 1},
    },
    "prescribe_medication": {
        "description": "Prescribe a medication to the patient",
        "parameters": {
            "type": "object",
            "properties": {
                "medication": {"type": "string"},
                "dose": {"type": "string"},
                "frequency": {"type": "string"},
                "duration": {"type": "string"},
            },
            "required": ["medication"],
        },
        "returns": {
            "type": "object",
            "properties": {
                "prescription_id": {"type": "string"},
                "prescribed": {"type": "boolean"},
                "warnings": {"type": "array"},
            },
        },
        "preconditions": ["allergy_checked == true", "diagnosis_recorded == true"],
        "postconditions": ["prescription_written = true", "state transitions to PRESCRIPTION_WRITTEN"],
        "cost": {"turns": 1},
    },
    "health_education": {
        "description": "Provide health education to the patient",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "key_points": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["topic"],
        },
        "returns": {
            "type": "object",
            "properties": {
                "patient_understanding": {"type": "number"},
                "questions_asked": {"type": "array"},
            },
        },
        "preconditions": ["state in [TREATMENT_PLANNING, PATIENT_DISCUSSION, DIAGNOSIS_MADE]"],
        "postconditions": ["education_provided = true"],
        "cost": {"turns": 1},
    },
    "patient_education": {
        "description": "Educate patient about their condition and treatment",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "use_simple_language": {"type": "boolean", "default": True},
            },
            "required": ["topic"],
        },
        "returns": {
            "type": "object",
            "properties": {
                "patient_understanding": {"type": "number", "minimum": 0, "maximum": 1},
                "misconceptions_corrected": {"type": "array"},
            },
        },
        "preconditions": ["state in [PATIENT_DISCUSSION, DIAGNOSIS_MADE]"],
        "postconditions": ["patient_educated = true"],
        "cost": {"turns": 1},
    },
    "schedule_followup": {
        "description": "Schedule a follow-up appointment",
        "parameters": {
            "type": "object",
            "properties": {
                "timeframe": {"type": "string"},
                "reason": {"type": "string"},
                "tests_to_repeat": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["timeframe"],
        },
        "returns": {
            "type": "object",
            "properties": {
                "appointment_scheduled": {"type": "boolean"},
                "date": {"type": "string"},
            },
        },
        "preconditions": ["prescription_written == true"],
        "postconditions": ["followup_scheduled = true", "state transitions to CONSULTATION_COMPLETE"],
        "cost": {"turns": 1},
    },
}

# ============================================================
# Observation Field Model
# ============================================================

OBSERVATION_FIELDS = {
    # Always observable
    "patient_demographics": {
        "field": "age, gender, name, mrn",
        "observable": "always",
        "noise_level": 0.0,
        "source": "initial_state",
    },
    "ticket": {
        "field": "chief_complaint",
        "observable": "always",
        "noise_level": 0.0,
        "source": "ticket",
    },
    "patient_verbal_responses": {
        "field": "what patient says in response to questions",
        "observable": "on_ask",
        "noise_level": 0.05,
        "noise_type": "occasional_vagueness",
        "source": "user_scenario.information_sharing_strategy",
    },
    "vital_signs": {
        "field": "blood_pressure, heart_rate, oxygen_saturation, bmi",
        "observable": "after_assess_vital_signs",
        "noise_level": 0.02,
        "noise_type": "measurement_variance",
        "source": "medical_persona.vital_signs",
    },
    "lab_results": {
        "field": "all ordered test results",
        "observable": "after_get_lab_results",
        "noise_level": 0.01,
        "noise_type": "lab_variance",
        "source": "medical_persona.lab_results",
    },
    "volunteer_symptoms": {
        "field": "symptoms patient volunteers without prompting",
        "observable": "in_turn_1",
        "noise_level": 0.0,
        "source": "information_sharing_strategy.volunteer_without_asking",
    },
    "if_asked_symptoms": {
        "field": "symptoms revealed only if specifically asked",
        "observable": "on_specific_question",
        "noise_level": 0.05,
        "noise_type": "partial_recall",
        "source": "information_sharing_strategy.share_only_if_asked",
        "trigger": "question matches symptom keyword",
    },
    "hidden_symptoms": {
        "field": "symptoms patient won't mention unless carefully probed",
        "observable": "on_targeted_probe",
        "noise_level": 0.10,
        "noise_type": "reluctance_delay",
        "source": "information_sharing_strategy.hidden_truth",
        "trigger": "specific medical question about the symptom area",
    },
    "resistant_symptoms": {
        "field": "sensitive symptoms requiring trust/empathy to reveal",
        "observable": "after_trust_threshold",
        "noise_level": 0.15,
        "noise_type": "emotional_barrier",
        "source": "information_sharing_strategy.resistant_to_share",
        "trigger": "empathy demonstrated + specific question",
    },
    "undiagnosed_comorbidities": {
        "field": "conditions patient has but doesn't know about",
        "observable": "through_symptom_correlation",
        "noise_level": 0.20,
        "noise_type": "patient_unaware",
        "source": "information_state.undiagnosed_comorbidities",
        "trigger": "doctor recognizes symptom pattern + orders relevant tests",
    },
    "patient_misconceptions": {
        "field": "incorrect beliefs patient holds",
        "observable": "when_patient_expresses_concern",
        "noise_level": 0.0,
        "source": "information_state.patient_misconceptions_and_concerns",
        "trigger": "treatment discussion or patient asks question",
    },
    "correct_diagnosis": {
        "field": "the actual diagnosis",
        "observable": "never_to_agent",
        "noise_level": 0.0,
        "source": "ground_truth.correct_diagnosis",
        "note": "only available to evaluator, never to agent",
    },
}


class MedicalTaskGenerator:
    """
    Convert v2.7 ScenarioSpec + SymptomSet → rich tau2-bench task JSON.

    Generates detailed, benchmark-quality tasks with:
    - Patient-friendly symptom language
    - Realistic lab values and vital signs
    - Detailed persona with socioeconomic factors
    - Rich information sharing tiers
    - Disease-specific evaluation criteria
    """

    def __init__(self, clinical_kb, primekg=None):
        self.kb = clinical_kb
        self.primekg = primekg
        self.scenario_gen = ScenarioGenerator(clinical_kb, primekg)
        self.symptom_gen = SymptomGenerator(clinical_kb, primekg)
        self.lang = PatientLanguageLayer()
        self._tool_registry = self._load_tool_registry()
        self._rng = random.Random(42)  # Deterministic default; overridden per-task

    def _load_tool_registry(self) -> Dict:
        try:
            data_path = Path(__file__).parent.parent.parent.parent / "clinical_knowledge" / "data" / "tool_registry.json"
            if data_path.exists():
                with open(data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    # ============================================================
    # Public API
    # ============================================================

    def generate_task(
        self,
        task_type: str = "diagnostic_uncertainty",
        difficulty: str = "L2",
        target_disease: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        # Deterministic RNG: same seed always produces identical task
        self._rng = random.Random(seed if seed is not None else 42)

        # Step 1: Generate scenario
        scenario = self.scenario_gen.generate(
            task_type, difficulty,
            target_disease=target_disease,
            seed=seed,
        )

        # Step 2: Generate symptoms
        disease = scenario.target_disease or "fatigue"
        symptoms = self.symptom_gen.generate(disease, scenario, seed=seed)

        # Step 3: Get disease profile from KB
        profile = self.kb.get_disease_profile(disease)

        # Step 4: Generate patient persona
        persona = self._generate_patient_persona(scenario, profile)

        # Step 5: Build task
        task = self._build_task(scenario, symptoms, profile, persona, seed=seed)
        return task

    def generate_batch(
        self,
        n: int = 50,
        task_types: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        seed: int = 42,
    ) -> List[Dict[str, Any]]:
        task_types = task_types or TASK_TYPES
        difficulties = difficulties or ["L1", "L2", "L3"]
        rng = random.Random(seed)

        tasks = []
        for i in range(n):
            tt = task_types[i % len(task_types)]
            diff = difficulties[i % len(difficulties)]
            s = rng.randint(0, 999999)

            try:
                task = self.generate_task(tt, diff, seed=s)
                tasks.append(task)
            except Exception:
                continue

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=2, ensure_ascii=False)

        return tasks

    # ============================================================
    # Task Construction
    # ============================================================

    def _build_task(
        self,
        scenario: ScenarioSpec,
        symptoms: SymptomSet,
        profile,
        persona: Dict,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        disease = scenario.target_disease or "unknown"
        # Deterministic task_id from seed instead of uuid4
        import hashlib
        id_input = f"{scenario.task_type}|{scenario.difficulty}|{disease}|{seed}"
        task_hash = hashlib.sha256(id_input.encode()).hexdigest()[:6]
        task_id = f"v27_{scenario.task_type}_{scenario.difficulty}_{disease.replace(' ', '_')[:30]}_{task_hash}"

        return {
            "id": task_id,
            "domain": self._infer_domain(disease),
            "task_type": scenario.task_type,
            "difficulty": scenario.difficulty,
            "version": "2.7",

            "description": self._build_description(scenario, profile, persona),
            "user_scenario": self._build_user_scenario(scenario, symptoms, profile, persona),
            "medical_persona": self._build_medical_persona(scenario, profile, symptoms, persona),
            "ticket": self._build_ticket(scenario, symptoms),
            "initial_state": self._build_initial_state(persona, symptoms),
            "evaluation_criteria": self._build_evaluation_criteria(scenario, profile),

            # --- New structural additions ---
            "ground_truth": self._build_ground_truth(scenario, symptoms, profile),
            "environment_dynamics": self._build_environment_dynamics(scenario, disease),
            "outcome_criteria": self._build_outcome_criteria(scenario, profile, disease),
            "episode_structure": self._build_episode_structure(scenario, disease),
            "capability_dimensions": self._build_capability_dimensions(scenario, disease),
            "difficulty_profile": self._build_difficulty_profile(scenario, disease, symptoms),

            # --- Execution layer ---
            "action_space": self._build_action_space(scenario, disease),
            "observation_function": self._build_observation_function(scenario, symptoms, disease),
            "scoring_function": self._build_scoring_function(scenario, disease),
            "agent_api": self._build_agent_api(scenario, disease),
            "execution_config": self._build_execution_config(scenario, disease),

            # --- Verification & calibration layer ---
            "verification": self._build_verification(scenario, disease),
            "score_calibration": self._build_score_calibration(scenario, disease),
            "benchmark_protocol": self._build_benchmark_protocol(scenario, disease),
            "determinism_guarantee": self._build_determinism_guarantee(scenario, seed),

            "generation_metadata": {
                "source": "v2.7_medical_suite",
                "scenario_id": scenario.scenario_id,
                "risk_level": scenario.risk_level,
                "uncertainty_level": scenario.uncertainty_level,
                "behavior_type": scenario.behavior_type,
                "seed": scenario.generation_seed,
            },
        }

    # ============================================================
    # Description Builder
    # ============================================================

    def _build_description(self, scenario: ScenarioSpec, profile, persona: Dict) -> Dict:
        disease = scenario.target_disease or "unknown"
        age = persona.get("age", 50)
        gender = persona.get("gender", "unknown")
        chief = self._get_chief_complaint_text(scenario, persona)

        patient_lang = self.lang.to_patient(disease)

        educational_objectives = self._build_educational_objectives(scenario)
        focus = TASK_TYPE_TOOL_FOCUS.get(scenario.task_type, {})

        return {
            "purpose": f"{scenario.task_type} — {age}-year-old {gender} with {chief}",
            "clinical_scenario": (
                f"Patient presents with {chief}. "
                f"Requires history taking, examination, diagnosis, and treatment planning."
            ),
            "educational_objectives": educational_objectives,
            "focus": focus.get("focus_description", ""),
        }

    def _get_chief_complaint_text(self, scenario: ScenarioSpec, persona: Dict) -> str:
        """Get patient-friendly chief complaint text."""
        symptom_keyword = scenario.symptom_keyword or "symptoms"
        # Convert clinical keyword to patient language
        patient_term = self.lang.to_patient(symptom_keyword)
        duration = persona.get("duration_text", "a few weeks")
        return f"{patient_term} for {duration}"

    def _build_educational_objectives(self, scenario: ScenarioSpec) -> List[str]:
        base = [
            "Assess information gathering ability",
            "Evaluate clinical reasoning",
        ]

        type_specific = {
            "diagnostic_uncertainty": [
                "Ability to probe for hidden symptoms",
                "Quality of differential diagnosis",
            ],
            "conflicting_evidence": [
                "Ability to resolve conflicting data",
                "Critical appraisal of evidence",
            ],
            "treatment_tradeoff": [
                "Consideration of comorbidities in treatment",
                "Shared decision-making ability",
            ],
            "patient_non_compliance": [
                "Communication and trust-building",
                "Addressing patient concerns and misconceptions",
            ],
            "drug_safety_risk": [
                "Safety checking before prescribing",
                "Drug interaction awareness",
            ],
            "emergency_triage": [
                "Rapid assessment and prioritization",
                "Time-sensitive decision making",
            ],
        }

        objectives = base + type_specific.get(scenario.task_type, [])

        if scenario.difficulty == "L3":
            objectives.append("Handle complex multi-condition scenario")
        if scenario.behavior_type in ("concealing", "refusing"):
            objectives.append("Manage difficult patient behavior")

        return objectives

    # ============================================================
    # User Scenario Builder (RICH version)
    # ============================================================

    def _build_user_scenario(
        self,
        scenario: ScenarioSpec,
        symptoms: SymptomSet,
        profile,
        persona: Dict,
    ) -> Dict:
        disease = scenario.target_disease or "unknown"
        behavior = BEHAVIOR_PROFILES.get(scenario.behavior_type, BEHAVIOR_PROFILES["cooperative"])

        chief_complaint = self._build_chief_complaint(scenario, symptoms)

        patient_profile = {
            "age": persona["age"],
            "gender": persona["gender"],
            "education_level": persona.get("education_level", "high_school"),
            "communication_style": behavior["communication_style"],
            "cooperation_level": behavior["cooperation_level"],
            "chief_complaint": chief_complaint,
        }

        # Add occupation if available
        if persona.get("occupation"):
            patient_profile["occupation"] = persona["occupation"]

        information_state = self._build_information_state(scenario, symptoms, profile, persona)
        sharing_strategy = self._build_information_sharing_strategy(symptoms, scenario, profile, persona)
        task_instructions = self._build_task_instructions(scenario, persona, symptoms, profile)

        return {
            "persona": self._build_persona_description(scenario, persona, profile),
            "patient_profile": patient_profile,
            "information_state": information_state,
            "information_sharing_strategy": sharing_strategy,
            "task_instructions": task_instructions,
        }

    def _build_chief_complaint(self, scenario: ScenarioSpec, symptoms: SymptomSet) -> str:
        """Build patient-friendly chief complaint."""
        if symptoms.volunteer:
            chief_symptoms = [self.lang.to_patient(s) for s in symptoms.volunteer[:3]]
        else:
            chief_symptoms = [self.lang.to_patient(scenario.symptom_keyword or "discomfort")]

        duration_map = {"a few weeks": "about a month", "several weeks": "several weeks"}
        duration = duration_map.get(scenario.symptom_keyword or "", "a few weeks")

        parts = []
        for i, s in enumerate(chief_symptoms):
            if i == 0:
                parts.append(s)
            elif i == len(chief_symptoms) - 1:
                parts.append(f"and {s}")
            else:
                parts.append(s)

        complaint = ", ".join(parts) if len(parts) > 2 else " and ".join(parts)
        return f"{complaint} for {duration}"

    def _build_persona_description(self, scenario: ScenarioSpec, persona: Dict, profile) -> str:
        """Build rich natural language persona description."""
        age = persona["age"]
        gender = persona["gender"]
        edu_label = EDUCATION_LABELS.get(persona.get("education_level", "high_school"), "high school")
        occupation = persona.get("occupation", "")
        behavior = scenario.behavior_type

        behavior_desc = {
            "cooperative": "a cooperative patient who answers questions clearly",
            "forgetful": "a patient who may forget to mention some symptoms",
            "confused": "a patient who is confused about medical terms and needs simple explanations",
            "concealing": "a patient who may try to hide or downplay symptoms",
            "pressuring": "a patient who is impatient and wants quick resolution",
            "refusing": "a patient who may resist tests or treatment",
        }

        symptom_keyword = scenario.symptom_keyword or "medical concerns"
        patient_symptom = self.lang.to_patient(symptom_keyword)

        desc = f"{age}-year-old {gender} patient, {edu_label} education"
        if occupation:
            desc += f", works as a {occupation}"
        desc += f". {behavior_desc.get(behavior, 'a patient')} presenting with {patient_symptom}."

        return desc

    def _build_information_state(
        self,
        scenario: ScenarioSpec,
        symptoms: SymptomSet,
        profile,
        persona: Dict,
    ) -> Dict:
        """Build rich information state with patient knowledge layers."""
        disease = scenario.target_disease or "unknown"

        # What patient knows — use patient-friendly language
        patient_knows = {
            "symptoms": [self.lang.to_patient(s) for s in symptoms.volunteer[:5]],
            "duration_approximate": "about a few weeks",
            "general_concern": self.lang.to_patient(scenario.symptom_keyword or "not feeling well"),
        }

        # Add family history if known
        gt = scenario.ground_truth
        if gt and gt.comorbidities:
            family_hist = []
            for c in gt.comorbidities[:2]:
                family_hist.append(f"family member has {self.lang.to_patient(c.name)}")
            if family_hist:
                patient_knows["family_history"] = family_hist[0]

        # Past medical history from comorbidities
        pmh = []
        if gt and gt.comorbidities:
            for c in gt.comorbidities[:3]:
                pmh.append(self.lang.to_patient(c.name))
        if pmh:
            patient_knows["past_history"] = pmh

        # Current medications from KB
        meds = self.kb.get_medications_for_condition(disease)
        if meds:
            med_names = []
            for m in meds[:3]:
                if isinstance(m, dict) and self._rng.random() < m.get("probability", 0.5):
                    med_names.append(f"{m['name']} {m.get('dose', '')} {m.get('frequency', '')}")
            if med_names:
                patient_knows["current_medications"] = med_names

        # What patient doesn't know
        patient_doesnt_know = {
            "diagnosis": disease,
        }

        # Add specific lab values patient doesn't know
        lab_panel = self.kb.get_lab_panel(disease)
        if lab_panel:
            for lab in lab_panel[:3]:
                if lab.get("is_abnormal"):
                    test = lab["test_name"]
                    val = self._generate_realistic_lab_value(lab)
                    test_key = test
                    patient_doesnt_know[test_key] = val

        # Specific medication needed
        if meds:
            primary_med = meds[0]
            if isinstance(primary_med, dict):
                drug_info = self.kb.get_drug_info(primary_med["name"])
                if drug_info:
                    patient_doesnt_know["specific_medication_needed"] = (
                        f"{drug_info.generic_name} "
                        f"({drug_info.standard_doses[0]['dose'] if drug_info.standard_doses else primary_med.get('dose', '')} "
                        f"{drug_info.standard_doses[0]['frequency'] if drug_info.standard_doses else primary_med.get('frequency', '')})"
                    )
                    # Add contraindications as things patient doesn't know about
                    if drug_info.contraindications:
                        patient_doesnt_know["medication_contraindications"] = drug_info.contraindications

        # Patient misconceptions and concerns
        misconceptions = self._build_misconceptions(disease, scenario, persona)

        result = {
            "patient_knows": patient_knows,
            "patient_doesnt_know": patient_doesnt_know,
            "patient_misconceptions_and_concerns": misconceptions,
        }

        # Undiagnosed comorbidities — patient has these but doesn't know
        if scenario.difficulty in ("L2", "L3") and gt and gt.comorbidities:
            undiagnosed = []
            for c in gt.comorbidities:
                if self._rng.random() < (0.5 if scenario.difficulty == "L3" else 0.3):
                    c_profile = self.kb.get_disease_profile(c.name)
                    c_symptoms = self._get_comorbidity_symptoms(c.name)
                    undiagnosed.append({
                        "condition": c.name,
                        "patient_aware_of_symptoms": [self.lang.to_patient(s) for s in c_symptoms[:2]],
                        "patient_unaware_of_diagnosis": True,
                    })
            if undiagnosed:
                result["undiagnosed_comorbidities"] = undiagnosed

        return result

    def _generate_realistic_lab_value(self, lab: Dict) -> str:
        """Generate a realistic lab value string with jitter."""
        base = lab["base_value"]
        low = lab["range_low"]
        high = lab["range_high"]

        # Add small random jitter within range
        jittered = base + self._rng.uniform(-0.1, 0.1) * (high - low)
        jittered = max(low, min(high, jittered))

        # Format appropriately
        if jittered >= 100:
            val_str = f"{jittered:.0f}"
        elif jittered >= 10:
            val_str = f"{jittered:.1f}"
        else:
            val_str = f"{jittered:.2f}"

        unit = lab.get("unit", "")
        abnormal = " (abnormal)" if lab.get("is_abnormal") else ""
        significance = lab.get("clinical_significance", "")

        return f"{val_str} {unit}{abnormal}"

    def _build_misconceptions(self, disease: str, scenario: ScenarioSpec, persona: Dict) -> Dict:
        """Build disease-specific patient misconceptions."""
        disease_lower = disease.lower()
        misconceptions = {}

        # Find matching misconception category
        for key, templates in DISEASE_MISCONCEPTIONS.items():
            if key in disease_lower:
                for category, items in templates.items():
                    misconceptions[category] = items
                break

        # If no disease-specific misconceptions, add generic ones
        if not misconceptions:
            misconceptions["general_concerns"] = [
                "Is this serious?",
                "Will I need surgery?",
                "How long will treatment take?",
            ]

        # Economic concerns based on persona
        if persona.get("economic_status") in ("low", "moderate"):
            misconceptions["economic_concerns"] = [
                "How much will this medication cost per month?",
                "Is there a cheaper alternative?",
                "Will my insurance cover this?",
                "Can we only prescribe what's absolutely necessary?",
            ]

        return misconceptions

    def _build_information_sharing_strategy(
        self, symptoms: SymptomSet, scenario: ScenarioSpec, profile, persona: Dict
    ) -> Dict:
        """Build detailed information sharing strategy with rich tiers + progressive reveal."""
        disease = scenario.target_disease or "unknown"
        behavior_type = scenario.behavior_type

        # Convert symptom tiers to patient-friendly descriptions
        volunteer_items = self._symptoms_to_sharing_items(
            symptoms.volunteer, "volunteer", disease
        )
        if_asked_items = self._symptoms_to_sharing_items(
            symptoms.if_asked, "if_asked", disease
        )

        strategy = {
            "volunteer_without_asking": volunteer_items,
            "share_only_if_asked": if_asked_items,
        }

        # Hidden symptoms with specific probing hints
        if symptoms.hidden:
            hidden_items = self._symptoms_to_sharing_items(
                symptoms.hidden, "hidden", disease
            )
            strategy["hidden_truth"] = hidden_items
            strategy["hidden_note"] = "Only revealed through careful, specific questioning by the doctor"

        # Resistant symptoms need trust/empathy
        if symptoms.resistant:
            resistant_items = self._symptoms_to_sharing_items(
                symptoms.resistant, "resistant", disease
            )
            strategy["resistant_to_share"] = resistant_items
            strategy["resistance_note"] = "Patient needs empathy and trust before revealing these symptoms"

        # Noise symptoms (distracting unrelated)
        if symptoms.noise:
            noise_items = [self.lang.to_patient(s) for s in symptoms.noise[:3]]
            strategy["noise_symptoms"] = noise_items
            strategy["noise_note"] = "Unrelated symptoms that may distract from the main issue"

        # Misleading symptoms — ENHANCED with cross-overlapping and atypical
        misleading_items = [self.lang.to_patient(s) for s in symptoms.misleading[:3]]
        # Add disease-specific misleading from DISEASE_MISLEADING_MAP
        disease_lower = disease.lower()
        for key in DISEASE_MISLEADING_MAP:
            if key in disease_lower:
                misl_map = DISEASE_MISLEADING_MAP[key]
                # Add atypical presentations
                for atyp in misl_map.get("atypical", [])[:2]:
                    if atyp not in misleading_items:
                        misleading_items.append(atyp)
                # Add cross-overlapping
                for cross in misl_map.get("cross_overlapping", [])[:2]:
                    if cross not in misleading_items:
                        misleading_items.append(cross)
                break
        if misleading_items:
            strategy["misleading_symptoms"] = misleading_items[:6]
            strategy["misleading_note"] = (
                "Symptoms that may point toward an incorrect diagnosis or overlap with other conditions. "
                "Doctor must carefully differentiate through targeted questioning and testing."
            )

        # Progressive reveal — symptoms unlocked at specific dialogue turns
        progressive = self._build_progressive_reveal(symptoms, scenario, disease)
        if progressive:
            strategy["progressive_reveal"] = progressive

        # Add medication discussion items
        meds = self.kb.get_medications_for_condition(disease)
        if meds:
            med_discussion = []
            for m in meds[:2]:
                if isinstance(m, dict):
                    drug_info = self.kb.get_drug_info(m["name"])
                    if drug_info and drug_info.contraindications:
                        med_discussion.append(
                            f"Concerns about {drug_info.generic_name} side effects — {', '.join(drug_info.contraindications)}"
                        )
            if med_discussion:
                strategy["share_in_response_to_medication_discussion"] = med_discussion

        # Response style
        behavior = BEHAVIOR_PROFILES.get(behavior_type, BEHAVIOR_PROFILES["cooperative"])
        strategy["response_style"] = {
            "honest": behavior_type in ("cooperative", "forgetful", "confused"),
            "direct": behavior_type in ("cooperative", "pressuring"),
            "limited_medical_knowledge": True,
            "may_need_clarification": ["medical terminology", "complex concepts"] if persona.get("education_level") in ("elementary", "middle_school") else [],
            "emotional_state": {
                "cooperative": "neutral",
                "forgetful": "neutral",
                "confused": "anxious",
                "concealing": "guarded",
                "pressuring": "impatient",
                "refusing": "hostile",
            }.get(behavior_type, "neutral"),
            "may_resist_certain_treatments": self._get_resistance_treatments(disease, behavior_type),
            "financial_constraints": persona.get("economic_status") in ("low", "moderate"),
        }

        return strategy

    def _build_progressive_reveal(
        self, symptoms: SymptomSet, scenario: ScenarioSpec, disease: str
    ) -> List[Dict]:
        """Build turn-gated progressive symptom reveal schedule."""
        min_turns = max(3, scenario.constraints.min_required_questions)
        progressive = []

        # Collect all symptoms eligible for progressive reveal
        reveal_pool = list(symptoms.hidden) + list(symptoms.resistant)

        # For L3, also add comorbidity symptoms
        if scenario.difficulty == "L3":
            gt = scenario.ground_truth
            if gt and gt.comorbidities:
                for c in gt.comorbidities[:2]:
                    c_symptoms = self._get_comorbidity_symptoms(c.name)
                    reveal_pool.extend(c_symptoms[:2])

        if not reveal_pool:
            return progressive

        self._rng.shuffle(reveal_pool)
        used = set()

        for i, symptom in enumerate(reveal_pool[:5]):
            patient_term = self.lang.to_patient(symptom)
            if patient_term in used:
                continue
            used.add(patient_term)

            # Assign turn number: spread across the consultation
            turn = min_turns + i * self._rng.randint(1, 3)
            turn = min(turn, scenario.constraints.max_turns - 3)

            # Find trigger probe
            trigger = self._find_trigger_probe(symptom)

            progressive.append({
                "after_turn": turn,
                "symptom": patient_term,
                "trigger": trigger,
            })

        return progressive

    def _get_comorbidity_symptoms(self, comorbidity_name: str) -> List[str]:
        """Get symptom list for a comorbidity."""
        profile = self.kb.get_disease_profile(comorbidity_name)
        symptoms = []
        if hasattr(profile, 'differential_questions') and profile.differential_questions:
            symptoms = [q.replace("?", "").strip() for q in profile.differential_questions if len(q) < 40]
        if not symptoms and hasattr(profile, 'aliases') and profile.aliases:
            symptoms = profile.aliases[:3]
        if not symptoms:
            symptoms = ["fatigue", "discomfort"]
        return symptoms[:4]

    def _find_trigger_probe(self, symptom: str) -> str:
        """Find what doctor question would trigger this symptom reveal."""
        symptom_lower = symptom.lower()
        for keyword, probe in SYMPTOM_TRIGGER_PROBES.items():
            if keyword in symptom_lower:
                return probe
        return "doctor asks a specific follow-up question about related symptoms"

    def _symptoms_to_sharing_items(
        self, symptom_list: List[str], tier: str, disease: str
    ) -> List[str]:
        """Convert symptom names to rich sharing items with context."""
        items = []
        for s in symptom_list[:8]:
            patient_term = self.lang.to_patient(s)
            if tier == "volunteer":
                items.append(patient_term)
            elif tier == "if_asked":
                items.append(f"{patient_term} (needs doctor to specifically ask)")
            elif tier == "hidden":
                items.append(f"{patient_term} (won't mention unless specifically probed)")
            elif tier == "resistant":
                items.append(f"{patient_term} (reluctant to discuss, needs trust)")
            else:
                items.append(patient_term)
        return items

    def _get_resistance_treatments(self, disease: str, behavior_type: str) -> List[str]:
        """Get treatments patient may resist based on disease and behavior."""
        resistances = []
        disease_lower = disease.lower()

        if "diabetes" in disease_lower:
            resistances.extend(["insulin", "long_term_medication"])
        if behavior_type == "refusing":
            resistances.extend(["expensive_medications", "multiple_medications"])
        if behavior_type == "concealing":
            resistances.append("procedures")

        return resistances

    def _build_task_instructions(
        self,
        scenario: ScenarioSpec,
        persona: Dict,
        symptoms: SymptomSet,
        profile,
    ) -> str:
        """Build detailed task instructions for the patient actor."""
        disease = scenario.target_disease or "unknown"
        age = persona["age"]
        gender = persona["gender"]
        behavior = scenario.behavior_type
        edu_label = EDUCATION_LABELS.get(persona.get("education_level", "high_school"), "high school")
        occupation = persona.get("occupation", "")
        chief = symptoms.volunteer[0] if symptoms.volunteer else (scenario.symptom_keyword or "symptoms")
        chief_patient = self.lang.to_patient(chief)

        name = persona.get("name", "the patient")

        # Build detailed instructions
        instructions = f"You are {name}, a {age}-year-old {gender} patient. "
        instructions += f"Your education level is {edu_label}."
        if occupation:
            instructions += f" You work as a {occupation}."
        instructions += f" You are seeing a doctor because of {chief_patient}. "

        # Duration
        instructions += "This has been going on for about a few weeks. "

        # Behavior-specific instructions
        behavior_instructions = {
            "cooperative": (
                "Answer the doctor's questions honestly and completely. "
                "Share what you know about your symptoms. "
                "You don't know much about medicine, so express things in your own words."
            ),
            "forgetful": (
                "Answer honestly but you may forget to mention some symptoms. "
                "If the doctor doesn't specifically ask about something, you might not remember it. "
                "Your memory for details is not great — approximate answers are fine."
            ),
            "confused": (
                "You don't understand medical terms. Express your symptoms in your own simple words. "
                "Ask for clarification if the doctor uses terms you don't understand. "
                "You've been reading about your symptoms online and you're worried it might be something serious."
            ),
            "concealing": (
                "You are reluctant to share certain symptoms, especially sensitive ones. "
                "Downplay severity when you can. Only reveal details if the doctor specifically asks "
                "and you feel comfortable. You don't want to make a big deal out of this."
            ),
            "pressuring": (
                "You want this visit to be quick. Express impatience if the doctor asks too many questions. "
                "Push for a quick diagnosis and treatment. You've been dealing with this for a while "
                "and you want answers NOW."
            ),
            "refusing": (
                "You are skeptical of medical advice. You may refuse certain tests or medications. "
                "Express concerns about side effects, costs, and whether treatment is really necessary. "
                "You prefer to handle things yourself when possible."
            ),
        }
        instructions += behavior_instructions.get(behavior, "Answer the doctor's questions honestly.")

        # Hidden symptom hint
        if symptoms.hidden:
            instructions += (
                f" You have some symptoms you haven't mentioned to anyone — "
                f"only reveal them if the doctor specifically asks about them."
            )

        # Resistant symptom hint
        if symptoms.resistant:
            instructions += (
                f" There are some things you're not comfortable talking about. "
                f"Only open up if the doctor shows genuine empathy and you feel safe."
            )

        # Economic sensitivity
        if persona.get("economic_status") in ("low", "moderate"):
            instructions += (
                " You are sensitive about medical costs. "
                "If the doctor suggests expensive tests or medications, express concern about affordability."
            )

        return instructions

    # ============================================================
    # Medical Persona Builder (RICH version)
    # ============================================================

    def _build_medical_persona(
        self,
        scenario: ScenarioSpec,
        profile,
        symptoms: SymptomSet,
        persona: Dict,
    ) -> Dict:
        """Build rich medical_persona section with real lab values and drug details."""
        disease = scenario.target_disease or "unknown"

        # Convert symptoms to patient-friendly descriptions
        symptom_descriptions = {}
        for s in (symptoms.real_symptoms or symptoms.volunteer)[:8]:
            patient_term = self.lang.to_patient(s)
            symptom_descriptions[s] = patient_term

        medical = {
            "age": persona["age"],
            "gender": persona["gender"],
            "symptoms": symptom_descriptions if symptom_descriptions else {
                s: self.lang.to_patient(s) for s in symptoms.volunteer[:5]
            },
            "duration": "a few weeks",
            "severity": self._get_severity(scenario, profile),
        }

        # Past medical history from comorbidities
        gt = scenario.ground_truth
        pmh = []
        if gt and gt.primary and gt.primary.name != "unknown":
            pass  # Primary is the current condition
        if gt and gt.comorbidities:
            for comorb in gt.comorbidities:
                pmh.append(self.lang.to_patient(comorb.name))
        if gt and gt.confounders:
            for conf in gt.confounders:
                pmh.append(self.lang.to_patient(conf.name))
        if pmh:
            medical["past_medical_history"] = pmh

        # Current medications with full details from drug database
        meds = self.kb.get_medications_for_condition(disease)
        current_meds = []
        for m in (meds or [])[:5]:
            if isinstance(m, dict) and self._rng.random() < m.get("probability", 0.5):
                drug_info = self.kb.get_drug_info(m["name"])
                if drug_info:
                    dose_info = drug_info.standard_doses[0] if drug_info.standard_doses else {}
                    current_meds.append({
                        "name": drug_info.generic_name,
                        "brand_names": drug_info.brand_names,
                        "drug_class": drug_info.drug_class,
                        "dose": dose_info.get("dose", m.get("dose", "")),
                        "frequency": dose_info.get("frequency", m.get("frequency", "")),
                    })
                else:
                    current_meds.append({
                        "name": m["name"],
                        "dose": m.get("dose", ""),
                        "frequency": m.get("frequency", ""),
                    })
        if current_meds:
            medical["current_medications"] = current_meds

        # Allergies
        if scenario.constraints.allergy_count > 0:
            medical["allergies"] = self._generate_allergies(scenario.constraints.allergy_count)

        # Lab results — use REAL values from lab_reference.json
        lab_panel = self.kb.get_lab_panel(disease)
        if lab_panel:
            lab_results = {}
            for lab in lab_panel:
                val_str = self._generate_realistic_lab_value(lab)
                test_name = lab["test_name"]
                lab_results[test_name] = val_str
            medical["lab_results"] = lab_results

        # Vital signs from disease profile
        vital_mods = self.kb.get_vital_sign_modifiers(disease)
        if vital_mods:
            vital_signs = {}
            bp = vital_mods.get("blood_pressure", {})
            if bp:
                sys_range = bp.get("systolic_range", [120, 140])
                dia_range = bp.get("diastolic_range", [70, 90])
                systolic = self._rng.randint(sys_range[0], sys_range[1])
                diastolic = self._rng.randint(dia_range[0], dia_range[1])
                vital_signs["blood_pressure"] = f"{systolic}/{diastolic} mmHg"

            hr = vital_mods.get("heart_rate", {})
            if hr:
                hr_range = hr.get("range", [60, 100])
                vital_signs["heart_rate"] = f"{self._rng.randint(hr_range[0], hr_range[1])} bpm"

            spo2 = vital_mods.get("oxygen_saturation", {})
            if spo2:
                spo2_range = spo2.get("range", [95, 100])
                vital_signs["oxygen_saturation"] = f"{self._rng.randint(spo2_range[0], spo2_range[1])}%"

            # BMI (random, higher for diabetes/metabolic)
            bmi_base = 28 if any(k in disease.lower() for k in ["diabetes", "metabolic", "obesity"]) else 24
            bmi = bmi_base + self._rng.uniform(-3, 3)
            vital_signs["bmi"] = f"{bmi:.1f}"

            medical["vital_signs"] = vital_signs
        else:
            # Default vital signs
            medical["vital_signs"] = {
                "blood_pressure": f"{self._rng.randint(120, 145)}/{self._rng.randint(75, 95)} mmHg",
                "bmi": f"{24 + self._rng.uniform(-3, 4):.1f}",
            }

        # Lifestyle factors
        social_hist = self.kb.get_disease_profile(disease).social_history_relevance if hasattr(profile, 'social_history_relevance') else {}
        if not social_hist and hasattr(profile, 'raw'):
            social_hist = profile.raw.get("social_history_relevance", {})

        lifestyle = {}
        if social_hist.get("smoking", False):
            lifestyle["smoking"] = self._rng.choice([
                "yes (half pack/day for 15+ years)",
                "yes (1 pack/day for 20+ years)",
                "quit 2 years ago (former 1 pack/day for 25 years)",
                "no",
            ])
        if social_hist.get("alcohol", False):
            lifestyle["alcohol"] = self._rng.choice([
                "occasional (1-2 drinks/week)",
                "moderate (3-4 drinks/week)",
                "social drinking only",
                "rarely",
            ])
        lifestyle["exercise"] = self._rng.choice(["sedentary", "light activity 1-2x/week", "moderate 3x/week", "minimal"])
        if lifestyle:
            medical["lifestyle_factors"] = lifestyle

        # Comorbidities detail
        comorb_dict = {}
        if gt and gt.comorbidities:
            for c in gt.comorbidities[:5]:
                patient_name = self.lang.to_patient(c.name)
                comorb_dict[c.name] = f"{patient_name}, severity: {c.severity if hasattr(c, 'severity') else 'moderate'}"
        if comorb_dict:
            medical["comorbidities"] = comorb_dict

        # Socioeconomic factors
        medical["socioeconomic_factors"] = {
            "occupation": persona.get("occupation", "not specified"),
            "monthly_income": persona.get("income_text", "not specified"),
            "insurance": persona.get("insurance", "basic coverage"),
        }

        # Medication considerations (drug-specific)
        med_considerations = {}
        if meds:
            primary_med = meds[0]
            if isinstance(primary_med, dict):
                drug_info = self.kb.get_drug_info(primary_med["name"])
                if drug_info:
                    med_considerations[drug_info.generic_name] = {
                        "drug_class": drug_info.drug_class,
                        "standard_dose": f"{drug_info.standard_doses[0]['dose']} {drug_info.standard_doses[0]['frequency']}" if drug_info.standard_doses else "",
                        "contraindications": drug_info.contraindications,
                    }
                    # Check for drug-condition interactions
                    conditions = [c.name for c in (gt.comorbidities if gt else [])]
                    contras = self.kb.get_contraindications(drug_info.generic_name, conditions)
                    if contras:
                        med_considerations[drug_info.generic_name]["condition_contraindications"] = contras
        if med_considerations:
            medical["medication_considerations"] = med_considerations

        # Diagnosis info
        differentials = self.kb.get_differential_diagnoses(disease)
        medical["diagnosis"] = {
            "primary": disease,
            "severity": self._get_severity(scenario, profile),
        }
        if differentials:
            medical["diagnosis"]["differential_diagnoses"] = differentials[:5]

        # Confounders
        if gt and gt.confounders:
            medical["confounder_conditions"] = [c.name for c in gt.confounders]

        # Complication symptoms — detailed comorbidity manifestations
        if gt and gt.comorbidities and scenario.difficulty in ("L2", "L3"):
            tpl = self._get_disease_template(disease)
            complication_symptoms = {}
            for c in gt.comorbidities[:4]:
                c_symptoms = self._get_comorbidity_symptoms(c.name)
                interaction = tpl.get("common_complication_interactions", "may complicate diagnosis")
                complication_symptoms[c.name] = {
                    "symptoms": [self.lang.to_patient(s) for s in c_symptoms[:3]],
                    "status": self._rng.choice(["partially_diagnosed", "undiagnosed", "known_to_patient"]),
                    "interaction_with_primary": interaction,
                }
            if complication_symptoms:
                medical["complication_symptoms"] = complication_symptoms

        return medical

    def _get_severity(self, scenario: ScenarioSpec, profile) -> str:
        """Get severity based on scenario difficulty and disease profile."""
        diff = scenario.difficulty
        if diff == "L1":
            return "mild"
        elif diff == "L3":
            return "severe"
        return "moderate"

    def _generate_allergies(self, count: int) -> List[str]:
        common_allergies = ["penicillin", "sulfa drugs", "aspirin", "ibuprofen", "contrast dye", "latex"]
        return self._rng.sample(common_allergies, min(count, len(common_allergies)))

    # ============================================================
    # Ticket Builder
    # ============================================================

    def _build_ticket(self, scenario: ScenarioSpec, symptoms: SymptomSet) -> str:
        """Build patient-friendly chief complaint ticket."""
        if symptoms.volunteer:
            items = [self.lang.to_patient(s) for s in symptoms.volunteer[:3]]
            return ", ".join(items)
        return self.lang.to_patient(scenario.symptom_keyword or "General consultation")

    # ============================================================
    # Initial State Builder
    # ============================================================

    def _build_initial_state(self, persona: Dict, symptoms: SymptomSet) -> Dict:
        age = persona["age"]
        gender = persona["gender"]
        name = persona.get("name", "Patient")

        # Patient-friendly symptom list
        patient_symptoms = [self.lang.to_patient(s) for s in symptoms.volunteer[:5]]

        return {
            "initialization_actions": [
                {
                    "env_type": "user",
                    "func_name": "set_user_info",
                    "arguments": {
                        "name": name,
                        "mrn": f"MRN{self._rng.randint(100000, 999999)}",
                        "age": age,
                        "gender": gender,
                    },
                },
                {
                    "env_type": "user",
                    "func_name": "set_medical_persona",
                    "arguments": {
                        "patient_profile": {
                            "age": age,
                            "gender": gender,
                            "symptoms": patient_symptoms,
                            "duration": "a few weeks",
                            "severity": "moderate",
                        },
                        "information_sharing_strategy": {
                            "volunteer": [self.lang.to_patient(s) for s in symptoms.volunteer[:3]],
                            "ask_only": [self.lang.to_patient(s) for s in symptoms.if_asked[:3]],
                        },
                        "response_style": {
                            "honest": True,
                            "limited_medical_knowledge": True,
                        },
                    },
                },
            ],
        }

    # ============================================================
    # Evaluation Criteria Builder (RICH version)
    # ============================================================

    def _build_evaluation_criteria(self, scenario: ScenarioSpec, profile) -> Dict:
        disease = scenario.target_disease or "unknown"

        actions = self._build_required_actions(scenario, disease)
        medical_criteria = self._build_medical_criteria(scenario, profile, disease)

        return {
            "actions": actions,
            "communication_checks": self._build_communication_checks(scenario),
            "reward_basis": self._build_reward_basis(scenario),
            "medical_criteria": medical_criteria,
        }

    def _build_required_actions(self, scenario: ScenarioSpec, disease: str) -> List[Dict]:
        focus = TASK_TYPE_TOOL_FOCUS.get(scenario.task_type, {})
        required_tools = focus.get("required_tool_types", [])

        actions = []

        # Always need to gather information
        actions.append({
            "action_id": "gather_patient_history",
            "requestor": "assistant",
            "name": "ask_patient",
            "arguments": {
                "min_questions": scenario.constraints.min_required_questions,
            },
        })

        # Required tools with disease-specific arguments
        for tool in required_tools:
            actions.append({
                "action_id": f"use_{tool}",
                "requestor": "assistant",
                "name": tool,
                "arguments": self._get_tool_args(tool, disease, scenario),
            })

        return actions

    def _get_tool_args(self, tool: str, disease: str, scenario: ScenarioSpec) -> Dict:
        """Get tool arguments with disease-specific content."""
        # Get disease-specific lab tests
        lab_panel = self.kb.get_lab_panel(disease)

        defaults = {
            "order_lab_tests": {
                "tests": [lab["test_name"] for lab in lab_panel[:5]] if lab_panel else ["CBC", "BMP"],
                "rationale": f"Labs to evaluate {disease}",
            },
            "get_lab_results": {"patient_id": "current"},
            "differential_diagnosis": {
                "symptoms": [self.lang.to_patient(disease)],
                "must_consider": self.kb.get_differential_diagnoses(disease)[:3],
            },
            "record_diagnosis": {"diagnosis": disease},
            "check_allergy": {"patient_id": "current"},
            "check_drug_interactions": {
                "drug_list": [m["name"] for m in self.kb.get_medications_for_condition(disease)[:3] if isinstance(m, dict)],
            },
            "prescribe_medication": {
                "medication": self.kb.get_medications_for_condition(disease)[0]["name"] if self.kb.get_medications_for_condition(disease) else "",
                "dose": "",
            },
            "schedule_followup": {"timeframe": "2-4 weeks"},
            "assess_vital_signs": {"include_bmi": True},
            "health_education": {"topic": disease},
            "patient_education": {"topic": disease},
            "check_contraindications": {
                "medication": self.kb.get_medications_for_condition(disease)[0]["name"] if self.kb.get_medications_for_condition(disease) else "",
                "conditions": [c.name for c in (scenario.ground_truth.comorbidities if scenario.ground_truth else [])],
            },
        }
        return defaults.get(tool, {})

    def _build_communication_checks(self, scenario: ScenarioSpec) -> List[Dict]:
        checks = [
            {
                "check_id": "patient_understands",
                "criteria": "Patient should understand the diagnosis and treatment plan",
                "weight": 1.0,
            },
            {
                "check_id": "appropriate_language",
                "criteria": "Uses clear, patient-friendly language appropriate to education level",
                "weight": 1.0,
            },
        ]

        if scenario.behavior_type in ("concealing", "refusing"):
            checks.append({
                "check_id": "trust_building",
                "criteria": "Demonstrates empathy and builds patient trust",
                "weight": 1.5,
            })

        if scenario.difficulty in ("L2", "L3"):
            checks.append({
                "check_id": "addresses_concerns",
                "criteria": "Addresses patient concerns, misconceptions, and questions",
                "weight": 1.0,
            })

        return checks

    def _build_medical_criteria(
        self, scenario: ScenarioSpec, profile, disease: str
    ) -> Dict:
        criteria = {
            "category": self._get_medical_category(scenario.task_type),
            "min_turns": max(3, scenario.constraints.min_required_questions),
            "max_turns": scenario.constraints.max_turns,
        }

        # Information gathering — with disease-specific weights
        differentials = self.kb.get_differential_diagnoses(disease)
        diff_questions = self.kb.get_differential_questions(disease)
        profile_obj = self.kb.get_disease_profile(disease)

        must_collect = {
            "chief_complaint_detail": {
                "required": True,
                "description": "Complete chief complaint with onset, duration, severity, and aggravating/relieving factors",
                "weight": 0.18,
            },
            "symptoms_completeness": {
                "required": True,
                "description": f"All major symptoms of {disease} identified through systematic questioning",
                "weight": 0.20,
            },
            "past_medical_history": {
                "required": True,
                "description": "Relevant past medical history including comorbidities",
                "weight": 0.12,
            },
            "current_medications": {
                "required": True,
                "description": "Current medication list with doses and adherence",
                "weight": 0.15,
            },
            "allergies": {
                "required": True,
                "description": "Drug allergy history",
                "weight": 0.15,
            },
            "family_history": {
                "required": scenario.difficulty != "L1",
                "description": "Relevant family history",
                "weight": 0.08,
            },
            "lifestyle_factors": {
                "required": scenario.difficulty == "L3",
                "description": "Smoking, alcohol, diet, exercise habits",
                "weight": 0.05,
            },
            "social_determinants": {
                "required": scenario.difficulty == "L3",
                "description": "Socioeconomic factors affecting treatment adherence",
                "weight": 0.04,
            },
        }
        criteria["information_gathering_requirements"] = {
            "must_collect": must_collect,
            "scoring_method": "count",
            "pass_threshold": 0.7 if scenario.difficulty == "L1" else 0.8,
        }

        # Diagnostic requirements — disease-specific
        diag_req = {
            "diagnosis_accuracy": {
                "required": True,
                "correct_diagnosis": disease,
                "allow_alternatives": differentials[:3] if differentials else [],
                "weight": 0.35,
            },
            "differential_diagnosis": {
                "required": scenario.difficulty != "L1",
                "must_consider": differentials[:3] if differentials else [],
                "weight": 0.20,
            },
        }

        # Add specific tests if lab panel available
        lab_panel = self.kb.get_lab_panel(disease)
        if lab_panel:
            diag_req["appropriate_tests"] = {
                "must_order": [lab["test_name"] for lab in lab_panel if lab.get("is_abnormal")][:3],
                "should_order": [lab["test_name"] for lab in lab_panel if not lab.get("is_abnormal")][:2],
                "weight": 0.15,
            }

        # Evidence-based requirement
        diag_req["evidence_based"] = {
            "required": True,
            "diagnosis_must_be_based_on": ["symptoms", "lab_results"],
            "weight": 0.10,
        }

        # Differential questions from KB
        if diff_questions:
            diag_req["key_questions"] = {
                "required": scenario.difficulty != "L1",
                "must_ask": diff_questions[:3],
                "weight": 0.10,
            }

        criteria["diagnostic_requirements"] = diag_req

        # Treatment requirements — with drug-specific detail and scenarios
        meds = self.kb.get_medications_for_condition(disease)
        gt = scenario.ground_truth
        if meds and scenario.task_type in ("treatment_tradeoff", "drug_safety_risk", "patient_non_compliance"):
            primary_med = meds[0]
            if isinstance(primary_med, dict):
                drug_info = self.kb.get_drug_info(primary_med["name"])
                treatment_req = {
                    "medication_appropriateness": {
                        "required": True,
                        "should_prescribe": primary_med["name"],
                        "appropriate_dosage": f"{primary_med.get('dose', '')} {primary_med.get('frequency', '')}",
                        "weight": 0.30,
                    },
                }
                if drug_info and drug_info.contraindications:
                    treatment_req["contraindication_awareness"] = {
                        "required": True,
                        "must_check": drug_info.contraindications,
                        "weight": 0.20,
                    }
                criteria["treatment_requirements"] = treatment_req

        # Treatment scenarios — dynamic from drug interactions + comorbidities
        if scenario.difficulty in ("L2", "L3"):
            treatment_scenarios = self._build_treatment_scenarios(disease, scenario, meds)
            if treatment_scenarios:
                criteria["treatment_scenarios"] = treatment_scenarios

        # Safety requirements — with disease context from template
        tpl = self._get_disease_template(disease)
        safety_req = {
            "allergy_check_before_prescribe": {
                "required": True,
                "description": "Must check allergies before prescribing",
                "severity": "critical",
            },
            "drug_interaction_check": {
                "required": scenario.difficulty != "L1",
                "description": "Must check drug interactions before prescribing",
                "severity": "critical" if scenario.difficulty == "L3" else "major",
            },
        }

        # Template-driven safety rules
        for safety_item in tpl.get("safety_focus", []):
            rule_key = safety_item.lower().replace(" ", "_")[:40]
            safety_req[rule_key] = {
                "required": True,
                "description": f"Must assess: {safety_item}",
                "severity": "high" if scenario.difficulty == "L3" else "major",
            }

        # Disease-specific safety rules
        if any(k in disease.lower() for k in ["diabetes", "kidney"]):
            safety_req["kidney_function_before_metformin"] = {
                "required": True,
                "description": "Must assess kidney function before prescribing metformin",
                "severity": "high",
            }
        if any(k in disease.lower() for k in ["heart", "cardiac", "hypertension"]):
            safety_req["blood_pressure_control"] = {
                "required": True,
                "description": "Must assess and address blood pressure",
                "severity": "high",
            }

        criteria["safety_requirements"] = safety_req

        # Required tools
        focus = TASK_TYPE_TOOL_FOCUS.get(scenario.task_type, {})
        if focus:
            criteria["required_tools"] = focus.get("required_tool_types", [])

        # Forbidden actions — DYNAMIC and context-aware
        criteria["forbidden_actions"] = self._build_forbidden_actions(disease, scenario, differentials, meds)

        # Uncertainty events — lab inconsistencies and patient changes
        if scenario.difficulty in ("L2", "L3"):
            uncertainty_events = self._build_uncertainty_events(disease, scenario, lab_panel, tpl)
            if uncertainty_events:
                criteria["uncertainty_events"] = uncertainty_events

        return criteria

    def _build_treatment_scenarios(
        self, disease: str, scenario: ScenarioSpec, meds: List[Dict]
    ) -> List[Dict]:
        """Build treatment decision scenarios from drug data and comorbidities."""
        scenarios = []
        gt = scenario.ground_truth

        # Scenario 1: First-line drug intolerance
        if meds:
            primary_med = meds[0]
            if isinstance(primary_med, dict):
                drug_name = primary_med["name"]
                drug_info = self.kb.get_drug_info(drug_name)
                drug_class = drug_info.drug_class if drug_info else ""
                scenarios.append({
                    "scenario": "first_line_intolerance",
                    "description": f"Patient reports side effects from {drug_name} ({drug_class})",
                    "options": [
                        f"Reduce dose of {drug_name}",
                        f"Switch to alternative medication class",
                        f"Try extended-release formulation",
                        f"Add adjunct medication to manage side effects",
                    ],
                    "correct_approach": f"Start with low-dose {drug_name}, titrate up, monitor symptoms; consider alternative if intolerant",
                    "complexity": "moderate",
                })

        # Scenario 2: Drug interaction with comorbidity medication
        if gt and gt.comorbidities:
            for c in gt.comorbidities[:2]:
                c_meds = self.kb.get_medications_for_condition(c.name)
                if c_meds and meds:
                    c_med = c_meds[0]
                    p_med = meds[0]
                    if isinstance(c_med, dict) and isinstance(p_med, dict):
                        interactions = self.kb.check_drug_interactions([c_med["name"], p_med["name"]])
                        if interactions:
                            scenarios.append({
                                "scenario": "drug_interaction_discovery",
                                "description": (
                                    f"Patient is on {c_med['name']} for {c.name} — "
                                    f"check interaction with proposed {p_med['name']}"
                                ),
                                "options": [
                                    "Adjust dose of one or both medications",
                                    "Choose alternative without interaction",
                                    "Monitor closely if interaction is minor",
                                    "Consult specialist for complex interaction",
                                ],
                                "correct_approach": "Identify interaction, weigh severity, adjust regimen accordingly",
                                "complexity": "high",
                            })
                            break  # One interaction scenario is enough

        # Scenario 3: Contraindication from comorbidity
        if gt and gt.comorbidities and meds:
            primary_med = meds[0]
            if isinstance(primary_med, dict):
                drug_info = self.kb.get_drug_info(primary_med["name"])
                if drug_info and drug_info.contraindications:
                    conditions = [c.name for c in gt.comorbidities]
                    contras = self.kb.get_contraindications(drug_info.generic_name, conditions)
                    if contras:
                        scenarios.append({
                            "scenario": "contraindication_conflict",
                            "description": (
                                f"Standard first-line {drug_info.generic_name} may be contraindicated "
                                f"due to patient's comorbidities: {', '.join(conditions[:3])}"
                            ),
                            "options": [
                                f"Use {drug_info.generic_name} with caution and monitoring",
                                "Select alternative medication without contraindication",
                                "Address contraindication condition first",
                                "Consult specialist for guidance",
                            ],
                            "correct_approach": "Evaluate risk-benefit, consider alternatives, document rationale if proceeding",
                            "complexity": "high",
                        })

        return scenarios[:3]  # Max 3 scenarios

    def _build_forbidden_actions(
        self,
        disease: str,
        scenario: ScenarioSpec,
        differentials: List[str],
        meds: List[Dict],
    ) -> List[str]:
        """Build dynamic, context-aware forbidden actions."""
        forbidden = [
            # General safety
            "Prescribe medication before checking allergies",
            "Agree with patient misconceptions without correction",
            "Ignore abnormal lab values without explanation or follow-up plan",
            # History-taking rigor
            "Diagnose without asking about symptom onset, duration, and progression",
            "Diagnose without exploring at least one differential diagnosis",
            "Dismiss patient concerns without addressing them",
            "Use medical jargon without explanation when patient has limited health literacy",
            # Communication
            "Fail to correct patient misconceptions about treatment",
            "Prescribe contraindicated drug without documenting rationale",
            "Order unnecessary tests without clinical justification",
        ]

        # Disease-specific
        if any(k in disease.lower() for k in ["diabetes", "kidney", "renal"]):
            forbidden.append("Prescribe metformin without checking kidney function (eGFR)")
            forbidden.append("Ignore declining kidney function in medication dosing")

        if any(k in disease.lower() for k in ["heart", "cardiac", "hypertension"]):
            forbidden.append("Prescribe NSAIDs without assessing cardiovascular risk")
            forbidden.append("Discharge without assessing exercise tolerance")

        if any(k in disease.lower() for k in ["copd", "asthma"]):
            forbidden.append("Prescribe beta-blockers without considering pulmonary contraindication")
            forbidden.append("Discharge without checking oxygen saturation")

        # Dynamic from differentials
        if differentials:
            forbidden.append(f"Fail to consider {differentials[0]} as alternative diagnosis")

        # Dynamic from medications
        if meds and isinstance(meds[0], dict):
            drug_name = meds[0]["name"]
            drug_info = self.kb.get_drug_info(drug_name)
            if drug_info and drug_info.contraindications:
                for ci in drug_info.contraindications[:1]:
                    forbidden.append(f"Prescribe {drug_name} in patient with {ci} without special precautions")

        # Lab-based
        forbidden.append(f"Diagnose {disease} without ordering any supporting lab tests")

        # Difficulty-specific
        if scenario.difficulty == "L3":
            forbidden.append("Fail to assess comorbidity impact on treatment plan")
            forbidden.append("Prescribe multiple new medications simultaneously without interaction check")

        return list(dict.fromkeys(forbidden))  # Deduplicate preserving order

    def _build_uncertainty_events(
        self,
        disease: str,
        scenario: ScenarioSpec,
        lab_panel: List[Dict],
        template: Dict,
    ) -> List[Dict]:
        """Build uncertainty events — lab inconsistencies, patient changes."""
        events = []

        # Event 1: Lab result inconsistency
        lab_conflict = template.get("typical_lab_conflict")
        if lab_conflict:
            events.append({
                "trigger": "after_lab_results",
                "event": "Lab results show inconsistent or borderline findings",
                "example": lab_conflict,
                "expected_handling": "Order repeat/confirmatory test, consider pre-analytical error, correlate with clinical symptoms before concluding",
            })
        elif lab_panel:
            # Generic lab uncertainty
            abnormal_labs = [l for l in lab_panel if l.get("is_abnormal")]
            if abnormal_labs:
                test_name = abnormal_labs[0]["test_name"]
                events.append({
                    "trigger": "after_lab_results",
                    "event": f"{test_name} result is borderline and doesn't fully match clinical picture",
                    "example": f"Single abnormal {test_name} with otherwise normal panel",
                    "expected_handling": "Consider repeat testing, evaluate trending, correlate with symptoms before making definitive diagnosis",
                })

        # Event 2: Patient reveals new symptom during treatment discussion
        gt = scenario.ground_truth
        if gt and gt.comorbidities:
            comorb_name = gt.comorbidities[0].name
            comorb_symptoms = self._get_comorbidity_symptoms(comorb_name)
            if comorb_symptoms:
                patient_symptom = self.lang.to_patient(comorb_symptoms[0])
                events.append({
                    "trigger": "during_treatment_discussion",
                    "event": f"Patient casually mentions '{patient_symptom}' when discussing treatment options",
                    "example": f"'Oh, I also sometimes get {patient_symptom} — is that related?'",
                    "expected_handling": f"Recognize this may indicate undiagnosed {self.lang.to_patient(comorb_name)}, update differential, order appropriate workup",
                })

        # Event 3: Condition change during consultation (L3 only)
        if scenario.difficulty == "L3":
            tpl = self._get_disease_template(disease)
            events.append({
                "trigger": "mid_consultation",
                "event": "Patient reports acute worsening of symptoms during the visit",
                "example": "Patient becomes visibly more uncomfortable or reports new severe symptom",
                "expected_handling": "Reassess urgency, consider acute complication, adjust pace and priorities of the consultation",
            })

        return events[:3]

    def _build_reward_basis(self, scenario: ScenarioSpec) -> List[str]:
        basis = ["DB", "COMMUNICATE"]

        if scenario.task_type in ("diagnostic_uncertainty", "conflicting_evidence"):
            basis.append("CLINICAL")
        elif scenario.task_type in ("treatment_tradeoff", "drug_safety_risk"):
            basis.extend(["CLINICAL", "SAFETY"])
        elif scenario.task_type == "emergency_triage":
            basis.extend(["CLINICAL", "SAFETY", "TIME"])

        return basis

    # ============================================================
    # Persona Generation (RICH version)
    # ============================================================

    def _generate_patient_persona(self, scenario: ScenarioSpec, profile) -> Dict:
        """Generate a realistic, detailed patient persona."""
        disease = scenario.target_disease or "unknown"
        behavior = scenario.behavior_type

        # Age range from disease profile
        age_range = (25, 75)
        if hasattr(profile, 'typical_age_range'):
            age_range = profile.typical_age_range
        age = self._rng.randint(age_range[0], age_range[1])

        gender = self._rng.choice(["male", "female"])

        # Name generation
        first_names = {
            "male": ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Zhao", "Huang", "Zhou", "Wu"],
            "female": ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Zhao", "Huang", "Zhou", "Wu"],
        }
        name = f"{self._rng.choice(first_names[gender])}XX"

        # Education level from behavior
        edu_level = BEHAVIOR_PROFILES.get(behavior, BEHAVIOR_PROFILES["cooperative"]).get("education_level", "high_school")

        # Occupation from education
        occupations = OCCUPATIONS.get(edu_level, OCCUPATIONS["high_school"])
        occupation = self._rng.choice(occupations)

        # Economic status
        economic_choices = ["low", "moderate", "moderate", "comfortable"]
        economic_status = self._rng.choice(economic_choices)

        income_texts = {
            "low": "about 3000-5000 yuan/month",
            "moderate": "about 5000-8000 yuan/month",
            "comfortable": "about 10000+ yuan/month",
        }

        insurances = {
            "low": "basic rural/cooperative medical insurance, limited coverage",
            "moderate": "employee medical insurance, ~60-70% coverage",
            "comfortable": "comprehensive medical insurance, good coverage",
        }

        return {
            "age": age,
            "gender": gender,
            "name": name,
            "language": "zh",
            "education_level": edu_level,
            "occupation": occupation,
            "economic_status": economic_status,
            "income_text": income_texts[economic_status],
            "insurance": insurances[economic_status],
        }

    # ============================================================
    # Helpers
    # ============================================================

    def _infer_domain(self, disease: str) -> str:
        disease_lower = disease.lower()
        domain_map = {
            "diabetes": "endocrinology",
            "hyperthyroid": "endocrinology",
            "hypothyroid": "endocrinology",
            "hyperlipidemia": "endocrinology",
            "hypertension": "cardiology",
            "heart": "cardiology",
            "cardiac": "cardiology",
            "atrial": "cardiology",
            "coronary": "cardiology",
            "copd": "pulmonology",
            "asthma": "pulmonology",
            "pneumonia": "pulmonology",
            "stroke": "neurology",
            "epilepsy": "neurology",
            "migraine": "neurology",
            "parkinson": "neurology",
            "cirrhosis": "gastroenterology",
            "gerd": "gastroenterology",
            "pancreat": "gastroenterology",
            "kidney": "nephrology",
            "renal": "nephrology",
            "arthritis": "rheumatology",
            "rheumatoid": "rheumatology",
            "lupus": "rheumatology",
            "gout": "rheumatology",
            "osteoarthritis": "rheumatology",
            "depression": "psychiatry",
            "anxiety": "psychiatry",
            "anemia": "hematology",
            "sickle cell": "hematology",
            "leukemia": "hematology",
            "cancer": "oncology",
            "tumor": "oncology",
        }
        for key, domain in domain_map.items():
            if key in disease_lower:
                return domain
        return "internal_medicine"

    def _infer_template_category(self, disease: str) -> str:
        """Map disease to template category for auto-adaptation."""
        disease_lower = disease.lower()
        for cat, tpl in DISEASE_TEMPLATES.items():
            for kw in tpl["diseases"]:
                if kw in disease_lower:
                    return cat
        return "default"

    def _get_disease_template(self, disease: str) -> Dict:
        """Get the disease template for auto-adaptation."""
        cat = self._infer_template_category(disease)
        if cat in DISEASE_TEMPLATES:
            return DISEASE_TEMPLATES[cat]
        return {
            "key_assessment_areas": ["symptom timeline", "functional impact", "red flags"],
            "safety_focus": ["allergy check", "drug interaction"],
            "typical_lab_conflict": None,
            "common_complication_interactions": None,
        }

    def _get_medical_category(self, task_type: str) -> str:
        mapping = {
            "diagnostic_uncertainty": "diagnosis",
            "conflicting_evidence": "diagnosis",
            "treatment_tradeoff": "treatment",
            "patient_non_compliance": "communication",
            "drug_safety_risk": "safety",
            "emergency_triage": "emergency",
        }
        return mapping.get(task_type, "diagnosis")

    # ============================================================
    # Ground Truth Manifold
    # ============================================================

    def _build_ground_truth(
        self, scenario: ScenarioSpec, symptoms: SymptomSet, profile
    ) -> Dict:
        """Build verifiable standard answer space with decision tree."""
        disease = scenario.target_disease or "unknown"
        gt = scenario.ground_truth
        meds = self.kb.get_medications_for_condition(disease)
        lab_panel = self.kb.get_lab_panel(disease)
        differentials = self.kb.get_differential_diagnoses(disease)

        # Correct diagnosis
        correct_diagnosis = {
            "primary": disease,
            "confidence_threshold": 0.8 if scenario.difficulty != "L1" else 0.7,
            "acceptable_alternatives": differentials[:3] if differentials else [],
            "required_evidence": [],
        }

        # Evidence needed for diagnosis
        evidence_items = ["symptom_cluster_matching"]
        if lab_panel:
            evidence_items.append("lab_result_confirmation")
            abnormal_labs = [l["test_name"] for l in lab_panel if l.get("is_abnormal")]
            if abnormal_labs:
                evidence_items.append(f"abnormal_{abnormal_labs[0]}")
        correct_diagnosis["required_evidence"] = evidence_items

        # Expected lab results
        expected_labs = {}
        if lab_panel:
            for lab in lab_panel:
                expected_labs[lab["test_name"]] = {
                    "expected_value": self._generate_realistic_lab_value(lab),
                    "reference_range": f"{lab['range_low']}-{lab['range_high']} {lab.get('unit', '')}",
                    "is_abnormal": lab.get("is_abnormal", False),
                    "clinical_significance": lab.get("clinical_significance", ""),
                }

        # Correct treatment plan
        correct_treatment = {"medications": [], "non_pharmacological": [], "follow_up": "2-4 weeks"}
        if meds:
            for m in meds[:3]:
                if isinstance(m, dict) and m.get("is_first_line", True):
                    drug_info = self.kb.get_drug_info(m["name"])
                    if drug_info:
                        correct_treatment["medications"].append({
                            "name": drug_info.generic_name,
                            "drug_class": drug_info.drug_class,
                            "dose": drug_info.standard_doses[0]["dose"] if drug_info.standard_doses else m.get("dose", ""),
                            "frequency": drug_info.standard_doses[0]["frequency"] if drug_info.standard_doses else m.get("frequency", ""),
                            "rationale": f"First-line treatment for {disease}",
                        })
                        break  # Only first-line
        correct_treatment["non_pharmacological"] = [
            "Lifestyle modification counseling",
            "Dietary guidance",
        ]

        # Safety checks that must be performed
        required_safety_checks = [
            {"check": "allergy_check", "before": "prescribing", "critical": True},
            {"check": "drug_interaction_check", "before": "prescribing", "critical": scenario.difficulty != "L1"},
        ]
        if gt and gt.comorbidities:
            required_safety_checks.append({
                "check": "contraindication_check",
                "before": "prescribing",
                "conditions": [c.name for c in gt.comorbidities],
                "critical": True,
            })

        # Communication milestones
        communication_truth = [
            {"milestone": "explain_diagnosis", "must_include": [f"diagnosis name in patient terms", "what it means"]},
            {"milestone": "explain_treatment", "must_include": ["medication name and purpose", "how to take it", "expected effects"]},
            {"milestone": "address_concerns", "must_include": ["acknowledge patient worries", "correct misconceptions"]},
        ]

        # Decision tree — correct path through consultation
        decision_tree = [
            {
                "step": 1,
                "action": "history_taking",
                "correct_approach": "Systematically ask about symptoms, onset, duration, severity, aggravating/relieving factors",
                "key_questions": [
                    self.lang.to_patient(s) for s in symptoms.volunteer[:3]
                ],
                "hidden_information_to_uncover": [
                    self.lang.to_patient(s) for s in (symptoms.hidden + symptoms.resistant)[:3]
                ],
            },
            {
                "step": 2,
                "action": "order_labs",
                "correct_approach": f"Order disease-relevant labs for {disease}",
                "required_tests": [lab["test_name"] for lab in lab_panel[:5]] if lab_panel else ["CBC", "BMP"],
            },
            {
                "step": 3,
                "action": "form_diagnosis",
                "correct_approach": "Consider differential diagnoses, correlate symptoms with lab results",
                "must_consider": differentials[:3] if differentials else [],
            },
            {
                "step": 4,
                "action": "plan_treatment",
                "correct_approach": "Check safety before prescribing, select appropriate first-line medication",
                "safety_first": True,
            },
            {
                "step": 5,
                "action": "communicate_and_close",
                "correct_approach": "Explain in patient-friendly language, address concerns, schedule follow-up",
            },
        ]

        return {
            "correct_diagnosis": correct_diagnosis,
            "expected_lab_results": expected_labs,
            "correct_treatment_plan": correct_treatment,
            "required_safety_checks": required_safety_checks,
            "communication_truth": communication_truth,
            "decision_tree": decision_tree,
        }

    # ============================================================
    # Environment Dynamics (State Transition System)
    # ============================================================

    def _build_environment_dynamics(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Build state machine for agent-environment interaction."""
        gt = scenario.ground_truth

        # Filter transitions relevant to this task type
        task_type = scenario.task_type
        if task_type == "emergency_triage":
            # Emergency skips ahead faster
            active_states = ["INITIAL", "HISTORY_TAKING", "LAB_ORDERED", "LAB_RESULTS_AVAILABLE",
                           "DIAGNOSIS_MADE", "TREATMENT_PLANNING", "PRESCRIPTION_WRITTEN", "CONSULTATION_COMPLETE"]
        else:
            active_states = list(ENVIRONMENT_STATES.keys())

        states = {k: v for k, v in ENVIRONMENT_STATES.items() if k in active_states}

        # Add disease-specific observations per state
        lab_panel = self.kb.get_lab_panel(disease)
        for state_name, state_data in states.items():
            if state_name == "LAB_RESULTS_AVAILABLE" and lab_panel:
                state_data["disease_specific_observations"] = [
                    f"{lab['test_name']}: results pending" for lab in lab_panel[:5]
                ]
            if state_name == "HISTORY_TAKING":
                state_data["partial_observability"] = {
                    "patient_visible_symptoms": "volunteer tier only",
                    "requires_probing": "if_asked and hidden tiers need specific questions",
                    "trust_gated": "resistant symptoms need empathy/probing",
                }

        # Build reward function per state
        rewards = {
            "HISTORY_TAKING": {
                "per_relevant_question": 0.05,
                "discover_hidden_symptom": 0.15,
                "discover_resistant_symptom": 0.20,
                "missed_symptom_penalty": -0.10,
            },
            "EXAMINATION_AND_LABS": {
                "order_appropriate_test": 0.10,
                "order_unnecessary_test": -0.05,
                "miss_critical_test": -0.20,
            },
            "DIAGNOSIS_MADE": {
                "correct_diagnosis": 0.30,
                "acceptable_alternative": 0.20,
                "incorrect_diagnosis": -0.30,
            },
            "TREATMENT_PLANNING": {
                "safety_check_performed": 0.10,
                "safety_check_skipped": -0.30,
                "appropriate_medication": 0.20,
                "contraindicated_medication": -0.40,
            },
            "PATIENT_DISCUSSION": {
                "used_patient_friendly_language": 0.05,
                "corrected_misconception": 0.10,
                "ignored_concern": -0.10,
            },
            "CONSULTATION_COMPLETE": {
                "all_phases_complete": 0.10,
                "efficiency_bonus": 0.05,
                "incomplete_consultation": -0.20,
            },
        }

        # Penalty for forbidden state transitions
        invalid_transitions = [
            {"from": "INITIAL", "to": "PRESCRIPTION_WRITTEN", "reason": "Cannot prescribe without diagnosis"},
            {"from": "HISTORY_TAKING", "to": "PRESCRIPTION_WRITTEN", "reason": "Cannot prescribe without diagnosis and labs"},
            {"from": "INITIAL", "to": "DIAGNOSIS_MADE", "reason": "Cannot diagnose without gathering history"},
            {"from": "LAB_ORDERED", "to": "PRESCRIPTION_WRITTEN", "reason": "Cannot prescribe before reviewing lab results"},
        ]

        return {
            "states": states,
            "transitions": [t for t in STATE_TRANSITIONS if t["from"] in active_states],
            "invalid_transitions": invalid_transitions,
            "reward_function": rewards,
            "initial_state": "INITIAL",
            "terminal_states": ["CONSULTATION_COMPLETE"],
            "partial_observability": {
                "description": "Agent cannot directly observe hidden symptoms, patient thoughts, or lab results without ordering",
                "observable": ["patient_verbal_responses", "vital_signs", "ordered_lab_results"],
                "unobservable": ["hidden_symptoms", "resistant_symptoms", "undiagnosed_comorbidities", "patient_inner_thoughts"],
                "information_cost": "Each question costs 1 turn; each lab order costs 1-2 turns",
            },
        }

    # ============================================================
    # Result-Driven Outcome Criteria
    # ============================================================

    def _build_outcome_criteria(self, scenario: ScenarioSpec, profile, disease: str) -> Dict:
        """Build outcome-driven evaluation metrics focused on decision correctness."""
        meds = self.kb.get_medications_for_condition(disease)
        differentials = self.kb.get_differential_diagnoses(disease)

        # Primary outcome — the main result that matters
        primary = {
            "metric": "diagnostic_accuracy",
            "description": "Agent arrives at the correct diagnosis",
            "verifiable": True,
            "scoring": {
                "exact_match": 1.0,
                "acceptable_alternative": 0.7,
                "partially_correct": 0.4,
                "incorrect": 0.0,
            },
            "correct_answer": disease,
            "acceptable_answers": differentials[:3] if differentials else [],
        }

        # Secondary outcomes
        secondary = [
            {
                "metric": "treatment_appropriateness",
                "description": "Treatment plan is safe and effective for the diagnosed condition",
                "verifiable": True,
                "scoring": {
                    "optimal_first_line": 1.0,
                    "acceptable_alternative": 0.7,
                    "suboptimal_but_safe": 0.4,
                    "unsafe_or_contraindicated": 0.0,
                },
                "correct_answer": meds[0]["name"] if meds and isinstance(meds[0], dict) else "appropriate first-line medication",
            },
            {
                "metric": "safety_adherence",
                "description": "All required safety checks performed before prescribing",
                "verifiable": True,
                "scoring": {
                    "all_checks_performed": 1.0,
                    "minor_omission": 0.5,
                    "critical_omission": 0.0,
                },
                "required_checks": ["allergy_check", "drug_interaction_check"],
                "critical_checks": ["allergy_check"],
            },
            {
                "metric": "information_completeness",
                "description": "Agent gathered all critical patient information",
                "verifiable": True,
                "scoring": {
                    "complete": 1.0,
                    "minor_gap": 0.7,
                    "significant_gap": 0.3,
                    "inadequate": 0.0,
                },
                "required_categories": ["chief_complaint", "symptoms", "past_history", "medications", "allergies"],
            },
            {
                "metric": "patient_satisfaction",
                "description": "Patient understands their condition and agrees to treatment plan",
                "verifiable": True,
                "scoring": {
                    "patient_understands_and_agrees": 1.0,
                    "patient_understands_but_hesitant": 0.6,
                    "patient_confused": 0.3,
                    "patient_refuses": 0.1,
                },
            },
        ]

        # Aggregate scoring rubric
        rubric = {
            "weights": {
                "diagnostic_accuracy": 0.30,
                "treatment_appropriateness": 0.25,
                "safety_adherence": 0.20,
                "information_completeness": 0.15,
                "patient_satisfaction": 0.10,
            },
            "pass_threshold": 0.7 if scenario.difficulty == "L1" else 0.8,
            "grade_levels": {
                "excellent": (0.9, 1.0),
                "good": (0.8, 0.9),
                "acceptable": (0.7, 0.8),
                "needs_improvement": (0.5, 0.7),
                "failing": (0.0, 0.5),
            },
            "critical_failure_conditions": [
                "Missed critical diagnosis",
                "Prescribed contraindicated medication",
                "Failed to check allergies before prescribing",
                "Ignored abnormal lab results without follow-up",
            ],
        }

        return {
            "primary_outcome": primary,
            "secondary_outcomes": secondary,
            "scoring_rubric": rubric,
        }

    # ============================================================
    # Episode Structure (Time / Phase)
    # ============================================================

    def _build_episode_structure(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Build time-structured episode with phases and turn budgets."""
        max_turns = scenario.constraints.max_turns
        min_turns = max(3, scenario.constraints.min_required_questions)

        # Adjust phase turn budgets based on max_turns
        phases = []
        for phase in EPISODE_PHASES:
            rec_low, rec_high = phase["recommended_turns"]
            # Scale to available turns
            scaled_low = max(1, int(rec_low * max_turns / 20))
            scaled_high = max(scaled_low + 1, int(rec_high * max_turns / 20))
            phases.append({
                "name": phase["name"],
                "description": phase["description"],
                "turn_budget": {"min": scaled_low, "max": scaled_high},
                "required_actions": phase["required_actions"],
                "exit_condition": phase["exit_condition"],
            })

        # Time pressure events
        time_events = []
        if scenario.difficulty in ("L2", "L3"):
            time_events.append({
                "trigger_turn": int(max_turns * 0.6),
                "event": "Patient shows signs of impatience",
                "effect": "Agent must balance thoroughness with efficiency",
            })
        if scenario.difficulty == "L3":
            time_events.append({
                "trigger_turn": int(max_turns * 0.8),
                "event": "Patient condition acutely worsens",
                "effect": "Agent must immediately prioritize stabilization",
            })

        # Efficiency metrics
        efficiency = {
            "optimal_turn_range": (min_turns + 2, min_turns + 8),
            "max_turns": max_turns,
            "turn_efficiency_score": "max(0, 1 - (actual_turns - optimal) / max_turns)",
            "waste_penalty": -0.02,  # Per unnecessary turn beyond optimal
            "rush_penalty": -0.05,   # Per critical step skipped for speed
        }

        return {
            "phases": phases,
            "time_pressure_events": time_events,
            "efficiency_metrics": efficiency,
            "total_turn_budget": max_turns,
            "minimum_required_turns": min_turns,
        }

    # ============================================================
    # Capability Dimensions (Benchmark Tags)
    # ============================================================

    def _build_capability_dimensions(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Build agent capability dimension tags with task-specific weights."""
        task_type = scenario.task_type
        diff = scenario.difficulty

        # Task type → dimension weight profiles
        weight_profiles = {
            "diagnostic_uncertainty": {
                "information_gathering": 0.25,
                "diagnostic_reasoning": 0.30,
                "treatment_planning": 0.15,
                "safety_awareness": 0.10,
                "communication_quality": 0.10,
                "efficiency": 0.10,
            },
            "conflicting_evidence": {
                "information_gathering": 0.20,
                "diagnostic_reasoning": 0.35,
                "treatment_planning": 0.10,
                "safety_awareness": 0.10,
                "communication_quality": 0.10,
                "efficiency": 0.15,
            },
            "treatment_tradeoff": {
                "information_gathering": 0.10,
                "diagnostic_reasoning": 0.10,
                "treatment_planning": 0.35,
                "safety_awareness": 0.20,
                "communication_quality": 0.15,
                "efficiency": 0.10,
            },
            "patient_non_compliance": {
                "information_gathering": 0.10,
                "diagnostic_reasoning": 0.10,
                "treatment_planning": 0.15,
                "safety_awareness": 0.10,
                "communication_quality": 0.40,
                "efficiency": 0.15,
            },
            "drug_safety_risk": {
                "information_gathering": 0.10,
                "diagnostic_reasoning": 0.10,
                "treatment_planning": 0.20,
                "safety_awareness": 0.40,
                "communication_quality": 0.10,
                "efficiency": 0.10,
            },
            "emergency_triage": {
                "information_gathering": 0.15,
                "diagnostic_reasoning": 0.25,
                "treatment_planning": 0.15,
                "safety_awareness": 0.15,
                "communication_quality": 0.10,
                "efficiency": 0.20,
            },
        }

        weights = weight_profiles.get(task_type, weight_profiles["diagnostic_uncertainty"])

        dimensions = {}
        for dim_key, dim_info in CAPABILITY_DIMENSIONS.items():
            dimensions[dim_key] = {
                "description": dim_info["description"],
                "sub_skills": dim_info["sub_skills"],
                "weight": weights.get(dim_key, 0.1),
                "test_method": self._get_dimension_test_method(dim_key, disease),
            }

        # Difficulty modifiers on sub-skills
        difficulty_modifiers = {
            "L1": {"focus": "basic competence", "sub_skill_multiplier": 0.8},
            "L2": {"focus": "intermediate proficiency with nuance", "sub_skill_multiplier": 1.0},
            "L3": {"focus": "advanced mastery under adversarial conditions", "sub_skill_multiplier": 1.3},
        }

        return {
            "dimensions": dimensions,
            "primary_dimensions": sorted(weights, key=weights.get, reverse=True)[:3],
            "difficulty_modifier": difficulty_modifiers.get(diff, difficulty_modifiers["L2"]),
        }

    def _get_dimension_test_method(self, dimension: str, disease: str) -> str:
        """Get how a capability dimension is tested."""
        methods = {
            "information_gathering": f"Measure percentage of critical symptoms discovered for {disease}",
            "diagnostic_reasoning": "Check if correct diagnosis is reached and differentials considered",
            "treatment_planning": "Verify treatment matches guidelines and accounts for comorbidities",
            "safety_awareness": "Check all safety checks performed before treatment decisions",
            "communication_quality": "Evaluate patient understanding and misconception correction",
            "efficiency": "Count turns and actions relative to optimal path",
        }
        return methods.get(dimension, "Evaluate against ground truth decision tree")

    # ============================================================
    # Structural Difficulty Profile
    # ============================================================

    def _build_difficulty_profile(
        self, scenario: ScenarioSpec, disease: str, symptoms: SymptomSet
    ) -> Dict:
        """Build structural difficulty breakdown explaining WHY this task is hard."""
        diff = scenario.difficulty
        gt = scenario.ground_truth
        behavior = scenario.behavior_type

        n_comorbidities = len(gt.comorbidities) if gt and gt.comorbidities else 0
        n_hidden = len(symptoms.hidden) + len(symptoms.resistant)
        n_misleading = len(symptoms.misleading) + len(symptoms.noise)

        profile = {}
        for factor_key, factor_info in DIFFICULTY_FACTORS.items():
            level_desc = factor_info.get(diff, factor_info.get("L2", ""))
            score = {"L1": 1, "L2": 2, "L3": 3}.get(diff, 2)

            # Adjust score based on actual task content
            if factor_key == "symptom_complexity":
                total_symptoms = len(symptoms.volunteer) + len(symptoms.if_asked) + n_hidden
                score = min(3, max(1, total_symptoms // 3))
                level_desc = f"{total_symptoms} total symptoms across tiers"
            elif factor_key == "diagnostic_ambiguity":
                differentials = self.kb.get_differential_diagnoses(disease)
                n_diffs = len(differentials) if differentials else 1
                score = min(3, max(1, n_diffs // 2))
                level_desc = f"{n_diffs} plausible differentials"
            elif factor_key == "treatment_complexity":
                score = min(3, n_comorbidities + 1)
                level_desc = f"{n_comorbidities} comorbidities affecting treatment choice"
            elif factor_key == "patient_behavior_difficulty":
                behavior_scores = {
                    "cooperative": 1, "forgetful": 2, "confused": 2,
                    "pressuring": 2, "concealing": 3, "refusing": 3,
                }
                score = behavior_scores.get(behavior, 2)
                level_desc = f"behavior: {behavior}"
            elif factor_key == "information_asymmetry":
                score = min(3, max(1, n_hidden))
                level_desc = f"{n_hidden} hidden/resistant symptoms to discover"
            elif factor_key == "comorbidity_burden":
                score = min(3, n_comorbidities)
                level_desc = f"{n_comorbidities} comorbidities present"
            elif factor_key == "time_pressure":
                if scenario.task_type == "emergency_triage":
                    score = 3
                    level_desc = "Emergency — time-sensitive decisions required"
                elif diff == "L3":
                    score = 2
                    level_desc = "Moderate urgency with condition change event"
                else:
                    score = 1
                    level_desc = "Routine consultation, no urgency"

            profile[factor_key] = {
                "score": score,
                "max": 3,
                "description": factor_info["description"],
                "task_specific": level_desc,
            }

        # Overall difficulty score and explanation
        total_score = sum(p["score"] for p in profile.values())
        max_possible = len(profile) * 3
        overall = {
            "aggregate_score": total_score,
            "max_possible": max_possible,
            "difficulty_rating": diff,
            "primary_difficulty_drivers": sorted(
                profile.keys(), key=lambda k: profile[k]["score"], reverse=True
            )[:3],
            "explanation": self._generate_difficulty_explanation(profile, diff, disease),
        }

        # Adversarial design
        adversarial = {
            "noise_injection": {
                "misleading_symptoms": n_misleading,
                "noise_symptoms": len(symptoms.noise),
                "cross_overlapping_conditions": self._get_overlap_count(disease),
            },
            "partial_observability": {
                "hidden_symptoms": n_hidden,
                "trust_gated_symptoms": len(symptoms.resistant),
                "undiagnosed_comorbidities": n_comorbidities if diff == "L3" else max(0, n_comorbidities - 1),
            },
            "adversarial_patient_behavior": behavior in ("concealing", "refusing", "confused"),
            "conflicting_evidence": diff in ("L2", "L3") and scenario.task_type == "conflicting_evidence",
        }

        return {
            "factors": profile,
            "overall": overall,
            "adversarial_design": adversarial,
        }

    def _get_overlap_count(self, disease: str) -> int:
        """Count diseases with overlapping symptoms."""
        disease_lower = disease.lower()
        for key in DISEASE_MISLEADING_MAP:
            if key in disease_lower:
                misl = DISEASE_MISLEADING_MAP[key]
                return len(misl.get("cross_overlapping", []))
        return 0

    def _generate_difficulty_explanation(self, profile: Dict, diff: str, disease: str) -> str:
        """Generate human-readable difficulty explanation."""
        drivers = sorted(profile.keys(), key=lambda k: profile[k]["score"], reverse=True)[:3]
        driver_names = [k.replace("_", " ") for k in drivers]
        return (
            f"This {diff} task is primarily challenging due to {', '.join(driver_names[:2])}. "
            f"The diagnosis of {disease} requires careful information gathering and clinical reasoning."
        )

    # ============================================================
    # Execution Layer: Action Space
    # ============================================================

    def _build_action_space(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Build formal action space with JSON schema for each action."""
        focus = TASK_TYPE_TOOL_FOCUS.get(scenario.task_type, {})
        required_tool_types = focus.get("required_tool_types", [])

        # Determine which actions are available for this task type
        available_actions = ["greet_patient", "ask_patient"]
        for tool in required_tool_types:
            if tool in ACTION_SCHEMA:
                available_actions.append(tool)
        # Always include these
        for always in ["assess_vital_signs", "schedule_followup"]:
            if always not in available_actions:
                available_actions.append(always)

        # Build task-specific action schemas
        actions = {}
        lab_panel = self.kb.get_lab_panel(disease)
        for action_name in available_actions:
            schema = dict(ACTION_SCHEMA.get(action_name, {}))
            # Inject disease-specific parameter hints
            if action_name == "order_lab_tests" and lab_panel:
                schema["parameter_hints"] = {
                    "recommended_tests": [l["test_name"] for l in lab_panel[:5]],
                }
            elif action_name == "record_diagnosis":
                schema["parameter_hints"] = {
                    "correct_diagnosis": disease,
                }
            elif action_name == "differential_diagnosis":
                differentials = self.kb.get_differential_diagnoses(disease)
                schema["parameter_hints"] = {
                    "must_consider": differentials[:3] if differentials else [],
                }
            actions[action_name] = schema

        return {
            "version": "1.0",
            "schema_type": "json_schema",
            "total_actions": len(actions),
            "actions": actions,
            "action_validation": {
                "unknown_action": "REJECT — action not in action_space",
                "invalid_precondition": "REJECT — return error message, state unchanged",
                "missing_required_param": "REJECT — return validation error",
                "valid_action": "EXECUTE — apply state transition, return observation",
            },
        }

    # ============================================================
    # Execution Layer: Observation Function
    # ============================================================

    def _build_observation_function(
        self, scenario: ScenarioSpec, symptoms: SymptomSet, disease: str
    ) -> Dict:
        """Build formal observation function with field-level access control."""
        behavior = scenario.behavior_type
        diff = scenario.difficulty

        # Build noise model
        noise_model = {
            "patient_response_noise": {
                "type": "categorical",
                "levels": {
                    "cooperative": {"vagueness": 0.02, "omission": 0.0, "delay": 0.0},
                    "forgetful": {"vagueness": 0.15, "omission": 0.10, "delay": 0.0},
                    "confused": {"vagueness": 0.10, "omission": 0.05, "delay": 0.05},
                    "concealing": {"vagueness": 0.05, "omission": 0.20, "delay": 0.15},
                    "pressuring": {"vagueness": 0.05, "omission": 0.0, "delay": 0.0},
                    "refusing": {"vagueness": 0.10, "omission": 0.15, "delay": 0.10},
                },
                "active_level": behavior,
            },
            "lab_result_noise": {
                "type": "gaussian",
                "sigma": 0.02,  # 2% variance on lab values
                "applies_to": "lab_results after get_lab_results",
            },
            "vital_sign_noise": {
                "type": "uniform",
                "range": [-1, 1],  # ±1 unit
                "applies_to": "vital_signs after assess_vital_signs",
            },
        }

        # Build information gates — what triggers access to hidden fields
        n_hidden = len(symptoms.hidden)
        n_resistant = len(symptoms.resistant)
        trust_threshold = {
            "cooperative": 0.0,
            "forgetful": 0.1,
            "confused": 0.2,
            "concealing": 0.5,
            "pressuring": 0.1,
            "refusing": 0.6,
        }

        information_gates = {
            "volunteer_tier": {
                "access": "immediate",
                "fields": [self.lang.to_patient(s) for s in symptoms.volunteer[:5]],
                "cost": 0,
            },
            "if_asked_tier": {
                "access": "on_category_match",
                "fields": [self.lang.to_patient(s) for s in symptoms.if_asked[:5]],
                "cost": 1,  # 1 turn per question
                "trigger": "ask_patient with category matching the symptom",
            },
            "hidden_tier": {
                "access": "on_specific_probe",
                "fields": [self.lang.to_patient(s) for s in symptoms.hidden[:5]],
                "cost": 1,
                "trigger": "ask_patient with question containing specific symptom keyword",
            },
            "resistant_tier": {
                "access": "after_trust_threshold",
                "fields": [self.lang.to_patient(s) for s in symptoms.resistant[:5]],
                "cost": 2,  # Requires empathy + question
                "trust_required": trust_threshold.get(behavior, 0.3),
                "trigger": "demonstrate empathy + ask specific question",
            },
        }

        # Difficulty-scaled noise multiplier
        difficulty_noise_multiplier = {"L1": 0.5, "L2": 1.0, "L3": 1.5}.get(diff, 1.0)

        return {
            "fields": OBSERVATION_FIELDS,
            "noise_model": noise_model,
            "information_gates": information_gates,
            "difficulty_noise_multiplier": difficulty_noise_multiplier,
            "observation_protocol": {
                "step_input": {
                    "agent_action": "ActionSchema compliant JSON",
                    "current_state": "ENVIRONMENT_STATES key",
                    "turn_count": "integer",
                    "trust_level": "float 0-1",
                },
                "step_output": {
                    "observation": "dict of visible fields at current state",
                    "reward": "float — incremental reward for this step",
                    "terminated": "boolean — has consultation ended",
                    "info": "dict — debug/metadata (agent cannot see ground_truth)",
                },
            },
        }

    # ============================================================
    # Execution Layer: Scoring Function
    # ============================================================

    def _build_scoring_function(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Build executable scoring function with evaluable logic."""
        gt = scenario.ground_truth
        diff = scenario.difficulty
        n_comorbidities = len(gt.comorbidities) if gt and gt.comorbidities else 0

        return {
            "version": "1.0",
            "evaluable": True,
            "score_range": [0.0, 1.0],
            "components": {
                "diagnosis_score": {
                    "weight": 0.30,
                    "logic": "if agent_diagnosis == ground_truth.correct_diagnosis.primary: 1.0 elif agent_diagnosis in ground_truth.correct_diagnosis.acceptable_alternatives: 0.7 elif partial_match(agent_diagnosis, ground_truth): 0.4 else: 0.0",
                    "source": "ground_truth.correct_diagnosis",
                    "evaluable_expression": "exact_match(agent_output.diagnosis, ground_truth.correct_diagnosis.primary) ? 1.0 : (in_list(agent_output.diagnosis, ground_truth.correct_diagnosis.acceptable_alternatives) ? 0.7 : 0.0)",
                },
                "safety_score": {
                    "weight": 0.25,
                    "logic": "all_checks = sum(check_performed(c) for c in ground_truth.required_safety_checks); critical_missed = sum(1 for c in ground_truth.required_safety_checks if c.critical and not check_performed(c)); if critical_missed > 0: 0.0 else: all_checks / len(ground_truth.required_safety_checks)",
                    "source": "ground_truth.required_safety_checks",
                    "evaluable_expression": "critical_missed = count(c for c in required_safety_checks where c.critical and not performed); critical_missed == 0 ? performed_count / total_count : 0.0",
                },
                "information_score": {
                    "weight": 0.20,
                    "logic": "discovered = count(s for s in all_symptoms if agent_asked_about(s)); total = len(all_symptoms); min(discovered / total, 1.0)",
                    "source": "user_scenario.information_sharing_strategy",
                    "evaluable_expression": "min(discovered_symptoms / total_symptoms, 1.0)",
                },
                "treatment_score": {
                    "weight": 0.15,
                    "logic": "if agent_treatment in ground_truth.correct_treatment_plan.medications: 1.0 elif safe_alternative(agent_treatment, disease): 0.7 else: 0.0",
                    "source": "ground_truth.correct_treatment_plan",
                    "evaluable_expression": "in_treatment_plan(agent_output.medication) ? 1.0 : (is_safe_alternative(agent_output.medication) ? 0.7 : 0.0)",
                },
                "communication_score": {
                    "weight": 0.10,
                    "logic": "milestones_hit = count(m for m in ground_truth.communication_truth if milestone_achieved(m)); milestones_hit / len(ground_truth.communication_truth)",
                    "source": "ground_truth.communication_truth",
                    "evaluable_expression": "milestones_achieved / total_milestones",
                },
            },
            "aggregate_logic": "sum(component_score * component_weight for each component)",
            "pass_threshold": 0.7 if diff == "L1" else 0.8,
            "critical_failure_rules": [
                {
                    "condition": "diagnosis_score == 0.0",
                    "result": "FAIL — incorrect diagnosis regardless of other scores",
                    "override_threshold": None,
                },
                {
                    "condition": "safety_score == 0.0 and critical_check_missed",
                    "result": "FAIL — critical safety check missed",
                    "override_threshold": None,
                },
                {
                    "condition": "prescribed_contraindicated_drug == true",
                    "result": "FAIL — prescribed contraindicated medication",
                    "override_threshold": None,
                },
            ],
            "efficiency_bonus": {
                "logic": "if turns <= optimal_turns: +0.05; elif turns <= optimal_turns * 1.5: +0.0; else: -0.05 * (turns - optimal_turns * 1.5) / max_turns",
                "optimal_turns_formula": "len(required_phases) * 2 + len(required_labs) + 2",
            },
        }

    # ============================================================
    # Execution Layer: Agent API (Interaction Protocol)
    # ============================================================

    def _build_agent_api(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Build formal agent-task interaction protocol."""
        max_turns = scenario.constraints.max_turns
        min_turns = max(3, scenario.constraints.min_required_questions)

        return {
            "protocol_version": "1.0",
            "interface_type": "step_based",
            "step_signature": {
                "input": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Action name from action_space"},
                                "arguments": {"type": "object", "description": "Arguments per action schema"},
                            },
                            "required": ["name"],
                        },
                    },
                    "required": ["action"],
                },
                "output": {
                    "type": "object",
                    "properties": {
                        "observation": {
                            "type": "object",
                            "description": "Fields visible at current state per observation_function",
                        },
                        "reward": {
                            "type": "number",
                            "description": "Incremental reward for this step, from environment_dynamics.reward_function",
                        },
                        "terminated": {
                            "type": "boolean",
                            "description": "True if consultation is complete or max turns reached",
                        },
                        "truncated": {
                            "type": "boolean",
                            "description": "True if max_turns exceeded without completion",
                        },
                        "info": {
                            "type": "object",
                            "properties": {
                                "current_state": {"type": "string"},
                                "turn_count": {"type": "integer"},
                                "trust_level": {"type": "number"},
                                "action_valid": {"type": "boolean"},
                                "error": {"type": "string", "description": "Error message if action was rejected"},
                            },
                        },
                    },
                },
            },
            "turn_rules": {
                "max_turns": max_turns,
                "min_required_turns": min_turns,
                "agent_goes_first": True,
                "patient_responds_after_each_action": True,
                "multi_action_per_turn": False,
            },
            "termination_conditions": [
                {
                    "type": "normal",
                    "condition": "state == CONSULTATION_COMPLETE",
                    "description": "Agent completed all required phases",
                },
                {
                    "type": "truncation",
                    "condition": "turn_count >= max_turns",
                    "description": "Maximum turns exceeded",
                },
                {
                    "type": "failure",
                    "condition": "prescribed_contraindicated_drug or missed_critical_safety",
                    "description": "Agent made a critical safety error",
                },
            ],
            "reset": {
                "description": "Reset environment to initial state",
                "returns": {
                    "observation": "Initial observation (demographics, ticket)",
                    "info": {"state": "INITIAL", "turn_count": 0, "trust_level": 0.5},
                },
            },
        }

    # ============================================================
    # Execution Layer: Execution Config
    # ============================================================

    def _build_execution_config(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Build execution config tying all execution layer components together."""
        diff = scenario.difficulty
        behavior = scenario.behavior_type

        return {
            "version": "1.0",
            "environment_type": "medical_consultation",
            "components": {
                "action_space": "Defines all valid agent actions with schema",
                "observation_function": "Controls information flow with noise model and gates",
                "scoring_function": "Evaluates agent performance with per-component scoring",
                "agent_api": "Defines step-based interaction protocol",
                "environment_dynamics": "State machine with transitions and rewards",
                "ground_truth": "Reference answers for evaluation",
            },
            "execution_flow": [
                "1. Initialize: load task, set state=INITIAL, turn_count=0",
                "2. Agent calls step(action) with action from action_space",
                "3. Validate action against action_space schema and preconditions",
                "4. If valid: apply state transition from environment_dynamics",
                "5. Apply observation_function to determine what agent sees",
                "6. Apply noise_model to observations",
                "7. Calculate incremental reward from environment_dynamics.reward_function",
                "8. Return (observation, reward, terminated, info)",
                "9. If terminated: run scoring_function for final score",
                "10. Return final_score with component breakdown",
            ],
            "agent_requirements": {
                "input_format": "Must produce actions conforming to action_space schema",
                "output_parsing": "Must handle observations from observation_function",
                "memory": "Agent must maintain own history (no state reset between turns)",
                "tool_use": "Must call tools via action_space, not free-form text",
            },
            "evaluator_requirements": {
                "ground_truth_access": "Evaluator has access to ground_truth for scoring",
                "scoring_execution": "Run scoring_function logic against agent action log",
                "component_breakdown": "Report per-component scores, not just aggregate",
                "critical_failure_check": "Check critical_failure_rules before reporting pass/fail",
            },
            "randomness": {
                "seed": scenario.generation_seed,
                "stochastic_elements": [
                    "patient_response_variation",
                    "lab_result_noise",
                    "vital_sign_noise",
                    "symptom_reveal_timing",
                ],
                "deterministic_elements": [
                    "ground_truth",
                    "correct_diagnosis",
                    "expected_lab_results",
                    "action_space",
                ],
            },
        }

    # ============================================================
    # Verification Layer: External Source Attribution
    # ============================================================

    def _build_verification(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Build verification metadata with external source citations."""
        profile = self.kb.get_disease_profile(disease)
        meds = self.kb.get_medications_for_condition(disease)
        lab_panel = self.kb.get_lab_panel(disease)

        # Source citations
        sources = {
            "disease_profile": {
                "source": "disease_profiles.json",
                "fields_used": ["differential_questions", "aliases", "typical_age_range"],
                "clinical_validation": "Derived from established medical knowledge base",
            },
            "medication_data": {
                "source": "drug_database.json",
                "fields_used": ["generic_name", "drug_class", "standard_doses", "contraindications", "interactions"],
                "clinical_validation": "Based on standard pharmacological references",
            },
            "lab_reference": {
                "source": "lab_reference.json",
                "fields_used": ["test_name", "range_low", "range_high", "is_abnormal", "clinical_significance"],
                "clinical_validation": "Reference ranges from standard clinical laboratory values",
            },
            "clinical_questions": {
                "source": "clinical_questions.json",
                "fields_used": ["differential_questions", "symptom_probes"],
                "clinical_validation": "Questions derived from clinical diagnostic protocols",
            },
        }

        # Cross-validation rules — what must be internally consistent
        cross_validation = [
            {
                "rule": "diagnosis_matches_symptoms",
                "check": f"ground_truth.correct_diagnosis.primary ({disease}) must be consistent with medical_persona.symptoms and expected_lab_results",
                "status": "auto_verified",
            },
            {
                "rule": "treatment_matches_diagnosis",
                "check": "ground_truth.correct_treatment_plan medications must be indicated for the correct_diagnosis",
                "status": "auto_verified",
            },
            {
                "rule": "lab_values_in_range",
                "check": "All lab values in medical_persona.lab_results must fall within or near disease-specific reference ranges from lab_reference.json",
                "status": "auto_verified",
            },
            {
                "rule": "contraindications_consistent",
                "check": "ground_truth.correct_treatment_plan must not include medications contraindicated by medical_persona.comorbidities",
                "status": "auto_verified",
            },
        ]

        # Confidence levels for each ground truth component
        confidence = {
            "correct_diagnosis": {
                "level": "high",
                "reason": "Directly from disease_profiles.json — established condition",
            },
            "expected_lab_results": {
                "level": "high",
                "reason": "Values generated from lab_reference.json reference ranges with disease-specific adjustments",
            },
            "correct_treatment_plan": {
                "level": "high" if meds else "moderate",
                "reason": "First-line medication from drug_database.json" if meds else "No specific medication data available in KB",
            },
            "differential_diagnoses": {
                "level": "high",
                "reason": "From disease_profiles.json differential field",
            },
        }

        # External guideline references (task-specific)
        guideline_refs = {
            "type 2 diabetes": "ADA Standards of Medical Care in Diabetes",
            "hypertension": "ACC/AHA Hypertension Clinical Practice Guidelines",
            "copd": "GOLD Global Strategy for COPD",
            "heart failure": "ACC/AHA Heart Failure Guideline",
            "chronic kidney disease": "KDIGO Clinical Practice Guidelines",
            "asthma": "GINA Global Strategy for Asthma Management",
            "stroke": "AHA/ASA Acute Ischemic Stroke Guidelines",
            "atrial fibrillation": "ACC/AHA/AFib Guideline",
            "gout": "ACR Gout Management Guidelines",
            "depression": "APA Practice Guidelines for Depression",
            "anemia": "WHO/ASH Anemia Guidelines",
        }
        specific_guideline = None
        for key, ref in guideline_refs.items():
            if key in disease.lower():
                specific_guideline = ref
                break

        return {
            "version": "1.0",
            "sources": sources,
            "cross_validation_rules": cross_validation,
            "confidence_levels": confidence,
            "clinical_guideline_reference": specific_guideline or "General internal medicine guidelines",
            "verification_method": {
                "automated_checks": [
                    "diagnosis-treatment consistency",
                    "lab value range validation",
                    "contraindication cross-check",
                    "symptom-diagnosis alignment",
                ],
                "manual_review_recommended": True,
                "disclaimer": "Generated ground truth should be reviewed by a clinical domain expert before use in high-stakes evaluation",
            },
        }

    # ============================================================
    # Score Calibration Layer
    # ============================================================

    def _build_score_calibration(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Build score calibration for cross-task comparability."""
        diff = scenario.difficulty

        # Reference distributions per difficulty level
        reference_distributions = {
            "L1": {
                "mean": 0.75,
                "std": 0.12,
                "percentiles": {"p10": 0.55, "p25": 0.65, "p50": 0.75, "p75": 0.85, "p90": 0.92},
                "description": "Reference distribution from baseline agent performance on L1 tasks",
            },
            "L2": {
                "mean": 0.60,
                "std": 0.15,
                "percentiles": {"p10": 0.38, "p25": 0.50, "p50": 0.60, "p75": 0.72, "p90": 0.82},
                "description": "Reference distribution from baseline agent performance on L2 tasks",
            },
            "L3": {
                "mean": 0.45,
                "std": 0.18,
                "percentiles": {"p10": 0.22, "p25": 0.33, "p50": 0.45, "p75": 0.58, "p90": 0.70},
                "description": "Reference distribution from baseline agent performance on L3 tasks",
            },
        }

        ref = reference_distributions.get(diff, reference_distributions["L2"])

        return {
            "version": "1.0",
            "calibration_method": "z_score_normalization_with_difficulty_adjustment",
            "raw_score_range": [0.0, 1.0],
            "reference_distribution": ref,
            "normalization": {
                "formula": "normalized_score = (raw_score - reference_mean) / reference_std",
                "output_range": "z-scores, comparable across all difficulty levels",
                "interpretation": {
                    "z > 1.0": "Above 84th percentile — excellent",
                    "z > 0.0": "Above 50th percentile — above average",
                    "z > -1.0": "Above 16th percentile — below average",
                    "z <= -1.0": "Below 16th percentile — needs improvement",
                },
            },
            "difficulty_adjustment": {
                "description": "Same raw score at different difficulties maps to different normalized scores",
                "example": {
                    "raw_0.7_at_L1": f"z = (0.7 - {ref['mean']}) / {ref['std']:.2f} = {(0.7 - ref['mean']) / ref['std']:.2f}" if diff == "L1" else "see L1 reference",
                    "raw_0.7_at_L3": f"z = (0.7 - 0.45) / 0.18 = 1.39 — excellent at hardest level" if diff == "L3" else "see L3 reference",
                },
            },
            "leaderboard_scoring": {
                "primary_metric": "normalized_z_score",
                "secondary_metric": "raw_score",
                "grouping": "by difficulty level AND task type",
                "ranking_rule": "Higher z-score = better, adjusted for difficulty",
            },
        }

    # ============================================================
    # Benchmark Protocol
    # ============================================================

    def _build_benchmark_protocol(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Build standardized benchmark running protocol."""
        max_turns = scenario.constraints.max_turns

        return {
            "protocol_version": "1.0",
            "benchmark_name": "tau2-medical-bench",
            "run_configuration": {
                "agent_interface": "Agent must implement step(action) -> (observation, reward, terminated, info)",
                "initialization": {
                    "step_1": "Load task JSON",
                    "step_2": "Initialize environment with initial_state",
                    "step_3": "Set state=INITIAL, turn_count=0",
                    "step_4": "Return first observation (demographics + ticket)",
                },
                "execution_loop": {
                    "type": "for turn in range(max_turns)",
                    "body": [
                        "agent produces action via step(action_dict)",
                        "environment validates action against action_space",
                        "if valid: apply state transition from environment_dynamics",
                        "apply observation_function with noise_model",
                        "compute incremental reward from environment_dynamics.reward_function",
                        "return (observation, reward, terminated, info)",
                        "if terminated: break loop",
                    ],
                },
                "post_execution": {
                    "step_1": "Collect agent action log",
                    "step_2": "Run scoring_function for final score",
                    "step_3": "Apply score_calibration for normalized score",
                    "step_4": "Generate per-component score breakdown",
                },
            },
            "evaluation_pipeline": {
                "input": "agent_action_log + task JSON",
                "steps": [
                    "Verify all required_actions were performed",
                    "Check forbidden_actions not violated",
                    "Score diagnosis_accuracy against ground_truth",
                    "Score safety_adherence against required_safety_checks",
                    "Score treatment_appropriateness against correct_treatment_plan",
                    "Score information_completeness against information_gates",
                    "Score communication_quality against communication_truth",
                    "Apply critical_failure_rules",
                    "Calculate weighted aggregate",
                    "Apply efficiency_bonus/deduction",
                    "Normalize with score_calibration",
                ],
                "output": {
                    "raw_score": "float [0.0, 1.0]",
                    "normalized_z_score": "float (z-score)",
                    "component_scores": "dict[str, float]",
                    "pass_fail": "boolean",
                    "grade": "string (excellent/good/acceptable/needs_improvement/failing)",
                    "critical_failures": "list[str]",
                },
            },
            "leaderboard_format": {
                "schema": {
                    "agent_name": "string",
                    "model_id": "string",
                    "task_id": "string",
                    "task_type": "string",
                    "difficulty": "string",
                    "disease": "string",
                    "raw_score": "float",
                    "normalized_z_score": "float",
                    "grade": "string",
                    "component_scores": "dict",
                    "turns_used": "int",
                    "seed": "int",
                    "timestamp": "ISO 8601",
                },
                "aggregation": {
                    "per_agent": "mean(normalized_z_score) across all tasks",
                    "per_difficulty": "mean(normalized_z_score) per difficulty level",
                    "per_task_type": "mean(normalized_z_score) per task type",
                    "per_dimension": "mean(component_score) per capability_dimension",
                },
                "ranking": "Primary: mean normalized_z_score. Tiebreak: fewer turns, then fewer critical failures.",
            },
            "reproducibility_requirements": {
                "must_specify": ["agent_name", "model_id", "seed", "task_id"],
                "deterministic_run": "Same seed + task_id + action_sequence must produce identical scores",
                "version_lock": "Results only comparable within same benchmark protocol version",
            },
        }

    # ============================================================
    # Determinism Guarantee
    # ============================================================

    def _build_determinism_guarantee(self, scenario: ScenarioSpec, seed) -> Dict:
        """Build determinism and reproducibility guarantees."""
        import hashlib

        # Create a content hash of deterministic task elements
        disease = scenario.target_disease or "unknown"
        hash_input = f"{scenario.scenario_id}|{disease}|{scenario.difficulty}|{scenario.task_type}|{scenario.behavior_type}|{seed}"
        content_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        return {
            "version": "1.0",
            "guarantee": "Same task_id + seed produces bit-identical task JSON",
            "seed": seed,
            "rng_type": "random.Random (Mersenne Twister, deterministic)",
            "rng_scope": "Single self._rng instance per task, seeded in generate_task()",
            "nondeterministic_elements": [
                "scenario_id contains uuid4 from upstream ScenarioGenerator (does not affect task content)",
            ],
            "content_hash": content_hash,
            "hash_input": hash_input,
            "verification": {
                "method": "Generate same task twice with same seed, compare JSON byte-for-byte",
                "expected": "Identical output",
                "command": "python -c \"import json; t1=json.dumps(gen.generate_task('diagnostic_uncertainty','L2',seed=42)); t2=json.dumps(gen.generate_task('diagnostic_uncertainty','L2',seed=42)); assert t1==t2\"",
            },
            "replay": {
                "description": "Given task JSON + agent action log, evaluator can replay and reproduce identical scores",
                "requires": ["task_id", "seed", "ordered list of agent actions"],
                "guarantees": "Identical observation sequence and final score",
            },
        }
