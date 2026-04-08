#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Protocol — Clean API for external LLM agents to drive medical environments.

The protocol wraps MedicalEnvironment into a standardized observe-act loop:
1. Agent receives a ProtocolObservation (JSON-serializable)
2. Agent produces a ProtocolAction (function call or message)
3. Environment processes the action and returns next observation
4. Repeat until done

This is the interface between "your LLM" and "our benchmark".
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ..interaction_engine.environment import MedicalEnvironment
from ..interaction_engine.turn_simulator import AgentAction, Observation
from ..scenario_engine.scenario_schema import ScenarioSpec
from ..persona_engine.patient_agent import PatientAgent
from ..clinical_world.symptom_generator import SymptomGenerator, SymptomSet
from ..clinical_world.disease_sampler import DiseaseSampler


# ============================================================
# Tool Definitions — What the agent can do
# ============================================================

@dataclass
class ToolDefinition:
    """Definition of a tool available to the agent."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": list(self.parameters.keys()),
                },
            },
        }


# Standard tool set available to medical agents
TOOL_DEFINITIONS = [
    ToolDefinition(
        name="ask_patient",
        description="Ask the patient a question about their symptoms, history, or concerns.",
        parameters={
            "question": {
                "type": "string",
                "description": "The question to ask the patient.",
            },
        },
    ),
    ToolDefinition(
        name="order_lab",
        description="Order a laboratory test for the patient.",
        parameters={
            "test_name": {
                "type": "string",
                "description": "Name of the lab test to order (e.g., 'CBC', 'BMP', 'HbA1c', 'TSH', 'Urinalysis').",
            },
            "reason": {
                "type": "string",
                "description": "Clinical reason for ordering this test.",
            },
        },
    ),
    ToolDefinition(
        name="order_imaging",
        description="Order an imaging study for the patient.",
        parameters={
            "imaging_type": {
                "type": "string",
                "description": "Type of imaging (e.g., 'chest_xray', 'CT_head', 'MRI_brain', 'ultrasound_abdomen').",
            },
            "reason": {
                "type": "string",
                "description": "Clinical reason for ordering this imaging.",
            },
        },
    ),
    ToolDefinition(
        name="check_drug_interaction",
        description="Check if a medication has interactions with the patient's current medications or conditions.",
        parameters={
            "drug_name": {
                "type": "string",
                "description": "Name of the drug to check.",
            },
        },
    ),
    ToolDefinition(
        name="check_allergies",
        description="Check the patient's allergy history.",
        parameters={
            "drug_class": {
                "type": "string",
                "description": "Optional drug class to specifically check (e.g., 'penicillin', 'sulfa').",
            },
        },
    ),
    ToolDefinition(
        name="make_diagnosis",
        description="Make a clinical diagnosis. Use this when you have gathered enough evidence.",
        parameters={
            "diagnosis": {
                "type": "string",
                "description": "The diagnosis you are making.",
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "moderate", "low"],
                "description": "Your confidence level in this diagnosis.",
            },
            "reasoning": {
                "type": "string",
                "description": "Brief reasoning for this diagnosis.",
            },
        },
    ),
    ToolDefinition(
        name="prescribe",
        description="Prescribe a medication to the patient.",
        parameters={
            "medication": {
                "type": "string",
                "description": "Name of the medication.",
            },
            "dosage": {
                "type": "string",
                "description": "Dosage and frequency (e.g., '500mg twice daily').",
            },
            "duration": {
                "type": "string",
                "description": "Duration of treatment (e.g., '7 days', 'ongoing').",
            },
        },
    ),
    ToolDefinition(
        name="end_conversation",
        description="End the conversation. Use when you have completed diagnosis and treatment, or when you cannot proceed.",
        parameters={
            "summary": {
                "type": "string",
                "description": "Brief summary of what was accomplished.",
            },
        },
    ),
]


# ============================================================
# Protocol Messages — What flows between agent and environment
# ============================================================

@dataclass
class ProtocolObservation:
    """
    Observation sent from environment to agent.
    JSON-serializable for LLM consumption.
    """
    obs_type: str           # "opening", "patient_response", "tool_result", "system", "done"
    content: str            # Main text content
    data: Optional[Dict] = None  # Structured data (lab results, etc.)
    turn_number: int = 0
    available_tools: List[str] = field(default_factory=list)
    is_complete: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "obs_type": self.obs_type,
            "content": self.content,
            "data": self.data,
            "turn_number": self.turn_number,
            "available_tools": self.available_tools,
            "is_complete": self.is_complete,
        }

    def to_prompt(self) -> str:
        """Format as a prompt string for text-based LLMs."""
        parts = [f"[{self.obs_type.upper()}] {self.content}"]
        if self.data:
            parts.append(f"Data: {json.dumps(self.data, indent=2)}")
        if self.available_tools and not self.is_complete:
            parts.append(f"Available tools: {', '.join(self.available_tools)}")
        return "\n".join(parts)


@dataclass
class ProtocolAction:
    """
    Action from agent to environment.
    Can be constructed from OpenAI function call or manually.
    """
    tool_name: str          # Must match a ToolDefinition name
    arguments: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""      # For text-only agents

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
        }


@dataclass
class ProtocolResult:
    """Complete result of running an agent through a scenario."""
    scenario_id: str
    task_type: str
    difficulty: str
    target_disease: str
    agent_diagnosis: str
    diagnosis_correct: bool
    total_turns: int
    total_questions: int
    total_tool_calls: int
    patient_trust_final: float
    completion_reason: str

    # Detailed scores
    outcome_score: float = 0.0
    process_score: float = 0.0
    safety_score: float = 0.0
    total_score: float = 0.0

    # Full history
    observations: List[Dict] = field(default_factory=list)
    actions: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "task_type": self.task_type,
            "difficulty": self.difficulty,
            "target_disease": self.target_disease,
            "agent_diagnosis": self.agent_diagnosis,
            "diagnosis_correct": self.diagnosis_correct,
            "total_turns": self.total_turns,
            "total_questions": self.total_questions,
            "total_tool_calls": self.total_tool_calls,
            "patient_trust_final": round(self.patient_trust_final, 3),
            "completion_reason": self.completion_reason,
            "outcome_score": round(self.outcome_score, 3),
            "process_score": round(self.process_score, 3),
            "safety_score": round(self.safety_score, 3),
            "total_score": round(self.total_score, 3),
        }


# ============================================================
# Agent Protocol — The main interface
# ============================================================

class AgentProtocol:
    """
    Clean API for external LLM agents to interact with medical scenarios.

    Usage:
        # Setup
        protocol = AgentProtocol.from_scenario(scenario, clinical_kb)

        # Get first observation
        obs = protocol.start()

        # Agent loop
        while not obs.is_complete:
            action = your_llm_decide(obs)  # Your LLM picks an action
            obs = protocol.act(action)

        # Get results
        result = protocol.get_result()
    """

    def __init__(
        self,
        env: MedicalEnvironment,
        scenario: ScenarioSpec,
    ):
        self.env = env
        self.scenario = scenario
        self._observations: List[ProtocolObservation] = []
        self._actions: List[ProtocolAction] = []
        self._started = False

    @classmethod
    def from_scenario(
        cls,
        scenario: ScenarioSpec,
        clinical_kb,
        persona_data: Optional[Dict] = None,
    ) -> "AgentProtocol":
        """Build a complete protocol from a scenario spec."""
        # Generate symptoms
        symptom_gen = SymptomGenerator(clinical_kb)
        symptoms = symptom_gen.generate(
            scenario.target_disease or "fatigue",
            scenario,
        )

        # Build patient agent
        patient = PatientAgent.from_scenario(scenario, symptoms, persona_data)

        # Build environment
        env = MedicalEnvironment(scenario, patient, clinical_kb)

        return cls(env, scenario)

    def start(self) -> ProtocolObservation:
        """Start the scenario and get opening observation."""
        raw_obs = self.env.reset()
        obs = self._wrap_observation(raw_obs, 1)
        self._observations.append(obs)
        self._started = True
        return obs

    def act(self, action: ProtocolAction) -> ProtocolObservation:
        """
        Execute an agent action and return next observation.

        Args:
            action: ProtocolAction with tool_name and arguments

        Returns:
            Next ProtocolObservation
        """
        if not self._started:
            raise RuntimeError("Call start() before act()")

        # Convert ProtocolAction to internal AgentAction
        agent_action = self._convert_action(action)
        self._actions.append(action)

        # Execute in environment
        raw_obs = self.env.step(agent_action)

        # Wrap result
        turn_num = self.env.state.turn_count
        obs = self._wrap_observation(raw_obs, turn_num)
        self._observations.append(obs)

        return obs

    def get_tools(self) -> List[ToolDefinition]:
        """Get available tool definitions for this scenario."""
        return TOOL_DEFINITIONS

    def get_tools_openai(self) -> List[Dict[str, Any]]:
        """Get tools in OpenAI function calling format."""
        return [t.to_openai_function() for t in TOOL_DEFINITIONS]

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history as role/content pairs (for LLM context)."""
        messages = []
        for obs in self._observations:
            if obs.obs_type == "opening":
                messages.append({"role": "user", "content": obs.content})
            elif obs.obs_type == "patient_response":
                messages.append({"role": "user", "content": f"Patient: {obs.content}"})
            elif obs.obs_type == "tool_result":
                messages.append({"role": "system", "content": f"Tool result: {obs.content}"})
            elif obs.obs_type == "system":
                messages.append({"role": "system", "content": obs.content})
            elif obs.obs_type == "done":
                messages.append({"role": "system", "content": obs.content})

        # Interleave agent actions
        action_messages = []
        for action in self._actions:
            args_str = ", ".join(f"{k}={v}" for k, v in action.arguments.items())
            action_messages.append(f"Doctor [{action.tool_name}]: {args_str}")

        # Merge: observations and actions interleaved
        merged = []
        obs_idx = 0
        act_idx = 0
        # First observation is the opening, then alternate action -> observation
        if self._observations:
            merged.append(messages[0])
            obs_idx = 1

        for act_msg in action_messages:
            merged.append({"role": "assistant", "content": act_msg})
            if obs_idx < len(messages):
                merged.append(messages[obs_idx])
                obs_idx += 1

        # Remaining observations
        while obs_idx < len(messages):
            merged.append(messages[obs_idx])
            obs_idx += 1

        return merged

    def get_result(self) -> ProtocolResult:
        """Get final result after scenario completes."""
        state = self.env.get_state()
        eval_state = self.env.get_evaluation_state()

        # Extract diagnosis
        diagnoses = state.clinical.diagnoses
        agent_diagnosis = diagnoses[-1] if diagnoses else ""
        correct = agent_diagnosis.lower() == (self.scenario.target_disease or "").lower()

        return ProtocolResult(
            scenario_id=self.scenario.scenario_id,
            task_type=self.scenario.task_type,
            difficulty=self.scenario.difficulty,
            target_disease=self.scenario.target_disease or "",
            agent_diagnosis=agent_diagnosis,
            diagnosis_correct=correct,
            total_turns=state.turn_count,
            total_questions=state.total_questions,
            total_tool_calls=state.total_tool_calls,
            patient_trust_final=state.patient_trust,
            completion_reason=state.completion_reason,
            observations=[o.to_dict() for o in self._observations],
            actions=[a.to_dict() for a in self._actions],
        )

    def evaluate(self) -> ProtocolResult:
        """Run full evaluation and return scored result."""
        from ..evaluation_v2.outcome_evaluator import OutcomeEvaluator
        from ..evaluation_v2.process_evaluator import ProcessEvaluator
        from ..evaluation_v2.safety_evaluator import SafetyEvaluator
        from ..evaluation_v2.adaptive_weights import compute_total_score

        result = self.get_result()
        state = self.env.get_evaluation_state()

        # Run evaluators
        outcome = OutcomeEvaluator().evaluate(self.scenario, state)
        process = ProcessEvaluator().evaluate(self.scenario, self.env.state)
        safety = SafetyEvaluator().evaluate(self.scenario, state)

        result.outcome_score = outcome.total_score
        result.process_score = process.total_score
        result.safety_score = safety.total_score
        result.total_score = compute_total_score(
            self.scenario.task_type,
            outcome.total_score,
            process.total_score,
            safety.total_score,
        )

        return result

    # ================================================================
    # Internal
    # ================================================================

    def _convert_action(self, action: ProtocolAction) -> AgentAction:
        """Convert ProtocolAction to internal AgentAction."""
        args = action.arguments

        if action.tool_name == "ask_patient":
            return AgentAction(
                action_type="ask_question",
                content=args.get("question", args.get("content", "")),
            )
        elif action.tool_name in ("order_lab", "order_imaging"):
            tool_map = {
                "order_lab": "order_lab_test",
                "order_imaging": "order_imaging",
            }
            return AgentAction(
                action_type="call_tool",
                tool_name=tool_map[action.tool_name],
                content=args.get("reason", ""),
                tool_args={
                    "test_name": args.get("test_name", args.get("imaging_type", "")),
                },
            )
        elif action.tool_name == "check_drug_interaction":
            return AgentAction(
                action_type="call_tool",
                tool_name="check_drug_interaction",
                content=args.get("drug_name", ""),
                tool_args={"drug_name": args.get("drug_name", "")},
            )
        elif action.tool_name == "check_allergies":
            return AgentAction(
                action_type="call_tool",
                tool_name="check_allergies",
                content=args.get("drug_class", ""),
                tool_args={"drug_class": args.get("drug_class", "")},
            )
        elif action.tool_name == "make_diagnosis":
            return AgentAction(
                action_type="diagnose",
                content=args.get("diagnosis", ""),
            )
        elif action.tool_name == "prescribe":
            med = args.get("medication", "")
            dosage = args.get("dosage", "")
            duration = args.get("duration", "")
            return AgentAction(
                action_type="prescribe",
                content=f"{med} {dosage} {duration}".strip(),
            )
        elif action.tool_name == "end_conversation":
            return AgentAction(
                action_type="end",
                content=args.get("summary", ""),
            )
        else:
            # Fallback: treat as a question
            return AgentAction(
                action_type="ask_question",
                content=action.raw_text or action.tool_name,
            )

    def _wrap_observation(self, raw: Observation, turn_num: int) -> ProtocolObservation:
        """Wrap internal Observation into ProtocolObservation."""
        tool_names = [t.name for t in TOOL_DEFINITIONS]

        data = None
        if raw.data and isinstance(raw.data, dict):
            data = raw.data

        return ProtocolObservation(
            obs_type=raw.obs_type,
            content=raw.content,
            data=data,
            turn_number=turn_num,
            available_tools=tool_names if not self.env.state.is_complete else [],
            is_complete=self.env.state.is_complete,
            metadata={"revealed_info": raw.revealed_info} if raw.revealed_info else {},
        )
