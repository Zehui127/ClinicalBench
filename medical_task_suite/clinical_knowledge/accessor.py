#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clinical Knowledge Base Accessor

Loads clinical data from JSON files and provides typed access methods.
Single source of truth for disease profiles, drug data, lab references,
triage rules, and clinical questions.

Usage:
    from clinical_knowledge import ClinicalKnowledgeBase
    kb = ClinicalKnowledgeBase.get_instance()
    profile = kb.get_disease_profile("type 2 diabetes")
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class DiseaseProfile:
    """Structured disease information loaded from JSON."""
    name: str
    coverage_level: str  # "full", "partial", "generic"

    aliases: List[str] = field(default_factory=list)
    typical_age_range: Tuple[int, int] = (25, 75)
    comorbidities: Dict[str, float] = field(default_factory=dict)
    medications: List[Dict[str, Any]] = field(default_factory=list)
    differential_diagnoses: List[str] = field(default_factory=list)
    differential_questions: List[str] = field(default_factory=list)
    patient_education: str = ""
    vital_sign_modifiers: Dict[str, Any] = field(default_factory=dict)
    social_history_relevance: Dict[str, bool] = field(default_factory=dict)
    severity_distribution: Dict[str, float] = field(default_factory=dict)

    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_deep_coverage(self) -> bool:
        return self.coverage_level == "full" and bool(self.medications)


