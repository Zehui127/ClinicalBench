# Copyright Sierra

"""
Medical Tool Classification System

Categorizes all medical tools into three functional categories:
- Suggestion: Health education, lifestyle recommendations
- Diagnosis: Symptom analysis, test result interpretation
- Treatment: Medication guidance, treatment planning

Each category has specific evaluation metrics defined.
"""

from typing import Dict, List

from tau2.data_model.medical_tasks import ToolCategory, ToolEvaluationMetrics

# ============================================================================
# TOOL CATEGORIES MAPPING
# ============================================================================

# Cardiology Tools
CARDIOLOGY_TOOL_CATEGORIES: Dict[str, ToolCategory] = {
    "assess_blood_pressure": ToolCategory.DIAGNOSIS,
    "calculate_qtc": ToolCategory.DIAGNOSIS,
    "interpret_heart_rate": ToolCategory.DIAGNOSIS,
    "get_patient_by_mrn": ToolCategory.SUGGESTION,
}

# Endocrinology Tools
ENDOCRINOLOGY_TOOL_CATEGORIES: Dict[str, ToolCategory] = {
    "assess_blood_glucose": ToolCategory.DIAGNOSIS,
    "calculate_bmi": ToolCategory.DIAGNOSIS,
    "get_medication_dosage": ToolCategory.TREATMENT,
    "check_diabetes_complications": ToolCategory.DIAGNOSIS,
}

# Gastroenterology Tools
GASTROENTEROLOGY_TOOL_CATEGORIES: Dict[str, ToolCategory] = {
    "assess_abdominal_pain": ToolCategory.DIAGNOSIS,
    "check_liver_function": ToolCategory.DIAGNOSIS,
    "recommend_dietary_changes": ToolCategory.SUGGESTION,
}

# Nephrology Tools
NEPHROLOGY_TOOL_CATEGORIES: Dict[str, ToolCategory] = {
    "assess_kidney_function": ToolCategory.DIAGNOSIS,
    "check_electrolytes": ToolCategory.DIAGNOSIS,
    "recommend_fluid_intake": ToolCategory.SUGGESTION,
}

# Neurology Tools
NEUROLOGY_TOOL_CATEGORIES: Dict[str, ToolCategory] = {
    "assess_headache": ToolCategory.DIAGNOSIS,
    "check_neurological_deficits": ToolCategory.DIAGNOSIS,
    "recommend_migraine_management": ToolCategory.TREATMENT,
}

# Chinese Internal Medicine Tools
CHINESE_MEDICINE_TOOL_CATEGORIES: Dict[str, ToolCategory] = {
    "assess_tcm_syndrome": ToolCategory.DIAGNOSIS,
    "recommend_herbal_formula": ToolCategory.TREATMENT,
    "recommend_acupuncture": ToolCategory.TREATMENT,
}

# PrimeKG / General Clinical Tools
GENERAL_TOOL_CATEGORIES: Dict[str, ToolCategory] = {
    "search_disease_info": ToolCategory.DIAGNOSIS,
    "search_drug_info": ToolCategory.TREATMENT,
    "check_drug_interactions": ToolCategory.TREATMENT,
    "get_treatment_guidelines": ToolCategory.TREATMENT,
    "get_patient_info": ToolCategory.SUGGESTION,
    "set_user_info": ToolCategory.SUGGESTION,
    "set_chief_complaint": ToolCategory.SUGGESTION,
}

# Combined mapping
MEDICAL_TOOL_CATEGORIES: Dict[str, ToolCategory] = {
    **CARDIOLOGY_TOOL_CATEGORIES,
    **ENDOCRINOLOGY_TOOL_CATEGORIES,
    **GASTROENTEROLOGY_TOOL_CATEGORIES,
    **NEPHROLOGY_TOOL_CATEGORIES,
    **NEUROLOGY_TOOL_CATEGORIES,
    **CHINESE_MEDICINE_TOOL_CATEGORIES,
    **GENERAL_TOOL_CATEGORIES,
}

# ============================================================================
# EVALUATION METRICS BY CATEGORY
# ============================================================================

# Suggestion Category Metrics
SUGGESTION_METRICS = ToolEvaluationMetrics(
    category=ToolCategory.SUGGESTION,
    metrics=[
        "relevance",      # Is the suggestion relevant to patient's condition?
        "actionability",  # Can the patient actually follow this suggestion?
        "clarity",        # Is the suggestion clear and understandable?
        "safety"         # Is the suggestion safe? Any potential risks?
    ],
    weights={
        "relevance": 0.3,
        "actionability": 0.3,
        "clarity": 0.2,
        "safety": 0.2
    }
)

