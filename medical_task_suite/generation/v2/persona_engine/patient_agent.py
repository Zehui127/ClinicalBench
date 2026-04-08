#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patient Agent — The patient as a strategic, stochastic information holder.

v2.1: Patient is now truly stochastic:
- Refusal probability depends on trust level
- Information revelation is probabilistic, not deterministic
- Patient mood evolves based on agent behavior
- Agent's actions change the world state
"""

import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ..scenario_engine.scenario_schema import ScenarioSpec, ScenarioConstraints
from ..clinical_world.symptom_generator import SymptomSet
from ..clinical_world.patient_language import PatientLanguageLayer
from .info_policy import InfoPolicy, SymptomVisibility
from .behavior_model import BehaviorModel, BehavioralState


def _behavior_to_goal(behavior_type: str) -> str:
    """Map behavior type to patient goal."""
    goal_map = {
        "cooperative": "get_help",
        "forgetful": "get_help",
        "confused": "get_help",
        "concealing": "avoid_bad_news",
        "pressuring": "finish_quickly",
        "refusing": "avoid_bad_news",
    }
    return goal_map.get(behavior_type, "get_help")


@dataclass
class DecisionPolicy:
    """
    How the patient decides what to reveal.
    v2.1: probabilities are BASELINES, actual behavior is stochastic.
    """
    goal: str = "get_help"
    initial_trust: float = 0.5
    compliance_level: float = 0.7
    reveal_probability: float = 0.6
    hide_if_not_asked: bool = False
    refuse_tests: List[str] = field(default_factory=list)
    refuse_medications: List[str] = field(default_factory=list)
    challenge_count: int = 0
    concerns: List[str] = field(default_factory=list)
    fears: List[str] = field(default_factory=list)

    @classmethod
    def from_scenario(cls, scenario: ScenarioSpec) -> "DecisionPolicy":
        """Generate decision policy using calibrated ranges when available."""
        c = scenario.constraints

        # v2.7: Try calibrated data first
        try:
            from .calibrated_defaults import DEPARTMENT_CALIBRATIONS
            cal = DEPARTMENT_CALIBRATIONS.get(scenario.behavior_type,
                                               DEPARTMENT_CALIBRATIONS.get("cooperative"))
            if cal:
                policy = cls(
                    goal=_behavior_to_goal(scenario.behavior_type),
                    initial_trust=random.uniform(*cal["trust_range"]),
                    compliance_level=random.uniform(*cal["compliance_range"]),
                    reveal_probability=random.uniform(*cal["reveal_prob_range"]),
                    hide_if_not_asked=scenario.behavior_type in ("concealing", "refusing"),
                    challenge_count=2 if scenario.behavior_type == "pressuring" else (
                        3 if scenario.behavior_type == "refusing" else 0
                    ),
                )
                # Override with constraint-driven values
                if c.patient_refusal_probability > 0:
                    policy.compliance_level = max(0.1, 1.0 - c.patient_refusal_probability)
                return policy
        except ImportError:
            pass

        # Fallback: original hand-coded presets
        policies = {
            "cooperative": cls(
                goal="get_help",
                initial_trust=0.7,
                compliance_level=0.9,
                reveal_probability=0.8,
            ),
            "forgetful": cls(
                goal="get_help",
                initial_trust=0.6,
                compliance_level=0.7,
                reveal_probability=0.4,
            ),
            "confused": cls(
                goal="get_help",
                initial_trust=0.5,
                compliance_level=0.5,
                reveal_probability=0.3,
            ),
            "concealing": cls(
                goal="avoid_bad_news",
                initial_trust=0.3,
                compliance_level=0.4,
                reveal_probability=0.2,
                hide_if_not_asked=True,
            ),
            "pressuring": cls(
                goal="finish_quickly",
                initial_trust=0.4,
                compliance_level=0.6,
                reveal_probability=0.5,
                challenge_count=2,
            ),
            "refusing": cls(
                goal="avoid_bad_news",
                initial_trust=0.2,
                compliance_level=0.2,
                reveal_probability=0.15,
                hide_if_not_asked=True,
                challenge_count=3,
            ),
        }
        policy = policies.get(scenario.behavior_type, policies["cooperative"])

        # Override with constraint-driven values
        if c.patient_refusal_probability > 0:
            policy.compliance_level = max(0.1, 1.0 - c.patient_refusal_probability)

        return policy


class PatientAgent:
    """
    A patient agent with stochastic decision policy.

    v2.1: Agent actions CHANGE the world:
    - Trust goes up/down based on agent approach
    - Compliance is probabilistic based on current trust
    - Information revelation is stochastic
    - Refusal depends on trust level, not just behavior type
    """

    def __init__(
        self,
        policy: DecisionPolicy,
        symptoms: SymptomSet,
        disease: str,
        constraints: Optional[ScenarioConstraints] = None,
        persona_data: Optional[Dict] = None,
    ):
        self.policy = policy
        self.symptoms = symptoms
        self.disease = disease
        self.constraints = constraints or ScenarioConstraints()
        self.persona_data = persona_data or {}

        self.info_policy = InfoPolicy(symptoms, policy)
        self.behavior = BehaviorModel(policy)
        self.language = PatientLanguageLayer()
        self.revealed_info: set = set()
        self.asked_about: set = set()
        self.turn_count = 0

        # Stochastic state
        self._rng = random.Random()

    @classmethod
    def from_scenario(
        cls,
        scenario: ScenarioSpec,
        symptoms: SymptomSet,
        persona_data: Optional[Dict] = None,
    ) -> "PatientAgent":
        policy = DecisionPolicy.from_scenario(scenario)
        return cls(policy, symptoms, scenario.target_disease, scenario.constraints, persona_data)

    def respond(
        self,
        doctor_action: str,
        doctor_content: str = "",
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Generate stochastic patient response."""
        self.turn_count += 1
        context = context or {}

        # Update behavior state (trust changes based on doctor action)
        behavioral_state = self.behavior.update(doctor_action, context)

        # Route to handler
        if doctor_action == "ask_question":
            return self._respond_to_question(doctor_content, behavioral_state, context)
        elif doctor_action == "prescribe":
            return self._respond_to_prescription(doctor_content, behavioral_state)
        elif doctor_action == "call_tool":
            return self._respond_to_tool(doctor_content, behavioral_state)
        elif doctor_action == "diagnose":
            return self._respond_to_diagnosis(doctor_content, behavioral_state)
        else:
            return self._respond_generic(behavioral_state)

    def get_opening_statement(self) -> str:
        """Generate the patient's opening statement (stochastic, patient-friendly language)."""
        volunteer = self.symptoms.volunteer[:3]
        if not volunteer:
            return "I'm not feeling well."

        # Stochastic: may not mention all volunteer symptoms
        n_mention = max(1, sum(1 for s in volunteer if self._rng.random() < self.policy.reveal_probability))
        mentioned = volunteer[:n_mention]

        # Convert clinical terms to patient-friendly language
        patient_terms = [self.language.to_patient(s) for s in mentioned]

        state = self.behavior.current_state
        mood = state.mood
        return self.language.generate_complaint(self.disease, patient_terms, mood)

    # ================================================================
    # Stochastic response handlers
    # ================================================================

    def _respond_to_question(
        self, question: str, state: BehavioralState, context: Dict
    ) -> Dict[str, Any]:
        """Stochastic question response — trust-gated revelation."""
        newly_revealed = []
        response_parts = []
        trust_change = 0.0

        # Check if question is empathetic → trust gain
        if self._is_empathetic(question, context):
            trust_change = self.constraints.trust_gain_per_empathy
        elif self._is_dismissive(question, context):
            trust_change = -self.constraints.trust_loss_per_dismissal

        # Process if_asked symptoms
        for symptom in self.symptoms.if_asked:
            if symptom.lower() in question.lower() and symptom not in self.revealed_info:
                # Stochastic reveal based on trust + base probability
                reveal_prob = min(1.0, state.trust + self.policy.reveal_probability) / 2
                if self._rng.random() < reveal_prob:
                    newly_revealed.append(symptom)
                    self.revealed_info.add(symptom)
                    response_parts.append(self.language.symptom_to_response(symptom, "if_asked"))

        # Process resistant symptoms (need higher trust)
        for symptom in self.symptoms.resistant:
            if symptom.lower() in question.lower() and symptom not in self.revealed_info:
                # Trust-gated: only reveal if trust > threshold
                threshold = 0.5 if not self.policy.hide_if_not_asked else 0.7
                if state.trust > threshold and self._rng.random() < state.trust * 0.7:
                    newly_revealed.append(symptom)
                    self.revealed_info.add(symptom)
                    response_parts.append(self.language.symptom_to_response(symptom, "resistant"))
                else:
                    response_parts.append(self._deflect(symptom, state))

        # Process hidden symptoms (only with specific probe + high trust)
        for symptom in self.symptoms.hidden:
            if symptom.lower() in question.lower() and symptom not in self.revealed_info:
                if state.trust > 0.7 and self._rng.random() < state.trust * 0.5:
                    newly_revealed.append(symptom)
                    self.revealed_info.add(symptom)
                    response_parts.append(self.language.symptom_to_response(symptom, "hidden"))

        # Noise symptoms (stochastic — may or may not mention)
        if any(w in question.lower() for w in ["else", "other", "anything more", "additional"]):
            for noise in self.symptoms.noise[:2]:
                if noise not in self.revealed_info and self._rng.random() < 0.7:
                    newly_revealed.append(noise)
                    self.revealed_info.add(noise)
                    patient_term = self.language.to_patient(noise)
                    response_parts.append(f"I've also been having some {patient_term}.")

        # Misleading symptoms (volunteered readily — that's the point)
        if any(w in question.lower() for w in ["else", "other", "anything more"]):
            for ms in self.symptoms.misleading[:1]:
                if ms not in self.revealed_info and self._rng.random() < 0.8:
                    newly_revealed.append(ms)
                    self.revealed_info.add(ms)
                    patient_term = self.language.to_patient(ms)
                    response_parts.append(f"Oh yeah, I've also had {patient_term}.")

        if not response_parts:
            response_parts.append(self._generic_response(question, state))

        return {
            "response": " ".join(response_parts),
            "revealed": newly_revealed,
            "behavior": state.behavior_type,
            "trust_change": trust_change,
            "compliance": state.compliance,
        }

    def _respond_to_prescription(
        self, content: str, state: BehavioralState
    ) -> Dict[str, Any]:
        """Stochastic prescription response — trust-gated refusal."""
        # Check refusal probability (stochastic, trust-dependent)
        refusal_prob = max(0.0, (1.0 - state.trust) * self.constraints.patient_refusal_probability)

        # Specific medication refusal
        for med in self.policy.refuse_medications:
            if med.lower() in content.lower():
                refusal_prob = max(refusal_prob, 0.6)

        if self._rng.random() < refusal_prob:
            return {
                "response": self._refuse_response(content, state),
                "revealed": [],
                "behavior": state.behavior_type,
                "trust_change": -0.05,
                "compliance": state.compliance,
                "patient_refused": True,
            }

        return {
            "response": "Okay, I'll take that. Are there any side effects I should know about?",
            "revealed": [],
            "behavior": state.behavior_type,
            "trust_change": 0.1,
            "compliance": state.compliance,
            "patient_refused": False,
        }

    def _respond_to_tool(
        self, content: str, state: BehavioralState
    ) -> Dict[str, Any]:
        """Stochastic tool response — trust-gated test refusal."""
        refusal_prob = max(0.0, (1.0 - state.trust) * self.constraints.patient_refusal_probability)

        for test in self.policy.refuse_tests:
            if test.lower() in content.lower():
                refusal_prob = max(refusal_prob, 0.5)

        if self._rng.random() < refusal_prob:
            return {
                "response": self._refuse_test(content, state),
                "revealed": [],
                "behavior": state.behavior_type,
                "trust_change": -0.05,
                "compliance": state.compliance,
                "patient_refused": True,
            }

        return {
            "response": "Okay, when will I get the results?",
            "revealed": [],
            "behavior": state.behavior_type,
            "trust_change": 0.05,
            "compliance": state.compliance,
            "patient_refused": False,
        }

    def _respond_to_diagnosis(
        self, content: str, state: BehavioralState
    ) -> Dict[str, Any]:
        """Stochastic diagnosis response."""
        if self.policy.goal == "avoid_bad_news" and self._rng.random() < 0.4:
            return {
                "response": "Are you sure? Is it possible it's something less serious?",
                "revealed": [],
                "behavior": state.behavior_type,
                "trust_change": -0.1,
                "compliance": state.compliance,
            }
        return {
            "response": "Thank you for explaining. What's the treatment plan?",
            "revealed": [],
            "behavior": state.behavior_type,
            "trust_change": 0.15,
            "compliance": state.compliance,
        }

    def _respond_generic(self, state: BehavioralState) -> Dict[str, Any]:
        return {
            "response": self._generic_response("", state),
            "revealed": [],
            "behavior": state.behavior_type,
            "trust_change": 0,
            "compliance": state.compliance,
        }

    # ================================================================
    # Stochastic helpers
    # ================================================================

    def _is_empathetic(self, text: str, context: Dict) -> bool:
        """Detect empathetic doctor behavior."""
        empathetic_words = ["understand", "sorry", "worry", "concern", "how do you feel", "that must be"]
        text_lower = text.lower()
        if any(w in text_lower for w in empathetic_words):
            return True
        return context.get("empathetic", False)

    def _is_dismissive(self, text: str, context: Dict) -> bool:
        """Detect dismissive doctor behavior."""
        dismissive_words = ["just", "don't worry", "it's nothing", "that's normal", "move on"]
        text_lower = text.lower()
        if any(w in text_lower for w in dismissive_words):
            return True
        return context.get("dismissive", False)

    def _deflect(self, symptom: str, state: BehavioralState) -> str:
        """Generate stochastic deflection."""
        deflections_by_trust = {
            "high": ["I think that's getting better actually.", "It comes and goes."],
            "medium": ["That's not really a big deal.", "I'd rather not talk about that."],
            "low": ["That's none of your business.", "Why do you need to know that?"],
        }
        trust_band = "high" if state.trust > 0.6 else ("medium" if state.trust > 0.3 else "low")
        return self._rng.choice(deflections_by_trust[trust_band])

    def _refuse_response(self, content: str, state: BehavioralState) -> str:
        """Generate stochastic refusal."""
        refusals = [
            f"I'd rather not take that. Is there an alternative?",
            "I don't like taking medications. Do I really need this?",
            "I've heard bad things about that drug. Can we try something else?",
            "Let me think about it. What are the side effects?",
        ]
        return self._rng.choice(refusals)

    def _refuse_test(self, content: str, state: BehavioralState) -> str:
        """Generate stochastic test refusal."""
        refusals = [
            "Do I really need that test? It seems unnecessary.",
            "I'd prefer not to. Can you just figure it out without more tests?",
            "Is that going to be expensive? I'm not sure about that.",
            "Can we try something less invasive first?",
        ]
        return self._rng.choice(refusals)

    def _generic_response(self, question: str, state: BehavioralState) -> str:
        """Generate stochastic generic response."""
        responses = {
            "anxious": ["I'm just really worried about what's going on.", "Is it serious?", "I can't stop thinking about it."],
            "reluctant": ["I'm not sure. Can we move on?", "I don't want to talk about that.", "Why does it matter?"],
            "hurried": ["Look, can we just figure this out?", "How much longer is this going to take?", "Just give me something for it."],
            "reassured": ["That makes sense.", "Thank you for explaining.", "I appreciate your help."],
        }
        pool = responses.get(state.mood, ["I understand.", "Okay.", "Alright."])
        return self._rng.choice(pool)
