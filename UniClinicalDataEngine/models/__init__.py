"""
Data Models for UniClinicalDataEngine
UniClinicalDataEngine 的数据模型

Common data structures and schemas for clinical data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class Department(Enum):
    """Clinical department enumeration."""
    CARDIOLOGY = "cardiology"
    NEPHROLOGY = "nephrology"
    GASTROENTEROLOGY = "gastroenterology"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    PEDIATRICS = "pediatrics"
    GENERAL_PRACTICE = "general_practice"
    INTERNAL_MEDICINE = "internal_medicine"


class Difficulty(Enum):
    """Task difficulty enumeration."""
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"


@dataclass
class ClinicalRecord:
    """
    Base clinical data record.
    基础临床数据记录。
    """
    patient_id: str
    department: str
    diagnosis: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "patient_id": self.patient_id,
            "department": self.department,
            "diagnosis": self.diagnosis,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClinicalRecord":
        """Create from dictionary."""
        return cls(
            patient_id=data.get("patient_id", ""),
            department=data.get("department", ""),
            diagnosis=data.get("diagnosis", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class VitalSigns:
    """
    Vital signs measurements.
    生命体征测量。
    """
    heart_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, omitting None values."""
        return {
            k: v for k, v in {
                "heart_rate": self.heart_rate,
                "blood_pressure_systolic": self.blood_pressure_systolic,
                "blood_pressure_diastolic": self.blood_pressure_diastolic,
                "temperature": self.temperature,
                "respiratory_rate": self.respiratory_rate,
                "oxygen_saturation": self.oxygen_saturation,
            }.items() if v is not None
        }


@dataclass
class LabResult:
    """
    Laboratory test result.
    实验室检查结果。
    """
    test_name: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    is_abnormal: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "value": self.value,
            "unit": self.unit,
            "reference_range": self.reference_range,
            "is_abnormal": self.is_abnormal,
        }


@dataclass
class ClinicalTask:
    """
    Clinical task for benchmark evaluation.
    临床基准评估任务。
    """
    task_id: str
    department: str
    difficulty: str
    description: str
    clinical_scenario: Dict[str, Any]
    tool_call_requirements: Dict[str, Any]
    expected_outcome: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "department": self.department,
            "difficulty": self.difficulty,
            "description": self.description,
            "clinical_scenario": self.clinical_scenario,
            "tool_call_requirements": self.tool_call_requirements,
            "expected_outcome": self.expected_outcome,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClinicalTask":
        """Create from dictionary."""
        return cls(
            task_id=data.get("task_id", data.get("id", "")),
            department=data.get("department", ""),
            difficulty=data.get("difficulty", ""),
            description=data.get("description", ""),
            clinical_scenario=data.get("clinical_scenario", {}),
            tool_call_requirements=data.get("tool_call_requirements", {}),
            expected_outcome=data.get("expected_outcome"),
            metadata=data.get("metadata", {}),
        )


# Common schemas for validation
CLINICAL_RECORD_SCHEMA = {
    "required_fields": ["patient_id", "department", "diagnosis"],
    "field_types": {
        "patient_id": "string",
        "department": "string",
        "diagnosis": "string",
    },
    "field_constraints": {
        "department": {
            "allowed_values": [d.value for d in Department]
        }
    }
}

CLINICAL_TASK_SCHEMA = {
    "required_fields": ["task_id", "department", "difficulty", "description"],
    "field_types": {
        "task_id": "string",
        "department": "string",
        "difficulty": "string",
        "description": "string",
    },
    "field_constraints": {
        "department": {
            "allowed_values": [d.value for d in Department]
        },
        "difficulty": {
            "allowed_values": [d.value for d in Difficulty]
        }
    }
}


# Alias for backward compatibility
# ClinicalScenario is used in db_builder.py, but ClinicalTask is the actual class
ClinicalScenario = ClinicalTask