# Diagnosis Category Metrics
DIAGNOSIS_METRICS = ToolEvaluationMetrics(
    category=ToolCategory.DIAGNOSIS,
    metrics=[
        "accuracy",       # Is the diagnosis/interpretation correct?
        "completeness",   # Were all relevant findings considered?
        "reasoning_logic", # Is the diagnostic reasoning sound?
        "evidence_support" # Is there evidence to support the diagnosis?
    ],
    weights={
        "accuracy": 0.4,
        "completeness": 0.2,
        "reasoning_logic": 0.2,
        "evidence_support": 0.2
    }
)

# Treatment Category Metrics
TREATMENT_METRICS = ToolEvaluationMetrics(
    category=ToolCategory.TREATMENT,
    metrics=[
        "rationality",        # Is the treatment rational for the condition?
        "evidence_based",     # Is it supported by clinical guidelines?
        "personalization",    # Is it tailored to the patient?
        "safety_checking"    # Were drug interactions/contraindications checked?
    ],
    weights={
        "rationality": 0.3,
        "evidence_based": 0.25,
        "personalization": 0.25,
        "safety_checking": 0.2
    }
)

# Metrics by category
TOOL_EVALUATION_METRICS: Dict[ToolCategory, ToolEvaluationMetrics] = {
    ToolCategory.SUGGESTION: SUGGESTION_METRICS,
    ToolCategory.DIAGNOSIS: DIAGNOSIS_METRICS,
    ToolCategory.TREATMENT: TREATMENT_METRICS,
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_tool_category(tool_name: str) -> ToolCategory:
    """
    Get the category for a given tool name.

    Args:
        tool_name: Name of the tool

    Returns:
        ToolCategory: The category this tool belongs to
    """
    # Normalize tool name (remove underscores, convert to lowercase for matching)
    normalized_name = tool_name.lower().strip()

    # Direct match
    if normalized_name in MEDICAL_TOOL_CATEGORIES:
        return MEDICAL_TOOL_CATEGORIES[normalized_name]

    # Fuzzy match - check if tool_name contains any known tool
    for known_tool, category in MEDICAL_TOOL_CATEGORIES.items():
        if known_tool in normalized_name or normalized_name in known_tool:
            return category

    # Default to SUGGESTION for unknown tools
    return ToolCategory.SUGGESTION


def get_tool_metrics(category: ToolCategory) -> ToolEvaluationMetrics:
    """
    Get the evaluation metrics for a tool category.

    Args:
        category: The tool category

    Returns:
        ToolEvaluationMetrics: Metrics for this category
    """
    return TOOL_EVALUATION_METRICS.get(category, SUGGESTION_METRICS)


def get_tools_by_category(category: ToolCategory) -> List[str]:
    """
    Get all tools belonging to a specific category.

    Args:
        category: The tool category to filter by

    Returns:
        List of tool names in this category
    """
    return [
        tool_name
        for tool_name, tool_category in MEDICAL_TOOL_CATEGORIES.items()
        if tool_category == category
    ]


def is_medical_tool(tool_name: str) -> bool:
    """
    Check if a tool is a medical tool.

    Args:
        tool_name: Name of the tool

    Returns:
        True if this is a recognized medical tool
    """
    return tool_name.lower() in MEDICAL_TOOL_CATEGORIES


def get_all_medical_tools() -> List[str]:
    """
    Get all registered medical tools.

    Returns:
        List of all medical tool names
    """
    return list(MEDICAL_TOOL_CATEGORIES.keys())


def get_category_summary() -> Dict[str, List[str]]:
    """
    Get a summary of all tools organized by category.

    Returns:
        Dictionary mapping category names to lists of tools
    """
    summary = {}
    for category in ToolCategory:
        tools = get_tools_by_category(category)
        summary[category.value] = tools
    return summary


# ============================================================================
# DECORATOR FOR TOOL CATEGORY ANNOTATION
# ============================================================================

def medical_tool(category: ToolCategory):
    """
    Decorator to annotate a tool function with its medical category.

    Usage:
        @medical_tool(ToolCategory.DIAGNOSIS)
        def assess_blood_pressure(self, systolic: int, diastolic: int) -> dict:
            ...
    """
    def decorator(func):
        # Store category as function attribute
        func._medical_tool_category = category
        return func
    return decorator


# ============================================================================
# INITIALIZATION
# ============================================================================

def register_tool_category(tool_name: str, category: ToolCategory) -> None:
    """
    Register or update a tool's category.

    Args:
        tool_name: Name of the tool
        category: Category to assign
    """
    MEDICAL_TOOL_CATEGORIES[tool_name.lower()] = category


if __name__ == "__main__":
    # Print category summary when run directly
    print("Medical Tool Categories:")
    print("=" * 60)
    summary = get_category_summary()
    for category, tools in summary.items():
        print(f"\n{category.upper()} ({len(tools)} tools):")
        for tool in tools:
            print(f"  - {tool}")
