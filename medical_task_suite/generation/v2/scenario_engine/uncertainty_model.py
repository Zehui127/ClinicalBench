#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uncertainty Model — Controls information completeness in scenarios.

Determines what information is available, hidden, noisy, or misleading.
This is the key difference from v1: symptoms are NOT all revealed upfront.
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class CompletenessLevel(str, Enum):
    COMPLETE = "complete"      # All symptoms visible
    PARTIAL = "partial"        # Some symptoms hidden, must probe
    MINIMAL = "minimal"        # Most symptoms hidden, heavy probing needed
    MISLEADING = "misleading"  # Some wrong symptoms included


@dataclass
class InformationBudget:
    """How much information the patient provides vs hides."""
    total_real_symptoms: int = 0
    volunteered_count: int = 0       # Patient says without asking
    if_asked_count: int = 0         # Reveals when asked directly
    resistant_count: int = 0         # Reluctant, needs persistence
    hidden_count: int = 0            # Never revealed unless specific probe
    noise_symptom_count: int = 0     # Unrelated symptoms added
    misleading_count: int = 0        # Symptoms pointing to wrong diagnosis

    @property
    def visible_count(self) -> int:
        return self.volunteered_count + self.if_asked_count

    @property
    def completeness_ratio(self) -> float:
        if self.total_real_symptoms == 0:
            return 1.0
        return self.visible_count / self.total_real_symptoms


@dataclass
class UncertaintyConfig:
    """Configuration for uncertainty in a scenario."""
    completeness_level: str = "partial"
    missing_fraction: float = 0.3       # Fraction of symptoms that are hidden
    noise_fraction: float = 0.1         # Fraction of symptoms that are noise
    misleading_fraction: float = 0.0    # Fraction of symptoms that are misleading
    lab_uncertainty: float = 0.0        # Probability of conflicting/ambiguous labs
    history_gap_probability: float = 0.2  # Probability of missing history items

    @classmethod
    def from_difficulty(cls, difficulty: str, task_type: str = "") -> "UncertaintyConfig":
        """Generate uncertainty config based on difficulty and task type."""
        profiles = {
            "L1": cls(
                completeness_level="partial",
                missing_fraction=0.2,
                noise_fraction=0.05,
                misleading_fraction=0.0,
                lab_uncertainty=0.05,
                history_gap_probability=0.1,
            ),
            "L2": cls(
                completeness_level="partial",
                missing_fraction=0.35,
                noise_fraction=0.15,
                misleading_fraction=0.1,
                lab_uncertainty=0.2,
                history_gap_probability=0.3,
            ),
            "L3": cls(
                completeness_level="minimal",
                missing_fraction=0.5,
                noise_fraction=0.2,
                misleading_fraction=0.2,
                lab_uncertainty=0.35,
                history_gap_probability=0.5,
            ),
        }
        config = profiles.get(difficulty, profiles["L2"])

        # Task-type-specific overrides
        if task_type == "conflicting_evidence":
            config.lab_uncertainty = min(1.0, config.lab_uncertainty + 0.3)
        elif task_type == "diagnostic_uncertainty":
            config.missing_fraction = min(0.8, config.missing_fraction + 0.15)
        elif task_type == "patient_non_compliance":
            config.history_gap_probability = min(0.8, config.history_gap_probability + 0.2)

        return config

    @classmethod
    def from_calibrated_data(
        cls,
        difficulty: str,
        task_type: str = "",
        calibration=None,
    ) -> "UncertaintyConfig":
        """
        v2.7: Create config using calibrated noise data if available.

        Falls back to from_difficulty() if no calibration data.
        """
        if calibration is None:
            try:
                from .noise_calibration import NoiseCalibration, DEFAULT_CALIBRATION
                calibration = DEFAULT_CALIBRATION
            except ImportError:
                return cls.from_difficulty(difficulty, task_type)

        # Get calibrated parameters
        cal = NoiseCalibration()
        params = cal.get_calibrated_config(difficulty, task_type)

        # Base lab uncertainty from difficulty
        lab_uncertainty = {"L1": 0.05, "L2": 0.20, "L3": 0.35}.get(difficulty, 0.20)
        history_gap = {"L1": 0.10, "L2": 0.30, "L3": 0.50}.get(difficulty, 0.30)
        completeness = "minimal" if difficulty == "L3" else "partial"

        config = cls(
            completeness_level=completeness,
            missing_fraction=params["missing_fraction"],
            noise_fraction=params["noise_fraction"],
            misleading_fraction=params["misleading_fraction"],
            lab_uncertainty=lab_uncertainty,
            history_gap_probability=history_gap,
        )

        # Task-type overrides (same logic as from_difficulty)
        if task_type == "conflicting_evidence":
            config.lab_uncertainty = min(1.0, config.lab_uncertainty + 0.3)
        elif task_type == "diagnostic_uncertainty":
            config.missing_fraction = min(0.8, config.missing_fraction + 0.15)
        elif task_type == "patient_non_compliance":
            config.history_gap_probability = min(0.8, config.history_gap_probability + 0.2)

        return config


