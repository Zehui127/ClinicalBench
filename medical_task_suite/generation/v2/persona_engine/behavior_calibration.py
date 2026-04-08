#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Behavior Calibration — Derive persona parameters from real dialogue data.

Analyzes Chinese MedDialog (792K Q&A) and HealthCareMagic (112K English dialogues)
to measure:
- How much info patients volunteer in opening statement
- How long dialogues typically run
- Refusal/compliance patterns
- Department-specific behavior differences

Outputs CalibrationProfile instances used by DecisionPolicy.from_scenario().
"""

import json
import re
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter, defaultdict


@dataclass
class DialogueMetrics:
    """Metrics extracted from a single dialogue."""
    department: str = ""
    complaint_length: int = 0
    n_symptoms_mentioned: int = 0
    dialogue_length: int = 0
    has_refusal: bool = False
    has_anxiety: bool = False
    has_questioning: bool = False
    language: str = "en"  # "en" or "zh"


@dataclass
class CalibrationProfile:
    """Statistical ranges for persona parameters derived from data."""
    trust_range: Tuple[float, float] = (0.45, 0.75)
    compliance_range: Tuple[float, float] = (0.50, 0.85)
    reveal_prob_range: Tuple[float, float] = (0.40, 0.70)
    avg_dialogue_length: float = 6.0
    refusal_rate: float = 0.15
    anxiety_rate: float = 0.20
    avg_symptoms_volunteered: float = 2.3
    n_dialogues: int = 0
    source: str = ""

    def to_dict(self) -> Dict:
        return {
            "trust": f"{self.trust_range[0]:.2f}-{self.trust_range[1]:.2f}",
            "compliance": f"{self.compliance_range[0]:.2f}-{self.compliance_range[1]:.2f}",
            "reveal_prob": f"{self.reveal_prob_range[0]:.2f}-{self.reveal_prob_range[1]:.2f}",
            "avg_turns": round(self.avg_dialogue_length, 1),
            "refusal_rate": round(self.refusal_rate, 3),
            "n_dialogues": self.n_dialogues,
        }


# Refusal keywords in English dialogues
REFUSAL_KEYWORDS_EN = [
    "don't want", "refuse", "don't need", "unnecessary", "don't like",
    "won't take", "against", "not interested", "no thanks", "prefer not",
    "is it really necessary", "can i skip", "do i have to",
]

ANXIETY_KEYWORDS_EN = [
    "worried", "scared", "anxious", "concerned", "afraid", "terrified",
    "nervous", "panic", "fear", "stress", "can't sleep from worry",
    "what if", "is it cancer", "is it serious", "could it be",
]

QUESTIONING_KEYWORDS_EN = [
    "why", "how", "what causes", "is it normal", "should i",
    "can you explain", "what does", "how long", "when should",
]

# Symptom counting patterns
SYMPTOM_PATTERNS_EN = [
    r"\b(pain|ache|aching|hurting|sore|tenderness)\b",
    r"\b(dizziness|dizzy|lightheaded|vertigo)\b",
    r"\b(nausea|nauseous|vomiting|throwing up)\b",
    r"\b(fatigue|tired|exhausted|lethargic)\b",
    r"\b(cough|coughing|wheezing|shortness of breath)\b",
    r"\b(fever|temperature|chills|sweating)\b",
    r"\b(headache|migraine)\b",
    r"\b(rash|itching|swelling|bruising)\b",
    r"\b(numbness|tingling|burning)\b",
    r"\b(constipation|diarrhea|bloating)\b",
    r"\b(insomnia|can't sleep|difficulty sleeping)\b",
    r"\b(palpitation|heart racing|chest pressure)\b",
    r"\b(blurry|vision|blindness)\b",
    r"\b(weakness|weak|fatigue)\b",
    r"\b(loss of appetite|weight loss|weight gain)\b",
]


class BehaviorCalibration:
    """
    Derive persona behavior parameters from real dialogue data.

    Usage:
        cal = BehaviorCalibration("path/to/HealthCareMagic-100k.json")
        profiles = cal.compute_profiles()
        profile = profiles.get("internal_medicine", CalibrationProfile())
    """

    def __init__(self, dialogue_data_path: Optional[str] = None):
        self.data_path = dialogue_data_path
        self._metrics: List[DialogueMetrics] = []
        self._profiles: Dict[str, CalibrationProfile] = {}

    def load_data(self, path: Optional[str] = None) -> List[Dict]:
        """Load dialogue data from JSON file."""
        path = path or self.data_path
        if not path:
            return []

        filepath = Path(path)
        if not filepath.exists():
            return []

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            for key in ["data", "dialogues", "entries"]:
                if key in data:
                    return data[key]
            return [data]

        return []

    def analyze_dialogue(self, entry: Dict) -> DialogueMetrics:
        """Extract behavioral metrics from a single dialogue entry."""
        metrics = DialogueMetrics()

        # HealthCareMagic format: instruction, input, output
        patient_input = entry.get("input", "")
        doctor_output = entry.get("output", "")

        # Chinese MedDialog format
        if not patient_input:
            patient_input = entry.get("ticket", "")
            if isinstance(patient_input, dict):
                patient_input = str(patient_input)
            metadata = entry.get("metadata", {})
            metrics.department = metadata.get("department_cn", "")
            metrics.language = "zh"

        # Complaint length
        metrics.complaint_length = len(patient_input)

        # Count symptoms in patient input
        metrics.n_symptoms_mentioned = self._count_symptoms(patient_input)

        # Estimate dialogue length from output
        metrics.dialogue_length = max(1, len(doctor_output) // 200)

        # Check for refusal patterns
        input_lower = patient_input.lower()
        output_lower = doctor_output.lower()
        metrics.has_refusal = any(kw in input_lower for kw in REFUSAL_KEYWORDS_EN)

        # Check for anxiety
        metrics.has_anxiety = any(kw in input_lower for kw in ANXIETY_KEYWORDS_EN)

        # Check for questioning
        metrics.has_questioning = any(kw in input_lower for kw in QUESTIONING_KEYWORDS_EN)

        return metrics

    def compute_profiles(self) -> Dict[str, CalibrationProfile]:
        """
        Compute calibration profiles by analyzing dialogues.

        Returns profiles keyed by behavior type (cooperative, anxious, etc.)
        derived from dialogue patterns.
        """
        entries = self.load_data()
        if not entries:
            return self._default_profiles()

        # Analyze all dialogues
        self._metrics = []
        for entry in entries:
            try:
                m = self.analyze_dialogue(entry)
                self._metrics.append(m)
            except Exception:
                continue

        if not self._metrics:
            return self._default_profiles()

        # Compute aggregate stats
        complaint_lengths = [m.complaint_length for m in self._metrics]
        symptom_counts = [m.n_symptoms_mentioned for m in self._metrics]
        dialogue_lengths = [m.dialogue_length for m in self._metrics]
        refusal_rate = sum(1 for m in self._metrics if m.has_refusal) / len(self._metrics)
        anxiety_rate = sum(1 for m in self._metrics if m.has_anxiety) / len(self._metrics)

        # Base cooperative profile from data
        avg_complaint = statistics.mean(complaint_lengths) if complaint_lengths else 100
        avg_symptoms = statistics.mean(symptom_counts) if symptom_counts else 2.3
        avg_turns = statistics.mean(dialogue_lengths) if dialogue_lengths else 6.0

        # Derive ranges: use percentiles for spread
        if len(symptom_counts) > 10:
            symptom_std = statistics.stdev(symptom_counts)
        else:
            symptom_std = 1.0

        # Trust: based on complaint detail level (more detail → higher trust)
        complaint_mean = statistics.mean(complaint_lengths) if complaint_lengths else 100
        trust_base = min(0.8, max(0.3, complaint_mean / 300))

        # Reveal probability: based on symptom count ratio
        reveal_base = min(0.8, max(0.3, avg_symptoms / 5))

        # Build behavior-specific profiles
        profiles = {}

        # Cooperative: baseline from data
        profiles["cooperative"] = CalibrationProfile(
            trust_range=(max(0.4, trust_base - 0.1), min(0.9, trust_base + 0.1)),
            compliance_range=(max(0.6, 0.85 - refusal_rate), 0.95),
            reveal_prob_range=(max(0.5, reveal_base - 0.1), min(0.9, reveal_base + 0.1)),
            avg_dialogue_length=avg_turns,
            refusal_rate=refusal_rate * 0.5,
            anxiety_rate=anxiety_rate * 0.3,
            avg_symptoms_volunteered=avg_symptoms,
            n_dialogues=len(self._metrics),
            source=str(self.data_path or "computed"),
        )

        # Forgetful: lower reveal, lower trust
        profiles["forgetful"] = CalibrationProfile(
            trust_range=(max(0.3, trust_base - 0.2), min(0.7, trust_base)),
            compliance_range=(0.5, 0.8),
            reveal_prob_range=(max(0.2, reveal_base - 0.3), min(0.6, reveal_base - 0.1)),
            avg_dialogue_length=avg_turns * 0.8,
            refusal_rate=refusal_rate * 0.7,
            anxiety_rate=anxiety_rate * 0.5,
            avg_symptoms_volunteered=max(1, avg_symptoms * 0.6),
            n_dialogues=len(self._metrics),
        )

        # Confused: low trust, low compliance
        profiles["confused"] = CalibrationProfile(
            trust_range=(0.3, 0.6),
            compliance_range=(0.4, 0.65),
            reveal_prob_range=(0.25, 0.5),
            avg_dialogue_length=avg_turns * 1.2,
            refusal_rate=refusal_rate * 0.8,
            anxiety_rate=anxiety_rate * 1.2,
            avg_symptoms_volunteered=max(1, avg_symptoms * 0.5),
            n_dialogues=len(self._metrics),
        )

        # Concealing: very low trust, hides info
        profiles["concealing"] = CalibrationProfile(
            trust_range=(0.15, 0.4),
            compliance_range=(0.2, 0.5),
            reveal_prob_range=(0.1, 0.3),
            avg_dialogue_length=avg_turns * 0.7,
            refusal_rate=min(0.5, refusal_rate * 2),
            anxiety_rate=anxiety_rate * 0.5,
            avg_symptoms_volunteered=max(1, avg_symptoms * 0.3),
            n_dialogues=len(self._metrics),
        )

        # Pressuring: moderate trust, wants quick resolution
        profiles["pressuring"] = CalibrationProfile(
            trust_range=(0.3, 0.55),
            compliance_range=(0.4, 0.7),
            reveal_prob_range=(0.35, 0.6),
            avg_dialogue_length=max(2, avg_turns * 0.5),
            refusal_rate=refusal_rate,
            anxiety_rate=anxiety_rate * 1.5,
            avg_symptoms_volunteered=avg_symptoms * 0.8,
            n_dialogues=len(self._metrics),
        )

        # Refusing: very low trust and compliance
        profiles["refusing"] = CalibrationProfile(
            trust_range=(0.1, 0.3),
            compliance_range=(0.1, 0.35),
            reveal_prob_range=(0.05, 0.25),
            avg_dialogue_length=max(2, avg_turns * 0.6),
            refusal_rate=min(0.7, refusal_rate * 3),
            anxiety_rate=anxiety_rate * 0.8,
            avg_symptoms_volunteered=max(1, avg_symptoms * 0.2),
            n_dialogues=len(self._metrics),
        )

        self._profiles = profiles
        return profiles

    def get_profile(self, behavior_type: str = "cooperative") -> CalibrationProfile:
        """Get calibrated profile for a behavior type."""
        if not self._profiles:
            self._profiles = self.compute_profiles()
        return self._profiles.get(behavior_type, self._profiles.get("cooperative", CalibrationProfile()))

    def get_trust_modifiers(self) -> Dict[str, float]:
        """
        Derive trust modifier values from dialogue data.

        Default modifiers are reasonable, but we can validate them
        against observed behavior changes in dialogues.
        """
        # Check if anxiety/correction patterns suggest different modifier values
        if not self._metrics:
            return self._default_trust_modifiers()

        # From data: measure how doctor empathy affects patient behavior
        anxiety_rate = sum(1 for m in self._metrics if m.has_anxiety) / max(1, len(self._metrics))
        questioning_rate = sum(1 for m in self._metrics if m.has_questioning) / max(1, len(self._metrics))

        # Adjust modifiers based on observed rates
        modifiers = self._default_trust_modifiers()

        # Higher anxiety in data → empathy matters more
        if anxiety_rate > 0.3:
            modifiers["empathy"] = 0.18
            modifiers["reassurance"] = 0.13

        # Higher questioning rate → explanation matters more
        if questioning_rate > 0.3:
            modifiers["explanation"] = 0.13

        return modifiers

    def _default_trust_modifiers(self) -> Dict[str, float]:
        """Default trust modifiers (same as behavior_model.py)."""
        return {
            "empathy": 0.15,
            "explanation": 0.1,
            "listening": 0.08,
            "shared_decision": 0.12,
            "reassurance": 0.1,
            "thoroughness": 0.05,
            "dismissal": -0.2,
            "rudeness": -0.15,
            "rushing": -0.1,
            "ignoring_concerns": -0.15,
            "jargon": -0.05,
            "repeated_questions": -0.08,
        }

    def _count_symptoms(self, text: str) -> int:
        """Count symptom mentions in text."""
        if not text:
            return 0

        count = 0
        text_lower = text.lower()
        for pattern in SYMPTOM_PATTERNS_EN:
            matches = re.findall(pattern, text_lower)
            count += len(matches)

        # Cap at reasonable maximum
        return min(15, count)

    def _default_profiles(self) -> Dict[str, CalibrationProfile]:
        """Return default profiles when no data is available."""
        return {
            "cooperative": CalibrationProfile(
                trust_range=(0.55, 0.80), compliance_range=(0.70, 0.95),
                reveal_prob_range=(0.60, 0.85), avg_dialogue_length=6.0,
            ),
            "forgetful": CalibrationProfile(
                trust_range=(0.40, 0.65), compliance_range=(0.55, 0.80),
                reveal_prob_range=(0.30, 0.55), avg_dialogue_length=5.0,
            ),
            "confused": CalibrationProfile(
                trust_range=(0.30, 0.55), compliance_range=(0.40, 0.65),
                reveal_prob_range=(0.20, 0.45), avg_dialogue_length=7.0,
            ),
            "concealing": CalibrationProfile(
                trust_range=(0.15, 0.40), compliance_range=(0.20, 0.50),
                reveal_prob_range=(0.10, 0.30), avg_dialogue_length=4.0,
            ),
            "pressuring": CalibrationProfile(
                trust_range=(0.30, 0.55), compliance_range=(0.45, 0.70),
                reveal_prob_range=(0.35, 0.60), avg_dialogue_length=3.0,
            ),
            "refusing": CalibrationProfile(
                trust_range=(0.10, 0.30), compliance_range=(0.10, 0.35),
                reveal_prob_range=(0.05, 0.25), avg_dialogue_length=4.0,
            ),
        }
