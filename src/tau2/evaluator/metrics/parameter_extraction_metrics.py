# Copyright Sierra

"""
Parameter Extraction Metrics

Evaluates whether the agent correctly extracted and used parameters
required for tool calls.

Metrics include:
- Extraction accuracy: Percentage of required parameters correctly extracted
- Correct parameters: Parameters extracted correctly
- Missing parameters: Required parameters not extracted
- Incorrect parameters: Parameters extracted with wrong values
"""

import json
import logging
from typing import Any, Dict, List, Optional

from tau2.data_model.message import Message

logger = logging.getLogger(__name__)


class ParameterExtractionMetrics:
    """
    Evaluates parameter extraction accuracy for medical domain tasks.

    This metric assesses:
    1. Whether all required parameters were extracted
    2. Whether extracted values match expected values
    3. Whether parameters were used in the correct tools
    """

    @staticmethod
    def extract_all_parameters(trajectory: List[Message]) -> Dict[str, Dict]:
        """
        Extract all parameters used in tool calls from the trajectory.

        Args:
            trajectory: List of messages from the conversation

        Returns:
            Dictionary mapping parameter names to their values and sources
            Format: {
                "param_name": {
                    "value": extracted_value,
                    "tool": tool_name,
                    "call_count": number_of_times_used
                }
            }
        """
        extracted_params = {}

        for msg in trajectory:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for call in msg.tool_calls:
                    tool_name = call.name if hasattr(call, 'name') else getattr(call.function, 'name', 'unknown')

                    # Get arguments
                    arguments = {}
                    if hasattr(call, 'arguments') and call.arguments:
                        if isinstance(call.arguments, dict):
                            arguments = call.arguments
                        elif isinstance(call.arguments, str):
                            try:
                                arguments = json.loads(call.arguments)
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse arguments: {call.arguments}")
                                continue
                    elif hasattr(call.function, 'arguments'):
                        try:
                            arguments = json.loads(call.function.arguments)
                        except (json.JSONDecodeError, AttributeError):
                            continue

                    # Extract parameters
                    for param_name, param_value in arguments.items():
                        if param_name not in extracted_params:
                            extracted_params[param_name] = {
                                "value": param_value,
                                "tool": tool_name,
                                "call_count": 1
                            }
                        else:
                            extracted_params[param_name]["call_count"] += 1

        return extracted_params

    @staticmethod
    def evaluate(
        trajectory: List[Message],
        required_parameters: Dict[str, Any],
        tool_context: Optional[str] = None,
    ) -> Dict:
        """
        Evaluate parameter extraction accuracy.

        Args:
            trajectory: Conversation message history
            required_parameters: Dictionary of required parameters and their expected values
                               Format: {"param_name": expected_value}
            tool_context: Optional context about which tool these parameters are for

        Returns:
            Dictionary containing:
            - extraction_accuracy: float - overall accuracy (0-1)
            - extracted_params: Dict - all parameters that were extracted
            - correct_params: Dict - parameters with correct values
            - missing_params: List[str] - required parameters not found
            - incorrect_params: Dict - parameters with wrong values
            - extra_params: List[str] - parameters extracted but not required
            - total_params: int - total number of required parameters
            - correct_count: int - number of correct parameters
        """
        # Extract all parameters from trajectory
        extracted_params = ParameterExtractionMetrics.extract_all_parameters(trajectory)

        # Initialize result containers
        correct_params = {}
        incorrect_params = {}
        missing_params = []
        extra_params = []

        # Check each required parameter
        for param_name, expected_value in required_parameters.items():
            if param_name not in extracted_params:
                missing_params.append(param_name)
            else:
                extracted_value = extracted_params[param_name]["value"]

                # Compare values (handle type conversions)
                try:
                    if str(extracted_value) == str(expected_value):
                        correct_params[param_name] = {
                            "expected": expected_value,
                            "actual": extracted_value
                        }
                    else:
                        # Try numeric comparison
                        try:
                            if float(extracted_value) == float(expected_value):
                                correct_params[param_name] = {
                                    "expected": expected_value,
                                    "actual": extracted_value
                                }
                            else:
                                incorrect_params[param_name] = {
                                    "expected": expected_value,
                                    "actual": extracted_value
                                }
                        except (ValueError, TypeError):
                            incorrect_params[param_name] = {
                                "expected": expected_value,
                                "actual": extracted_value
                            }
                except Exception as e:
                    logger.warning(f"Error comparing parameter {param_name}: {e}")
                    incorrect_params[param_name] = {
                        "expected": expected_value,
                        "actual": extracted_value,
                        "error": str(e)
                    }

        # Find extra parameters (extracted but not required)
        extra_params = [
            param_name for param_name in extracted_params
            if param_name not in required_parameters
        ]

        # Calculate accuracy
        total_params = len(required_parameters)
        correct_count = len(correct_params)
        extraction_accuracy = correct_count / total_params if total_params > 0 else 0.0

        return {
            "extraction_accuracy": round(extraction_accuracy, 3),
            "extracted_params": extracted_params,
            "correct_params": correct_params,
            "missing_params": missing_params,
            "incorrect_params": incorrect_params,
            "extra_params": extra_params,
            "total_params": total_params,
            "correct_count": correct_count
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
            "Parameter Extraction Evaluation:",
            f"  Accuracy: {result['extraction_accuracy']:.1%} ({result['correct_count']}/{result['total_params']})",
        ]

        if result['correct_params']:
            lines.append(f"  Correct Parameters ({len(result['correct_params'])}):")
            for param, values in result['correct_params'].items():
                lines.append(f"    ✓ {param}: {values['actual']}")

        if result['incorrect_params']:
            lines.append(f"  Incorrect Parameters ({len(result['incorrect_params'])}):")
            for param, values in result['incorrect_params'].items():
                lines.append(f"    ✗ {param}: expected {values['expected']}, got {values['actual']}")

        if result['missing_params']:
            lines.append(f"  Missing Parameters: {', '.join(result['missing_params'])}")

        if result['extra_params']:
            lines.append(f"  Extra Parameters Extracted: {', '.join(result['extra_params'][:5])}")
            if len(result['extra_params']) > 5:
                lines.append(f"    ... and {len(result['extra_params']) - 5} more")

        return "\n".join(lines)


if __name__ == "__main__":
    # Test with sample data
    from tau2.data_model.message import AssistantMessage, ToolCall

    # Create a mock trajectory
    trajectory = [
        AssistantMessage(
            role="assistant",
            content="Let me assess your blood pressure",
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

    # Required parameters
    required = {
        "systolic": 140,
        "diastolic": 90,
        "age": 54
    }

    # Evaluate
    result = ParameterExtractionMetrics.evaluate(
        trajectory=trajectory,
        required_parameters=required
    )

    print(ParameterExtractionMetrics.format_score(result))
