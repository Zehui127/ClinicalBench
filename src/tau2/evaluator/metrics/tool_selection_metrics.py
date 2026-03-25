# Copyright Sierra

"""
Tool Selection Metrics

Evaluates whether the agent selected the correct tools for the task.
Metrics include:
- Category correctness: Did agent use tools from expected category?
- Required tools usage: Did agent use all required tools?
- Tool selection score: Overall score combining above metrics
"""

import json
import logging
from typing import Dict, List, Optional

from tau2.data_model.message import Message
from tau2.data_model.medical_tasks import ToolCategory

logger = logging.getLogger(__name__)


class ToolSelectionMetrics:
    """
    Evaluates tool selection correctness for medical domain tasks.

    This metric assesses:
    1. Whether tools from the correct category were used
    2. Whether all required tools were used
    3. Whether inappropriate tools were avoided
    """

    @staticmethod
    def extract_tool_calls(trajectory: List[Message]) -> List[Dict]:
        """
        Extract all tool calls from the message trajectory.

        Args:
            trajectory: List of messages from the conversation

        Returns:
            List of tool call dictionaries with 'name' and 'arguments'
        """
        tool_calls = []

        for msg in trajectory:
            # Handle different message types
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for call in msg.tool_calls:
                    tool_name = call.name if hasattr(call, 'name') else getattr(call.function, 'name', 'unknown')
                    tool_calls.append({
                        'name': tool_name,
                        'call': call
                    })

        return tool_calls

    @staticmethod
    def evaluate(
        trajectory: List[Message],
        expected_category: Optional[str] = None,
        required_tools: Optional[List[str]] = None,
        forbidden_tools: Optional[List[str]] = None,
        category: Optional[ToolCategory] = None,
    ) -> Dict:
        """
        Evaluate tool selection correctness.

        Args:
            trajectory: Conversation message history
            expected_category: Expected tool category (as string or ToolCategory)
            required_tools: List of required tool names
            forbidden_tools: List of tools that should NOT be used
            category: ToolCategory enum (alternative to expected_category)

        Returns:
            Dictionary containing:
            - category_correct: bool - whether correct category was used
            - required_tools_used: bool - whether all required tools were used
            - forbidden_tools_avoided: bool - whether forbidden tools were avoided
            - tool_selection_score: float - overall score (0-1)
            - used_tools: List[str] - tools that were used
            - missing_tools: List[str] - required tools not used
            - used_forbidden_tools: List[str] - forbidden tools that were used
            - used_categories: List[str] - categories of tools used
        """
        # Normalize inputs
        if required_tools is None:
            required_tools = []
        if forbidden_tools is None:
            forbidden_tools = []

        # Handle ToolCategory enum
        if category is not None:
            expected_category = category.value if isinstance(category, ToolCategory) else category

        # Extract tool calls from trajectory
        tool_calls = ToolSelectionMetrics.extract_tool_calls(trajectory)
        used_tools = set()
        used_categories = set()

        # Import tool categories
        try:
            from tau2.domains.clinical.tool_categories import get_tool_category
            has_tool_categories = True
        except ImportError:
            has_tool_categories = False
            logger.warning("tool_categories module not available")

        # Analyze used tools
        for call_info in tool_calls:
            tool_name = call_info['name']
            used_tools.add(tool_name)

            if has_tool_categories:
                tool_cat = get_tool_category(tool_name)
                used_categories.add(tool_cat.value if isinstance(tool_cat, ToolCategory) else tool_cat)

        # Evaluate category correctness
        category_correct = False
        if expected_category is None:
            # No category specified, consider it correct
            category_correct = True
        else:
            category_correct = expected_category in used_categories

        # Evaluate required tools
        missing_tools = set(required_tools) - used_tools
        required_tools_used = len(missing_tools) == 0

        # Evaluate forbidden tools
        used_forbidden = set()
        if forbidden_tools:
            used_forbidden = used_tools & set(forbidden_tools)
        forbidden_tools_avoided = len(used_forbidden) == 0

        # Calculate scores
        # 1. Category score (40% weight)
        category_score = 1.0 if category_correct else 0.0

        # 2. Required tools score (40% weight)
        if required_tools:
            required_score = len(used_tools & set(required_tools)) / len(required_tools)
        else:
            required_score = 1.0

        # 3. Forbidden tools penalty (20% weight)
        forbidden_score = 0.0 if used_forbidden else 1.0

        # Overall score
        tool_selection_score = (
            category_score * 0.4 +
            required_score * 0.4 +
            forbidden_score * 0.2
        )

        return {
            "category_correct": category_correct,
            "required_tools_used": required_tools_used,
            "forbidden_tools_avoided": forbidden_tools_avoided,
            "tool_selection_score": round(tool_selection_score, 3),
            "used_tools": list(used_tools),
            "missing_tools": list(missing_tools),
            "used_forbidden_tools": list(used_forbidden),
            "used_categories": list(used_categories),
            "expected_category": expected_category,
            "total_tool_calls": len(tool_calls)
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
            "Tool Selection Evaluation:",
            f"  Overall Score: {result['tool_selection_score']:.3f}/1.0",
            f"  Category Correct: {'✓' if result['category_correct'] else '✗'}",
            f"  Required Tools Used: {'✓' if result['required_tools_used'] else '✗'}",
            f"  Forbidden Tools Avoided: {'✓' if result['forbidden_tools_avoided'] else '✗'}",
        ]

        if result['used_tools']:
            lines.append(f"  Used Tools ({len(result['used_tools'])}): {', '.join(result['used_tools'])}")

        if result['missing_tools']:
            lines.append(f"  Missing Required Tools: {', '.join(result['missing_tools'])}")

        if result['used_forbidden_tools']:
            lines.append(f"  Used Forbidden Tools: {', '.join(result['used_forbidden_tools'])}")

        if result['expected_category']:
            lines.append(f"  Expected Category: {result['expected_category']}")
            lines.append(f"  Used Categories: {', '.join(result['used_categories'])}")

        return "\n".join(lines)


if __name__ == "__main__":
    # Test with sample data
    from tau2.data_model.message import AssistantMessage, ToolCall

    # Create a mock trajectory
    trajectory = [
        AssistantMessage(
            role="assistant",
            content="Let me check your blood pressure",
            tool_calls=[
                ToolCall(
                    id="call_1",
                    name="assess_blood_pressure",
                    arguments='{"systolic": 140, "diastolic": 90, "age": 54}',
                    requestor="assistant"
                )
            ]
        )
    ]

    # Evaluate
    result = ToolSelectionMetrics.evaluate(
        trajectory=trajectory,
        expected_category="diagnosis",
        required_tools=["assess_blood_pressure"]
    )

    print(ToolSelectionMetrics.format_score(result))
