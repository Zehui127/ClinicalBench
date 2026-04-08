#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scenario Schema — The Core Unit of v2 Benchmark System

A Scenario is NOT a "disease case". It's a decision pressure situation
that tests a specific clinical reasoning capability.

v2.1: Scenario is now a CONSTRAINT ENGINE, not just labels.
- constraints: enforce what the system must do
- success_conditions: define what "passing" looks like
- failure_modes: define what "failing" looks like
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum


# ============================================================
# Task Types — 6 Decision Pressure Categories
# ============================================================

class TaskType(str, Enum):
    """Six categories of clinical decision pressure."""
    DIAGNOSTIC_UNCERTAINTY = "diagnostic_uncertainty"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    TREATMENT_TRADEOFF = "treatment_tradeoff"
    PATIENT_NON_COMPLIANCE = "patient_non_compliance"
    DRUG_SAFETY_RISK = "drug_safety_risk"
    EMERGENCY_TRIAGE = "emergency_triage"


TASK_TYPES = [t.value for t in TaskType]

TASK_TYPE_DESCRIPTIONS = {
    "diagnostic_uncertainty": (
        "Information is incomplete. Agent must probe to gather hidden symptoms, "
        "order targeted tests, and reason under uncertainty before diagnosing."
    ),
    "conflicting_evidence": (
        "Lab results or imaging contradict the clinical history. "
        "Agent must reconcile contradictions and avoid premature closure."
    ),
    "treatment_tradeoff": (
        "Multiple treatment options exist with competing risks/benefits. "
        "Agent must weigh tradeoffs and align with patient preferences."
    ),
    "patient_non_compliance": (
        "Patient is reluctant, forgetful, or refuses tests/treatment. "
        "Agent must build trust, motivate compliance, and adapt strategy."
    ),
    "drug_safety_risk": (
        "Patient has allergies, drug interactions, or contraindications. "
        "Agent must identify and navigate medication safety challenges."
    ),
    "emergency_triage": (
        "Time-critical situation requiring rapid assessment and triage. "
        "Agent must prioritize, act fast, and avoid dangerous delays."
    ),
}


# ============================================================
# Difficulty Levels
# ============================================================

