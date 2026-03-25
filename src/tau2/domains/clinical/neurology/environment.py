"""Environment Setup for Clinical Neurology Domain"""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.clinical.neurology.tools import NeurologyTools
from tau2.domains.clinical.neurology.utils import DB_PATH, POLICY_PATH, TASKS_PATH
from tau2.environment.environment import Environment
from tau2.utils import load_file
from tau2.domains.clinical.user_simulator import ClinicalUserDB, ClinicalUserTools


# === DATA MODELS ===
import json
from typing import Dict, List
from pydantic import BaseModel


class NeurologicalExam(BaseModel):
    """Neurological examination findings"""
    mental_status: Optional[str] = None
    cranial_nerves: Optional[str] = None
    motor_function: Optional[str] = None
    sensory_function: Optional[str] = None
    reflexes: Optional[str] = None
    coordination: Optional[str] = None


class PatientRecord(BaseModel):
    """Patient medical record for neurology"""
    patient_id: str
    name: str
    age: int
    gender: str
    diagnoses: List[str] = []
    neurological_exam: Optional[NeurologicalExam] = None
    medications: List[str] = []
    comorbidities: List[str] = []
    chief_complaint: Optional[str] = None


class NeurologyDB(BaseModel):
    """Neurology domain database"""
    patients: Dict[str, PatientRecord] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, db_path: str) -> "NeurologyDB":
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


def get_environment(db: Optional["NeurologyDB"] = None, solo_mode: bool = False) -> Environment:
    """Create neurology domain environment"""
    if db is None:
        try:
            db = NeurologyDB.load(str(DB_PATH))
        except Exception:
            db = NeurologyDB()
    tools = NeurologyTools(db)

    # Create user tools for patient information
    user_db = ClinicalUserDB()
    user_tools = ClinicalUserTools(user_db)

    try:
        with open(POLICY_PATH, "r") as fp:
            policy = fp.read()
    except Exception:
        policy = _get_default_policy()
    return Environment(
        domain_name="clinical_neurology",
        policy=policy,
        tools=tools,
        user_tools=user_tools
    )


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """Load neurology tasks"""
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
    """Default neurology policy"""
    return """# Clinical Neurology Domain Policy

## Overview
This domain specializes in brain and nervous system tasks.

## Clinical Guidelines
- Assess stroke risk using common risk factors
- Classify headaches by location and characteristics
- Evaluate seizure types and consciousness
- Recommend neurological consultations when appropriate

## Available Tools
- assess_stroke_risk: Basic stroke risk assessment
- interpret_headache: Classify headache types
- evaluate_seizure: Determine seizure classification
- get_patient_by_mrn: Find patients
"""