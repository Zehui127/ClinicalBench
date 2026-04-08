#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lab Generator — Generate lab results with scenario-aware constraints.

Reuses clinical_constraints.py for constraint enforcement, but adds
scenario-specific perturbation (conflicting results, missing panels, etc.).
"""

import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ..scenario_engine.scenario_schema import ScenarioSpec


@dataclass
class LabResult:
    """A single lab test result."""
    test_name: str
    value: Any
    unit: str = ""
    reference_range: str = ""
    flag: str = ""  # "normal", "high", "low", "critical"
    interpretation: str = ""


@dataclass
class LabSet:
    """Complete lab results for a scenario."""
    results: List[LabResult] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    missing_panels: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def to_dict_list(self) -> List[Dict[str, Any]]:
        return [
            {
                "test": r.test_name,
                "value": r.value,
                "unit": r.unit,
                "reference_range": r.reference_range,
                "flag": r.flag,
            }
            for r in self.results
        ]


class LabGenerator:
    """Generate lab results controlled by scenario parameters."""

    def __init__(self, clinical_kb):
        self.kb = clinical_kb

    def generate(
        self,
        disease: str,
        scenario: ScenarioSpec,
        seed: Optional[int] = None,
    ) -> LabSet:
        """
        Generate lab results for the disease-scenario pair.

        For conflicting_evidence scenarios, introduces deliberate conflicts.
        For L3, may produce partial/missing panels.
        """
        if seed is not None:
            random.seed(seed)

        # Get disease-specific lab panel
        panel = self.kb.get_lab_panel(disease)
        if not panel:
            return LabSet()

        results = []
        conflicts = []
        missing = []

        for test_spec in panel:
            test_name = test_spec.get("test_name", test_spec.get("name", ""))
            if not test_name:
                continue

            # Generate result
            result = self._generate_single_result(test_name, disease, scenario)
            results.append(result)

        # Introduce conflicts for conflicting_evidence scenarios
        if scenario.task_type == "conflicting_evidence" and len(results) >= 2:
            conflicts = self._introduce_conflicts(results, scenario)

        # Introduce missing panels for L3
        if scenario.difficulty == "L3" and scenario.information_completeness == "minimal":
            n_remove = min(2, max(1, len(results) // 3))
            to_remove = random.sample(range(len(results)), n_remove)
            for idx in sorted(to_remove, reverse=True):
                missing.append(results[idx].test_name)
                results.pop(idx)

        return LabSet(
            results=results,
            conflicts=conflicts,
            missing_panels=missing,
        )

    def _generate_single_result(
        self, test_name: str, disease: str, scenario: ScenarioSpec
    ) -> LabResult:
        """Generate a single lab result with scenario-appropriate perturbation."""
        # Get reference ranges
        ranges = self.kb.get_lab_ranges(test_name)

        if ranges:
            low = ranges.get("low", ranges.get("min", 0))
            high = ranges.get("high", ranges.get("max", 100))
            unit = ranges.get("unit", "")

            # Generate value — bias toward abnormal for the disease
            if random.random() < 0.7:  # 70% chance of abnormal result
                # Abnormal: outside reference range
                direction = random.choice(["high", "low"])
                margin = (high - low) * random.uniform(0.05, 0.3)
                if direction == "high":
                    value = high + margin
                    flag = "high"
                else:
                    value = max(0, low - margin)
                    flag = "low"
            else:
                # Normal result
                value = random.uniform(low, high)
                flag = "normal"

            value = round(value, 2) if isinstance(value, float) else value

            return LabResult(
                test_name=test_name,
                value=value,
                unit=unit,
                reference_range=f"{low}-{high}",
                flag=flag,
                interpretation=self.kb.interpret_lab_value(test_name, value) or "",
            )

        # No reference range available — use generic
        return LabResult(
            test_name=test_name,
            value="pending",
            unit="",
            reference_range="N/A",
            flag="normal",
        )

    def _introduce_conflicts(
        self, results: List[LabResult], scenario: ScenarioSpec
    ) -> List[Dict[str, Any]]:
        """Introduce conflicting results for conflicting_evidence scenarios."""
        if len(results) < 2:
            return []

        conflicts = []
        # Pick two results and make them contradictory
        idx_a, idx_b = random.sample(range(len(results)), 2)

        # Make result B contradict result A
        result_b = results[idx_b]
        if result_b.flag == "high":
            # Override to normal (contradicts the disease)
            ranges = self.kb.get_lab_ranges(result_b.test_name)
            if ranges:
                low = ranges.get("low", 0)
                high = ranges.get("high", 100)
                result_b.value = round(random.uniform(low, high), 2)
                result_b.flag = "normal"
        elif result_b.flag == "low":
            result_b.value = "normal"
            result_b.flag = "normal"
        else:
            # Make it abnormally high to conflict with other normal results
            ranges = self.kb.get_lab_ranges(result_b.test_name)
            if ranges:
                high = ranges.get("high", 100)
                result_b.value = round(high * 1.3, 2)
                result_b.flag = "high"

        conflicts.append({
            "test_a": results[idx_a].test_name,
            "test_b": result_b.test_name,
            "conflict_type": scenario.scenario_params.get(
                "conflict_type", "lab_vs_history"
            ),
        })

        return conflicts
