# Copyright Sierra

"""
Medical Domain Task Data Models

Defines medical-specific user personas, disease-symptom mappings,
and evaluation criteria for the healthcare domain.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ToolCategory(str, Enum):
    """Medical tool categories for classification and evaluation."""

    SUGGESTION = "suggestion"  # Health education, lifestyle advice
    DIAGNOSIS = "diagnosis"    # Symptom analysis, test interpretation
    TREATMENT = "treatment"    # Medication guidance, treatment planning


class MedicalPersona(BaseModel):
    """
    Medical user persona containing only clinically relevant information.

    This persona model focuses on medical diagnosis and excludes
    non-medical fields like occupation, hobbies, or location (unless
    medically relevant).
    """

    # Basic Information
    age: int = Field(description="Patient age in years")
    gender: str = Field(description="Patient gender (male/female/other)")

    # Clinical Information
    symptoms: List[str] = Field(
        default_factory=list,
        description="List of symptoms the patient is experiencing"
    )
    duration: Optional[str] = Field(
        None,
        description="Duration of symptoms (e.g., '21 days', '2 weeks')"
    )
    severity: Optional[str] = Field(
        None,
        description="Severity of symptoms (e.g., 'mild', 'moderate', 'severe')"
    )

    # Medical History
    past_medical_history: List[str] = Field(
        default_factory=list,
        description="List of past medical conditions and diagnoses"
    )
    current_medications: List[str] = Field(
        default_factory=list,
        description="List of current medications the patient is taking"
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="List of known allergies (medications, food, environmental)"
    )

    # Test Results
    lab_results: Dict[str, str] = Field(
        default_factory=dict,
        description="Laboratory test results (e.g., {'blood_glucose': '120 mg/dL'})"
    )
    vital_signs: Dict[str, str] = Field(
        default_factory=dict,
        description="Vital signs (e.g., {'blood_pressure': '120/80', 'heart_rate': '72'})"
    )

    # Social History (clinically relevant only)
    smoking_status: Optional[str] = Field(
        None,
        description="Smoking status (never/former/current)"
    )
    alcohol_use: Optional[str] = Field(
        None,
        description="Alcohol consumption (none/moderate/heavy)"
    )

    class Config:
        schema_extra = {
            "example": {
                "age": 54,
                "gender": "male",
                "symptoms": ["severe headache", "eye pain", "nasal congestion"],
                "duration": "21 days",
                "severity": "severe",
                "past_medical_history": ["hypertension", "type 2 diabetes"],
                "current_medications": ["lisinopril 10mg", "metformin 500mg"],
                "allergies": ["penicillin"],
                "lab_results": {},
                "vital_signs": {"blood_pressure": "140/90"},
                "smoking_status": "former",
                "alcohol_use": "moderate"
            }
        }


class DiseaseSymptomMapping(BaseModel):
    """Mapping between diseases and their associated symptoms."""

    disease_id: str = Field(description="Unique disease identifier from knowledge graph")
    disease_name: str = Field(description="Name of the disease")
    typical_symptoms: List[str] = Field(description="Symptoms typically present in this disease")
    associated_symptoms: List[str] = Field(description="Symptoms that may be associated")
    prevalence: float = Field(
        default=1.0,
        description="Prevalence of symptoms (0.0 to 1.0)"
    )


class MedicalEvaluationCriteria(BaseModel):
    """
    Quantifiable evaluation criteria for medical domain tasks.

    Defines explicit, measurable criteria for evaluating agent performance
    in medical consultations.
    """

    # Tool Selection Criteria
    expected_tool_category: Optional[ToolCategory] = Field(
        None,
        description="Expected tool category for this task"
    )
    required_tools: List[str] = Field(
        default_factory=list,
        description="List of required tools that must be used"
    )
    optional_tools: List[str] = Field(
        default_factory=list,
        description="Optional tools that may enhance the response"
    )

    # Parameter Extraction Criteria
    required_parameters: Dict[str, object] = Field(
        default_factory=dict,
        description="Required parameters that must be extracted (e.g., {'age': 54, 'systolic': 140})"
    )

    # Reasoning Chain Criteria
    reasoning_steps: List[str] = Field(
        default_factory=list,
        description="Expected reasoning steps in the diagnostic process"
    )

    # Safety Criteria
    safety_checks: List[str] = Field(
        default_factory=list,
        description="Required safety checks (e.g., 'check_allergies', 'check_drug_interactions')"
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Red flag violations that result in automatic failure"
    )

    # Conversation Criteria
    min_turns: int = Field(
        default=5,
        description="Minimum number of conversation turns expected"
    )
    max_turns: int = Field(
        default=10,
        description="Maximum number of conversation turns expected"
    )

    # Information Completeness
    information_level: str = Field(
        default="partial",
        description="Patient information level (complete/partial/minimal)"
    )

    class Config:
        schema_extra = {
            "example": {
                "expected_tool_category": ToolCategory.DIAGNOSIS,
                "required_tools": ["assess_blood_pressure", "get_patient_by_mrn"],
                "required_parameters": {"systolic": 140, "diastolic": 90, "age": 54},
                "reasoning_steps": [
                    "Assess blood pressure values",
                    "Classify hypertension stage",
                    "Check for risk factors",
                    "Provide treatment recommendations"
                ],
                "safety_checks": ["check_allergies", "check_current_medications"],
                "red_flags": ["never_tell_patient_to_stop_medication"],
                "min_turns": 5,
                "max_turns": 10,
                "information_level": "partial"
            }
        }


class ToolEvaluationMetrics(BaseModel):
    """Evaluation metrics for a specific tool category."""

    category: ToolCategory = Field(description="Tool category being evaluated")
    metrics: List[str] = Field(description="List of metrics for this category")
    weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Weight for each metric (sums to 1.0)"
    )

    def get_weighted_score(self, scores: Dict[str, float]) -> float:
        """
        Calculate weighted score from individual metric scores.

        Args:
            scores: Dictionary of metric_name -> score (0-1)

        Returns:
            Weighted overall score
        """
        total_weight = 0.0
        weighted_sum = 0.0

        for metric, weight in self.weights.items():
            if metric in scores:
                weighted_sum += scores[metric] * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0
