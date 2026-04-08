#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process Evaluator — Strategy-aware reasoning evaluation.

v2.1: Evaluation now depends on detected strategy:
- evidence_first: requires labs before diagnosis
- empirical_then_confirm: allows early treatment, delayed labs
- rule_out_critical: prioritizes emergency exclusion
- No single "standard path" — multiple valid strategies exist
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from ..interaction_engine.state_manager import ConversationState
from ..scenario_engine.scenario_schema import ScenarioSpec
from ..clinical_world.causal_graph import ConditionGraph


# Strategy-specific evaluation criteria
STRATEGY_CRITERIA = {
    "evidence_first": {
        "requires_labs_before_diagnosis": True,
        "allows_early_treatment": False,
        "min_questions_before_diagnosis": 3,
        "values": {
            "evidence_first": 0.30,
            "differential_quality": 0.25,
            "uncertainty_handling": 0.15,
            "info_seeking": 0.15,
            "patient_communication": 0.10,
            "efficiency": 0.05,
        },
    },
    "empirical_then_confirm": {
        "requires_labs_before_diagnosis": False,
        "allows_early_treatment": True,
        "min_questions_before_diagnosis": 1,
        "values": {
            "evidence_first": 0.10,
            "differential_quality": 0.15,
            "uncertainty_handling": 0.15,
            "info_seeking": 0.20,
            "patient_communication": 0.15,
            "efficiency": 0.25,  # Efficiency matters more here
        },
    },
    "rule_out_critical": {
        "requires_labs_before_diagnosis": False,
        "allows_early_treatment": True,
        "min_questions_before_diagnosis": 1,
        "values": {
            "evidence_first": 0.15,
            "differential_quality": 0.10,
            "uncertainty_handling": 0.10,
            "info_seeking": 0.15,
            "patient_communication": 0.10,
            "efficiency": 0.40,  # Speed is paramount
        },
    },
    "thorough": {
        "requires_labs_before_diagnosis": True,
        "allows_early_treatment": False,
        "min_questions_before_diagnosis": 4,
        "values": {
            "evidence_first": 0.25,
            "differential_quality": 0.30,
            "uncertainty_handling": 0.15,
            "info_seeking": 0.20,
            "patient_communication": 0.05,
            "efficiency": 0.05,
        },
    },
    # Penalized strategies
    "shotgun": {
        "requires_labs_before_diagnosis": False,
        "allows_early_treatment": False,
        "min_questions_before_diagnosis": 1,
        "values": {
            "evidence_first": 0.05,
            "differential_quality": 0.10,
            "uncertainty_handling": 0.10,
            "info_seeking": 0.05,
            "patient_communication": 0.10,
            "efficiency": -0.40,  # Penalized
        },
    },
    "premature_closure": {
        "requires_labs_before_diagnosis": False,
        "allows_early_treatment": False,
        "min_questions_before_diagnosis": 1,
        "values": {
            "evidence_first": -0.30,  # Heavily penalized
            "differential_quality": 0.05,
            "uncertainty_handling": 0.10,
            "info_seeking": -0.20,
            "patient_communication": 0.10,
            "efficiency": 0.25,
        },
    },
}

DEFAULT_WEIGHTS = {
    "evidence_first": 0.25,
    "differential_quality": 0.20,
    "uncertainty_handling": 0.15,
    "info_seeking": 0.20,
    "patient_communication": 0.10,
    "efficiency": 0.10,
}


@dataclass
class ProcessReport:
    """Result of process evaluation."""
    evidence_first: float = 0.0
    differential_quality: float = 0.0
    uncertainty_handling: float = 0.0
    info_seeking: float = 0.0
    patient_communication: float = 0.0
    efficiency: float = 0.0
    overall_score: float = 0.0
    notes: List[str] = field(default_factory=list)
    # v2.1: strategy context
    strategy_used: str = ""
    strategy_appropriate: bool = True
    # v2.4: causal reasoning score
    causal_score: float = 1.0
    causal_details: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_score(self) -> float:
        """Alias for overall_score (compatibility)."""
        return self.overall_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_first": self.evidence_first,
            "differential_quality": self.differential_quality,
            "uncertainty_handling": self.uncertainty_handling,
            "info_seeking": self.info_seeking,
            "patient_communication": self.patient_communication,
            "efficiency": self.efficiency,
            "overall_score": self.overall_score,
            "causal_score": self.causal_score,
            "notes": self.notes,
            "strategy_used": self.strategy_used,
            "strategy_appropriate": self.strategy_appropriate,
        }


