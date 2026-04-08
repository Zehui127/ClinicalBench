#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tool Call Format Validator

Validates tool call arguments against schema definitions from
tool_aware_generator.py. Checks required args, types, enums, and ranges.

Usage:
    validator = ToolCallValidator()
    result = validator.validate_tool_call("prescribe_medication", {
        "medication": "metformin", "dose": "500mg"
    })
    print(result.is_valid, result.errors)
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class ErrorType(str, Enum):
    MISSING_REQUIRED = "missing_required"
    WRONG_TYPE = "wrong_type"
    INVALID_ENUM = "invalid_enum"
    OUT_OF_RANGE = "out_of_range"
    PATTERN_MISMATCH = "pattern_mismatch"
    UNKNOWN_ARG = "unknown_arg"


class Severity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


@dataclass
class ToolArgSchema:
    """Schema for a single tool argument."""
    name: str
    type: str                    # "int", "str", "float", "bool", "list", "enum"
    required: bool = True
    enum_values: List[str] = field(default_factory=list)
    item_type: Optional[str] = None    # For list types: "str", "int"
    min_value: Optional[float] = None  # For numeric types
    max_value: Optional[float] = None
    pattern: Optional[str] = None      # Regex for string validation
    description: str = ""


@dataclass
class ValidationError:
    """A single validation error."""
    tool_name: str
    arg_name: str
    error_type: ErrorType
    expected: str
    actual: str
    severity: Severity = Severity.MAJOR

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool_name,
            "arg": self.arg_name,
            "error_type": self.error_type.value,
            "expected": self.expected,
            "actual": self.actual,
            "severity": self.severity.value,
        }


@dataclass
class ValidationResult:
    """Validation result for a single tool call."""
    tool_name: str
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool_name,
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
        }


@dataclass
class BatchValidationMetrics:
    """Aggregate validation metrics across many tool calls."""
    total_calls: int = 0
    valid_calls: int = 0
    invalid_calls: int = 0
    error_rate: float = 0.0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    errors_by_tool: Dict[str, int] = field(default_factory=dict)
    critical_errors: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "valid_calls": self.valid_calls,
            "invalid_calls": self.invalid_calls,
            "error_rate": round(self.error_rate, 3),
            "errors_by_type": self.errors_by_type,
            "errors_by_tool": self.errors_by_tool,
            "critical_errors": self.critical_errors,
        }


# ============================================================
# Tool argument schemas derived from tool_aware_generator.py
# ============================================================

