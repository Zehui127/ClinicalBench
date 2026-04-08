#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Behavior Model — Trust/compliance dynamics that evolve during conversation.

Unlike static behavior_type, BehavioralState evolves as the conversation
progresses. Trust increases when the doctor is empathetic, decreases
when they're dismissive or pushy.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class MoodType(str, Enum):
    NEUTRAL = "neutral"
    ANXIOUS = "anxious"
    RELUCTANT = "reluctant"
    HURRIED = "hurried"
    ANGRY = "angry"
    REASSURED = "reassured"


@dataclass
class BehavioralState:
    """Current behavioral state of the patient."""
    behavior_type: str = "cooperative"
    mood: str = "neutral"
    trust: float = 0.5
    compliance: float = 0.7
    openness: float = 0.6  # Willingness to share information
    turn_count: int = 0
    patience_remaining: int = 20  # Turns before patient gets frustrated

    # Event tracking
    trust_events: List[str] = field(default_factory=list)


# Trust modifiers for different doctor actions
TRUST_MODIFIERS = {
    # Positive actions
    "empathy": 0.15,
    "explanation": 0.1,
    "listening": 0.08,
    "shared_decision": 0.12,
    "reassurance": 0.1,
    "thoroughness": 0.05,

    # Negative actions
    "dismissal": -0.2,
    "rudeness": -0.15,
    "rushing": -0.1,
    "ignoring_concerns": -0.15,
    "jargon": -0.05,
    "repeated_questions": -0.08,
}

# Mood transitions
MOOD_TRANSITIONS = {
    ("cooperative", "empathy"): "reassured",
    ("cooperative", "dismissal"): "reluctant",
    ("anxious", "reassurance"): "reassured",
    ("anxious", "rushing"): "anxious",
    ("reluctant", "empathy"): "neutral",
    ("reluctant", "rushing"): "angry",
    ("hurried", "thoroughness"): "neutral",
    ("hurried", "rushing"): "angry",
}


class BehaviorModel:
    """
    Model patient behavior dynamics during a conversation.

    v2.7: Uses calibrated trust modifiers when available.

    Usage:
        model = BehaviorModel(policy)
        state = model.update("ask_question", {"empathetic": True})
        print(state.trust, state.mood)
    """

    def __init__(self, policy):
        """
        Args:
            policy: DecisionPolicy with initial trust, compliance, etc.
        """
        self.policy = policy
        self.trust_modifiers = self._load_calibrated_modifiers()
        self.current_state = BehavioralState(
            behavior_type=policy.goal,
            mood=self._initial_mood(policy.goal),
            trust=policy.initial_trust,
            compliance=policy.compliance_level,
            openness=policy.reveal_probability,
        )

    @staticmethod
    def _load_calibrated_modifiers() -> Dict[str, float]:
        """Load calibrated trust modifiers, fall back to defaults."""
        try:
            from .calibrated_defaults import CALIBRATED_TRUST_MODIFIERS
            return CALIBRATED_TRUST_MODIFIERS
        except ImportError:
            return dict(TRUST_MODIFIERS)

    def update(
        self,
        doctor_action: str,
        context: Optional[Dict] = None,
    ) -> BehavioralState:
        """
        Update behavioral state based on doctor's action.

        Args:
            doctor_action: What the doctor did (ask_question, prescribe, etc.)
            context: Additional context (empathetic?, thorough?, etc.)

        Returns:
            Updated BehavioralState
        """
        context = context or {}
        self.current_state.turn_count += 1

        # Detect doctor's approach from context
        approach = self._detect_approach(doctor_action, context)

        # Update trust
        trust_delta = self.trust_modifiers.get(approach, 0)
        self.current_state.trust = max(0.0, min(1.0, self.current_state.trust + trust_delta))

        if trust_delta != 0:
            self.current_state.trust_events.append(
                f"Turn {self.current_state.turn_count}: {approach} ({trust_delta:+.2f})"
            )

        # Update mood
        current_mood = self.current_state.mood
        transition_key = (current_mood, approach)
        if transition_key in MOOD_TRANSITIONS:
            self.current_state.mood = MOOD_TRANSITIONS[transition_key]

        # Update compliance (influenced by trust)
        trust_factor = self.current_state.trust - self.policy.initial_trust
        self.current_state.compliance = max(0.1, min(1.0,
            self.policy.compliance_level + trust_factor * 0.5
        ))

        # Update openness (influenced by trust and mood)
        mood_bonus = {
            "reassured": 0.2,
            "neutral": 0.0,
            "anxious": -0.1,
            "reluctant": -0.2,
            "hurried": -0.1,
            "angry": -0.3,
        }.get(self.current_state.mood, 0)
        self.current_state.openness = max(0.05, min(1.0,
            self.policy.reveal_probability + trust_factor * 0.3 + mood_bonus
        ))

        # Decrease patience
        if self.current_state.turn_count > self.current_state.patience_remaining:
            self.current_state.mood = "hurried"

        return self.current_state

    def _detect_approach(self, action: str, context: Dict) -> str:
        """Detect the doctor's approach from action and context."""
        # Explicit approach indicators
        if context.get("empathetic"):
            return "empathy"
        if context.get("dismissive"):
            return "dismissal"
        if context.get("rushed"):
            return "rushing"

        # Infer from action type
        if action == "ask_question":
            if context.get("patient_centered"):
                return "listening"
            return "thoroughness"
        elif action == "prescribe":
            if context.get("explained"):
                return "explanation"
            return "shared_decision"
        elif action == "diagnose":
            if context.get("explained"):
                return "explanation"
            return "thoroughness"

        return "thoroughness"

    def _initial_mood(self, goal: str) -> str:
        """Map goal to initial mood."""
        mood_map = {
            "get_help": "neutral",
            "finish_quickly": "hurried",
            "avoid_bad_news": "reluctant",
            "seek_reassurance": "anxious",
        }
        return mood_map.get(goal, "neutral")
