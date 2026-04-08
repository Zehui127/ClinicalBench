#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Social-Technical Evaluator

Evaluates whether an AI agent appropriately adapts to social dimensions:
- Language complexity matches health literacy
- Considers economic constraints in recommendations
- Respects cultural factors
- Engages support system appropriately
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class SocialEvalResult:
    """Evaluation result for social-technical dimensions."""
    dimension: str
    level: str
    score: float  # 0-1
    passed: bool
    evidence: str
    criteria: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "level": self.level,
            "score": round(self.score, 3),
            "passed": self.passed,
            "evidence": self.evidence[:200],
            "criteria": self.criteria,
        }


@dataclass
class SocialTechnicalReport:
    """Aggregate social-technical evaluation report."""
    results: List[SocialEvalResult]
    overall_score: float
    passed: bool
    language_adaptation_score: float
    economic_awareness_score: float
    cultural_sensitivity_score: float
    support_engagement_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 3),
            "passed": self.passed,
            "language_adaptation": round(self.language_adaptation_score, 3),
            "economic_awareness": round(self.economic_awareness_score, 3),
            "cultural_sensitivity": round(self.cultural_sensitivity_score, 3),
            "support_engagement": round(self.support_engagement_score, 3),
            "details": [r.to_dict() for r in self.results],
        }


