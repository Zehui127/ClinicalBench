#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Value Function — 1 form, task-conditioned parameters, non-linear safety.

v2.6: Upgraded from linear model to continuous risk function.

v2.5 problem: Linear safety weight can't capture that some safety violations
are catastrophic (fatal drug interaction) while others are minor (slight delay).
A linear model treats safety=0.1 the same as safety=0.9 - just scaled by weight.

v2.6 solution: Soft safety threshold using sigmoid + piecewise penalty.
  - Near threshold: smooth gradient (differentiable for optimization)
  - Below threshold: steep penalty that increases with severity
  - Well above threshold: no penalty

value = linear_base(w, scores) + safety_penalty(safety) + efficiency_bonus(cost)
"""

import math
from typing import Dict, List, Optional, Any


# ============================================================
# Task Objectives → Weight Derivation
# ============================================================

TASK_OBJECTIVES = {
    "diagnostic_uncertainty": {
        "objective": "Find correct diagnosis through systematic information gathering",
        "priority": ["information", "outcome", "safety", "cost"],
        "rationale": "The core challenge is information gathering — agent must probe hidden symptoms, order tests, reason under uncertainty before concluding.",
    },
    "conflicting_evidence": {
        "objective": "Resolve contradictory evidence through additional investigation",
        "priority": ["information", "outcome", "safety", "cost"],
        "rationale": "Primary challenge is reconciling conflicting data — requires thorough evidence gathering and systematic reasoning.",
    },
    "treatment_tradeoff": {
        "objective": "Select optimal treatment balancing risks and benefits with patient preferences",
        "priority": ["outcome", "safety", "information", "cost"],
        "rationale": "The decision itself matters most (outcome), but must be safe and informed by patient preferences.",
    },
    "patient_non_compliance": {
        "objective": "Build trust and motivate patient compliance through communication",
        "priority": ["information", "safety", "outcome", "cost"],
        "rationale": "Communication (information gathering about concerns, building rapport) is the primary tool. Safety matters because non-compliance creates risks.",
    },
    "drug_safety_risk": {
        "objective": "Identify and avoid drug interactions, allergies, and contraindications",
        "priority": ["safety", "information", "outcome", "cost"],
        "rationale": "Avoiding harm is the paramount objective. Information gathering is needed to identify risks, but safety dominates.",
    },
    "emergency_triage": {
        "objective": "Rapidly assess and triage while maintaining patient safety",
        "priority": ["safety", "cost", "outcome", "information"],
        "rationale": "Speed (low cost) and safety are co-primary. Over-investigation (high information) is actively penalized in emergencies.",
    },
}


def _derive_weights(priority: List[str]) -> Dict[str, float]:
    """
    Derive weights from a priority ordering via geometric decay.
    Deterministic function of priority → weights. No hand-tuning.
    """
    base = 1.0
    decay = 0.75
    raw = {dim: base * (decay ** i) for i, dim in enumerate(priority)}
    total = sum(raw.values())
    return {k: round(v / total, 2) for k, v in raw.items()}


TASK_VALUE_WEIGHTS = {
    task_type: _derive_weights(obj["priority"])
    for task_type, obj in TASK_OBJECTIVES.items()
}

DEFAULT_WEIGHTS = _derive_weights(["outcome", "information", "safety", "cost"])


# ============================================================
# Non-linear Safety Penalty (Sigmoid + Piecewise)
# ============================================================

# Safety thresholds per task type — below this, penalty kicks in
SAFETY_THRESHOLDS = {
    "diagnostic_uncertainty": 0.4,
    "conflicting_evidence": 0.4,
    "treatment_tradeoff": 0.3,
    "patient_non_compliance": 0.3,
    "drug_safety_risk": 0.5,       # Stricter — drug errors are catastrophic
    "emergency_triage": 0.5,       # Stricter — emergency errors are catastrophic
}

DEFAULT_SAFETY_THRESHOLD = 0.4


def safety_penalty(safety: float, task_type: str) -> float:
    """
    Non-linear safety penalty using sigmoid near threshold + piecewise below.

    Properties:
    - safety >> threshold: penalty ≈ 0 (safe, no concern)
    - safety ≈ threshold: smooth gradient via sigmoid (differentiable)
    - safety << threshold: steep penalty that increases with severity

    Formula:
        if safety >= threshold + margin:
            return 0.0
        elif safety >= threshold:
            # Sigmoid zone: smooth transition
            return -alpha * sigmoid((threshold - safety) / tau)
        else:
            # Below threshold: heavy penalty + severity scaling
            return -(alpha + beta * (threshold - safety))

    Args:
        safety: Safety score (0-1)
        task_type: Task type (determines threshold)

    Returns:
        Penalty (negative float, 0.0 when safe)
    """
    threshold = SAFETY_THRESHOLDS.get(task_type, DEFAULT_SAFETY_THRESHOLD)

    if safety >= threshold + 0.2:
        # Well above threshold: no penalty
        return 0.0
    elif safety >= threshold:
        # Sigmoid zone: smooth gradient, differentiable
        # As safety drops toward threshold, penalty increases smoothly
        tau = 0.1  # Controls sharpness of sigmoid
        alpha = 0.1  # Maximum penalty in sigmoid zone
        z = (threshold - safety) / tau
        return -alpha * (1.0 / (1.0 + math.exp(-z)))
    else:
        # Below threshold: severe penalty + severity scaling
        # safety=0 → very bad, safety=threshold → bad
        severity = threshold - safety
        beta = 0.5  # Severity scaling
        base_penalty = 0.1
        return -(base_penalty + beta * severity)


# ============================================================
# Efficiency Bonus (for "shortcut correct")
# ============================================================

def efficiency_bonus(outcome: float, cost: float) -> float:
    """
    Bonus for agents that achieve good outcomes with low cost.

    "Don't penalize efficiently correct" — if agent gets the right answer
    quickly, it should be rewarded, not penalized for not asking enough questions.

    Args:
        outcome: Outcome score (0-1)
        cost: Cost score (0-1, higher = more costly)

    Returns:
        Bonus (positive float)
    """
    if outcome >= 0.8 and cost <= 0.3:
        # Good outcome + low cost = efficient shortcut
        return 0.05 * outcome * (1.0 - cost)
    return 0.0


# ============================================================
# Canonical Dimension Mapping
# ============================================================

DIMENSION_MAPPING = {
    "diagnosis_accuracy": "outcome",
    "treatment_correctness": "outcome",
    "overall_outcome": "outcome",
    "outcome": "outcome",

    "evidence_first": "information",
    "differential_quality": "information",
    "uncertainty_handling": "information",
    "info_seeking": "information",
    "patient_communication": "information",
    "information": "information",
    "process": "information",

    "drug_interaction_score": "safety",
    "red_flag_score": "safety",
    "overall_safety": "safety",
    "safety": "safety",

    "efficiency": "cost",
    "turn_efficiency": "cost",
    "cost": "cost",
}


def map_to_canonical(scores: Dict[str, float]) -> Dict[str, float]:
    """Map arbitrary evaluation scores to the 4 canonical dimensions."""
    canonical: Dict[str, List[float]] = {
        "outcome": [], "information": [], "safety": [], "cost": [],
    }
    for name, value in scores.items():
        dim = DIMENSION_MAPPING.get(name)
        if dim and dim in canonical:
            canonical[dim].append(value)
    result = {}
    for dim, values in canonical.items():
        result[dim] = sum(values) / len(values) if values else 0.5
    return result


# ============================================================
# The Unified Value Function (v2.6 — non-linear)
# ============================================================

def get_value_weights(task_type: str) -> Dict[str, float]:
    """Get task-conditioned value function weights."""
    return TASK_VALUE_WEIGHTS.get(task_type, DEFAULT_WEIGHTS)


def compute_value(
    task_type: str,
    outcome: float = 0.0,
    information: float = 0.0,
    safety: float = 0.0,
    cost: float = 0.0,
) -> float:
    """
    v2.6 Unified value function with non-linear safety.

    value = linear_base(w, scores)
          + safety_penalty(safety, task_type)    ← non-linear (sigmoid + piecewise)
          + efficiency_bonus(outcome, cost)      ← rewards efficient correct answers

    The linear base captures the task-conditioned priority.
    The safety penalty captures the non-linear risk: near-miss is different from catastrophe.
    The efficiency bonus captures "don't penalize efficiently correct".
    """
    w = get_value_weights(task_type)

    # Linear base
    linear = (
        w.get("outcome", 0.25) * outcome
        + w.get("information", 0.25) * information
        + w.get("safety", 0.25) * safety
        - w.get("cost", 0.25) * cost
    )

    # Non-linear safety penalty (negative)
    safe_pen = safety_penalty(safety, task_type)

    # Efficiency bonus (positive)
    eff_bonus = efficiency_bonus(outcome, cost)

    value = linear + safe_pen + eff_bonus
    return max(0.0, min(1.0, value))


def compute_total_score(
    task_type: str,
    outcome_score: float,
    process_score: float,
    safety_score: float,
) -> float:
    """Backward-compatible API."""
    return compute_value(
        task_type,
        outcome=outcome_score,
        information=process_score,
        safety=safety_score,
        cost=0.0,
    )


# Legacy aliases
get_eval_weights = get_value_weights


# ============================================================
# Inspection API
# ============================================================

def get_weight_derivation(task_type: str) -> Dict[str, Any]:
    """Full derivation trace for a task type's weights."""
    obj = TASK_OBJECTIVES.get(task_type)
    if not obj:
        return {"error": f"Unknown task type: {task_type}"}

    weights = get_value_weights(task_type)
    threshold = SAFETY_THRESHOLDS.get(task_type, DEFAULT_SAFETY_THRESHOLD)

    return {
        "task_type": task_type,
        "objective": obj["objective"],
        "priority_ordering": obj["priority"],
        "rationale": obj["rationale"],
        "derived_weights": weights,
        "safety_threshold": threshold,
        "safety_model": "sigmoid(piecewise) — smooth gradient near threshold, steep below",
        "derivation_method": "geometric_decay(base=1.0, decay=0.75) → normalize + nonlinear_safety",
    }
