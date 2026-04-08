#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Risk Model — Maps disease + presentation to clinical risk level.

Used by ScenarioGenerator to set scenario risk parameters.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


# Emergency indicators that automatically escalate risk
EMERGENCY_INDICATORS = [
    "chest pain", "shortness of breath at rest", "loss of consciousness",
    "severe headache", "sudden weakness", "sudden numbness",
    "difficulty breathing", "severe bleeding", "seizure",
    "suicidal ideation", "confusion", "fever over 40",
    "blood pressure over 180/120", "heart rate over 150",
    "oxygen saturation below 90", "anaphylaxis",
]

# Disease-specific risk multipliers
DISEASE_RISK_MULTIPLIERS: Dict[str, float] = {
    "stroke": 2.0,
    "myocardial infarction": 2.0,
    "pulmonary embolism": 2.0,
    "meningitis": 2.0,
    "sepsis": 2.0,
    "anaphylaxis": 2.0,
    "heart failure": 1.8,
    "coronary artery disease": 1.7,
    "atrial fibrillation": 1.5,
    "copd": 1.4,
    "pneumonia": 1.4,
    "asthma": 1.3,
    "type 2 diabetes": 1.0,
    "hypertension": 1.0,
    "hyperlipidemia": 0.8,
    "gerd": 0.7,
    "ibs": 0.6,
    "migraine": 0.7,
    "anxiety disorder": 0.6,
}

# Severity keywords that escalate risk
SEVERITY_ESCALATORS = {
    "acute": 0.3,
    "sudden onset": 0.4,
    "progressive": 0.2,
    "severe": 0.3,
    "worsening": 0.2,
    "uncontrollable": 0.3,
    "persistent": 0.1,
    "recurrent": 0.1,
}


@dataclass
class RiskAssessment:
    """Result of risk evaluation."""
    risk_level: str
    risk_score: float  # 0.0-1.0
    factors: List[str] = field(default_factory=list)
    emergency_indicators: List[str] = field(default_factory=list)
    time_sensitive: bool = False

    def __post_init__(self):
        self.time_sensitive = self.risk_level in ("high", "critical")


class RiskModel:
    """Assess clinical risk for scenario generation."""

    def assess(
        self,
        disease_name: str,
        symptoms: List[str],
        severity: str = "moderate",
        patient_age: int = 50,
        comorbidities: Optional[List[str]] = None,
    ) -> RiskAssessment:
        """
        Calculate risk level for a clinical presentation.

        Args:
            disease_name: The target disease
            symptoms: Presenting symptoms
            severity: Reported severity (mild/moderate/severe)
            patient_age: Patient age
            comorbidities: List of comorbid conditions

        Returns:
            RiskAssessment with risk level and contributing factors
        """
        base_score = 0.3  # Start at moderate
        factors = []
        emergencies = []

        # 1. Disease-specific risk multiplier
        mult = 1.0
        for disease_key, multiplier in DISEASE_RISK_MULTIPLIERS.items():
            if disease_key in disease_name.lower():
                mult = max(mult, multiplier)
                break
        base_score *= mult
        if mult > 1.5:
            factors.append(f"High-risk disease: {disease_name}")

        # 2. Emergency symptom check
        for indicator in EMERGENCY_INDICATORS:
            for symptom in symptoms:
                if indicator in symptom.lower() or symptom.lower() in indicator:
                    emergencies.append(indicator)
                    base_score += 0.2

        # 3. Severity escalation
        severity_map = {"mild": 0.0, "moderate": 0.1, "severe": 0.3}
        base_score += severity_map.get(severity, 0.1)

        # 4. Age factor (very young or very old = higher risk)
        if patient_age < 5 or patient_age > 75:
            base_score += 0.15
            factors.append(f"Age risk factor: {patient_age}")
        elif patient_age > 65:
            base_score += 0.08

        # 5. Comorbidity burden
        if comorbidities:
            n_comorbid = len(comorbidities)
            if n_comorbid >= 3:
                base_score += 0.2
                factors.append(f"Multiple comorbidities ({n_comorbid})")
            elif n_comorbid >= 1:
                base_score += 0.1

        # Clamp to [0, 1]
        base_score = min(1.0, max(0.0, base_score))

        # Map score to risk level
        if base_score >= 0.8:
            risk_level = "critical"
        elif base_score >= 0.6:
            risk_level = "high"
        elif base_score >= 0.35:
            risk_level = "moderate"
        else:
            risk_level = "low"

        return RiskAssessment(
            risk_level=risk_level,
            risk_score=round(base_score, 3),
            factors=factors,
            emergency_indicators=emergencies,
        )
