#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clinical Tools Definitions
临床工具定义

Six default clinical tools for the UniClinicalDataEngine.
"""

from typing import List, Dict, Any


# ============================================================================
# CLINICAL TOOLS DEFINITIONS
# ============================================================================

CLINICAL_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "egfr_calculator",
        "display_name": "eGFR Calculator",
        "description": "Calculates estimated Glomerular Filtration Rate (eGFR) using CKD-EPI formula. Used to assess kidney function and determine appropriate drug dosing.",
        "category": "nephrology",
        "department": "nephrology",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "creatinine",
                "type": "number",
                "description": "Serum creatinine level in mg/dL",
                "required": True,
                "unit": "mg/dL",
                "range": [0.1, 20.0],
            },
            {
                "name": "age",
                "type": "integer",
                "description": "Patient age in years",
                "required": True,
                "unit": "years",
                "range": [18, 120],
            },
            {
                "name": "gender",
                "type": "string",
                "description": "Patient gender",
                "required": True,
                "enum": ["male", "female"],
            },
            {
                "name": "race",
                "type": "string",
                "description": "Patient race (optional, for adjusted calculation)",
                "required": False,
                "enum": ["black", "non-black", "other"],
            },
        ],
        "output": {
            "type": "object",
            "description": "eGFR value and CKD stage classification",
            "fields": [
                {"name": "egfr", "type": "number", "unit": "mL/min/1.73m²"},
                {"name": "ckd_stage", "type": "string", "enum": ["1", "2", "3a", "3b", "4", "5"]},
                {"name": "interpretation", "type": "string"},
            ],
        },
        "clinical_notes": "eGFR < 60 mL/min/1.73m² indicates CKD. Drug dosing adjustments required for eGFR < 30.",
        "references": ["CKD-EPI 2009", "KDIGO 2012 Guidelines"],
    },
    {
        "name": "drug_dosing_calculator",
        "display_name": "Drug Dosing Calculator",
        "description": "Calculates appropriate drug doses based on patient parameters (weight, renal function, hepatic function). Supports dose adjustments for special populations.",
        "category": "pharmacology",
        "department": "general",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "drug_name",
                "type": "string",
                "description": "Name of the medication",
                "required": True,
            },
            {
                "name": "standard_dose",
                "type": "number",
                "description": "Standard dose in mg",
                "required": True,
                "unit": "mg",
            },
            {
                "name": "weight",
                "type": "number",
                "description": "Patient weight in kg",
                "required": False,
                "unit": "kg",
                "range": [10, 200],
            },
            {
                "name": "egfr",
                "type": "number",
                "description": "eGFR value for renal dose adjustment",
                "required": False,
                "unit": "mL/min/1.73m²",
                "range": [0, 150],
            },
            {
                "name": "indication",
                "type": "string",
                "description": "Clinical indication for the drug",
                "required": False,
            },
        ],
        "output": {
            "type": "object",
            "description": "Calculated dose with adjustment rationale",
            "fields": [
                {"name": "adjusted_dose", "type": "number", "unit": "mg"},
                {"name": "dosing_frequency", "type": "string"},
                {"name": "adjustment_reason", "type": "string"},
                {"name": "warnings", "type": "array", "items": {"type": "string"}},
            ],
        },
        "clinical_notes": "Always verify calculated doses with clinical guidelines. Consider patient-specific factors.",
        "references": ["Drug Prescribing Information", "Clinical Pharmacology Textbooks"],
    },
    {
        "name": "drug_interaction_checker",
        "display_name": "Drug Interaction Checker",
        "description": "Checks for potential drug-drug interactions and provides severity assessment and management recommendations.",
        "category": "pharmacology",
        "department": "general",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "drug_list",
                "type": "array",
                "description": "List of medications to check for interactions",
                "required": True,
                "items": {"type": "string"},
            },
            {
                "name": "patient_age",
                "type": "integer",
                "description": "Patient age for age-specific interactions",
                "required": False,
                "unit": "years",
            },
            {
                "name": "comorbidities",
                "type": "array",
                "description": "Patient comorbidities for context",
                "required": False,
                "items": {"type": "string"},
            },
        ],
        "output": {
            "type": "object",
            "description": "Interaction analysis results",
            "fields": [
                {"name": "interactions", "type": "array"},
                {"name": "severity_counts", "type": "object"},
                {"name": "recommendations", "type": "array", "items": {"type": "string"}},
            ],
        },
        "clinical_notes": "Severity levels: Major (avoid combination), Moderate (monitor), Minor (no action needed).",
        "references": ["Lexicomp", "Micromedex", "DrugBank"],
    },
    {
        "name": "vital_signs_analyzer",
        "display_name": "Vital Signs Analyzer",
        "description": "Analyzes vital signs (BP, HR, RR, Temp, SpO2) and identifies abnormalities, trends, and critical values requiring immediate attention.",
        "category": "assessment",
        "department": "general",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "blood_pressure_systolic",
                "type": "integer",
                "description": "Systolic blood pressure",
                "required": False,
                "unit": "mmHg",
                "range": [60, 250],
            },
            {
                "name": "blood_pressure_diastolic",
                "type": "integer",
                "description": "Diastolic blood pressure",
                "required": False,
                "unit": "mmHg",
                "range": [30, 150],
            },
            {
                "name": "heart_rate",
                "type": "integer",
                "description": "Heart rate/pulse",
                "required": False,
                "unit": "bpm",
                "range": [30, 200],
            },
            {
                "name": "respiratory_rate",
                "type": "integer",
                "description": "Respiratory rate",
                "required": False,
                "unit": "breaths/min",
                "range": [5, 60],
            },
            {
                "name": "temperature",
                "type": "number",
                "description": "Body temperature",
                "required": False,
                "unit": "°C",
                "range": [30, 45],
            },
            {
                "name": "oxygen_saturation",
                "type": "number",
                "description": "Oxygen saturation (SpO2)",
                "required": False,
                "unit": "%",
                "range": [70, 100],
            },
            {
                "name": "age",
                "type": "integer",
                "description": "Patient age for age-specific ranges",
                "required": False,
                "unit": "years",
            },
        ],
        "output": {
            "type": "object",
            "description": "Analysis of vital signs with alerts",
            "fields": [
                {"name": "abnormal_findings", "type": "array"},
                {"name": "critical_alerts", "type": "array", "items": {"type": "string"}},
                {"name": "warnings", "type": "array", "items": {"type": "string"}},
                {"name": "clinical_context", "type": "string"},
            ],
        },
        "clinical_notes": "Critical values: SBP > 180 or < 90, HR > 120 or < 50, Temp > 40 or < 35, SpO2 < 90%",
        "references": ["ACLS Guidelines", "ATLS Guidelines"],
    },
    {
        "name": "lab_values_interpreter",
        "display_name": "Lab Values Interpreter",
        "description": "Interprets common laboratory values and identifies abnormalities, trends, and clinical significance. Includes CBC, CMP, coagulation studies, and cardiac markers.",
        "category": "laboratory",
        "department": "general",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "test_name",
                "type": "string",
                "description": "Name of the laboratory test",
                "required": True,
            },
            {
                "name": "value",
                "type": "number",
                "description": "Laboratory value",
                "required": True,
            },
            {
                "name": "unit",
                "type": "string",
                "description": "Unit of measurement",
                "required": False,
            },
            {
                "name": "reference_range",
                "type": "string",
                "description": "Normal reference range",
                "required": False,
            },
            {
                "name": "patient_context",
                "type": "object",
                "description": "Additional patient context (age, gender, diagnosis)",
                "required": False,
            },
        ],
        "output": {
            "type": "object",
            "description": "Interpretation of lab value",
            "fields": [
                {"name": "interpretation", "type": "string"},
                {"name": "abnormality_level", "type": "string", "enum": ["normal", "low", "high", "critical"]},
                {"name": "clinical_significance", "type": "string"},
                {"name": "differential_diagnosis", "type": "array", "items": {"type": "string"}},
                {"name": "recommendations", "type": "array", "items": {"type": "string"}},
            ],
        },
        "clinical_notes": "Always interpret lab values in clinical context. Consider patient demographics and comorbidities.",
        "references": ["Henry's Clinical Diagnosis", "Laboratory Test Handbook"],
    },
    {
        "name": "clinical_calculator",
        "display_name": "Clinical Calculator Suite",
        "description": "Multi-purpose clinical calculator including BMI, risk scores, decision rules, and diagnostic criteria. Supports FRAX, CHA2DS2-VASc, HAS-BLED, Wells criteria, etc.",
        "category": "calculation",
        "department": "general",
        "version": "1.0.0",
        "parameters": [
            {
                "name": "calculator_type",
                "type": "string",
                "description": "Type of calculator to use",
                "required": True,
                "enum": [
                    "bmi",
                    "cha2ds2_vasc",
                    "has_bled",
                    "wells_dvt",
                    "wells_pe",
                    "frax",
                    "qtc",
                    "anion_gap",
                    "osmolar_gap",
                ],
            },
            {
                "name": "parameters",
                "type": "object",
                "description": "Calculator-specific parameters",
                "required": True,
            },
        ],
        "output": {
            "type": "object",
            "description": "Calculated score with interpretation",
            "fields": [
                {"name": "score", "type": "number"},
                {"name": "category", "type": "string"},
                {"name": "interpretation", "type": "string"},
                {"name": "recommendations", "type": "array", "items": {"type": "string"}},
                {"name": "references", "type": "array", "items": {"type": "string"}},
            ],
        },
        "clinical_notes": "Use clinical scores as aids to decision-making, not replacements for clinical judgment.",
        "references": [
            "ACC/AHA Guidelines",
            "ASH Guidelines",
            "ESC Guidelines",
            "Chest Guidelines",
        ],
    },
]


# ============================================================================
# TOOL REGISTRY HELPER FUNCTIONS
# ============================================================================

def get_tool_by_name(name: str) -> Dict[str, Any]:
    """Get tool definition by name."""
    for tool in CLINICAL_TOOLS:
        if tool["name"] == name:
            return tool.copy()
    return None


def get_tools_by_department(department: str) -> List[Dict[str, Any]]:
    """Get all tools for a specific department."""
    return [
        tool.copy()
        for tool in CLINICAL_TOOLS
        if tool.get("department") == department.lower()
    ]


def get_tools_by_category(category: str) -> List[Dict[str, Any]]:
    """Get all tools in a specific category."""
    return [
        tool.copy()
        for tool in CLINICAL_TOOLS
        if tool.get("category") == category.lower()
    ]


def get_all_tool_names() -> List[str]:
    """Get list of all tool names."""
    return [tool["name"] for tool in CLINICAL_TOOLS]


def validate_tool_parameters(tool_name: str, parameters: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate tool parameters against definition.

    Returns:
        Tuple of (is_valid, error_messages)
    """
    tool = get_tool_by_name(tool_name)
    if not tool:
        return False, [f"Tool not found: {tool_name}"]

    errors = []
    tool_params = tool.get("parameters", [])

    # Check required parameters
    for param in tool_params:
        if param.get("required", False):
            if param["name"] not in parameters:
                errors.append(f"Missing required parameter: {param['name']}")

    # Check parameter types (basic validation)
    for param_name, param_value in parameters.items():
        param_def = next((p for p in tool_params if p["name"] == param_name), None)
        if param_def:
            param_type = param_def.get("type", "string")
            if param_type == "number" and not isinstance(param_value, (int, float)):
                errors.append(f"Parameter {param_name} should be a number")
            elif param_type == "integer" and not isinstance(param_value, int):
                errors.append(f"Parameter {param_name} should be an integer")
            elif param_type == "array" and not isinstance(param_value, list):
                errors.append(f"Parameter {param_name} should be an array")

    return len(errors) == 0, errors


