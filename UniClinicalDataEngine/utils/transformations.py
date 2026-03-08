#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Transformations for Clinical Data
临床数据的数据转换

Common transformation functions for clinical data processing.
"""

import hashlib
import re
from typing import List, Dict, Any, Callable, Optional


def normalize_fields(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize field names and values in records.

    Normalizes:
    - Field names: convert to snake_case, remove special chars
    - Strings: strip whitespace, normalize case
    - Numbers: ensure numeric types
    - Dates: standardize format (ISO 8601)

    Args:
        data: List of data records

    Returns:
        Normalized data
    """
    normalized = []

    for record in data:
        new_record = {}

        for key, value in record.items():
            # Normalize key: snake_case, lowercase
            norm_key = _to_snake_case(key).lower().strip()

            # Normalize value based on type
            norm_value = _normalize_value(value)

            new_record[norm_key] = norm_value

        normalized.append(new_record)

    return normalized


def _to_snake_case(text: str) -> str:
    """Convert text to snake_case."""
    # Insert underscores before capital letters
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    # Insert underscores before capital letters followed by lowercase
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    # Replace spaces and special chars with underscores
    s3 = re.sub(r'[\s\-]+', '_', s2)
    # Remove non-alphanumeric chars except underscores
    s4 = re.sub(r'[^a-zA-Z0-9_]', '', s3)
    return s4.lower()


def _normalize_value(value: Any) -> Any:
    """Normalize a value to its appropriate type."""
    if value is None:
        return None

    if isinstance(value, str):
        # Strip whitespace
        value = value.strip()

        # Try to convert to number
        if value.isdigit():
            return int(value)

        if value.replace(".", "", 1).replace("-", "", 1).isdigit():
            return float(value)

        # Try to convert to boolean
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        return value

    if isinstance(value, (int, float, bool)):
        return value

    if isinstance(value, list):
        return [_normalize_value(v) for v in value]

    if isinstance(value, dict):
        return {k: _normalize_value(v) for k, v in value.items()}

    return str(value)


def deduplicate(data: List[Dict[str, Any]], key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Remove duplicate records from data.

    Args:
        data: List of data records
        key: Field to use as unique identifier (uses all fields if None)

    Returns:
        Deduplicated data
    """
    if not data:
        return data

    seen = set()
    deduplicated = []

    for record in data:
        if key:
            # Use specific field as identifier
            identifier = record.get(key)
        else:
            # Use hash of entire record as identifier
            record_str = json.dumps(record, sort_keys=True)
            identifier = hashlib.md5(record_str.encode()).hexdigest()

        if identifier not in seen:
            seen.add(identifier)
            deduplicated.append(record)

    return deduplicated


def anonymize(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Anonymize sensitive fields in clinical data.

    Anonymizes common PHI (Protected Health Information) fields:
    - patient_id, patient_name, name
    - ssn, social_security
    - email, phone, address
    - dob, date_of_birth

    Args:
        data: List of data records

    Returns:
        Anonymized data
    """
    import json

    # Patterns for sensitive fields
    sensitive_patterns = [
        r'patient.*id',
        r'patient.*name',
        r'\bname\b',
        r'ssn',
        r'social.*security',
        r'\bemail\b',
        r'\bphone\b',
        r'address',
        r'dob',
        r'date.*of.*birth',
    ]

    # Compile pattern
    pattern = re.compile('|'.join(sensitive_patterns), re.IGNORECASE)

    anonymized = []

    for record in data:
        new_record = {}

        for key, value in record.items():
            if pattern.search(key):
                # Anonymize sensitive field
                new_record[key] = _anonymize_value(value)
            else:
                new_record[key] = value

        anonymized.append(new_record)

    return anonymized


def _anonymize_value(value: Any) -> str:
    """Anonymize a value."""
    if value is None:
        return None

    value_str = str(value)

    # Return hash of value
    return hashlib.sha256(value_str.encode()).hexdigest()[:16]


def filter_by_field(
    data: List[Dict[str, Any]],
    field: str,
    value: Any
) -> List[Dict[str, Any]]:
    """
    Filter records by field value.

    Args:
        data: List of data records
        field: Field name to filter on
        value: Value to match

    Returns:
        Filtered data
    """
    return [r for r in data if r.get(field) == value]


def filter_by_range(
    data: List[Dict[str, Any]],
    field: str,
    min_value: Optional[Any] = None,
    max_value: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Filter records by numeric range.

    Args:
        data: List of data records
        field: Field name to filter on
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)

    Returns:
        Filtered data
    """
    filtered = []

    for record in data:
        field_value = record.get(field)

        if field_value is None:
            continue

        if min_value is not None and field_value < min_value:
            continue

        if max_value is not None and field_value > max_value:
            continue

        filtered.append(record)

    return filtered


def aggregate_by_field(
    data: List[Dict[str, Any]],
    group_by: str,
    aggregations: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Aggregate data by field.

    Args:
        data: List of data records
        group_by: Field to group by
        aggregations: Dictionary of {field: aggregation_type}
                     (aggregation_type: count, sum, avg, min, max)

    Returns:
        Aggregated data
    """
    groups = {}

    for record in data:
        group_key = record.get(group_by, "unknown")

        if group_key not in groups:
            groups[group_key] = []

        groups[group_key].append(record)

    results = []

    for group_key, group_records in groups.items():
        result = {group_by: group_key}

        for field, agg_type in aggregations.items():
            values = [r.get(field) for r in group_records if field in r]

            if not values:
                result[f"{field}_{agg_type}"] = None
                continue

            if agg_type == "count":
                result[f"{field}_{agg_type}"] = len(values)
            elif agg_type == "sum":
                result[f"{field}_{agg_type}"] = sum(values)
            elif agg_type == "avg":
                result[f"{field}_{agg_type}"] = sum(values) / len(values)
            elif agg_type == "min":
                result[f"{field}_{agg_type}"] = min(values)
            elif agg_type == "max":
                result[f"{field}_{agg_type}"] = max(values)

        results.append(result)

    return results


def rename_fields(
    data: List[Dict[str, Any]],
    mapping: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Rename fields in records.

    Args:
        data: List of data records
        mapping: Dictionary of {old_name: new_name}

    Returns:
        Data with renamed fields
    """
    renamed = []

    for record in data:
        new_record = {}

        for key, value in record.items():
            new_key = mapping.get(key, key)
            new_record[new_key] = value

        renamed.append(new_record)

    return renamed


def select_fields(
    data: List[Dict[str, Any]],
    fields: List[str]
) -> List[Dict[str, Any]]:
    """
    Select specific fields from records.

    Args:
        data: List of data records
        fields: List of field names to keep

    Returns:
        Data with selected fields
    """
    selected = []

    for record in data:
        new_record = {f: record.get(f) for f in fields if f in record}
        selected.append(new_record)

    return selected
