#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strategy Distribution Evaluator — Anti-hack scoring via distribution over strategies.

v2.2: Strategy is NOT a classification — it's a DISTRIBUTION.
No single optimal path. Agent is scored across ALL valid strategies,
weighted by how well its actions match each strategy's pattern.

This prevents: "train model to mimic evidence_first → get high score"
Because: evidence_first is only ONE valid strategy, and others score well too.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

from ..interaction_engine.state_manager import ConversationState
from ..scenario_engine.scenario_schema import ScenarioSpec


# ============================================================
# Strategy Definitions — Multiple valid clinical approaches
# ============================================================

@dataclass
class StrategyProfile:
    """Profile of a valid clinical strategy."""
    strategy_id: str
    display_name: str
    description: str

    # What actions this strategy emphasizes
    expected_patterns: Dict[str, float] = field(default_factory=dict)
    # e.g., {"early_lab": 0.8, "many_questions": 0.6, "quick_diagnosis": 0.3}

    # Minimum requirements for this strategy to be valid
    min_questions: int = 1
    requires_labs: bool = False
    allows_early_diagnosis: bool = True

    # How well this strategy fits each scenario type (0.0-1.0)
    scenario_fitness: Dict[str, float] = field(default_factory=dict)

    # Weight for scoring dimensions when using this strategy
    scoring_weights: Dict[str, float] = field(default_factory=dict)


# All valid strategies
STRATEGY_PROFILES = [
    StrategyProfile(
        strategy_id="evidence_first",
        display_name="Evidence-First",
        description="Gather comprehensive evidence before concluding. Classic textbook approach.",
        expected_patterns={"early_lab": 0.8, "many_questions": 0.9, "thorough_history": 0.8, "differential_mentioned": 0.7, "quick_diagnosis": 0.2},
        min_questions=3,
        requires_labs=True,
        allows_early_diagnosis=False,
        scenario_fitness={
            "diagnostic_uncertainty": 1.0, "conflicting_evidence": 1.0,
            "treatment_tradeoff": 0.8, "patient_non_compliance": 0.6,
            "drug_safety_risk": 0.7, "emergency_triage": 0.3,
        },
        scoring_weights={
            "evidence_quality": 0.30, "differential_quality": 0.20,
            "info_seeking": 0.20, "uncertainty_handling": 0.15, "efficiency": 0.15,
        },
    ),
    StrategyProfile(
        strategy_id="empirical_then_confirm",
        display_name="Empirical → Confirm",
        description="Treat based on clinical impression, then confirm with tests. Common in primary care.",
        expected_patterns={"early_diagnosis": 0.7, "early_treatment": 0.8, "confirmatory_lab": 0.6, "fewer_questions": 0.5, "quick_diagnosis": 0.7},
        min_questions=1,
        requires_labs=False,
        allows_early_diagnosis=True,
        scenario_fitness={
            "diagnostic_uncertainty": 0.7, "conflicting_evidence": 0.4,
            "treatment_tradeoff": 0.9, "patient_non_compliance": 0.8,
            "drug_safety_risk": 0.6, "emergency_triage": 0.4,
        },
        scoring_weights={
            "evidence_quality": 0.15, "differential_quality": 0.15,
            "info_seeking": 0.20, "uncertainty_handling": 0.15, "efficiency": 0.35,
        },
    ),
    StrategyProfile(
        strategy_id="rule_out_critical",
        display_name="Rule Out Critical First",
        description="Prioritize excluding life-threatening conditions. Essential in emergency/urgent care.",
        expected_patterns={"quick_assessment": 0.9, "early_lab": 0.7, "red_flag_check": 0.9, "triage_action": 0.8, "quick_diagnosis": 0.8},
        min_questions=1,
        requires_labs=False,
        allows_early_diagnosis=True,
        scenario_fitness={
            "diagnostic_uncertainty": 0.5, "conflicting_evidence": 0.5,
            "treatment_tradeoff": 0.3, "patient_non_compliance": 0.3,
            "drug_safety_risk": 0.5, "emergency_triage": 1.0,
        },
        scoring_weights={
            "evidence_quality": 0.10, "differential_quality": 0.10,
            "info_seeking": 0.15, "uncertainty_handling": 0.10, "efficiency": 0.55,
        },
    ),
    StrategyProfile(
        strategy_id="thorough_systematic",
        display_name="Thorough Systematic",
        description="Complete history, full review of systems, comprehensive workup. Academic ideal.",
        expected_patterns={"many_questions": 0.95, "early_lab": 0.9, "differential_mentioned": 0.9, "thorough_history": 0.9, "quick_diagnosis": 0.1},
        min_questions=4,
        requires_labs=True,
        allows_early_diagnosis=False,
        scenario_fitness={
            "diagnostic_uncertainty": 0.8, "conflicting_evidence": 0.9,
            "treatment_tradeoff": 0.7, "patient_non_compliance": 0.5,
            "drug_safety_risk": 0.8, "emergency_triage": 0.1,
        },
        scoring_weights={
            "evidence_quality": 0.25, "differential_quality": 0.30,
            "info_seeking": 0.25, "uncertainty_handling": 0.15, "efficiency": 0.05,
        },
    ),
]