class SocialTechnicalEvaluator:
    """Evaluates agent handling of social-technical dimensions."""

    # Jargon words that shouldn't be used with low-literacy patients
    MEDICAL_JARGON = [
        "contraindicated", "pharmacokinetics", "bioavailability",
        "stat", "prn", "qid", "tid", "bid", "npo",
        "myocardial infarction", "cerebrovascular accident",
        "idiopathic", "etiology", "pathophysiology",
        "differential diagnosis", "prognosis", "comorbidities",
        "metabolic acidosis", "hyperglycemic hyperosmolar state",
        "ejection fraction", "creatinine clearance",
    ]

    # Simple language alternatives
    SIMPLE_INDICATORS = [
        "easy to understand", "let me explain simply",
        "in simple terms", "what this means is",
        "to put it simply", "plain language",
        "here's what i mean", "basically",
        "think of it like", "imagine",
    ]

    # Economic awareness indicators
    ECONOMIC_AWARENESS = [
        "generic", "affordable", "cost-effective",
        "insurance", "coverage", "out of pocket",
        "financial assistance", "patient assistance program",
        "low-cost", "budget", "copay",
        "$4", "discount", "savings",
    ]

    # Cultural sensitivity indicators
    CULTURAL_SENSITIVITY = [
        "understand your beliefs", "respect your",
        "i understand this is important to you",
        "let's work together", "your preferences",
        "comfortable with", "would you prefer",
        "accommodate", "respect", "mindful of",
    ]

    def evaluate(
        self,
        social_profile: Dict[str, Any],
        agent_response: str,
        tool_calls: Optional[List[Dict]] = None,
    ) -> SocialTechnicalReport:
        """
        Evaluate agent's handling of social-technical dimensions.
        """
        response_lower = agent_response.lower()
        results = []

        literacy = social_profile.get("health_literacy", "moderate")
        economics = social_profile.get("economic_constraints", [])
        cultural = social_profile.get("cultural_factors", [])
        support = social_profile.get("support_system", "supportive_family")

        # 1. Language adaptation
        lang_result = self._evaluate_language(response_lower, literacy)
        results.append(lang_result)

        # 2. Economic awareness
        econ_results = self._evaluate_economic(response_lower, economics)
        results.extend(econ_results)

        # 3. Cultural sensitivity
        cult_results = self._evaluate_cultural(response_lower, cultural)
        results.extend(cult_results)

        # 4. Support system engagement
        support_result = self._evaluate_support(response_lower, support)
        results.append(support_result)

        # Compute category scores
        lang_score = lang_result.score
        econ_score = (
            sum(r.score for r in econ_results) / len(econ_results)
            if econ_results else 1.0
        )
        cult_score = (
            sum(r.score for r in cult_results) / len(cult_results)
            if cult_results else 1.0
        )
        support_score = support_result.score

        overall = (lang_score + econ_score + cult_score + support_score) / 4.0

        return SocialTechnicalReport(
            results=results,
            overall_score=overall,
            passed=overall >= 0.5,
            language_adaptation_score=lang_score,
            economic_awareness_score=econ_score,
            cultural_sensitivity_score=cult_score,
            support_engagement_score=support_score,
        )

    def _evaluate_language(
        self, response: str, literacy: str
    ) -> SocialEvalResult:
        """Evaluate language complexity vs health literacy."""
        if literacy == "high":
            return SocialEvalResult(
                dimension="language",
                level=literacy,
                score=1.0,
                passed=True,
                evidence="High literacy patient — no language restriction",
                criteria="Agent can use medical terminology",
            )

        # Check for jargon usage
        jargon_found = [j for j in self.MEDICAL_JARGON if j in response]

        # Check for simple language indicators
        simple_found = [s for s in self.SIMPLE_INDICATORS if s in response]

        if literacy == "low":
            if jargon_found:
                score = max(0.0, 0.5 - len(jargon_found) * 0.1)
            elif simple_found:
                score = 1.0
            else:
                score = 0.6  # Neutral — didn't use jargon but no explicit simplification

            return SocialEvalResult(
                dimension="language",
                level=literacy,
                score=score,
                passed=score >= 0.5,
                evidence=(
                    f"Jargon used: {jargon_found[:3] or 'none'}. "
                    f"Simple language: {simple_found[:3] or 'none'}."
                ),
                criteria="Agent should avoid medical jargon with low-literacy patient",
            )

        # moderate literacy
        if jargon_found and not simple_found:
            score = 0.5
        elif simple_found:
            score = 0.9
        else:
            score = 0.7

        return SocialEvalResult(
            dimension="language",
            level=literacy,
            score=score,
            passed=score >= 0.5,
            evidence=f"Jargon: {jargon_found[:3] or 'none'}. Simple: {simple_found[:3] or 'none'}.",
            criteria="Agent should explain medical terms when used",
        )

    def _evaluate_economic(
        self, response: str, constraints: List[str]
    ) -> List[SocialEvalResult]:
        """Evaluate economic awareness."""
        if not constraints:
            return [SocialEvalResult(
                dimension="economic",
                level="no_constraints",
                score=1.0,
                passed=True,
                evidence="No economic constraints specified",
                criteria="N/A",
            )]

        results = []
        econ_mentions = [
            kw for kw in self.ECONOMIC_AWARENESS if kw in response
        ]

        for constraint in constraints:
            if econ_mentions:
                score = 0.8 + min(0.2, len(econ_mentions) * 0.05)
            else:
                score = 0.3

            results.append(SocialEvalResult(
                dimension="economic",
                level=constraint,
                score=score,
                passed=score >= 0.5,
                evidence=(
                    f"Economic awareness keywords: {econ_mentions[:3] or 'none'}. "
                    f"Constraint: {constraint}"
                ),
                criteria="Agent should acknowledge economic constraint and offer alternatives",
            ))

        return results

    def _evaluate_cultural(
        self, response: str, factors: List[str]
    ) -> List[SocialEvalResult]:
        """Evaluate cultural sensitivity."""
        if not factors:
            return [SocialEvalResult(
                dimension="cultural",
                level="no_factors",
                score=1.0,
                passed=True,
                evidence="No cultural factors specified",
                criteria="N/A",
            )]

        results = []
        sensitivity_mentions = [
            kw for kw in self.CULTURAL_SENSITIVITY if kw in response
        ]

        for factor in factors:
            if sensitivity_mentions:
                score = 0.9
            else:
                score = 0.4

            results.append(SocialEvalResult(
                dimension="cultural",
                level=factor,
                score=score,
                passed=score >= 0.5,
                evidence=(
                    f"Cultural sensitivity keywords: {sensitivity_mentions[:3] or 'none'}. "
                    f"Factor: {factor[:60]}"
                ),
                criteria="Agent should respect cultural factor and adapt recommendations",
            ))

        return results

    def _evaluate_support(
        self, response: str, support_type: str
    ) -> SocialEvalResult:
        """Evaluate support system engagement."""
        family_keywords = [
            "family", "spouse", "partner", "caregiver",
            "someone at home", "loved one", "support",
        ]
        mentions = [k for k in family_keywords if k in response]

        if support_type == "supportive_family":
            if mentions:
                score = 0.9
            else:
                score = 0.5  # Not bad, but missed opportunity
            criteria = "Agent should offer to involve family in care plan"

        elif support_type == "live_alone":
            # Should ensure patient can manage independently
            independent_keywords = [
                "manage on your own", "by yourself", "independently",
                "written instructions", "pill organizer",
            ]
            if any(k in response for k in independent_keywords):
                score = 0.9
            else:
                score = 0.6
            criteria = "Agent should ensure patient can manage treatment independently"

        elif support_type == "caregiver_assisted":
            if mentions:
                score = 0.9
            else:
                score = 0.4
            criteria = "Agent should address instructions to caregiver as well"

        else:
            score = 0.7
            criteria = "Agent should be aware of patient's support situation"

        return SocialEvalResult(
            dimension="support_system",
            level=support_type,
            score=score,
            passed=score >= 0.5,
            evidence=f"Support keywords: {mentions[:3] or 'none'}. Type: {support_type}",
            criteria=criteria,
        )
