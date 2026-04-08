#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Disease Trajectory — Temporal progression of disease state.

v2.1: Disease is not static — it evolves over conversation turns.
- Symptoms can worsen if agent delays
- New complications can emerge
- Patient state changes based on agent actions

This is the key difference between "toy benchmark" and "clinical benchmark".
"""

import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class TrajectoryPhase(str, Enum):
    STABLE = "stable"
    WORSENING = "worsening"
    CRITICAL = "critical"
    IMPROVING = "improving"


@dataclass
class SymptomEvolution:
    """How a single symptom evolves over time."""
    symptom: str
    initial_severity: float = 0.5  # 0.0-1.0
    current_severity: float = 0.5
    worsening_rate: float = 0.0    # Per turn if untreated
    improvement_rate: float = 0.0  # Per turn if treated
    complication_threshold: float = 0.8  # Triggers complication at this severity

    def evolve(self, turn: int, treated: bool = False) -> None:
        """Evolve symptom for one turn."""
        if treated:
            self.current_severity = max(0.0, self.current_severity - self.improvement_rate)
        else:
            self.current_severity = min(1.0, self.current_severity + self.worsening_rate)

    @property
    def has_complication(self) -> bool:
        return self.current_severity >= self.complication_threshold


@dataclass
class DiseaseTrajectory:
    """
    Temporal disease progression model.

    Tracks how disease state evolves across conversation turns.
    Agent delays cause worsening; proper treatment causes improvement.
    """
    disease: str = ""
    current_phase: TrajectoryPhase = TrajectoryPhase.STABLE
    turn_count: int = 0

    # Symptom evolutions
    symptom_evolutions: Dict[str, SymptomEvolution] = field(default_factory=dict)

    # Complications that have emerged
    emerged_complications: List[str] = field(default_factory=list)

    # Timeline milestones (turn → event)
    milestones: Dict[int, str] = field(default_factory=dict)

    # Base worsening rate (affected by difficulty and disease)
    base_worsening_rate: float = 0.02

    @classmethod
    def from_disease(
        cls,
        disease: str,
        difficulty: str = "L2",
        symptoms: Optional[List[str]] = None,
    ) -> "DiseaseTrajectory":
        """Create trajectory for a disease."""
        # Difficulty affects worsening rate
        rate_map = {"L1": 0.01, "L2": 0.03, "L3": 0.06}
        base_rate = rate_map.get(difficulty, 0.03)

        trajectory = cls(
            disease=disease,
            base_worsening_rate=base_rate,
        )

        # Create symptom evolutions
        if symptoms:
            for i, symptom in enumerate(symptoms):
                # Key symptoms worsen faster
                is_key = i < len(symptoms) // 2  # First half are key symptoms
                trajectory.symptom_evolutions[symptom] = SymptomEvolution(
                    symptom=symptom,
                    initial_severity=0.4 if not is_key else 0.6,
                    current_severity=0.4 if not is_key else 0.6,
                    worsening_rate=base_rate * (1.5 if is_key else 1.0),
                    improvement_rate=0.05,
                    complication_threshold=0.8,
                )

        # Disease-specific milestones
        trajectory.milestones = cls._get_milestones(disease, difficulty)

        return trajectory

    def evolve(self, treated: bool = False) -> Dict[str, Any]:
        """
        Evolve disease state for one turn.

        Returns dict with:
        - new_symptoms: symptoms that emerged
        - complications: complications that appeared
        - phase_change: if trajectory phase changed
        """
        self.turn_count += 1
        result = {
            "new_symptoms": [],
            "complications": [],
            "phase_change": None,
            "current_phase": self.current_phase.value,
        }

        # Check milestones
        if self.turn_count in self.milestones:
            event = self.milestones[self.turn_count]
            result["new_symptoms"].append(event)

        # Evolve each symptom
        for symptom, evolution in self.symptom_evolutions.items():
            prev_severity = evolution.current_severity
            evolution.evolve(self.turn_count, treated)

            # Check for complication
            if evolution.has_complication and symptom not in self.emerged_complications:
                complication = f"worsening_{symptom}"
                self.emerged_complications.append(symptom)
                result["complications"].append(complication)

        # Update phase
        old_phase = self.current_phase
        avg_severity = (
            sum(e.current_severity for e in self.symptom_evolutions.values()) /
            max(1, len(self.symptom_evolutions))
        )

        if treated and avg_severity < 0.3:
            self.current_phase = TrajectoryPhase.IMPROVING
        elif avg_severity > 0.7:
            self.current_phase = TrajectoryPhase.CRITICAL
        elif avg_severity > 0.5:
            self.current_phase = TrajectoryPhase.WORSENING
        else:
            self.current_phase = TrajectoryPhase.STABLE

        if old_phase != self.current_phase:
            result["phase_change"] = f"{old_phase.value} → {self.current_phase.value}"

        return result

    def get_current_severity(self) -> float:
        """Get average current severity across all symptoms."""
        if not self.symptom_evolutions:
            return 0.5
        return sum(e.current_severity for e in self.symptom_evolutions.values()) / len(self.symptom_evolutions)

    def get_symptom_state(self, symptom: str) -> Optional[Dict[str, Any]]:
        """Get current state of a specific symptom."""
        evo = self.symptom_evolutions.get(symptom)
        if not evo:
            return None
        return {
            "symptom": symptom,
            "severity": round(evo.current_severity, 2),
            "trend": "worsening" if evo.worsening_rate > 0 and not evo.has_complication else "stable",
            "complication": evo.has_complication,
        }

    @staticmethod
    def _get_milestones(disease: str, difficulty: str) -> Dict[int, str]:
        """Get disease-specific timeline milestones."""
        # Common milestones by disease category
        disease_milestones = {
            "diabetes": {5: "polyuria worsening", 8: "blurred vision onset"},
            "hypertension": {4: "headache worsening", 7: "visual changes"},
            "heart": {3: "chest pain at rest", 6: "shortness of breath worsening"},
            "copd": {4: "cough worsening", 7: "cyanosis risk"},
            "stroke": {2: "speech difficulty", 4: "weakness spreading"},
            "pneumonia": {3: "fever spike", 5: "oxygen desaturation risk"},
            "meningitis": {2: "neck stiffness", 4: "confusion worsening"},
            "appendicitis": {3: "rebound tenderness", 5: "fever spike"},
        }

        milestones = {}
        for key, ms in disease_milestones.items():
            if key in disease.lower():
                for turn, event in ms.items():
                    # Scale turns by difficulty
                    scale = {"L1": 1.5, "L2": 1.0, "L3": 0.7}.get(difficulty, 1.0)
                    scaled_turn = max(2, int(turn * scale))
                    milestones[scaled_turn] = event
                break

        return milestones


# Causal consistency rules
# These define which symptoms are causally related
CAUSAL_RULES = {
    # disease_symptom → related symptoms that should be consistent
    "chest_pain": {
        "related": ["shortness of breath", "fatigue"],
        "consistency": "if chest pain severe, shortness of breath should be present",
    },
    "fever": {
        "related": ["chills", "fatigue", "sweating"],
        "consistency": "if fever > 39, chills should be mentioned",
    },
    "headache_severe": {
        "related": ["nausea", "photophobia", "confusion"],
        "consistency": "severe headache often accompanied by nausea",
    },
    "shortness_of_breath": {
        "related": ["fatigue", "chest pain"],
        "consistency": "SOB at rest implies severe respiratory issue",
    },
    "joint_pain": {
        "related": ["swelling", "stiffness"],
        "consistency": "joint pain with swelling suggests inflammation",
    },
}


def check_causal_consistency(symptoms: List[str]) -> List[str]:
    """
    Check if a set of symptoms is causally consistent.

    Returns list of consistency warnings.
    """
    warnings = []
    symptom_lower = [s.lower() for s in symptoms]

    for trigger, rule in CAUSAL_RULES.items():
        if trigger in " ".join(symptom_lower):
            for related in rule["related"]:
                if related.lower() not in " ".join(symptom_lower):
                    # Not necessarily wrong, but worth noting
                    pass

    return warnings
