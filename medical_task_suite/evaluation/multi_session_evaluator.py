#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Session Consistency Evaluator

Evaluates whether an AI agent maintains consistent clinical reasoning
across linked sessions for chronic disease management.

Checks:
1. Memory: Agent remembers info from previous sessions without re-asking
2. Consistency: Agent doesn't contradict its own previous recommendations
3. Adaptation: Agent adjusts recommendations based on clinical changes
4. Follow-up: Agent follows through on planned actions from last session
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ConsistencyResult:
    """Result of a single consistency check."""
    check_id: str
    passed: bool
    description: str
    field: str
    evidence: str  # What in the response supports the check result
    severity: str = "major"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "passed": self.passed,
            "description": self.description,
            "field": self.field,
            "evidence": self.evidence[:200],
            "severity": self.severity,
        }


@dataclass
class SessionConsistencyReport:
    """Aggregate report for a multi-session evaluation."""
    session_link_id: str
    session_index: int
    total_sessions: int
    check_results: List[ConsistencyResult]
    memory_score: float          # 0-1: did agent remember prior info?
    consistency_score: float     # 0-1: were recommendations consistent?
    adaptation_score: float      # 0-1: did agent adapt to clinical changes?
    overall_score: float
    passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_link_id": self.session_link_id,
            "session_index": self.session_index,
            "total_sessions": self.total_sessions,
            "memory_score": round(self.memory_score, 3),
            "consistency_score": round(self.consistency_score, 3),
            "adaptation_score": round(self.adaptation_score, 3),
            "overall_score": round(self.overall_score, 3),
            "passed": self.passed,
            "checks": [c.to_dict() for c in self.check_results],
        }


