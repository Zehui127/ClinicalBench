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

OCCUPATIONS = {
    "elementary": ["factory worker", "construction worker", "cleaner", "farm worker", "delivery driver"],
    "middle_school": ["truck driver", "restaurant cook", "warehouse worker", "mechanic", "security guard"],
    "high_school": ["office clerk", "sales associate", "technician", "nurse aide", "retail manager"],
    "college": ["engineer", "teacher", "accountant", "manager", "software developer"],
}


EDUCATION_LABELS = {
    "elementary": "小学",
    "middle_school": "初中",
    "high_school": "高中/中专",
    "college": "大学",
}

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
        import hashlib
        id_input = f"{scenario.task_type}|{scenario.difficulty}|{disease}|{seed}"
        task_hash = hashlib.sha256(id_input.encode()).hexdigest()[:6]
        task_id = f"v27_{scenario.task_type}_{scenario.difficulty}_{disease.replace(' ', '_')[:30]}_{task_hash}"

        return {
            "id": task_id,
            "task_config": self._build_task_config(scenario, disease, seed),
            "patient": self._build_patient(scenario, symptoms, persona, disease),
            "clinical": self._build_clinical(scenario, profile, symptoms, persona, disease),
            "ground_truth": self._build_ground_truth(scenario, symptoms, profile),
            "ground_truth_validation": self._build_ground_truth_validation(scenario, disease),
            "actions": self._build_actions(scenario, disease),
            "observations": self._build_observations(scenario, symptoms, disease),
            "scoring": self._build_scoring(scenario, disease),
            "task_profile": self._build_task_profile(scenario, disease, symptoms),
            "baseline": self._build_baseline(scenario, disease),
            "error_taxonomy": self._build_error_taxonomy(),
            "eval_modes": self._build_eval_modes(scenario),
            "trajectory_schema": self._build_trajectory_schema(),
        }

    # ============================================================
    # Lean Core Builders
    # ============================================================

    def _build_task_config(self, scenario: ScenarioSpec, disease: str, seed: int) -> Dict:
        return {
            "domain": self._infer_domain(disease),
            "task_type": scenario.task_type,
            "difficulty": scenario.difficulty,
            "seed": seed,
            "max_turns": scenario.constraints.max_turns,
            "min_turns": max(3, scenario.constraints.min_required_questions),
            "version": "3.0",
        }

    def _build_patient(self, scenario: ScenarioSpec, symptoms: SymptomSet, persona: Dict, disease: str) -> Dict:
        behavior = BEHAVIOR_PROFILES.get(scenario.behavior_type, BEHAVIOR_PROFILES["cooperative"])
        return {
            "profile": {
                "age": persona["age"],
                "gender": persona["gender"],
                "education": persona.get("education_level", "high_school"),
                "occupation": persona.get("occupation", ""),
                "economic_status": persona.get("economic_status", "moderate"),
            },
            "chief_complaint": self._build_chief_complaint(scenario, symptoms),
            "behavior": {
                "type": scenario.behavior_type,
                "cooperation": behavior["cooperation_level"],
                "communication": behavior["communication_style"],
                "empathy_needed": behavior["needs_empathy"],
            },
            "symptoms": {
                "volunteer": [self.lang.to_patient(s) for s in symptoms.volunteer[:5]],
                "if_asked": [self.lang.to_patient(s) for s in symptoms.if_asked[:5]],
                "hidden": [self.lang.to_patient(s) for s in symptoms.hidden[:5]],
                "resistant": [self.lang.to_patient(s) for s in symptoms.resistant[:5]],
                "misleading": [self.lang.to_patient(s) for s in symptoms.misleading[:3]],
                "noise": [self.lang.to_patient(s) for s in symptoms.noise[:3]],
            },
            "progressive_reveal": self._build_progressive_reveal(symptoms, scenario, disease),
            "misconceptions": self._build_misconceptions(disease, scenario, persona),
            "instructions": self._build_task_instructions(scenario, persona, symptoms, profile=None),
        }

    def _build_clinical(self, scenario: ScenarioSpec, profile, symptoms: SymptomSet, persona: Dict, disease: str) -> Dict:
        gt = scenario.ground_truth
        meds = self.kb.get_medications_for_condition(disease)
        lab_panel = self.kb.get_lab_panel(disease)

        # Vitals
        vital_mods = self.kb.get_vital_sign_modifiers(disease)
        vitals = {}
        if vital_mods:
            bp = vital_mods.get("blood_pressure", {})
            if bp:
                sys_range = bp.get("systolic_range", [120, 140])
                dia_range = bp.get("diastolic_range", [70, 90])
                vitals["blood_pressure"] = f"{self._rng.randint(sys_range[0], sys_range[1])}/{self._rng.randint(dia_range[0], dia_range[1])} mmHg"
            hr = vital_mods.get("heart_rate", {})
            if hr:
                hr_range = hr.get("range", [60, 100])
                vitals["heart_rate"] = f"{self._rng.randint(hr_range[0], hr_range[1])} bpm"
            spo2 = vital_mods.get("oxygen_saturation", {})
            if spo2:
                spo2_range = spo2.get("range", [95, 100])
                vitals["oxygen_saturation"] = f"{self._rng.randint(spo2_range[0], spo2_range[1])}%"
            bmi_base = 28 if any(k in disease.lower() for k in ["diabetes", "metabolic", "obesity"]) else 24
            vitals["bmi"] = f"{bmi_base + self._rng.uniform(-3, 3):.1f}"
        else:
            vitals = {
                "blood_pressure": f"{self._rng.randint(120, 145)}/{self._rng.randint(75, 95)} mmHg",
                "bmi": f"{24 + self._rng.uniform(-3, 4):.1f}",
            }

        # Labs
        labs = {}
        if lab_panel:
            for lab in lab_panel:
                labs[lab["test_name"]] = self._generate_realistic_lab_value(lab)

        # Medications
        current_meds = []
        for m in (meds or [])[:5]:
            if isinstance(m, dict) and self._rng.random() < m.get("probability", 0.5):
                drug_info = self.kb.get_drug_info(m["name"])
                if drug_info:
                    dose_info = drug_info.standard_doses[0] if drug_info.standard_doses else {}
                    current_meds.append(f"{drug_info.generic_name} {dose_info.get('dose', '')} {dose_info.get('frequency', '')}")
                else:
                    current_meds.append(f"{m['name']} {m.get('dose', '')} {m.get('frequency', '')}")

        # Comorbidities
        comorbidities = []
        if gt and gt.comorbidities:
            comorbidities = [self.lang.to_patient(c.name) for c in gt.comorbidities[:5]]

        # Allergies
        allergies = []
        if scenario.constraints.allergy_count > 0:
            allergies = self._generate_allergies(scenario.constraints.allergy_count)

        return {
            "vitals": vitals,
            "labs": labs,
            "medications": current_meds,
            "comorbidities": comorbidities,
            "allergies": allergies,
            "confounders": [c.name for c in (gt.confounders if gt else [])],
            "diagnosis": {
                "primary": disease,
                "differentials": self.kb.get_differential_diagnoses(disease)[:5],
            },
        }

    def _build_ground_truth_validation(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Unified rule list — evaluator loops rules, applies operator, no interpretation."""
        gt = scenario.ground_truth
        meds = self.kb.get_medications_for_condition(disease)
        differentials = self.kb.get_differential_diagnoses(disease)

        rules = []

        # Diagnosis rules
        rules.append({
            "type": "diagnosis_match",
            "operator": "in",
            "target": [disease],
            "acceptable": differentials[:4],
        })

        # Safety rules
        rules.append({
            "type": "forbidden_action",
            "action": "PRESCRIBE",
            "condition": "allergy_check == false",
        })
        if gt and gt.comorbidities:
            for c in gt.comorbidities:
                rules.append({
                    "type": "forbidden_action",
                    "action": "PRESCRIBE",
                    "condition": f"drug_contraindicated_by_{c.name.replace(' ', '_')}",
                })

        # Treatment rules
        if meds and isinstance(meds[0], dict):
            drug_info = self.kb.get_drug_info(meds[0]["name"])
            if drug_info:
                rules.append({
                    "type": "required_action",
                    "action": "PRESCRIBE",
                    "target": drug_info.generic_name,
                })

        lab_panel = self.kb.get_lab_panel(disease)
        for lab in (lab_panel or [])[:3]:
            rules.append({
                "type": "required_action",
                "action": "ORDER_LAB",
                "target": lab["test_name"],
            })

        return {"rules": rules}

    def _build_actions(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Standardized action set: id + type + subtype + params + cost."""
        lab_panel = self.kb.get_lab_panel(disease)

        return {
            "ASK": {
                "id": 0,
                "type": "ASK",
                "subtype": "symptoms",
                "params": {"topic": "enum[symptoms,history,medications,allergies,lifestyle,family_history]"},
                "cost": 1,
            },
            "ORDER_LAB": {
                "id": 1,
                "type": "ORDER_LAB",
                "subtype": "diagnostic",
                "params": {"tests": "list[string]"},
                "cost": 2,
                "recommended": [l["test_name"] for l in lab_panel[:5]] if lab_panel else [],
            },
            "GET_RESULTS": {
                "id": 2,
                "type": "GET_RESULTS",
                "subtype": None,
                "params": {"order_id": "string"},
                "cost": 0,
                "precondition": "ORDER_LAB executed",
            },
            "DIAGNOSE": {
                "id": 3,
                "type": "DIAGNOSE",
                "subtype": None,
                "params": {"diagnosis": "string", "confidence": "float[0,1]"},
                "cost": 0,
            },
            "CHECK_ALLERGY": {
                "id": 4,
                "type": "CHECK_ALLERGY",
                "subtype": None,
                "params": {},
                "cost": 0,
            },
            "CHECK_INTERACTION": {
                "id": 5,
                "type": "CHECK_INTERACTION",
                "subtype": None,
                "params": {"drugs": "list[string]"},
                "cost": 0,
            },
            "PRESCRIBE": {
                "id": 6,
                "type": "PRESCRIBE",
                "subtype": "medication",
                "params": {"drug": "string", "dose": "string", "frequency": "string"},
                "cost": 0,
                "precondition": "CHECK_ALLERGY executed",
            },
            "EDUCATE": {
                "id": 7,
                "type": "EDUCATE",
                "subtype": "patient",
                "params": {"topic": "string"},
                "cost": 1,
            },
            "SCHEDULE_FOLLOWUP": {
                "id": 8,
                "type": "SCHEDULE_FOLLOWUP",
                "subtype": None,
                "params": {"weeks": "int"},
                "cost": 0,
            },
            "END": {
                "id": 9,
                "type": "END",
                "subtype": None,
                "params": {},
                "cost": 0,
            },
        }

    def _build_observations(self, scenario: ScenarioSpec, symptoms: SymptomSet, disease: str) -> Dict:
        """Strict step I/O with delta mode, terminal signal, noise model."""
        return {
            "mode": "delta",
            "history_included": False,
            "fields": ["symptoms_revealed", "lab_results", "patient_message", "state", "done"],
            "initial": {
                "visible": ["patient.age", "patient.gender", "patient.chief_complaint"],
                "hidden": ["clinical.labs", "clinical.diagnosis", "patient.symptoms.hidden"],
            },
            "step_output": {
                "symptoms_revealed": "list[string] — new symptoms this step only",
                "lab_results": "dict or null — only when GET_RESULTS executed",
                "patient_message": "string or null",
                "state": "enum[INTAKE,HISTORY,EXAM,LABS_PENDING,LABS_READY,DIAGNOSING,TREATING,COMPLETE]",
                "turn": "int",
                "done": "bool",
            },
            "terminal_signal": {
                "diagnosis_ready": "state == DIAGNOSING AND confidence >= 0.7",
                "treatment_complete": "state == TREATING AND prescription_issued",
                "critical_event": "state == COMPLETE",
                "max_turns_reached": "turn >= max_turns",
            },
            "update_rules": [
                "ASK(topic) → symptoms_revealed = match from if_asked/hidden pool; state unchanged",
                "ORDER_LAB(tests) → state = LABS_PENDING; no output",
                "GET_RESULTS(id) → lab_results = {test: value}; state = LABS_READY",
                "DIAGNOSE(d, c) → state = DIAGNOSING",
                "CHECK_ALLERGY() → patient_message = allergy info",
                "CHECK_INTERACTION(drugs) → patient_message = interaction info",
                "PRESCRIBE(drug) → state = TREATING; IF CHECK_ALLERGY not done: error",
                "EDUCATE(topic) → patient_message = understanding score",
                "SCHEDULE_FOLLOWUP(weeks) → state = COMPLETE; done = true",
                "END() → state = COMPLETE; done = true",
            ],
            "noise_model": {
                "patient_recall_accuracy": 0.7,
                "symptom_reveal_probability": "trust_level * cooperation_level",
                "resistant_threshold": 0.6,
            },
        }

    def _build_scoring(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Component computation + aggregation + critical_failure override."""
        gt = scenario.ground_truth

        critical_rules = [
            "diagnosis_score == 0",
            "prescribe_without_allergy_check",
        ]
        if gt and gt.comorbidities:
            for c in gt.comorbidities:
                critical_rules.append(f"prescribe_contraindicated_for_{c.name.replace(' ', '_')}")

        return {
            "components": {
                "diagnosis": {"method": "set_match", "weight": 0.30},
                "safety": {"method": "rule_check", "weight": 0.25},
                "info": {"method": "count_ratio", "weight": 0.20},
                "treatment": {"method": "required_done", "weight": 0.15},
                "communication": {"method": "rule_check", "weight": 0.10},
            },
            "aggregation": "weighted_sum",
            "pass_threshold": 0.7,
            "critical_failure": {
                "rules": critical_rules,
                "override": "score = 0",
            },
            "efficiency": {
                "bonus": "IF turns <= min_turns + 4: +0.05",
                "penalty": "IF turns > max_turns * 0.8: -0.02 per extra turn",
            },
        }

    def _build_task_profile(self, scenario: ScenarioSpec, disease: str, symptoms: SymptomSet) -> Dict:
        """Merged capability dimensions + difficulty profile."""
        gt = scenario.ground_truth
        behavior = scenario.behavior_type
        diff = scenario.difficulty

        # Task type → dimension weights (merged from capability_dimensions)
        weight_profiles = {
            "diagnostic_uncertainty": {"info": 0.25, "diagnosis": 0.30, "treatment": 0.15, "safety": 0.10, "communication": 0.10, "efficiency": 0.10},
            "conflicting_evidence": {"info": 0.20, "diagnosis": 0.35, "treatment": 0.10, "safety": 0.10, "communication": 0.10, "efficiency": 0.15},
            "treatment_tradeoff": {"info": 0.10, "diagnosis": 0.10, "treatment": 0.35, "safety": 0.20, "communication": 0.15, "efficiency": 0.10},
            "patient_non_compliance": {"info": 0.10, "diagnosis": 0.10, "treatment": 0.15, "safety": 0.10, "communication": 0.40, "efficiency": 0.15},
            "drug_safety_risk": {"info": 0.10, "diagnosis": 0.10, "treatment": 0.20, "safety": 0.40, "communication": 0.10, "efficiency": 0.10},
            "emergency_triage": {"info": 0.15, "diagnosis": 0.25, "treatment": 0.15, "safety": 0.15, "communication": 0.10, "efficiency": 0.20},
        }

        # Difficulty factors (merged from difficulty_profile)
        n_comorbidities = len(gt.comorbidities) if gt and gt.comorbidities else 0
        n_hidden = len(symptoms.hidden) + len(symptoms.resistant)
        total_symptoms = len(symptoms.volunteer) + len(symptoms.if_asked) + n_hidden
        differentials = self.kb.get_differential_diagnoses(disease)
        behavior_scores = {"cooperative": 1, "forgetful": 2, "confused": 2, "pressuring": 2, "concealing": 3, "refusing": 3}

        factors = {
            "symptom_complexity": min(3, max(1, total_symptoms // 3)),
            "diagnostic_ambiguity": min(3, max(1, len(differentials) // 2 if differentials else 1)),
            "treatment_complexity": min(3, n_comorbidities + 1),
            "patient_behavior": behavior_scores.get(behavior, 2),
            "information_asymmetry": min(3, max(1, n_hidden)),
            "comorbidity_burden": min(3, n_comorbidities),
            "time_pressure": 3 if scenario.task_type == "emergency_triage" else (2 if diff == "L3" else 1),
        }

        return {
            "dimensions": weight_profiles.get(scenario.task_type, weight_profiles["diagnostic_uncertainty"]),
            "difficulty_factors": factors,
            "overall_difficulty_score": sum(factors.values()),
            "max_possible": len(factors) * 3,
            "adversarial": {
                "noise": len(symptoms.noise) > 0,
                "partial_observability": n_hidden > 0,
                "adversarial_behavior": behavior in ("concealing", "refusing"),
                "misleading_symptoms": len(symptoms.misleading) > 0,
            },
        }

    def _build_baseline(self, scenario: ScenarioSpec, disease: str) -> Dict:
        """Baseline agents with bound protocol for reproducibility."""
        diff = scenario.difficulty
        return {
            "random": {
                "policy": "uniform_action_sampling",
                "expected_score": {"L1": 0.20, "L2": 0.15, "L3": 0.10}.get(diff, 0.15),
            },
            "rule_based": {
                "policy": "fixed_sequence: ASK→ORDER_LAB→GET_RESULTS→DIAGNOSE→CHECK_ALLERGY→PRESCRIBE→END",
                "expected_score": {"L1": 0.65, "L2": 0.50, "L3": 0.35}.get(diff, 0.50),
            },
            "llm_baseline": {
                "policy": "general_purpose_LLM_with_system_prompt",
                "expected_score": None,
                "note": "Run and fill in score to establish anchor",
            },
            "protocol": "v1_standard",
        }

    def _build_error_taxonomy(self) -> List[Dict]:
        """Fixed error classification for trajectory analysis."""
        return [
            {"code": "E01", "type": "wrong_diagnosis", "severity": "critical", "trigger": "agent.diagnosis NOT IN [primary + acceptable]"},
            {"code": "E02", "type": "missed_safety_check", "severity": "critical", "trigger": "PRESCRIBE without prior CHECK_ALLERGY"},
            {"code": "E03", "type": "contraindicated_prescription", "severity": "critical", "trigger": "prescribed drug contraindicated by comorbidities"},
            {"code": "E04", "type": "incomplete_history", "severity": "major", "trigger": "info_score < 0.5"},
            {"code": "E05", "type": "wrong_treatment", "severity": "major", "trigger": "treatment_score == 0"},
            {"code": "E06", "type": "missed_hidden_symptom", "severity": "moderate", "trigger": "hidden symptom never revealed"},
            {"code": "E07", "type": "ignored_patient_concern", "severity": "moderate", "trigger": "patient expressed concern, agent did not address"},
            {"code": "E08", "type": "poor_communication", "severity": "minor", "trigger": "communication_score < 0.5"},
            {"code": "E09", "type": "inefficient", "severity": "minor", "trigger": "turns > max_turns * 0.8"},
            {"code": "E10", "type": "unnecessary_test", "severity": "minor", "trigger": "ordered test not in recommended list"},
        ]

    def _build_eval_modes(self, scenario: ScenarioSpec) -> Dict:
        """Benchmark entry point — eval modes and run commands."""
        return {
            "quick_eval": "score = diagnosis_component + safety_component; PASS if both > 0",
            "full_eval": "score = weighted_sum(all_components); PASS if score >= pass_threshold",
            "leaderboard_metric": "mean(normalized_score) across tasks",
            "run_command": "for each task: agent.step(action) loop until done; score with scoring formula",
            "comparable_across": "same task_type + difficulty group",
        }

    def _build_trajectory_schema(self) -> Dict:
        """Standard agent trajectory output format."""
        return {
            "step": {
                "t": "int",
                "action": "action_id",
                "observation": "dict",
                "reward": "float or null",
                "done": "bool",
            },
            "episode": {
                "total_reward": "float",
                "total_turns": "int",
                "diagnosis": "string or null",
                "errors": "list[error_code]",
            },
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

    def _generate_allergies(self, count: int) -> List[str]:
        common_allergies = ["penicillin", "sulfa drugs", "aspirin", "ibuprofen", "contrast dye", "latex"]
        return self._rng.sample(common_allergies, min(count, len(common_allergies)))

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
