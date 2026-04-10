#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Symptom Generator — Generate symptoms with controlled noise/missing/misleading.

v1: all real symptoms revealed upfront.
v2: symptoms distributed across visibility tiers based on scenario uncertainty.
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from ..scenario_engine.scenario_schema import ScenarioSpec, ClinicalGroundTruth
from ..scenario_engine.uncertainty_model import UncertaintyModel, UncertaintyConfig
from .disease_sampler import DiseaseSampler
from .patient_language import PatientLanguageLayer


# v2.7: Try expanded pools first, fall back to original
try:
    from .expanded_symptom_pools import EXPANDED_NOISE_SYMPTOM_POOL, EXPANDED_MISLEADING_SYMPTOM_MAP
    _NOISE_POOL = EXPANDED_NOISE_SYMPTOM_POOL
    _MISLEADING_MAP = EXPANDED_MISLEADING_SYMPTOM_MAP
except ImportError:
    # Original pools (fallback)
    _NOISE_POOL = [
        "mild headache", "occasional dizziness", "minor skin rash",
        "slight nausea", "mild fatigue", "intermittent back pain",
        "occasional heartburn", "mild joint stiffness", "slight blurry vision",
        "trouble sleeping", "dry mouth", "mild anxiety",
        "occasional ringing in ears", "slight swelling in ankles",
        "mild constipation", "bloating", "mild throat irritation",
        "occasional muscle cramps", "slight hand numbness",
    ]
    _MISLEADING_MAP = {
        "type 2 diabetes": ["weight loss", "frequent infections"],
        "hypertension": ["nosebleed", "visual changes"],
        "coronary artery disease": ["jaw pain", "left arm pain"],
        "copd": ["morning headache", "swollen ankles"],
        "asthma": ["chronic cough", "difficulty swallowing"],
        "heart failure": ["abdominal swelling", "loss of appetite"],
        "stroke": ["ear pain", "toothache"],
        "atrial fibrillation": ["chest pressure", "sweating"],
        "gerd": ["chronic cough", "sore throat"],
        "anxiety disorder": ["chest pain", "shortness of breath"],
    }

# Keep original names as aliases for backward compatibility
NOISE_SYMPTOM_POOL = _NOISE_POOL
MISLEADING_SYMPTOM_MAP = _MISLEADING_MAP


@dataclass
class SymptomSet:
    """Complete symptom configuration for a scenario."""
    # Real symptoms of the target disease
    real_symptoms: List[str] = field(default_factory=list)

    # Distribution across visibility tiers
    volunteer: List[str] = field(default_factory=list)
    if_asked: List[str] = field(default_factory=list)
    resistant: List[str] = field(default_factory=list)
    hidden: List[str] = field(default_factory=list)

    # Non-real symptoms
    noise: List[str] = field(default_factory=list)
    misleading: List[str] = field(default_factory=list)

    # All symptoms the patient might mention (for dialogue generation)
    @property
    def presented_symptoms(self) -> List[str]:
        return self.volunteer + self.noise + self.misleading

    @property
    def all_known_symptoms(self) -> List[str]:
        return self.volunteer + self.if_asked + self.resistant