class UncertaintyModel:
    """Apply uncertainty to a set of clinical information."""

    def compute_budget(
        self,
        total_symptoms: int,
        config: UncertaintyConfig,
    ) -> InformationBudget:
        """Calculate how symptoms are distributed across visibility tiers."""
        # Noise symptoms
        noise = max(0, int(total_symptoms * config.noise_fraction))

        # Misleading symptoms
        misleading = max(0, int(total_symptoms * config.misleading_fraction))

        # Hidden symptoms (never volunteered)
        hidden = max(0, int(total_symptoms * config.missing_fraction))

        # Remaining visible symptoms
        visible = max(1, total_symptoms - hidden)

        # Split visible into volunteered vs if_asked
        volunteer_ratio = 0.6 if config.completeness_level != "minimal" else 0.3
        volunteered = max(1, int(visible * volunteer_ratio))
        if_asked = visible - volunteered
        resistant = max(0, int(if_asked * 0.3))

        return InformationBudget(
            total_real_symptoms=total_symptoms,
            volunteered_count=volunteered,
            if_asked_count=if_asked - resistant,
            resistant_count=resistant,
            hidden_count=hidden,
            noise_symptom_count=noise,
            misleading_count=misleading,
        )

    def apply_uncertainty(
        self,
        symptoms: List[str],
        config: UncertaintyConfig,
        rng: Optional[random.Random] = None,
    ) -> Dict[str, List[str]]:
        """
        Distribute symptoms into visibility tiers.

        Returns:
            {
                "volunteer": [...],     # Patient volunteers these
                "if_asked": [...],      # Reveals when asked
                "resistant": [...],     # Reluctant to share
                "hidden": [...],        # Only specific probing reveals
                "noise": [...],         # Unrelated symptoms
                "misleading": [...],    # Points to wrong diagnosis
            }
        """
        if rng is None:
            rng = random.Random()

        budget = self.compute_budget(len(symptoms), config)

        # Shuffle symptoms for random assignment
        shuffled = list(symptoms)
        rng.shuffle(shuffled)

        result = {
            "volunteer": [],
            "if_asked": [],
            "resistant": [],
            "hidden": [],
            "noise": [],
            "misleading": [],
        }

        idx = 0

        # Assign volunteer symptoms
        for _ in range(min(budget.volunteered_count, len(shuffled) - idx)):
            result["volunteer"].append(shuffled[idx])
            idx += 1

        # Assign if_asked symptoms
        for _ in range(min(budget.if_asked_count, len(shuffled) - idx)):
            result["if_asked"].append(shuffled[idx])
            idx += 1

        # Assign resistant symptoms
        for _ in range(min(budget.resistant_count, len(shuffled) - idx)):
            result["resistant"].append(shuffled[idx])
            idx += 1

        # Remaining go to hidden
        while idx < len(shuffled):
            result["hidden"].append(shuffled[idx])
            idx += 1

        return result
