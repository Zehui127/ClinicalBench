#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turn Simulator — Simulate one turn of the interaction.

Wraps the step logic: given an agent action, produces the patient
response and tool results, then updates conversation state.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .state_manager import ConversationState, Turn
from .tool_router import ToolRouter, ToolCall, ToolResult
from ..scenario_engine.scenario_schema import ScenarioSpec
from ..persona_engine.patient_agent import PatientAgent


@dataclass
class AgentAction:
    """An action taken by the agent (doctor)."""
    action_type: str  # ask_question, call_tool, diagnose, prescribe, end
    content: str = ""
    tool_name: str = ""
    tool_args: Dict[str, Any] = None

    def __post_init__(self):
        if self.tool_args is None:
            self.tool_args = {}


@dataclass
class Observation:
    """What the agent observes after an action."""
    obs_type: str  # patient_response, tool_result, system_message, done
    content: str = ""
    data: Any = None
    revealed_info: List[str] = None

    def __post_init__(self):
        if self.revealed_info is None:
            self.revealed_info = []


class TurnSimulator:
    """
    Simulate one turn of the medical interaction.

    Usage:
        sim = TurnSimulator(patient, tool_router, scenario, state)
        obs = sim.step(AgentAction("ask_question", content="What brings you here?"))
    """

    def __init__(
        self,
        patient: PatientAgent,
        tool_router: ToolRouter,
        scenario: ScenarioSpec,
        state: ConversationState,
    ):
        self.patient = patient
        self.router = tool_router
        self.scenario = scenario
        self.state = state

    def step(self, action: AgentAction) -> Observation:
        """
        Process one agent action and return observation.

        Args:
            action: What the agent did

        Returns:
            Observation with patient response, tool result, or status
        """
        turn_num = self.state.turn_count + 1

        if action.action_type == "ask_question":
            return self._handle_question(action, turn_num)
        elif action.action_type == "call_tool":
            return self._handle_tool(action, turn_num)
        elif action.action_type == "diagnose":
            return self._handle_diagnosis(action, turn_num)
        elif action.action_type == "prescribe":
            return self._handle_prescription(action, turn_num)
        elif action.action_type == "end":
            return self._handle_end(action, turn_num)
        else:
            return Observation(
                obs_type="system_message",
                content=f"Unknown action type: {action.action_type}",
            )

    def _handle_question(self, action: AgentAction, turn_num: int) -> Observation:
        """Handle an ask_question action."""
        # Record agent turn
        agent_turn = Turn(
            turn_number=turn_num,
            role="agent",
            action_type="ask_question",
            content=action.content,
        )
        self.state.add_turn(agent_turn)

        # Get patient response
        patient_resp = self.patient.respond("ask_question", action.content)

        # Record patient turn
        patient_turn = Turn(
            turn_number=turn_num + 1,
            role="patient",
            action_type="respond",
            content=patient_resp["response"],
            revealed_info=patient_resp["revealed"],
            trust_delta=patient_resp["trust_change"],
        )
        self.state.add_turn(patient_turn)

        return Observation(
            obs_type="patient_response",
            content=patient_resp["response"],
            revealed_info=patient_resp["revealed"],
            data=patient_resp,
        )

    def _handle_tool(self, action: AgentAction, turn_num: int) -> Observation:
        """Handle a call_tool action."""
        # Record agent turn
        agent_turn = Turn(
            turn_number=turn_num,
            role="agent",
            action_type="call_tool",
            content=f"Ordering: {action.tool_name}",
            tool_name=action.tool_name,
            tool_args=action.tool_args,
        )
        self.state.add_turn(agent_turn)

        # Execute tool
        tool_call = ToolCall(
            tool_name=action.tool_name,
            args=action.tool_args,
        )
        tool_result = self.router.execute(tool_call, self.scenario)

        # Record tool result turn
        result_turn = Turn(
            turn_number=turn_num + 1,
            role="system",
            action_type="tool_result",
            content=str(tool_result.result) if tool_result.success else tool_result.error,
            tool_name=action.tool_name,
            tool_result=tool_result.result if tool_result.success else None,
        )
        self.state.add_turn(result_turn)

        return Observation(
            obs_type="tool_result",
            content=str(tool_result.result) if tool_result.success else tool_result.error,
            data=tool_result.result if tool_result.success else {"error": tool_result.error},
        )

    def _handle_diagnosis(self, action: AgentAction, turn_num: int) -> Observation:
        """Handle a diagnose action."""
        # Record agent turn
        agent_turn = Turn(
            turn_number=turn_num,
            role="agent",
            action_type="diagnose",
            content=action.content,
        )
        self.state.add_turn(agent_turn)

        # Check correctness
        correct = action.content.lower() == (self.scenario.target_disease or "").lower()

        # Get patient response to diagnosis
        patient_resp = self.patient.respond("diagnose", action.content)

        patient_turn = Turn(
            turn_number=turn_num + 1,
            role="patient",
            action_type="respond",
            content=patient_resp["response"],
            trust_delta=patient_resp["trust_change"],
        )
        self.state.add_turn(patient_turn)

        return Observation(
            obs_type="patient_response",
            content=patient_resp["response"],
            data={"diagnosis_correct": correct},
        )

    def _handle_prescription(self, action: AgentAction, turn_num: int) -> Observation:
        """Handle a prescribe action."""
        agent_turn = Turn(
            turn_number=turn_num,
            role="agent",
            action_type="prescribe",
            content=action.content,
        )
        self.state.add_turn(agent_turn)

        patient_resp = self.patient.respond("prescribe", action.content)

        patient_turn = Turn(
            turn_number=turn_num + 1,
            role="patient",
            action_type="respond",
            content=patient_resp["response"],
            trust_delta=patient_resp["trust_change"],
        )
        self.state.add_turn(patient_turn)

        return Observation(
            obs_type="patient_response",
            content=patient_resp["response"],
            data=patient_resp,
        )

    def _handle_end(self, action: AgentAction, turn_num: int) -> Observation:
        """Handle conversation end."""
        self.state.is_complete = True
        self.state.completion_reason = action.content or "agent_ended"

        return Observation(
            obs_type="done",
            content="Conversation ended.",
        )
