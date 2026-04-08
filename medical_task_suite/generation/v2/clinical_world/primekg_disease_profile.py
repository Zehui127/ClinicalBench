#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrimeKG Disease Profile — Lightweight disease metadata from PrimeKG edges.

Provides disease fitness data for DiseaseSampler to use when selecting
diseases that match scenario constraints. Supplements ClinicalKnowledgeBase
with PrimeKG-derived metadata (symptom counts, drug counts, overlaps).
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class PrimeKGDiseaseProfile:
    """Minimal disease profile derived from PrimeKG edges."""
    name: str
    source: str = "primekg"          # "primekg" or "clinical_kb"

    # Symptom data
    symptom_count: int = 0
    symptoms: List[str] = field(default_factory=list)
    negative_symptoms: List[str] = field(default_factory=list)  # "phenotype absent"

    # Drug data
    drug_count: int = 0
    drugs: List[str] = field(default_factory=list)

    # Contraindication data
    contraindication_count: int = 0

    # Overlap with other diseases (Jaccard similarity)
    overlap_diseases: Dict[str, float] = field(default_factory=dict)

    # Derived fitness scores per task type
    fitness_scores: Dict[str, float] = field(default_factory=dict)

    @property
    def is_useful(self) -> bool:
        """Disease has enough data to be used in scenarios."""
        return self.symptom_count >= 3 or self.drug_count >= 2

    @property
    def complexity_score(self) -> float:
        """How complex this disease is for scenario generation."""
        overlap_score = min(1.0, len(self.overlap_diseases) / 10)
        drug_score = min(1.0, self.drug_count / 10)
        symptom_score = min(1.0, self.symptom_count / 20)
        return (overlap_score + drug_score + symptom_score) / 3