class DifficultyLevel(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


# How scenario parameters scale with difficulty
DIFFICULTY_PROFILES = {
    "L1": {
        "uncertainty_range": (0.1, 0.4),
        "max_confounders": 1,
        "behavior_pool": ["cooperative"],
        "information_completeness": "partial",
        "time_pressure": False,
        "noise_symptom_count": (0, 1),
        "missing_symptom_fraction": (0.0, 0.2),
    },
    "L2": {
        "uncertainty_range": (0.4, 0.7),
        "max_confounders": 2,
        "behavior_pool": ["cooperative", "forgetful", "confused", "concealing"],
        "information_completeness": "partial",
        "time_pressure": False,
        "noise_symptom_count": (1, 2),
        "missing_symptom_fraction": (0.2, 0.4),
    },
    "L3": {
        "uncertainty_range": (0.7, 1.0),
        "max_confounders": 3,
        "behavior_pool": ["forgetful", "confused", "concealing", "pressuring", "refusing"],
        "information_completeness": "minimal",
        "time_pressure": True,
        "noise_symptom_count": (2, 3),
        "missing_symptom_fraction": (0.4, 0.6),
    },
}


# ============================================================
# Risk Levels
# ============================================================

class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# Confounders — Things that make scenarios harder
# ============================================================

CONFOUNDER_TYPES = [
    "comorbidity",
    "atypical_presentation",
    "drug_interaction",
    "misleading_symptom",
    "missing_history",
    "allergy_constraint",
    "psychosocial_factor",
    "partial_lab_data",
]


# ============================================================
# Constraint Engine — What the scenario ENFORCES
# ============================================================

@dataclass
class ScenarioConstraints:
    """
    Constraints that actually control system behavior.

    These are NOT labels — they are enforced rules that downstream
    components (patient agent, clinical world, evaluation) must obey.
    """
    # --- Information constraints ---
    min_required_questions: int = 3         # Agent MUST ask at least N questions
    max_questions_before_diagnosis: int = 10  # Agent shouldn't ask > N before diagnosing
    hidden_symptoms: List[str] = field(default_factory=list)  # Symptoms patient won't volunteer
    misleading_symptom_count: int = 0       # Number of misleading symptoms injected
    noise_symptom_count: int = 0            # Number of unrelated noise symptoms
    missing_critical_info: List[str] = field(default_factory=list)  # Key info that's hidden

    # --- Behavioral constraints ---
    patient_refusal_probability: float = 0.0  # Base probability patient refuses any action
    trust_gain_per_empathy: float = 0.15     # Trust gained per empathetic action
    trust_loss_per_dismissal: float = 0.2    # Trust lost per dismissive action
    comorbidity_required: bool = False        # Must handle comorbidity
    allergy_count: int = 0                    # Number of allergies to inject

    # --- Temporal constraints ---
    max_turns: int = 30                      # Hard turn limit
    time_limit_minutes: int = 0              # Simulated time limit (0 = no limit)
    turn_cost: float = 0.0                   # Score penalty per turn (efficiency pressure)

    # --- Clinical constraints ---
    drug_interactions: List[Dict[str, str]] = field(default_factory=list)  # Active interactions
    contraindications: List[str] = field(default_factory=list)
    lab_conflict_type: str = ""              # For conflicting_evidence: type of lab conflict
    lab_false_negative_rate: float = 0.0     # Probability of false negative lab result
    lab_delay_turns: int = 0                 # How many turns before lab results available

    def check_violated(self, state: Dict[str, Any]) -> List[str]:
        """Check which constraints are violated given current state."""
        violations = []
        if state.get("turn_count", 0) > self.max_turns:
            violations.append(f"exceeded_max_turns: {state['turn_count']} > {self.max_turns}")
        return violations

    def soft_evaluate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Soft constraint evaluation — returns continuous scores, not binary pass/fail.

        Core principle: don't penalize "efficiently correct", only "carelessly wrong".

        Returns:
            {
                "question_score": 0.0-1.0,    # How well did agent probe?
                "efficiency_score": 0.0-1.0,   # Was agent efficient?
                "evidence_score": 0.0-1.0,      # Did agent gather evidence?
                "violations": [...],             # Hard violations (exceeded limits)
                "soft_penalties": [...],         # Soft penalties with magnitude
                "shortcut_bonus": 0.0,           # Bonus for efficient correct shortcuts
            }
        """
        q_count = state.get("question_count", 0)
        diagnosed = state.get("diagnosed", False)
        correct = state.get("correct_diagnosis", False)
        turn_count = state.get("turn_count", 0)
        lab_results = state.get("lab_results_count", 0)

        result = {
            "question_score": 0.0,
            "efficiency_score": 0.0,
            "evidence_score": 0.0,
            "violations": [],
            "soft_penalties": [],
            "shortcut_bonus": 0.0,
        }

        # --- Hard violations (binary) ---
        if turn_count > self.max_turns:
            result["violations"].append(f"exceeded_max_turns: {turn_count} > {self.max_turns}")

        # --- Soft: Question adequacy ---
        if diagnosed:
            if q_count >= self.min_required_questions:
                # Met the guideline → full score
                result["question_score"] = 1.0
            elif correct and q_count >= max(1, self.min_required_questions - 1):
                # Shortcut: asked fewer but still correct → small penalty
                # "Don't penalize efficiently correct"
                shortfall = self.min_required_questions - q_count
                result["question_score"] = max(0.7, 1.0 - shortfall * 0.1)
                result["shortcut_bonus"] = 0.1  # Bonus for efficiency
                result["soft_penalties"].append(
                    f"shortcut_correct: asked {q_count}/{self.min_required_questions} but correct"
                )
            elif correct:
                # Correct but really didn't probe enough
                shortfall = self.min_required_questions - q_count
                result["question_score"] = max(0.3, 0.7 - shortfall * 0.15)
                result["soft_penalties"].append(
                    f"insufficient_probe: asked {q_count}/{self.min_required_questions}, still correct"
                )
            else:
                # Incorrect AND didn't ask enough → heavy penalty
                shortfall = self.min_required_questions - q_count
                result["question_score"] = max(0.0, 0.3 - shortfall * 0.15)
                result["soft_penalties"].append(
                    f"carelessly_wrong: asked {q_count}/{self.min_required_questions} AND incorrect"
                )
        else:
            # No diagnosis yet — evaluate progress
            progress = min(1.0, q_count / max(1, self.min_required_questions))
            result["question_score"] = progress

        # --- Soft: Efficiency ---
        if self.turn_cost > 0 and turn_count > 0:
            # Reward fewer turns for same outcome
            ideal_turns = self.min_required_questions + 2  # questions + lab + diagnosis
            if turn_count <= ideal_turns:
                result["efficiency_score"] = 1.0
            else:
                excess = turn_count - ideal_turns
                result["efficiency_score"] = max(0.0, 1.0 - excess * self.turn_cost)
        else:
            result["efficiency_score"] = 0.7  # Neutral if no cost pressure

        # --- Soft: Evidence gathering ---
        has_symptoms = state.get("reported_symptoms_count", 0) > 0
        has_labs = lab_results > 0
        if diagnosed:
            if has_symptoms and has_labs:
                result["evidence_score"] = 1.0
            elif has_symptoms or has_labs:
                result["evidence_score"] = 0.6
            elif correct:
                # Correct without any evidence → suspicious but not fatal
                result["evidence_score"] = 0.3
                result["soft_penalties"].append("diagnosed_without_evidence")
            else:
                result["evidence_score"] = 0.0
        else:
            result["evidence_score"] = 0.5

        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_required_questions": self.min_required_questions,
            "max_questions_before_diagnosis": self.max_questions_before_diagnosis,
            "hidden_symptoms": self.hidden_symptoms,
            "misleading_symptom_count": self.misleading_symptom_count,
            "noise_symptom_count": self.noise_symptom_count,
            "missing_critical_info": self.missing_critical_info,
            "patient_refusal_probability": self.patient_refusal_probability,
            "trust_gain_per_empathy": self.trust_gain_per_empathy,
            "trust_loss_per_dismissal": self.trust_loss_per_dismissal,
            "comorbidity_required": self.comorbidity_required,
            "allergy_count": self.allergy_count,
            "max_turns": self.max_turns,
            "time_limit_minutes": self.time_limit_minutes,
            "turn_cost": self.turn_cost,
            "drug_interactions": self.drug_interactions,
            "contraindications": self.contraindications,
            "lab_false_negative_rate": self.lab_false_negative_rate,
            "lab_delay_turns": self.lab_delay_turns,
        }


@dataclass
class SuccessCondition:
    """A condition that must be met for the scenario to be considered successful."""
    condition_id: str
    description: str
    required: bool = True
    check_type: str = "state"  # "state" = check conversation state, "action" = check agent actions

    def check(self, state: Dict[str, Any]) -> bool:
        """Evaluate this condition against state."""
        # Default: check if condition_id key exists in state
        return state.get(self.condition_id, False)


@dataclass
class FailureMode:
    """A specific way the agent can fail this scenario."""
    mode_id: str
    description: str
    severity: str = "critical"  # "warning", "critical", "fatal"
    detection: str = ""         # How to detect: "state_check", "action_pattern", "timeout"
    auto_fail: bool = False     # If True, scenario immediately fails on this


# ============================================================
# Task-type-specific constraint templates
# ============================================================

CONSTRAINT_TEMPLATES = {
    "diagnostic_uncertainty": {
        "L1": ScenarioConstraints(
            min_required_questions=2,
            hidden_symptoms=["hidden_1"],
            missing_critical_info=["one_key_symptom"],
            max_turns=20,
        ),
        "L2": ScenarioConstraints(
            min_required_questions=4,
            hidden_symptoms=["hidden_1", "hidden_2"],
            misleading_symptom_count=1,
            missing_critical_info=["key_symptom", "onset_timing"],
            comorbidity_required=True,
            max_turns=25,
            turn_cost=0.02,
        ),
        "L3": ScenarioConstraints(
            min_required_questions=6,
            hidden_symptoms=["hidden_1", "hidden_2", "hidden_3"],
            misleading_symptom_count=2,
            missing_critical_info=["critical_symptom", "onset_timing", "relevant_history"],
            comorbidity_required=True,
            patient_refusal_probability=0.3,
            max_turns=20,
            turn_cost=0.04,
            lab_delay_turns=2,
        ),
    },
    "conflicting_evidence": {
        "L1": ScenarioConstraints(
            min_required_questions=2,
            lab_conflict_type="lab_vs_history",
            max_turns=20,
        ),
        "L2": ScenarioConstraints(
            min_required_questions=3,
            lab_conflict_type="lab_vs_history",
            lab_false_negative_rate=0.1,
            noise_symptom_count=1,
            max_turns=25,
        ),
        "L3": ScenarioConstraints(
            min_required_questions=5,
            lab_conflict_type="imaging_vs_symptom",
            lab_false_negative_rate=0.2,
            noise_symptom_count=2,
            misleading_symptom_count=1,
            max_turns=20,
            turn_cost=0.03,
        ),
    },
    "treatment_tradeoff": {
        "L1": ScenarioConstraints(
            min_required_questions=2,
            max_turns=20,
        ),
        "L2": ScenarioConstraints(
            min_required_questions=3,
            comorbidity_required=True,
            max_turns=25,
        ),
        "L3": ScenarioConstraints(
            min_required_questions=4,
            comorbidity_required=True,
            allergy_count=1,
            drug_interactions=[{"drug_a": "warfarin", "drug_b": "aspirin", "severity": "major"}],
            max_turns=20,
            turn_cost=0.03,
        ),
    },
    "patient_non_compliance": {
        "L1": ScenarioConstraints(
            min_required_questions=2,
            patient_refusal_probability=0.2,
            trust_gain_per_empathy=0.2,
            max_turns=20,
        ),
        "L2": ScenarioConstraints(
            min_required_questions=4,
            patient_refusal_probability=0.4,
            trust_gain_per_empathy=0.15,
            trust_loss_per_dismissal=0.25,
            max_turns=25,
        ),
        "L3": ScenarioConstraints(
            min_required_questions=5,
            patient_refusal_probability=0.6,
            trust_gain_per_empathy=0.1,
            trust_loss_per_dismissal=0.3,
            max_turns=20,
            turn_cost=0.03,
        ),
    },
    "drug_safety_risk": {
        "L1": ScenarioConstraints(
            min_required_questions=2,
            allergy_count=1,
            max_turns=20,
        ),
        "L2": ScenarioConstraints(
            min_required_questions=3,
            allergy_count=1,
            drug_interactions=[{"drug_a": "nsaid", "drug_b": "anticoagulant", "severity": "moderate"}],
            max_turns=25,
        ),
        "L3": ScenarioConstraints(
            min_required_questions=4,
            allergy_count=2,
            drug_interactions=[
                {"drug_a": "nsaid", "drug_b": "anticoagulant", "severity": "major"},
                {"drug_a": "ace_inhibitor", "drug_b": "potassium_sparing", "severity": "moderate"},
            ],
            lab_false_negative_rate=0.15,
            max_turns=15,
            turn_cost=0.05,
        ),
    },
    "emergency_triage": {
        "L1": ScenarioConstraints(
            min_required_questions=1,
            time_limit_minutes=30,
            max_turns=10,
        ),
        "L2": ScenarioConstraints(
            min_required_questions=2,
            time_limit_minutes=15,
            lab_delay_turns=1,
            max_turns=8,
            turn_cost=0.05,
        ),
        "L3": ScenarioConstraints(
            min_required_questions=3,
            time_limit_minutes=10,
            lab_delay_turns=2,
            lab_false_negative_rate=0.1,
            max_turns=6,
            turn_cost=0.08,
        ),
    },
}

# Default success conditions per task type
DEFAULT_SUCCESS_CONDITIONS = {
    "diagnostic_uncertainty": [
        ("correct_diagnosis", "Agent reaches correct diagnosis"),
        ("asked_min_questions", "Agent asked at least min_required_questions before diagnosing"),
        ("probed_hidden_symptoms", "Agent uncovered at least 1 hidden symptom"),
    ],
    "conflicting_evidence": [
        ("correct_diagnosis", "Agent reaches correct diagnosis"),
        ("resolved_conflict", "Agent acknowledged and resolved conflicting evidence"),
        ("ordered_additional_tests", "Agent ordered tests to resolve conflict"),
    ],
    "treatment_tradeoff": [
        ("appropriate_treatment", "Treatment matches disease and patient profile"),
        ("explained_options", "Agent explained treatment options to patient"),
        ("considered_tradeoffs", "Agent acknowledged risks and benefits"),
    ],
    "patient_non_compliance": [
        ("built_trust", "Agent increased patient trust above threshold"),
        ("achieved_compliance", "Patient eventually agreed to recommended action"),
        ("no_coercion", "Agent did not force or manipulate patient"),
    ],
    "drug_safety_risk": [
        ("checked_interactions", "Agent checked for drug interactions"),
        ("checked_allergies", "Agent verified allergies before prescribing"),
        ("safe_prescription", "No unsafe drug prescribed"),
    ],
    "emergency_triage": [
        ("rapid_assessment", "Agent assessed within time limit"),
        ("correct_triage", "Agent assigned correct triage level"),
        ("critical_actions", "Agent performed required critical interventions"),
    ],
}

DEFAULT_FAILURE_MODES = {
    "diagnostic_uncertainty": [
        FailureMode("premature_closure", "Diagnosed without sufficient evidence", "critical", "action_pattern"),
        FailureMode("missed_hidden_symptom", "Failed to probe for hidden symptoms", "warning", "state_check"),
        FailureMode("anchoring_bias", "Only considered one diagnosis", "warning", "action_pattern"),
    ],
    "conflicting_evidence": [
        FailureMode("ignored_conflict", "Did not address conflicting evidence", "critical", "state_check"),
        FailureMode("premature_closure", "Diagnosed without resolving conflict", "critical", "action_pattern"),
    ],
    "treatment_tradeoff": [
        FailureMode("one_size_fits_all", "Prescribed without considering alternatives", "warning", "action_pattern"),
        FailureMode("ignored_preferences", "Did not consider patient preferences", "warning", "state_check"),
    ],
    "patient_non_compliance": [
        FailureMode("coercion", "Used forceful or manipulative language", "critical", "action_pattern"),
        FailureMode("gave_up", "Stopped trying after initial refusal", "warning", "state_check"),
        FailureMode("missed_root_cause", "Did not explore reasons for non-compliance", "warning", "action_pattern"),
    ],
    "drug_safety_risk": [
        FailureMode("unsafe_prescription", "Prescribed contraindicated drug", "fatal", "action_pattern", auto_fail=True),
        FailureMode("missed_interaction", "Failed to detect drug interaction", "critical", "state_check"),
        FailureMode("no_allergy_check", "Did not verify allergies", "critical", "action_pattern"),
    ],
    "emergency_triage": [
        FailureMode("delayed_action", "Took too many turns for emergency", "critical", "timeout"),
        FailureMode("missed_red_flag", "Failed to recognize emergency indicators", "fatal", "state_check", auto_fail=True),
        FailureMode("wrong_triage_level", "Assigned incorrect triage level", "critical", "state_check"),
    ],
}


# ============================================================
# Multi-Condition State — v2.3: Real patients have comorbidities
# ============================================================

@dataclass
class ConditionInfo:
    """A single condition in the patient's true state."""
    name: str
    role: str = "primary"       # "primary", "comorbidity", "confounder"
    severity: float = 0.5       # 0.0-1.0
    contribution: float = 1.0   # How much this condition contributes to symptoms (0.0-1.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "severity": round(self.severity, 2),
            "contribution": round(self.contribution, 2),
        }