TOOL_ARG_SCHEMAS: Dict[str, List[ToolArgSchema]] = {
    # --- Suggestion tools ---
    "get_patient_info": [
        ToolArgSchema("patient_identifier", "str", required=True,
                      description="Patient MRN or ID"),
    ],
    "set_user_info": [
        ToolArgSchema("name", "str", required=True),
        ToolArgSchema("age", "int", required=True, min_value=0, max_value=150),
        ToolArgSchema("gender", "enum", required=True,
                      enum_values=["male", "female", "other"]),
        ToolArgSchema("mrn", "str", required=False),
    ],
    "health_education": [
        ToolArgSchema("topic", "str", required=True),
        ToolArgSchema("detail_level", "enum", required=False,
                      enum_values=["basic", "intermediate", "detailed"]),
    ],
    "lifestyle_guidance": [
        ToolArgSchema("area", "str", required=True),
        ToolArgSchema("specific_recommendation", "str", required=False),
    ],
    # --- Diagnosis tools ---
    "order_lab_tests": [
        ToolArgSchema("tests", "list", required=True, item_type="str",
                      description="List of test names to order"),
        ToolArgSchema("priority", "enum", required=False,
                      enum_values=["routine", "urgent", "stat"]),
        ToolArgSchema("fasting_required", "bool", required=False),
    ],
    "get_lab_results": [
        ToolArgSchema("patient_id", "str", required=True),
        ToolArgSchema("test_names", "list", required=False, item_type="str"),
    ],
    "assess_blood_pressure": [
        ToolArgSchema("systolic", "int", required=True, min_value=40, max_value=300),
        ToolArgSchema("diastolic", "int", required=True, min_value=20, max_value=200),
        ToolArgSchema("position", "enum", required=False,
                      enum_values=["sitting", "standing", "lying"]),
        ToolArgSchema("arm", "enum", required=False,
                      enum_values=["left", "right"]),
    ],
    "assess_blood_glucose": [
        ToolArgSchema("glucose_value", "float", required=True, min_value=0, max_value=50),
        ToolArgSchema("unit", "enum", required=True,
                      enum_values=["mg/dL", "mmol/L"]),
        ToolArgSchema("fasting_status", "bool", required=False),
    ],
    "interpret_hba1c": [
        ToolArgSchema("hba1c_value", "float", required=True, min_value=2.0, max_value=20.0),
    ],
    "assess_kidney_function": [
        ToolArgSchema("creatinine", "float", required=True, min_value=0.1, max_value=20.0),
        ToolArgSchema("age", "int", required=True, min_value=1, max_value=120),
        ToolArgSchema("gender", "enum", required=True,
                      enum_values=["male", "female"]),
        ToolArgSchema("race", "enum", required=False,
                      enum_values=["black", "non-black"]),
    ],
    "complete_blood_count": [
        ToolArgSchema("wbc", "float", required=True, min_value=0, max_value=100),
        ToolArgSchema("hgb", "float", required=True, min_value=0, max_value=25),
        ToolArgSchema("platelets", "int", required=True, min_value=0, max_value=1000),
        ToolArgSchema("diff", "str", required=False),
    ],
    "check_electrolytes": [
        ToolArgSchema("sodium", "float", required=True, min_value=100, max_value=170),
        ToolArgSchema("potassium", "float", required=True, min_value=1.0, max_value=8.0),
        ToolArgSchema("chloride", "float", required=False, min_value=60, max_value=140),
        ToolArgSchema("bicarbonate", "float", required=False, min_value=5, max_value=50),
    ],
    "differential_diagnosis": [
        ToolArgSchema("symptoms", "list", required=True, item_type="str"),
        ToolArgSchema("exclude", "list", required=False, item_type="str"),
    ],
    "record_diagnosis": [
        ToolArgSchema("diagnosis", "str", required=True),
        ToolArgSchema("icd_code", "str", required=False),
        ToolArgSchema("certainty", "enum", required=False,
                      enum_values=["definitive", "probable", "possible", "unlikely"]),
    ],
    # --- Treatment tools ---
    "prescribe_medication": [
        ToolArgSchema("medication", "str", required=True),
        ToolArgSchema("dose", "str", required=True),
        ToolArgSchema("frequency", "str", required=False),
        ToolArgSchema("duration", "str", required=False),
        ToolArgSchema("route", "enum", required=False,
                      enum_values=["oral", "iv", "im", "subcutaneous", "topical", "inhaled"]),
    ],
    "check_allergy": [
        ToolArgSchema("patient_id", "str", required=True),
        ToolArgSchema("drug_name", "str", required=False),
    ],
    "check_drug_interactions": [
        ToolArgSchema("drug_list", "list", required=True, item_type="str"),
    ],
    "get_medication_dosage": [
        ToolArgSchema("medication", "str", required=True),
        ToolArgSchema("indication", "str", required=True),
        ToolArgSchema("patient_weight", "float", required=False, min_value=0, max_value=300),
        ToolArgSchema("kidney_function", "enum", required=False,
                      enum_values=["normal", "mild_impairment", "moderate_impairment", "severe_impairment"]),
    ],
    "check_contraindications": [
        ToolArgSchema("medication", "str", required=True),
        ToolArgSchema("conditions", "list", required=True, item_type="str"),
    ],
    "find_alternative_medication": [
        ToolArgSchema("original_medication", "str", required=True),
        ToolArgSchema("reason", "str", required=True),
        ToolArgSchema("preferred_class", "str", required=False),
    ],
    "transfer_to_specialist": [
        ToolArgSchema("specialty", "str", required=True),
        ToolArgSchema("reason", "str", required=True),
        ToolArgSchema("urgency", "enum", required=False,
                      enum_values=["routine", "urgent", "emergency"]),
    ],
    "schedule_followup": [
        ToolArgSchema("timeframe", "str", required=True),
        ToolArgSchema("tests_to_repeat", "list", required=False, item_type="str"),
    ],
    # --- ECG / Imaging ---
    "ecg_interpretation": [
        ToolArgSchema("patient_id", "str", required=True),
        ToolArgSchema("indication", "str", required=False),
    ],
    "chest_xray_review": [
        ToolArgSchema("patient_id", "str", required=True),
        ToolArgSchema("indication", "str", required=False),
    ],
    "find_patient_info": [
        ToolArgSchema("query", "str", required=False),
        ToolArgSchema("should_lookup", "bool", required=False),
    ],
}