class SymptomGenerator:
    """Generate symptoms with controlled uncertainty for a scenario."""

    def __init__(self, clinical_kb, primekg=None):
        self.kb = clinical_kb
        self.primekg = primekg
        self.uncertainty = UncertaintyModel()
        self.language = PatientLanguageLayer()

    def generate(
        self,
        disease: str,
        scenario: ScenarioSpec,
        seed: Optional[int] = None,
    ) -> SymptomSet:
        """
        Generate a complete symptom set for the disease-scenario pair.

        v2.8: Confounder-dominant early presentation.
        - Confounder symptoms → volunteer + if_asked (prominent in early turns)
        - True critical symptoms → hidden + resistant (suppressed until later)
        - Confounder mimics the primary, making early misdiagnosis likely
        """
        if seed is not None:
            random.seed(seed)

        # 1. Get real symptoms for the PRIMARY disease
        real_symptoms = self._get_real_symptoms(disease)
        if not real_symptoms:
            real_symptoms = ["fatigue", "general discomfort"]

        # 2. Merge comorbidity symptoms
        gt = scenario.ground_truth
        comorbidity_symptoms = []
        for comorb in gt.comorbidities:
            comorb_name = comorb.name if hasattr(comorb, 'name') else str(comorb)
            c_symptoms = self._get_real_symptoms(comorb_name)
            contribution = comorb.contribution if hasattr(comorb, 'contribution') else 0.3
            n_include = max(1, int(len(c_symptoms) * contribution))
            comorbidity_symptoms.extend(c_symptoms[:n_include])

        # 3. Get confounder symptoms
        confounder_symptoms = []
        confounder_names = []
        for conf in gt.confounders:
            conf_name = conf.name if hasattr(conf, 'name') else str(conf)
            confounder_names.append(conf_name)
            c_symptoms = self._get_real_symptoms(conf_name)
            # Confounders contribute up to 3 overlapping/mimicking symptoms
            confounder_symptoms.extend(c_symptoms[:3])

        # 4. Build uncertainty config
        config = UncertaintyConfig.from_difficulty(scenario.difficulty, scenario.task_type)

        # 5. Distribute TRUE symptoms: push critical ones to hidden/resistant
        all_real = real_symptoms + comorbidity_symptoms
        distribution = self.uncertainty.apply_uncertainty(all_real, config)

        # 6. CONFOUNDER DOMINANCE: redistribute tiers
        #    Confounder symptoms → volunteer + if_asked (front-loaded)
        #    True symptoms → if_asked + hidden + resistant (back-loaded)
        volunteer_conf = confounder_symptoms[:2]  # Top 2 confounder symptoms: volunteered
        if_asked_conf = confounder_symptoms[2:4]  # Next confounder symptoms: if_asked

        # Remove confounder symptoms from true distribution (avoid double-counting)
        conf_set = set(s.lower() for s in confounder_symptoms)
        for tier in ("volunteer", "if_asked"):
            distribution[tier] = [s for s in distribution.get(tier, [])
                                  if s.lower() not in conf_set]

        # Push remaining true symptoms toward hidden/resistant
        true_volunteer = distribution.get("volunteer", [])
        true_if_asked = distribution.get("if_asked", [])
        true_hidden = distribution.get("hidden", [])
        true_resistant = distribution.get("resistant", [])

        # Keep only 1 true symptom in volunteer (the least informative one)
        if len(true_volunteer) > 1:
            demoted = true_volunteer[1:]
            true_volunteer = true_volunteer[:1]
            true_hidden.extend(demoted)

        # Move if_asked true symptoms to hidden for higher difficulty
        if scenario.difficulty in ("L2", "L3") and true_if_asked:
            # Keep first in if_asked, push rest to hidden
            demoted = true_if_asked[1:]
            true_if_asked = true_if_asked[:1]
            true_resistant.extend(demoted)

        # 7. Final tier assignment
        final_volunteer = volunteer_conf + true_volunteer
        final_if_asked = if_asked_conf + true_if_asked
        final_hidden = true_hidden
        final_resistant = true_resistant

        # 8. Generate noise
        noise = self._generate_noise(scenario, config)

        # 9. Misleading = confounder symptoms that aren't already in volunteer/if_asked
        remaining_conf = [s for s in confounder_symptoms
                          if s not in volunteer_conf and s not in if_asked_conf]
        misleading = remaining_conf if remaining_conf else self._generate_misleading(disease, scenario, config)

        # 10. Floor: ensure at least 3 true symptoms for discrimination
        MIN_SYMPTOMS = 3
        true_count = len(true_volunteer) + len(true_if_asked) + len(true_hidden) + len(true_resistant)
        if true_count < MIN_SYMPTOMS:
            existing = set(all_real)
            supplement_pool = self._fallback_symptoms(disease)
            supplement_pool = [s for s in supplement_pool if s not in existing]
            if not supplement_pool:
                supplement_pool = ["fatigue", "headache", "nausea", "dizziness", "appetite loss"]
                supplement_pool = [s for s in supplement_pool if s not in existing]
            needed = MIN_SYMPTOMS - true_count
            random.shuffle(supplement_pool)
            extra = supplement_pool[:needed]
            for i, s in enumerate(extra):
                tier = "hidden" if i % 2 == 0 else "resistant"
                if tier == "hidden":
                    final_hidden.append(s)
                else:
                    final_resistant.append(s)

        # 11. Convert to patient-friendly language
        volunteer = [self.language.to_patient(s) for s in final_volunteer]
        if_asked = [self.language.to_patient(s) for s in final_if_asked]
        hidden = [self.language.to_patient(s) for s in final_hidden]
        resistant = [self.language.to_patient(s) for s in final_resistant]
        noise = [self.language.to_patient(s) for s in noise]
        misleading = [self.language.to_patient(s) for s in misleading]

        return SymptomSet(
            real_symptoms=all_real,
            volunteer=volunteer,
            if_asked=if_asked,
            resistant=resistant,
            hidden=hidden,
            noise=noise,
            misleading=misleading,
        )

    def _get_real_symptoms(self, disease: str) -> List[str]:
        """Get real symptoms for a disease from clinical KB."""
        profile = self.kb.get_disease_profile(disease)
        symptoms = []

        # Try differential_questions for symptom-like content
        if hasattr(profile, 'differential_questions'):
            symptoms = [
                q.replace("?", "").strip()
                for q in (profile.differential_questions or [])
                if len(q) < 40
            ]

        # Try aliases
        if not symptoms and hasattr(profile, 'aliases'):
            symptoms = profile.aliases or []

        # Fallback to disease-specific common symptoms
        if not symptoms:
            symptoms = self._fallback_symptoms(disease)

        return symptoms

    def _fallback_symptoms(self, disease: str) -> List[str]:
        """Fallback symptom list for common diseases."""
        fallback = {
            "type 2 diabetes": ["frequent urination", "fatigue", "blurred vision", "thirst"],
            "hypertension": ["headache", "dizziness", "chest pain"],
            "coronary artery disease": ["chest pain", "shortness of breath", "fatigue"],
            "copd": ["cough", "shortness of breath", "fatigue"],
            "asthma": ["wheezing", "shortness of breath", "cough"],
            "heart failure": ["shortness of breath", "swelling", "fatigue"],
            "chronic kidney disease": ["fatigue", "swelling", "nausea"],
            "anemia": ["fatigue", "dizziness", "shortness of breath"],
            "stroke": ["weakness", "confusion", "headache"],
            "atrial fibrillation": ["palpitations", "dizziness", "shortness of breath"],
            "gout": ["joint pain", "swelling", "redness"],
            "osteoporosis": ["back pain", "joint pain", "weakness"],
            "gerd": ["heartburn", "chest pain", "cough"],
            "migraine": ["headache", "nausea", "blurred vision"],
            "epilepsy": ["seizure", "confusion", "headache"],
            "parkinson disease": ["tremor", "stiffness", "weakness"],
            "rheumatoid arthritis": ["joint pain", "swelling", "stiffness"],
            "anxiety disorder": ["anxiety", "insomnia", "fatigue"],
            "hyperthyroidism": ["weight loss", "tremor", "anxiety"],
            "nephrolithiasis": ["back pain", "abdominal pain", "nausea"],
            "pulmonary embolism": ["shortness of breath", "chest pain", "cough"],
            "meningitis": ["fever", "headache", "confusion"],
            "covid-19": ["fever", "cough", "fatigue"],
            "pneumonia": ["cough", "fever", "shortness of breath"],
        }
        return fallback.get(disease.lower(), ["fatigue", "pain"])

    def _generate_noise(
        self, scenario: ScenarioSpec, config: UncertaintyConfig
    ) -> List[str]:
        """Generate unrelated noise symptoms from expanded pool."""
        n_noise = max(0, int(config.noise_fraction * 5))  # Scale to ~5 base symptoms
        if n_noise == 0:
            return []

        pool = [s for s in _NOISE_POOL]
        random.shuffle(pool)
        return pool[:n_noise]

    def _generate_misleading(
        self, disease: str, scenario: ScenarioSpec, config: UncertaintyConfig
    ) -> List[str]:
        """Generate misleading symptoms that point to wrong diagnosis."""
        if config.misleading_fraction <= 0:
            return []

        # Check for disease-specific misleading symptoms (expanded map)
        candidates = _MISLEADING_MAP.get(disease.lower(), [])

        if not candidates:
            # Generic misleading pool
            candidates = [
                "unexplained weight change", "night sweats",
                "new skin changes", "change in appetite",
            ]

        n = max(1, int(config.misleading_fraction * 3))
        random.shuffle(candidates)
        return candidates[:n]
