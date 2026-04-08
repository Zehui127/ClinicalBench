#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scenario Generator — The Core Orchestrator of v2.1 System

v2.1: Scenario is now a constraint engine, not just labels.
Generates ScenarioSpec with enforced constraints, success conditions,
and failure modes that downstream components must obey.

"task_type → difficulty → constraints → disease → scenario"
"""

import random
import uuid
from typing import Dict, List, Optional, Any

from .scenario_schema import (
    ScenarioSpec, ScenarioConstraints, SuccessCondition, FailureMode,
    RiskLevel, ClinicalGroundTruth,
    DIFFICULTY_PROFILES, TASK_TYPES, CONFOUNDER_TYPES,
    CONSTRAINT_TEMPLATES, DEFAULT_SUCCESS_CONDITIONS, DEFAULT_FAILURE_MODES,
    DiagnosticUncertaintyParams, ConflictingEvidenceParams,
    TreatmentTradeoffParams, PatientNonComplianceParams,
    DrugSafetyRiskParams, EmergencyTriageParams,
)
from .risk_model import RiskModel, RiskAssessment
from .uncertainty_model import UncertaintyModel, UncertaintyConfig
from ..clinical_world.disease_sampler import DiseaseSampler


class ScenarioGenerator:
    """
    Generate decision-pressure scenarios with enforced constraints.

    Usage:
        gen = ScenarioGenerator(clinical_kb, primekg)
        scenario = gen.generate("diagnostic_uncertainty", "L2")
        # scenario.constraints.min_required_questions → 4
        # scenario.success_conditions → [...]
        # scenario.failure_modes → [...]
    """

    def __init__(self, clinical_kb, primekg=None):
        self.kb = clinical_kb
        self.primekg = primekg
        self.risk_model = RiskModel()
        self.uncertainty = UncertaintyModel()
        # v2.7: Disease sampler with PrimeKG support
        self._disease_sampler = DiseaseSampler(clinical_kb, primekg)

    def generate(
        self,
        task_type: str,
        difficulty: str = "L2",
        target_disease: Optional[str] = None,
        symptom_keyword: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> ScenarioSpec:
        """Generate a complete scenario specification with constraints."""
        if seed is not None:
            random.seed(seed)

        if task_type not in TASK_TYPES:
            raise ValueError(f"Unknown task_type '{task_type}'. Choose from: {TASK_TYPES}")
        if difficulty not in ("L1", "L2", "L3"):
            raise ValueError(f"difficulty must be L1/L2/L3, got '{difficulty}'")

        profile = DIFFICULTY_PROFILES[difficulty]

        # 1. Sample disease
        disease = target_disease or self._sample_disease(task_type, difficulty)
        if disease is None:
            disease = self._fallback_disease(task_type)
            if disease is None:
                raise ValueError(f"Could not sample disease for task_type={task_type}.")

        disease_profile = self.kb.get_disease_profile(disease)

        # 2. Generate symptom keyword
        symptom = symptom_keyword or self._sample_symptom(disease, disease_profile, task_type)
        if symptom is None:
            symptom = "general discomfort"

        # 3. Determine uncertainty level
        uncertainty_range = profile["uncertainty_range"]
        uncertainty_level = random.uniform(uncertainty_range[0], uncertainty_range[1])

        # 4. Determine risk level
        risk_assessment = self._assess_risk(disease, disease_profile)
        risk_level = risk_assessment.risk_level

        # 5. Select confounders
        confounders = self._select_confounders(task_type, difficulty, profile)

        # 6. Select behavior
        behavior = self._select_behavior(task_type, difficulty, profile)

        # 7. Time pressure
        time_pressure = (
            task_type == "emergency_triage"
            or (difficulty == "L3" and task_type in ("treatment_tradeoff", "drug_safety_risk"))
        )

        # 8. Information completeness
        completeness = profile["information_completeness"]

        # 9. Build CONSTRAINTS (v2.1 core upgrade)
        constraints = self._build_constraints(task_type, difficulty, disease, disease_profile)

        # 10. Build SUCCESS CONDITIONS
        success_conditions = self._build_success_conditions(task_type, difficulty)

        # 11. Build FAILURE MODES
        failure_modes = self._build_failure_modes(task_type, difficulty)

        # 12. Build task params (legacy compat)
        scenario_params = self._build_task_params(task_type, difficulty, disease, disease_profile)

        # 13. Build multi-condition ground truth (v2.3)
        ground_truth = self._build_ground_truth(disease, disease_profile, difficulty)

        # 14. Build scenario ID
        scenario_id = f"v2_{task_type}_{difficulty}_{disease.replace(' ', '_')[:30]}_{uuid.uuid4().hex[:6]}"

        return ScenarioSpec(
            scenario_id=scenario_id,
            task_type=task_type,
            difficulty=difficulty,
            risk_level=risk_level,
            uncertainty_level=round(uncertainty_level, 3),
            time_pressure=time_pressure,
            information_completeness=completeness,
            confounders=confounders,
            target_disease=disease,
            symptom_keyword=symptom,
            ground_truth=ground_truth,
            behavior_type=behavior,
            constraints=constraints,
            success_conditions=success_conditions,
            failure_modes=failure_modes,
            scenario_params=scenario_params,
            generation_seed=seed,
        )

    def generate_batch(
        self,
        task_types: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        count: int = 18,
        seed: int = 42,
    ) -> List[ScenarioSpec]:
        """Generate a batch of diverse scenarios."""
        random.seed(seed)
        if task_types is None:
            task_types = TASK_TYPES
        if difficulties is None:
            difficulties = ["L1", "L2", "L3"]

        scenarios = []
        for _ in range(count):
            tt = random.choice(task_types)
            diff = random.choice(difficulties)
            try:
                s = self.generate(tt, diff)
                scenarios.append(s)
            except Exception:
                continue
        return scenarios

    # ================================================================
    # Constraint Engine (v2.1)
    # ================================================================

    def _build_constraints(
        self, task_type: str, difficulty: str, disease: str, disease_profile
    ) -> ScenarioConstraints:
        """Build constraints from template + disease-specific overrides."""
        # Get template
        templates = CONSTRAINT_TEMPLATES.get(task_type, {})
        base = templates.get(difficulty, ScenarioConstraints())

        # Deep copy to avoid mutating template
        constraints = ScenarioConstraints(
            min_required_questions=base.min_required_questions,
            max_questions_before_diagnosis=base.max_questions_before_diagnosis,
            hidden_symptoms=list(base.hidden_symptoms),
            misleading_symptom_count=base.misleading_symptom_count,
            noise_symptom_count=base.noise_symptom_count,
            missing_critical_info=list(base.missing_critical_info),
            patient_refusal_probability=base.patient_refusal_probability,
            trust_gain_per_empathy=base.trust_gain_per_empathy,
            trust_loss_per_dismissal=base.trust_loss_per_dismissal,
            comorbidity_required=base.comorbidity_required,
            allergy_count=base.allergy_count,
            max_turns=base.max_turns,
            time_limit_minutes=base.time_limit_minutes,
            turn_cost=base.turn_cost,
            drug_interactions=list(base.drug_interactions),
            contraindications=list(base.contraindications),
            lab_conflict_type=base.lab_conflict_type,
            lab_false_negative_rate=base.lab_false_negative_rate,
            lab_delay_turns=base.lab_delay_turns,
        )

        # Disease-specific constraint enrichment
        # Add real disease symptoms to hidden list
        real_symptoms = self._extract_symptom_names(disease, disease_profile)
        n_hidden = constraints.min_required_questions  # roughly correlate
        if len(real_symptoms) > 1:
            hidden = random.sample(real_symptoms, min(n_hidden, len(real_symptoms) - 1))
            constraints.hidden_symptoms = [
                s for s in hidden if not any(s in h for h in constraints.hidden_symptoms)
            ][:3]

        # Add real drug interactions from KB
        meds = self.kb.get_medications_for_condition(disease)
        if meds and len(meds) >= 2:
            interactions = self.kb.check_drug_interactions([m.get("name", str(m)) if isinstance(m, dict) else str(m) for m in meds[:3]])
            if interactions:
                constraints.drug_interactions = [
                    {"drug_a": i.get("drug_a", ""), "drug_b": i.get("drug_b", ""), "severity": i.get("severity", "moderate")}
                    for i in interactions[:2]
                ]

        return constraints

    def _build_success_conditions(
        self, task_type: str, difficulty: str
    ) -> List[SuccessCondition]:
        """Build success conditions from template."""
        conditions = []
        templates = DEFAULT_SUCCESS_CONDITIONS.get(task_type, [])
        for cond_id, desc in templates:
            # Difficulty may relax some conditions
            required = True
            if difficulty == "L1" and cond_id in ("probed_hidden_symptoms", "resolved_conflict", "considered_tradeoffs"):
                required = False  # L1 relaxes these
            conditions.append(SuccessCondition(
                condition_id=cond_id,
                description=desc,
                required=required,
            ))
        return conditions

    def _build_failure_modes(
        self, task_type: str, difficulty: str
    ) -> List[FailureMode]:
        """Build failure modes from template."""
        modes = list(DEFAULT_FAILURE_MODES.get(task_type, []))
        # Difficulty may add extra failure modes
        if difficulty == "L3" and task_type in ("diagnostic_uncertainty", "conflicting_evidence"):
            modes.append(FailureMode(
                mode_id="excessive_turns",
                description="Used too many turns without reaching conclusion",
                severity="warning",
                detection="timeout",
            ))
        return modes

    # ================================================================
    # Internal methods
    # ================================================================

    def _extract_symptom_names(self, disease: str, profile) -> List[str]:
        """Extract symptom names from disease profile."""
        symptoms = []
        profile_data = profile.raw if hasattr(profile, 'raw') else {}
        if isinstance(profile_data, dict):
            symptoms = profile_data.get("differential_questions", [])
        if not symptoms and hasattr(profile, 'aliases'):
            symptoms = profile.aliases or []
        if not symptoms:
            fallback = {
                "diabetes": ["frequent urination", "fatigue", "thirst"],
                "hypertension": ["headache", "dizziness"],
                "heart": ["chest pain", "shortness of breath"],
                "copd": ["cough", "shortness of breath"],
                "asthma": ["wheezing", "shortness of breath"],
                "stroke": ["weakness", "confusion"],
                "arthritis": ["joint pain", "stiffness"],
            }
            for key, syms in fallback.items():
                if key in disease.lower():
                    symptoms = syms
                    break
        return symptoms

    def _sample_disease(self, task_type: str, difficulty: str) -> Optional[str]:
        """Sample disease using DiseaseSampler with PrimeKG support (v2.7)."""
        return self._disease_sampler._sample_for_task_type(task_type, difficulty)

    def _fallback_disease(self, task_type: str) -> Optional[str]:
        fallback_map = {
            "diagnostic_uncertainty": "type 2 diabetes",
            "conflicting_evidence": "hypertension",
            "treatment_tradeoff": "coronary artery disease",
            "patient_non_compliance": "copd",
            "drug_safety_risk": "rheumatoid arthritis",
            "emergency_triage": "stroke",
        }
        return fallback_map.get(task_type, "type 2 diabetes")

    def _sample_symptom(self, disease: str, profile, task_type: str) -> Optional[str]:
        """Sample a chief complaint symptom."""
        symptoms = []
        profile_data = profile.raw if hasattr(profile, 'raw') else {}
        if isinstance(profile_data, dict):
            symptoms = profile_data.get("differential_questions", [])
        if not symptoms:
            symptoms = profile.aliases if hasattr(profile, 'aliases') else []
        if not symptoms:
            common_symptoms = {
                "diabetes": ["frequent urination", "fatigue", "thirst"],
                "hypertension": ["headache", "dizziness"],
                "heart": ["chest pain", "shortness of breath"],
                "lung": ["cough", "shortness of breath"],
                "arthritis": ["joint pain", "stiffness"],
                "asthma": ["wheezing", "shortness of breath"],
                "stroke": ["weakness", "confusion"],
            }
            for key, syms in common_symptoms.items():
                if key in disease.lower():
                    symptoms = syms
                    break
        if not symptoms:
            symptoms = ["fatigue", "pain", "discomfort"]
        return random.choice(symptoms) if symptoms else None

    def _assess_risk(self, disease: str, profile) -> RiskAssessment:
        """Assess risk level for the disease."""
        severity = "moderate"
        if hasattr(profile, 'severity_distribution'):
            sev_dist = profile.severity_distribution
            if sev_dist:
                flat = sev_dist
                first_val = next(iter(sev_dist.values()), None)
                if isinstance(first_val, dict):
                    flat = sev_dist.get("L2", sev_dist.get("L1", first_val))
                if flat:
                    severity = max(flat, key=flat.get)
        return self.risk_model.assess(disease_name=disease, symptoms=[], severity=severity)

    def _select_confounders(self, task_type: str, difficulty: str, profile: dict) -> List[str]:
        max_confounders = profile["max_confounders"]
        if max_confounders == 0:
            return []
        preferred = {
            "diagnostic_uncertainty": ["atypical_symptom", "missing_history", "comorbidity"],
            "conflicting_evidence": ["misleading_symptom", "partial_lab_data", "comorbidity"],
            "treatment_tradeoff": ["comorbidity", "drug_interaction", "allergy_constraint"],
            "patient_non_compliance": ["psychosocial_factor", "misleading_symptom"],
            "drug_safety_risk": ["drug_interaction", "allergy_constraint", "comorbidity"],
            "emergency_triage": ["atypical_presentation", "missing_history", "comorbidity"],
        }
        pool = preferred.get(task_type, CONFOUNDER_TYPES)
        n = random.randint(
            max(0, max_confounders - 1) if difficulty == "L1" else 1,
            max_confounders
        )
        return random.sample(pool, min(n, len(pool)))

    def _select_behavior(self, task_type: str, difficulty: str, profile: dict) -> str:
        pool = profile["behavior_pool"]
        preferred = {
            "patient_non_compliance": ["refusing", "pressuring", "concealing"],
            "drug_safety_risk": ["forgetful", "confused"],
            "emergency_triage": ["cooperative", "anxious"],
        }
        if task_type in preferred:
            candidates = [b for b in preferred[task_type] if b in pool]
            if candidates:
                return random.choice(candidates)
        return random.choice(pool) if pool else "cooperative"

    def _build_task_params(self, task_type: str, difficulty: str, disease: str, profile) -> Dict[str, Any]:
        if task_type == "diagnostic_uncertainty":
            hidden = {"L1": 1, "L2": 2, "L3": 3}.get(difficulty, 2)
            return {"hidden_symptom_count": hidden, "probe_questions_needed": hidden + 1, "differential_depth": {"L1": 2, "L2": 3, "L3": 4}.get(difficulty, 3)}
        elif task_type == "conflicting_evidence":
            return {"conflict_type": random.choice(["lab_vs_history", "imaging_vs_symptom"]), "resolution_strategy": random.choice(["order_additional", "clinical_judgment"])}
        elif task_type == "treatment_tradeoff":
            meds = profile.medications if hasattr(profile, 'medications') else []
            return {"treatment_options": max(2, len(meds)) if meds else 3, "risk_factors": self._get_risk_factors(disease), "patient_preference": random.choice(["neutral", "risk_averse", "aggressive"])}
        elif task_type == "patient_non_compliance":
            return {"refusal_type": random.choice(["test_refusal", "medication_refusal", "lifestyle_resistance"]), "trust_threshold": {"L1": 0.3, "L2": 0.5, "L3": 0.8}.get(difficulty, 0.5), "motivation_strategy": random.choice(["education", "shared_decision", "gradual"])}
        elif task_type == "drug_safety_risk":
            return {"allergy_count": {"L1": 1, "L2": 1, "L3": 2}.get(difficulty, 1), "interaction_severity": {"L1": "mild", "L2": "moderate", "L3": "critical"}.get(difficulty, "moderate"), "alternative_available": True}
        elif task_type == "emergency_triage":
            return {"time_limit_minutes": {"L1": 30, "L2": 15, "L3": 10}.get(difficulty, 15), "critical_interventions": ["stabilize_vitals", "order_emergency_labs"]}
        return {}

    def _get_risk_factors(self, disease: str) -> List[str]:
        profile = self.kb.get_disease_profile(disease)
        factors = []
        if hasattr(profile, 'risk_factors') and profile.risk_factors:
            factors = profile.risk_factors
        elif hasattr(profile, 'raw') and isinstance(profile.raw, dict):
            factors = profile.raw.get("risk_factors", [])
        return factors[:5] if factors else ["age", "family_history"]

    # ================================================================
    # Multi-condition Ground Truth (v2.3)
    # ================================================================

    # How many comorbidities/confounders per difficulty level
    MULTICONDITION_PROFILES = {
        "L1": {"n_comorbidities": (0, 1), "n_confounders": 0, "contribution_threshold": 0.5},
        "L2": {"n_comorbidities": (1, 2), "n_confounders": 1, "contribution_threshold": 0.3},
        "L3": {"n_comorbidities": (2, 3), "n_confounders": 1, "contribution_threshold": 0.2},
    }

    # Common comorbidity pairs (realistic co-occurrence)
    COMORBIDITY_MAP = {
        "type 2 diabetes": ["hypertension", "hyperlipidemia", "coronary artery disease", "chronic kidney disease", "obesity"],
        "hypertension": ["type 2 diabetes", "hyperlipidemia", "chronic kidney disease", "heart failure", "gout"],
        "coronary artery disease": ["hypertension", "type 2 diabetes", "hyperlipidemia", "heart failure"],
        "copd": ["hypertension", "heart failure", "osteoporosis", "anxiety disorder", "lung cancer"],
        "asthma": ["allergic rhinitis", "gerd", "anxiety disorder", "sinusitis"],
        "heart failure": ["hypertension", "type 2 diabetes", "atrial fibrillation", "chronic kidney disease"],
        "stroke": ["hypertension", "type 2 diabetes", "atrial fibrillation", "hyperlipidemia"],
        "atrial fibrillation": ["hypertension", "heart failure", "type 2 diabetes", "hyperthyroidism"],
        "chronic kidney disease": ["type 2 diabetes", "hypertension", "anemia", "hyperparathyroidism"],
        "rheumatoid arthritis": ["osteoporosis", "anemia", "coronary artery disease", "depression"],
        "gerd": ["asthma", "obesity", "hiatal hernia"],
        "hyperlipidemia": ["type 2 diabetes", "hypertension", "coronary artery disease"],
    }

    # Confounder diseases that mimic other conditions
    CONFOUNDER_MAP = {
        "type 2 diabetes": ["hyperthyroidism", "diabetes insipidus"],
        "hypertension": ["anxiety disorder", "pain crisis", "sleep apnea"],
        "coronary artery disease": ["gerd", "anxiety disorder", "musculoskeletal chest pain"],
        "copd": ["asthma", "heart failure", "lung cancer"],
        "asthma": ["copd", "vocal cord dysfunction", "gerd"],
        "heart failure": ["copd", "pneumonia", "pulmonary embolism"],
        "stroke": ["migraine", "hypoglycemia", "seizure"],
        "atrial fibrillation": ["anxiety disorder", "hyperthyroidism", "excessive caffeine"],
        "pneumonia": ["copd", "pulmonary embolism", "heart failure"],
        "migraine": ["tension headache", "stroke", "sinusitis"],
    }

    def _build_ground_truth(
        self, disease: str, disease_profile, difficulty: str
    ) -> ClinicalGroundTruth:
        """
        Build the multi-condition ground truth.

        Real patients have: primary disease + comorbidities + confounders.
        The agent must reason across ALL of these, not just "guess one disease".
        """
        from .scenario_schema import ConditionInfo

        profile = self.MULTICONDITION_PROFILES.get(difficulty, self.MULTICONDITION_PROFILES["L2"])

        # 1. Primary disease (always present)
        primary = ConditionInfo(name=disease, role="primary", severity=0.7, contribution=1.0)

        # 2. Comorbidities (realistic co-occurring conditions)
        comorbidity_pool = self.COMORBIDITY_MAP.get(disease.lower(), [])
        n_comorbidities = random.randint(*profile["n_comorbidities"])
        comorbidities = []

        if comorbidity_pool and n_comorbidities > 0:
            covered = self.kb.get_covered_diseases()
            available = [c for c in comorbidity_pool if c.lower() in [d.lower() for d in covered]]
            if not available:
                available = comorbidity_pool  # fallback to known list

            n = min(n_comorbidities, len(available))
            for c in random.sample(available, n):
                comorbidities.append(ConditionInfo(
                    name=c,
                    role="comorbidity",
                    contribution=random.uniform(profile["contribution_threshold"], 0.6),
                ))

        # 3. Confounder diseases (mimic primary, create diagnostic ambiguity)
        confounder_pool = self.CONFOUNDER_MAP.get(disease.lower(), [])
        n_confounders = profile["n_confounders"]
        confounders = []

        if confounder_pool and n_confounders > 0:
            n = min(n_confounders, len(confounder_pool))
            for c in random.sample(confounder_pool, n):
                confounders.append(ConditionInfo(
                    name=c,
                    role="confounder",
                    contribution=0.2,
                ))

        return ClinicalGroundTruth(
            primary=primary,
            comorbidities=comorbidities,
            confounders=confounders,
        )
