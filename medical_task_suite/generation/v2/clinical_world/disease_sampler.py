#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Disease Sampler — Sample disease from KB/KG matching scenario constraints.

v2.7: Uses PrimeKGDiseaseIndex for expanded disease pool and data-driven
fitness scoring. Falls back to ClinicalKnowledgeBase-only mode when
PrimeKG is not available.

Unlike v1 which uses PrimeKG random walks to discover diseases,
v2 starts from the scenario type and selects diseases that create
the right kind of decision pressure.
"""

import random
from typing import Dict, List, Optional, Set

from ..scenario_engine.scenario_schema import ScenarioSpec, TASK_TYPES


# Scenario-type → disease fitness criteria (used as fallback when no PrimeKG)
SCENARIO_FITNESS = {
    "diagnostic_uncertainty": {
        "prefer_comorbidities": True,
        "min_differentials": 2,
        "prefer_atypical": True,
    },
    "conflicting_evidence": {
        "prefer_lab_overlap": True,
        "min_lab_tests": 3,
    },
    "treatment_tradeoff": {
        "min_medications": 2,
        "prefer_contraindications": True,
    },
    "patient_non_compliance": {
        "prefer_chronic": True,
        "prefer_lifestyle_component": True,
    },
    "drug_safety_risk": {
        "min_medications": 2,
        "prefer_interactions": True,
        "prefer_allergies": True,
    },
    "emergency_triage": {
        "min_severity": 0.3,
        "prefer_time_sensitive": True,
    },
}

# Chronic diseases suitable for non-compliance scenarios
CHRONIC_DISEASES = {
    "type 2 diabetes", "hypertension", "copd", "asthma",
    "heart failure", "coronary artery disease", "chronic kidney disease",
    "rheumatoid arthritis", "osteoarthritis", "hyperlipidemia",
    "parkinson disease", "epilepsy", "bipolar disorder", "anxiety disorder",
    "depression", "hypothyroidism", "gout", "osteoporosis",
    "psoriasis", "irritable bowel syndrome", "glaucoma",
}

# Diseases with lifestyle modification components
LIFESTYLE_DISEASES = {
    "type 2 diabetes", "hypertension", "hyperlipidemia", "copd",
    "obesity", "gerd", "sleep apnea", "ibs",
    "fatty liver disease", "metabolic syndrome",
}


class DiseaseSampler:
    """Sample diseases that create the right decision pressure for a scenario.

    v2.7: Uses PrimeKGDiseaseIndex for expanded pool and data-driven fitness.
    """

    def __init__(self, clinical_kb, primekg=None):
        self.kb = clinical_kb
        self.primekg = primekg
        self._primekg_index = None

    def _ensure_primekg_index(self):
        """Lazy-load PrimeKG disease index."""
        if self._primekg_index is not None:
            return self._primekg_index is not False

        if self.primekg is not None:
            try:
                from .primekg_bridge import PrimeKGBridge
                from .primekg_disease_profile import PrimeKGDiseaseIndex

                # primekg might be (nodes, edges) tuple or loader object
                if isinstance(self.primekg, tuple) and len(self.primekg) == 2:
                    nodes, edges = self.primekg
                else:
                    # Try loading from loader object
                    try:
                        nodes = self.primekg.nodes
                        edges = self.primekg.edges
                    except AttributeError:
                        self._primekg_index = False
                        return False

                bridge = PrimeKGBridge(nodes, edges, self.kb)
                self._primekg_index = PrimeKGDiseaseIndex(bridge)
                return True
            except Exception:
                self._primekg_index = False
                return False

        self._primekg_index = False
        return False

    def sample(self, scenario: ScenarioSpec) -> Optional[str]:
        """
        Sample a disease that fits the scenario constraints.
        If scenario.target_disease is set, return it directly.
        """
        if scenario.target_disease:
            return scenario.target_disease
        return self._sample_for_task_type(scenario.task_type, scenario.difficulty)

    def _sample_for_task_type(
        self, task_type: str, difficulty: str
    ) -> Optional[str]:
        """Sample disease weighted by fitness for the task type."""
        has_primekg = self._ensure_primekg_index()

        # Build expanded disease pool
        kb_diseases = self.kb.get_covered_diseases()

        if has_primekg:
            scored = self._score_with_primekg(kb_diseases, task_type, difficulty)
        else:
            scored = self._score_with_kb(kb_diseases, task_type, difficulty)

        if not scored:
            # Final fallback: random from KB
            if kb_diseases:
                return random.choice(kb_diseases)
            return None

        # Weighted random selection
        total = sum(s for _, s in scored)
        r = random.uniform(0, total)
        cumulative = 0
        for disease, score in scored:
            cumulative += score
            if r <= cumulative:
                return disease

        return scored[-1][0]

    def _score_with_primekg(
        self, kb_diseases: List[str], task_type: str, difficulty: str
    ) -> List[tuple]:
        """Score diseases using PrimeKG data."""
        index = self._primekg_index

        # Get PrimeKG diseases suitable for this task type
        primekg_candidates = index.get_diseases_for_task_type(task_type, min_fitness=0.2)

        # Combine: KB diseases get a quality bonus, PrimeKG diseases add diversity
        scored = []
        kb_set = {d.lower() for d in kb_diseases}

        # KB diseases: base score + primekg fitness + quality bonus
        for disease in kb_diseases:
            score = 1.0  # Base quality bonus for KB diseases
            profile = index.get_profile(disease)
            if profile:
                score += profile.fitness_scores.get(task_type, 0.0) * 2.0
            else:
                # KB disease without PrimeKG data — use legacy scoring
                fitness = SCENARIO_FITNESS.get(task_type, {})
                score += self._compute_legacy_fitness(disease, task_type, fitness, difficulty) * 0.5
            scored.append((disease, score))

        # PrimeKG-only diseases: fitness score only (no quality bonus)
        for disease, fitness in primekg_candidates:
            if disease.lower() not in kb_set:
                # Only include if disease has enough data
                profile = index.get_profile(disease)
                if profile and profile.is_useful:
                    scored.append((disease, fitness * 0.5))  # Lower weight than KB diseases

        # Difficulty scaling
        scored = [(d, self._apply_difficulty_scaling(d, s, difficulty))
                  for d, s in scored]

        # Filter out zero scores
        scored = [(d, s) for d, s in scored if s > 0]

        return scored

    def _score_with_kb(
        self, kb_diseases: List[str], task_type: str, difficulty: str
    ) -> List[tuple]:
        """Legacy scoring using only ClinicalKnowledgeBase."""
        fitness = SCENARIO_FITNESS.get(task_type, {})
        scored = []
        for disease in kb_diseases:
            score = self._compute_legacy_fitness(disease, task_type, fitness, difficulty)
            if score > 0:
                scored.append((disease, score))
        return scored

    def _compute_legacy_fitness(
        self, disease: str, task_type: str, fitness: dict, difficulty: str
    ) -> float:
        """Original fitness computation from KB data."""
        profile = self.kb.get_disease_profile(disease)
        score = 1.0

        meds = self.kb.get_medications_for_condition(disease)
        n_meds = len(meds) if meds else 0

        if task_type == "treatment_tradeoff":
            if n_meds < fitness.get("min_medications", 2):
                return 0
            score += n_meds * 0.5

        elif task_type == "drug_safety_risk":
            if n_meds < fitness.get("min_medications", 2):
                return 0
            score += n_meds * 0.3
            for med in meds[:3]:
                if isinstance(med, dict):
                    ci = med.get("contraindications", [])
                    if ci:
                        score += 0.5

        elif task_type == "diagnostic_uncertainty":
            diffs = self.kb.get_differential_diagnoses(disease)
            n_diffs = len(diffs) if diffs else 0
            if n_diffs < fitness.get("min_differentials", 2):
                score *= 0.3
            else:
                score += n_diffs * 0.3
            comorbs = self.kb.get_comorbidities(disease)
            if comorbs and len(comorbs) >= 2:
                score += 0.5

        elif task_type == "conflicting_evidence":
            lab_panel = self.kb.get_lab_panel(disease)
            n_labs = len(lab_panel) if lab_panel else 0
            if n_labs < fitness.get("min_lab_tests", 3):
                score *= 0.5
            else:
                score += n_labs * 0.2

        elif task_type == "patient_non_compliance":
            if disease.lower() in CHRONIC_DISEASES:
                score += 1.0
            if disease.lower() in LIFESTYLE_DISEASES:
                score += 0.5

        elif task_type == "emergency_triage":
            sev = self._get_flat_severity(profile)
            severe_prob = sev.get("severe", 0)
            if severe_prob < fitness.get("min_severity", 0.3):
                score *= 0.5
            else:
                score += severe_prob * 2

        if difficulty == "L3":
            comorbs = self.kb.get_comorbidities(disease)
            n_comorbs = len(comorbs) if comorbs else 0
            score += n_comorbs * 0.2

        return score

    def _apply_difficulty_scaling(
        self, disease: str, score: float, difficulty: str
    ) -> float:
        """Scale score based on difficulty level."""
        if difficulty == "L1":
            # Prefer simpler diseases
            if disease.lower() in CHRONIC_DISEASES:
                return score * 0.7  # Less likely for L1
            return score

        elif difficulty == "L3":
            # Prefer complex diseases
            comorbs = self.kb.get_comorbidities(disease)
            n_comorbs = len(comorbs) if comorbs else 0
            score += n_comorbs * 0.2

            # PrimeKG complexity bonus
            if self._primekg_index and self._primekg_index is not False:
                profile = self._primekg_index.get_profile(disease)
                if profile:
                    score += profile.complexity_score * 0.3

            return score

        return score

    def _get_flat_severity(self, profile) -> Dict[str, float]:
        """Get flat severity distribution, handling nested structures."""
        sev = {}
        if hasattr(profile, 'severity_distribution'):
            sev = profile.severity_distribution or {}
        first_val = next(iter(sev.values()), None) if sev else None
        if isinstance(first_val, dict):
            return sev.get("L2", sev.get("L1", {"moderate": 1.0}))
        return sev

    def get_compatible_diseases(self, task_type: str) -> List[str]:
        """Get list of diseases compatible with a task type."""
        has_primekg = self._ensure_primekg_index()
        kb_diseases = self.kb.get_covered_diseases()

        if has_primekg:
            scored = self._score_with_primekg(kb_diseases, task_type, "L2")
        else:
            scored = self._score_with_kb(kb_diseases, task_type, "L2")

        scored.sort(key=lambda x: x[1], reverse=True)
        return [d for d, _ in scored]