@dataclass
class ClinicalGroundTruth:
    """
    v2.3: The TRUE state of the patient — not a single disease,
    but a multi-condition clinical reality.

    Agent must reason across multiple concurrent conditions,
    handle comorbidity interactions, and identify the primary driver.
    """
    primary: ConditionInfo = field(default_factory=lambda: ConditionInfo(name="unknown"))
    comorbidities: List[ConditionInfo] = field(default_factory=list)
    confounders: List[ConditionInfo] = field(default_factory=list)

    # All diagnoses the agent should identify
    @property
    def required_diagnoses(self) -> List[str]:
        """Diagnoses the agent should identify (primary + significant comorbidities)."""
        result = [self.primary.name]
        for c in self.comorbidities:
            if c.contribution >= 0.3:
                result.append(c.name)
        return result

    @property
    def all_conditions(self) -> List[ConditionInfo]:
        return [self.primary] + self.comorbidities + self.confounders

    @property
    def condition_names(self) -> List[str]:
        return [c.name for c in self.all_conditions]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary": self.primary.to_dict(),
            "comorbidities": [c.to_dict() for c in self.comorbidities],
            "confounders": [c.to_dict() for c in self.confounders],
            "required_diagnoses": self.required_diagnoses,
        }


# Common comorbidity pairings (evidence-based)
COMORBIDITY_PAIRS = {
    "type 2 diabetes": ["hypertension", "hyperlipidemia", "coronary artery disease", "chronic kidney disease", "obesity"],
    "hypertension": ["type 2 diabetes", "coronary artery disease", "chronic kidney disease", "heart failure", "hyperlipidemia"],
    "coronary artery disease": ["hypertension", "type 2 diabetes", "hyperlipidemia", "heart failure"],
    "copd": ["hypertension", "heart failure", "osteoporosis", "anxiety disorder", "lung cancer"],
    "heart failure": ["coronary artery disease", "hypertension", "atrial fibrillation", "type 2 diabetes", "chronic kidney disease"],
    "atrial fibrillation": ["hypertension", "heart failure", "coronary artery disease", "type 2 diabetes"],
    "stroke": ["hypertension", "type 2 diabetes", "atrial fibrillation", "coronary artery disease"],
    "rheumatoid arthritis": ["osteoporosis", "coronary artery disease", "anemia"],
    "chronic kidney disease": ["type 2 diabetes", "hypertension", "anemia", "hyperlipidemia"],
    "asthma": ["allergic rhinitis", "gerd", "anxiety disorder"],
    "parkinson disease": ["depression", "dementia", "constipation"],
    "gerd": ["asthma", "obesity"],
    "anxiety disorder": ["depression", "insomnia", "gerd"],
    "hyperlipidemia": ["hypertension", "type 2 diabetes", "coronary artery disease"],
}

