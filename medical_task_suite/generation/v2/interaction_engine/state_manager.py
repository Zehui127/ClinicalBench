#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
State Manager — Track conversation state across turns.

Unlike v1 where dialogue is pre-generated, v2 tracks state that evolves
as the agent (and patient) take actions. This state is what the
evaluation module uses to assess reasoning quality.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Turn:
    """A single turn in the conversation."""
    turn_number: int
    role: str  # "agent" (doctor) or "patient" or "system"
    action_type: str = ""  # ask_question, call_tool, diagnose, prescribe, respond
    content: str = ""
    tool_name: str = ""  # If action_type == call_tool
    tool_args: Dict[str, Any] = field(default_factory=dict)
    tool_result: Any = None
    revealed_info: List[str] = field(default_factory=list)
    trust_delta: float = 0.0
    timestamp: str = ""


@dataclass
class ClinicalState:
    """Current clinical state accumulated during conversation."""
    # Patient-reported symptoms
    reported_symptoms: List[str] = field(default_factory=list)

    # Lab results obtained
    lab_results: List[Dict[str, Any]] = field(default_factory=list)

    # Diagnoses made
    diagnoses: List[str] = field(default_factory=list)

    # Prescriptions given
    prescriptions: List[Dict[str, Any]] = field(default_factory=list)

    # Tests ordered
    tests_ordered: List[str] = field(default_factory=list)

    # Vital signs
    vital_signs: Dict[str, Any] = field(default_factory=dict)

    # Allergies mentioned
    allergies: List[str] = field(default_factory=list)

    # Current medications (patient's existing meds)
    current_medications: List[str] = field(default_factory=list)

    # Differential diagnoses mentioned
    differentials: List[str] = field(default_factory=list)


@dataclass
class ConversationState:
    """
    Complete state of a conversation at any point.

    This is the core state object passed between the interaction engine,
    evaluation module, and any other consumers.
    """
    # Scenario metadata
    scenario_id: str = ""
    task_type: str = ""
    difficulty: str = ""
    target_disease: str = ""

    # Turns
    turns: List[Turn] = field(default_factory=list)

    # Clinical state
    clinical: ClinicalState = field(default_factory=ClinicalState)

    # Patient state
    patient_trust: float = 0.5
    patient_compliance: float = 0.7
    patient_mood: str = "neutral"

    # Tracking
    total_tool_calls: int = 0
    total_questions: int = 0
    duplicate_actions: int = 0
    is_complete: bool = False
    completion_reason: str = ""  # "diagnosis", "prescription", "max_turns", "patient_left"

    # Tool call history (for duplicate detection)
    _tool_call_history: List[str] = field(default_factory=list)
    _question_history: List[str] = field(default_factory=list)

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    @property
    def agent_turns(self) -> List[Turn]:
        return [t for t in self.turns if t.role == "agent"]

    @property
    def patient_turns(self) -> List[Turn]:
        return [t for t in self.turns if t.role == "patient"]

    def add_turn(self, turn: Turn) -> None:
        """Add a turn and update tracking."""
        self.turns.append(turn)

        # Track tool calls
        if turn.action_type == "call_tool":
            tool_key = f"{turn.tool_name}:{sorted(turn.tool_args.items())}"
            if tool_key in self._tool_call_history:
                self.duplicate_actions += 1
            self._tool_call_history.append(tool_key)
            self.total_tool_calls += 1

        # Track questions
        if turn.action_type == "ask_question":
            q_key = turn.content.lower().strip()
            if q_key in self._question_history:
                self.duplicate_actions += 1
            self._question_history.append(q_key)
            self.total_questions += 1

        # Update clinical state
        self._update_clinical(turn)

        # Update patient state
        self.patient_trust += turn.trust_delta
        self.patient_trust = max(0.0, min(1.0, self.patient_trust))

    def _update_clinical(self, turn: Turn) -> None:
        """Update clinical state from a turn."""
        # Add revealed info to reported symptoms
        for info in turn.revealed_info:
            if info not in self.clinical.reported_symptoms:
                self.clinical.reported_symptoms.append(info)

        # Track tool results
        if turn.tool_result and isinstance(turn.tool_result, dict):
            if "test_name" in turn.tool_result:
                self.clinical.lab_results.append(turn.tool_result)
            elif "results" in turn.tool_result:
                self.clinical.lab_results.extend(turn.tool_result["results"])

        # Track diagnoses
        if turn.action_type == "diagnose" and turn.content:
            self.clinical.diagnoses.append(turn.content)

        # Track prescriptions
        if turn.action_type == "prescribe":
            self.clinical.prescriptions.append({
                "content": turn.content,
                "turn": turn.turn_number,
            })

    def to_dict(self) -> Dict[str, Any]:
        """Serialize conversation state."""
        return {
            "scenario_id": self.scenario_id,
            "task_type": self.task_type,
            "difficulty": self.difficulty,
            "target_disease": self.target_disease,
            "turn_count": self.turn_count,
            "total_tool_calls": self.total_tool_calls,
            "total_questions": self.total_questions,
            "duplicate_actions": self.duplicate_actions,
            "patient_trust": round(self.patient_trust, 3),
            "patient_compliance": round(self.patient_compliance, 3),
            "patient_mood": self.patient_mood,
            "is_complete": self.is_complete,
            "completion_reason": self.completion_reason,
            "clinical": {
                "reported_symptoms": self.clinical.reported_symptoms,
                "lab_results": self.clinical.lab_results,
                "diagnoses": self.clinical.diagnoses,
                "prescriptions": self.clinical.prescriptions,
                "tests_ordered": self.clinical.tests_ordered,
            },
            "turns": [
                {
                    "turn": t.turn_number,
                    "role": t.role,
                    "action": t.action_type,
                    "content": t.content,
                    "revealed": t.revealed_info,
                }
                for t in self.turns
            ],
        }
