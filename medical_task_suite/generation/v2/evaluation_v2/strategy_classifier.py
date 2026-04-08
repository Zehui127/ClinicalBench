#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strategy Classifier — Classify the agent's clinical approach.

Identifies the reasoning strategy the agent used:
- evidence_first: Gather data before concluding
- empirical_then_confirm: Try treatment, then confirm
- rule_out_critical: Prioritize emergency exclusion
- shotgun: Order everything at once (penalized)
- premature_closure: Conclude too quickly without evidence
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from ..interaction_engine.state_manager import ConversationState
from ..scenario_engine.scenario_schema import ScenarioSpec


class StrategyType(str, Enum):
    EVIDENCE_FIRST = "evidence_first"
    EMPIRICAL_THEN_CONFIRM = "empirical_then_confirm"
    RULE_OUT_CRITICAL = "rule_out_critical"
    SHOTGUN = "shotgun"
    PREMATURE_CLOSURE = "premature_closure"
    THOROUGH = "thorough"
    UNDEFINED = "undefined"


@dataclass
class StrategyReport:
    """Result of strategy classification."""
    primary_strategy: str
    confidence: float  # 0.0-1.0
    strategy_sequence: List[str] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    quality_assessment: str = ""  # "good", "acceptable", "poor"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_strategy": self.primary_strategy,
            "confidence": self.confidence,
            "strategy_sequence": self.strategy_sequence,
            "observations": self.observations,
            "quality": self.quality_assessment,
        }


class StrategyClassifier:
    """
    Classify the agent's clinical reasoning strategy.

    Usage:
        classifier = StrategyClassifier()
        report = classifier.classify(scenario, state)
        print(report.primary_strategy)  # "evidence_first"
    """

    def classify(
        self, scenario: ScenarioSpec, state: ConversationState
    ) -> StrategyReport:
        """Classify the agent's strategy."""
        sequence = self._extract_sequence(state)
        features = self._extract_features(state, sequence)

        # Classify based on features
        strategy = self._determine_strategy(features, scenario, state)
        quality = self._assess_quality(strategy, features, scenario)

        return StrategyReport(
            primary_strategy=strategy.value,
            confidence=features.get("confidence", 0.5),
            strategy_sequence=sequence,
            observations=features.get("observations", []),
            quality_assessment=quality,
        )

    def _extract_sequence(self, state: ConversationState) -> List[str]:
        """Extract the sequence of action types."""
        return [
            f"{t.role}:{t.action_type}" for t in state.turns
            if t.role == "agent"
        ]

    def _extract_features(
        self, state: ConversationState, sequence: List[str]
    ) -> Dict[str, Any]:
        """Extract features for strategy classification."""
        features = {
            "observations": [],
            "confidence": 0.5,
        }

        agent_actions = [t for t in state.turns if t.role == "agent"]

        if not agent_actions:
            return features

        # Action counts
        questions = sum(1 for a in agent_actions if a.action_type == "ask_question")
        tools = sum(1 for a in agent_actions if a.action_type == "call_tool")
        diagnoses = sum(1 for a in agent_actions if a.action_type == "diagnose")
        prescriptions = sum(1 for a in agent_actions if a.action_type == "prescribe")

        features["question_count"] = questions
        features["tool_count"] = tools
        features["diagnosis_count"] = diagnoses
        features["prescription_count"] = prescriptions

        # First action type
        if agent_actions:
            features["first_action"] = agent_actions[0].action_type

        # Ordering patterns
        first_diag_idx = None
        first_tool_idx = None
        first_question_idx = None

        for i, action in enumerate(agent_actions):
            if action.action_type == "diagnose" and first_diag_idx is None:
                first_diag_idx = i
            if action.action_type == "call_tool" and first_tool_idx is None:
                first_tool_idx = i
            if action.action_type == "ask_question" and first_question_idx is None:
                first_question_idx = i

        features["questions_before_diagnosis"] = (
            first_question_idx is not None and
            first_diag_idx is not None and
            first_question_idx < first_diag_idx
        )

        features["tools_before_diagnosis"] = (
            first_tool_idx is not None and
            first_diag_idx is not None and
            first_tool_idx < first_diag_idx
        )

        # Batch tool calls (shotgun pattern)
        consecutive_tools = 0
        max_consecutive = 0
        for action in agent_actions:
            if action.action_type == "call_tool":
                consecutive_tools += 1
                max_consecutive = max(max_consecutive, consecutive_tools)
            else:
                consecutive_tools = 0
        features["max_consecutive_tools"] = max_consecutive
        features["batch_tools"] = max_consecutive >= 3

        # Premature closure detection
        if first_diag_idx is not None and first_diag_idx <= 1:
            features["premature_closure"] = True
            features["observations"].append("Diagnosed in first or second turn")
        else:
            features["premature_closure"] = False

        return features

    def _determine_strategy(
        self, features: Dict, scenario: ScenarioSpec, state: ConversationState
    ) -> StrategyType:
        """Determine the primary strategy."""
        # Premature closure
        if features.get("premature_closure"):
            return StrategyType.PREMATURE_CLOSURE

        # Shotgun (batch tool calls)
        if features.get("batch_tools"):
            return StrategyType.SHOTGUN

        # Rule out critical (for emergency scenarios)
        if scenario.task_type == "emergency_triage":
            if features.get("questions_before_diagnosis"):
                return StrategyType.RULE_OUT_CRITICAL

        # Empirical then confirm
        if features.get("prescription_count", 0) > 0:
            if features.get("diagnosis_count", 0) > 0:
                first_diag = None
                first_presc = None
                for i, t in enumerate(state.turns):
                    if t.role == "agent":
                        if t.action_type == "diagnose" and first_diag is None:
                            first_diag = i
                        if t.action_type == "prescribe" and first_presc is None:
                            first_presc = i
                if first_presc is not None and first_diag is not None and first_presc < first_diag:
                    return StrategyType.EMPIRICAL_THEN_CONFIRM

        # Evidence first
        if features.get("questions_before_diagnosis") and features.get("tools_before_diagnosis"):
            return StrategyType.EVIDENCE_FIRST

        # Thorough
        if features.get("question_count", 0) >= 3 and features.get("tool_count", 0) >= 1:
            return StrategyType.THOROUGH

        return StrategyType.UNDEFINED

    def _assess_quality(
        self, strategy: StrategyType, features: Dict, scenario: ScenarioSpec
    ) -> str:
        """Assess the quality of the strategy."""
        quality_map = {
            StrategyType.EVIDENCE_FIRST: "good",
            StrategyType.THOROUGH: "good",
            StrategyType.RULE_OUT_CRITICAL: "good",
            StrategyType.EMPIRICAL_THEN_CONFIRM: "acceptable",
            StrategyType.SHOTGUN: "poor",
            StrategyType.PREMATURE_CLOSURE: "poor",
            StrategyType.UNDEFINED: "acceptable",
        }

        return quality_map.get(strategy, "acceptable")
