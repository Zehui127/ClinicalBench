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
- Rich persona with socioeconomic factors, family dynamics, misconceptions
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

# Disease → family member disease-specific concerns
FAMILY_CONCERN_TEMPLATES = {
    "diabetes": [
        "Will our children get diabetes too?",
        "Should we throw out all the sweets at home?",
        "I heard supplements can lower blood sugar, should we buy some?",
    ],
    "heart": [
        "Is this genetic? Should our kids get checked?",
        "Can they still drive?",
    ],
    "cancer": [
        "How long do they have?",
        "Is it contagious?",
    ],
    "default": [
        "How can we help at home?",
        "What should we cook for them?",
    ],
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
        if seed is not None:
            random.seed(seed)

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
        task = self._build_task(scenario, symptoms, profile, persona)
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
    ) -> Dict[str, Any]:
        disease = scenario.target_disease or "unknown"
        task_id = f"v27_{scenario.task_type}_{scenario.difficulty}_{disease.replace(' ', '_')[:30]}_{uuid.uuid4().hex[:6]}"

        return {
            "id": task_id,
            "domain": self._infer_domain(disease),
            "task_type": scenario.task_type,
            "difficulty": scenario.difficulty,
            "version": "2.7",

            "description": self._build_description(scenario, profile, persona),
            "user_scenario": self._build_user_scenario(scenario, symptoms, profile, persona),
            "family_member_scenario": self._build_family_scenario(scenario, persona, disease),
            "medical_persona": self._build_medical_persona(scenario, profile, symptoms, persona),
            "ticket": self._build_ticket(scenario, symptoms),
            "initial_state": self._build_initial_state(persona, symptoms),
            "evaluation_criteria": self._build_evaluation_criteria(scenario, profile),

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

        if persona.get("family_member"):
            fm = persona["family_member"]
            desc += f" Accompanied by {fm['relationship']} (age {fm['age']})."

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
                if isinstance(m, dict) and random.random() < m.get("probability", 0.5):
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
                if random.random() < (0.5 if scenario.difficulty == "L3" else 0.3):
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
        jittered = base + random.uniform(-0.1, 0.1) * (high - low)
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

        # Family member interjection items
        if persona.get("family_member"):
            fm = persona["family_member"]
            family_key = "default"
            for key in FAMILY_CONCERN_TEMPLATES:
                if key in disease.lower():
                    family_key = key
                    break
            family_items = FAMILY_CONCERN_TEMPLATES.get(family_key, FAMILY_CONCERN_TEMPLATES["default"])
            strategy["family_member_will_interject"] = [
                f"{fm['relationship']}: {item}" for item in family_items[:4]
            ]

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
            "family_involvement": persona.get("family_member") is not None,
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

        random.shuffle(reveal_pool)
        used = set()

        for i, symptom in enumerate(reveal_pool[:5]):
            patient_term = self.lang.to_patient(symptom)
            if patient_term in used:
                continue
            used.add(patient_term)

            # Assign turn number: spread across the consultation
            turn = min_turns + i * random.randint(1, 3)
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

        # Family member
        if persona.get("family_member"):
            fm = persona["family_member"]
            instructions += (
                f" Your {fm['relationship']} is with you and may speak up during the consultation "
                f"to ask questions or express concerns."
            )

        return instructions

    # ============================================================
    # Family Member Scenario
    # ============================================================

    def _build_family_scenario(self, scenario: ScenarioSpec, persona: Dict, disease: str) -> Optional[Dict]:
        """Build optional family member scenario."""
        fm = persona.get("family_member")
        if not fm:
            return None

        return {
            "scenario": f"{fm['relationship']} accompanies patient, participates in the entire visit",
            "role": fm.get("attitude", "Supportive and concerned"),
            "interaction_timing": [
                "When medication is discussed, the family member asks about costs",
                "After diagnosis is explained, the family member asks about heritability",
                "When a prescription is written, the family member asks about side effects",
                "When lifestyle changes are mentioned, the family member asks for specifics",
            ],
        }

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
            if isinstance(m, dict) and random.random() < m.get("probability", 0.5):
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
                systolic = random.randint(sys_range[0], sys_range[1])
                diastolic = random.randint(dia_range[0], dia_range[1])
                vital_signs["blood_pressure"] = f"{systolic}/{diastolic} mmHg"

            hr = vital_mods.get("heart_rate", {})
            if hr:
                hr_range = hr.get("range", [60, 100])
                vital_signs["heart_rate"] = f"{random.randint(hr_range[0], hr_range[1])} bpm"

            spo2 = vital_mods.get("oxygen_saturation", {})
            if spo2:
                spo2_range = spo2.get("range", [95, 100])
                vital_signs["oxygen_saturation"] = f"{random.randint(spo2_range[0], spo2_range[1])}%"

            # BMI (random, higher for diabetes/metabolic)
            bmi_base = 28 if any(k in disease.lower() for k in ["diabetes", "metabolic", "obesity"]) else 24
            bmi = bmi_base + random.uniform(-3, 3)
            vital_signs["bmi"] = f"{bmi:.1f}"

            medical["vital_signs"] = vital_signs
        else:
            # Default vital signs
            medical["vital_signs"] = {
                "blood_pressure": f"{random.randint(120, 145)}/{random.randint(75, 95)} mmHg",
                "bmi": f"{24 + random.uniform(-3, 4):.1f}",
            }

        # Lifestyle factors
        social_hist = self.kb.get_disease_profile(disease).social_history_relevance if hasattr(profile, 'social_history_relevance') else {}
        if not social_hist and hasattr(profile, 'raw'):
            social_hist = profile.raw.get("social_history_relevance", {})

        lifestyle = {}
        if social_hist.get("smoking", False):
            lifestyle["smoking"] = random.choice([
                "yes (half pack/day for 15+ years)",
                "yes (1 pack/day for 20+ years)",
                "quit 2 years ago (former 1 pack/day for 25 years)",
                "no",
            ])
        if social_hist.get("alcohol", False):
            lifestyle["alcohol"] = random.choice([
                "occasional (1-2 drinks/week)",
                "moderate (3-4 drinks/week)",
                "social drinking only",
                "rarely",
            ])
        lifestyle["exercise"] = random.choice(["sedentary", "light activity 1-2x/week", "moderate 3x/week", "minimal"])
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
            "family_burden": persona.get("family_burden", ""),
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
                    "status": random.choice(["partially_diagnosed", "undiagnosed", "known_to_patient"]),
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
        return random.sample(common_allergies, min(count, len(common_allergies)))

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
                        "mrn": f"MRN{random.randint(100000, 999999)}",
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
        age = random.randint(age_range[0], age_range[1])

        gender = random.choice(["male", "female"])

        # Name generation
        first_names = {
            "male": ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Zhao", "Huang", "Zhou", "Wu"],
            "female": ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Zhao", "Huang", "Zhou", "Wu"],
        }
        name = f"{random.choice(first_names[gender])}XX"

        # Education level from behavior
        edu_level = BEHAVIOR_PROFILES.get(behavior, BEHAVIOR_PROFILES["cooperative"]).get("education_level", "high_school")

        # Occupation from education
        occupations = OCCUPATIONS.get(edu_level, OCCUPATIONS["high_school"])
        occupation = random.choice(occupations)

        # Economic status
        economic_choices = ["low", "moderate", "moderate", "comfortable"]
        economic_status = random.choice(economic_choices)

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

        # Family member (50% chance for L2+, higher for confused/forgetful)
        family_chance = 0.7 if behavior in ("confused", "forgetful") else 0.5
        family_member = None
        if scenario.difficulty != "L1" and random.random() < family_chance:
            fm_relations = {
                "male": [("wife", 2), ("daughter", -20), ("son", -20)],
                "female": [("husband", 2), ("daughter", -20), ("son", -20)],
            }
            relations = fm_relations.get(gender, fm_relations["male"])
            relation, age_diff = random.choice(relations)
            fm_age = max(18, age + age_diff + random.randint(-3, 3))
            family_member = {
                "relationship": relation,
                "age": fm_age,
                "education_level": random.choice(["elementary", "middle_school", "high_school"]),
                "role": "primary caregiver, accompanies to visits",
                "attitude": "concerned and supportive, may express economic worries",
                "knowledge_level": "limited medical knowledge, many questions",
            }

        # Family burden text
        family_burden = ""
        if random.random() < 0.5:
            burdens = [
                "two children in school, financial pressure",
                "elderly parents to care for",
                "single income household",
            ]
            family_burden = random.choice(burdens)

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
            "family_member": family_member,
            "family_burden": family_burden,
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
