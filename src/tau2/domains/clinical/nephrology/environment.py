"""
Environment Setup for Clinical Nephrology Domain
"""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.clinical.nephrology.tools import NephrologyTools
from tau2.domains.clinical.nephrology.utils import (
    DB_PATH,
    POLICY_PATH,
    TASKS_PATH,
)
from tau2.environment.environment import Environment
from tau2.utils import load_file



# === DATA MODELS ===
"""Data Models for Clinical Nephrology Domain

Defines patient records, lab results, and kidney function data
"""

import json
from typing import Dict, List, Optional
from pydantic import BaseModel
from tau2.domains.clinical.user_simulator import ClinicalUserDB, ClinicalUserTools



class KidneyFunction(BaseModel):
    """Kidney function lab results"""
    creatinine: float  # mg/dL
    egfr: float  # mL/min/1.73m²
    bun: Optional[float] = None  # mg/dL
    potassium: Optional[float] = None  # mEq/L
    sodium: Optional[float] = None  # mEq/L
    albumin: Optional[float] = None  # g/dL


class PatientRecord(BaseModel):
    """Patient medical record for nephrology"""
    patient_id: str
    name: str
    age: int
    gender: str  # "male" or "female"
    race: Optional[str] = None  # For eGFR calculation
    diagnoses: List[str] = []
    kidney_function: Optional[KidneyFunction] = None
    medications: List[str] = []
    comorbidities: List[str] = []  # diabetes, hypertension, etc.
    ckd_stage: Optional[int] = None  # CKD stage 1-5


class MedicationRecord(BaseModel):
    """Medication record for renal dosing"""
    medication_name: str
    standard_dose: float
    adjusted_dose: Optional[float] = None
    adjustment_reason: Optional[str] = None
    requires_renal_dosing: bool = False


class NephrologyDB(BaseModel):
    """Nephrology domain database"""
    patients: Dict[str, PatientRecord] = {}
    lab_results: Dict[str, KidneyFunction] = {}
    medications: Dict[str, MedicationRecord] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, db_path: str) -> "NephrologyDB":
        """Load database from JSON file"""
        import json
        from pathlib import Path

        path = Path(db_path)
        if not path.exists():
            # Return empty database if file doesn't exist
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(**data)

    def get_patient(self, patient_id: str) -> Optional[PatientRecord]:
        """Get patient by ID"""
        return self.patients.get(patient_id)

    def add_patient(self, patient: PatientRecord) -> None:
        """Add patient to database"""
        self.patients[patient.patient_id] = patient
def get_environment(db: Optional[NephrologyDB] = None) -> Environment:
    """
    Create and configure the nephrology domain environment.

    Args:
        db: Optional pre-configured database

    Returns:
        Configured Environment instance
    """
    # Load or create database
    if db is None:
        try:
            db = NephrologyDB.load(str(DB_PATH))
        except Exception:
            db = NephrologyDB()

    # Create tools
    tools = NephrologyTools(db)

    # Create user tools for patient information
    user_db = ClinicalUserDB()
    user_tools = ClinicalUserTools(user_db)

    # Load policy
    try:
        with open(POLICY_PATH, "r") as fp:
            policy = fp.read()
    except Exception:
        policy = _get_default_policy()

    # Create environment
    env = Environment(
        domain_name="clinical_nephrology",
        policy=policy,
        tools=tools,
        user_tools=user_tools,
    )

    return env


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """
    Load nephrology domain tasks.

    Args:
        task_split_name: Optional task split name (e.g., "base", "test")

    Returns:
        List of Task objects
    """
    tasks = load_file(TASKS_PATH)
    tasks = [Task.model_validate(task) for task in tasks]

    if task_split_name is None:
        return tasks

    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(
            f"Invalid task split name: {task_split_name}. "
            f"Valid splits are: {list(task_splits.keys())}"
        )

    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    """Load task splits for nephrology domain"""
    split_file = (
        Path(TASKS_PATH).parent / f"split_{Path(TASKS_PATH).stem}.json"
    )
    return load_file(split_file)


def _get_default_policy() -> str:
    """Return default nephrology domain policy"""
    return """# Clinical Nephrology Domain Policy

## Overview
This domain specializes in kidney-related clinical tasks including:
- Glomerular Filtration Rate (eGFR) calculations
- Renal function assessment
- Chronic Kidney Disease (CKD) staging
- Medication dose adjustments for renal impairment
- Nephrology consultations

## Clinical Guidelines
- Use CKD-EPI 2009 formula for eGFR calculation
- Consider race adjustment for African American patients
- CKD staging: Stage 1 (90+), Stage 2 (60-89), Stage 3a (45-59), Stage 3b (30-44), Stage 4 (15-29), Stage 5 (under 15)
- Adjust medication doses based on eGFR thresholds
- Monitor electrolytes (potassium, sodium) in renal patients

## Available Tools
- calculate_egfr: Calculate eGFR from creatinine, age, gender, race
- get_patient_kidney_function: Retrieve patient's kidney function data
- adjust_medication_dose: Calculate renal-adjusted medication doses
- get_patient_by_mrn: Find patients by Medical Record Number

## Privacy Considerations
- Handle all patient data with confidentiality
- Follow HIPAA guidelines for protected health information
"""