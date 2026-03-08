#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Validators for Clinical Data
临床数据的验证器

Validation functions for clinical data processing.
"""

import re
from typing import List, Dict, Any, Optional, Callable


def validate_schema(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a schema.

    Schema format:
    {
        "required_fields": ["field1", "field2"],
        "field_types": {"field1": "string", "field2": "number"},
        "field_constraints": {
            "age": {"min": 0, "max": 120},
            "department": {"allowed_values": ["cardiology", "nephrology"]}
        }
    }

    Args:
        data: List of data records
        schema: Validation schema

    Returns:
        True if all records are valid
    """
    if not data:
        return True

    for record in data:
        if not validate_record(record, schema):
            return False

    return True


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a single record against a schema.

    Args:
        record: Data record
        schema: Validation schema

    Returns:
        True if record is valid
    """
    # Check required fields
    required_fields = schema.get("required_fields", [])
    for field in required_fields:
        if field not in record:
            return False

    # Check field types
    field_types = schema.get("field_types", {})
    for field, expected_type in field_types.items():
        if field in record:
            if not _validate_type(record[field], expected_type):
                return False

    # Check field constraints
    field_constraints = schema.get("field_constraints", {})
    for field, constraints in field_constraints.items():
        if field in record:
            if not _validate_constraints(record[field], constraints):
                return False

    return True


def _validate_type(value: Any, expected_type: str) -> bool:
    """Validate value type."""
    type_checkers = {
        "string": lambda v: isinstance(v, str),
        "number": lambda v: isinstance(v, (int, float)),
        "integer": lambda v: isinstance(v, int),
        "float": lambda v: isinstance(v, float),
        "boolean": lambda v: isinstance(v, bool),
        "list": lambda v: isinstance(v, list),
        "dict": lambda v: isinstance(v, dict),
        "any": lambda v: True,
    }

    checker = type_checkers.get(expected_type)
    if checker:
        return checker(value)

    return True


def _validate_constraints(value: Any, constraints: Dict[str, Any]) -> bool:
    """Validate value against constraints."""
    # Min/max for numeric values
    if "min" in constraints:
        if value < constraints["min"]:
            return False

    if "max" in constraints:
        if value > constraints["max"]:
            return False

    # Allowed values
    if "allowed_values" in constraints:
        if value not in constraints["allowed_values"]:
            return False

    # Pattern matching for strings
    if "pattern" in constraints:
        if not re.match(constraints["pattern"], str(value)):
            return False

    # Min/max length for strings
    if isinstance(value, str):
        if "min_length" in constraints:
            if len(value) < constraints["min_length"]:
                return False

        if "max_length" in constraints:
            if len(value) > constraints["max_length"]:
                return False

    return True


def validate_clinical_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate a clinical record and return list of errors.

    Checks for:
    - Required clinical fields
    - Valid value ranges (vital signs, lab values, etc.)
    - Data format consistency

    Args:
        record: Clinical data record

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Required fields
    required_fields = ["patient_id", "department", "diagnosis"]
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Validate vital signs ranges (if present)
    vital_signs = {
        "heart_rate": (30, 200),
        "blood_pressure_systolic": (60, 250),
        "blood_pressure_diastolic": (30, 150),
        "temperature": (30, 45),  # Celsius
        "respiratory_rate": (5, 60),
        "oxygen_saturation": (70, 100),
        "bmi": (10, 80),
    }

    for field, (min_val, max_val) in vital_signs.items():
        if field in record:
            value = record[field]
            if isinstance(value, (int, float)):
                if not (min_val <= value <= max_val):
                    errors.append(
                        f"{field} value {value} outside valid range ({min_val}-{max_val})"
                    )

    # Validate lab values (if present)
    lab_values = {
        "egfr": (0, 200),
        "creatinine": (0, 20),
        "troponin": (0, 50),
        "glucose": (0, 1000),
        "hemoglobin": (0, 25),
        "platelet_count": (0, 1000),
    }

    for field, (min_val, max_val) in lab_values.items():
        if field in record:
            value = record[field]
            if isinstance(value, (int, float)):
                if not (min_val <= value <= max_val):
                    errors.append(
                        f"{field} value {value} outside typical range ({min_val}-{max_val})"
                    )

    return errors


def validate_patient_id(patient_id: str) -> bool:
    """
    Validate patient ID format.

    Args:
        patient_id: Patient identifier

    Returns:
        True if valid format
    """
    if not patient_id:
        return False

    # Check minimum length
    if len(str(patient_id)) < 3:
        return False

    return True


def validate_department(department: str) -> bool:
    """
    Validate department name.

    Args:
        department: Department name

    Returns:
        True if valid department
    """
    valid_departments = [
        "cardiology",
        "nephrology",
        "gastroenterology",
        "neurology",
        "oncology",
        "pediatrics",
        "general_practice",
        "internal_medicine",
    ]

    return department.lower() in valid_departments


def validate_date_string(date_str: str) -> bool:
    """
    Validate date string format.

    Accepts formats:
    - ISO 8601: 2024-01-15, 2024-01-15T10:30:00
    - US: MM/DD/YYYY, MM-DD-YYYY
    - European: DD/MM/YYYY, DD-MM-YYYY

    Args:
        date_str: Date string

    Returns:
        True if valid date format
    """
    # ISO 8601 format
    iso_pattern = r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$"
    if re.match(iso_pattern, date_str):
        return True

    # US format
    us_pattern = r"^\d{2}[/-]\d{2}[/-]\d{4}$"
    if re.match(us_pattern, date_str):
        return True

    # European format
    eu_pattern = r"^\d{2}[/-]\d{2}[/-]\d{4}$"
    if re.match(eu_pattern, date_str):
        return True

    return False


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address

    Returns:
        True if valid email format
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.

    Accepts formats:
    - International: +1234567890
    - US: (123) 456-7890, 123-456-7890, 123.456.7890

    Args:
        phone: Phone number

    Returns:
        True if valid phone format
    """
    # Remove common separators
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone)

    # Check if all digits (with optional + prefix)
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]

    return cleaned.isdigit() and 10 <= len(cleaned) <= 15


def validate_ssn(ssn: str) -> bool:
    """
    Validate US Social Security Number format.

    Args:
        ssn: SSN string

    Returns:
        True if valid SSN format (XXX-XX-XXXX)
    """
    pattern = r"^\d{3}-\d{2}-\d{4}$"
    return re.match(pattern, ssn) is not None


def create_validator_from_schema(schema: Dict[str, Any]) -> Callable:
    """
    Create a validator function from a schema.

    Args:
        schema: Validation schema

    Returns:
        Validator function that takes a record and returns bool
    """
    def validator(record: Dict[str, Any]) -> bool:
        return validate_record(record, schema)

    return validator