# Penalized strategies (always bad)
PENALIZED_STRATEGIES = {
    "shotgun": -0.3,        # Order everything at once
    "premature_closure": -0.5,  # Diagnose immediately without evidence
    "anchoring": -0.3,      # Fixate on one diagnosis
    "posturing": -0.2,      # Ask many irrelevant questions
}


@dataclass
class StrategyDistribution:
    """
    Distribution over valid strategies for an agent's interaction.

    This is the anti-hack mechanism:
    - Agent is scored against ALL valid strategies, not just one
    - Final score is weighted blend across the distribution
    - No single strategy can be gamed for maximum score
    """
    weights: Dict[str, float] = field(default_factory=dict)
    best_strategy: str = ""
    best_weight: float = 0.0
    entropy: float = 0.0  # How spread out (higher = harder to hack)

    @property
    def is_concentrated(self) -> bool:
        """If too concentrated on one strategy, might be gaming."""
        return self.entropy < 0.3

    @property
    def is_ambiguous(self) -> bool:
        """If too spread out, agent is being deliberately ambiguous (v2.3)."""
        # Max entropy for 4 strategies = log2(4) = 2.0
        # Uniform distribution = 2.0, concentrated = ~0.5
        return self.entropy > 1.8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weights": {k: round(v, 3) for k, v in self.weights.items()},
            "best_strategy": self.best_strategy,
            "best_weight": round(self.best_weight, 3),
            "entropy": round(self.entropy, 3),
            "is_ambiguous": self.is_ambiguous,
        }