@dataclass
class DrugInfo:
    """Structured drug information loaded from JSON."""
    generic_name: str
    brand_names: List[str] = field(default_factory=list)
    drug_class: str = ""
    standard_doses: List[Dict[str, str]] = field(default_factory=list)
    contraindications: List[str] = field(default_factory=list)
    interaction_class: str = ""
    alternatives: List[Dict[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Generic fallback profiles
# ---------------------------------------------------------------------------

_GENERIC_DISEASE = {
    "aliases": [],
    "typical_age_range": [25, 75],
    "comorbidities": {},
    "medications": [],
    "differential_diagnoses": [],
    "differential_questions": [],
    "patient_education": "",
    "vital_sign_modifiers": {},
    "social_history_relevance": {"smoking": False, "alcohol": False},
    "severity_distribution": {"mild": 0.3, "moderate": 0.5, "severe": 0.2},
}


# ---------------------------------------------------------------------------
# Accessor
# ---------------------------------------------------------------------------


class ClinicalKnowledgeBase:
    """
    Single accessor for all clinical knowledge data.

    Loads JSON files once on first instantiation, then serves cached data.
    Thread-safe singleton pattern.
    """

    _instance: Optional["ClinicalKnowledgeBase"] = None

    # ------------------------------------------------------------------ init

    @classmethod
    def get_instance(cls, data_dir: Optional[str] = None) -> "ClinicalKnowledgeBase":
        if cls._instance is None:
            cls._instance = cls(data_dir=data_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """For testing — clear the singleton."""
        cls._instance = None

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = str(Path(__file__).parent / "data")
        self._data_dir = Path(data_dir)

        # Load all JSON files (silently skip missing ones)
        self._diseases: Dict[str, Dict] = self._load("disease_profiles.json", {}).get("diseases", {})
        self._drugs: Dict[str, Dict] = self._load("drug_database.json", {})
        self._lab: Dict[str, Any] = self._load("lab_reference.json", {})
        self._triage: Dict[str, Any] = self._load("triage_rules.json", {})
        self._tools: Dict[str, Any] = self._load("tool_registry.json", {})
        self._questions: Dict[str, Any] = self._load("clinical_questions.json", {})

        # Build alias index for fast lookup
        self._disease_alias_index: Dict[str, str] = {}
        for key, profile in self._diseases.items():
            self._disease_alias_index[key.lower()] = key
            for alias in profile.get("aliases", []):
                self._disease_alias_index[alias.lower()] = key

    # --------------------------------------------------------------- helpers

    def _load(self, filename: str, default: Any) -> Any:
        path = self._data_dir / filename
        if not path.exists():
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _match_disease_key(self, disease_name: str) -> Optional[str]:
        """Three-tier disease name lookup."""
        lower = disease_name.lower().strip()

        # Tier 1: exact / alias
        if lower in self._disease_alias_index:
            return self._disease_alias_index[lower]

        # Tier 2: substring
        for key in self._diseases:
            if key in lower or lower in key:
                return key

        # Tier 3: word overlap (check if significant words match)
        query_words = set(lower.split()) - {"disease", "syndrome", "disorder", "type", "chronic", "acute"}
        best_key = None
        best_overlap = 0
        for key in self._diseases:
            key_words = set(key.split()) - {"disease", "syndrome", "disorder", "type", "chronic", "acute"}
            overlap = len(query_words & key_words)
            if overlap > best_overlap:
                best_overlap = overlap
                best_key = key
        if best_key and best_overlap >= 1:
            return best_key

        return None

    def _parse_profile(self, key: str, raw: Dict, coverage: str) -> DiseaseProfile:
        age = raw.get("typical_age_range", [25, 75])
        return DiseaseProfile(
            name=key,
            coverage_level=coverage,
            aliases=raw.get("aliases", []),
            typical_age_range=(age[0], age[1]),
            comorbidities=raw.get("comorbidities", {}),
            medications=raw.get("medications", []),
            differential_diagnoses=raw.get("differential_diagnoses", []),
            differential_questions=raw.get("differential_questions", []),
            patient_education=raw.get("patient_education", ""),
            vital_sign_modifiers=raw.get("vital_sign_modifiers", {}),
            social_history_relevance=raw.get("social_history_relevance", {}),
            severity_distribution=raw.get("severity_distribution", {}),
            raw=raw,
        )

    # --------------------------------------------------------- disease access

    def get_disease_profile(self, disease_name: str) -> DiseaseProfile:
        """Get full disease profile (full / partial / generic coverage)."""
        key = self._match_disease_key(disease_name)
        if key and key in self._diseases:
            return self._parse_profile(key, self._diseases[key], "full")
        return self._parse_profile(
            disease_name, _GENERIC_DISEASE, "generic"
        )

    def get_covered_diseases(self) -> List[str]:
        return list(self._diseases.keys())

    def get_coverage_level(self, disease_name: str) -> str:
        key = self._match_disease_key(disease_name)
        if key and key in self._diseases:
            return "full"
        return "generic"

    # Convenience accessors ------------------------------------------------

    def get_comorbidities(self, disease_name: str) -> Dict[str, float]:
        return self.get_disease_profile(disease_name).comorbidities

    def get_medications_for_condition(self, condition: str) -> List[Dict]:
        return self.get_disease_profile(condition).medications

    def get_differential_diagnoses(self, disease_name: str) -> List[str]:
        return self.get_disease_profile(disease_name).differential_diagnoses

    def get_differential_questions(self, disease_name: str) -> List[str]:
        return self.get_disease_profile(disease_name).differential_questions

    def get_patient_education(self, disease_name: str) -> str:
        return self.get_disease_profile(disease_name).patient_education

    def get_age_range(self, disease_name: str) -> Tuple[int, int]:
        return self.get_disease_profile(disease_name).typical_age_range

    def get_vital_sign_modifiers(self, disease_name: str) -> Dict:
        return self.get_disease_profile(disease_name).vital_sign_modifiers

    def get_severity_distribution(self, disease_name: str) -> Dict[str, float]:
        return self.get_disease_profile(disease_name).severity_distribution

    # ------------------------------------------------------------ drug access

    def normalize_drug_name(self, drug_name: str) -> str:
        """Normalize brand/synonym to generic name."""
        norm_map = self._drugs.get("name_normalization", {})
        lower = drug_name.lower().strip()
        return norm_map.get(lower, drug_name.lower())

    def get_drug_info(self, drug_name: str) -> Optional[DrugInfo]:
        """Get full drug information."""
        drugs = self._drugs.get("drugs", {})
        generic = self.normalize_drug_name(drug_name)
        if generic in drugs:
            raw = drugs[generic]
            return DrugInfo(
                generic_name=generic,
                brand_names=raw.get("brand_names", []),
                drug_class=raw.get("drug_class", ""),
                standard_doses=raw.get("standard_doses", []),
                contraindications=raw.get("contraindications", []),
                interaction_class=raw.get("interaction_class", ""),
                alternatives=raw.get("alternatives", []),
            )
        return None

    def get_alternative_drugs(self, disease_name: str) -> List[Dict]:
        """Get alternative drugs for a disease (when primary already prescribed)."""
        profile = self.get_disease_profile(disease_name)
        if profile.raw and "alternative_drugs" in profile.raw:
            return profile.raw["alternative_drugs"]
        # Also check the drug database
        alts = self._drugs.get("disease_alternatives", {})
        key = self._match_disease_key(disease_name)
        if key and key in alts:
            return alts[key]
        return []

    def check_drug_interactions(self, medications: List[str]) -> List[Dict]:
        """Check all pairs for known interactions."""
        interactions_db = self._drugs.get("interactions", [])
        normalized = [self.normalize_drug_name(m) for m in medications]
        found = []
        seen = set()
        for entry in interactions_db:
            d1 = self.normalize_drug_name(entry.get("drug1", ""))
            d2 = self.normalize_drug_name(entry.get("drug2", ""))
            for med in normalized:
                for med2 in normalized:
                    if med == med2:
                        continue
                    pair = tuple(sorted([med, med2]))
                    if pair in seen:
                        continue
                    if (d1 == med and d2 == med2) or (d1 == med2 and d2 == med):
                        found.append(entry)
                        seen.add(pair)
        return found

    def get_allergy_cross_reactivity(self, allergen: str) -> List[Dict]:
        """Get cross-reactive drugs for an allergen."""
        groups = self._drugs.get("allergy_cross_reactivity", [])
        lower = allergen.lower()
        for group in groups:
            if group.get("allergen", "").lower() == lower:
                return group.get("cross_reactive_drugs", [])
        return []

    def get_allergy_prevalence(self) -> Dict[str, float]:
        return self._drugs.get("allergy_prevalence", {})

    def get_contraindications(self, drug: str, conditions: List[str]) -> List[Dict]:
        """Check drug against patient conditions."""
        contra_db = self._drugs.get("contraindications", [])
        generic = self.normalize_drug_name(drug)
        found = []
        for entry in contra_db:
            if self.normalize_drug_name(entry.get("drug", "")) == generic:
                for cond in conditions:
                    if cond.lower() in entry.get("condition", "").lower():
                        found.append(entry)
        return found

    # ------------------------------------------------------------- lab access

    def get_lab_panel(self, disease_name: str) -> List[Dict]:
        """Get disease-specific lab panel with ranges."""
        panels = self._lab.get("disease_panels", {})
        # Try matching
        key = self._match_disease_key(disease_name)
        if key and key in panels:
            return panels[key]
        # Substring search on panel keys
        lower = disease_name.lower()
        for panel_key in panels:
            if panel_key in lower or lower in panel_key:
                return panels[panel_key]
        return []

    def get_lab_constraints(self) -> List[Dict]:
        return self._lab.get("cross_constraints", [])

    def get_lab_ranges(self, test_name: str) -> Optional[Dict]:
        """Get absolute physiological range for a test."""
        ranges = self._lab.get("absolute_ranges", {}).get("lab_tests", {})
        lower = test_name.lower()
        for key, val in ranges.items():
            if key.lower() == lower:
                return val
        return None

    def get_vital_sign_ranges(self) -> Dict:
        return self._lab.get("absolute_ranges", {}).get("vital_signs", {})

    def interpret_lab_value(self, test_name: str, value: float) -> Optional[str]:
        """Get clinical interpretation string for a lab value."""
        thresholds = self._lab.get("interpretation_thresholds", {})
        lower = test_name.lower()
        for key, entries in thresholds.items():
            if key in lower:
                for entry in entries:
                    lo, hi = entry.get("range", [0, 999])
                    if lo <= value <= hi:
                        return entry.get("description", entry.get("label", ""))
        return None

    # ---------------------------------------------------------- triage access

    def get_triage_rules(self) -> List[Dict]:
        return self._triage.get("rules", [])

    def get_follow_up_defaults(self) -> Dict[str, str]:
        return self._triage.get("follow_up_defaults", {})

    # ------------------------------------------------------------ tool access

    def get_tool_definition(self, tool_name: str) -> Optional[Dict]:
        defs = self._tools.get("tool_definitions", {})
        return defs.get(tool_name)

    def get_tool_human_name(self, tool_name: str) -> str:
        defs = self._tools.get("tool_definitions", {})
        if tool_name in defs:
            return defs[tool_name].get("human_name", tool_name)
        return tool_name

    def get_symptom_tools(self, symptom_name: str) -> List[str]:
        """Get tools for a symptom."""
        mapping = self._tools.get("symptom_tool_map", {})
        lower = symptom_name.lower()
        for key, tools in mapping.items():
            if key in lower or lower in key:
                return tools
        return []

    def get_disease_tools(self, disease_name: str) -> List[str]:
        """Get tools for a disease."""
        mapping = self._tools.get("disease_tool_map", {})
        lower = disease_name.lower()
        for key, tools in mapping.items():
            if key in lower or lower in key:
                return tools
        return []

    def get_all_symptom_probes(self) -> Dict[str, str]:
        """Get all symptom probe questions from clinical_questions.json."""
        return dict(self._questions.get("symptom_probes", {}))

    def get_baseline_tools(self) -> List[str]:
        return self._tools.get("baseline_tools", [])

    def get_ordering_constraints(self) -> List[Dict]:
        return self._tools.get("ordering_constraints", [])

    def get_forbidden_sequences(self) -> List[Dict]:
        return self._tools.get("baseline_forbidden", [])

    # ------------------------------------------------------- question access

    def get_symptom_probe(self, symptom_keyword: str) -> Optional[str]:
        """Get clinical probe question for a symptom keyword."""
        probes = self._questions.get("symptom_probes", {})
        lower = symptom_keyword.lower()
        for key, question in probes.items():
            if key in lower:
                return question
        return None

    def get_all_symptom_probes(self) -> Dict[str, str]:
        return self._questions.get("symptom_probes", {})

    def get_behavior_templates(self, behavior_type: str) -> Dict[str, List[str]]:
        """Get dialogue templates for a behavior type."""
        templates = self._questions.get("behavior_templates", {})
        return templates.get(behavior_type, {})
