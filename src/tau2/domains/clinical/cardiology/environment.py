"""Environment Setup for Clinical Cardiology Domain"""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.clinical.cardiology.tools import CardiologyTools
from tau2.domains.clinical.cardiology.utils import DB_PATH, POLICY_PATH, TASKS_PATH
from tau2.environment.environment import Environment
from tau2.utils import load_file



# === DATA MODELS ===


import json
from typing import Dict, List, Optional
from pydantic import BaseModel
from tau2.domains.clinical.user_simulator import ClinicalUserDB, ClinicalUserTools



class VitalSigns(BaseModel):
    """Patient vital signs"""
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[float] = None


class CardiacTest(BaseModel):
    """Cardiac diagnostic test results"""
    ecg_interpretation: Optional[str] = None
    echocardiogram: Optional[str] = None
    stress_test: Optional[str] = None
    cardiac_biomarkers: Optional[dict] = None


class PatientRecord(BaseModel):
    """Patient record for cardiology"""
    patient_id: str
    name: str
    age: int
    gender: str
    diagnoses: List[str] = []
    vital_signs: Optional[VitalSigns] = None
    cardiac_tests: Optional[CardiacTest] = None
    medications: List[str] = []
    comorbidities: List[str] = []
    chief_complaint: Optional[str] = None


class CardiologyDB(BaseModel):
    """Cardiology domain database"""
    patients: Dict[str, PatientRecord] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, db_path: str) -> "CardiologyDB":
        import json
        from pathlib import Path
        path = Path(db_path)
        if not path.exists():
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def get_patient(self, patient_id: str) -> Optional[PatientRecord]:
        return self.patients.get(patient_id)
def get_environment(db: Optional[CardiologyDB] = None, solo_mode: bool = False) -> Environment:
    """Create cardiology domain environment"""
    if db is None:
        try:
            db = CardiologyDB.load(str(DB_PATH))
        except Exception:
            db = CardiologyDB()
    tools = CardiologyTools(db)

    # Create user tools for patient information
    user_db = ClinicalUserDB()
    user_tools = ClinicalUserTools(user_db)

    try:
        with open(POLICY_PATH, "r") as fp:
            policy = fp.read()
    except Exception:
        policy = _get_default_policy()
    return Environment(
        domain_name="clinical_cardiology",
        policy=policy,
        tools=tools,
        user_tools=user_tools
    )


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """Load cardiology tasks"""
    tasks = load_file(TASKS_PATH)
    tasks = [Task.model_validate(task) for task in tasks]
    if task_split_name is None:
        return tasks
    task_splits = get_tasks_split()
    if task_split_name not in task_splits:
        raise ValueError(f"Invalid split: {task_split_name}")
    return [task for task in tasks if task.id in task_splits[task_split_name]]


def get_tasks_split() -> dict[str, list[str]]:
    """Load task splits"""
    split_file = Path(TASKS_PATH).parent / f"split_{Path(TASKS_PATH).stem}.json"
    return load_file(split_file)


def _get_default_policy() -> str:
    """Default cardiology policy"""
    return """# Clinical Cardiology Domain Policy

## Overview
This domain specializes in heart and cardiovascular system tasks.

## Clinical Guidelines
- Assess blood pressure using ACC/AHA guidelines
- Calculate QTc using Bazett's formula
- Interpret heart rate based on age-specific norms
- Evaluate cardiac symptoms and risk factors

## Available Tools
- assess_blood_pressure: Classify blood pressure
- calculate_qtc: Calculate corrected QT interval
- interpret_heart_rate: Assess heart rate
- get_patient_by_mrn: Find patients
"""