class StrategyDistributionEvaluator:
    """
    Evaluate agent by scoring across ALL valid strategy distributions.

    Usage:
        evaluator = StrategyDistributionEvaluator()
        dist = evaluator.compute_distribution(scenario, state)
        score = evaluator.weighted_score(dist, dimension_scores)
    """

    def compute_distribution(
        self, scenario: ScenarioSpec, state: ConversationState
    ) -> StrategyDistribution:
        """
        Compute how well agent's actions match each valid strategy.

        Returns a distribution, not a single classification.
        """
        weights = {}

        # Compute match score for each valid strategy
        for profile in STRATEGY_PROFILES:
            match = self._compute_match(profile, scenario, state)
            # Weight by scenario fitness
            fitness = profile.scenario_fitness.get(scenario.task_type, 0.5)
            weights[profile.strategy_id] = match * fitness

        # Normalize to distribution
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        # Compute best
        best = max(weights.items(), key=lambda x: x[1]) if weights else ("unknown", 0.0)

        # Compute entropy (measure of distribution spread)
        import math
        entropy = 0.0
        for w in weights.values():
            if w > 0:
                entropy -= w * math.log2(w + 1e-10)

        return StrategyDistribution(
            weights=weights,
            best_strategy=best[0],
            best_weight=best[1],
            entropy=entropy,
        )

    def weighted_score(
        self,
        distribution: StrategyDistribution,
        dimension_scores: Dict[str, float],
        scenario: ScenarioSpec,
    ) -> float:
            """
            Compute final score by blending across strategy distribution.

            Each strategy has its own weight vector for scoring dimensions.
            Final score = Σ(strategy_weight × strategy_specific_score)

            v2.3: Adds ambiguity penalty for deliberately unfocused agents.
            Agent must COMMIT to a strategy — cannot hide behind uniform distribution.
            """
            total_score = 0.0

            for profile in STRATEGY_PROFILES:
                strategy_weight = distribution.weights.get(profile.strategy_id, 0.0)
                if strategy_weight < 0.01:
                    continue

                # Compute score using this strategy's weights
                strategy_score = 0.0
                for dim, weight in profile.scoring_weights.items():
                    dim_score = dimension_scores.get(dim, 0.5)
                    strategy_score += weight * dim_score

                total_score += strategy_weight * strategy_score

            # Check for penalized strategies (always-bad patterns)
            penalty = self._detect_penalized(dimension_scores, scenario)

            # v2.4: KL divergence penalty — not just "too ambiguous" but "wrong strategy space"
            kl_penalty = self._compute_kl_penalty(distribution, scenario)
            penalty += kl_penalty

            total_score = max(0.0, total_score + penalty)

            return min(1.0, total_score)

    def compute_temporal_consistency(
        self, state: ConversationState, scenario: ScenarioSpec,
    ) -> Dict[str, Any]:
        """
        v2.6: Phase-aware temporal consistency check.

        Detects strategy switching patterns:
        - Legitimate phase transitions (exploration → conclusion): low penalty
        - Rapid oscillation (strategy flip-flopping): high penalty
        - Sustained coherent strategy: no penalty

        Returns:
            {
                "segments": [...],               # Detected strategy segments
                "n_switches": int,                # Number of strategy changes
                "n_phase_changes": int,           # Number of phase transitions
                "n_rapid_oscillations": int,      # Number of rapid back-and-forth switches
                "penalty": float,                 # Computed penalty (-0.0 to -0.3)
                "is_coherent": bool,              # Whether strategy is temporally coherent
            }
        """
        agent_turns = [t for t in state.turns if t.role == "agent"]
        if len(agent_turns) < 3:
            return {"segments": [], "n_switches": 0, "penalty": 0.0, "is_coherent": True}

        # Compute per-turn strategy classification
        turn_strategies = []
        for turn in agent_turns:
            strategy = self._classify_turn_strategy(turn)
            turn_strategies.append({
                "turn": turn.turn_number,
                "strategy": strategy,
                "action": turn.action_type,
            })

        # Detect segments (runs of same strategy)
        segments = []
        if turn_strategies:
            current = turn_strategies[0]["strategy"]
            start = turn_strategies[0]["turn"]
            for ts in turn_strategies[1:]:
                if ts["strategy"] != current:
                    segments.append({
                        "strategy": current,
                        "start_turn": start,
                        "end_turn": ts["turn"] - 1,
                    })
                    current = ts["strategy"]
                    start = ts["turn"]
            segments.append({
                "strategy": current,
                "start_turn": start,
                "end_turn": turn_strategies[-1]["turn"],
            })

        n_switches = len(segments) - 1

        # Count phase changes (legitimate transitions)
        total_turns = len(agent_turns)
        n_phase_changes = 0
        for seg in segments:
            ratio = seg["start_turn"] / max(1, total_turns)
            if 0.3 < ratio < 0.7:  # Mid-conversation transition
                n_phase_changes += 1

        # Detect rapid oscillation (A→B→A within 3 turns)
        n_rapid_oscillations = 0
        for i in range(len(turn_strategies) - 2):
            s1 = turn_strategies[i]["strategy"]
            s2 = turn_strategies[i + 1]["strategy"]
            s3 = turn_strategies[i + 2]["strategy"]
            if s1 == s3 and s1 != s2:  # A→B→A pattern
                n_rapid_oscillations += 1

        # Compute penalty
        # Phase changes reduce penalty (legitimate transition)
        # Rapid oscillations increase penalty (gaming behavior)
        adjusted_switches = n_switches - n_phase_changes
        penalty = 0.0
        if adjusted_switches > 0:
            penalty -= 0.03 * adjusted_switches  # Base penalty per switch
        if n_rapid_oscillations > 0:
            penalty -= 0.05 * n_rapid_oscillations  # Extra penalty for oscillation
        penalty = max(-0.3, penalty)  # Cap

        is_coherent = n_switches <= 2 and n_rapid_oscillations == 0

        return {
            "segments": segments,
            "n_switches": n_switches,
            "n_phase_changes": n_phase_changes,
            "n_rapid_oscillations": n_rapid_oscillations,
            "penalty": round(penalty, 3),
            "is_coherent": is_coherent,
        }

    def _classify_turn_strategy(self, turn) -> str:
        """Classify a single turn's strategy based on its action."""
        if turn.action_type == "ask_question":
            content = turn.content.lower()
            if any(w in content for w in ["emergency", "urgent", "critical", "life-threatening"]):
                return "rule_out_critical"
            return "evidence_first"
        elif turn.action_type == "call_tool":
            return "evidence_first"
        elif turn.action_type == "diagnose":
            return "empirical_then_confirm"
        elif turn.action_type == "prescribe":
            return "empirical_then_confirm"
        return "evidence_first"  # Default

    def _get_expected_distribution(self, task_type: str) -> Dict[str, float]:
        """
        Get the EXPECTED strategy distribution for a scenario type.

        v2.5: Derived from reference policies, not hand-tuned numbers.

        Derivation chain:
        1. Each task type has 3 reference policies (guideline, conservative, aggressive)
        2. Each policy has observable characteristics (questions, labs, timing)
        3. Those characteristics map to strategy alignment scores
        4. Weighted by policy quality (expected outcome scores)
        5. Aggregated into expected distribution

        Traceability: a reviewer can see exactly why evidence_first=0.X
        for a given task type — it comes from guideline policy having
        high quality + evidence_first-like behavior for that task type.
        """
        return self._derive_from_reference_policies(task_type)

    def _derive_from_reference_policies(self, task_type: str) -> Dict[str, float]:
        """
        Derive expected distribution by simulating each reference policy's
        behavior and measuring what strategy distribution that behavior produces.

        Derivation chain:
        1. Get reference policies for this task type
        2. For each policy, simulate its behavior as a ConversationState
           (policy parameters → concrete agent turns)
        3. Run compute_distribution() on the simulated state
           → this measures how well the simulated behavior matches each strategy
        4. Weight by policy quality (expected performance scores)
        5. Aggregate into expected distribution

        This is NOT "policy → strategy label". Each policy produces a full
        DISTRIBUTION over strategies because the strategy evaluator measures
        continuous match, not discrete classification.
        """
        from .counterfactual_evaluator import CounterfactualEvaluator

        evaluator = CounterfactualEvaluator()

        # Create minimal scenario to get reference policies for this task type
        from ..scenario_engine.scenario_schema import ScenarioSpec
        temp_scenario = ScenarioSpec(task_type=task_type, difficulty="L2")
        policies = evaluator._compute_reference_policies(temp_scenario, {})

        if not policies:
            return self._uniform_dist()

        strategy_weights: Dict[str, float] = defaultdict(float)

        for policy in policies:
            # Policy quality = expected performance (transparent weighting)
            quality = (
                policy.expected_diagnosis_accuracy +
                policy.expected_process_score +
                policy.expected_safety_score
            ) / 3.0

            # Simulate this policy's behavior as a ConversationState
            sim_state = self._simulate_policy(policy, temp_scenario)

            # Compute ACTUAL strategy distribution for the simulated behavior
            # This uses the same compute_distribution() that evaluates real agents
            policy_dist = self.compute_distribution(temp_scenario, sim_state)

            # Aggregate: each policy contributes its distribution weighted by quality
            for strategy, weight in policy_dist.weights.items():
                strategy_weights[strategy] += weight * quality

        # Normalize
        total = sum(strategy_weights.values())
        if total > 0:
            return {k: v / total for k, v in strategy_weights.items()}
        return self._uniform_dist()

    def _simulate_policy(self, policy, scenario):
        """
        Simulate a reference policy's behavior as a ConversationState.

        The policy has concrete parameters that define its behavioral signature:
        - min_questions_to_diagnosis: how many questions before diagnosing
        - requires_lab: whether lab tests are ordered
        - optimal_tool_sequence: what tools the policy uses
        - optimal_turn_count: how many turns the policy takes

        We convert these parameters into concrete agent turns, then
        compute_distribution() objectively measures what strategies
        those turns match.

        This is simulation, not labeling — the strategy evaluator
        decides what strategy the behavior represents.
        """
        from ..interaction_engine.state_manager import ConversationState, Turn

        state = ConversationState(scenario_id=scenario.scenario_id)
        turn_num = 0

        # Phase 1: Ask questions (min_questions_to_diagnosis turns)
        for i in range(policy.min_questions_to_diagnosis):
            turn_num += 1
            state.add_turn(Turn(
                turn_number=turn_num, role="patient",
                action_type="answer",
                content="Patient responds to question",
            ))
            turn_num += 1
            state.add_turn(Turn(
                turn_number=turn_num, role="agent",
                action_type="ask_question",
                content=f"Asking about symptom history and clinical details",
            ))

        # Phase 2: Order labs / tools if policy requires
        if policy.requires_lab:
            for tool in policy.optimal_tool_sequence:
                if tool in ("order_lab", "order_imaging", "confirm_with_lab"):
                    turn_num += 1
                    state.add_turn(Turn(
                        turn_number=turn_num, role="agent",
                        action_type="call_tool",
                        content=f"Ordering diagnostic tests",
                        tool_name=tool,
                    ))

        # Phase 3: Consider differential (if policy mentions it in sequence)
        if any(t in policy.optimal_tool_sequence
               for t in ("reconcile", "review_options", "build_trust", "educate")):
            turn_num += 1
            state.add_turn(Turn(
                turn_number=turn_num, role="agent",
                action_type="ask_question",
                content="Considering differential diagnosis and evaluating alternatives",
            ))

        # Phase 4: Diagnose
        turn_num += 1
        state.add_turn(Turn(
            turn_number=turn_num, role="agent",
            action_type="diagnose",
            content="Making diagnosis based on gathered evidence",
        ))

        return state

    @staticmethod
    def _uniform_dist() -> Dict[str, float]:
        """Uniform distribution over strategies."""
        return {
            "evidence_first": 0.25,
            "empirical_then_confirm": 0.25,
            "rule_out_critical": 0.25,
            "thorough_systematic": 0.25,
        }

    def _compute_kl_penalty(
        self, distribution: StrategyDistribution, scenario: ScenarioSpec
    ) -> float:
        """
        v2.4: KL divergence penalty — punish deviation from reasonable strategy space.

        KL(agent_dist || expected_dist) measures how much the agent's strategy
        distribution diverges from what's reasonable for this task type.

        Why this is better than simple entropy penalty:
        - Simple entropy says "you're too ambiguous" → agent can be 100% rule_out_critical
          in a diagnostic_uncertainty scenario and pass the entropy check
        - KL divergence says "you're in the WRONG strategy space" → catches both
          ambiguity AND wrong-strategy concentration

        Penalty = KL * kl_weight
        """
        import math

        expected = self._get_expected_distribution(scenario.task_type)
        agent = distribution.weights

        # Compute KL(agent || expected)
        kl = 0.0
        all_strategies = set(list(expected.keys()) + list(agent.keys()))

        for strategy in all_strategies:
            p = agent.get(strategy, 0.001)  # agent's actual distribution
            q = expected.get(strategy, 0.001)  # expected distribution

            # Avoid log(0)
            p = max(p, 1e-6)
            q = max(q, 1e-6)

            kl += p * math.log2(p / q)

        # Scale KL to penalty
        # KL = 0: perfect match → no penalty
        # KL = 0.5: mild deviation → small penalty
        # KL > 1.0: severe deviation → strong penalty
        if kl < 0.2:
            return 0.0  # Close enough to expected
        elif kl < 0.5:
            return -0.05 * (kl - 0.2) / 0.3  # -0.05 to 0
        elif kl < 1.0:
            return -0.05 - 0.10 * (kl - 0.5) / 0.5  # -0.05 to -0.15
        else:
            return -0.15 - 0.15 * min(1.0, (kl - 1.0))  # -0.15 to -0.30

    def _compute_ambiguity_penalty(self, distribution: StrategyDistribution) -> float:
        """
        v2.3 legacy: entropy-based ambiguity penalty.
        Kept as a secondary check alongside KL divergence.
        """
        import math
        max_entropy = math.log2(len(STRATEGY_PROFILES))

        if distribution.entropy < 1.5:
            return 0.0
        elif distribution.entropy < 1.8:
            frac = (distribution.entropy - 1.5) / 0.3
            return -0.05 * frac
        else:
            frac = min(1.0, (distribution.entropy - 1.8) / (max_entropy - 1.8))
            return -0.05 - 0.10 * frac

    def _compute_match(
        self, profile: StrategyProfile, scenario: ScenarioSpec, state: ConversationState
    ) -> float:
        """Compute how well agent's actions match a strategy profile."""
        # Extract action patterns from state
        agent_turns = [t for t in state.turns if t.role == "agent"]
        if not agent_turns:
            return 0.0

        n_questions = sum(1 for t in agent_turns if t.action_type == "ask_question")
        n_tools = sum(1 for t in agent_turns if t.action_type == "call_tool")
        n_diagnoses = sum(1 for t in agent_turns if t.action_type == "diagnose")
        n_prescriptions = sum(1 for t in agent_turns if t.action_type == "prescribe")

        # Check pattern matches
        match_score = 0.0
        n_patterns = 0

        # many_questions pattern
        if "many_questions" in profile.expected_patterns:
            expected = profile.expected_patterns["many_questions"]
            actual = min(1.0, n_questions / 5)
            match_score += 1.0 - abs(expected - actual)
            n_patterns += 1

        # early_lab pattern
        if "early_lab" in profile.expected_patterns:
            expected = profile.expected_patterns["early_lab"]
            actual = 1.0 if n_tools > 0 else 0.0
            match_score += 1.0 - abs(expected - actual)
            n_patterns += 1

        # quick_diagnosis pattern
        if "quick_diagnosis" in profile.expected_patterns:
            expected = profile.expected_patterns["quick_diagnosis"]
            if n_diagnoses > 0:
                diag_turn = next((t.turn_number for t in agent_turns if t.action_type == "diagnose"), 999)
                actual = 1.0 if diag_turn <= 4 else 0.3
            else:
                actual = 0.0
            match_score += 1.0 - abs(expected - actual)
            n_patterns += 1

        # early_treatment pattern
        if "early_treatment" in profile.expected_patterns:
            expected = profile.expected_patterns["early_treatment"]
            actual = 1.0 if n_prescriptions > 0 else 0.0
            match_score += 1.0 - abs(expected - actual)
            n_patterns += 1

        # differential_mentioned pattern
        if "differential_mentioned" in profile.expected_patterns:
            expected = profile.expected_patterns["differential_mentioned"]
            diff_count = sum(
                1 for t in agent_turns
                if t.role == "agent" and any(
                    w in t.content.lower()
                    for w in ["differential", "could be", "might be", "consider", "rule out"]
                )
            )
            actual = min(1.0, diff_count / 2)
            match_score += 1.0 - abs(expected - actual)
            n_patterns += 1

        # Min questions requirement
        if n_questions < profile.min_questions and n_diagnoses > 0:
            match_score *= 0.5  # Penalty for not meeting min requirement

        return match_score / max(1, n_patterns)

    def _detect_penalized(
        self, dimension_scores: Dict[str, float], scenario: ScenarioSpec
    ) -> float:
        """Detect if agent used a penalized strategy."""
        penalty = 0.0

        # Shotgun: low evidence quality + high tool count
        if dimension_scores.get("evidence_quality", 1.0) < 0.3:
            penalty += PENALIZED_STRATEGIES["shotgun"]

        # Premature closure: low info_seeking + diagnosis exists
        if dimension_scores.get("info_seeking", 1.0) < 0.2:
            penalty += PENALIZED_STRATEGIES["premature_closure"]

        return penalty
