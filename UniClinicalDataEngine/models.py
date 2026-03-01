"""Pydantic models for UniClinicalDataEngine."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PatientRecord(BaseModel):
    """Normalized patient record extracted from any clinical data source."""

    patient_id: str = Field(description="Unique patient identifier")
    name: Optional[str] = Field(default=None, description="Patient name")
    age: Optional[int] = Field(default=None, description="Patient age")
    sex: Optional[str] = Field(default=None, description="Patient sex/gender")
    chief_complaint: Optional[str] = Field(
        default=None, description="Chief complaint or reason for visit"
    )
    medical_history: Optional[List[str]] = Field(
        default=None, description="List of past medical conditions"
    )
    current_medications: Optional[List[str]] = Field(
        default=None, description="List of current medications"
    )
    allergies: Optional[List[str]] = Field(
        default=None, description="Known allergies"
    )
    vitals: Optional[Dict[str, Any]] = Field(
        default=None, description="Vital signs (e.g., BP, HR, temp)"
    )
    lab_results: Optional[Dict[str, Any]] = Field(
        default=None, description="Lab test results"
    )
    diagnoses: Optional[List[str]] = Field(
        default=None, description="Diagnoses or differential diagnoses"
    )
    notes: Optional[str] = Field(
        default=None, description="Free-text clinical notes"
    )
    extra: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional source-specific fields"
    )


class ClinicalScenario(BaseModel):
    """A clinical scenario constructed from one or more patient records."""

    scenario_id: str = Field(description="Unique scenario identifier")
    patient: PatientRecord = Field(description="The patient record for this scenario")
    reason_for_call: str = Field(
        description="Why the patient is contacting the clinician"
    )
    task_instructions: str = Field(
        description="Instructions for the simulated patient"
    )
    expected_actions: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Expected clinician actions for evaluation"
    )
    nl_assertions: Optional[List[str]] = Field(
        default=None, description="Natural language evaluation assertions"
    )
    difficulty: Optional[str] = Field(
        default=None, description="Estimated difficulty: easy, medium, hard"
    )
    clinical_domain: Optional[str] = Field(
        default=None, description="Clinical subdomain (e.g., cardiology, ER)"
    )


class ClinicalToolSpec(BaseModel):
    """Specification for a clinical tool to be generated."""

    name: str = Field(description="Tool function name")
    description: str = Field(description="Tool description / docstring")
    parameters: Dict[str, Dict[str, str]] = Field(
        description="Parameter name -> {type, description}"
    )
    return_type: str = Field(
        default="str", description="Return type annotation"
    )
    tool_type: str = Field(
        default="read", description="Tool type: read, write, think, generic"
    )


class EngineConfig(BaseModel):
    """Configuration for the UniClinicalDataEngine."""

    source_type: str = Field(description="Data source type: nhands, csv, json")
    source_path: str = Field(description="Path to the source data")
    output_dir: str = Field(
        default="output", description="Directory for output files"
    )
    domain_name: str = Field(
        default="clinical", description="Domain name for tau2 tasks"
    )
    adapter_kwargs: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional kwargs passed to the adapter"
    )
