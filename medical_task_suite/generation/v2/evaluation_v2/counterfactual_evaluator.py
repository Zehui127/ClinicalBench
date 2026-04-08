#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Counterfactual Regret Evaluation — How far from the reference frontier?

v2.3: Renamed from "optimal" to "reference frontier".
- Multiple reference policies (guideline, conservative, aggressive)
- Regret = max(reference_outcomes) - agent_outcome
- This is more defensible than claiming a single "optimal"
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ..scenario_engine.scenario_schema import ScenarioSpec
from .adaptive_weights import get_value_weights


@dataclass
class ReferencePolicy:
    """
    A reference (not "optimal") policy for a scenario.

    Multiple valid approaches exist in clinical medicine.
    We don't claim any single one is "optimal" — instead we define
    a frontier of reference policies and measure distance from the best one.
    """
    policy_id: str = "guideline"    # "guideline", "conservative", "aggressive"
    display_name: str = "Guideline-Based"
    description: str = ""

    min_questions_to_diagnosis: int = 2
    critical_questions: List[str] = field(default_factory=list)
    optimal_tool_sequence: List[str] = field(default_factory=list)
    optimal_turn_count: int = 4
    requires_lab: bool = True
    required_labs: List[str] = field(default_factory=list)
    must_avoid: List[str] = field(default_factory=list)

    # Expected outcomes
    expected_diagnosis_accuracy: float = 1.0
    expected_safety_score: float = 1.0
    expected_process_score: float = 0.9

    # Tradeoffs this policy makes explicit
    tradeoff_note: str = ""  # e.g., "Slower but more thorough"


@dataclass
class RegretReport:
    """Result of counterfactual regret evaluation."""
    # Agent's actual performance
    agent_outcome_score: float = 0.0
    agent_process_score: float = 0.0
    agent_safety_score: float = 0.0

    # Best reference performance (the frontier)
    best_reference_policy: str = ""
    reference_outcome_score: float = 1.0
    reference_process_score: float = 0.9
    reference_safety_score: float = 1.0

    # Regret (how far from reference frontier)
    outcome_regret: float = 0.0    # 0.0 = perfect, 1.0 = worst
    process_regret: float = 0.0
    safety_regret: float = 0.0
    total_regret: float = 0.0

    # Efficiency gap
    turn_efficiency: float = 0.0   # optimal_turns / actual_turns
    question_efficiency: float = 0.0  # min_questions / actual_questions

    # What the agent could have done better
    missed_opportunities: List[str] = field(default_factory=list)
    avoidable_errors: List[str] = field(default_factory=list)

    # All reference policies evaluated
    reference_policies: List[Dict[str, Any]] = field(default_factory=list)

    # v2.4: Step-level regret (per-turn analysis)
    step_regrets: List[Dict[str, Any]] = field(default_factory=list)
    critical_steps: List[Dict[str, Any]] = field(default_factory=list)  # Steps with highest regret
    avg_step_regret: float = 0.0

    # Overall regret grade
    regret_grade: str = ""  # "optimal", "near_optimal", "suboptimal", "poor", "critical"

    # v2.6: Frontier expansion
    frontier_bonus: float = 0.0  # Positive when agent beats reference frontier
    agent_exceeds_frontier: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_regret": round(self.total_regret, 3),
            "outcome_regret": round(self.outcome_regret, 3),
            "process_regret": round(self.process_regret, 3),
            "safety_regret": round(self.safety_regret, 3),
            "turn_efficiency": round(self.turn_efficiency, 3),
            "question_efficiency": round(self.question_efficiency, 3),
            "regret_grade": self.regret_grade,
            "best_reference_policy": self.best_reference_policy,
            "missed_opportunities": self.missed_opportunities,
            "avoidable_errors": self.avoidable_errors,
            "reference_policies": self.reference_policies,
            "avg_step_regret": round(self.avg_step_regret, 3),
            "n_critical_steps": len(self.critical_steps),
            "critical_steps": self.critical_steps[:5],
        }


