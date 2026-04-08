#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Environment — The core game loop.

v2.1: Agent decisions now CHANGE the world:
- Patient state evolves based on agent behavior
- Red flag consequences (patient deteriorates if missed)
- Lab delays (results arrive after N turns)
- Turn cost penalty from constraints
- Constraint violations tracked and enforced
"""

from typing import Dict, List, Optional, Any

from .state_manager import ConversationState, Turn
from .turn_simulator import TurnSimulator, AgentAction, Observation
from .tool_router import ToolRouter
from ..scenario_engine.scenario_schema import ScenarioSpec
from ..persona_engine.patient_agent import PatientAgent
from ..clinical_world.lab_generator import LabGenerator
from ..clinical_world.guideline_engine import GuidelineEngine


class MedicalEnvironment:
    """
    The medical interaction environment — the core game loop.

    v2.1: Agent actions have consequences:
    - Missing red flags → patient deteriorates
    - Poor communication → trust drops → less info revealed
    - Ordering too many tests → cost penalty
    - Taking too long → turn cost penalty
    """

    def __init__(
        self,
        scenario: ScenarioSpec,
        patient: PatientAgent,
        clinical_kb,
        max_turns: int = None,
    ):
        self.scenario = scenario
        self.patient = patient
        self.kb = clinical_kb
        # Use constraint-driven max turns (not arbitrary)
        self.max_turns = max_turns or scenario.constraints.max_turns

        self.lab_gen = LabGenerator(clinical_kb)
        self.guidelines = GuidelineEngine(clinical_kb)
        self.router = ToolRouter(clinical_kb, self.lab_gen, self.guidelines)

        self.state = ConversationState(
            scenario_id=scenario.scenario_id,
            task_type=scenario.task_type,
            difficulty=scenario.difficulty,
            target_disease=scenario.target_disease or "",
            patient_trust=patient.policy.initial_trust,
            patient_compliance=patient.policy.compliance_level,
            patient_mood=patient.behavior.current_state.mood,
        )

        self.simulator = TurnSimulator(patient, self.router, scenario, self.state)
        self._initialized = False
        self._constraint_violations: List[str] = []
        self._turn_cost_total: float = 0.0

    def reset(self) -> Observation:
        """Reset environment and get opening observation."""
        self._initialized = True
        opening = self.patient.get_opening_statement()

        opening_turn = Turn(
            turn_number=1,
            role="patient",
            action_type="opening",
            content=opening,
            revealed_info=self.patient.symptoms.volunteer[:3],
        )
        self.state.add_turn(opening_turn)
        return Observation(obs_type="patient_response", content=opening, revealed_info=self.patient.symptoms.volunteer[:3])

    def step(self, action: AgentAction) -> Observation:
        """Process one agent action with consequences."""
        if not self._initialized:
            raise RuntimeError("Call reset() before step()")

        # Check max turns (from constraints)
        if self.state.turn_count >= self.max_turns:
            self.state.is_complete = True
            self.state.completion_reason = "max_turns"
            self._constraint_violations.append("exceeded_max_turns")
            return Observation(obs_type="done", content="Maximum turns reached.")

        # Process action
        obs = self.simulator.step(action)

        # Apply turn cost penalty
        turn_cost = self.scenario.constraints.turn_cost
        if turn_cost > 0:
            self._turn_cost_total += turn_cost

        # Check for delayed lab results
        delayed = self.router.get_pending_results(self.state.turn_count)
        if delayed:
            # Append delayed results as system messages
            for dr in delayed:
                delayed_turn = Turn(
                    turn_number=self.state.turn_count + 1,
                    role="system",
                    action_type="delayed_result",
                    content=f"Delayed results now available: {dr['tool_name']}",
                    tool_name=dr["tool_name"],
                    tool_result=dr["result"],
                )
                self.state.add_turn(delayed_turn)

        # Check red flag consequences
        consequence = self._check_consequences(action)
        if consequence:
            # Apply consequence: patient deteriorates
            self.state.patient_trust = max(0.0, self.state.patient_trust + consequence.get("trust_impact", 0))
            self.state.patient_mood = "anxious"

            # Add consequence observation
            consequence_turn = Turn(
                turn_number=self.state.turn_count + 1,
                role="system",
                action_type="consequence",
                content=consequence["message"],
            )
            self.state.add_turn(consequence_turn)

        # Check constraint violations
        self._check_constraints()

        # Check completion
        self._check_completion(action)

        return obs

    def get_state(self) -> ConversationState:
        return self.state

    def get_available_tools(self) -> List[Dict[str, Any]]:
        return self.router.get_available_tools(self.scenario)

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get resource cost summary."""
        return {
            **self.router.get_cost_summary(),
            "turn_cost_total": round(self._turn_cost_total, 3),
            "constraint_violations": self._constraint_violations,
        }

    def get_evaluation_state(self) -> Dict[str, Any]:
        """Get state dict for evaluation (includes constraint violations)."""
        return {
            "turn_count": self.state.turn_count,
            "question_count": self.state.total_questions,
            "diagnosed": len(self.state.clinical.diagnoses) > 0,
            "diagnoses": self.state.clinical.diagnoses,
            "reported_symptoms": self.state.clinical.reported_symptoms,
            "patient_trust": self.state.patient_trust,
            "patient_compliance": self.state.patient_compliance,
            "patient_mood": self.state.patient_mood,
            "constraint_violations": self._constraint_violations,
            "turn_cost_total": self._turn_cost_total,
            "cost_summary": self.router.get_cost_summary(),
            "missed_red_flags": self.router.missed_red_flags,
            # v2.4: Include turns for step-level counterfactual analysis
            "turns": [
                {
                    "turn_number": t.turn_number,
                    "role": t.role,
                    "action_type": t.action_type,
                    "content": t.content,
                    "tool_name": t.tool_name,
                }
                for t in self.state.turns
            ],
        }

    # ================================================================
    # Consequence engine
    # ================================================================

    def _check_consequences(self, action: AgentAction) -> Optional[Dict[str, Any]]:
        """Check if agent's action triggers consequences."""
        # Build state for red flag check
        state_dict = {
            "reported_symptoms": self.state.clinical.reported_symptoms,
            "agent_addressed_red_flag": self._agent_addressed_red_flag(action),
        }
        return self.router.check_red_flag_consequence(self.scenario, state_dict)

    def _agent_addressed_red_flag(self, action: AgentAction) -> bool:
        """Check if agent's current action addresses a red flag."""
        red_flag_words = ["emergency", "urgent", "immediate", "critical", "serious", "life-threatening"]
        content = action.content.lower()
        return any(w in content for w in red_flag_words)

    def _check_constraints(self) -> None:
        """Check constraint violations."""
        state_dict = {
            "question_count": self.state.total_questions,
            "diagnosed": len(self.state.clinical.diagnoses) > 0,
            "turn_count": self.state.turn_count,
        }
        violations = self.scenario.constraints.check_violated(state_dict)
        self._constraint_violations.extend(violations)

    def _check_completion(self, action: AgentAction) -> None:
        """Check if conversation should end."""
        if self.state.is_complete:
            return
        if action.action_type == "end":
            self.state.is_complete = True
            self.state.completion_reason = "agent_ended"
            return
        if self.state.clinical.diagnoses and self.state.clinical.prescriptions:
            self.state.is_complete = True
            self.state.completion_reason = "diagnosis_and_treatment"
            return
        if (action.action_type == "diagnose" and
            self.scenario.task_type in ("diagnostic_uncertainty", "conflicting_evidence", "emergency_triage")):
            self.state.is_complete = True
            self.state.completion_reason = "diagnosis_only"
            return