class ProcessEvaluator:
    """
    Strategy-aware process evaluation.

    v2.1: Evaluation depends on detected strategy, not a single standard path.
    """

    def evaluate(
        self,
        scenario: ScenarioSpec,
        state: ConversationState,
        strategy: Optional[str] = None,
    ) -> ProcessReport:
        """Evaluate reasoning process with strategy awareness."""
        report = ProcessReport()
        report.strategy_used = strategy or "undefined"

        # Get strategy-specific criteria
        criteria = STRATEGY_CRITERIA.get(strategy, {})
        weights = criteria.get("values", DEFAULT_WEIGHTS)
        report.strategy_appropriate = self._is_strategy_appropriate(strategy, scenario)

        # Evaluate dimensions
        report.evidence_first = self._eval_evidence_first(state, criteria, report)
        report.differential_quality = self._eval_differentials(state, scenario, report)
        report.uncertainty_handling = self._eval_uncertainty(state, scenario, report)
        report.info_seeking = self._eval_info_seeking(state, scenario, report)
        report.patient_communication = self._eval_communication(state, report)
        report.efficiency = self._eval_efficiency(state, report)

        # Strategy-weighted overall score
        raw_score = (
            weights.get("evidence_first", 0.25) * max(0, report.evidence_first) +
            weights.get("differential_quality", 0.20) * max(0, report.differential_quality) +
            weights.get("uncertainty_handling", 0.15) * max(0, report.uncertainty_handling) +
            weights.get("info_seeking", 0.20) * max(0, report.info_seeking) +
            weights.get("patient_communication", 0.10) * max(0, report.patient_communication) +
            weights.get("efficiency", 0.10) * max(0, report.efficiency)
        )

        # Strategy appropriateness bonus/penalty
        if not report.strategy_appropriate:
            raw_score *= 0.7  # 30% penalty for wrong strategy

        report.overall_score = max(0.0, min(1.0, raw_score))

        # v2.4: Causal reasoning evaluation
        report.causal_score, report.causal_details = self._evaluate_causal_reasoning(
            scenario, state
        )

        return report

    def _is_strategy_appropriate(self, strategy: Optional[str], scenario: ScenarioSpec) -> bool:
        """Check if strategy is appropriate for the scenario type."""
        appropriate_map = {
            "diagnostic_uncertainty": ["evidence_first", "thorough", "empirical_then_confirm"],
            "conflicting_evidence": ["evidence_first", "thorough"],
            "treatment_tradeoff": ["evidence_first", "empirical_then_confirm", "thorough"],
            "patient_non_compliance": ["evidence_first", "empirical_then_confirm"],
            "drug_safety_risk": ["evidence_first", "rule_out_critical"],
            "emergency_triage": ["rule_out_critical", "evidence_first"],
        }
        ok_strategies = appropriate_map.get(scenario.task_type, [])
        if strategy in ("shotgun", "premature_closure"):
            return False
        return strategy in ok_strategies if ok_strategies else True

    def _eval_evidence_first(
        self, state: ConversationState, criteria: Dict, report: ProcessReport
    ) -> float:
        """Evaluate evidence-first approach with strategy awareness."""
        requires_labs = criteria.get("requires_labs_before_diagnosis", True)
        min_questions = criteria.get("min_questions_before_diagnosis", 3)

        diag_turn = None
        first_evidence_turn = None

        for turn in state.turns:
            if turn.action_type == "diagnose" and diag_turn is None:
                diag_turn = turn.turn_number
            if turn.action_type in ("ask_question", "call_tool") and first_evidence_turn is None:
                first_evidence_turn = turn.turn_number

        if diag_turn is None:
            if first_evidence_turn:
                report.notes.append("Gathered evidence but no diagnosis made")
                return 0.5
            report.notes.append("No evidence gathered and no diagnosis")
            return 0.0

        if first_evidence_turn and first_evidence_turn < diag_turn:
            # Check if enough questions were asked
            questions_before = sum(
                1 for t in state.turns
                if t.action_type == "ask_question" and t.turn_number < diag_turn
            )
            if questions_before >= min_questions:
                report.notes.append(f"Evidence gathered before diagnosis ({questions_before} questions)")
                return 1.0
            elif questions_before >= min_questions - 1:
                return 0.7
            else:
                report.notes.append(f"Insufficient questions before diagnosis ({questions_before}/{min_questions})")
                return 0.4
        else:
            report.notes.append("Diagnosed without gathering evidence first")
            return 0.1

    def _eval_differentials(
        self, state: ConversationState, scenario: ScenarioSpec, report: ProcessReport
    ) -> float:
        """Evaluate differential diagnosis quality."""
        conditions_mentioned = set()
        for turn in state.turns:
            if turn.role == "agent" and turn.action_type in ("ask_question", "diagnose"):
                content = turn.content.lower()
                if any(w in content for w in ["could be", "might be", "possible", "consider", "differential", "rule out"]):
                    conditions_mentioned.add(turn.content[:50])

        n = len(conditions_mentioned)
        if n >= 3:
            report.notes.append(f"Considered {n} alternative diagnoses")
            return min(1.0, 0.6 + n * 0.1)
        elif n >= 1:
            return 0.4
        else:
            if scenario.task_type in ("diagnostic_uncertainty", "conflicting_evidence"):
                report.notes.append("No differential diagnoses considered")
                return 0.1
            return 0.5

    def _eval_uncertainty(
        self, state: ConversationState, scenario: ScenarioSpec, report: ProcessReport
    ) -> float:
        """Evaluate uncertainty handling."""
        for turn in state.turns:
            if turn.role == "agent":
                content = turn.content.lower()
                if any(w in content for w in [
                    "uncertain", "not sure", "need more", "further",
                    "possible", "likely", "rule out", "differential",
                    "consider", "investigate",
                ]):
                    if scenario.uncertainty_level > 0.5:
                        report.notes.append("Acknowledged uncertainty")
                        return 1.0
                    return 0.7
        if scenario.uncertainty_level > 0.5:
            report.notes.append("Failed to acknowledge uncertainty")
            return 0.2
        return 0.7

    def _eval_info_seeking(
        self, state: ConversationState, scenario: ScenarioSpec, report: ProcessReport
    ) -> float:
        """Evaluate information seeking."""
        n_questions = state.total_questions
        min_q = scenario.constraints.min_required_questions

        if n_questions >= min_q:
            report.notes.append(f"Good probing: {n_questions}/{min_q} required questions")
            return min(1.0, 0.6 + (n_questions - min_q) * 0.1)
        elif n_questions >= min_q - 1:
            return 0.5
        else:
            report.notes.append(f"Insufficient probing: {n_questions}/{min_q} required questions")
            return 0.2

    def _eval_communication(self, state: ConversationState, report: ProcessReport) -> float:
        score = 0.5
        for turn in state.turns:
            if turn.role == "agent":
                content = turn.content.lower()
                if any(w in content for w in ["explain", "mean", "reason", "because"]):
                    score += 0.2
                    break
        for turn in state.turns:
            if turn.role == "agent":
                content = turn.content.lower()
                if any(w in content for w in ["understand", "sorry", "worry", "concern"]):
                    score += 0.2
                    break
        if state.patient_trust > 0.5:
            score += 0.1
        return min(1.0, score)

    def _eval_efficiency(self, state: ConversationState, report: ProcessReport) -> float:
        if state.turn_count == 0:
            return 0.0
        useful = state.total_questions + state.total_tool_calls
        total_agent = len(state.agent_turns)
        if total_agent == 0:
            return 0.0
        efficiency_ratio = useful / total_agent
        dup_penalty = min(0.3, state.duplicate_actions * 0.1)
        if state.turn_count > 20:
            dup_penalty += 0.1
        return max(0.0, min(1.0, efficiency_ratio - dup_penalty))

    # ================================================================
    # v2.4: Causal Reasoning Evaluation
    # ================================================================

    def _evaluate_causal_reasoning(
        self, scenario: ScenarioSpec, state: ConversationState
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluate whether agent's reasoning respects causal structure.

        Not just "did you get the right diagnosis?" but
        "did you reason about causes, rule-outs, and dependencies?"
        """
        # Build condition graph from scenario's ground truth
        gt = scenario.ground_truth
        all_conditions = [scenario.target_disease or ""] + gt.comorbidities
        all_conditions = [c for c in all_conditions if c]

        graph = ConditionGraph.from_conditions(all_conditions)

        # Get agent's actions as dicts
        agent_actions = [
            {
                "action_type": t.action_type,
                "content": t.content,
                "tool_name": t.tool_name,
            }
            for t in state.turns if t.role == "agent"
        ]

        # Get agent's diagnoses
        diagnoses = state.clinical.diagnoses

        if not diagnoses:
            return 1.0, {"note": "No diagnoses to evaluate causally"}

        # Evaluate causal reasoning
        result = graph.evaluate_causal_reasoning(diagnoses, agent_actions)

        return result["causal_score"], result
