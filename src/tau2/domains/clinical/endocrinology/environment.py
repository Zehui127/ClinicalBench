"""Environment Setup for Clinical Endocrinology Domain"""

from pathlib import Path
from typing import Optional

from tau2.data_model.tasks import Task
from tau2.domains.clinical.endocrinology.tools import EndocrinologyTools
from tau2.domains.clinical.endocrinology.utils import DB_PATH, POLICY_PATH, TASKS_PATH
from tau2.environment.environment import Environment
from tau2.utils import load_file



# === DATA MODELS ===


import json
from typing import Dict, List, Optional
from pydantic import BaseModel
from tau2.domains.clinical.user_simulator import ClinicalUserDB, ClinicalUserTools



class HormoneLevels(BaseModel):
    """Hormone lab results"""
    glucose: Optional[float] = None  # mg/dL
    hba1c: Optional[float] = None  # %
    tsh: Optional[float] = None  # mIU/L
    t4: Optional[float] = None  # mcg/dL
    t3: Optional[float] = None  # ng/dL
    cortisol: Optional[float] = None  # mcg/dL
    insulin: Optional[float] = None  # mcU/mL


class PatientRecord(BaseModel):
    """Patient record for endocrinology"""
    patient_id: str
    name: str
    age: int
    gender: str
    diagnoses: List[str] = []
    hormone_levels: Optional[HormoneLevels] = None
    medications: List[str] = []
    comorbidities: List[str] = []
    chief_complaint: Optional[str] = None


class EndocrinologyDB(BaseModel):
    """Endocrinology domain database"""
    patients: Dict[str, PatientRecord] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, db_path: str) -> "EndocrinologyDB":
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
def get_environment(db: Optional[EndocrinologyDB] = None, solo_mode: bool = False) -> Environment:
    """Create endocrinology domain environment"""
    if db is None:
        try:
            db = EndocrinologyDB.load(str(DB_PATH))
        except Exception:
            db = EndocrinologyDB()
    tools = EndocrinologyTools(db)

    # Create user tools for patient information
    user_db = ClinicalUserDB()
    user_tools = ClinicalUserTools(user_db)

    try:
        with open(POLICY_PATH, "r") as fp:
            policy = fp.read()
    except Exception:
        policy = _get_default_policy()
    return Environment(
        domain_name="clinical_endocrinology",
        policy=policy,
        tools=tools,
        user_tools=user_tools
    )


def get_tasks(task_split_name: Optional[str] = None) -> list[Task]:
    """Load endocrinology tasks"""
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
    """Default endocrinology policy"""
    return """# Clinical Endocrinology Domain Policy

## Overview
This domain specializes in hormone and metabolism-related tasks.

## Clinical Guidelines
- Interpret blood glucose (fasting vs random)
- Classify HbA1c for diabetes assessment
- Evaluate thyroid function (TSH, T4)
- Monitor hormonal imbalances

## Available Tools
- interpret_blood_glucose: Classify glucose levels
- interpret_hba1c: Assess diabetes control
- interpret_thyroid: Evaluate thyroid function
- get_patient_by_mrn: Find patients
"""