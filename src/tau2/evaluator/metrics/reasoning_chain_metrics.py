# Copyright Sierra

"""
Reasoning Chain Metrics

Evaluates the quality and completeness of the agent's diagnostic reasoning.
Metrics include:
- Reasoning completeness: Were all expected reasoning steps covered?
- Reasoning order: Was the reasoning sequence logical?
- Reasoning clarity: Was the reasoning clearly expressed?
"""

import logging
from typing import Dict, List, Optional

from tau2.data_model.message import Message

logger = logging.getLogger(__name__)


class ReasoningChainMetrics:
    """
    Evaluates diagnostic reasoning chain quality.

    This metric assesses:
    1. Whether all expected reasoning steps were covered
    2. Whether the reasoning followed a logical sequence
    3. Whether the reasoning was clearly communicated
    """

    # Keywords that indicate good reasoning
    REASONING_KEYWORDS = [
        "because", "since", "due to", "caused by", "indicates", "suggests",
        "consistent with", "points to", "likely", "possibly", "considering",
        "based on", "given", "taking into account", "therefore", "thus",
        "hence", "consequently", "as a result"
    ]

    # Keywords that indicate step-by-step reasoning
    STEP_KEYWORDS = [
        "first", "second", "third", "next", "then", "finally",
        "step", "check", "assess", "evaluate", "consider"
    ]

    @staticmethod
    def extract_assistant_messages(trajectory: List[Message]) -> List[str]:
        """
        Extract all assistant message contents from trajectory.

        Args:
            trajectory: List of messages from the conversation

        Returns:
            List of assistant message contents
        """
        return [
            msg.content
            for msg in trajectory
            if msg.role == "assistant" and msg.content
        ]

    @staticmethod
    def check_reasoning_keywords(text: str) -> Dict[str, int]:
        """
        Check for reasoning keywords in text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with keyword counts
        """
        text_lower = text.lower()
        keyword_counts = {}

        for keyword in ReasoningChainMetrics.REASONING_KEYWORDS:
            count = text_lower.count(keyword)
            if count > 0:
                keyword_counts[keyword] = count

        return keyword_counts

    @staticmethod
    def check_step_keywords(text: str) -> int:
        """
        Check for step-indicating keywords in text.

        Args:
            text: Text to analyze

        Returns:
            Number of step keywords found
        """
        text_lower = text.lower()
        count = 0

        for keyword in ReasoningChainMetrics.STEP_KEYWORDS:
            count += text_lower.count(keyword)

        return count

    @staticmethod
    def evaluate(
        trajectory: List[Message],
        expected_steps: List[str],
        check_order: bool = True,
    ) -> Dict:
        """
        Evaluate reasoning chain quality.

        Args:
            trajectory: Conversation message history
            expected_steps: Expected reasoning steps (list of descriptions)
            check_order: Whether to check the order of reasoning steps

        Returns:
            Dictionary containing:
            - reasoning_completeness: float - proportion of steps covered (0-1)
            - reasoning_order: float - whether steps were in correct order (0-1)
            - reasoning_clarity: float - clarity of reasoning expression (0-1)
            - overall_score: float - combined score (0-1)
            - covered_steps: List[str] - steps that were covered
            - missing_steps: List[str] - steps that were missed
            - reasoning_keywords: Dict - reasoning keywords found
            - step_count: int - number of step indicators found
        """
        # Extract all assistant messages
        assistant_messages = ReasoningChainMetrics.extract_assistant_messages(trajectory)
        full_response = " ".join(assistant_messages).lower()

        # Check each expected step
        covered_steps = []
        missing_steps = []

        for step in expected_steps:
            # Extract keywords from step description
            step_keywords = step.lower().split()

            # Check if any keywords from this step are in the response
            # This is a simplified approach - a more sophisticated version would use embeddings
            if any(kw in full_response for kw in step_keywords if len(kw) > 3):
                covered_steps.append(step)
            else:
                missing_steps.append(step)

        # Calculate completeness
        reasoning_completeness = (
            len(covered_steps) / len(expected_steps)
            if expected_steps else 1.0
        )

        # Check reasoning order (simplified - checks if covered steps appear in order)
        reasoning_order = 1.0
        if check_order and covered_steps and len(covered_steps) > 1:
            # Check if steps are mentioned in approximately the right order
            positions = []
            for step in covered_steps:
                # Find first keyword position
                keywords = step.lower().split()
                for kw in keywords:
                    if len(kw) > 3 and kw in full_response:
                        positions.append(full_response.index(kw))
                        break

            # Check if positions are generally increasing
            if positions:
                out_of_order = sum(
                    1 for i in range(len(positions) - 1)
                    if positions[i] > positions[i + 1]
                )
                reasoning_order = 1.0 - (out_of_order / len(positions))

        # Check reasoning clarity
        reasoning_keywords = ReasoningChainMetrics.check_reasoning_keywords(full_response)
        step_count = ReasoningChainMetrics.check_step_keywords(full_response)

        # Clarity based on:
        # 1. Use of reasoning keywords (50%)
        # 2. Use of step indicators (30%)
        # 3. Response length (20% - assumes longer responses are more detailed)
        keyword_score = min(1.0, len(reasoning_keywords) / 5)  # 5+ keywords is excellent
        step_score = min(1.0, step_count / 3)  # 3+ step indicators is excellent
        length_score = min(1.0, len(full_response) / 500)  # 500 chars is good

        reasoning_clarity = keyword_score * 0.5 + step_score * 0.3 + length_score * 0.2

        # Overall score (weighted)
        overall_score = (
            reasoning_completeness * 0.5 +
            reasoning_order * 0.2 +
            reasoning_clarity * 0.3
        )

        return {
            "reasoning_completeness": round(reasoning_completeness, 3),
            "reasoning_order": round(reasoning_order, 3),
            "reasoning_clarity": round(reasoning_clarity, 3),
            "overall_score": round(overall_score, 3),
            "covered_steps": covered_steps,
            "missing_steps": missing_steps,
            "reasoning_keywords": reasoning_keywords,
            "step_count": step_count,
            "response_length": len(full_response)
        }

    @staticmethod
    def format_score(result: Dict) -> str:
        """
        Format the evaluation result as a human-readable string.

        Args:
            result: Result dictionary from evaluate()

        Returns:
            Formatted string
        """
        lines = [
            "Reasoning Chain Evaluation:",
            f"  Overall Score: {result['overall_score']:.3f}/1.0",
            f"  Completeness: {result['reasoning_completeness']:.1%}",
            f"  Order: {result['reasoning_order']:.1%}",
            f"  Clarity: {result['reasoning_clarity']:.1%}",
            "",
            f"  Covered Steps: {len(result['covered_steps'])}/{len(result['covered_steps']) + len(result['missing_steps'])}",
        ]

        if result['covered_steps']:
            lines.append("    ✓ Covered:")
            for step in result['covered_steps']:
                lines.append(f"      - {step}")

        if result['missing_steps']:
            lines.append("    ✗ Missing:")
            for step in result['missing_steps']:
                lines.append(f"      - {step}")

        if result['reasoning_keywords']:
            lines.append(f"  Reasoning Keywords Found: {len(result['reasoning_keywords'])}")
            keywords = list(result['reasoning_keywords'].keys())[:5]
            lines.append(f"    {', '.join(keywords)}")

        if result['step_count'] > 0:
            lines.append(f"  Step Indicators: {result['step_count']}")

        return "\n".join(lines)


if __name__ == "__main__":
    # Test with sample data
    from tau2.data_model.message import AssistantMessage, UserMessage

    # Create a mock trajectory
    trajectory = [
        UserMessage(role="user", content="I have a headache and my blood pressure is high."),
        AssistantMessage(
            role="assistant",
            content="Based on your symptoms of headache and high blood pressure, I need to assess your condition. "
                   "First, let me check your blood pressure readings. Then, I'll evaluate the severity. "
                   "This suggests possible hypertension that needs evaluation."
        )
    ]

    # Expected reasoning steps
    expected_steps = [
        "Assess blood pressure values",
        "Evaluate severity",
        "Consider headache causes",
        "Provide treatment recommendations"
    ]

    # Evaluate
    result = ReasoningChainMetrics.evaluate(
        trajectory=trajectory,
        expected_steps=expected_steps
    )

    print(ReasoningChainMetrics.format_score(result))