class PrimeKGDiseaseIndex:
    """
    Index of PrimeKG diseases with computed fitness metadata.

    Used by DiseaseSampler to expand the disease pool beyond the
    49 diseases in ClinicalKnowledgeBase.

    Usage:
        bridge = PrimeKGBridge(nodes, edges, kb)
        index = PrimeKGDiseaseIndex(bridge)
        profile = index.get_profile("asthma")
        suitable = index.get_diseases_for_task_type("drug_safety_risk")
    """

    def __init__(self, bridge):
        """
        Args:
            bridge: PrimeKGBridge instance with loaded data
        """
        self.bridge = bridge
        self._profiles: Dict[str, PrimeKGDiseaseProfile] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Build disease profiles from PrimeKG bridge data."""
        symptom_map = self.bridge.get_disease_symptom_map()
        drug_map = self.bridge.get_disease_drug_map()
        contra_map = self.bridge.get_drug_contraindication_map()

        # Get KB diseases for marking source
        kb_diseases: Set[str] = set()
        if self.bridge.kb:
            kb_diseases = {d.lower() for d in self.bridge.kb.get_covered_diseases()}

        # Build profiles for all diseases with data
        all_diseases = set(list(symptom_map.keys()) + list(drug_map.keys()))

        for disease in all_diseases:
            symptoms = symptom_map.get(disease, [])
            positive = [s for s in symptoms if not s.startswith("!")]
            negative = [s[1:] for s in symptoms if s.startswith("!")]
            drugs = drug_map.get(disease, [])

            # Count contraindications for this disease's drugs
            contra_count = 0
            for drug in drugs:
                contra_count += len(contra_map.get(drug, []))

            source = "clinical_kb" if disease in kb_diseases else "primekg"

            self._profiles[disease] = PrimeKGDiseaseProfile(
                name=disease,
                source=source,
                symptom_count=len(positive),
                symptoms=positive,
                negative_symptoms=negative,
                drug_count=len(set(drugs)),
                drugs=list(set(drugs)),
                contraindication_count=contra_count,
            )

        # Compute symptom overlaps for useful diseases
        self._compute_overlaps()

        # Pre-compute fitness scores per task type
        self._compute_fitness_scores()

    def _compute_overlaps(self) -> None:
        """Compute Jaccard similarity between disease symptom sets."""
        # Only compute for diseases with enough symptoms
        candidates = {
            d: set(p.symptoms)
            for d, p in self._profiles.items()
            if p.symptom_count >= 3
        }

        for disease, symptom_set in candidates.items():
            profile = self._profiles[disease]
            overlaps: Dict[str, float] = {}

            for other, other_set in candidates.items():
                if disease == other:
                    continue
                if len(other_set) < 3:
                    continue

                intersection = len(symptom_set & other_set)
                union = len(symptom_set | other_set)
                if union == 0:
                    continue
                jaccard = intersection / union

                if jaccard >= 0.15:  # Only store meaningful overlaps
                    overlaps[other] = round(jaccard, 3)

            # Keep top 20 overlaps
            profile.overlap_diseases = dict(
                sorted(overlaps.items(), key=lambda x: -x[1])[:20]
            )

    def _compute_fitness_scores(self) -> None:
        """Pre-compute fitness scores for each task type."""
        for disease, profile in self._profiles.items():
            scores = {}

            # diagnostic_uncertainty: wants symptom overlap (confusion potential)
            n_high_overlap = sum(
                1 for v in profile.overlap_diseases.values() if v > 0.2
            )
            scores["diagnostic_uncertainty"] = min(1.0, n_high_overlap * 0.15 + profile.symptom_count * 0.02)

            # conflicting_evidence: wants many symptoms + drugs
            scores["conflicting_evidence"] = min(1.0, (
                profile.symptom_count * 0.02 +
                profile.drug_count * 0.05 +
                len(profile.negative_symptoms) * 0.1
            ))

            # treatment_tradeoff: wants multiple drug options
            scores["treatment_tradeoff"] = (
                min(1.0, profile.drug_count / 5) * 0.7 +
                min(1.0, profile.contraindication_count / 20) * 0.3
            )

            # drug_safety_risk: wants contraindications
            scores["drug_safety_risk"] = (
                min(1.0, profile.contraindication_count / 30) * 0.5 +
                min(1.0, profile.drug_count / 5) * 0.3 +
                min(1.0, len(profile.negative_symptoms) / 5) * 0.2
            )

            # patient_non_compliance: wants chronic diseases with drugs
            scores["patient_non_compliance"] = (
                min(1.0, profile.drug_count / 3) * 0.5 +
                min(1.0, profile.symptom_count / 10) * 0.3 +
                (0.2 if profile.source == "clinical_kb" else 0.0)
            )

            # emergency_triage: wants many symptoms (severity potential)
            scores["emergency_triage"] = (
                min(1.0, profile.symptom_count / 15) * 0.6 +
                min(1.0, n_high_overlap * 0.1) * 0.4
            )

            profile.fitness_scores = scores

    # ================================================================
    # Public API
    # ================================================================

    def get_profile(self, disease_name: str) -> Optional[PrimeKGDiseaseProfile]:
        """Get profile for a specific disease."""
        return self._profiles.get(disease_name.lower())

    def get_diseases_with_drugs(self, min_drugs: int = 2) -> List[str]:
        """Get diseases that have at least min_drugs drug options."""
        return [
            d for d, p in self._profiles.items()
            if p.drug_count >= min_drugs
        ]

    def get_diseases_with_symptoms(self, min_symptoms: int = 5) -> List[str]:
        """Get diseases that have at least min_symptoms symptoms."""
        return [
            d for d, p in self._profiles.items()
            if p.symptom_count >= min_symptoms
        ]

    def get_diseases_for_task_type(
        self, task_type: str, min_fitness: float = 0.3
    ) -> List[tuple]:
        """
        Get diseases suitable for a task type, sorted by fitness.

        Returns:
            [(disease_name, fitness_score), ...]
        """
        results = []
        for disease, profile in self._profiles.items():
            score = profile.fitness_scores.get(task_type, 0.0)
            if score >= min_fitness:
                results.append((disease, score))

        results.sort(key=lambda x: -x[1])
        return results

    def get_useful_diseases(self) -> List[str]:
        """Get all diseases with enough data to be useful in scenarios."""
        return [d for d, p in self._profiles.items() if p.is_useful]

    def get_symptom_overlap(self, disease_a: str, disease_b: str) -> float:
        """Get Jaccard similarity between two diseases' symptoms."""
        pa = self._profiles.get(disease_a.lower())
        if pa:
            return pa.overlap_diseases.get(disease_b.lower(), 0.0)
        return 0.0

    def get_statistics(self) -> Dict[str, int]:
        """Get index statistics."""
        kb_count = sum(1 for p in self._profiles.values() if p.source == "clinical_kb")
        return {
            "total_diseases": len(self._profiles),
            "kb_diseases": kb_count,
            "primekg_only_diseases": len(self._profiles) - kb_count,
            "useful_diseases": len(self.get_useful_diseases()),
            "diseases_with_drugs": len(self.get_diseases_with_drugs()),
            "diseases_with_symptoms": len(self.get_diseases_with_symptoms()),
        }
