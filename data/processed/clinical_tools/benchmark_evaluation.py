#!/usr/bin/env python3
"""
Clinical Consultation Agent Benchmark - Evaluation Framework

This module evaluates Agent tool invocation performance for clinical consultation
tasks based on OpenAI Function Call schema and clinical workflow best practices.

Author: Clinical Benchmark Team
Date: 2026-03-03
Version: 1.0
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Tuple, Any


def load_tools(tools_path: str = None) -> List[Dict[str, Any]]:
    """
    Load and parse tools.json file containing OpenAI Function Call schema.

    The tools.json file defines available clinical tools with their parameters,
    output schemas, call scenarios, and mock execution logic.

    Args:
        tools_path: Path to tools.json file. If None, uses default path.

    Returns:
        List of tool dictionaries containing schema and metadata.

    Raises:
        FileNotFoundError: If tools.json not found at specified path.
        json.JSONDecodeError: If tools.json contains invalid JSON.
    """
    if tools_path is None:
        # Default path relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        tools_path = os.path.join(script_dir, "tools.json")

    with open(tools_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get('tools', [])


def validate_invocation_timing(agent_tool_calls: List[Dict], tool_list: List[Dict]) -> Tuple[int, List[str]]:
    """
    Validate if Agent calls tools in correct workflow order (50 points max).

    Scoring Rules:
    - 0 points if find_patient_basic_info is not called first (critical failure)
    - 0 points if generate_follow_up_plan is not called last (critical failure)
    - Up to 5 points per tool for correct sequential order (10 tools × 5 = 50 max)
    - Deductions for premature or delayed tool calls based on call_scenario

    Args:
        agent_tool_calls: List of tool invocations with 'tool_name', 'call_time'
        tool_list: List of tool schemas from tools.json

    Returns:
        Tuple of (score_0_to_50, list_of_feedback_strings)
    """
    score = 50  # Start with max points, deduct for errors
    feedback = []

    if not agent_tool_calls:
        return 0, ["No tool calls made"]

    # Create tool name -> schema mapping for easy lookup
    tool_schema = {tool['function']['name']: tool['function'] for tool in tool_list}

    # Extract call order
    call_order = [call['tool_name'] for call in agent_tool_calls]

    # CRITICAL RULE 1: find_patient_basic_info MUST be first
    if call_order[0] != 'find_patient_basic_info':
        score = 0
        feedback.append("CRITICAL: find_patient_basic_info not called first (auto-fail)")
        return score, feedback
    else:
        feedback.append("✓ find_patient_basic_info called first (correct)")

    # CRITICAL RULE 2: generate_follow_up_plan MUST be last
    if call_order[-1] != 'generate_follow_up_plan':
        score = 0
        feedback.append("CRITICAL: generate_follow_up_plan not called last (auto-fail)")
        return score, feedback
    else:
        feedback.append("✓ generate_follow_up_plan called last (correct)")

    # Define expected workflow order based on call_scenario
    expected_order = [
        'find_patient_basic_info',
        'assess_risk_level',
        'get_medical_history_key',
        'ask_symptom_details',
        'retrieve_clinical_guideline',
        'retrieve_medication_details',
        'prescribe_medication_safe',
        'record_diagnosis_icd10',
        'transfer_to_specialist',
        'generate_follow_up_plan'
    ]

    # Create position mapping
    position_map = {tool: idx for idx, tool in enumerate(expected_order)}

    # Check for gross order violations (major workflow disruption)
    # Allow flexibility: tools can be skipped, but called tools should respect relative order
    for i in range(len(call_order) - 1):
        current_tool = call_order[i]
        next_tool = call_order[i + 1]

        if current_tool in position_map and next_tool in position_map:
            current_pos = position_map[current_tool]
            next_pos = position_map[next_tool]

            # Deduct points if called significantly out of order
            if next_pos < current_pos - 2:  # Allow minor flexibility
                score -= 5
                feedback.append(f"Order violation: {next_tool} called before {current_tool}")

    # Specific workflow dependency checks
    tool_names_set = set(call_order)

    # Check: get_medical_history_key before prescribe_medication_safe
    if 'prescribe_medication_safe' in tool_names_set:
        if 'get_medical_history_key' not in tool_names_set:
            score -= 10
            feedback.append("CRITICAL: prescribe_medication_safe called without allergy check")
        else:
            allergy_idx = call_order.index('get_medical_history_key')
            prescription_idx = call_order.index('prescribe_medication_safe')
            if allergy_idx > prescription_idx:
                score -= 10
                feedback.append("CRITICAL: get_medical_history_key called AFTER prescription")
            else:
                feedback.append("✓ get_medical_history_key before prescribe_medication_safe (correct)")

    # Check: retrieve_medication_details before prescribe_medication_safe
    if 'prescribe_medication_safe' in tool_names_set:
        if 'retrieve_medication_details' not in tool_names_set:
            score -= 5
            feedback.append("Warning: prescribe_medication_safe called without drug details check")
        else:
            details_idx = call_order.index('retrieve_medication_details')
            prescription_idx = call_order.index('prescribe_medication_safe')
            if details_idx > prescription_idx:
                score -= 5
                feedback.append("Warning: retrieve_medication_details called AFTER prescription")

    # Check: record_diagnosis_icd10 should be after assessment
    if 'record_diagnosis_icd10' in tool_names_set:
        if 'assess_risk_level' not in tool_names_set and 'ask_symptom_details' not in tool_names_set:
            score -= 5
            feedback.append("Warning: diagnosis recorded without proper assessment")

    # Ensure score doesn't go below 0
    score = max(0, score)

    return score, feedback


def validate_parameter_accuracy(agent_tool_call: Dict, tool_schema: Dict) -> Tuple[int, List[str]]:
    """
    Validate if Agent provides complete and valid parameters for a tool call.

    Scoring Rules (30 points total across all tools):
    - 3 points per tool call for having all required parameters
    - Deductions for missing required parameters (-1 point each)
    - Deductions for invalid parameter values (-0.5 points each)
    - Bonus for correct parameter formats (+0.5 points each)

    Args:
        agent_tool_call: Single tool invocation dict with 'tool_name', 'parameters'
        tool_schema: Tool schema from tools.json

    Returns:
        Tuple of (score_0_to_3, list_of_feedback_strings)
    """
    score = 3.0  # Max 3 points per tool
    feedback = []

    tool_name = agent_tool_call.get('tool_name', '')
    provided_params = agent_tool_call.get('parameters', {})

    if not tool_schema:
        return 0, [f"Unknown tool: {tool_name}"]

    # Get parameter schema
    param_schema = tool_schema.get('parameters', {})
    required_params = param_schema.get('required', [])
    properties = param_schema.get('properties', {})

    # Check all required parameters are present
    missing_params = []
    for req_param in required_params:
        if req_param not in provided_params:
            missing_params.append(req_param)
            score -= 1.0

    if missing_params:
        feedback.append(f"Missing required parameters: {', '.join(missing_params)}")
    else:
        feedback.append(f"✓ All required parameters present")

    # Validate parameter values
    for param_name, param_value in provided_params.items():
        if param_name in properties:
            param_def = properties[param_name]
            param_type = param_def.get('type')
            param_desc = param_def.get('description', '')
            param_enum = param_def.get('enum', [])

            # Type checking
            if param_type == 'string':
                if not isinstance(param_value, str):
                    score -= 0.5
                    feedback.append(f"Invalid type for {param_name}: expected string, got {type(param_value).__name__}")
                elif not param_value.strip():
                    score -= 0.5
                    feedback.append(f"Empty string for {param_name}")

            # Enum validation
            if param_enum and param_value in param_enum:
                score += 0.5
                feedback.append(f"✓ {param_name} has valid enum value: {param_value}")
            elif param_enum and param_value not in param_enum:
                score -= 0.5
                feedback.append(f"Invalid enum value for {param_name}: {param_value} (not in {param_enum})")

            # Format validation for specific parameters
            if param_name == 'patient_id':
                if isinstance(param_value, str) and len(param_value) > 3:
                    score += 0.5
                    feedback.append(f"✓ Valid patient_id format")
                else:
                    score -= 0.5
                    feedback.append(f"Invalid patient_id format: too short or wrong type")

            if param_name == 'icd10_code':
                if isinstance(param_value, str) and len(param_value) >= 3:
                    score += 0.5
                    feedback.append(f"✓ Valid ICD-10 code format")
                else:
                    score -= 0.5
                    feedback.append(f"Invalid ICD-10 code format")

    # Ensure score doesn't go below 0
    score = max(0.0, min(3.0, score))

    return round(score, 2), feedback


def validate_context_awareness(agent_tool_calls: List[Dict]) -> Tuple[int, List[str]]:
    """
    Validate if Agent demonstrates clinical context awareness (20 points max).

    Scoring Rules:
    - 5 points: Risk assessment before treatment
    - 5 points: Symptom exploration before diagnosis
    - 5 points: Safety checks before prescribing
    - 5 points: Appropriate specialist referral when needed

    Args:
        agent_tool_calls: List of tool invocations

    Returns:
        Tuple of (score_0_to_20, list_of_feedback_strings)
    """
    score = 0.0
    feedback = []

    call_order = [call['tool_name'] for call in agent_tool_calls]
    tool_set = set(call_order)

    # CRITICAL 1: Risk assessment before treatment (5 points)
    if 'assess_risk_level' in tool_set:
        risk_idx = call_order.index('assess_risk_level')
        treatment_tools = ['prescribe_medication_safe', 'record_diagnosis_icd10', 'transfer_to_specialist']

        risk_before_treatment = True
        for treatment_tool in treatment_tools:
            if treatment_tool in tool_set:
                treatment_idx = call_order.index(treatment_tool)
                if risk_idx > treatment_idx:
                    risk_before_treatment = False
                    break

        if risk_before_treatment and any(t in tool_set for t in treatment_tools):
            score += 5
            feedback.append("✓ Risk assessment before treatment (correct)")
        else:
            feedback.append("Warning: Risk assessment not before treatment")
    else:
        feedback.append("Warning: No risk assessment performed")

    # CRITICAL 2: Symptom exploration before diagnosis (5 points)
    if 'ask_symptom_details' in tool_set:
        symptom_idx = call_order.index('ask_symptom_details')
        diagnosis_tools = ['record_diagnosis_icd10', 'prescribe_medication_safe']

        symptoms_before_diagnosis = True
        for diag_tool in diagnosis_tools:
            if diag_tool in tool_set:
                diag_idx = call_order.index(diag_tool)
                if symptom_idx > diag_idx:
                    symptoms_before_diagnosis = False
                    break

        if symptoms_before_diagnosis and any(d in tool_set for d in diagnosis_tools):
            score += 5
            feedback.append("✓ Symptom exploration before diagnosis (correct)")
        else:
            feedback.append("Warning: Diagnosis recorded before symptom exploration")
    else:
        feedback.append("Warning: No symptom exploration performed")

    # CRITICAL 3: Safety checks before prescribing (5 points)
    if 'prescribe_medication_safe' in tool_set:
        required_checks = ['get_medical_history_key', 'retrieve_medication_details']
        all_checks_present = all(check in tool_set for check in required_checks)

        prescription_idx = call_order.index('prescribe_medication_safe')
        checks_before_prescription = True

        for check in required_checks:
            if check in tool_set:
                check_idx = call_order.index(check)
                if check_idx > prescription_idx:
                    checks_before_prescription = False
                    break

        if all_checks_present and checks_before_prescription:
            score += 5
            feedback.append("✓ All safety checks before prescribing (correct)")
        elif not all_checks_present:
            feedback.append("CRITICAL: Missing safety checks before prescribing")
        else:
            feedback.append("Warning: Safety checks not all before prescribing")
    else:
        # No deduction if no prescription made
        feedback.append("Note: No prescribing attempted")

    # CRITICAL 4: Appropriate use of clinical guidelines (5 points)
    if 'retrieve_clinical_guideline' in tool_set:
        # Check if guideline retrieved before diagnosis/treatment decision
        guideline_idx = call_order.index('retrieve_clinical_guideline')
        decision_tools = ['record_diagnosis_icd10', 'prescribe_medication_safe']

        guideline_before_decision = False
        for decision_tool in decision_tools:
            if decision_tool in tool_set:
                decision_idx = call_order.index(decision_tool)
                if guideline_idx < decision_idx:
                    guideline_before_decision = True
                    break

        if guideline_before_decision:
            score += 5
            feedback.append("✓ Clinical guideline consulted before decision (correct)")
        else:
            feedback.append("Note: Guideline retrieved but may not inform decision")
    else:
        # Minor deduction for not consulting guidelines in complex case
        if len(agent_tool_calls) > 5:
            score -= 2
            feedback.append("Note: Complex case without guideline consultation")

    # Bonus: Specialist referral for complex cases
    if 'transfer_to_specialist' in tool_set:
        score += 2
        feedback.append("✓ Specialist referral initiated (appropriate)")

    # Ensure score is within bounds
    score = max(0.0, min(20.0, score))

    return round(score, 2), feedback


def evaluate_agent(agent_tool_calls: List[Dict], tools_path: str = None) -> Dict[str, Any]:
    """
    Main evaluation function - calculates total score and generates structured report.

    Scoring Breakdown:
    - Invocation Timing: 50 points (workflow order + critical rules)
    - Parameter Accuracy: 30 points (3 points per tool × 10 tools max)
    - Context Awareness: 20 points (clinical reasoning + safety)

    Total: 100 points
    Pass Threshold: 70 points (70%)
    Excellence Threshold: 90 points (90%)

    Args:
        agent_tool_calls: List of tool invocations with structure:
            [{
                "tool_name": str,
                "parameters": dict,
                "call_time": str (ISO format, optional)
            }]
        tools_path: Path to tools.json file

    Returns:
        Evaluation report dict with:
        {
            "total_score": int (0-100),
            "timing_score": int (0-50),
            "parameter_score": float (0-30),
            "context_score": float (0-20),
            "feedback": list of feedback strings,
            "pass_status": bool,
            "evaluation_timestamp": str,
            "tool_calls_evaluated": int
        }
    """
    # Load tools
    tool_list = load_tools(tools_path)
    tool_schemas = {tool['function']['name']: tool['function'] for tool in tool_list}

    # Evaluate invocation timing
    timing_score, timing_feedback = validate_invocation_timing(agent_tool_calls, tool_list)

    # Evaluate parameter accuracy for each tool call
    parameter_score = 0.0
    parameter_feedback = []
    evaluated_tools = 0

    for tool_call in agent_tool_calls:
        tool_name = tool_call.get('tool_name')
        if tool_name in tool_schemas:
            tool_score, tool_feedback = validate_parameter_accuracy(tool_call, tool_schemas[tool_name])
            parameter_score += tool_score
            parameter_feedback.extend([f"[{tool_name}] {fb}" for fb in tool_feedback])
            evaluated_tools += 1

    # Cap parameter score at 30
    parameter_score = min(30.0, parameter_score)

    # Evaluate context awareness
    context_score, context_feedback = validate_context_awareness(agent_tool_calls)

    # Combine feedback
    all_feedback = timing_feedback + parameter_feedback + context_feedback

    # Determine overall pass status
    total_score = round(timing_score + parameter_score + context_score)
    pass_status = total_score >= 70

    # Add status message
    if total_score >= 90:
        all_feedback.insert(0, "EXCELLENT: Outstanding performance across all dimensions")
    elif total_score >= 70:
        all_feedback.insert(0, "PASS: Meets minimum competency requirements")
    else:
        all_feedback.insert(0, "FAIL: Below minimum competency threshold")

    # Generate report
    report = {
        "total_score": total_score,
        "timing_score": timing_score,
        "parameter_score": round(parameter_score, 2),
        "context_score": context_score,
        "feedback": all_feedback,
        "pass_status": pass_status,
        "evaluation_timestamp": datetime.now().isoformat(),
        "tool_calls_evaluated": evaluated_tools
    }

    return report


def print_evaluation_report(report: Dict[str, Any]) -> None:
    """
    Pretty print evaluation report to console.

    Args:
        report: Evaluation report dict from evaluate_agent()
    """
    print("\n" + "=" * 70)
    print("CLINICAL CONSULTATION AGENT EVALUATION REPORT")
    print("=" * 70)
    print(f"Evaluation Time: {report['evaluation_timestamp']}")
    print(f"Tool Calls Evaluated: {report['tool_calls_evaluated']}")
    print("\n" + "-" * 70)

    # Score breakdown
    print(f"\nTOTAL SCORE: {report['total_score']}/100")
    print(f"Status: {'✓ PASS' if report['pass_status'] else '✗ FAIL'}")
    print("\nBreakdown:")
    print(f"  Invocation Timing:     {report['timing_score']}/50")
    print(f"  Parameter Accuracy:    {report['parameter_score']}/30")
    print(f"  Context Awareness:     {report['context_score']}/20")

    print("\n" + "-" * 70)
    print("\nFeedback:")
    for feedback in report['feedback']:
        print(f"  {feedback}")

    print("\n" + "=" * 70)


def test_evaluation():
    """
    Test function with sample Agent tool calls (both pass and fail scenarios).

    Demonstrates:
    - Passing case: Correct workflow with all safety checks
    - Failing case: Missing critical steps and wrong order
    """
    print("\n" + "=" * 70)
    print("RUNNING TEST CASES")
    print("=" * 70)

    # TEST CASE 1: PASSING AGENT (Excellent performance)
    print("\n[TEST 1] PASSING AGENT - Excellent Clinical Workflow")
    print("-" * 70)

    passing_agent_calls = [
        {
            "tool_name": "find_patient_basic_info",
            "parameters": {"patient_id": "P20260303001"},
            "call_time": "2026-03-03T08:00:00"
        },
        {
            "tool_name": "assess_risk_level",
            "parameters": {
                "patient_id": "P20260303001",
                "symptoms": "headache, dizziness",
                "vital_signs": "BP 160/100, HR 88"
            },
            "call_time": "2026-03-03T08:05:00"
        },
        {
            "tool_name": "get_medical_history_key",
            "parameters": {
                "patient_id": "P20260303001",
                "history_type": "allergies"
            },
            "call_time": "2026-03-03T08:07:00"
        },
        {
            "tool_name": "ask_symptom_details",
            "parameters": {
                "patient_id": "P20260303001",
                "symptom_category": "cardiovascular",
                "question_focus": "severity"
            },
            "call_time": "2026-03-03T08:10:00"
        },
        {
            "tool_name": "retrieve_clinical_guideline",
            "parameters": {
                "condition": "hypertension",
                "specialty": "cardiology",
                "guideline_aspect": "treatment"
            },
            "call_time": "2026-03-03T08:12:00"
        },
        {
            "tool_name": "retrieve_medication_details",
            "parameters": {
                "medication_name": "Amlodipine",
                "info_type": "dosage"
            },
            "call_time": "2026-03-03T08:14:00"
        },
        {
            "tool_name": "prescribe_medication_safe",
            "parameters": {
                "patient_id": "P20260303001",
                "medication_name": "Amlodipine",
                "dosage": "5mg qd",
                "duration": "30 days",
                "route": "oral"
            },
            "call_time": "2026-03-03T08:16:00"
        },
        {
            "tool_name": "record_diagnosis_icd10",
            "parameters": {
                "patient_id": "P20260303001",
                "diagnosis_name": "Essential hypertension",
                "icd10_code": "I10",
                "diagnosis_type": "primary"
            },
            "call_time": "2026-03-03T08:18:00"
        },
        {
            "tool_name": "generate_follow_up_plan",
            "parameters": {
                "patient_id": "P20260303001",
                "diagnosis": "hypertension",
                "follow_up_type": "in_person",
                "timeframe_days": 14
            },
            "call_time": "2026-03-03T08:20:00"
        }
    ]

    report_pass = evaluate_agent(passing_agent_calls)
    print_evaluation_report(report_pass)

    # TEST CASE 2: FAILING AGENT (Critical workflow violations)
    print("\n\n[TEST 2] FAILING AGENT - Critical Workflow Violations")
    print("-" * 70)

    failing_agent_calls = [
        {
            "tool_name": "get_medical_history_key",  # WRONG: Not first!
            "parameters": {
                "patient_id": "P20260303002",
                "history_type": "allergies"
            },
            "call_time": "2026-03-03T09:00:00"
        },
        {
            "tool_name": "prescribe_medication_safe",  # WRONG: No allergy check before this
            "parameters": {
                "patient_id": "P20260303002",
                "medication_name": "Lisinopril",
                "dosage": "10mg qd",
                "duration": "30 days",
                "route": "oral"
            },
            "call_time": "2026-03-03T09:05:00"
        },
        {
            "tool_name": "find_patient_basic_info",  # WRONG: Should be first!
            "parameters": {"patient_id": "P20260303002"},
            "call_time": "2026-03-03T09:10:00"
        },
        {
            "tool_name": "generate_follow_up_plan",  # WRONG: Not last!
            "parameters": {
                "patient_id": "P20260303002",
                "diagnosis": "hypertension",
                "follow_up_type": "phone",
                "timeframe_days": 7
            },
            "call_time": "2026-03-03T09:15:00"
        },
        {
            "tool_name": "record_diagnosis_icd10",  # WRONG: After follow-up
            "parameters": {
                "patient_id": "P20260303002",
                "diagnosis_name": "Hypertension",
                "icd10_code": "I10",
                "diagnosis_type": "primary"
            },
            "call_time": "2026-03-03T09:20:00"
        }
    ]

    report_fail = evaluate_agent(failing_agent_calls)
    print_evaluation_report(report_fail)

    # TEST CASE 3: PARTIAL PASS (Missing some steps but no critical failures)
    print("\n\n[TEST 3] PARTIAL PASS - Missing Risk Assessment")
    print("-" * 70)

    partial_agent_calls = [
        {
            "tool_name": "find_patient_basic_info",
            "parameters": {"patient_id": "P20260303003"},
            "call_time": "2026-03-03T10:00:00"
        },
        {
            "tool_name": "get_medical_history_key",
            "parameters": {
                "patient_id": "P20260303003",
                "history_type": "medications"
            },
            "call_time": "2026-03-03T10:05:00"
        },
        {
            "tool_name": "prescribe_medication_safe",
            "parameters": {
                "patient_id": "P20260303003",
                "medication_name": "Amlodipine",
                "dosage": "5mg qd",
                "duration": "30 days",
                "route": "oral"
            },
            "call_time": "2026-03-03T10:10:00"
        },
        {
            "tool_name": "generate_follow_up_plan",
            "parameters": {
                "patient_id": "P20260303003",
                "diagnosis": "hypertension",
                "follow_up_type": "in_person",
                "timeframe_days": 30
            },
            "call_time": "2026-03-03T10:15:00"
        }
    ]

    report_partial = evaluate_agent(partial_agent_calls)
    print_evaluation_report(report_partial)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Test 1 (Passing Agent):  Score {report_pass['total_score']}/100 - {'✓ PASS' if report_pass['pass_status'] else '✗ FAIL'}")
    print(f"Test 2 (Failing Agent):  Score {report_fail['total_score']}/100 - {'✓ PASS' if report_fail['pass_status'] else '✗ FAIL'}")
    print(f"Test 3 (Partial Pass):   Score {report_partial['total_score']}/100 - {'✓ PASS' if report_partial['pass_status'] else '✗ FAIL'}")
    print("=" * 70)


def main():
    """
    Main entry point - demonstrates usage with examples.

    Usage Examples:
    1. Run test cases: python benchmark_evaluation.py
    2. Use as module: from benchmark_evaluation import evaluate_agent
    """
    import sys

    if len(sys.argv) > 1:
        # If command line argument provided, use it as tools.json path
        tools_path = sys.argv[1]
    else:
        # Use default path
        tools_path = None

    print("Clinical Consultation Agent Benchmark - Evaluation Framework")
    print(f"Loading tools from: {tools_path or 'default path'}")

    try:
        tools = load_tools(tools_path)
        print(f"✓ Loaded {len(tools)} tools")
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("\nPlease ensure tools.json is in the same directory as this script.")
        return
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing tools.json: {e}")
        return

    # Run test cases
    test_evaluation()


if __name__ == "__main__":
    main()
