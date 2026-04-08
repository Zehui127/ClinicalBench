#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Evaluation Pipeline — Generate, run, and evaluate scenarios at scale.

Usage:
    from medical_task_suite.generation.v2.batch_pipeline import BatchPipeline

    pipeline = BatchPipeline(clinical_kb, primekg)

    # Generate + run with optimal agent (baseline)
    results = pipeline.run_baseline(
        n_scenarios=50,
        task_types=["diagnostic_uncertainty", "emergency_triage"],
        difficulties=["L1", "L2", "L3"],
    )

    # Generate + run with external LLM
    results = pipeline.run_with_openai(
        n_scenarios=50,
        client=openai_client,
        model="gpt-4",
    )

    # Aggregate results
    summary = pipeline.aggregate(results)
    print(summary.to_table())
"""

import json
import random
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path

from .scenario_engine.scenario_generator import ScenarioGenerator
from .scenario_engine.scenario_schema import TASK_TYPES, ScenarioSpec
from .clinical_world.symptom_generator import SymptomGenerator
from .persona_engine.patient_agent import PatientAgent
from .interaction_engine.environment import MedicalEnvironment
from .interaction_engine.turn_simulator import AgentAction, Observation
from .evaluation_v2.outcome_evaluator import OutcomeEvaluator, OutcomeReport
from .evaluation_v2.process_evaluator import ProcessEvaluator, ProcessReport
from .evaluation_v2.safety_evaluator import SafetyEvaluator, SafetyReport
from .evaluation_v2.strategy_distribution import StrategyDistributionEvaluator, StrategyDistribution
from .evaluation_v2.counterfactual_evaluator import CounterfactualEvaluator, RegretReport
from .evaluation_v2.adaptive_weights import compute_total_score
from .agent_protocol.protocol import (
    AgentProtocol, ProtocolAction, ProtocolObservation, ProtocolResult,
)


# ============================================================
# Optimal Agent — Baseline agent that follows best practice
# ============================================================

class OptimalAgent:
    """
    A scripted agent that follows near-optimal strategy.
    Used as baseline for regret computation.

    Strategy: Ask key questions → Order targeted labs → Diagnose → Treat
    """

    def __init__(self, scenario: ScenarioSpec, disease: str):
        self.scenario = scenario
        self.disease = disease
        self._step = 0
        self._max_steps = scenario.constraints.max_turns

    def next_action(self, obs: Observation, env: MedicalEnvironment) -> AgentAction:
        """Determine next action based on conversation state."""
        state = env.get_state()
        self._step += 1

        n_questions = state.total_questions
        has_labs = len(state.clinical.lab_results) > 0
        diagnosed = len(state.clinical.diagnoses) > 0

        # Phase 1: Ask questions (gather info)
        if n_questions < self.scenario.constraints.min_required_questions:
            return self._ask_question(state, n_questions)

        # Phase 2: Order labs (if needed)
        if not has_labs and self.scenario.task_type not in ("patient_non_compliance",):
            return self._order_lab()

        # Phase 3: Diagnose
        if not diagnosed:
            return AgentAction(action_type="diagnose", content=self.disease)

        # Phase 4: Prescribe
        if not state.clinical.prescriptions:
            return self._prescribe(state)

        # Phase 5: End
        return AgentAction(action_type="end", content="Treatment complete.")

    def _ask_question(self, state, n_questions: int) -> AgentAction:
        """Ask the next most informative question."""
        questions = [
            "Can you tell me more about your main symptoms?",
            "When did this start and how has it progressed?",
            "Do you have any other symptoms I should know about?",
            "Do you have any past medical history or conditions?",
            "Are you taking any medications currently?",
            "Does anyone in your family have similar conditions?",
        ]
        idx = min(n_questions, len(questions) - 1)
        return AgentAction(action_type="ask_question", content=questions[idx])

    def _order_lab(self) -> AgentAction:
        """Order appropriate labs."""
        labs = {
            "diagnostic_uncertainty": "CBC",
            "conflicting_evidence": "BMP",
            "treatment_tradeoff": "BMP",
            "drug_safety_risk": "BMP",
            "emergency_triage": "CBC",
        }
        lab = labs.get(self.scenario.task_type, "CBC")
        return AgentAction(
            action_type="call_tool",
            tool_name="order_lab_test",
            content=f"Ordering {lab} to help with diagnosis",
            tool_args={"test_name": lab},
        )

    def _prescribe(self, state) -> AgentAction:
        """Prescribe appropriate treatment."""
        return AgentAction(
            action_type="prescribe",
            content=f"metformin 500mg twice daily ongoing",
        )


# ============================================================
# Batch Result Types
# ============================================================

@dataclass
class ScenarioResult:
    """Result of running a single scenario."""
    scenario_id: str
    task_type: str
    difficulty: str
    target_disease: str
    agent_type: str  # "optimal", "openai", "custom"

    # Scores
    outcome_score: float = 0.0
    process_score: float = 0.0
    safety_score: float = 0.0
    total_score: float = 0.0

    # Regret
    outcome_regret: float = 0.0
    process_regret: float = 0.0
    safety_regret: float = 0.0
    total_regret: float = 0.0
    regret_grade: str = ""

    # Efficiency
    total_turns: int = 0
    total_questions: int = 0
    total_tool_calls: int = 0
    correct_diagnosis: bool = False
    patient_trust_final: float = 0.0

    # Timing
    elapsed_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "task_type": self.task_type,
            "difficulty": self.difficulty,
            "target_disease": self.target_disease,
            "agent_type": self.agent_type,
            "outcome_score": round(self.outcome_score, 3),
            "process_score": round(self.process_score, 3),
            "safety_score": round(self.safety_score, 3),
            "total_score": round(self.total_score, 3),
            "total_regret": round(self.total_regret, 3),
            "regret_grade": self.regret_grade,
            "total_turns": self.total_turns,
            "correct_diagnosis": self.correct_diagnosis,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
        }


@dataclass
class BatchSummary:
    """Aggregated results across multiple scenarios."""
    agent_type: str
    n_scenarios: int = 0

    # Score aggregates
    avg_outcome: float = 0.0
    avg_process: float = 0.0
    avg_safety: float = 0.0
    avg_total: float = 0.0

    # Regret aggregates
    avg_regret: float = 0.0
    pct_optimal: float = 0.0      # % scenarios with regret <= 0.05
    pct_near_optimal: float = 0.0  # % scenarios with regret <= 0.15

    # Accuracy
    diagnosis_accuracy: float = 0.0  # % correct diagnoses

    # Efficiency
    avg_turns: float = 0.0
    avg_questions: float = 0.0

    # Per-task-type breakdown
    by_task_type: Dict[str, Dict[str, float]] = field(default_factory=dict)
    by_difficulty: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Timing
    total_seconds: float = 0.0
    avg_seconds_per_scenario: float = 0.0

    def to_table(self) -> str:
        """Format as readable table."""
        lines = [
            f"{'='*60}",
            f"  Batch Evaluation Summary ({self.agent_type})",
            f"{'='*60}",
            f"  Scenarios:        {self.n_scenarios}",
            f"  Total time:       {self.total_seconds:.1f}s ({self.avg_seconds_per_scenario:.1f}s/scenario)",
            f"",
            f"  --- Scores ---",
            f"  Outcome:          {self.avg_outcome:.1%}",
            f"  Process:          {self.avg_process:.1%}",
            f"  Safety:           {self.avg_safety:.1%}",
            f"  Total:            {self.avg_total:.1%}",
            f"",
            f"  --- Regret ---",
            f"  Avg regret:       {self.avg_regret:.3f}",
            f"  Optimal (≤0.05):  {self.pct_optimal:.1%}",
            f"  Near-opt (≤0.15): {self.pct_near_optimal:.1%}",
            f"",
            f"  --- Accuracy ---",
            f"  Diagnosis:        {self.diagnosis_accuracy:.1%}",
            f"  Avg turns:        {self.avg_turns:.1f}",
            f"  Avg questions:    {self.avg_questions:.1f}",
            f"",
        ]

        # Per-task-type breakdown
        if self.by_task_type:
            lines.append(f"  --- By Task Type ---")
            lines.append(f"  {'Task Type':<28} {'Score':>8} {'Regret':>8} {'Accuracy':>8}")
            lines.append(f"  {'-'*28} {'-'*8} {'-'*8} {'-'*8}")
            for tt, stats in sorted(self.by_task_type.items()):
                lines.append(
                    f"  {tt:<28} {stats.get('total', 0):>7.1%} "
                    f"{stats.get('regret', 0):>8.3f} "
                    f"{stats.get('accuracy', 0):>7.1%}"
                )
            lines.append("")

        # Per-difficulty breakdown
        if self.by_difficulty:
            lines.append(f"  --- By Difficulty ---")
            lines.append(f"  {'Level':<10} {'Score':>8} {'Regret':>8} {'Accuracy':>8}")
            lines.append(f"  {'-'*10} {'-'*8} {'-'*8} {'-'*8}")
            for diff, stats in sorted(self.by_difficulty.items()):
                lines.append(
                    f"  {diff:<10} {stats.get('total', 0):>7.1%} "
                    f"{stats.get('regret', 0):>8.3f} "
                    f"{stats.get('accuracy', 0):>7.1%}"
                )
            lines.append("")

        lines.append(f"{'='*60}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_type": self.agent_type,
            "n_scenarios": self.n_scenarios,
            "avg_outcome": round(self.avg_outcome, 3),
            "avg_process": round(self.avg_process, 3),
            "avg_safety": round(self.avg_safety, 3),
            "avg_total": round(self.avg_total, 3),
            "avg_regret": round(self.avg_regret, 3),
            "pct_optimal": round(self.pct_optimal, 3),
            "pct_near_optimal": round(self.pct_near_optimal, 3),
            "diagnosis_accuracy": round(self.diagnosis_accuracy, 3),
            "avg_turns": round(self.avg_turns, 1),
            "avg_questions": round(self.avg_questions, 1),
            "by_task_type": self.by_task_type,
            "by_difficulty": self.by_difficulty,
            "total_seconds": round(self.total_seconds, 1),
        }


# ============================================================
# Batch Pipeline
# ============================================================

class BatchPipeline:
    """
    Generate, run, and evaluate scenarios at scale.

    Usage:
        pipeline = BatchPipeline(clinical_kb, primekg)

        # Baseline with optimal agent
        results = pipeline.run_baseline(n_scenarios=30)
        summary = pipeline.aggregate(results)
        print(summary.to_table())

        # With external LLM
        results = pipeline.run_with_agent_fn(
            n_scenarios=30,
            agent_fn=my_llm_agent,
        )

        # Save/load results
        pipeline.save_results(results, "results.json")
    """

    def __init__(self, clinical_kb, primekg=None):
        self.kb = clinical_kb
        self.primekg = primekg
        self.scenario_gen = ScenarioGenerator(clinical_kb, primekg)

        # v2.7: Build PrimeKGBridge if primekg data provided
        self._primekg_bridge = None
        if primekg is not None:
            try:
                from .clinical_world.primekg_bridge import PrimeKGBridge
                if isinstance(primekg, tuple) and len(primekg) == 2:
                    nodes, edges = primekg
                else:
                    try:
                        nodes = primekg.nodes
                        edges = primekg.edges
                    except AttributeError:
                        nodes, edges = None, None
                if nodes and edges:
                    self._primekg_bridge = PrimeKGBridge(nodes, edges, clinical_kb)
            except Exception:
                pass

    # ============================================================
    # Scenario Generation
    # ============================================================

    def generate_scenarios(
        self,
        n_scenarios: int = 50,
        task_types: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        seed: int = 42,
    ) -> List[ScenarioSpec]:
        """Generate a balanced set of scenarios."""
        rng = random.Random(seed)
        task_types = task_types or TASK_TYPES
        difficulties = difficulties or ["L1", "L2", "L3"]

        scenarios = []
        for i in range(n_scenarios):
            tt = task_types[i % len(task_types)]
            diff = difficulties[i % len(difficulties)]
            # Add randomness within determinism
            s = rng.randint(0, 999999)

            try:
                scenario = self.scenario_gen.generate(tt, diff, seed=s)
                scenarios.append(scenario)
            except Exception as e:
                # Skip failed generations
                continue

        return scenarios

    # ============================================================
    # Run Methods
    # ============================================================

    def run_baseline(
        self,
        n_scenarios: int = 50,
        task_types: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        seed: int = 42,
    ) -> List[ScenarioResult]:
        """Run scenarios with optimal agent (baseline for regret computation)."""
        scenarios = self.generate_scenarios(n_scenarios, task_types, difficulties, seed)
        results = []

        for scenario in scenarios:
            result = self._run_single_optimal(scenario)
            if result is not None:
                results.append(result)

        return results

    def run_with_agent_fn(
        self,
        n_scenarios: int = 50,
        agent_fn: Optional[Callable] = None,
        task_types: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        seed: int = 42,
        agent_name: str = "custom",
    ) -> List[ScenarioResult]:
        """
        Run scenarios with a custom agent function.

        agent_fn signature:
            (observation: Observation, env: MedicalEnvironment) -> AgentAction

        If agent_fn is None, runs with the agent protocol's callable interface.
        """
        scenarios = self.generate_scenarios(n_scenarios, task_types, difficulties, seed)
        results = []

        for scenario in scenarios:
            result = self._run_single_with_fn(scenario, agent_fn, agent_name)
            if result is not None:
                results.append(result)

        return results

    def run_with_openai(
        self,
        client: Any,
        model: str = "gpt-4",
        n_scenarios: int = 50,
        task_types: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        seed: int = 42,
        temperature: float = 0.3,
    ) -> List[ScenarioResult]:
        """Run scenarios with an OpenAI-compatible LLM."""
        from .agent_protocol.openai_adapter import OpenAIAdapter

        scenarios = self.generate_scenarios(n_scenarios, task_types, difficulties, seed)
        results = []

        for i, scenario in enumerate(scenarios):
            try:
                protocol = AgentProtocol.from_scenario(scenario, self.kb)
                adapter = OpenAIAdapter(protocol)

                start_time = time.time()
                result = adapter.run_with_openai(client, model, temperature)
                elapsed = time.time() - start_time

                sr = self._protocol_result_to_scenario_result(
                    result, scenario, "openai", elapsed
                )
                results.append(sr)

            except Exception as e:
                # Skip failed runs
                continue

        return results

    # ============================================================
    # Aggregation
    # ============================================================

    def aggregate(
        self,
        results: List[ScenarioResult],
        agent_name: str = "",
    ) -> BatchSummary:
        """Aggregate scenario results into summary."""
        if not results:
            return BatchSummary(agent_type=agent_name or "unknown")

        n = len(results)
        summary = BatchSummary(
            agent_type=agent_name or results[0].agent_type,
            n_scenarios=n,
        )

        # Averages
        summary.avg_outcome = sum(r.outcome_score for r in results) / n
        summary.avg_process = sum(r.process_score for r in results) / n
        summary.avg_safety = sum(r.safety_score for r in results) / n
        summary.avg_total = sum(r.total_score for r in results) / n

        # Regret
        summary.avg_regret = sum(r.total_regret for r in results) / n
        summary.pct_optimal = sum(1 for r in results if r.total_regret <= 0.05) / n
        summary.pct_near_optimal = sum(1 for r in results if r.total_regret <= 0.15) / n

        # Accuracy
        summary.diagnosis_accuracy = sum(1 for r in results if r.correct_diagnosis) / n

        # Efficiency
        summary.avg_turns = sum(r.total_turns for r in results) / n
        summary.avg_questions = sum(r.total_questions for r in results) / n

        # Timing
        summary.total_seconds = sum(r.elapsed_seconds for r in results)
        summary.avg_seconds_per_scenario = summary.total_seconds / n

        # Per-task-type breakdown
        by_tt: Dict[str, List[ScenarioResult]] = {}
        for r in results:
            by_tt.setdefault(r.task_type, []).append(r)

        for tt, tt_results in by_tt.items():
            tn = len(tt_results)
            summary.by_task_type[tt] = {
                "total": sum(r.total_score for r in tt_results) / tn,
                "regret": sum(r.total_regret for r in tt_results) / tn,
                "accuracy": sum(1 for r in tt_results if r.correct_diagnosis) / tn,
                "outcome": sum(r.outcome_score for r in tt_results) / tn,
                "process": sum(r.process_score for r in tt_results) / tn,
                "safety": sum(r.safety_score for r in tt_results) / tn,
            }

        # Per-difficulty breakdown
        by_diff: Dict[str, List[ScenarioResult]] = {}
        for r in results:
            by_diff.setdefault(r.difficulty, []).append(r)

        for diff, diff_results in by_diff.items():
            dn = len(diff_results)
            summary.by_difficulty[diff] = {
                "total": sum(r.total_score for r in diff_results) / dn,
                "regret": sum(r.total_regret for r in diff_results) / dn,
                "accuracy": sum(1 for r in diff_results if r.correct_diagnosis) / dn,
                "outcome": sum(r.outcome_score for r in diff_results) / dn,
                "process": sum(r.process_score for r in diff_results) / dn,
                "safety": sum(r.safety_score for r in diff_results) / dn,
            }

        return summary

    # ============================================================
    # Save/Load
    # ============================================================

    def save_results(
        self,
        results: List[ScenarioResult],
        path: str,
    ) -> None:
        """Save results to JSON."""
        data = [r.to_dict() for r in results]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_results(self, path: str) -> List[ScenarioResult]:
        """Load results from JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [ScenarioResult(**d) for d in data]

    def save_summary(
        self,
        summary: BatchSummary,
        path: str,
    ) -> None:
        """Save summary to JSON."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary.to_dict(), f, indent=2, ensure_ascii=False)

    # ============================================================
    # Internal
    # ============================================================

    def _run_single_optimal(self, scenario: ScenarioSpec) -> Optional[ScenarioResult]:
        """Run a single scenario with the optimal agent."""
        try:
            # Build environment (v2.7: pass primekg for expanded pools)
            symptoms = SymptomGenerator(self.kb, self.primekg).generate(
                scenario.target_disease or "fatigue",
                scenario,
            )
            patient = PatientAgent.from_scenario(scenario, symptoms)
            env = MedicalEnvironment(scenario, patient, self.kb)

            # Optimal agent
            agent = OptimalAgent(scenario, scenario.target_disease or "unknown")

            # Run
            start_time = time.time()
            obs = env.reset()

            while not env.state.is_complete and env.state.turn_count < scenario.constraints.max_turns:
                action = agent.next_action(obs, env)
                obs = env.step(action)

            elapsed = time.time() - start_time

            # Evaluate
            return self._evaluate_scenario(scenario, env, "optimal", elapsed)

        except Exception:
            return None

    def _run_single_with_fn(
        self,
        scenario: ScenarioSpec,
        agent_fn: Optional[Callable],
        agent_name: str,
    ) -> Optional[ScenarioResult]:
        """Run a single scenario with a custom agent function."""
        try:
            # v2.7: pass primekg for expanded pools
            symptoms = SymptomGenerator(self.kb, self.primekg).generate(
                scenario.target_disease or "fatigue",
                scenario,
            )
            patient = PatientAgent.from_scenario(scenario, symptoms)
            env = MedicalEnvironment(scenario, patient, self.kb)

            start_time = time.time()
            obs = env.reset()

            while not env.state.is_complete and env.state.turn_count < scenario.constraints.max_turns:
                if agent_fn is None:
                    break
                action = agent_fn(obs, env)
                if action is None:
                    break
                obs = env.step(action)

            elapsed = time.time() - start_time
            return self._evaluate_scenario(scenario, env, agent_name, elapsed)

        except Exception:
            return None

    def _evaluate_scenario(
        self,
        scenario: ScenarioSpec,
        env: MedicalEnvironment,
        agent_type: str,
        elapsed: float,
    ) -> ScenarioResult:
        """Run full evaluation on a completed scenario."""
        state = env.get_state()
        eval_state = env.get_evaluation_state()

        # Run evaluators
        outcome = OutcomeEvaluator().evaluate(scenario, state)
        process = ProcessEvaluator().evaluate(scenario, state)
        safety = SafetyEvaluator().evaluate(scenario, state)
        regret = CounterfactualEvaluator().evaluate(
            scenario,
            outcome.overall_score,
            process.total_score,
            safety.safety_score,
            eval_state,
        )

        # Diagnosis check
        diagnoses = state.clinical.diagnoses
        agent_diagnosis = diagnoses[-1] if diagnoses else ""
        correct = agent_diagnosis.lower() == (scenario.target_disease or "").lower()

        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            task_type=scenario.task_type,
            difficulty=scenario.difficulty,
            target_disease=scenario.target_disease or "",
            agent_type=agent_type,
            outcome_score=outcome.overall_score,
            process_score=process.total_score,
            safety_score=safety.safety_score,
            total_score=compute_total_score(
                scenario.task_type,
                outcome.overall_score,
                process.total_score,
                safety.safety_score,
            ),
            outcome_regret=regret.outcome_regret,
            process_regret=regret.process_regret,
            safety_regret=regret.safety_regret,
            total_regret=regret.total_regret,
            regret_grade=regret.regret_grade,
            total_turns=state.turn_count,
            total_questions=state.total_questions,
            total_tool_calls=state.total_tool_calls,
            correct_diagnosis=correct,
            patient_trust_final=state.patient_trust,
            elapsed_seconds=elapsed,
        )

    def _protocol_result_to_scenario_result(
        self,
        pr: ProtocolResult,
        scenario: ScenarioSpec,
        agent_type: str,
        elapsed: float,
    ) -> ScenarioResult:
        """Convert ProtocolResult to ScenarioResult."""
        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            task_type=scenario.task_type,
            difficulty=scenario.difficulty,
            target_disease=scenario.target_disease or "",
            agent_type=agent_type,
            outcome_score=pr.outcome_score,
            process_score=pr.process_score,
            safety_score=pr.safety_score,
            total_score=pr.total_score,
            total_turns=pr.total_turns,
            total_questions=pr.total_questions,
            total_tool_calls=pr.total_tool_calls,
            correct_diagnosis=pr.diagnosis_correct,
            patient_trust_final=pr.patient_trust_final,
            elapsed_seconds=elapsed,
        )