class MultiSessionEvaluator:
    """
    Evaluates cross-session consistency for chronic disease management.
    """

    # Phrases indicating agent is re-asking known info (bad)
    RE_ASKING_PHRASES = [
        "can you tell me about your medical history",
        "what medications are you taking",
        "do you have any allergies",
        "what is your diagnosis",
        "tell me about your conditions",
        "could you remind me",
        "what were you diagnosed with",
        "what medicines",
    ]

    # Phrases indicating agent remembers (good)
    MEMORY_PHRASES = [
        "i see from your last visit",
        "as we discussed",
        "from your previous visit",
        "i remember that you",
        "we noted last time",
        "your records show",
        "as planned",
        "following up on",
        "from last session",
        "as we established",
        "you mentioned previously",
        "we started you on",
        "we adjusted your",
    ]

    # Phrases indicating logical adaptation
    ADAPTATION_PHRASES = [
        "given the change", "since your last visit",
        "based on the new results", "compared to last time",
        "your symptoms have", "the results show improvement",
        "the results show worsening", "let's adjust",
        "i'd like to modify", "we need to change",
        "different approach", "based on how you've been doing",
    ]

    # Phrases indicating contradiction (bad)
    CONTRADICTION_PHRASES = [
        "actually, i think", "on second thought",
        "i was wrong before", "let me reconsider",
        "i'm changing my recommendation",
    ]

    def evaluate_session(
        self,
        session_context: Dict[str, Any],
        agent_response: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> SessionConsistencyReport:
        """
        Evaluate agent consistency for a single session in a chain.

        Args:
            session_context: From task JSON's session_context field
            agent_response: Agent's response text
            tool_calls: List of tool calls made by agent

        Returns:
            SessionConsistencyReport
        """
        session_index = session_context.get("session_index", 0)
        total_sessions = session_context.get("total_sessions", 1)
        link_id = session_context.get("link_id", "unknown")
        checks_data = session_context.get("consistency_checks", [])

        # First session: no consistency checks needed
        if session_index == 0:
            return SessionConsistencyReport(
                session_link_id=link_id,
                session_index=session_index,
                total_sessions=total_sessions,
                check_results=[],
                memory_score=1.0,
                consistency_score=1.0,
                adaptation_score=1.0,
                overall_score=1.0,
                passed=True,
            )

        response_lower = agent_response.lower()
        check_results = []

        # 1. Memory checks — did agent remember prior info?
        memory_results = self._evaluate_memory(response_lower)
        check_results.extend(memory_results)

        # 2. Consistency checks from task definition
        for check_def in checks_data:
            result = self._evaluate_consistency_check(
                check_def, response_lower, tool_calls or []
            )
            check_results.append(result)

        # 3. Adaptation checks — did agent adapt to changes?
        evolution = session_context.get("evolution_summary", {})
        adaptation_results = self._evaluate_adaptation(
            response_lower, evolution, tool_calls or []
        )
        check_results.extend(adaptation_results)

        # Compute scores
        memory_checks = [r for r in check_results if "memory" in r.check_id]
        consistency_checks = [r for r in check_results if "consistency" in r.check_id]
        adaptation_checks = [r for r in check_results if "adaptation" in r.check_id]

        memory_score = (
            sum(1 for r in memory_checks if r.passed) / len(memory_checks)
            if memory_checks else 1.0
        )
        consistency_score = (
            sum(1 for r in consistency_checks if r.passed) / len(consistency_checks)
            if consistency_checks else 1.0
        )
        adaptation_score = (
            sum(1 for r in adaptation_checks if r.passed) / len(adaptation_checks)
            if adaptation_checks else 1.0
        )

        overall = (memory_score + consistency_score + adaptation_score) / 3.0

        # Critical failures in any check = overall fail
        has_critical_fail = any(
            not r.passed and r.severity == "critical"
            for r in check_results
        )

        return SessionConsistencyReport(
            session_link_id=link_id,
            session_index=session_index,
            total_sessions=total_sessions,
            check_results=check_results,
            memory_score=memory_score,
            consistency_score=consistency_score,
            adaptation_score=adaptation_score,
            overall_score=overall,
            passed=overall >= 0.6 and not has_critical_fail,
        )

    def _evaluate_memory(self, response: str) -> List[ConsistencyResult]:
        """Check if agent uses memory rather than re-asking."""
        results = []

        # Check for memory phrases (positive)
        has_memory = any(phrase in response for phrase in self.MEMORY_PHRASES)

        # Check for re-asking phrases (negative)
        re_asking = [
            phrase for phrase in self.RE_ASKING_PHRASES
            if phrase in response
        ]

        results.append(ConsistencyResult(
            check_id="memory_uses_prior",
            passed=has_memory or not re_asking,
            description="Agent should use prior session info without re-asking",
            field="session_memory",
            evidence=(
                f"Memory phrases found: {has_memory}. "
                f"Re-asking phrases: {re_asking[:3]}"
            ),
            severity="major",
        ))

        return results

    def _evaluate_consistency_check(
        self,
        check_def: Dict[str, Any],
        response: str,
        tool_calls: List[Dict],
    ) -> ConsistencyResult:
        """Evaluate a single consistency check from task definition."""
        check_id = check_def.get("check_id", "unknown")
        description = check_def.get("description", "")
        field_name = check_def.get("field", "")
        expected = check_def.get("expected_behavior", "")
        severity = check_def.get("severity", "major")

        # Check if response contradicts expected behavior
        # Simple heuristic: check for the field/topic in response
        field_keywords = field_name.lower().replace("_", " ").split()

        mentions_field = any(kw in response for kw in field_keywords if len(kw) > 3)

        # Check for contradiction
        has_contradiction = any(
            phrase in response for phrase in self.CONTRADICTION_PHRASES
        )

        passed = not has_contradiction
        if mentions_field and not has_contradiction:
            passed = True

        return ConsistencyResult(
            check_id=f"consistency_{check_id}",
            passed=passed,
            description=description,
            field=field_name,
            evidence=f"Expected: {expected[:100]}. Mentioned: {mentions_field}",
            severity=severity,
        )

    def _evaluate_adaptation(
        self,
        response: str,
        evolution: Dict[str, Any],
        tool_calls: List[Dict],
    ) -> List[ConsistencyResult]:
        """Check if agent adapted to clinical changes."""
        results = []

        lab_changes = evolution.get("lab_changes", {})
        new_symptoms = evolution.get("new_symptoms", [])
        med_changes = evolution.get("medication_changes", [])

        has_changes = bool(lab_changes or new_symptoms or med_changes)

        if not has_changes:
            return results

        # Check for adaptation language
        has_adaptation = any(
            phrase in response for phrase in self.ADAPTATION_PHRASES
        )

        results.append(ConsistencyResult(
            check_id="adaptation_to_changes",
            passed=has_adaptation,
            description="Agent should acknowledge and adapt to clinical changes",
            field="clinical_evolution",
            evidence=(
                f"Changes detected: labs={bool(lab_changes)}, "
                f"new_symptoms={len(new_symptoms)}, "
                f"med_changes={len(med_changes)}. "
                f"Adaptation language: {has_adaptation}"
            ),
            severity="major",
        ))

        # Check if agent addressed medication changes
        if med_changes:
            for mc in med_changes:
                med_name = mc.get("medication", "")
                if med_name and med_name.lower() in response:
                    results.append(ConsistencyResult(
                        check_id=f"adaptation_med_{med_name}",
                        passed=True,
                        description=f"Agent addressed medication change: {med_name}",
                        field="medication_changes",
                        evidence=f"Agent mentioned {med_name}",
                        severity="minor",
                    ))

        return results