class ToolCallValidator:
    """
    Validates tool call arguments against defined schemas.

    Checks:
    1. Required arguments are present
    2. Argument types match expected types
    3. Enum values are in allowed set
    4. Numeric values are within min/max range
    """

    def validate_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate a single tool call.

        Args:
            tool_name: Name of the tool being called
            arguments: Dict of argument name -> value

        Returns:
            ValidationResult with errors and warnings
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        schemas = TOOL_ARG_SCHEMAS.get(tool_name)
        if schemas is None:
            # Unknown tool — return valid with warning
            warnings.append(ValidationError(
                tool_name=tool_name,
                arg_name="",
                error_type=ErrorType.UNKNOWN_ARG,
                expected="known tool",
                actual=f"unknown tool: {tool_name}",
                severity=Severity.MINOR,
            ))
            return ValidationResult(
                tool_name=tool_name,
                is_valid=True,
                errors=[],
                warnings=warnings,
            )

        schema_by_name = {s.name: s for s in schemas}

        # Check required args
        for schema in schemas:
            if schema.required and schema.name not in arguments:
                errors.append(ValidationError(
                    tool_name=tool_name,
                    arg_name=schema.name,
                    error_type=ErrorType.MISSING_REQUIRED,
                    expected=f"required argument of type {schema.type}",
                    actual="missing",
                    severity=Severity.CRITICAL,
                ))

        # Validate present args
        for arg_name, arg_value in arguments.items():
            schema = schema_by_name.get(arg_name)
            if schema is None:
                warnings.append(ValidationError(
                    tool_name=tool_name,
                    arg_name=arg_name,
                    error_type=ErrorType.UNKNOWN_ARG,
                    expected="known argument",
                    actual=f"unknown argument: {arg_name}",
                    severity=Severity.MINOR,
                ))
                continue

            type_errors = self._validate_type(schema, arg_value, tool_name)
            errors.extend(type_errors)

        is_valid = len(errors) == 0
        return ValidationResult(
            tool_name=tool_name,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
        )

    def validate_batch(
        self,
        tool_calls: List[Dict[str, Any]],
    ) -> Dict[str, ValidationResult]:
        """
        Validate a batch of tool calls.

        Args:
            tool_calls: List of {"tool": str, "arguments": dict}

        Returns:
            Dict mapping tool call index to ValidationResult
        """
        results = {}
        for i, tc in enumerate(tool_calls):
            tool_name = tc.get("tool", tc.get("name", ""))
            arguments = tc.get("arguments", {})
            results[f"{i}_{tool_name}"] = self.validate_tool_call(
                tool_name, arguments
            )
        return results

    def get_error_metrics(
        self,
        results: Dict[str, ValidationResult],
    ) -> BatchValidationMetrics:
        """Compute aggregate error metrics from validation results."""
        metrics = BatchValidationMetrics()
        metrics.total_calls = len(results)
        metrics.valid_calls = sum(1 for r in results.values() if r.is_valid)
        metrics.invalid_calls = metrics.total_calls - metrics.valid_calls
        metrics.error_rate = (
            metrics.invalid_calls / metrics.total_calls
            if metrics.total_calls > 0 else 0.0
        )

        for key, result in results.items():
            for error in result.errors:
                error_type = error.error_type.value
                metrics.errors_by_type[error_type] = (
                    metrics.errors_by_type.get(error_type, 0) + 1
                )
                metrics.errors_by_tool[error.tool_name] = (
                    metrics.errors_by_tool.get(error.tool_name, 0) + 1
                )
                if error.severity == Severity.CRITICAL:
                    metrics.critical_errors += 1

        return metrics

    def get_validation_rules(self) -> List[Dict[str, Any]]:
        """Export validation rules for task JSON embedding."""
        rules = []
        for tool_name, schemas in TOOL_ARG_SCHEMAS.items():
            for schema in schemas:
                rule = {
                    "tool": tool_name,
                    "arg": schema.name,
                    "type": schema.type,
                    "required": schema.required,
                }
                if schema.enum_values:
                    rule["enum_values"] = schema.enum_values
                if schema.min_value is not None:
                    rule["min"] = schema.min_value
                if schema.max_value is not None:
                    rule["max"] = schema.max_value
                rules.append(rule)
        return rules

    def _validate_type(
        self,
        schema: ToolArgSchema,
        value: Any,
        tool_name: str,
    ) -> List[ValidationError]:
        """Validate a single argument value against its schema."""
        errors = []

        if schema.type == "int":
            if not isinstance(value, int) or isinstance(value, bool):
                # Allow float that is whole number
                if isinstance(value, float) and value == int(value):
                    pass  # Accept 140.0 as 140
                else:
                    errors.append(ValidationError(
                        tool_name=tool_name,
                        arg_name=schema.name,
                        error_type=ErrorType.WRONG_TYPE,
                        expected="int",
                        actual=type(value).__name__,
                        severity=Severity.MAJOR,
                    ))
                    return errors

            if schema.min_value is not None and value < schema.min_value:
                errors.append(ValidationError(
                    tool_name=tool_name,
                    arg_name=schema.name,
                    error_type=ErrorType.OUT_OF_RANGE,
                    expected=f">= {schema.min_value}",
                    actual=str(value),
                    severity=Severity.MAJOR,
                ))
            if schema.max_value is not None and value > schema.max_value:
                errors.append(ValidationError(
                    tool_name=tool_name,
                    arg_name=schema.name,
                    error_type=ErrorType.OUT_OF_RANGE,
                    expected=f"<= {schema.max_value}",
                    actual=str(value),
                    severity=Severity.MAJOR,
                ))

        elif schema.type == "float":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(ValidationError(
                    tool_name=tool_name,
                    arg_name=schema.name,
                    error_type=ErrorType.WRONG_TYPE,
                    expected="float",
                    actual=type(value).__name__,
                    severity=Severity.MAJOR,
                ))
                return errors

            if schema.min_value is not None and value < schema.min_value:
                errors.append(ValidationError(
                    tool_name=tool_name,
                    arg_name=schema.name,
                    error_type=ErrorType.OUT_OF_RANGE,
                    expected=f">= {schema.min_value}",
                    actual=str(value),
                    severity=Severity.MAJOR,
                ))
            if schema.max_value is not None and value > schema.max_value:
                errors.append(ValidationError(
                    tool_name=tool_name,
                    arg_name=schema.name,
                    error_type=ErrorType.OUT_OF_RANGE,
                    expected=f"<= {schema.max_value}",
                    actual=str(value),
                    severity=Severity.MAJOR,
                ))

        elif schema.type == "str":
            if not isinstance(value, str):
                errors.append(ValidationError(
                    tool_name=tool_name,
                    arg_name=schema.name,
                    error_type=ErrorType.WRONG_TYPE,
                    expected="str",
                    actual=type(value).__name__,
                    severity=Severity.MAJOR,
                ))

        elif schema.type == "bool":
            if not isinstance(value, bool):
                errors.append(ValidationError(
                    tool_name=tool_name,
                    arg_name=schema.name,
                    error_type=ErrorType.WRONG_TYPE,
                    expected="bool",
                    actual=type(value).__name__,
                    severity=Severity.MAJOR,
                ))

        elif schema.type == "list":
            if not isinstance(value, list):
                errors.append(ValidationError(
                    tool_name=tool_name,
                    arg_name=schema.name,
                    error_type=ErrorType.WRONG_TYPE,
                    expected="list",
                    actual=type(value).__name__,
                    severity=Severity.MAJOR,
                ))
            elif schema.item_type == "str":
                for i, item in enumerate(value):
                    if not isinstance(item, str):
                        errors.append(ValidationError(
                            tool_name=tool_name,
                            arg_name=f"{schema.name}[{i}]",
                            error_type=ErrorType.WRONG_TYPE,
                            expected=f"str (item_type)",
                            actual=type(item).__name__,
                            severity=Severity.MINOR,
                        ))

        elif schema.type == "enum":
            if not isinstance(value, str):
                errors.append(ValidationError(
                    tool_name=tool_name,
                    arg_name=schema.name,
                    error_type=ErrorType.WRONG_TYPE,
                    expected="str (enum)",
                    actual=type(value).__name__,
                    severity=Severity.MAJOR,
                ))
            elif schema.enum_values and value not in schema.enum_values:
                errors.append(ValidationError(
                    tool_name=tool_name,
                    arg_name=schema.name,
                    error_type=ErrorType.INVALID_ENUM,
                    expected=f"one of {schema.enum_values}",
                    actual=value,
                    severity=Severity.MAJOR,
                ))

        return errors