# Export tools and helper functions
__all__ = [
    "CLINICAL_TOOLS",
    "get_tool_by_name",
    "get_tools_by_department",
    "get_tools_by_category",
    "get_all_tool_names",
    "validate_tool_parameters",
    "load_fhir_tools",
    "merge_tools_with_fhir",
]


# ============================================================================
# FHIR TOOLS HELPER FUNCTIONS
# ============================================================================

def load_fhir_tools(funcs_path: str) -> List[Dict[str, Any]]:
    """
    Load FHIR tools from MedAgentBench funcs_v1.json.

    Args:
        funcs_path: Path to funcs_v1.json

    Returns:
        List of FHIR tool definitions compatible with CLINICAL_TOOLS format

    Example:
        >>> fhir_tools = load_fhir_tools("MedAgentBench/data/medagentbench/funcs_v1.json")
        >>> print(f"Loaded {len(fhir_tools)} FHIR tools")
    """
    from .adapters.medagentbench_adapter import MedAgentBenchAdapter

    adapter = MedAgentBenchAdapter()
    return adapter.load(funcs_path)


def merge_tools_with_fhir(
    clinical_tools: List[Dict[str, Any]],
    fhir_tools: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge clinical tools with FHIR tools.

    Args:
        clinical_tools: Standard clinical tools (CLINICAL_TOOLS)
        fhir_tools: FHIR API tools from load_fhir_tools()

    Returns:
        Combined tool list with FHIR tools marked

    Example:
        >>> from .tools import CLINICAL_TOOLS, load_fhir_tools, merge_tools_with_fhir
        >>> fhir_tools = load_fhir_tools("funcs_v1.json")
        >>> all_tools = merge_tools_with_fhir(CLINICAL_TOOLS, fhir_tools)
        >>> print(f"Total tools: {len(all_tools)}")
    """
    all_tools = clinical_tools.copy()

    # Add FHIR tools with special marker
    for tool in fhir_tools:
        tool["is_fhir_tool"] = True
        all_tools.append(tool)

    return all_tools