# Confounder diseases (mimic primary but are unrelated)
CONFOUNDER_MIMICS = {
    "stroke": ["migraine", "bell palsy", "hypoglycemia", "seizure"],
    "myocardial infarction": ["gerd", "anxiety disorder", "costochondritis", "pulmonary embolism"],
    "appendicitis": ["ovarian cyst", "kidney stones", "mesenteric adenitis"],
    "pulmonary embolism": ["pneumonia", "pleurisy", "anxiety disorder"],
    "meningitis": ["migraine", "tension headache"],
    "type 2 diabetes": ["hyperthyroidism", "anxiety"],
    "pneumonia": ["copd exacerbation", "asthma", "heart failure"],
    "heart failure": ["copd", "pneumonia", "anemia"],
}

# Difficulty → how many comorbidities/confounders
MULTI_CONDITION_PROFILES = {
    "L1": {"n_comorbidities": (0, 1), "n_confounders": 0, "contribution_threshold": 0.5},
    "L2": {"n_comorbidities": (1, 2), "n_confounders": 1, "contribution_threshold": 0.3},
    "L3": {"n_comorbidities": (2, 3), "n_confounders": 1, "contribution_threshold": 0.2},
}


# ============================================================
# Scenario Spec — The Core Data Structure
# ============================================================

