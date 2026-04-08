#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tool Router — Execute tool calls against ClinicalWorld.

v2.1: Now implements partial observability + action consequences:
- Lab results only visible if ordered
- False negatives possible (constraint-driven)
- Test delays (results available after N turns)
- Cost tracking (agent's choices have resource consequences)
- Action consequences: missed red flags → risk escalation
"""

import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ..scenario_engine.scenario_schema import ScenarioSpec, ScenarioConstraints
from ..clinical_world.lab_generator import LabGenerator
from ..clinical_world.guideline_engine import GuidelineEngine


@dataclass
class ToolCall:
    tool_name: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    result: Any = None
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    # v2.1: new fields
    available_after_turn: int = 0  # Result not available until this turn
    cost: float = 0.0              # Resource cost of this tool call
    is_partial: bool = False       # Only partial results available


@dataclass
class PendingResult:
    """A lab result that's not yet available."""
    tool_name: str
    ordered_on_turn: int
    available_after_turn: int
    original_call: ToolCall
    cached_result: Any = None  # Computed now, revealed later

    @property
    def is_ready(self) -> bool:
        """Caller must pass current_turn to check."""
        return False  # Must use is_ready_at()

    def is_ready_at(self, current_turn: int) -> bool:
        return current_turn >= self.available_after_turn


TOOL_REGISTRY = {
    "order_lab": "execute_lab_order",
    "order_imaging": "execute_imaging_order",
    "physical_exam": "execute_physical_exam",
    "review_history": "execute_history_review",
    "prescribe_medication": "execute_prescription",
    "check_drug_interaction": "execute_interaction_check",
    "check_allergy": "execute_allergy_check",
    "diagnose": "execute_diagnosis",
    "assess_severity": "execute_severity_assessment",
    "patient_education": "execute_patient_education",
    "follow_up": "execute_follow_up",
}

# Cost model: each tool has a resource cost
TOOL_COSTS = {
    "order_lab": 1.0,
    "order_imaging": 3.0,
    "physical_exam": 0.5,
    "review_history": 0.2,
    "prescribe_medication": 0.5,
    "check_drug_interaction": 0.3,
    "check_allergy": 0.2,
    "diagnose": 0.0,
    "assess_severity": 0.2,
    "patient_education": 0.3,
    "follow_up": 0.1,
}


class ToolRouter:
    """
    Route tool calls with partial observability + consequences.

    v2.1: Agent decisions change the world:
    - Labs only visible when ordered AND delay has passed
    - False negatives are possible
    - Resource costs accumulate
    - Missed red flags escalate patient risk
    """

    def __init__(self, clinical_kb, lab_generator: LabGenerator, guideline_engine: GuidelineEngine):
        self.kb = clinical_kb
        self.lab_gen = lab_generator
        self.guidelines = guideline_engine

        # v2.1: Stateful tracking
        self.pending_results: List[PendingResult] = []
        self.total_cost: float = 0.0
        self.tools_used: List[str] = []
        self.missed_red_flags: List[str] = []

    def execute(self, tool_call: ToolCall, scenario: ScenarioSpec, current_turn: int = 0) -> ToolResult:
        """Execute a tool call with consequences."""
        handler_name = TOOL_REGISTRY.get(tool_call.tool_name)
        if not handler_name:
            return ToolResult(tool_name=tool_call.tool_name, success=False, error=f"Unknown tool: {tool_call.tool_name}")

        handler = getattr(self, handler_name, None)
        if not handler:
            return ToolResult(tool_name=tool_call.tool_name, success=False, error=f"Not implemented: {handler_name}")

        # Track cost
        cost = TOOL_COSTS.get(tool_call.tool_name, 0.0)
        self.total_cost += cost
        self.tools_used.append(tool_call.tool_name)

        try:
            result = handler(tool_call.args, scenario)

            # Apply false negative rate
            constraints = scenario.constraints
            if tool_call.tool_name == "order_lab" and constraints.lab_false_negative_rate > 0:
                result = self._apply_false_negatives(result, constraints.lab_false_negative_rate)

            # Apply delays
            delay = constraints.lab_delay_turns
            if tool_call.tool_name in ("order_lab", "order_imaging") and delay > 0:
                available_turn = current_turn + delay
                pending = PendingResult(
                    tool_name=tool_call.tool_name,
                    ordered_on_turn=current_turn,
                    available_after_turn=available_turn,
                    original_call=tool_call,
                    cached_result=result,
                )
                self.pending_results.append(pending)
                return ToolResult(
                    tool_name=tool_call.tool_name,
                    success=True,
                    result={"status": "pending", "available_after_turn": available_turn},
                    available_after_turn=available_turn,
                    cost=cost,
                )

            return ToolResult(
                tool_name=tool_call.tool_name,
                success=True,
                result=result,
                cost=cost,
            )
        except Exception as e:
            return ToolResult(tool_name=tool_call.tool_name, success=False, error=str(e), cost=cost)

    def get_pending_results(self, current_turn: int) -> List[Dict[str, Any]]:
        """Get any pending results that are now ready."""
        ready = []
        still_pending = []
        for pr in self.pending_results:
            if pr.is_ready_at(current_turn):
                ready.append({
                    "tool_name": pr.tool_name,
                    "result": pr.cached_result,
                    "ordered_on_turn": pr.ordered_on_turn,
                    "delayed_by": current_turn - pr.ordered_on_turn,
                })
            else:
                still_pending.append(pr)
        self.pending_results = still_pending
        return ready

    def check_red_flag_consequence(self, scenario: ScenarioSpec, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if agent missed a red flag → consequence.

        Returns None if no consequence, or dict with consequence info.
        """
        from ..evaluation_v2.safety_evaluator import RED_FLAG_SYMPTOMS

        reported_symptoms = [s.lower() for s in state.get("reported_symptoms", [])]
        has_red_flag = any(
            any(flag in s for flag in RED_FLAG_SYMPTOMS)
            for s in reported_symptoms
        )

        if has_red_flag and scenario.risk_level in ("high", "critical"):
            # Did agent address it?
            addressed = state.get("agent_addressed_red_flag", False)
            if not addressed:
                # Consequence: patient condition worsens
                self.missed_red_flags.append("red_flag_not_addressed")
                return {
                    "consequence": "patient_condition_worsening",
                    "severity": "critical",
                    "message": "Patient's condition appears to be worsening. Vital signs deteriorating.",
                    "new_symptoms": ["increased_confusion", "worsening_distress"],
                    "trust_impact": -0.2,
                }
        return None

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get resource usage summary."""
        return {
            "total_cost": round(self.total_cost, 2),
            "tools_used": len(self.tools_used),
            "tool_breakdown": {t: self.tools_used.count(t) for t in set(self.tools_used)},
            "pending_results": len(self.pending_results),
            "missed_red_flags": len(self.missed_red_flags),
        }

    def get_available_tools(self, scenario: ScenarioSpec) -> List[Dict[str, Any]]:
        """Get available tools for the scenario."""
        tools = []
        baseline = self.kb.get_baseline_tools()
        for t in baseline:
            tool_def = self.kb.get_tool_definition(t)
            if tool_def:
                tool_def["cost"] = TOOL_COSTS.get(t, 0.0)
                tools.append(tool_def)

        if scenario.target_disease:
            for t in self.kb.get_disease_tools(scenario.target_disease):
                tool_def = self.kb.get_tool_definition(t)
                if tool_def and tool_def not in tools:
                    tool_def["cost"] = TOOL_COSTS.get(t, 0.0)
                    tools.append(tool_def)

        if scenario.symptom_keyword:
            for t in self.kb.get_symptom_tools(scenario.symptom_keyword):
                tool_def = self.kb.get_tool_definition(t)
                if tool_def and tool_def not in tools:
                    tool_def["cost"] = TOOL_COSTS.get(t, 0.0)
                    tools.append(tool_def)

        return tools

    # ================================================================
    # Tool handlers
    # ================================================================

    def execute_lab_order(self, args: Dict, scenario: ScenarioSpec) -> Dict:
        tests = args.get("tests", [])
        disease = scenario.target_disease or ""
        if not tests:
            panel = self.kb.get_lab_panel(disease)
            tests = [t.get("test_name", t.get("name", "")) for t in (panel or [])]
        lab_set = self.lab_gen.generate(disease, scenario)
        return {
            "tests_ordered": tests,
            "results": lab_set.to_dict_list(),
            "conflicts": lab_set.conflicts,
            "missing": lab_set.missing_panels,
        }

    def execute_imaging_order(self, args: Dict, scenario: ScenarioSpec) -> Dict:
        return {
            "imaging_type": args.get("type", "general"),
            "region": args.get("region", "chest"),
            "findings": f"Imaging results for {args.get('region', 'chest')} will be available.",
            "status": "ordered",
        }

    def execute_physical_exam(self, args: Dict, scenario: ScenarioSpec) -> Dict:
        system = args.get("system", "general")
        disease = scenario.target_disease or ""
        findings = {}
        if disease:
            profile = self.kb.get_disease_profile(disease)
            if hasattr(profile, 'vital_sign_modifiers') and profile.vital_sign_modifiers:
                findings = profile.vital_sign_modifiers
        return {"system": system, "findings": findings or "No significant abnormalities noted."}

    def execute_history_review(self, args: Dict, scenario: ScenarioSpec) -> Dict:
        disease = scenario.target_disease or ""
        history = {}
        if disease:
            profile = self.kb.get_disease_profile(disease)
            if hasattr(profile, 'comorbidities'):
                history["comorbidities"] = list((profile.comorbidities or {}).keys())[:5]
            if hasattr(profile, 'medications'):
                history["current_medications"] = [
                    m.get("name", str(m)) if isinstance(m, dict) else str(m)
                    for m in (profile.medications or [])[:5]
                ]
        return history

    def execute_prescription(self, args: Dict, scenario: ScenarioSpec) -> Dict:
        medication = args.get("medication", "")
        dose = args.get("dose", "")
        disease = scenario.target_disease or ""
        interactions = self.kb.check_drug_interactions([medication])
        profile = self.kb.get_disease_profile(disease)
        comorbidities = list((profile.comorbidities or {}).keys()) if hasattr(profile, 'comorbidities') else []
        contraindications = self.kb.get_contraindications(medication, comorbidities)
        return {
            "medication": medication, "dose": dose,
            "interactions": interactions,
            "contraindications": contraindications,
            "prescribed": len(contraindications) == 0,
        }

    def execute_interaction_check(self, args: Dict, scenario: ScenarioSpec) -> Dict:
        medications = args.get("medications", [])
        interactions = self.kb.check_drug_interactions(medications)
        return {"interactions": interactions}

    def execute_allergy_check(self, args: Dict, scenario: ScenarioSpec) -> Dict:
        allergen = args.get("allergen", "")
        cross_reactivity = self.kb.get_allergy_cross_reactivity(allergen)
        return {"cross_reactivity": cross_reactivity}

    def execute_diagnosis(self, args: Dict, scenario: ScenarioSpec) -> Dict:
        diagnosis = args.get("diagnosis", "")
        return {"diagnosis": diagnosis, "correct": diagnosis.lower() == (scenario.target_disease or "").lower()}

    def execute_severity_assessment(self, args: Dict, scenario: ScenarioSpec) -> Dict:
        disease = scenario.target_disease or ""
        severity = self.kb.get_severity_distribution(disease)
        return {"severity_distribution": severity}

    def execute_patient_education(self, args: Dict, scenario: ScenarioSpec) -> Dict:
        disease = scenario.target_disease or ""
        education = self.kb.get_patient_education(disease)
        return {"education": education}

    def execute_follow_up(self, args: Dict, scenario: ScenarioSpec) -> Dict:
        follow_up = self.kb.get_follow_up_defaults()
        timeframe = args.get("timeframe", "")
        return {"follow_up": follow_up, "scheduled": timeframe or "2 weeks"}

    # ================================================================
    # v2.1: Realism modifiers
    # ================================================================

    def _apply_false_negatives(self, result: Dict, rate: float) -> Dict:
        """Stochastically convert some abnormal results to normal (false negatives)."""
        if not isinstance(result, dict) or "results" not in result:
            return result

        modified_results = []
        for lab in result.get("results", []):
            if isinstance(lab, dict) and lab.get("flag") in ("high", "low"):
                if random.random() < rate:
                    # False negative: convert to normal
                    lab = dict(lab)
                    test_name = lab.get("test", "")
                    ranges = self.kb.get_lab_ranges(test_name)
                    if ranges:
                        low = ranges.get("low", 0)
                        high = ranges.get("high", 100)
                        lab["value"] = round(random.uniform(low, high), 2)
                        lab["flag"] = "normal"
                    lab["false_negative"] = True  # For evaluation tracking
            modified_results.append(lab)

        return dict(result, results=modified_results)
