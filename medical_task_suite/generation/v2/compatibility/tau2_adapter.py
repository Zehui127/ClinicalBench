#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tau2 Adapter — Convert v2 output to tau2-bench format.

Ensures v2 tasks can run on the same tau2-bench runner as v1 tasks.
This is the compatibility bridge between the new architecture and
the existing evaluation infrastructure.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..scenario_engine.scenario_schema import ScenarioSpec
from ..interaction_engine.state_manager import ConversationState
from ..evaluation_v2.outcome_evaluator import OutcomeReport
from ..evaluation_v2.process_evaluator import ProcessReport
from ..evaluation_v2.safety_evaluator import SafetyReport
from ..evaluation_v2.strategy_classifier import StrategyReport


class Tau2Adapter:
    """
    Convert v2 results to tau2-bench JSON format.

    v2.7: Includes calibration metadata and PrimeKG stats when available.

    Usage:
        adapter = Tau2Adapter()
        tau2_task = adapter.convert(scenario, state, outcome, process)
        # tau2_task is compatible with existing tau2-bench runner
    """

    def convert(
        self,
        scenario: ScenarioSpec,
        state: ConversationState,
        outcome: Optional[OutcomeReport] = None,
        process: Optional[ProcessReport] = None,
        safety: Optional[SafetyReport] = None,
        strategy: Optional[StrategyReport] = None,
    ) -> Dict[str, Any]:
        """
        Convert v2 output to tau2-bench format.

        Args:
            scenario: Scenario specification
            state: Final conversation state
            outcome: Outcome evaluation (optional)
            process: Process evaluation (optional)
            safety: Safety evaluation (optional)
            strategy: Strategy classification (optional)

        Returns:
            Dict in tau2-bench format
        """
        # Build dialogue turns
        dialogue = self._build_dialogue(state)

        # Build latent truth
        latent_truth = self._build_latent_truth(scenario, state)

        # Build required tools
        required_tools = self._build_required_tools(state)

        # Build evaluation criteria
        evaluation = self._build_evaluation(scenario, outcome, process, safety, strategy)

        # Build task definition
        task = {
            "id": scenario.scenario_id or f"v2_{uuid.uuid4().hex[:8]}",
            "version": "2.7",
            "source": "v2_scenario_engine",
            "task_type": scenario.task_type,
            "difficulty": scenario.difficulty,

            # Patient persona (simplified from v2 persona engine)
            "user_persona": self._build_user_persona(scenario, state),

            # Dialogue history
            "dialogue": dialogue,

            # What the agent needs to discover
            "latent_truth": latent_truth,

            # Required tool calls
            "required_tool_calls": required_tools,

            # Evaluation criteria
            "evaluation": evaluation,

            # Generation metadata
            "generation_config": {
                "task_type": scenario.task_type,
                "difficulty": scenario.difficulty,
                "risk_level": scenario.risk_level,
                "uncertainty_level": scenario.uncertainty_level,
                "time_pressure": scenario.time_pressure,
                "information_completeness": scenario.information_completeness,
                "confounders": scenario.confounders,
                "behavior_type": scenario.behavior_type,
                "target_disease": scenario.target_disease,
                "symptom_keyword": scenario.symptom_keyword,
            },

            # v2.7: Calibration metadata
            "v2_7_metadata": self._build_v27_metadata(scenario, state),
        }

        return task

    def _build_dialogue(self, state: ConversationState) -> List[Dict[str, str]]:
        """Convert conversation turns to tau2 dialogue format."""
        dialogue = []
        for turn in state.turns:
            if turn.role == "patient":
                dialogue.append({
                    "role": "user",
                    "content": turn.content,
                })
            elif turn.role == "agent":
                dialogue.append({
                    "role": "assistant",
                    "content": turn.content,
                })
            elif turn.role == "system" and turn.tool_result:
                dialogue.append({
                    "role": "system",
                    "content": str(turn.tool_result),
                })
        return dialogue

    def _build_latent_truth(
        self, scenario: ScenarioSpec, state: ConversationState
    ) -> Dict[str, Any]:
        """Build latent truth section."""
        return {
            "primary_diagnosis": scenario.target_disease,
            "symptom_keyword": scenario.symptom_keyword,
            "risk_level": scenario.risk_level,
            "uncertainty_level": scenario.uncertainty_level,
            "confounders": scenario.confounders,
            "correct_diagnosis_reached": (
                scenario.target_disease and
                scenario.target_disease.lower() in [
                    d.lower() for d in state.clinical.diagnoses
                ]
            ) if state.clinical.diagnoses else False,
        }

    def _build_required_tools(self, state: ConversationState) -> List[Dict[str, Any]]:
        """Build required tool calls from actual tool usage."""
        tools = []
        seen = set()
        for turn in state.turns:
            if turn.action_type == "call_tool" and turn.tool_name:
                if turn.tool_name not in seen:
                    seen.add(turn.tool_name)
                    tools.append({
                        "tool": turn.tool_name,
                        "args": turn.tool_args,
                        "required": True,
                    })
        return tools

    def _build_evaluation(
        self,
        scenario: ScenarioSpec,
        outcome: Optional[OutcomeReport],
        process: Optional[ProcessReport],
        safety: Optional[SafetyReport],
        strategy: Optional[StrategyReport],
    ) -> Dict[str, Any]:
        """Build evaluation section."""
        evaluation = {
            "task_type": scenario.task_type,
            "difficulty": scenario.difficulty,
        }

        if outcome:
            evaluation["outcome"] = outcome.to_dict()

        if process:
            evaluation["process"] = process.to_dict()

        if safety:
            evaluation["safety"] = safety.to_dict()

        if strategy:
            evaluation["strategy"] = strategy.to_dict()

        return evaluation

    def _build_user_persona(
        self, scenario: ScenarioSpec, state: ConversationState
    ) -> str:
        """Build simplified user persona description."""
        symptoms = ", ".join(state.clinical.reported_symptoms[:5]) or scenario.symptom_keyword
        behavior_desc = {
            "cooperative": "a cooperative patient",
            "forgetful": "a patient who may forget to mention symptoms",
            "confused": "a patient who is confused about their condition",
            "concealing": "a patient who may conceal symptoms",
            "pressuring": "a patient who pressures for quick resolution",
            "refusing": "a patient who may refuse tests or treatment",
        }

        return (
            f"You are {behavior_desc.get(scenario.behavior_type, 'a patient')} "
            f"presenting with {symptoms}. "
            f"Risk level: {scenario.risk_level}. "
            f"Uncertainty: {scenario.uncertainty_level:.0%}."
        )

    def _build_v27_metadata(
        self, scenario: ScenarioSpec, state: ConversationState
    ) -> Dict[str, Any]:
        """Build v2.7 metadata section with calibration and data source info."""
        metadata: Dict[str, Any] = {
            "schema_version": "2.7",
            "data_sources": [],
        }

        # Persona calibration info
        try:
            from ..persona_engine.calibrated_defaults import CALIBRATION_SOURCE
            metadata["persona_calibration"] = CALIBRATION_SOURCE
            metadata["data_sources"].append("HealthCareMagic-100k")
        except ImportError:
            pass

        # Noise calibration info
        try:
            from ..scenario_engine.noise_calibration import DEFAULT_CALIBRATION
            metadata["noise_calibration"] = {
                "avg_volunteered_symptoms": DEFAULT_CALIBRATION.avg_volunteered_symptoms,
                "noise_symptom_rate": DEFAULT_CALIBRATION.noise_symptom_rate,
                "misleading_symptom_rate": DEFAULT_CALIBRATION.misleading_symptom_rate,
            }
        except ImportError:
            pass

        # Ground truth composition (comorbidities, confounders)
        gt = scenario.ground_truth
        if gt:
            metadata["ground_truth_composition"] = {
                "primary_disease": gt.primary.name if hasattr(gt.primary, 'name') else str(gt.primary),
                "n_comorbidities": len(gt.comorbidities),
                "n_confounders": len(gt.confounders),
            }

        return metadata
