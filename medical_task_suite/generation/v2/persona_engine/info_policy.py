#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Info Policy — Per-symptom reveal rules.

Controls when and how each piece of information is revealed based on
the patient's decision policy and the conversation context.
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from ..clinical_world.symptom_generator import SymptomSet


class SymptomVisibility(str, Enum):
    """How visible a symptom is to the doctor."""
    VOLUNTEERED = "volunteered"       # Patient mentions unprompted
    IF_ASKED = "if_asked"            # Reveals when asked directly
    RESISTANT = "resistant"          # Needs persistence and trust
    HIDDEN = "hidden"                # Never revealed without specific probe
    NOISE = "noise"                  # Unrelated symptom
    MISLEADING = "misleading"        # Points to wrong diagnosis


@dataclass
class SymptomRevealRule:
    """Rule governing when a symptom is revealed."""
    symptom: str
    visibility: SymptomVisibility
    reveal_on_ask: bool = True        # Reveals if specifically asked
    trust_threshold: float = 0.0      # Minimum trust needed
    turn_threshold: int = 0           # Minimum turns before revealing
    probe_keywords: List[str] = field(default_factory=list)

    def can_reveal(
        self,
        asked: bool,
        trust: float,
        turn: int,
        question_text: str = "",
    ) -> bool:
        """Check if this symptom can be revealed given the context."""
        if trust < self.trust_threshold:
            return False
        if turn < self.turn_threshold:
            return False
        if self.visibility == SymptomVisibility.VOLUNTEERED:
            return True
        if self.visibility == SymptomVisibility.NOISE:
            return True
        if self.visibility == SymptomVisibility.MISLEADING:
            return True
        if self.visibility == SymptomVisibility.HIDDEN:
            # Only reveal with specific probe keyword
            if self.probe_keywords:
                return any(kw in question_text.lower() for kw in self.probe_keywords)
            return asked and trust > 0.7
        if self.visibility == SymptomVisibility.RESISTANT:
            return asked and trust > self.trust_threshold
        if self.visibility == SymptomVisibility.IF_ASKED:
            return asked
        return False


class InfoPolicy:
    """
    Policy governing information revelation for each symptom.

    Usage:
        policy = InfoPolicy(symptom_set, decision_policy)
        if policy.should_reveal("fatigue", "asked", trust=0.6):
            # patient reveals the symptom
    """

    def __init__(self, symptoms: SymptomSet, decision_policy):
        """
        Args:
            symptoms: SymptomSet with all symptom tiers
            decision_policy: DecisionPolicy controlling revelation
        """
        self.symptoms = symptoms
        self.policy = decision_policy
        self.rules = self._build_rules(symptoms, decision_policy)

    def should_reveal(
        self,
        symptom: str,
        trigger: str,  # "volunteered", "asked", "pressed"
        trust: float = 0.5,
    ) -> bool:
        """
        Check if a symptom should be revealed.

        Args:
            symptom: The symptom to check
            trigger: What triggered the check (volunteered/asked/pressed)
            trust: Current trust level

        Returns:
            True if the symptom should be revealed
        """
        # Find the rule for this symptom
        rule = self.rules.get(symptom)
        if rule is None:
            # Unknown symptom — use base probability
            return random.random() < self.policy.reveal_probability

        # Check reveal conditions
        asked = trigger in ("asked", "pressed")
        question_text = ""  # Would need actual question text in production

        if trigger == "volunteered":
            return rule.visibility in (
                SymptomVisibility.VOLUNTEERED,
                SymptomVisibility.NOISE,
                SymptomVisibility.MISLEADING,
            )

        return rule.can_reveal(asked, trust, 0, question_text)

    def get_reveable_symptoms(self, trust: float, turn: int) -> List[str]:
        """Get list of symptoms that can be revealed at current trust/turn."""
        revealable = []
        for symptom, rule in self.rules.items():
            if rule.can_reveal(True, trust, turn):
                revealable.append(symptom)
        return revealable

    def _build_rules(
        self, symptoms: SymptomSet, policy
    ) -> Dict[str, SymptomRevealRule]:
        """Build reveal rules from symptom tiers and policy."""
        rules = {}

        # Volunteer symptoms
        for s in symptoms.volunteer:
            rules[s] = SymptomRevealRule(
                symptom=s,
                visibility=SymptomVisibility.VOLUNTEERED,
                reveal_on_ask=True,
                trust_threshold=0.0,
            )

        # If-asked symptoms
        for s in symptoms.if_asked:
            rules[s] = SymptomRevealRule(
                symptom=s,
                visibility=SymptomVisibility.IF_ASKED,
                reveal_on_ask=True,
                trust_threshold=0.2,
            )

        # Resistant symptoms
        for s in symptoms.resistant:
            rules[s] = SymptomRevealRule(
                symptom=s,
                visibility=SymptomVisibility.RESISTANT,
                reveal_on_ask=True,
                trust_threshold=0.5 if not policy.hide_if_not_asked else 0.7,
                turn_threshold=3,
            )

        # Hidden symptoms
        for s in symptoms.hidden:
            rules[s] = SymptomRevealRule(
                symptom=s,
                visibility=SymptomVisibility.HIDDEN,
                reveal_on_ask=False,
                trust_threshold=0.8,
                turn_threshold=5,
                probe_keywords=s.lower().split(),
            )

        # Noise symptoms
        for s in symptoms.noise:
            rules[s] = SymptomRevealRule(
                symptom=s,
                visibility=SymptomVisibility.NOISE,
                reveal_on_ask=True,
                trust_threshold=0.0,
            )

        # Misleading symptoms
        for s in symptoms.misleading:
            rules[s] = SymptomRevealRule(
                symptom=s,
                visibility=SymptomVisibility.MISLEADING,
                reveal_on_ask=True,
                trust_threshold=0.0,
            )

        return rules
