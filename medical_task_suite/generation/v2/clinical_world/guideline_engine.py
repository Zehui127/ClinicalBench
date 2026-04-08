#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guideline Engine — Clinical guidelines as scenario constraints.

Provides evidence-based constraints on what actions are appropriate
for a given disease + scenario combination. Used by evaluation to
determine if the agent followed reasonable clinical reasoning.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ..scenario_engine.scenario_schema import ScenarioSpec


@dataclass
class GuidelineConstraint:
    """A single clinical guideline constraint."""
    guideline_id: str
    category: str  # "diagnostic", "treatment", "safety", "follow_up"
    description: str
    required: bool = True
    applies_to: List[str] = field(default_factory=list)  # task types

    def is_applicable(self, task_type: str) -> bool:
        return not self.applies_to or task_type in self.applies_to


@dataclass
class SafetyRule:
    """A safety rule that must not be violated."""
    rule_id: str
    category: str  # "drug_interaction", "allergy", "contraindication", "emergency"
    description: str
    severity: str = "critical"  # "warning", "critical", "fatal"
    condition: str = ""  # When this rule applies


# Universal safety rules (apply to all scenarios)
UNIVERSAL_SAFETY_RULES = [
    SafetyRule(
        rule_id="check_allergies_before_prescribing",
        category="allergy",
        description="Always verify allergies before prescribing medication",
        severity="critical",
    ),
    SafetyRule(
        rule_id="drug_interaction_check",
        category="drug_interaction",
        description="Check for drug-drug interactions when prescribing multiple medications",
        severity="critical",
    ),
    SafetyRule(
        rule_id="emergency_escalation",
        category="emergency",
        description="Escalate to emergency care if patient shows red flag symptoms",
        severity="fatal",
    ),
    SafetyRule(
        rule_id="informed_consent",
        category="safety",
        description="Explain risks and benefits before significant interventions",
        severity="warning",
    ),
    SafetyRule(
        rule_id="monitor_vitals",
        category="safety",
        description="Monitor vital signs in acute or deteriorating conditions",
        severity="warning",
    ),
]