class CounterfactualEvaluator:
    """
    Evaluate agent by comparing against the reference frontier.

    Instead of a single "optimal", we evaluate against multiple reference policies:
    - guideline: Standard clinical guideline approach
    - conservative: More cautious, more tests, slower diagnosis
    - aggressive: Rapid assessment, empirical treatment

    regret = max(reference_policy_outcomes) - agent_outcome

    Usage:
        evaluator = CounterfactualEvaluator()
        regret = evaluator.evaluate(scenario, agent_scores, state)
        print(f"Regret: {regret.total_regret:.2f} ({regret.regret_grade})")
    """

    def evaluate(
        self,
        scenario: ScenarioSpec,
        agent_outcome: float,
        agent_process: float,
        agent_safety: float,
        state: Dict[str, Any],
    ) -> RegretReport:
        """
        Compute regret by comparing agent against reference frontier.

        Args:
            scenario: The scenario specification
            agent_outcome: Agent's outcome score (0-1)
            agent_process: Agent's process score (0-1)
            agent_safety: Agent's safety score (0-1)
            state: Evaluation state dict

        Returns:
            RegretReport with regret analysis
        """
        report = RegretReport()

        # Compute ALL reference policies for this scenario
        reference_policies = self._compute_reference_policies(scenario, state)

        # Store agent scores
        report.agent_outcome_score = agent_outcome
        report.agent_process_score = agent_process
        report.agent_safety_score = agent_safety

        # Find best reference policy (the frontier)
        best_policy = None
        best_score = -1.0

        weights = self._get_regret_weights(scenario.task_type)

        policy_records = []
        for policy in reference_policies:
            policy_score = (
                weights["outcome"] * policy.expected_diagnosis_accuracy +
                weights["process"] * policy.expected_process_score +
                weights["safety"] * policy.expected_safety_score
            )
            policy_records.append({
                "policy_id": policy.policy_id,
                "display_name": policy.display_name,
                "expected_score": round(policy_score, 3),
                "tradeoff": policy.tradeoff_note,
            })
            if policy_score > best_score:
                best_score = policy_score
                best_policy = policy

        report.reference_policies = policy_records

        if best_policy is None:
            best_policy = ReferencePolicy()

        # Store best reference scores
        report.best_reference_policy = best_policy.display_name
        report.reference_outcome_score = best_policy.expected_diagnosis_accuracy
        report.reference_process_score = best_policy.expected_process_score
        report.reference_safety_score = best_policy.expected_safety_score

        # Compute regret with frontier expansion
        # v2.6: Agent can EXCEED reference frontier (not capped at 0 regret)
        report.outcome_regret = max(0.0, best_policy.expected_diagnosis_accuracy - agent_outcome)
        report.process_regret = max(0.0, best_policy.expected_process_score - agent_process)
        report.safety_regret = max(0.0, best_policy.expected_safety_score - agent_safety)

        # v2.6: Expand frontier with perturbation variants
        # Approximate nearby policies by adding small deltas to each reference
        frontier_score = best_score
        for policy in reference_policies:
            # Add small perturbations to each reference to approximate nearby policies
            for delta in [0.02, 0.05, -0.02]:
                perturbed = (
                    weights["outcome"] * min(1.0, policy.expected_diagnosis_accuracy + delta) +
                    weights["process"] * min(1.0, policy.expected_process_score + delta) +
                    weights["safety"] * min(1.0, policy.expected_safety_score + delta)
                )
                frontier_score = max(frontier_score, perturbed)

        # Compute agent's weighted score
        agent_score = (
            weights["outcome"] * agent_outcome +
            weights["process"] * agent_process +
            weights["safety"] * agent_safety
        )

        # v2.6: If agent beats expanded frontier, give bonus instead of penalizing
        report.agent_exceeds_frontier = False
        if agent_score > frontier_score:
            # Agent found a policy better than any reference → reward innovation
            report.frontier_bonus = min(0.1, (agent_score - frontier_score) * 0.5)
            report.total_regret = 0.0  # No regret if beating frontier
            report.agent_exceeds_frontier = True
        else:
            # Weighted total regret (distance from best reference, not "optimal")
            report.total_regret = (
                weights["outcome"] * report.outcome_regret +
                weights["process"] * report.process_regret +
                weights["safety"] * report.safety_regret
            )

        # Efficiency analysis
        actual_turns = state.get("turn_count", 1)
        actual_questions = state.get("question_count", 0)

        report.turn_efficiency = (
            best_policy.optimal_turn_count / max(1, actual_turns)
            if actual_turns > 0 else 0.0
        )
        report.question_efficiency = (
            best_policy.min_questions_to_diagnosis / max(1, actual_questions)
            if actual_questions > 0 else 0.0
        )

        # Identify missed opportunities
        report.missed_opportunities = self._find_missed_opportunities(
            scenario, state, best_policy
        )

        # Identify avoidable errors
        report.avoidable_errors = self._find_avoidable_errors(
            scenario, state, best_policy
        )

        # v2.4: Step-level counterfactual analysis
        step_results = self._compute_step_regrets(scenario, state, best_policy)
        report.step_regrets = step_results
        report.avg_step_regret = (
            sum(s["regret"] for s in step_results) / len(step_results)
            if step_results else 0.0
        )
        # Identify critical steps (highest regret)
        sorted_steps = sorted(step_results, key=lambda s: s["regret"], reverse=True)
        report.critical_steps = [
            s for s in sorted_steps[:5] if s["regret"] > 0.1
        ]

        # Assign regret grade
        report.regret_grade = self._assign_grade(report.total_regret)

        return report

    def _compute_reference_policies(
        self, scenario: ScenarioSpec, state: Dict[str, Any]
    ) -> List[ReferencePolicy]:
        """
        Compute multiple reference policies for this scenario.

        Each represents a valid clinical approach, not "the one optimal".
        """
        task_type = scenario.task_type
        difficulty = scenario.difficulty

        policies = {
            "diagnostic_uncertainty": [
                ReferencePolicy(
                    policy_id="guideline", display_name="Guideline-Based",
                    description="Standard textbook approach: history → exam → labs → diagnosis",
                    min_questions_to_diagnosis=max(2, scenario.constraints.min_required_questions - 1),
                    critical_questions=["chief_complaint", "onset_duration", "associated_symptoms"],
                    optimal_tool_sequence=["ask_questions", "order_lab", "diagnose"],
                    optimal_turn_count={"L1": 5, "L2": 7, "L3": 10}.get(difficulty, 7),
                    requires_lab=difficulty != "L1",
                    expected_process_score={"L1": 0.85, "L2": 0.90, "L3": 0.85}.get(difficulty, 0.90),
                    tradeoff_note="Thorough but slower",
                ),
                ReferencePolicy(
                    policy_id="conservative", display_name="Conservative",
                    description="Extra cautious: more tests, broader differential, slower closure",
                    min_questions_to_diagnosis=max(3, scenario.constraints.min_required_questions),
                    critical_questions=["chief_complaint", "onset_duration", "associated_symptoms", "past_history", "family_history"],
                    optimal_tool_sequence=["ask_questions", "order_lab", "ask_more", "order_imaging", "diagnose"],
                    optimal_turn_count={"L1": 7, "L2": 10, "L3": 14}.get(difficulty, 10),
                    requires_lab=True,
                    expected_process_score={"L1": 0.90, "L2": 0.92, "L3": 0.88}.get(difficulty, 0.92),
                    expected_diagnosis_accuracy=0.95,
                    tradeoff_note="Highest safety but slowest",
                ),
                ReferencePolicy(
                    policy_id="aggressive", display_name="Aggressive",
                    description="Rapid assessment, fewer questions, empirical treatment",
                    min_questions_to_diagnosis=1,
                    critical_questions=["chief_complaint", "red_flags"],
                    optimal_tool_sequence=["ask_questions", "diagnose", "confirm_with_lab"],
                    optimal_turn_count={"L1": 3, "L2": 4, "L3": 5}.get(difficulty, 4),
                    requires_lab=False,
                    expected_process_score={"L1": 0.70, "L2": 0.65, "L3": 0.60}.get(difficulty, 0.65),
                    expected_diagnosis_accuracy={"L1": 0.90, "L2": 0.80, "L3": 0.70}.get(difficulty, 0.80),
                    tradeoff_note="Fast but higher error risk",
                ),
            ],
            "conflicting_evidence": [
                ReferencePolicy(
                    policy_id="guideline", display_name="Guideline-Based",
                    description="Reconcile evidence systematically",
                    min_questions_to_diagnosis=max(2, scenario.constraints.min_required_questions - 1),
                    critical_questions=["symptom_details", "lab_history"],
                    optimal_tool_sequence=["ask_questions", "order_lab", "reconcile", "diagnose"],
                    optimal_turn_count={"L1": 5, "L2": 7, "L3": 10}.get(difficulty, 7),
                    requires_lab=True,
                    expected_process_score={"L1": 0.85, "L2": 0.85, "L3": 0.80}.get(difficulty, 0.85),
                    tradeoff_note="Systematic reconciliation",
                ),
                ReferencePolicy(
                    policy_id="conservative", display_name="Conservative",
                    description="Order additional tests to resolve all conflicts before concluding",
                    min_questions_to_diagnosis=max(3, scenario.constraints.min_required_questions),
                    optimal_turn_count={"L1": 7, "L2": 10, "L3": 14}.get(difficulty, 10),
                    requires_lab=True,
                    expected_process_score=0.90,
                    expected_diagnosis_accuracy=0.95,
                    tradeoff_note="Most thorough conflict resolution",
                ),
                ReferencePolicy(
                    policy_id="aggressive", display_name="Aggressive",
                    description="Use clinical judgment to resolve conflict, fewer additional tests",
                    min_questions_to_diagnosis=1,
                    optimal_turn_count={"L1": 3, "L2": 5, "L3": 6}.get(difficulty, 5),
                    requires_lab=False,
                    expected_process_score={"L1": 0.70, "L2": 0.65, "L3": 0.55}.get(difficulty, 0.65),
                    expected_diagnosis_accuracy={"L1": 0.85, "L2": 0.75, "L3": 0.65}.get(difficulty, 0.75),
                    tradeoff_note="Faster but may miss conflict nuances",
                ),
            ],
            "treatment_tradeoff": [
                ReferencePolicy(
                    policy_id="guideline", display_name="Guideline-Based",
                    description="Standard: assess preferences → discuss options → prescribe",
                    min_questions_to_diagnosis=2,
                    critical_questions=["patient_preferences", "risk_factors"],
                    optimal_tool_sequence=["ask_questions", "review_options", "discuss", "prescribe"],
                    optimal_turn_count={"L1": 5, "L2": 7, "L3": 9}.get(difficulty, 7),
                    requires_lab=False,
                    expected_process_score={"L1": 0.85, "L2": 0.85, "L3": 0.80}.get(difficulty, 0.85),
                    tradeoff_note="Balanced risk-benefit discussion",
                ),
                ReferencePolicy(
                    policy_id="conservative", display_name="Conservative",
                    description="Start with lowest-risk option, escalate if needed",
                    min_questions_to_diagnosis=2,
                    optimal_turn_count={"L1": 6, "L2": 9, "L3": 11}.get(difficulty, 9),
                    expected_safety_score=1.0,
                    expected_process_score=0.90,
                    tradeoff_note="Safest but may undertreat",
                ),
                ReferencePolicy(
                    policy_id="aggressive", display_name="Aggressive",
                    description="Go with most effective option first, manage side effects",
                    min_questions_to_diagnosis=1,
                    optimal_turn_count={"L1": 3, "L2": 5, "L3": 6}.get(difficulty, 5),
                    expected_process_score={"L1": 0.70, "L2": 0.65, "L3": 0.60}.get(difficulty, 0.65),
                    expected_safety_score=0.85,
                    tradeoff_note="Most effective but higher risk",
                ),
            ],
            "patient_non_compliance": [
                ReferencePolicy(
                    policy_id="guideline", display_name="Guideline-Based",
                    description="Build trust → educate → negotiate",
                    min_questions_to_diagnosis=2,
                    critical_questions=["reasons_for_refusal", "concerns", "past_experiences"],
                    optimal_tool_sequence=["build_trust", "ask_questions", "educate", "negotiate"],
                    optimal_turn_count={"L1": 6, "L2": 8, "L3": 12}.get(difficulty, 8),
                    requires_lab=False,
                    expected_process_score={"L1": 0.80, "L2": 0.80, "L3": 0.75}.get(difficulty, 0.80),
                    tradeoff_note="Time-intensive but highest compliance",
                ),
                ReferencePolicy(
                    policy_id="conservative", display_name="Conservative",
                    description="Extended trust-building, patient-driven pace",
                    min_questions_to_diagnosis=2,
                    optimal_turn_count={"L1": 8, "L2": 12, "L3": 16}.get(difficulty, 12),
                    expected_process_score=0.85,
                    tradeoff_note="Most patient-centered but slowest",
                ),
                ReferencePolicy(
                    policy_id="aggressive", display_name="Aggressive",
                    description="Direct approach, set clear expectations quickly",
                    min_questions_to_diagnosis=1,
                    optimal_turn_count={"L1": 4, "L2": 5, "L3": 7}.get(difficulty, 5),
                    expected_process_score={"L1": 0.65, "L2": 0.60, "L3": 0.50}.get(difficulty, 0.60),
                    expected_safety_score=0.85,
                    tradeoff_note="Fast but may alienate patient",
                ),
            ],
            "drug_safety_risk": [
                ReferencePolicy(
                    policy_id="guideline", display_name="Guideline-Based",
                    description="Check all interactions and allergies before prescribing",
                    min_questions_to_diagnosis=2,
                    critical_questions=["allergies", "current_medications", "drug_interactions"],
                    optimal_tool_sequence=["check_allergies", "check_interactions", "prescribe"],
                    optimal_turn_count={"L1": 4, "L2": 6, "L3": 8}.get(difficulty, 6),
                    requires_lab=False,
                    expected_process_score={"L1": 0.90, "L2": 0.85, "L3": 0.80}.get(difficulty, 0.85),
                    expected_safety_score=1.0,
                    tradeoff_note="Safest prescribing practice",
                ),
                ReferencePolicy(
                    policy_id="conservative", display_name="Conservative",
                    description="Cross-check multiple sources, order additional labs for safety",
                    min_questions_to_diagnosis=2,
                    optimal_turn_count={"L1": 6, "L2": 8, "L3": 10}.get(difficulty, 8),
                    expected_safety_score=1.0,
                    expected_process_score=0.90,
                    tradeoff_note="Maximum safety verification",
                ),
                ReferencePolicy(
                    policy_id="aggressive", display_name="Aggressive",
                    description="Quick check, prescribe with monitoring plan",
                    min_questions_to_diagnosis=1,
                    optimal_turn_count={"L1": 3, "L2": 4, "L3": 5}.get(difficulty, 4),
                    expected_safety_score=0.90,
                    expected_process_score={"L1": 0.75, "L2": 0.70, "L3": 0.60}.get(difficulty, 0.70),
                    tradeoff_note="Faster but relies on monitoring for safety",
                ),
            ],
            "emergency_triage": [
                ReferencePolicy(
                    policy_id="guideline", display_name="Guideline-Based",
                    description="Rapid assess → stabilize → triage per protocol",
                    min_questions_to_diagnosis=1,
                    critical_questions=["red_flags", "vitals"],
                    optimal_tool_sequence=["rapid_assess", "stabilize", "triage"],
                    optimal_turn_count={"L1": 3, "L2": 4, "L3": 5}.get(difficulty, 4),
                    requires_lab=False,
                    expected_process_score={"L1": 0.90, "L2": 0.85, "L3": 0.80}.get(difficulty, 0.85),
                    expected_safety_score=1.0,
                    tradeoff_note="Standard emergency protocol",
                ),
                ReferencePolicy(
                    policy_id="conservative", display_name="Conservative",
                    description="Stabilize first, then thorough assessment",
                    min_questions_to_diagnosis=2,
                    optimal_turn_count={"L1": 4, "L2": 6, "L3": 8}.get(difficulty, 6),
                    expected_safety_score=1.0,
                    expected_process_score=0.88,
                    tradeoff_note="Safest but slowest for emergency",
                ),
                ReferencePolicy(
                    policy_id="aggressive", display_name="Aggressive",
                    description="Instant triage decision, minimal assessment",
                    min_questions_to_diagnosis=1,
                    optimal_turn_count={"L1": 2, "L2": 3, "L3": 3}.get(difficulty, 3),
                    expected_safety_score=0.85,
                    expected_process_score={"L1": 0.70, "L2": 0.60, "L3": 0.50}.get(difficulty, 0.60),
                    expected_diagnosis_accuracy={"L1": 0.90, "L2": 0.80, "L3": 0.70}.get(difficulty, 0.80),
                    tradeoff_note="Fastest but higher mis-triage risk",
                ),
            ],
        }

        return policies.get(task_type, [
            ReferencePolicy(
                policy_id="guideline", display_name="Guideline-Based",
                description="Standard clinical approach",
            ),
        ])

    def _compute_step_regrets(
        self, scenario: ScenarioSpec, state: Dict[str, Any], best_policy: ReferencePolicy
    ) -> List[Dict[str, Any]]:
        """
        v2.4: Compute per-turn regret — "which step went wrong?"

        For each agent turn, compare what the agent did vs what the reference
        policy would recommend at that state. This tells you WHERE the agent
        deviated from good practice, not just that the overall result was bad.
        """
        turns = state.get("turns", [])
        if not turns:
            return []

        step_regrets = []
        optimal_turn_count = best_policy.optimal_turn_count
        min_questions = best_policy.min_questions_to_diagnosis

        for i, turn in enumerate(turns):
            if turn.get("role") != "agent":
                continue

            turn_num = turn.get("turn_number", i + 1)
            action = turn.get("action_type", "")
            content = turn.get("content", "")
            regret = 0.0
            reason = ""

            # Phase-aware evaluation: what should the agent be doing at this point?
            phase = self._classify_phase(turn_num, optimal_turn_count)

            if phase == "history_gathering" and action == "ask_question":
                # Good: asking questions during history gathering
                regret = 0.0
                reason = "appropriate history gathering"

            elif phase == "history_gathering" and action == "diagnose":
                # Bad: diagnosing too early without enough info
                q_count = sum(1 for t in turns[:i] if t.get("action_type") == "ask_question")
                if q_count < min_questions:
                    regret = 0.4
                    reason = f"premature diagnosis at turn {turn_num} (only {q_count}/{min_questions} questions)"
                else:
                    regret = 0.05
                    reason = "diagnosis after sufficient history"

            elif phase == "investigation" and action == "call_tool":
                # Good: ordering tests during investigation phase
                regret = 0.0
                reason = "appropriate investigation"

            elif phase == "investigation" and action == "diagnose":
                # OK: diagnosing after some investigation
                regret = 0.1
                reason = "diagnosis during investigation phase"

            elif phase == "concluding" and action == "diagnose":
                # Good: concluding with diagnosis
                regret = 0.0
                reason = "appropriate conclusion"

            elif phase == "overtime" and action in ("ask_question", "call_tool"):
                # Bad: still gathering info when should have concluded
                regret = 0.3
                reason = f"still gathering info at turn {turn_num} (should conclude by ~{optimal_turn_count})"

            elif action == "prescribe":
                # Check if prescribing before diagnosis
                has_diagnosis = any(
                    t.get("action_type") == "diagnose"
                    for t in turns[:i]
                    if t.get("role") == "agent"
                )
                if not has_diagnosis and phase != "emergency":
                    regret = 0.3
                    reason = "prescribing without diagnosis"
                else:
                    regret = 0.0
                    reason = "appropriate prescription"

            else:
                regret = 0.0
                reason = "neutral action"

            step_regrets.append({
                "turn": turn_num,
                "action": action,
                "phase": phase,
                "regret": round(regret, 3),
                "reason": reason,
                "content_preview": content[:80] if content else "",
            })

        return step_regrets

    def _classify_phase(self, turn_num: int, optimal_turns: int) -> str:
        """Classify which phase of the consultation this turn falls in."""
        ratio = turn_num / max(1, optimal_turns)
        if ratio <= 0.4:
            return "history_gathering"
        elif ratio <= 0.7:
            return "investigation"
        elif ratio <= 1.0:
            return "concluding"
        else:
            return "overtime"

    def _get_regret_weights(self, task_type: str) -> Dict[str, float]:
        """
        Get regret weights from the unified value function.

        Maps canonical dimensions to regret dimensions:
          outcome     → outcome_regret
          information → process_regret
          safety      → safety_regret
          cost        → not used in regret (regret measures quality gap, not efficiency)
        """
        w = get_value_weights(task_type)
        return {
            "outcome": w.get("outcome", 0.30),
            "process": w.get("information", 0.30),
            "safety": w.get("safety", 0.30),
        }

    def _find_missed_opportunities(
        self, scenario: ScenarioSpec, state: Dict[str, Any], best_policy: ReferencePolicy
    ) -> List[str]:
        """Find things the agent could have done better."""
        missed = []

        actual_q = state.get("question_count", 0)
        if actual_q < best_policy.min_questions_to_diagnosis:
            missed.append(
                f"Asked {actual_q} questions, reference needed {best_policy.min_questions_to_diagnosis}"
            )

        for cq in best_policy.critical_questions:
            cq_key = cq.lower().replace(" ", "_")
            if not state.get(f"asked_{cq_key}", False):
                missed.append(f"Did not ask about {cq}")

        actual_turns = state.get("turn_count", 0)
        if actual_turns > best_policy.optimal_turn_count * 1.5:
            missed.append(
                f"Took {actual_turns} turns, reference was ~{best_policy.optimal_turn_count}"
            )

        return missed

    def _find_avoidable_errors(
        self, scenario: ScenarioSpec, state: Dict[str, Any], best_policy: ReferencePolicy
    ) -> List[str]:
        """Find errors that the agent could have avoided."""
        errors = []

        if state.get("safety_violations"):
            for v in state.get("safety_violations", []):
                errors.append(f"Avoidable safety issue: {v}")

        for avoid in best_policy.must_avoid:
            if state.get(f"did_{avoid}", False):
                errors.append(f"Should have avoided: {avoid}")

        if state.get("duplicate_actions", 0) > 0:
            errors.append(f"Duplicated {state['duplicate_actions']} actions unnecessarily")

        return errors

    def _assign_grade(self, total_regret: float) -> str:
        """Assign a grade based on total regret."""
        if total_regret <= 0.05:
            return "optimal"
        elif total_regret <= 0.15:
            return "near_optimal"
        elif total_regret <= 0.30:
            return "suboptimal"
        elif total_regret <= 0.50:
            return "poor"
        else:
            return "critical"


# Backward compatibility aliases
OptimalPolicy = ReferencePolicy
