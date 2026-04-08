#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calibrated Defaults — Pre-computed persona parameters from dialogue analysis.

Generated from analysis of 112,165 HealthCareMagic English dialogues.
These values are used when no runtime calibration data is available.

Regenerate with:
    python -c "
    from medical_task_suite.generation.v2.persona_engine.behavior_calibration import BehaviorCalibration
    cal = BehaviorCalibration('path/to/HealthCareMagic-100k.json')
    profiles = cal.compute_profiles()
    # Then update the constants below
    "
"""

from typing import Dict, Tuple

# Calibration profiles per behavior type
# Values are (low, high) tuples for random.uniform() sampling
DEPARTMENT_CALIBRATIONS = {
    # Default profiles (behavior type → parameter ranges)
    "cooperative": {
        "trust_range": (0.55, 0.80),
        "compliance_range": (0.70, 0.95),
        "reveal_prob_range": (0.50, 0.80),
        "avg_dialogue_length": 6.0,
        "refusal_rate": 0.01,
    },
    "forgetful": {
        "trust_range": (0.40, 0.65),
        "compliance_range": (0.55, 0.80),
        "reveal_prob_range": (0.30, 0.55),
        "avg_dialogue_length": 5.0,
        "refusal_rate": 0.01,
    },
    "confused": {
        "trust_range": (0.30, 0.55),
        "compliance_range": (0.40, 0.65),
        "reveal_prob_range": (0.20, 0.45),
        "avg_dialogue_length": 7.0,
        "refusal_rate": 0.01,
    },
    "concealing": {
        "trust_range": (0.15, 0.40),
        "compliance_range": (0.20, 0.50),
        "reveal_prob_range": (0.10, 0.30),
        "avg_dialogue_length": 4.0,
        "refusal_rate": 0.02,
    },
    "pressuring": {
        "trust_range": (0.30, 0.55),
        "compliance_range": (0.45, 0.70),
        "reveal_prob_range": (0.35, 0.60),
        "avg_dialogue_length": 3.0,
        "refusal_rate": 0.01,
    },
    "refusing": {
        "trust_range": (0.10, 0.30),
        "compliance_range": (0.10, 0.35),
        "reveal_prob_range": (0.05, 0.25),
        "avg_dialogue_length": 4.0,
        "refusal_rate": 0.04,
    },
}

# Calibrated trust modifiers
# Slightly adjusted from original based on 112K dialogue analysis
CALIBRATED_TRUST_MODIFIERS: Dict[str, float] = {
    # Positive actions
    "empathy": 0.15,
    "explanation": 0.13,
    "listening": 0.08,
    "shared_decision": 0.12,
    "reassurance": 0.10,
    "thoroughness": 0.05,

    # Negative actions
    "dismissal": -0.20,
    "rudeness": -0.15,
    "rushing": -0.10,
    "ignoring_concerns": -0.15,
    "jargon": -0.05,
    "repeated_questions": -0.08,
}

# Data source metadata
CALIBRATION_SOURCE = {
    "dataset": "HealthCareMagic-100k",
    "n_dialogues": 112165,
    "method": "symptom_count + refusal_pattern + complaint_length analysis",
}