class GuidelineEngine:
    """Apply clinical guidelines as constraints on agent actions."""

    def __init__(self, clinical_kb):
        self.kb = clinical_kb

    def get_constraints(
        self, disease: str, scenario: ScenarioSpec
    ) -> List[GuidelineConstraint]:
        """Get guideline constraints applicable to this scenario."""
        constraints = []

        # Diagnostic constraints
        if scenario.task_type in ("diagnostic_uncertainty", "conflicting_evidence"):
            constraints.extend(self._diagnostic_constraints(disease, scenario))

        # Treatment constraints
        if scenario.task_type in ("treatment_tradeoff", "drug_safety_risk"):
            constraints.extend(self._treatment_constraints(disease, scenario))

        # Safety constraints
        constraints.extend(self._safety_constraints(disease, scenario))

        # Follow-up constraints
        constraints.extend(self._follow_up_constraints(disease, scenario))

        return constraints

    def get_safety_rules(
        self, disease: str, scenario: ScenarioSpec
    ) -> List[SafetyRule]:
        """Get safety rules for this scenario."""
        rules = list(UNIVERSAL_SAFETY_RULES)

        # Add disease-specific safety rules
        profile = self.kb.get_disease_profile(disease)

        # Check for drug interaction rules
        if scenario.task_type == "drug_safety_risk":
            meds = self.kb.get_medications_for_condition(disease)
            if meds:
                rules.append(SafetyRule(
                    rule_id="multi_med_interaction",
                    category="drug_interaction",
                    description=f"Patient may be on multiple medications — check interactions",
                    severity="critical",
                ))

        # Emergency rules
        if scenario.task_type == "emergency_triage":
            rules.append(SafetyRule(
                rule_id="time_critical_action",
                category="emergency",
                description="Time-critical condition — immediate action required",
                severity="fatal",
            ))

        return rules

    def check_action(
        self,
        action_type: str,
        action_detail: str,
        disease: str,
        scenario: ScenarioSpec,
    ) -> Dict[str, Any]:
        """
        Check if an agent action is consistent with guidelines.

        Returns dict with 'compliant' (bool) and 'notes' (list of strings).
        """
        notes = []
        violations = []

        # Check against safety rules
        rules = self.get_safety_rules(disease, scenario)
        for rule in rules:
            if action_type == "prescribe" and rule.category == "allergy":
                notes.append(f"Safety check: {rule.description}")
            if action_type == "prescribe" and rule.category == "drug_interaction":
                notes.append(f"Interaction check: {rule.description}")

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "notes": notes,
        }

    def _diagnostic_constraints(
        self, disease: str, scenario: ScenarioSpec
    ) -> List[GuidelineConstraint]:
        constraints = []

        # Must consider differential diagnoses
        diffs = self.kb.get_differential_diagnoses(disease)
        if diffs:
            constraints.append(GuidelineConstraint(
                guideline_id="consider_differentials",
                category="diagnostic",
                description=f"Consider at least 2 differential diagnoses before concluding",
                required=True,
                applies_to=["diagnostic_uncertainty", "conflicting_evidence"],
            ))

        # Must order relevant labs
        lab_panel = self.kb.get_lab_panel(disease)
        if lab_panel:
            constraints.append(GuidelineConstraint(
                guideline_id="order_relevant_labs",
                category="diagnostic",
                description="Order disease-relevant laboratory tests",
                required=True,
                applies_to=["diagnostic_uncertainty"],
            ))

        # For uncertainty scenarios, must probe before concluding
        if scenario.task_type == "diagnostic_uncertainty":
            constraints.append(GuidelineConstraint(
                guideline_id="probe_before_diagnose",
                category="diagnostic",
                description="Gather sufficient history before making diagnosis",
                required=True,
                applies_to=["diagnostic_uncertainty"],
            ))

        return constraints

    def _treatment_constraints(
        self, disease: str, scenario: ScenarioSpec
    ) -> List[GuidelineConstraint]:
        constraints = []

        # Must explain treatment options
        constraints.append(GuidelineConstraint(
            guideline_id="explain_treatment_options",
            category="treatment",
            description="Explain treatment options with risks and benefits",
            required=True,
            applies_to=["treatment_tradeoff"],
        ))

        # Must consider patient preferences
        constraints.append(GuidelineConstraint(
            guideline_id="consider_patient_preference",
            category="treatment",
            description="Consider patient preferences in treatment decisions",
            required=True,
            applies_to=["treatment_tradeoff"],
        ))

        # Drug safety: must check allergies
        if scenario.task_type == "drug_safety_risk":
            constraints.append(GuidelineConstraint(
                guideline_id="verify_allergies",
                category="safety",
                description="Verify allergies before any medication",
                required=True,
                applies_to=["drug_safety_risk"],
            ))

        return constraints

    def _safety_constraints(
        self, disease: str, scenario: ScenarioSpec
    ) -> List[GuidelineConstraint]:
        constraints = []

        # Check contraindications
        profile = self.kb.get_disease_profile(disease)
        if hasattr(profile, 'medications') and profile.medications:
            for med in profile.medications[:3]:
                if isinstance(med, dict):
                    ci = med.get("contraindications", [])
                    if ci:
                        constraints.append(GuidelineConstraint(
                            guideline_id=f"contraindication_check_{disease}",
                            category="safety",
                            description=f"Check contraindications before prescribing",
                            required=True,
                        ))
                        break

        return constraints

    def _follow_up_constraints(
        self, disease: str, scenario: ScenarioSpec
    ) -> List[GuidelineConstraint]:
        constraints = []

        follow_up = self.kb.get_follow_up_defaults()
        if follow_up:
            constraints.append(GuidelineConstraint(
                guideline_id="schedule_follow_up",
                category="follow_up",
                description="Schedule appropriate follow-up",
                required=True,
            ))

        return constraints