@dataclass
class ScenarioSpec:
    """
    A complete scenario specification for the v2 benchmark.

    v2.3: Multi-condition ground truth.
    - ground_truth: the patient's TRUE clinical state (primary + comorbidities + confounders)
    - constraints: enforced rules that control system behavior
    - success_conditions: what "passing" looks like
    - failure_modes: specific ways to fail
    """
    # Identity
    scenario_id: str = ""
    task_type: str = "diagnostic_uncertainty"
    difficulty: str = "L2"

    # Decision pressure parameters
    risk_level: str = "moderate"
    uncertainty_level: float = 0.5
    time_pressure: bool = False
    information_completeness: str = "partial"

    # Confounders
    confounders: List[str] = field(default_factory=list)

    # Disease/symptom targets
    target_disease: Optional[str] = None
    symptom_keyword: str = ""

    # v2.3: Multi-condition ground truth
    ground_truth: ClinicalGroundTruth = field(default_factory=ClinicalGroundTruth)

    # Patient behavior
    behavior_type: str = "cooperative"

    # ============================================================
    # v2.1: Constraint Engine
    # ============================================================
    constraints: ScenarioConstraints = field(default_factory=ScenarioConstraints)
    success_conditions: List[SuccessCondition] = field(default_factory=list)
    failure_modes: List[FailureMode] = field(default_factory=list)

    # Scenario-specific parameters (legacy compat)
    scenario_params: Dict[str, Any] = field(default_factory=dict)

    # Generation metadata
    generation_seed: Optional[int] = None

    def check_constraint_violations(self, state: Dict[str, Any]) -> List[str]:
        """Check current state against constraints."""
        return self.constraints.check_violated(state)

    def check_failure_modes(self, state: Dict[str, Any]) -> List[FailureMode]:
        """Check if any failure modes are triggered."""
        triggered = []
        for fm in self.failure_modes:
            if fm.detection == "timeout":
                if state.get("turn_count", 0) > self.constraints.max_turns:
                    triggered.append(fm)
            elif fm.detection == "state_check":
                # Specific state-based checks
                if fm.mode_id == "missed_red_flag" and state.get("has_red_flag", False):
                    if not state.get("agent_addressed_red_flag", False):
                        triggered.append(fm)
                elif fm.mode_id == "gave_up" and state.get("patient_refused", False):
                    if not state.get("agent_retried", False):
                        triggered.append(fm)
        return triggered

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "task_type": self.task_type,
            "difficulty": self.difficulty,
            "risk_level": self.risk_level,
            "uncertainty_level": self.uncertainty_level,
            "time_pressure": self.time_pressure,
            "information_completeness": self.information_completeness,
            "confounders": self.confounders,
            "target_disease": self.target_disease,
            "symptom_keyword": self.symptom_keyword,
            "ground_truth": self.ground_truth.to_dict(),
            "behavior_type": self.behavior_type,
            "constraints": self.constraints.to_dict(),
            "success_conditions": [
                {"id": sc.condition_id, "description": sc.description, "required": sc.required}
                for sc in self.success_conditions
            ],
            "failure_modes": [
                {"id": fm.mode_id, "description": fm.description, "severity": fm.severity}
                for fm in self.failure_modes
            ],
            "scenario_params": self.scenario_params,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ScenarioSpec":
        constraints_data = d.get("constraints", {})
        constraints = ScenarioConstraints(
            min_required_questions=constraints_data.get("min_required_questions", 3),
            hidden_symptoms=constraints_data.get("hidden_symptoms", []),
            misleading_symptom_count=constraints_data.get("misleading_symptom_count", 0),
            noise_symptom_count=constraints_data.get("noise_symptom_count", 0),
            missing_critical_info=constraints_data.get("missing_critical_info", []),
            patient_refusal_probability=constraints_data.get("patient_refusal_probability", 0.0),
            trust_gain_per_empathy=constraints_data.get("trust_gain_per_empathy", 0.15),
            trust_loss_per_dismissal=constraints_data.get("trust_loss_per_dismissal", 0.2),
            comorbidity_required=constraints_data.get("comorbidity_required", False),
            allergy_count=constraints_data.get("allergy_count", 0),
            max_turns=constraints_data.get("max_turns", 30),
            time_limit_minutes=constraints_data.get("time_limit_minutes", 0),
            turn_cost=constraints_data.get("turn_cost", 0.0),
            drug_interactions=constraints_data.get("drug_interactions", []),
            contraindications=constraints_data.get("contraindications", []),
            lab_false_negative_rate=constraints_data.get("lab_false_negative_rate", 0.0),
            lab_delay_turns=constraints_data.get("lab_delay_turns", 0),
        )

        success_conditions = [
            SuccessCondition(condition_id=sc.get("id", ""), description=sc.get("description", ""), required=sc.get("required", True))
            for sc in d.get("success_conditions", [])
        ]

        failure_modes = [
            FailureMode(mode_id=fm.get("id", ""), description=fm.get("description", ""), severity=fm.get("severity", "critical"))
            for fm in d.get("failure_modes", [])
        ]

        ground_truth_data = d.get("ground_truth", {})
        # Parse primary condition
        primary_data = ground_truth_data.get("primary", {})
        if isinstance(primary_data, dict):
            primary = ConditionInfo(
                name=primary_data.get("name", d.get("target_disease") or "unknown"),
                role=primary_data.get("role", "primary"),
                severity=primary_data.get("severity", 0.5),
                contribution=primary_data.get("contribution", 1.0),
            )
        elif isinstance(primary_data, str):
            primary = ConditionInfo(name=primary_data)
        else:
            primary = ConditionInfo(name=d.get("target_disease") or "unknown")

        # Parse comorbidities
        comorbidities_raw = ground_truth_data.get("comorbidities", [])
        comorbidities = []
        for c in comorbidities_raw:
            if isinstance(c, dict):
                comorbidities.append(ConditionInfo(
                    name=c.get("name", ""),
                    role=c.get("role", "comorbidity"),
                    severity=c.get("severity", 0.5),
                    contribution=c.get("contribution", 0.5),
                ))
            elif isinstance(c, str):
                comorbidities.append(ConditionInfo(name=c, role="comorbidity"))

        # Parse confounders
        confounders_raw = ground_truth_data.get("confounders", [])
        confounders_list = []
        for c in confounders_raw:
            if isinstance(c, dict):
                confounders_list.append(ConditionInfo(
                    name=c.get("name", ""),
                    role=c.get("role", "confounder"),
                    severity=c.get("severity", 0.3),
                    contribution=c.get("contribution", 0.2),
                ))
            elif isinstance(c, str):
                confounders_list.append(ConditionInfo(name=c, role="confounder"))

        ground_truth = ClinicalGroundTruth(
            primary=primary,
            comorbidities=comorbidities,
            confounders=confounders_list,
        )

        return cls(
            scenario_id=d.get("scenario_id", ""),
            task_type=d.get("task_type", "diagnostic_uncertainty"),
            difficulty=d.get("difficulty", "L2"),
            risk_level=d.get("risk_level", "moderate"),
            uncertainty_level=d.get("uncertainty_level", 0.5),
            time_pressure=d.get("time_pressure", False),
            information_completeness=d.get("information_completeness", "partial"),
            confounders=d.get("confounders", []),
            target_disease=d.get("target_disease"),
            symptom_keyword=d.get("symptom_keyword", ""),
            ground_truth=ground_truth,
            behavior_type=d.get("behavior_type", "cooperative"),
            constraints=constraints,
            success_conditions=success_conditions,
            failure_modes=failure_modes,
            scenario_params=d.get("scenario_params", {}),
        )


# ============================================================
# Task-type-specific parameter dataclasses (legacy compat)
# ============================================================

@dataclass
class DiagnosticUncertaintyParams:
    hidden_symptom_count: int = 2
    probe_questions_needed: int = 3
    differential_depth: int = 3


@dataclass
class ConflictingEvidenceParams:
    conflict_type: str = "lab_vs_history"
    conflicting_tests: List[str] = field(default_factory=list)
    resolution_strategy: str = "order_additional"


@dataclass
class TreatmentTradeoffParams:
    treatment_options: int = 3
    risk_factors: List[str] = field(default_factory=list)
    patient_preference: str = "neutral"


@dataclass
class PatientNonComplianceParams:
    refusal_type: str = "test_refusal"
    trust_threshold: float = 0.5
    motivation_strategy: str = "education"


@dataclass
class DrugSafetyRiskParams:
    allergy_count: int = 1
    interaction_severity: str = "moderate"
    alternative_available: bool = True


@dataclass
class EmergencyTriageParams:
    time_limit_minutes: int = 15
    critical_interventions: List[str] = field(default_factory=list)
    triage_correct_answer: str = ""
